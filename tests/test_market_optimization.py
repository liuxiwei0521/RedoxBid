import unittest

import numpy as np
import pandas as pd

from models.joint_market_model import JointEnergyRegulationModel
from models.sequential_market_model import SequentialRegulationModel


def battery_params():
    return {
        "E_rated": 40.0,
        "P_rated": 10.0,
        "E_0": 20.0,
        "E_T_target": 20.0,
        "SOC_min": 0.2,
        "SOC_max": 0.8,
        "η_charge": 0.9,
        "η_discharge": 0.9,
        "N_cycle_max": 2.0,
        "k": 0.0,
        "C_OM": 0.0,
        "R_ramp": 10.0,
    }


def regulation_market():
    return pd.DataFrame(
        {
            "regulation_demand_mw": np.full(96, 5.0),
            "capacity_price_cny_per_mw_h": np.full(96, 10.0),
            "mileage_price_cny_per_mw": np.full(96, 2.0),
            "performance_score": np.full(96, 0.95),
            "mileage_ratio": np.full(96, 0.25),
        }
    )


def regulation_config():
    return {
        "reserve_duration_hours": 0.25,
        "max_market_share": 1.0,
        "regulation_degradation_cost_cny_per_mwh": 0.2,
        "regulation_om_cost_cny_per_mw_h": 0.1,
        "efficiency_loss_fraction": 0.02,
        "regulation_ramp_mw_per_interval": 10.0,
    }


class MarketOptimizationTests(unittest.TestCase):
    def test_sequential_model_respects_fixed_power_and_reserve_headroom(self):
        schedule = pd.DataFrame(
            {
                "charge_power_mw": np.zeros(96),
                "discharge_power_mw": np.zeros(96),
                "energy_mwh": np.full(96, 20.0),
                "day_ahead_price_cny_per_mwh": np.full(96, 50.0),
            }
        )
        result = SequentialRegulationModel(
            schedule,
            battery_params(),
            regulation_market(),
            regulation_config(),
        ).solve()

        self.assertEqual(result.status, "optimal")
        self.assertTrue((result.schedule["regulation_reserve_mw"] <= 5.0 + 1e-6).all())
        self.assertTrue((result.schedule["regulation_reserve_mw"] >= -1e-6).all())
        self.assertGreater(result.kpis["regulation_profit_cny"], 0.0)

    def test_joint_model_enforces_power_energy_and_terminal_constraints(self):
        prices = np.r_[np.full(48, 10.0), np.full(48, 100.0)]
        result = JointEnergyRegulationModel(
            prices,
            battery_params(),
            regulation_market(),
            regulation_config(),
        ).solve()

        self.assertEqual(result.status, "optimal")
        schedule = result.schedule
        power = battery_params()["P_rated"]
        self.assertTrue(
            (
                schedule["charge_power_mw"]
                + schedule["regulation_reserve_mw"]
                <= power + 1e-6
            ).all()
        )
        self.assertTrue(
            (
                schedule["discharge_power_mw"]
                + schedule["regulation_reserve_mw"]
                <= power + 1e-6
            ).all()
        )
        self.assertAlmostEqual(schedule["ending_energy_mwh"].iloc[-1], 20.0, 6)
        self.assertLessEqual(result.kpis["equivalent_cycles"], 2.0 + 1e-6)

    def test_joint_solution_dominates_feasible_sequential_zero_schedule(self):
        prices = np.full(96, 50.0)
        schedule = pd.DataFrame(
            {
                "charge_power_mw": np.zeros(96),
                "discharge_power_mw": np.zeros(96),
                "energy_mwh": np.full(96, 20.0),
                "day_ahead_price_cny_per_mwh": prices,
            }
        )
        sequential = SequentialRegulationModel(
            schedule,
            battery_params(),
            regulation_market(),
            regulation_config(),
        ).solve()
        joint = JointEnergyRegulationModel(
            prices,
            battery_params(),
            regulation_market(),
            regulation_config(),
        ).solve()

        self.assertGreaterEqual(
            joint.kpis["total_profit_cny"] + 0.01,
            sequential.kpis["total_profit_cny"],
        )


if __name__ == "__main__":
    unittest.main()
