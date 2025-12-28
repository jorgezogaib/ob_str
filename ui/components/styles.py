"""
Shared CSS styles for the STR Investment Model dashboard.

This module provides a centralized location for all custom CSS styling
to avoid duplication across pages.
"""

import streamlit as st


def apply_custom_styles():
    """
    Apply custom CSS styling to the Streamlit dashboard.

    This includes:
    - Monospace font for financial tables
    - Compact KPI cards with reduced padding
    - Tighter spacing between sections
    - Streamlined form elements
    - Dark mode compatible styling
    """
    st.markdown("""
    <style>
        /* Financial tables - monospace numbers */
        .dataframe td {
            font-family: 'Courier New', monospace;
        }

        /* Subtle borders */
        .stDataFrame {
            border: 1px solid #333;
        }

        /* Compact KPI cards - reduce padding */
        [data-testid="stMetricValue"] {
            font-family: 'Courier New', monospace;
            font-size: 1.6rem;
            line-height: 1.1;
            padding-top: 0 !important;
        }

        [data-testid="stMetricLabel"] {
            font-size: 0.8rem;
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }

        [data-testid="stMetricDelta"] {
            font-size: 0.75rem;
            margin-top: 0 !important;
        }

        /* Reduce spacing between metric containers */
        [data-testid="metric-container"] {
            padding: 0.25rem 0.5rem !important;
        }

        /* Tighter dividers - CRITICAL */
        hr, [data-testid="stHorizontalBlock"] > div > div > div > hr {
            margin-top: 0.25rem !important;
            margin-bottom: 0.25rem !important;
        }

        /* Reduce spacing between ALL sections */
        .element-container {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }

        /* Block containers */
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
            gap: 0.25rem !important;
        }

        /* Tighter headers */
        h1 {
            margin-top: 0 !important;
            margin-bottom: 0.5rem !important;
            padding-top: 0 !important;
        }

        h2 {
            margin-top: 0.25rem !important;
            margin-bottom: 0.25rem !important;
            padding: 0 !important;
        }

        h3 {
            margin-top: 0 !important;
            margin-bottom: 0.25rem !important;
            padding: 0 !important;
        }

        /* Reduce tab container padding - CRITICAL */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem !important;
            margin-bottom: 0 !important;
            padding-top: 0 !important;
        }

        .stTabs [data-baseweb="tab-panel"] {
            padding-top: 0.5rem !important;
            padding-bottom: 0 !important;
        }

        .stTabs [data-baseweb="tab"] {
            padding-top: 0.5rem !important;
            padding-bottom: 0.5rem !important;
        }

        /* Compact expanders */
        .streamlit-expanderHeader {
            font-size: 0.9rem;
            padding: 0.25rem 0 !important;
        }

        /* Reduce column padding - CRITICAL */
        [data-testid="column"] {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }

        /* Tighter form elements - CRITICAL */
        .stSlider {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            margin-bottom: 0.5rem !important;
        }

        .stNumberInput {
            padding-bottom: 0 !important;
            margin-bottom: 0.5rem !important;
        }

        .stSelectbox {
            padding-bottom: 0 !important;
            margin-bottom: 0.5rem !important;
        }

        .stCheckbox {
            padding-bottom: 0 !important;
            margin-bottom: 0.5rem !important;
        }

        /* Form widget labels */
        label {
            margin-bottom: 0.25rem !important;
            padding-bottom: 0 !important;
        }

        /* Reduce main section spacing */
        section.main > div {
            padding-top: 0.5rem !important;
        }

        /* Markdown elements */
        .stMarkdown {
            margin-bottom: 0.25rem !important;
            padding-bottom: 0 !important;
        }

        /* Button containers */
        .stButton > button {
            margin-top: 0 !important;
        }

        /* Row widget spacing */
        .row-widget {
            margin-bottom: 0.25rem !important;
        }
    </style>
    """, unsafe_allow_html=True)


__all__ = ['apply_custom_styles']
