"""Utility functions and styling configurations for TrainOps Intelligence.

Contains enterprise UI themes, custom CSS generators, and Plotly visualization builders
standardized to navy/blue corporate palettes with high-contrast, crystal-clear typography.
"""

from typing import Dict, List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Color Theme Tokens
NAVY = "#1B365D"
DARK_NAVY = "#0F2038"
ACCENT_BLUE = "#006699"
SKY_BLUE = "#3388CC"
LIGHT_BG = "#F8FAFC"
CARD_BG = "#FFFFFF"
BORDER_COLOR = "#E2E8F0"
TEXT_PRIMARY = "#0F172A"       # Deep slate black for ultra-crisp readability
TEXT_SECONDARY = "#334155"     # Dark slate gray for subheaders and captions
SUCCESS_GREEN = "#16A34A"
WARNING_AMBER = "#D97706"
DANGER_RED = "#DC2626"

ENTERPRISE_PALETTE = [
    "#1B365D", "#006699", "#2B6CB0", "#3182CE",
    "#4299E1", "#63B3ED", "#90CDF4", "#BEE3F8"
]


def get_custom_css() -> str:
    """Return enterprise CSS for Streamlit with explicit high-contrast typography."""
    return f"""
    <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"], .stApp {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: {TEXT_PRIMARY} !important;
            background-color: {LIGHT_BG} !important;
        }}

        /* General Typography & Headers */
        h1, h2, h3, h4, h5, h6 {{
            color: {DARK_NAVY} !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em;
        }}

        p, span, label, div {{
            color: {TEXT_PRIMARY};
        }}

        /* Force high contrast for all widget labels */
        [data-testid="stWidgetLabel"] label,
        [data-testid="stWidgetLabel"] p,
        label[data-testid="stWidgetLabel"] {{
            color: {TEXT_PRIMARY} !important;
            font-weight: 600 !important;
            font-size: 0.88rem !important;
            opacity: 1.0 !important;
        }}

        /* Sidebar Styling */
        [data-testid="stSidebar"] {{
            background-color: #FFFFFF !important;
            border-right: 1px solid {BORDER_COLOR} !important;
        }}

        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span {{
            color: #0F172A !important;
        }}

        /* Radio Buttons in Sidebar */
        [data-testid="stSidebar"] div[role="radiogroup"] label {{
            color: #0F172A !important;
            cursor: pointer;
        }}

        [data-testid="stSidebar"] div[role="radiogroup"] label div p,
        [data-testid="stSidebar"] div[role="radiogroup"] label span {{
            color: #0F172A !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
        }}

        /* All Input Labels */
        [data-testid="stWidgetLabel"] label,
        [data-testid="stWidgetLabel"] p,
        label[data-testid="stWidgetLabel"],
        .stSelectbox label,
        .stMultiSelect label,
        .stDateInput label,
        .stTextInput label {{
            color: #0F172A !important;
            font-weight: 700 !important;
            font-size: 0.88rem !important;
            opacity: 1.0 !important;
        }}

        /* Inputs & Dropdowns */
        div[data-baseweb="select"] > div {{
            background-color: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 6px !important;
        }}

        div[data-baseweb="select"] input {{
            color: #0F172A !important;
        }}

        /* MultiSelect Pill Tags */
        [data-baseweb="tag"] {{
            background-color: #E2E8F0 !important;
            border: 1px solid #94A3B8 !important;
            border-radius: 4px !important;
        }}

        [data-baseweb="tag"] span {{
            color: #0F172A !important;
            font-weight: 600 !important;
        }}

        [data-baseweb="tag"] svg {{
            fill: #0F172A !important;
        }}

        /* Date Input & Text Input */
        .stDateInput input,
        .stTextInput input {{
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
        }}

        /* Expander Title */
        [data-testid="stExpander"] summary span {{
            color: {TEXT_PRIMARY} !important;
            font-weight: 600 !important;
        }}

        /* KPI Card Styling */
        .kpi-card {{
            background-color: {CARD_BG};
            border: 1px solid {BORDER_COLOR};
            border-radius: 8px;
            padding: 16px 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            transition: all 0.2s ease-in-out;
            height: 100%;
        }}
        .kpi-card:hover {{
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08);
            border-color: {ACCENT_BLUE};
        }}
        .kpi-title {{
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: {TEXT_SECONDARY};
            font-weight: 700;
            margin-bottom: 6px;
        }}
        .kpi-value {{
            font-size: 1.85rem;
            font-weight: 700;
            color: {DARK_NAVY};
            line-height: 1.1;
            margin-bottom: 6px;
        }}
        .kpi-subtitle {{
            font-size: 0.82rem;
            color: {TEXT_SECONDARY};
            font-weight: 500;
        }}
        .kpi-badge-good {{
            color: {SUCCESS_GREEN} !important;
            font-weight: 600;
        }}
        .kpi-badge-alert {{
            color: {DANGER_RED} !important;
            font-weight: 600;
        }}

        /* Section Container */
        .section-box {{
            background-color: {CARD_BG};
            border: 1px solid {BORDER_COLOR};
            border-radius: 8px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            color: {TEXT_PRIMARY};
        }}

        /* Dataframe Table styling */
        .stDataFrame {{
            border: 1px solid {BORDER_COLOR};
            border-radius: 6px;
        }}

        /* Tab styling */
        button[data-baseweb="tab"] {{
            font-size: 0.95rem;
            font-weight: 600;
            color: {TEXT_SECONDARY} !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            color: {NAVY} !important;
            border-bottom-color: {NAVY} !important;
        }}

        /* Buttons */
        .stButton button {{
            border-radius: 6px;
            font-weight: 600;
            transition: all 0.15s ease;
        }}
        .stButton button[kind="primary"] {{
            background-color: {NAVY} !important;
            border-color: {NAVY} !important;
            color: #FFFFFF !important;
        }}
        .stButton button[kind="primary"]:hover {{
            background-color: {ACCENT_BLUE} !important;
            border-color: {ACCENT_BLUE} !important;
        }}

        /* Alert and callout boxes */
        .callout-info {{
            background-color: #EFF6FF;
            border-left: 4px solid {ACCENT_BLUE};
            padding: 12px 16px;
            border-radius: 4px;
            margin-bottom: 16px;
            font-size: 0.92rem;
            color: #1E3A8A !important;
            font-weight: 500;
        }}
        .callout-info b {{
            color: #0F172A !important;
        }}
    </style>
    """


def create_kpi_card_html(
    title: str,
    value: str,
    subtitle: str = "",
    badge_type: str = "neutral"
) -> str:
    """Generate HTML for an executive KPI card."""
    badge_class = "kpi-subtitle"
    if badge_type == "good":
        badge_class += " kpi-badge-good"
    elif badge_type == "alert":
        badge_class += " kpi-badge-alert"

    return f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="{badge_class}">{subtitle}</div>
    </div>
    """


def format_chart_layout(fig: go.Figure, title: str = "", height: int = 380) -> go.Figure:
    """Apply uniform corporate styling to Plotly figures with high-contrast text."""
    fig.update_layout(
        title={
            "text": title,
            "font": {"size": 15, "color": DARK_NAVY, "family": "Inter, sans-serif"},
            "x": 0.0,
            "xanchor": "left"
        },
        template="plotly_white",
        paper_bgcolor=CARD_BG,
        plot_bgcolor=CARD_BG,
        font={"family": "Inter, sans-serif", "color": TEXT_PRIMARY, "size": 12},
        height=height,
        margin={"l": 40, "r": 20, "t": 50, "b": 40},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1.0,
            "font": {"color": TEXT_PRIMARY, "size": 11, "family": "Inter, sans-serif"}
        },
        hoverlabel={"bgcolor": DARK_NAVY, "font_color": "#FFFFFF", "font_size": 12}
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="#F1F5F9",
        linecolor="#CBD5E1",
        tickfont={"color": TEXT_PRIMARY, "size": 11, "family": "Inter, sans-serif"},
        title_font={"color": DARK_NAVY, "size": 12, "family": "Inter, sans-serif"}
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#F1F5F9",
        linecolor="#CBD5E1",
        tickfont={"color": TEXT_PRIMARY, "size": 11, "family": "Inter, sans-serif"},
        title_font={"color": DARK_NAVY, "size": 12, "family": "Inter, sans-serif"}
    )
    return fig
