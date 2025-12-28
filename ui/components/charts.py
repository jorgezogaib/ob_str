"""
Charts Component - Plotly chart generation functions
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Optional


def get_template() -> str:
    """Get the current Plotly template based on dark mode setting"""
    return st.session_state.get("plotly_template", "plotly_dark")


def _df_hash(df: pd.DataFrame) -> str:
    """Generate a hash for a DataFrame based on its shape and first/last rows."""
    return f"{df.shape}_{id(df)}"


@st.cache_data(show_spinner=False, hash_funcs={pd.DataFrame: _df_hash})
def portfolio_value_chart(df: pd.DataFrame, show_debt: bool = True) -> go.Figure:
    """Create portfolio value over time chart"""
    fig = go.Figure()

    # Create time index
    df = df.copy()
    df['Time'] = (df['Year'] - 1) * 12 + df['Month']

    fig.add_trace(go.Scatter(
        x=df['Time'],
        y=df['Total Portfolio Value'],
        mode='lines',
        name='Portfolio Value',
        line=dict(color='#00D9FF', width=2)
    ))

    if show_debt:
        fig.add_trace(go.Scatter(
            x=df['Time'],
            y=df['Total Debt'],
            mode='lines',
            name='Total Debt',
            line=dict(color='#FF6B6B', width=2)
        ))

    fig.update_layout(
        title="Portfolio Value & Debt Over Time",
        xaxis_title="Month",
        yaxis_title="Value ($)",
        hovermode='x unified',
        height=400,
        template=get_template()
    )

    return fig


@st.cache_data(show_spinner=False, hash_funcs={pd.DataFrame: _df_hash})
def properties_timeline_chart(df: pd.DataFrame) -> go.Figure:
    """Create properties owned step chart"""
    fig = go.Figure()

    df = df.copy()
    df['Time'] = (df['Year'] - 1) * 12 + df['Month']

    fig.add_trace(go.Scatter(
        x=df['Time'],
        y=df['Properties Owned'],
        mode='lines',
        name='Properties Owned',
        line=dict(color='#00FF88', width=2, shape='hv')
    ))

    # Add markers for acquisitions
    acq_months = df[df['Property Purchase'] > 0]
    fig.add_trace(go.Scatter(
        x=acq_months['Time'],
        y=acq_months['Properties Owned'],
        mode='markers',
        name='Acquisitions',
        marker=dict(size=10, color='#00FF88', symbol='triangle-up')
    ))

    fig.update_layout(
        title="Properties Owned Timeline",
        xaxis_title="Month",
        yaxis_title="Properties",
        height=300,
        template=get_template()
    )

    return fig


@st.cache_data(show_spinner=False, hash_funcs={pd.DataFrame: _df_hash})
def cash_reserves_chart(df: pd.DataFrame) -> go.Figure:
    """Create cash reserves over time chart"""
    fig = go.Figure()

    df = df.copy()
    df['Time'] = (df['Year'] - 1) * 12 + df['Month']

    fig.add_trace(go.Scatter(
        x=df['Time'],
        y=df['Operating Cash'],
        mode='lines',
        name='Operating Cash',
        line=dict(color='#00D9FF', width=1.5)
    ))

    fig.add_trace(go.Scatter(
        x=df['Time'],
        y=df['Emergency Reserve'],
        mode='lines',
        name='Emergency Reserve',
        line=dict(color='#FFB347', width=1.5)
    ))

    fig.add_trace(go.Scatter(
        x=df['Time'],
        y=df['Growth Savings'],
        mode='lines',
        name='Growth Savings',
        line=dict(color='#77DD77', width=1.5)
    ))

    # Add required reserves line
    fig.add_trace(go.Scatter(
        x=df['Time'],
        y=df['_RainyTarget'],
        mode='lines',
        name='Required Reserves',
        line=dict(color='#FF6B6B', width=1, dash='dash')
    ))

    fig.update_layout(
        title="Cash Reserves Over Time",
        xaxis_title="Month",
        yaxis_title="Balance ($)",
        hovermode='x unified',
        height=400,
        template=get_template()
    )

    return fig


@st.cache_data(show_spinner=False, hash_funcs={pd.DataFrame: _df_hash})
def waterfall_chart(waterfall_df: pd.DataFrame, title: str = "Cash Flow Waterfall") -> go.Figure:
    """Create a waterfall chart from waterfall DataFrame"""
    # Determine measure types
    measures = []
    for i, row in waterfall_df.iterrows():
        category = row['Category']
        if category.startswith('Starting') or category.startswith('='):
            measures.append('absolute')
        elif category.startswith('Ending'):
            measures.append('total')
        else:
            measures.append('relative')

    fig = go.Figure(go.Waterfall(
        name="Cash Flow",
        orientation="v",
        measure=measures,
        x=waterfall_df['Category'],
        y=waterfall_df['Amount'],
        text=waterfall_df['Amount'].apply(lambda x: f"${x:,.0f}"),
        textposition="outside",
        connector=dict(line=dict(color="rgba(63, 63, 63, 0.5)")),
        increasing=dict(marker=dict(color="#00FF88")),
        decreasing=dict(marker=dict(color="#FF6B6B")),
        totals=dict(marker=dict(color="#00D9FF"))
    ))

    fig.update_layout(
        title=title,
        showlegend=False,
        height=600,
        template=get_template(),
        xaxis_tickangle=-45
    )

    return fig


def multi_metric_chart(
    df: pd.DataFrame,
    metrics: List[str],
    title: str = "Time Series",
    yearly: bool = False
) -> go.Figure:
    """Create multi-metric time series chart"""
    fig = go.Figure()

    df = df.copy()

    if yearly:
        # Aggregate to yearly
        display_df = df.groupby('Year').last().reset_index()
        x_col = 'Year'
    else:
        df['Time'] = (df['Year'] - 1) * 12 + df['Month']
        display_df = df
        x_col = 'Time'

    colors = ['#00D9FF', '#FF6B6B', '#00FF88', '#FFB347', '#E066FF']

    for i, metric in enumerate(metrics):
        if metric in display_df.columns:
            fig.add_trace(go.Scatter(
                x=display_df[x_col],
                y=display_df[metric],
                mode='lines',
                name=metric,
                line=dict(color=colors[i % len(colors)], width=2)
            ))

    fig.update_layout(
        title=title,
        xaxis_title="Year" if yearly else "Month",
        yaxis_title="Value",
        hovermode='x unified',
        height=500,
        template=get_template()
    )

    return fig


def unit_comparison_chart(
    units_df: pd.DataFrame,
    unit_ids: List[int],
    metric: str,
    title: str = "Unit Comparison"
) -> go.Figure:
    """Create comparison chart for multiple units"""
    fig = go.Figure()

    colors = ['#00D9FF', '#FF6B6B', '#00FF88', '#FFB347', '#E066FF']

    for i, unit_id in enumerate(unit_ids):
        unit_data = units_df[units_df['Unit_ID'] == unit_id].copy()
        unit_data['Time'] = (unit_data['Year'] - 1) * 12 + unit_data['Month']

        if metric in unit_data.columns:
            fig.add_trace(go.Scatter(
                x=unit_data['Time'],
                y=unit_data[metric],
                mode='lines',
                name=f'Unit {unit_id}',
                line=dict(color=colors[i % len(colors)], width=2)
            ))

    fig.update_layout(
        title=title,
        xaxis_title="Month",
        yaxis_title=metric,
        hovermode='x unified',
        height=400,
        template=get_template()
    )

    return fig


def scenario_comparison_chart(
    scenario_results: dict,
    metric: str = 'Total Portfolio Value',
    title: str = "Scenario Comparison"
) -> go.Figure:
    """Create overlay chart comparing multiple scenarios"""
    fig = go.Figure()

    colors = ['#00D9FF', '#FF6B6B', '#00FF88', '#FFB347', '#E066FF']

    for i, (name, results) in enumerate(scenario_results.items()):
        df = results['portfolio_df']
        df = df.copy()
        df['Time'] = df['Year'] + df['Month']/12

        if metric in df.columns:
            fig.add_trace(go.Scatter(
                x=df['Time'],
                y=df[metric],
                mode='lines',
                name=name,
                line=dict(color=colors[i % len(colors)], width=2)
            ))

    fig.update_layout(
        title=title,
        xaxis_title="Year",
        yaxis_title=metric,
        hovermode='x unified',
        height=500,
        template=get_template()
    )

    return fig


def acquisition_timeline_chart(df: pd.DataFrame) -> go.Figure:
    """Create detailed acquisition timeline with annotations"""
    fig = go.Figure()

    # Create time index
    df = df.copy()
    df['Time'] = (df['Year'] - 1) * 12 + df['Month']

    # Base line - properties owned
    fig.add_trace(go.Scatter(
        x=df['Time'],
        y=df['Properties Owned'],
        mode='lines',
        name='Properties Owned',
        line=dict(color='#00D9FF', width=3, shape='hv'),
        fill='tozeroy',
        fillcolor='rgba(0, 217, 255, 0.1)'
    ))

    # Acquisition markers with annotations - show Property Market Value (purchase price)
    acq_months = df[df['Property Purchase'] > 0]

    for _, row in acq_months.iterrows():
        # Property Market Value is the actual purchase price
        purchase_price = row.get('Property Market Value', row['Property Purchase'])
        fig.add_annotation(
            x=row['Time'],
            y=row['Properties Owned'],
            text=f"Y{int(row['Year'])}M{int(row['Month'])}<br>${purchase_price:,.0f}",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=1,
            arrowcolor="#00FF88",
            font=dict(size=10),
            bgcolor="rgba(0, 0, 0, 0.7)",
            bordercolor="#00FF88",
            borderwidth=1
        )

    fig.update_layout(
        title="Acquisition Timeline (Purchase Price)",
        xaxis_title="Month",
        yaxis_title="Properties Owned",
        height=400,
        template=get_template()
    )

    return fig
