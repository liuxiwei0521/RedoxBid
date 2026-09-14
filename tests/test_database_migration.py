import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from utils import database


class DatabaseMigrationTests(unittest.TestCase):
    def test_market_columns_are_added_without_dropping_existing_records(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = str(Path(directory) / "archive.db")
            with patch.object(database, "DB_PATH", db_path):
                database.init_db()
                database.save_decision_record(
                    {"总净利润": 100.0, "总能量吞吐": 2.0, "等效循环次数": 0.1},
                    "报量不报价",
                    {
                        "market_mode": "comparison",
                        "da_profit": 100.0,
                        "sequential_profit": 120.0,
                        "joint_profit": 135.0,
                        "solver_name": "CBC",
                        "solver_status": "optimal",
                        "data_source": "sample",
                    },
                )
                records = database.load_decision_records()

        self.assertEqual(len(records), 1)
        self.assertEqual(records.iloc[0]["market_mode"], "comparison")
        self.assertEqual(records.iloc[0]["joint_profit"], 135.0)
        self.assertEqual(records.iloc[0]["solver_status"], "optimal")


if __name__ == "__main__":
    unittest.main()
