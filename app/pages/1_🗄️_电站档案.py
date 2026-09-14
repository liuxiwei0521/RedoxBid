import os
import sys

import streamlit as st


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ui import inject_theme


st.set_page_config(
    page_title="RedoxBid",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_theme()

from datetime import datetime

import pandas as pd
import plotly.graph_objects as go


try:
    from ui import (
        COLORS,
        apply_plotly_theme,
        get_language,
        localize_station_name,
        render_metric_strip,
        render_sidebar,
        render_topbar,
        t,
    )
    from utils.database import (
        init_db,
        load_decision_records,
        load_station_profile,
        save_station_profile,
    )
except ImportError as error:
    st.error(f"无法导入项目模块: {error}")
    st.stop()


def display_profile_form(profile):
    """Render the editable station profile without changing its data contract."""
    with st.form(key="profile_form"):
        st.markdown(
            f'<div class="pm-section-label">{t("profile.edit_title")}</div>',
            unsafe_allow_html=True,
        )
        edited_profile = {}
        col1, col2 = st.columns(2)
        with col1:
            edited_profile["station_name"] = st.text_input(
                t("profile.station_name"),
                value=profile.get("station_name") or "",
                key="profile_station_name",
            )
            edited_profile["e_rated"] = st.number_input(
                t("profile.e_rated"),
                min_value=1.0,
                value=float(profile.get("e_rated", 100.0)),
                format="%.1f",
                key="profile_e_rated",
            )
        with col2:
            edited_profile["location"] = st.text_input(
                t("profile.location"),
                value=profile.get("location") or "",
                key="profile_location",
            )
            edited_profile["p_rated"] = st.number_input(
                t("profile.p_rated"),
                min_value=1.0,
                value=float(profile.get("p_rated", 25.0)),
                format="%.1f",
                key="profile_p_rated",
            )

        try:
            default_date = datetime.strptime(
                profile.get("commission_date"), "%Y-%m-%d"
            ).date()
        except (ValueError, TypeError):
            default_date = datetime.now().date()

        edited_profile["commission_date"] = st.date_input(
            t("profile.commission_date"),
            value=default_date,
            key="profile_commission_date",
        ).strftime("%Y-%m-%d")

        if st.form_submit_button(
            t("action.save_profile"),
            use_container_width=True,
            type="primary",
        ):
            save_station_profile(edited_profile)
            st.success(t("profile.save_success"))
            st.rerun()


def build_history_figures(records_df, language):
    """Build display-only figures from archived decision records."""
    profit_figure = go.Figure()
    profit_figure.add_trace(
        go.Scatter(
            x=pd.to_datetime(records_df["run_timestamp"]),
            y=records_df["net_profit"],
            mode="lines+markers",
            name=t("result.net_profit", language),
            line={"color": COLORS["accent"], "width": 2.5},
            marker={"size": 6},
        )
    )
    profit_figure.update_layout(
        title=t("history.profit_trend", language),
        xaxis_title=t("history.run_time", language),
        yaxis_title=t("history.net_profit_axis", language),
    )
    apply_plotly_theme(profit_figure, language)
    profit_figure.update_layout(
        title={"text": t("history.profit_trend", language), "x": 0}
    )

    mode_counts = records_df["decision_mode"].value_counts()
    mode_labels = list(mode_counts.index)
    if language == "en":
        mode_labels = [
            t("mode.quantity_price", language)
            if value == "报量报价"
            else t("mode.quantity_only", language)
            if value == "报量不报价"
            else value
            for value in mode_labels
        ]
    mode_figure = go.Figure(
        data=[
            go.Pie(
                labels=mode_labels,
                values=mode_counts.values,
                hole=0.58,
                marker={
                    "colors": [
                        COLORS["accent"],
                        COLORS["success"],
                        COLORS["warning"],
                    ]
                },
            )
        ]
    )
    apply_plotly_theme(mode_figure, language)
    mode_figure.update_layout(
        title={"text": t("history.mode_distribution", language), "x": 0},
        showlegend=True,
    )
    return profit_figure, mode_figure


def main():
    init_db()

    profile = load_station_profile() or {}
    render_topbar(
        profile.get("station_name", t("station.unnamed")),
        t("status.system_normal"),
    )
    render_sidebar("station", "basic")
    language = get_language()

    st.markdown(
        '<div class="pm-eyebrow">Station Archive</div>',
        unsafe_allow_html=True,
    )
    st.title(t("profile.title"))
    st.caption(t("profile.subtitle"))

    with st.container(border=True):
        st.subheader(t("profile.basic"))
        if profile:
            render_metric_strip(
                [
                    (
                        t("profile.station_name"),
                        localize_station_name(profile["station_name"], language),
                        None,
                    ),
                    (t("profile.location"), str(profile["location"]), None),
                    (
                        t("profile.commission_date"),
                        str(profile.get("commission_date") or t("history.no_date")),
                        None,
                    ),
                    (t("profile.e_rated"), f'{profile["e_rated"]} MWh', None),
                    (t("profile.p_rated"), f'{profile["p_rated"]} MW', None),
                ]
            )
            with st.expander(t("action.edit_profile")):
                display_profile_form(profile)
        else:
            st.warning(t("profile.missing"))

    st.subheader(t("history.title"))
    records_df = load_decision_records()
    if records_df.empty:
        with st.container(border=True):
            st.info(t("history.empty"))
        return

    total_profit = records_df["net_profit"].sum()
    total_cycles = records_df["equivalent_cycles"].sum()
    average_profit = records_df["net_profit"].mean()
    currency = "元" if language == "zh" else "CNY"
    cycle_unit = "次" if language == "zh" else ""

    with st.container(border=True):
        st.markdown(
            f'<div class="pm-section-label">{t("history.overview")}</div>',
            unsafe_allow_html=True,
        )
        render_metric_strip(
            [
                (t("history.total_profit"), f"{total_profit:,.2f} {currency}", None),
                (
                    t("history.total_cycles"),
                    f"{total_cycles:.2f} {cycle_unit}".strip(),
                    None,
                ),
                (t("history.avg_profit"), f"{average_profit:,.2f} {currency}", None),
            ]
        )

        profit_figure, mode_figure = build_history_figures(records_df, language)
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.plotly_chart(profit_figure, use_container_width=True)
        with chart_col2:
            st.plotly_chart(mode_figure, use_container_width=True)

        with st.expander(t("history.details")):
            display_records = records_df
            if language == "en":
                display_records = records_df.rename(
                    columns={
                        "id": "ID",
                        "run_timestamp": "Run Time",
                        "decision_mode": "Decision Mode",
                        "net_profit": "Net Profit",
                        "total_throughput": "Energy Throughput",
                        "equivalent_cycles": "Equivalent Cycles",
                        "kpis_json": "KPI JSON",
                    }
                )
            st.dataframe(display_records, use_container_width=True)


if __name__ == "__main__":
    main()
