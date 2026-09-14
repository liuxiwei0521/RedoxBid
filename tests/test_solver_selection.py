import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pyomo.environ as pyo

from models import optimization_model


class _FakeSolver:
    def __init__(self):
        self.solve_kwargs = None

    def solve(self, model, **kwargs):
        self.solve_kwargs = kwargs
        return SimpleNamespace(
            solver=SimpleNamespace(
                status=pyo.SolverStatus.ok,
                termination_condition=pyo.TerminationCondition.optimal,
            )
        )


class SolverSelectionTests(unittest.TestCase):
    def test_energy_state_covers_the_final_interval(self):
        params = {
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
            "Q_flow_min": 0.0,
            "Q_flow_max": 100.0,
        }
        model = optimization_model.FlowBatteryDayAheadMarketModel(
            np.zeros(96), params
        ).create_optimization_model()

        self.assertEqual(len(model.E), 97)
        self.assertIn("E[96]", str(model.final_energy.expr))
        self.assertEqual(len(model.energy_transfer), 96)
        self.assertTrue(hasattr(model, "cycle_limit"))

    def test_registered_solver_drives_the_actual_pyomo_backend(self):
        registry = getattr(optimization_model, "SOLVER_REGISTRY", None)
        if registry is None:
            self.fail("The optimization model must expose a solver registry")

        fake_solver = _FakeSolver()
        test_config = {
            "factory": "test-milp",
            "options": {"time_limit": 1},
        }
        with patch.dict(registry, {"TEST_MILP": test_config}, clear=False):
            market_model = optimization_model.FlowBatteryDayAheadMarketModel(
                np.zeros(96),
                {},
                solver_type="TEST_MILP",
            )
            fake_model = object()
            with patch.object(
                market_model,
                "create_optimization_model",
                return_value=fake_model,
            ), patch.object(
                market_model,
                "diagnose_model",
            ), patch.object(
                optimization_model.pyo,
                "SolverFactory",
                return_value=fake_solver,
            ) as solver_factory:
                solved_model, _ = market_model.solve_model()

        self.assertIs(solved_model, fake_model)
        solver_factory.assert_called_once_with("test-milp")
        self.assertEqual(fake_solver.solve_kwargs["options"], {"time_limit": 1})

    def test_unregistered_solver_is_rejected(self):
        market_model_class = optimization_model.FlowBatteryDayAheadMarketModel
        try:
            market_model = market_model_class(
                np.zeros(96),
                {},
                solver_type="IPOPT",
            )
        except TypeError as error:
            self.fail(f"The model must accept an explicit solver_type: {error}")

        with self.assertRaisesRegex(ValueError, "Unsupported solver"):
            market_model.solve_model()


if __name__ == "__main__":
    unittest.main()
