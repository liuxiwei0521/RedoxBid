import importlib.util
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from ui.theme import apply_plotly_theme
from utils.visualization import generate_comprehensive_visualization


ROOT = Path(__file__).resolve().parents[1]


def load_decision_page():
    spec = importlib.util.spec_from_file_location(
        "decision_page", ROOT / "app" / "决策主页面.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeModel:
    P_charge = {0: 1.0, 1: 0.0}
    P_discharge = {0: 0.0, 1: 2.0}
    E = {0: 25.0, 1: 25.2}


class DataContractTests(unittest.TestCase):
    def test_default_regulation_sample_is_synthetic_and_loadable(self):
        page = load_decision_page()

        history, source = page.load_default_regulation_history()

        self.assertEqual(source, "synthetic seven-day sample")
        self.assertEqual(len(history), 168)
        self.assertEqual(
            list(history.columns[:3]),
            ["timestamp", "regulation_demand_mw", "mileage_price_cny_per_mw"],
        )
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(history["timestamp"]))

    def test_plotly_theme_supports_single_axis_figures(self):
        figure = go.Figure(data=[go.Scatter(x=[1, 2], y=[3, 4])])
        figure.update_layout(
            xaxis_title="运行时间",
            yaxis_title="净利润（元）",
        )

        themed = apply_plotly_theme(figure, "en")

        self.assertEqual(list(themed.data[0].y), [3, 4])

    def test_plotly_theme_preserves_a_market_specific_title(self):
        figure = go.Figure(data=[go.Bar(x=["A"], y=[1])])
        figure.update_layout(title="三方案利润对比")

        themed = apply_plotly_theme(figure, "zh")

        self.assertEqual(themed.layout.title.text, "三方案利润对比")

    def test_plotly_theme_does_not_change_trace_values(self):
        params = {
            "E_rated": 50.0,
            "P_rated": 10.0,
            "SOC_min": 0.2,
            "SOC_max": 0.8,
        }
        figure = generate_comprehensive_visualization(
            FakeModel(),
            np.array([300.0, 500.0]),
            params,
        )
        before = [list(trace.y) for trace in figure.data]

        themed = apply_plotly_theme(figure, "en")

        self.assertEqual(before, [list(trace.y) for trace in themed.data])

    def test_results_dataframe_schema_and_sign_convention(self):
        page = load_decision_page()
        result = page.create_results_dataframe(
            FakeModel(),
            np.array([300.0, 500.0]),
            {"E_rated": 50.0},
            15,
        )
        self.assertEqual(
            list(result.columns),
            [
                "Time",
                "Price (元/MWh)",
                "Charge_Power (MW)",
                "Discharge_Power (MW)",
                "Net_Power (MW)",
                "Energy_State (MWh)",
                "SOC (%)",
            ],
        )
        self.assertEqual(result["Net_Power (MW)"].tolist(), [-1.0, 2.0])
        self.assertAlmostEqual(result["SOC (%)"].iloc[0], 50.0)
        self.assertAlmostEqual(result["SOC (%)"].iloc[1], 50.4)

    def test_csv_export_preserves_column_order(self):
        page = load_decision_page()
        result = page.create_results_dataframe(
            FakeModel(),
            np.array([300.0, 500.0]),
            {"E_rated": 50.0},
            15,
        )
        exported = page.convert_df_to_csv(result).decode("utf-8-sig")
        self.assertTrue(exported.startswith(",".join(result.columns)))

    def test_download_artifacts_preserve_names_and_csv_schemas(self):
        page = load_decision_page()
        results = page.create_results_dataframe(
            FakeModel(),
            np.array([300.0, 500.0]),
            {"E_rated": 50.0},
            15,
        )
        bids = results[["Time", "Net_Power (MW)"]].copy()
        artifacts = page.build_download_artifacts(
            results,
            bids,
            optimal_mode=0,
        )

        self.assertEqual(
            artifacts["schedule"]["file_name"],
            "optimal_schedule_details.csv",
        )
        self.assertEqual(
            artifacts["bid"]["file_name"],
            "simple_bidding_strategy.csv",
        )
        schedule_text = artifacts["schedule"]["data"].decode("utf-8-sig")
        bid_text = artifacts["bid"]["data"].decode("utf-8-sig")
        self.assertTrue(schedule_text.startswith(",".join(results.columns)))
        self.assertTrue(bid_text.startswith("Time,Net_Power (MW)"))


if __name__ == "__main__":
    unittest.main()
