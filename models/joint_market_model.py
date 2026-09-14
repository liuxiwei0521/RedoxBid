"""True co-optimization of day-ahead energy and regulation reserve."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pyomo.environ as pyo

from models.market_types import MarketSolveResult, interval_labels
from models.optimization_model import DEFAULT_SOLVER, get_solver_config
from models.sequential_market_model import DT_HOURS, TOTAL_STEPS, _numeric_array


class JointEnergyRegulationModel:
    """Deterministic MILP with shared power and energy headroom."""

    def __init__(
        self,
        day_ahead_prices,
        battery_params: dict,
        regulation_market: pd.DataFrame,
        regulation_config: dict,
        solver_type: str = DEFAULT_SOLVER,
    ):
        self.day_ahead_prices = np.asarray(day_ahead_prices, dtype=float)
        if self.day_ahead_prices.shape != (TOTAL_STEPS,) or not np.isfinite(
            self.day_ahead_prices
        ).all():
            raise ValueError("day-ahead prices must contain 96 finite values")
        self.battery_params = battery_params
        self.regulation_market = regulation_market
        self.regulation_config = regulation_config
        self.solver_type = solver_type
        self.demand = _numeric_array(regulation_market, "regulation_demand_mw")
        self.capacity_price = _numeric_array(
            regulation_market, "capacity_price_cny_per_mw_h"
        )
        self.mileage_price = _numeric_array(
            regulation_market, "mileage_price_cny_per_mw"
        )
        self.performance = _numeric_array(regulation_market, "performance_score")
        self.mileage_ratio = _numeric_array(regulation_market, "mileage_ratio")
        if min(
            self.demand.min(),
            self.capacity_price.min(),
            self.mileage_price.min(),
            self.performance.min(),
            self.mileage_ratio.min(),
        ) < 0:
            raise ValueError("regulation market inputs must be non-negative")

    def _regulation_unit_margin(self, t: int) -> float:
        config = self.regulation_config
        throughput = self.mileage_ratio[t] * DT_HOURS
        return float(
            self.capacity_price[t] * DT_HOURS
            + self.mileage_price[t]
            * self.mileage_ratio[t]
            * self.performance[t]
            * DT_HOURS
            - config["regulation_degradation_cost_cny_per_mwh"] * throughput
            - config["regulation_om_cost_cny_per_mw_h"] * DT_HOURS
            - max(self.day_ahead_prices[t], 0.0)
            * config["efficiency_loss_fraction"]
            * throughput
        )

    def create_optimization_model(self):
        params = self.battery_params
        config = self.regulation_config
        model = pyo.ConcreteModel()
        model.T = pyo.RangeSet(0, TOTAL_STEPS - 1)
        model.E_INDEX = pyo.RangeSet(0, TOTAL_STEPS)
        model.P_charge = pyo.Var(model.T, domain=pyo.NonNegativeReals)
        model.P_discharge = pyo.Var(model.T, domain=pyo.NonNegativeReals)
        model.R = pyo.Var(model.T, domain=pyo.NonNegativeReals)
        model.E = pyo.Var(model.E_INDEX, domain=pyo.NonNegativeReals)
        model.charge_on = pyo.Var(model.T, domain=pyo.Binary)
        model.discharge_on = pyo.Var(model.T, domain=pyo.Binary)

        energy_revenue = sum(
            (model.P_discharge[t] - model.P_charge[t])
            * self.day_ahead_prices[t]
            * DT_HOURS
            for t in model.T
        )
        energy_degradation = sum(
            params["k"]
            * (
                model.P_charge[t] / params["η_charge"]
                + model.P_discharge[t] * params["η_discharge"]
            )
            * DT_HOURS
            for t in model.T
        )
        regulation_value = sum(
            model.R[t] * self._regulation_unit_margin(t) for t in model.T
        )
        model.objective = pyo.Objective(
            expr=energy_revenue
            - energy_degradation
            - params["C_OM"]
            + regulation_value,
            sense=pyo.maximize,
        )

        rated_power = float(params["P_rated"])
        energy_min = float(params["SOC_min"] * params["E_rated"])
        energy_max = float(params["SOC_max"] * params["E_rated"])
        eta_charge = float(params["η_charge"])
        eta_discharge = float(params["η_discharge"])
        reserve_duration = float(config["reserve_duration_hours"])
        max_share = float(config["max_market_share"])

        model.initial_energy = pyo.Constraint(expr=model.E[0] == params["E_0"])
        model.energy_balance = pyo.Constraint(
            model.T,
            rule=lambda m, t: m.E[t + 1]
            == m.E[t]
            + m.P_charge[t] * eta_charge * DT_HOURS
            - m.P_discharge[t] / eta_discharge * DT_HOURS,
        )
        model.terminal_energy = pyo.Constraint(
            expr=model.E[TOTAL_STEPS] == params["E_T_target"]
        )
        model.energy_lower = pyo.Constraint(
            model.E_INDEX, rule=lambda m, t: m.E[t] >= energy_min
        )
        model.energy_upper = pyo.Constraint(
            model.E_INDEX, rule=lambda m, t: m.E[t] <= energy_max
        )
        model.mode_mutex = pyo.Constraint(
            model.T,
            rule=lambda m, t: m.charge_on[t] + m.discharge_on[t] <= 1,
        )
        model.charge_mode = pyo.Constraint(
            model.T,
            rule=lambda m, t: m.P_charge[t] <= rated_power * m.charge_on[t],
        )
        model.discharge_mode = pyo.Constraint(
            model.T,
            rule=lambda m, t: m.P_discharge[t]
            <= rated_power * m.discharge_on[t],
        )
        model.charge_headroom = pyo.Constraint(
            model.T,
            rule=lambda m, t: m.P_charge[t] + m.R[t] <= rated_power,
        )
        model.discharge_headroom = pyo.Constraint(
            model.T,
            rule=lambda m, t: m.P_discharge[t] + m.R[t] <= rated_power,
        )
        model.market_limit = pyo.Constraint(
            model.T,
            rule=lambda m, t: m.R[t] <= self.demand[t] * max_share,
        )
        model.up_energy_reserve = pyo.Constraint(
            model.T,
            rule=lambda m, t: m.R[t] * reserve_duration / eta_discharge
            <= m.E[t] - energy_min,
        )
        model.down_energy_reserve = pyo.Constraint(
            model.T,
            rule=lambda m, t: m.R[t] * reserve_duration * eta_charge
            <= energy_max - m.E[t],
        )

        power_ramp = float(params["R_ramp"])
        regulation_ramp = float(config["regulation_ramp_mw_per_interval"])
        for name, current in (
            ("charge", model.P_charge),
            ("discharge", model.P_discharge),
        ):
            setattr(
                model,
                f"{name}_ramp_up",
                pyo.Constraint(
                    model.T,
                    rule=lambda m, t, variable=current: pyo.Constraint.Skip
                    if t == 0
                    else variable[t] - variable[t - 1] <= power_ramp,
                ),
            )
            setattr(
                model,
                f"{name}_ramp_down",
                pyo.Constraint(
                    model.T,
                    rule=lambda m, t, variable=current: pyo.Constraint.Skip
                    if t == 0
                    else variable[t - 1] - variable[t] <= power_ramp,
                ),
            )
        model.regulation_ramp_up = pyo.Constraint(
            model.T,
            rule=lambda m, t: pyo.Constraint.Skip
            if t == 0
            else m.R[t] - m.R[t - 1] <= regulation_ramp,
        )
        model.regulation_ramp_down = pyo.Constraint(
            model.T,
            rule=lambda m, t: pyo.Constraint.Skip
            if t == 0
            else m.R[t - 1] - m.R[t] <= regulation_ramp,
        )
        model.cycle_limit = pyo.Constraint(
            expr=sum(
                (
                    model.P_charge[t] * eta_charge
                    + model.P_discharge[t] / eta_discharge
                )
                * DT_HOURS
                for t in model.T
            )
            <= 2 * params["E_rated"] * params["N_cycle_max"]
        )
        return model

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

        charge = np.asarray(
            [pyo.value(model.P_charge[t]) for t in model.T], dtype=float
        )
        discharge = np.asarray(
            [pyo.value(model.P_discharge[t]) for t in model.T], dtype=float
        )
        reserve = np.asarray([pyo.value(model.R[t]) for t in model.T], dtype=float)
        energy = np.asarray(
            [pyo.value(model.E[t]) for t in model.E_INDEX], dtype=float
        )
        params = self.battery_params
        da_profit = float(
            np.sum((discharge - charge) * self.day_ahead_prices * DT_HOURS)
            - np.sum(
                params["k"]
                * (
                    charge / params["η_charge"]
                    + discharge * params["η_discharge"]
                )
                * DT_HOURS
            )
            - params["C_OM"]
        )
        regulation_profit = float(
            sum(reserve[t] * self._regulation_unit_margin(t) for t in range(TOTAL_STEPS))
        )
        throughput = float(
            np.sum(
                (
                    charge * params["η_charge"]
                    + discharge / params["η_discharge"]
                )
                * DT_HOURS
            )
        )
        schedule = pd.DataFrame(
            {
                "time": interval_labels(),
                "day_ahead_price_cny_per_mwh": self.day_ahead_prices,
                "charge_power_mw": charge,
                "discharge_power_mw": discharge,
                "net_power_mw": discharge - charge,
                "regulation_reserve_mw": reserve,
                "energy_mwh": energy[:-1],
                "ending_energy_mwh": energy[1:],
                "soc_percent": energy[:-1] / params["E_rated"] * 100,
            }
        )
        kpis = {
            "day_ahead_profit_cny": da_profit,
            "regulation_profit_cny": regulation_profit,
            "total_profit_cny": da_profit + regulation_profit,
            "average_reserve_mw": float(reserve.mean()),
            "peak_reserve_mw": float(reserve.max()),
            "equivalent_cycles": throughput / (2 * params["E_rated"]),
        }
        return MarketSolveResult(
            status="optimal",
            objective_value=float(pyo.value(model.objective)),
            schedule=schedule,
            kpis=kpis,
            solver_name=self.solver_type,
            raw_model=model,
        )
