"""Shared visual theme for the formal RedoxBid interface."""

from __future__ import annotations

import streamlit as st


COLORS = {
    "page": "#F3F2EF",
    "surface": "#FFFFFF",
    "surface_muted": "#F7F7F5",
    "text": "#18202A",
    "muted": "#73777D",
    "stroke": "#D9DADD",
    "accent": "#2858D6",
    "accent_soft": "#E8EDF9",
    "success": "#4F8D6D",
    "warning": "#B8753C",
    "danger": "#B65454",
}


def build_native_navigation_css() -> str:
    """Style Streamlit's sidebar shell for the product navigation."""
    return """
        [data-testid="stSidebarNav"] {
            display: none;
        }
        [data-testid="stSidebarContent"] {
            padding-top: 1.25rem;
        }
        [data-testid="stSidebarUserContent"] {
            padding-top: 0;
            margin-top: -2rem;
        }
    """


def inject_theme() -> None:
    """Inject the light, low-noise Streamlit theme."""
    st.markdown(
        f"""
        <style>
        {build_native_navigation_css()}
        :root {{
            --pm-page: {COLORS["page"]};
            --pm-surface: {COLORS["surface"]};
            --pm-surface-muted: {COLORS["surface_muted"]};
            --pm-text: {COLORS["text"]};
            --pm-muted: {COLORS["muted"]};
            --pm-stroke: {COLORS["stroke"]};
            --pm-accent: {COLORS["accent"]};
            --pm-accent-soft: {COLORS["accent_soft"]};
            --pm-success: {COLORS["success"]};
        }}
        .stApp {{
            background: var(--pm-page);
            color: var(--pm-text);
        }}
        [data-testid="stHeader"] {{
            background: transparent;
        }}
        [data-testid="stToolbar"] {{
            right: 1rem;
        }}
        [data-testid="stSidebar"] {{
            background: var(--pm-surface-muted);
            border-right: 1px solid var(--pm-stroke);
        }}
        .block-container {{
            max-width: 1440px;
            padding-top: 1.15rem;
            padding-bottom: 3rem;
        }}
        h1, h2, h3 {{
            color: var(--pm-text);
            letter-spacing: -0.025em;
        }}
        h1 {{
            font-size: clamp(1.9rem, 3vw, 2.55rem);
            font-weight: 720;
        }}
        h2 {{
            font-size: 1.35rem;
            font-weight: 700;
        }}
        p, label, [data-testid="stCaptionContainer"] {{
            color: var(--pm-muted);
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: var(--pm-surface);
            border-color: var(--pm-stroke);
            border-radius: 0.8rem;
        }}
        div[data-testid="stMetric"] {{
            background: transparent;
            border-right: 1px solid var(--pm-stroke);
            padding: 0.35rem 1rem 0.35rem 0;
        }}
        div[data-testid="stMetric"]:last-child {{
            border-right: 0;
        }}
        div[data-testid="stMetricLabel"] {{
            color: var(--pm-muted);
        }}
        div[data-testid="stMetricValue"] {{
            color: var(--pm-text);
            font-weight: 680;
            letter-spacing: -0.03em;
        }}
        .stButton > button,
        .stDownloadButton > button,
        [data-testid="stFormSubmitButton"] > button {{
            background: var(--pm-surface);
            color: var(--pm-text);
            border-radius: 0.55rem;
            border: 1px solid var(--pm-stroke);
            box-shadow: none;
            font-weight: 650;
        }}
        .stButton > button p,
        .stDownloadButton > button p,
        [data-testid="stPopover"] button p {{
            color: var(--pm-text);
        }}
        [data-testid="stPopover"] button {{
            background: var(--pm-surface);
            color: var(--pm-text);
            border-color: var(--pm-stroke);
        }}
        [data-testid="stSegmentedControl"] button {{
            background: var(--pm-surface);
            color: var(--pm-text);
        }}
        [data-testid="stSegmentedControl"] button p {{
            color: inherit;
        }}
        [data-testid="stSegmentedControl"] button[aria-pressed="true"] {{
            background: var(--pm-accent-soft);
            color: var(--pm-accent);
            border-color: var(--pm-accent);
        }}
        button[data-testid="stBaseButton-segmented_control"],
        button[data-testid="stPopoverButton"],
        button[data-testid="stBaseButton-secondary"] {{
            background: var(--pm-surface) !important;
            color: var(--pm-text) !important;
            border-color: var(--pm-stroke) !important;
        }}
        button[data-testid="stBaseButton-segmented_controlActive"] {{
            background: var(--pm-accent-soft) !important;
            color: var(--pm-accent) !important;
            border-color: var(--pm-accent) !important;
        }}
        button[data-testid="stBaseButton-segmented_control"] p,
        button[data-testid="stBaseButton-segmented_controlActive"] p,
        button[data-testid="stPopoverButton"] p,
        button[data-testid="stBaseButton-secondary"] p {{
            color: inherit !important;
        }}
        .stButton > button[kind="primary"],
        [data-testid="stFormSubmitButton"] > button[kind="primary"] {{
            background: var(--pm-accent);
            border-color: var(--pm-accent);
            color: #FFFFFF;
        }}
        
        .stButton > button[kind="primary"] p,
        [data-testid="stFormSubmitButton"] > button[kind="primary"] p {{
            color: #FFFFFF;
        }}
        .stTextInput input,
        .stNumberInput input,
        .stDateInput input,
        [data-baseweb="select"] > div {{
            background: var(--pm-surface);
            border-color: var(--pm-stroke);
            border-radius: 0.5rem;
        }}
        [data-testid="stFileUploaderDropzone"] {{
            background: var(--pm-surface-muted);
            border-color: #BFC3C8;
            border-radius: 0.75rem;
        }}
        [data-testid="stDataFrame"] {{
            border: 1px solid var(--pm-stroke);
            border-radius: 0.7rem;
            overflow: hidden;
        }}
        [data-baseweb="tab-list"] {{
            gap: 0.25rem;
            border-bottom: 1px solid var(--pm-stroke);
        }}
        [data-baseweb="tab"] {{
            border-radius: 0.45rem 0.45rem 0 0;
        }}
        .pm-topbar {{
            display: flex;
            align-items: center;
            gap: 0.7rem;
            min-height: 2.8rem;
        }}
        .pm-mark {{
            width: 1.7rem;
            height: 1.7rem;
            display: inline-grid;
            place-items: center;
            border-radius: 0.45rem;
            background: var(--pm-accent);
            color: white;
            font-weight: 800;
            font-size: 0.82rem;
        }}
        .pm-product {{
            color: var(--pm-text);
            font-weight: 750;
            font-size: 1.5rem;
        }}
        .pm-station {{
            color: var(--pm-muted);
            font-size: 1.1rem;
        }}
        .pm-status {{
            color: var(--pm-success);
            font-size: 0.75rem;
            margin-left: auto;
        }}
        .pm-status::before {{
            content: "";
            display: inline-block;
            width: 0.43rem;
            height: 0.43rem;
            margin-right: 0.35rem;
            border-radius: 50%;
            background: var(--pm-success);
        }}
        .pm-eyebrow {{
            color: var(--pm-muted);
            font-size: 0.72rem;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            margin-bottom: 0.4rem;
        }}
        .pm-stepper {{
            display: grid;
            grid-template-columns: repeat(var(--pm-step-count, 4), minmax(0, 1fr));
            overflow: hidden;
            border: 1px solid var(--pm-stroke);
            border-radius: 0.7rem;
            background: var(--pm-surface);
            margin: 1rem 0 1.25rem;
        }}
        .pm-step {{
            padding: 0.72rem 0.85rem;
            border-right: 1px solid var(--pm-stroke);
            color: var(--pm-muted);
            font-size: 0.78rem;
        }}
        .pm-step:last-child {{
            border-right: 0;
        }}
        .pm-step strong {{
            display: block;
            margin-top: 0.16rem;
            color: var(--pm-text);
        }}
        .pm-step.is-current {{
            background: var(--pm-accent-soft);
        }}
        .pm-step.is-current strong {{
            color: var(--pm-accent);
        }}
        .pm-section-label {{
            margin: 0.35rem 0 0.85rem;
            color: var(--pm-text);
            font-weight: 690;
            font-size: 1rem;
        }}
        .pm-sidebar-brand {{
            margin: 0 0.5rem 1.2rem;
            color: var(--pm-accent);
            font-weight: 780;
            letter-spacing: -0.02em;
        }}
        .pm-sidebar-group {{
            margin: 1.15rem 0.5rem 0.4rem;
            color: #989CA2;
            font-size: 0.66rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }}
        .pm-sidebar-outline {{
            margin: 0.2rem 0.5rem;
            padding: 0.36rem 0.55rem;
            color: var(--pm-muted);
            font-size: 0.78rem;
            border-left: 2px solid transparent;
        }}
        .pm-sidebar-outline.is-active {{
            color: var(--pm-accent);
            border-left-color: var(--pm-accent);
            background: var(--pm-accent-soft);
            border-radius: 0 0.35rem 0.35rem 0;
        }}
        @media (max-width: 900px) {{
            .block-container {{
                padding-left: 1rem;
                padding-right: 1rem;
            }}
            .pm-stepper {{
                grid-template-columns: 1fr 1fr;
            }}
            .pm-step:nth-child(2) {{
                border-right: 0;
            }}
            .pm-step:nth-child(-n+2) {{
                border-bottom: 1px solid var(--pm-stroke);
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_plotly_theme(fig, language: str):
    """Apply display-only styling and localization to a Plotly figure."""
    trace_labels = {
        "zh": {
            "充电功率": "充电功率",
            "放电功率": "放电功率",
            "电价": "电价",
            "SOC": "SOC",
        },
        "en": {
            "充电功率": "Charging Power",
            "放电功率": "Discharging Power",
            "电价": "Price",
            "SOC": "SOC",
        },
    }
    palette = {
        "充电功率": ("rgba(79,141,109,0.46)", COLORS["success"]),
        "放电功率": ("rgba(184,117,60,0.42)", COLORS["warning"]),
        "电价": ("rgba(40,88,214,0.12)", COLORS["accent"]),
        "SOC": ("rgba(91,99,112,0.12)", "#5B6370"),
    }
    selected_labels = trace_labels.get(language, trace_labels["zh"])

    for trace in fig.data:
        original_name = trace.name
        if original_name in selected_labels:
            trace.name = selected_labels[original_name]
        if original_name in palette:
            fill_color, line_color = palette[original_name]
            if hasattr(trace, "fillcolor"):
                trace.fillcolor = fill_color
            if hasattr(trace, "line"):
                trace.line.color = line_color

    existing_title = getattr(getattr(fig.layout, "title", None), "text", None)
    title = existing_title or (
        "储能电站日前市场联合优化策略"
        if language == "zh"
        else "Day-ahead Market Dispatch Strategy"
    )
    fig.update_layout(
        title={"text": title, "x": 0.0, "xanchor": "left"},
        template="plotly_white",
        paper_bgcolor=COLORS["surface"],
        plot_bgcolor=COLORS["surface"],
        font={"family": "Arial, Microsoft YaHei, sans-serif", "color": COLORS["text"]},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
        hovermode="x unified",
        margin={"l": 56, "r": 42, "t": 82, "b": 58},
    )
    fig.update_xaxes(gridcolor="#ECECEA", zerolinecolor="#D9DADD")
    fig.update_yaxes(gridcolor="#ECECEA", zerolinecolor="#D9DADD")

    if language == "en":
        annotation_map = {
            "<b>市场价格与储能功率调度</b>": "<b>Market Price and Battery Dispatch</b>",
            "<b>电池荷电状态 (SOC)</b>": "<b>State of Charge (SOC)</b>",
        }
        for annotation in fig.layout.annotations or ():
            if annotation.text in annotation_map:
                annotation.text = annotation_map[annotation.text]
        axis_titles = {
            "yaxis": "<b>Price (CNY/MWh)</b>",
            "yaxis2": "<b>Power (MW)</b>",
            "yaxis3": "<b>State of Charge (SOC)</b>",
            "xaxis2": "<b>Time</b>",
        }
        for axis_name, title_text in axis_titles.items():
            axis = getattr(fig.layout, axis_name, None)
            if axis is not None and axis.title:
                axis.title.text = title_text

    return fig
