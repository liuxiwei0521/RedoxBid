"""Reusable Streamlit presentation components."""

from __future__ import annotations

from html import escape

import streamlit as st

from .i18n import get_language, localize_station_name, render_language_switcher, t


PAGE_PATHS = {
    "decision": "决策主页面.py",
    "station": "pages/1_🗄️_电站档案.py",
}


def build_topbar_html(station_name: str, status_text: str) -> str:
    """Build safe product identity markup for the page header."""
    safe_station = escape(localize_station_name(station_name))
    safe_status = escape(str(status_text))
    return (
        '<div class="pm-topbar">'
        # '<span class="pm-mark">R</span>'
        '<span class="pm-product">RedoxBid</span>'
        f'<span class="pm-station">{safe_station}</span>'
        f'<span class="pm-status">{safe_status}</span>'
        "</div>"
    )


def render_topbar(station_name: str, status_text: str) -> None:
    """Render product identity, station status and language control."""
    identity, language = st.columns([7.6, 1.4], vertical_alignment="center")
    with identity:
        st.markdown(
            build_topbar_html(station_name, status_text),
            unsafe_allow_html=True,
        )
    with language:
        render_language_switcher()
    st.divider()


def build_sidebar_outline_html(
    active_page: str,
    active_section: str | None,
    language: str,
) -> str:
    """Build the page outline with exactly one state-driven active item."""
    if active_page == "decision":
        sections = [
            ("input", "nav.input"),
            ("parameters", "nav.parameters"),
            ("results", "nav.results"),
            ("bid", "nav.bid"),
        ]
    else:
        sections = [
            ("basic", "profile.basic"),
            ("history", "nav.history"),
        ]

    valid_sections = {section for section, _ in sections}
    selected = active_section if active_section in valid_sections else sections[0][0]
    return "".join(
        f'<div class="pm-sidebar-outline'
        f'{" is-active" if section == selected else ""}">'
        f'{escape(t(label_key, language))}</div>'
        for section, label_key in sections
    )


def render_sidebar(active_page: str, active_section: str | None = None) -> None:
    """Render the two formal page links and the current-page outline."""
    with st.sidebar:
        st.markdown(
            '<div class="pm-sidebar-brand">RedoxBid</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="pm-sidebar-group">{escape(t("nav.workspace"))}</div>',
            unsafe_allow_html=True,
        )
        st.page_link(PAGE_PATHS["decision"], label=t("nav.decision"))
        st.page_link(PAGE_PATHS["station"], label=t("nav.station"))

        st.markdown(
            f'<div class="pm-sidebar-group">{escape(t("nav.station_group"))}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            build_sidebar_outline_html(
                active_page,
                active_section,
                get_language(),
            ),
            unsafe_allow_html=True,
        )


def build_stepper_html(current_step: int, steps: list[str]) -> str:
    """Build a responsive workflow stepper for any practical stage count."""
    if not steps:
        raise ValueError("steps must not be empty")
    items = []
    for index, label in enumerate(steps, start=1):
        current_class = " is-current" if index == current_step else ""
        items.append(
            f'<div class="pm-step{current_class}">'
            f"<span>{index:02d}</span>"
            f"<strong>{escape(label)}</strong>"
            "</div>"
        )
    return (
        f'<div class="pm-stepper" style="--pm-step-count:{len(steps)}">'
        + "".join(items)
        + "</div>"
    )


def render_stepper(current_step: int, steps: list[str]) -> None:
    """Render a state-driven decision workflow."""
    st.markdown(build_stepper_html(current_step, steps), unsafe_allow_html=True)


def render_metric_strip(
    items: list[tuple[str, str, str | None]],
) -> None:
    """Render a consistent horizontal KPI strip."""
    columns = st.columns(len(items))
    for column, (label, value, delta) in zip(columns, items):
        column.metric(label, value, delta=delta)
