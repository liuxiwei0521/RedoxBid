import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from models.parameter_config import get_default_battery_params
from utils import database


EXPECTED_PROFILE = {
    "id": 1,
    "station_name": "三峡能源新疆吉木萨尔全钒液流储能电站",
    "location": "新疆维吾尔自治区昌吉回族自治州吉木萨尔县",
    "commission_date": "2025-12-31",
    "e_rated": 1000.0,
    "p_rated": 200.0,
}


class StationConfigurationTests(unittest.TestCase):
    def test_loading_profile_initializes_a_missing_archive(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "station_archive.db"
            connections = []

            def connect_to_test_archive():
                connection = sqlite3.connect(db_path)
                connection.row_factory = sqlite3.Row
                connections.append(connection)
                return connection

            with patch.object(
                database,
                "get_db_connection",
                side_effect=connect_to_test_archive,
            ):
                try:
                    profile = database.load_station_profile()
                except sqlite3.OperationalError as error:
                    self.fail(
                        "Loading the station profile must initialize a missing "
                        f"archive first: {error}"
                    )
                finally:
                    for connection in connections:
                        connection.close()

            self.assertTrue(db_path.exists())
            self.assertEqual(
                profile["station_name"],
                "三峡能源新疆吉木萨尔全钒液流储能电站",
            )

    def test_battery_defaults_match_station_rating_and_energy_state(self):
        params = get_default_battery_params()

        self.assertEqual(params["E_rated"], 1000)
        self.assertEqual(params["P_rated"], 200)
        self.assertEqual(params["initial_soc"], 0.5)
        self.assertEqual(params["E_0"], 500)
        self.assertEqual(params["E_T_target"], 500)
        self.assertAlmostEqual(params["η_charge"] * params["η_discharge"], 0.75, places=3)

    def test_new_archive_uses_jimsar_station_profile(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "station_archive.db"
            with patch.object(database, "DB_PATH", str(db_path)):
                database.init_db()
                profile = database.load_station_profile()

        self.assertEqual(profile, EXPECTED_PROFILE)

if __name__ == "__main__":
    unittest.main()
