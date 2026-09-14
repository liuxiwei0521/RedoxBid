import unittest

import numpy as np
import pandas as pd

from utils.regulation_data import (
    build_hourly_demand_forecast,
    expand_hourly_to_intervals,
    normalize_regulation_history,
)


class RegulationDataTests(unittest.TestCase):
    def setUp(self):
        self.reference_frame = pd.DataFrame(
            {
                "datetime": pd.date_range("2025-07-01", periods=72, freq="h"),
                "frequency_demand": np.tile(np.arange(1.0, 25.0), 3),
                "frequency_price": np.tile(np.arange(24.0), 3),
            }
        )

    def test_reference_column_aliases_are_normalized_and_zero_price_is_valid(self):
        normalized = normalize_regulation_history(self.reference_frame)

        self.assertEqual(
            list(normalized.columns[:3]),
            [
                "timestamp",
                "regulation_demand_mw",
                "mileage_price_cny_per_mw",
            ],
        )
        self.assertEqual(normalized.iloc[0]["mileage_price_cny_per_mw"], 0.0)
        self.assertTrue(normalized["timestamp"].is_monotonic_increasing)

    def test_duplicate_timestamps_are_rejected(self):
        duplicated = pd.concat(
            [self.reference_frame, self.reference_frame.iloc[[0]]],
            ignore_index=True,
        )

        with self.assertRaisesRegex(ValueError, "duplicate timestamp"):
            normalize_regulation_history(duplicated)

    def test_negative_demand_is_rejected(self):
        invalid = self.reference_frame.copy()
        invalid.loc[0, "frequency_demand"] = -1.0

        with self.assertRaisesRegex(ValueError, "non-negative"):
            normalize_regulation_history(invalid)

    def test_hourly_values_expand_to_four_identical_quarter_hours(self):
        expanded = expand_hourly_to_intervals(np.arange(24.0))

        self.assertEqual(len(expanded), 96)
        self.assertEqual(expanded[:4].tolist(), [0.0, 0.0, 0.0, 0.0])
        self.assertEqual(expanded[-4:].tolist(), [23.0, 23.0, 23.0, 23.0])

    def test_missing_future_demand_uses_hourly_historical_median(self):
        normalized = normalize_regulation_history(self.reference_frame)

        forecast, source = build_hourly_demand_forecast(normalized)

        self.assertEqual(len(forecast), 24)
        self.assertEqual(source, "estimated")
        self.assertEqual(forecast.tolist(), list(np.arange(1.0, 25.0)))


if __name__ == "__main__":
    unittest.main()
