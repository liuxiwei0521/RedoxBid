import unittest

import numpy as np
import pandas as pd

from models.regulation_forecast import forecast_regulation_prices


def build_history(hours=168):
    timestamps = pd.date_range("2025-07-01", periods=hours, freq="h")
    hour = timestamps.hour.to_numpy()
    demand = 500.0 + 80.0 * np.sin(2 * np.pi * hour / 24)
    price = 12.0 + 0.02 * demand + 3.0 * (hour >= 17)
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "regulation_demand_mw": demand,
            "mileage_price_cny_per_mw": price,
        }
    )


class RegulationForecastTests(unittest.TestCase):
    def test_forecast_is_deterministic_and_contains_24_future_hours(self):
        history = build_history()

        first = forecast_regulation_prices(history, random_state=7)
        second = forecast_regulation_prices(history, random_state=7)

        self.assertEqual(len(first.hourly_forecast), 24)
        self.assertTrue(
            np.allclose(
                first.hourly_forecast["mileage_price_cny_per_mw"],
                second.hourly_forecast["mileage_price_cny_per_mw"],
            )
        )
        self.assertGreater(
            first.hourly_forecast["timestamp"].min(),
            history["timestamp"].max(),
        )

    def test_reported_metrics_come_from_a_chronological_holdout(self):
        result = forecast_regulation_prices(build_history(), random_state=11)

        self.assertLess(result.train_end, result.test_start)
        self.assertIn(result.model_name, {"Linear Regression", "Random Forest"})
        self.assertGreaterEqual(result.metrics["mae"], 0.0)
        self.assertGreaterEqual(result.metrics["rmse"], 0.0)
        self.assertEqual(result.data_source, "sample")

    def test_too_little_history_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least 72"):
            forecast_regulation_prices(build_history(48))


if __name__ == "__main__":
    unittest.main()
