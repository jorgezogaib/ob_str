"""
Page 4: Time Series Analysis

Spot trends and anomalies over 30 years.
- Multi-metric time series
- Anomaly detection
- Growth rate analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from components.charts import multi_metric_chart
from components.validation import get_anomalies
from utils.simulation_runner import run_simulation, get_base_config

st.set_page_config(page_title="Time Series Analysis", page_icon="📈", layout="wide")

st.title("Time Series Analysis")

# Initialize if needed
if 'config' not in st.session_state:
    st.session_state.config = get_base_config()
    result = run_simulation(st.session_state.config)
    st.session_state.portfolio_df = result.monthly
    st.session_state.units_df = result.units

portfolio_df = st.session_state.portfolio_df
config = st.session_state.config

# Distribution Summary (if distributions occurred)
if 'Distribution Amount' in portfolio_df.columns:
    total_dist = portfolio_df['Distribution Amount'].sum()
    dist_months = (portfolio_df['Distribution Amount'] > 0).sum()

    if dist_months > 0:
        first_dist_row = portfolio_df[portfolio_df['Distribution Amount'] > 0].iloc[0]

        st.subheader("💸 Distribution Summary")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Distributed", f"${total_dist/1_000_000:.2f}M")

        with col2:
            start_year = int(first_dist_row['Year'])
            start_month = int(first_dist_row['Month'])
            st.metric("Started", f"Year {start_year}, Mo {start_month}")

        with col3:
            dist_years = dist_months / 12
            st.metric("Duration", f"{dist_years:.1f} years")

        st.divider()

# Time scale toggle
time_scale = st.radio("Time Scale", ["Monthly (1-360)", "Yearly (1-30)"], horizontal=True)
yearly = time_scale == "Yearly (1-30)"

st.divider()

# Metric selector
st.subheader("Select Metrics to Chart")

col1, col2, col3 = st.columns(3)

with col1:
    st.write("**Financial Metrics**")
    show_value = st.checkbox("Portfolio Value", value=True)
    show_debt = st.checkbox("Total Debt", value=True)
    show_equity = st.checkbox("Total Equity")
    show_ltv = st.checkbox("LTV %")

with col2:
    st.write("**Cash Flow Metrics**")
    show_rental = st.checkbox("Monthly Rental Income")
    show_noi = st.checkbox("Net Operating Income")
    show_opcf = st.checkbox("Operating Cash Flow")
    show_dist_cf = st.checkbox("Distributable Cash Flow")
    show_dist_amt = st.checkbox("Distribution Amount")

with col3:
    st.write("**Cash Reserves**")
    show_operating = st.checkbox("Operating Cash")
    show_emergency = st.checkbox("Emergency Reserve")
    show_savings = st.checkbox("Growth Savings")
    show_total_cash = st.checkbox("Total Cash Reserves")

# Build metrics list
metrics = []
if show_value:
    metrics.append("Total Portfolio Value")
if show_debt:
    metrics.append("Total Debt")
if show_equity:
    metrics.append("Total Equity")
if show_ltv:
    metrics.append("LTV %")
if show_rental:
    metrics.append("Monthly Rental Income")
if show_noi:
    metrics.append("Net Operating Income")
if show_opcf:
    metrics.append("Operating Cash Flow")
if show_dist_cf:
    metrics.append("Distributable Cash Flow")
if show_dist_amt:
    metrics.append("Distribution Amount")
if show_operating:
    metrics.append("Operating Cash")
if show_emergency:
    metrics.append("Emergency Reserve")
if show_savings:
    metrics.append("Growth Savings")
if show_total_cash:
    metrics.append("Total Cash Reserves")

if len(metrics) == 0:
    st.warning("Select at least one metric to display")
else:
    # Create chart
    fig = multi_metric_chart(portfolio_df, metrics, "Portfolio Metrics Over Time", yearly=yearly)

    # Add acquisition markers
    acq_events = portfolio_df[portfolio_df['Property Purchase'] > 0]
    if len(acq_events) > 0 and not yearly:
        for _, row in acq_events.iterrows():
            x_val = (row['Year'] - 1) * 12 + row['Month']
            fig.add_vline(x=x_val, line_dash="dash", line_color="green", opacity=0.5,
                         annotation_text="Purchase", annotation_position="top")

    # Add distribution start marker
    if 'Distribution Amount' in portfolio_df.columns:
        dist_events = portfolio_df[portfolio_df['Distribution Amount'] > 0]
        if len(dist_events) > 0:
            first_dist = dist_events.iloc[0]
            if yearly:
                x_val = int(first_dist['Year'])
            else:
                x_val = (first_dist['Year'] - 1) * 12 + first_dist['Month']
            fig.add_vline(x=x_val, line_dash="dot", line_color="gold", line_width=2,
                         annotation_text="Distributions Start", annotation_position="top")

    st.plotly_chart(fig, use_container_width=True)

    # Data grid matching selected metrics
    st.subheader("Data Table")

    # Build columns list based on selected metrics
    display_cols = ['Year', 'Month']
    display_cols.extend(metrics)

    # Filter dataframe to selected columns
    if yearly:
        # Aggregate to yearly for display
        agg_dict = {}
        for metric in metrics:
            if metric in ['Total Portfolio Value', 'Total Debt', 'Total Equity', 'LTV %',
                         'Operating Cash', 'Emergency Reserve', 'Growth Savings', 'Total Cash Reserves',
                         'Properties Owned']:
                agg_dict[metric] = 'last'
            else:
                agg_dict[metric] = 'sum'

        display_df = portfolio_df.groupby('Year').agg(agg_dict).reset_index()
        display_cols_filtered = ['Year'] + metrics
    else:
        # Monthly - show all data
        display_df = portfolio_df[display_cols].copy()
        display_cols_filtered = display_cols

    # Format numbers for better readability
    format_dict = {}
    for col in metrics:
        if 'LTV' in col or '%' in col or 'Ratio' in col:
            format_dict[col] = '{:.2f}%'
        else:
            format_dict[col] = '${:,.0f}'

    st.dataframe(
        display_df[display_cols_filtered].style.format(format_dict),
        use_container_width=True,
        height=400
    )

st.divider()

# Anomaly Detection
st.subheader("Anomaly Detection")

anomalies = get_anomalies(portfolio_df)

if len(anomalies) == 0:
    st.success("No anomalies detected")
else:
    st.warning(f"{len(anomalies)} anomaly(ies) detected")

    # Group by severity
    high = [a for a in anomalies if a['Severity'] == 'High']
    medium = [a for a in anomalies if a['Severity'] == 'Medium']

    if high:
        st.write(f"**High Severity:** {len(high)}")
    if medium:
        st.write(f"**Medium Severity:** {len(medium)}")

    # Display table
    anomaly_df = pd.DataFrame(anomalies)
    st.dataframe(
        anomaly_df.style.apply(
            lambda x: ['background-color: #ff6b6b' if v == 'High' else 'background-color: #ffb347' if v == 'Medium' else '' for v in x],
            subset=['Severity']
        ),
        use_container_width=True,
        height=300
    )

st.divider()

# Growth Rate Analysis
st.subheader("Year-over-Year Growth Analysis")

# Calculate YoY metrics
agg_dict = {
    'Monthly Rental Income': 'sum',
    'Net Operating Income': 'sum',
    'Total Equity': 'last',
    'Total Portfolio Value': 'last',
    'Properties Owned': 'last'
}

# Add distribution amount if available
if 'Distribution Amount' in portfolio_df.columns:
    agg_dict['Distribution Amount'] = 'sum'

yearly_df = portfolio_df.groupby('Year').agg(agg_dict).reset_index()

yearly_df['Revenue_Growth_%'] = yearly_df['Monthly Rental Income'].pct_change() * 100
yearly_df['NOI_Growth_%'] = yearly_df['Net Operating Income'].pct_change() * 100
yearly_df['Equity_Growth_%'] = yearly_df['Total Equity'].pct_change() * 100
yearly_df['Value_Growth_%'] = yearly_df['Total Portfolio Value'].pct_change() * 100

# Expected growth rates
expected_revenue_growth = config['market']['revenueInflationRate'] * 100
expected_value_growth = config['market']['annualAppreciation'] * 100

# Revenue growth chart
fig_revenue = go.Figure()

fig_revenue.add_trace(go.Bar(
    x=yearly_df['Year'],
    y=yearly_df['Revenue_Growth_%'],
    name='Actual Revenue Growth',
    marker_color='#00D9FF'
))

fig_revenue.add_hline(
    y=expected_revenue_growth,
    line_dash="dash",
    line_color="yellow",
    annotation_text=f"Expected ({expected_revenue_growth:.1f}%)"
)

fig_revenue.update_layout(
    title="Revenue Growth % vs Expected",
    xaxis_title="Year",
    yaxis_title="Growth %",
    height=400,
    template=st.session_state.get('plotly_template', 'plotly_dark')
)

st.plotly_chart(fig_revenue, use_container_width=True)

# Highlight underperformance
underperform_revenue = yearly_df[yearly_df['Revenue_Growth_%'] < expected_revenue_growth - 1]  # 1% tolerance
if len(underperform_revenue) > 1:  # Skip year 1 which has no prior
    st.info(f"Revenue growth below expected in {len(underperform_revenue)-1} year(s)")

# Value growth chart
fig_value = go.Figure()

fig_value.add_trace(go.Bar(
    x=yearly_df['Year'],
    y=yearly_df['Value_Growth_%'],
    name='Actual Value Growth',
    marker_color='#00FF88'
))

fig_value.add_hline(
    y=expected_value_growth,
    line_dash="dash",
    line_color="yellow",
    annotation_text=f"Expected ({expected_value_growth:.1f}%)"
)

fig_value.update_layout(
    title="Portfolio Value Growth % vs Expected",
    xaxis_title="Year",
    yaxis_title="Growth %",
    height=400,
    template=st.session_state.get('plotly_template', 'plotly_dark')
)

st.plotly_chart(fig_value, use_container_width=True)

# Growth summary table
st.subheader("Annual Summary")

display_yearly = yearly_df.copy()
display_yearly = display_yearly.rename(columns={
    'Monthly Rental Income': 'Annual Revenue',
    'Net Operating Income': 'Annual NOI'
})

# Skip Year 1 since growth % is meaningless (no prior year to compare)
display_yearly = display_yearly[display_yearly['Year'] > 1].copy()

# Build columns list based on available data
display_cols = ['Year', 'Properties Owned', 'Annual Revenue', 'Annual NOI',
                'Total Portfolio Value', 'Total Equity',
                'Revenue_Growth_%', 'Value_Growth_%']

# Add distribution column if present
if 'Distribution Amount' in display_yearly.columns:
    display_yearly = display_yearly.rename(columns={'Distribution Amount': 'Annual Distributions'})
    display_cols.insert(4, 'Annual Distributions')  # Insert after Annual NOI

# Build format dict
format_dict = {
    'Annual Revenue': '${:,.0f}',
    'Annual NOI': '${:,.0f}',
    'Total Portfolio Value': '${:,.0f}',
    'Total Equity': '${:,.0f}',
    'Revenue_Growth_%': '{:.1f}%',
    'Value_Growth_%': '{:.1f}%'
}

if 'Annual Distributions' in display_yearly.columns:
    format_dict['Annual Distributions'] = '${:,.0f}'

st.dataframe(
    display_yearly[display_cols].style.format(format_dict),
    use_container_width=True
)
