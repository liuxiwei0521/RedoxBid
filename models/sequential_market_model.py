"""Regulation optimization with the day-ahead schedule held fixed."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pyomo.environ as pyo

from models.market_types import MarketSolveResult, interval_labels
from models.optimization_model import DEFAULT_SOLVER, get_solver_config


TOTAL_STEPS = 96
DT_HOURS = 0.25


def _numeric_array(frame: pd.DataFrame, column: str) -> np.ndarray:
    if column not in frame:
        raise ValueError(f"missing required column: {column}")
    values = pd.to_numeric(frame[column], errors="coerce").to_numpy(dtype=float)
    if values.shape != (TOTAL_STEPS,) or not np.isfinite(values).all():
        raise ValueError(f"{column} must contain 96 finite values")
    return values


class SequentialRegulationModel:
    """Maximize regulation value without changing a fixed day-ahead dispatch."""

    def __init__(
        self,
        day_ahead_schedule: pd.DataFrame,
        battery_params: dict,
        regulation_market: pd.DataFrame,
        regulation_config: dict,
        solver_type: str = DEFAULT_SOLVER,
    ):
        self.day_ahead_schedule = day_ahead_schedule
        self.battery_params = battery_params
        self.regulation_market = regulation_market
        self.regulation_config = regulation_config
        self.solver_type = solver_type
        self._load_inputs()

    def _load_inputs(self):
        self.charge = _numeric_array(self.day_ahead_schedule, "charge_power_mw")
        self.discharge = _numeric_array(
            self.day_ahead_schedule, "discharge_power_mw"
        )
        self.energy = _numeric_array(self.day_ahead_schedule, "energy_mwh")
        self.da_price = _numeric_array(
            self.day_ahead_schedule, "day_ahead_price_cny_per_mwh"
        )
        self.demand = _numeric_array(
            self.regulation_market, "regulation_demand_mw"
        )
        self.capacity_price = _numeric_array(
            self.regulation_market, "capacity_price_cny_per_mw_h"
        )
        self.mileage_price = _numeric_array(
            self.regulation_market, "mileage_price_cny_per_mw"
        )
        self.performance = _numeric_array(
            self.regulation_market, "performance_score"
        )
        self.mileage_ratio = _numeric_array(
            self.regulation_market, "mileage_ratio"
        )
        if min(
            self.charge.min(),
            self.discharge.min(),
            self.energy.min(),
            self.demand.min(),
            self.capacity_price.min(),
            self.mileage_price.min(),
            self.performance.min(),
            self.mileage_ratio.min(),
        ) < 0:
            raise ValueError("market and schedule inputs must be non-negative")

    def _regulation_unit_margin(self, t: int) -> float:
        config = self.regulation_config
        throughput = self.mileage_ratio[t] * DT_HOURS
        revenue = self.capacity_price[t] * DT_HOURS + (
            self.mileage_price[t]
            * self.mileage_ratio[t]
            * self.performance[t]
            * DT_HOURS
        )
        cost = (
            config["regulation_degradation_cost_cny_per_mwh"] * throughput
            + config["regulation_om_cost_cny_per_mw_h"] * DT_HOURS
            + max(self.da_price[t], 0.0)
            * config["efficiency_loss_fraction"]
            * throughput
        )
        return revenue - cost

    def create_optimization_model(self):
        params = self.battery_params
        config = self.regulation_config
        model = pyo.ConcreteModel()
        model.T = pyo.RangeSet(0, TOTAL_STEPS - 1)
        model.R = pyo.Var(model.T, domain=pyo.NonNegativeReals)

        model.objective = pyo.Objective(
            expr=sum(model.R[t] * self._regulation_unit_margin(t) for t in model.T),
            sense=pyo.maximize,
        )
        max_share = float(config["max_market_share"])
        reserve_duration = float(config["reserve_duration_hours"])
        eta_charge = float(params["η_charge"])
        eta_discharge = float(params["η_discharge"])
        energy_min = float(params["SOC_min"] * params["E_rated"])
        energy_max = float(params["SOC_max"] * params["E_rated"])
        rated_power = float(params["P_rated"])

        model.market_limit = pyo.Constraint(
            model.T,
            rule=lambda m, t: m.R[t] <= self.demand[t] * max_share,
        )
        model.charge_headroom = pyo.Constraint(
            model.T,
            rule=lambda m, t: self.charge[t] + m.R[t] <= rated_power,
        )
        model.discharge_headroom = pyo.Constraint(
            model.T,
            rule=lambda m, t: self.discharge[t] + m.R[t] <= rated_power,
        )
        model.up_energy_reserve = pyo.Constraint(
            model.T,
            rule=lambda m, t: m.R[t] * reserve_duration / eta_discharge
            <= self.energy[t] - energy_min,
        )
        model.down_energy_reserve = pyo.Constraint(
            model.T,
            rule=lambda m, t: m.R[t] * reserve_duration * eta_charge
            <= energy_max - self.energy[t],
        )
        ramp = float(config["regulation_ramp_mw_per_interval"])
        model.ramp_up = pyo.Constraint(
            model.T,
            rule=lambda m, t: pyo.Constraint.Skip
            if t == 0
            else m.R[t] - m.R[t - 1] <= ramp,
        )
        model.ramp_down = pyo.Constraint(
            model.T,
            rule=lambda m, t: pyo.Constraint.Skip
            if t == 0
            else m.R[t - 1] - m.R[t] <= ramp,
        )
        return model

    def _day_ahead_profit(self) -> float:
        params = self.battery_params
        energy_margin = np.sum(
            (self.discharge - self.charge) * self.da_price * DT_HOURS
        )
        degradation = np.sum(
            params["k"]
            * (
                self.charge / params["η_charge"]
                + self.discharge * params["η_discharge"]
            )
            * DT_HOURS
        )
        return float(energy_margin - degradation - params["C_OM"])

    def solve(self) -> MarketSolveResult:
        model = self.create_optimization_model()
        config = get_solver_config(self.solver_type)
        solver = pyo.SolverFactory(config["factory"])
        try:
            results = solver.solve(model, tee=False, options=config["options"])
        except Exception as error:
            return MarketSolveResult(
                status="solver_error",
                objective_value=None,
                schedule=pd.DataFrame(),
                diagnostics=(str(error),),
                solver_name=self.solver_type,
                raw_model=model,
            )
        termination = results.solver.termination_condition
        if termination != pyo.TerminationCondition.optimal:
            status = (
                "infeasible"
                if termination == pyo.TerminationCondition.infeasible
                else "timeout"
                if termination == pyo.TerminationCondition.maxTimeLimit
                else "solver_error"
            )
            return MarketSolveResult(
                status=status,
                objective_value=None,
                schedule=pd.DataFrame(),
                diagnostics=(str(termination),),
                solver_name=self.solver_type,
                raw_model=model,
            )

        reserve = np.asarray([pyo.value(model.R[t]) for t in model.T], dtype=float)
        regulation_profit = float(pyo.value(model.objective))
        day_ahead_profit = self._day_ahead_profit()
        schedule = pd.DataFrame(
            {
                "time": interval_labels(),
                "charge_power_mw": self.charge,
                "discharge_power_mw": self.discharge,
                "energy_mwh": self.energy,
                "regulation_reserve_mw": reserve,
                "regulation_demand_mw": self.demand,
                "capacity_price_cny_per_mw_h": self.capacity_price,
                "mileage_price_cny_per_mw": self.mileage_price,
            }
        )
        kpis = {
            "day_ahead_profit_cny": day_ahead_profit,
            "regulation_profit_cny": regulation_profit,
            "total_profit_cny": day_ahead_profit + regulation_profit,
            "average_reserve_mw": float(reserve.mean()),
            "peak_reserve_mw": float(reserve.max()),
        }
        return MarketSolveResult(
            status="optimal",
            objective_value=kpis["total_profit_cny"],
            schedule=schedule,
            kpis=kpis,
            solver_name=self.solver_type,
            raw_model=model,
        )
