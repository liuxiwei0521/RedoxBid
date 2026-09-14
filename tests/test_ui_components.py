import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.9 and 3.10
    import toml as tomllib

from ui import components, i18n, theme
from ui.components import build_sidebar_outline_html, build_stepper_html, build_topbar_html
from ui.theme import COLORS


class UIComponentTests(unittest.TestCase):
    PROJECT_ROOT = Path(__file__).resolve().parents[1]

    def test_sidebar_outline_highlights_requested_decision_stage(self):
        html = build_sidebar_outline_html("decision", "results", "zh")

        self.assertIn(
            '<div class="pm-sidebar-outline is-active">结果分析</div>',
            html,
        )
        self.assertNotIn(
            '<div class="pm-sidebar-outline is-active">数据输入</div>',
            html,
        )

    def test_sidebar_outline_defaults_to_input_stage(self):
        html = build_sidebar_outline_html("decision", None, "zh")

        self.assertIn(
            '<div class="pm-sidebar-outline is-active">数据输入</div>',
            html,
        )

    def test_page_links_are_relative_to_streamlit_entrypoint(self):
        self.assertEqual(
            components.PAGE_PATHS,
            {
                "decision": "决策主页面.py",
                "station": "pages/1_🗄️_电站档案.py",
            },
        )

    def test_topbar_contains_redoxbid_brand_station_and_status(self):
        html = build_topbar_html("演示电站", "系统正常")
        self.assertIn('<span class="pm-product">RedoxBid</span>', html)
        self.assertIn("演示电站", html)
        self.assertIn("系统正常", html)

    def test_topbar_escapes_external_station_text(self):
        html = build_topbar_html("<script>alert(1)</script>", "系统正常")
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_topbar_localizes_the_known_station_in_english(self):
        with patch.object(i18n.st, "session_state", {"language": "en"}):
            html = build_topbar_html(
                "三峡能源新疆吉木萨尔全钒液流储能电站",
                "System normal",
            )

        self.assertIn(
            "China Three Gorges Renewables Xinjiang Jimusaer All-Vanadium "
            "Redox Flow Battery Energy Storage Station",
            html,
        )
        self.assertNotIn("三峡能源新疆吉木萨尔全钒液流储能电站", html)

    def test_bid_table_localizes_headers_types_and_notes_in_english(self):
        source = pd.DataFrame(
            {
                "时间点": ["00:00-00:15"] * 7,
                "申报类型": ["充电", "放电", "静置", "静置", "静置", "充电", "放电"],
                "申报功率 (MW)": ["-10.00", "10.00", "0.00", "0.00", "0.00", "-5.00", "5.00"],
                "预测电价 (元/MWh)": ["100.00"] * 7,
                "预期收益/成本 (元)": ["0.00"] * 7,
                "备注": [
                    "充电效率: 86.6%",
                    "放电效率: 86.6%",
                    "无充放电操作",
                    "无任何申报",
                    "模型求解失败，无充放电操作",
                    "保守报价，确保基础成交",
                    "激进报价，捕捉尖峰价格",
                ],
            }
        )

        localized = i18n.localize_bid_table(source, "en")

        self.assertEqual(
            list(localized.columns),
            [
                "Time Slot",
                "Bid Type",
                "Bid Power (MW)",
                "Forecast Price (CNY/MWh)",
                "Expected Revenue/Cost (CNY)",
                "Notes",
            ],
        )
        self.assertEqual(
            localized["Bid Type"].tolist(),
            ["Charge", "Discharge", "Idle", "Idle", "Idle", "Charge", "Discharge"],
        )
        self.assertEqual(
            localized["Notes"].tolist(),
            [
                "Charging efficiency: 86.6%",
                "Discharging efficiency: 86.6%",
                "No charging or discharging action",
                "No bid submitted",
                "Model solve failed; no charging or discharging action",
                "Conservative bid to improve base clearing probability",
                "Aggressive bid to capture price spikes",
            ],
        )
        self.assertIsNot(localized, source)
        self.assertIn("申报类型", source.columns)

    def test_bid_table_localizes_segmented_schema_in_english(self):
        source = pd.DataFrame(
            {
                "时间点": ["00:00-00:15", "00:15-00:30"],
                "申报类型": ["充电", "放电"],
                "功率段 (MW)": ["-5.0 ~ 0.0", "0.0 ~ 5.0"],
                "报价 (元/MWh)": ["120.00", "180.00"],
                "备注": ["核心报价，围绕预测边际价", "激进报价，仅在电价极低时成交"],
            }
        )

        localized = i18n.localize_bid_table(source, "en")

        self.assertEqual(
            list(localized.columns),
            ["Time Slot", "Bid Type", "Power Segment (MW)", "Bid Price (CNY/MWh)", "Notes"],
        )
        self.assertEqual(
            localized["Notes"].tolist(),
            [
                "Core bid around the forecast marginal price",
                "Aggressive bid that clears only at very low prices",
            ],
        )

    def test_bid_table_remains_unchanged_in_chinese(self):
        source = pd.DataFrame(
            {
                "时间点": ["00:00-00:15"],
                "申报类型": ["充电"],
                "备注": ["充电效率: 86.6%"],
            }
        )

        localized = i18n.localize_bid_table(source, "zh")

        pd.testing.assert_frame_equal(localized, source)
        self.assertIsNot(localized, source)

    def test_stepper_supports_a_six_stage_workflow(self):
        html = build_stepper_html(4, [f"Stage {index}" for index in range(1, 7)])

        self.assertIn("--pm-step-count:6", html)
        self.assertEqual(html.count('class="pm-step'), 7)
        self.assertIn('class="pm-step is-current"', html)

    def test_theme_uses_light_surfaces(self):
        self.assertEqual(COLORS["page"], "#F3F2EF")
        self.assertEqual(COLORS["surface"], "#FFFFFF")
        self.assertEqual(COLORS["accent"], "#2858D6")

    def test_native_streamlit_theme_matches_runtime_palette(self):
        config_path = self.PROJECT_ROOT / ".streamlit" / "config.toml"

        config = tomllib.loads(config_path.read_text(encoding="utf-8"))

        self.assertEqual(config["theme"]["base"], "light")
        self.assertEqual(config["theme"]["primaryColor"], COLORS["accent"])
        self.assertEqual(config["theme"]["backgroundColor"], COLORS["page"])
        self.assertEqual(
            config["theme"]["secondaryBackgroundColor"],
            COLORS["surface_muted"],
        )
        self.assertEqual(config["theme"]["textColor"], COLORS["text"])
        self.assertEqual(
            config["theme"]["sidebar"]["backgroundColor"],
            COLORS["surface_muted"],
        )

    def test_pages_inject_theme_before_heavy_imports(self):
        page_paths = [
            self.PROJECT_ROOT / "app" / "决策主页面.py",
            self.PROJECT_ROOT / "app" / "pages" / "1_🗄️_电站档案.py",
        ]

        for page_path in page_paths:
            source = page_path.read_text(encoding="utf-8")
            with self.subTest(page=page_path.name):
                first_heavy_import = min(
                    source.index("import pandas"),
                    source.index("import plotly"),
                )
                self.assertLess(source.index("st.set_page_config("), first_heavy_import)
                self.assertLess(source.index("inject_theme()"), first_heavy_import)
                self.assertEqual(source.count("st.set_page_config("), 1)
                self.assertEqual(source.count("inject_theme()"), 1)

    def test_native_navigation_css_hides_streamlit_generated_links(self):
        build_css = getattr(theme, "build_native_navigation_css", lambda: "")

        css = build_css()

        self.assertIn('[data-testid="stSidebarNav"]', css)
        self.assertIn("display: none", css)

    def test_sidebar_layout_css_moves_the_content_toward_the_top(self):
        css = theme.build_native_navigation_css()

        self.assertIn('[data-testid="stSidebarContent"]', css)
        self.assertIn("padding-top: 1.25rem", css)
        self.assertIn('[data-testid="stSidebarUserContent"]', css)
        self.assertIn("padding-top: 0", css)
        self.assertIn("margin-top: -2rem", css)


if __name__ == "__main__":
    unittest.main()
