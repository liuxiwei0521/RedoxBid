import io
import unittest
from pathlib import Path

import pandas as pd

from utils.input_sources import load_day_ahead_frame


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class DayAheadInputSourceTests(unittest.TestCase):
    def test_bundled_source_loads_the_repository_sample(self):
        frame = load_day_ahead_frame("bundled", project_root=PROJECT_ROOT)

        self.assertEqual(
            list(frame.columns), ["timestamp", "price", "day_of_week"]
        )
        self.assertEqual(len(frame), 96)
        self.assertAlmostEqual(frame.loc[0, "price"], 158.80)

    def test_upload_source_reads_the_uploaded_csv(self):
        uploaded = io.StringIO(
            "timestamp,price\n2025-01-01 00:00:00,123.45\n"
        )

        frame = load_day_ahead_frame("upload", uploaded_file=uploaded)

        pd.testing.assert_frame_equal(
            frame,
            pd.DataFrame(
                {
                    "timestamp": ["2025-01-01 00:00:00"],
                    "price": [123.45],
                }
            ),
        )

    def test_upload_source_requires_a_file(self):
        self.assertIsNone(
            load_day_ahead_frame("upload", uploaded_file=None)
        )

    def test_unknown_source_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError, "Unsupported day-ahead data source"
        ):
            load_day_ahead_frame("unknown")


if __name__ == "__main__":
    unittest.main()
