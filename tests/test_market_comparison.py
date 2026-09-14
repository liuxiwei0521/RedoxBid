import unittest

import numpy as np
import pandas as pd

from utils.market_comparison import (
    build_baseline_schedule,
    build_market_comparison,
    build_regulation_market_frame,
)


class FakeDayAheadModel:
    P_charge = {index: float(index % 2) for index in range(96)}
    P_discharge = {index: float((index + 1) % 2) for index in range(96)}
    E = {index: 50.0 for index in range(97)}


class MarketComparisonTests(unittest.TestCase):
    def test_hourly_regulation_forecast_is_mapped_to_96_intervals(self):
        hourly = pd.DataFrame(
            {
                "timestamp": pd.date_range("2025-01-01", periods=24, freq="h"),
                "regulation_demand_mw": np.arange(24.0),
                "mileage_price_cny_per_mw": np.arange(24.0) + 1,
            }
        )
        result = build_regulation_market_frame(
            hourly,
            capacity_price_cny_per_mw_h=8.0,
            performance_score=0.95,
            mileage_ratio=0.25,
        )

        self.assertEqual(len(result), 96)
        self.assertEqual(result["regulation_demand_mw"].iloc[:4].tolist(), [0.0] * 4)
        self.assertEqual(result["capacity_price_cny_per_mw_h"].unique().tolist(), [8.0])

    def test_baseline_schedule_uses_interval_start_energy(self):
        result = build_baseline_schedule(
            FakeDayAheadModel(), np.full(96, 50.0)
        )

        self.assertEqual(len(result), 96)
        self.assertEqual(result["energy_mwh"].iloc[-1], 50.0)
        self.assertEqual(result["day_ahead_price_cny_per_mwh"].iloc[0], 50.0)

    def test_comparison_uses_three_named_scenarios(self):
        result = build_market_comparison(100.0, 120.0, 135.0)

        self.assertEqual(
            result["scenario"].tolist(),
            ["day_ahead_only", "sequential", "joint"],
        )
        self.assertEqual(result["increment_vs_day_ahead_cny"].tolist(), [0.0, 20.0, 35.0])


if __name__ == "__main__":
    unittest.main()
