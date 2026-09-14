"""Shared presentation components for RedoxBid."""

from .components import (
    build_topbar_html,
    render_metric_strip,
    render_sidebar,
    render_stepper,
    render_topbar,
)
from .i18n import (
    get_language,
    localize_bid_table,
    localize_station_name,
    render_language_switcher,
    set_language,
    t,
)
from .theme import COLORS, apply_plotly_theme, inject_theme

__all__ = [
    "apply_plotly_theme",
    "COLORS",
    "build_topbar_html",
    "get_language",
    "inject_theme",
    "localize_bid_table",
    "localize_station_name",
    "render_language_switcher",
    "render_metric_strip",
    "render_sidebar",
    "render_stepper",
    "render_topbar",
    "set_language",
    "t",
]
