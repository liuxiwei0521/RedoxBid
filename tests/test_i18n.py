import unittest
from unittest.mock import patch

from ui import i18n
from ui.i18n import TRANSLATIONS, t


REQUIRED_KEYS = {
    "app.title",
    "app.subtitle",
    "nav.decision",
    "nav.station",
    "nav.input",
    "nav.parameters",
    "nav.results",
    "nav.bid",
    "nav.history",
    "status.system_normal",
    "status.interval_count",
    "stage.input",
    "stage.baseline",
    "stage.rarr",
    "stage.output",
    "action.parameters",
    "action.solve",
    "action.download_details",
    "action.download_bid",
    "field.solver",
    "field.time_horizon",
    "field.time_step",
    "field.price_csv",
    "field.e_rated",
    "field.p_rated",
    "field.initial_soc",
    "field.e_0",
    "field.e_t_target",
    "field.eta_charge",
    "field.eta_discharge",
    "field.soc_min",
    "field.soc_max",
    "field.k",
    "field.n_cycle_max",
    "field.c_om",
    "field.r_ramp",
    "result.net_profit",
    "result.discharge_revenue",
    "result.cycles",
    "result.throughput",
    "result.avg_profit",
    "result.schedule",
    "result.bid_strategy",
    "mode.quantity_only",
    "mode.quantity_price",
    "profile.title",
    "profile.station_name",
    "profile.location",
    "profile.commission_date",
    "profile.e_rated",
    "profile.p_rated",
    "profile.edit_title",
    "profile.save_success",
    "history.title",
    "history.total_profit",
    "history.total_cycles",
    "history.avg_profit",
    "history.run_time",
    "history.net_profit_axis",
    "history.no_date",
    "error.import",
    "error.solve",
    "error.workflow",
}


class TranslationTests(unittest.TestCase):
    def test_language_defaults_to_english_for_a_new_session(self):
        with patch.object(i18n.st, "session_state", {}):
            self.assertEqual(i18n.get_language(), "en")

    def test_language_switcher_widget_state_takes_precedence(self):
        with patch.object(
            i18n.st,
            "session_state",
            {"language": "zh", "language_switcher": "EN"},
        ):
            self.assertEqual(i18n.get_language(), "en")

    def test_chinese_switcher_value_selects_chinese(self):
        with patch.object(
            i18n.st,
            "session_state",
            {"language": "en", "language_switcher": "中文"},
        ):
            self.assertEqual(i18n.get_language(), "zh")

    def test_both_languages_cover_required_ui_keys(self):
        self.assertTrue(REQUIRED_KEYS <= TRANSLATIONS["zh"].keys())
        self.assertTrue(REQUIRED_KEYS <= TRANSLATIONS["en"].keys())

    def test_chinese_and_english_labels(self):
        self.assertEqual(t("nav.decision", "zh"), "日前决策")
        self.assertEqual(t("nav.decision", "en"), "Day-ahead Decision")

    def test_format_parameters(self):
        self.assertEqual(
            t("status.interval_count", "en", count=96),
            "96 intervals",
        )

    def test_baseline_stage_uses_selected_solver_name(self):
        self.assertEqual(
            t("stage.baseline", "zh", solver="HiGHS"),
            "HiGHS 基准求解",
        )
        self.assertEqual(
            t("stage.baseline", "en", solver="Gurobi"),
            "Gurobi Baseline Solve",
        )

    def test_jimusaer_station_name_is_localized_for_display(self):
        localize_station_name = getattr(
            i18n,
            "localize_station_name",
            lambda station_name, language: station_name,
        )
        chinese_name = "三峡能源新疆吉木萨尔全钒液流储能电站"
        english_name = (
            "China Three Gorges Renewables Xinjiang Jimusaer All-Vanadium "
            "Redox Flow Battery Energy Storage Station"
        )

        self.assertEqual(localize_station_name(chinese_name, "en"), english_name)
        self.assertEqual(localize_station_name(chinese_name, "zh"), chinese_name)

    def test_unknown_station_name_is_not_rewritten(self):
        localize_station_name = getattr(
            i18n,
            "localize_station_name",
            lambda station_name, language: station_name,
        )

        self.assertEqual(
            localize_station_name("用户自定义电站", "en"),
            "用户自定义电站",
        )

    def test_missing_english_key_falls_back_to_chinese(self):
        original = TRANSLATIONS["en"].pop("test.fallback", None)
        TRANSLATIONS["zh"]["test.fallback"] = "回退文本"
        try:
            self.assertEqual(t("test.fallback", "en"), "回退文本")
        finally:
            TRANSLATIONS["zh"].pop("test.fallback", None)
            if original is not None:
                TRANSLATIONS["en"]["test.fallback"] = original


if __name__ == "__main__":
    unittest.main()
