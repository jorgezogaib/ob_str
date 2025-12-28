"""
Page 5: Unit-Level Comparison

Compare individual property performance.
- Side-by-side charts
- Performance comparison table
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from components.charts import unit_comparison_chart
from utils.simulation_runner import run_simulation, get_base_config

st.set_page_config(page_title="Unit Comparison", page_icon="🏘️", layout="wide")

st.title("Unit-Level Comparison")

# Initialize if needed
if 'config' not in st.session_state:
    st.session_state.config = get_base_config()
    result = run_simulation(st.session_state.config)
    st.session_state.portfolio_df = result.monthly
    st.session_state.units_df = result.units

units_df = st.session_state.units_df
portfolio_df = st.session_state.portfolio_df

# Property selector
st.subheader("Select Properties to Compare")

all_units = sorted(units_df['Unit_ID'].unique())

if len(all_units) == 0:
    st.warning("No properties found in simulation results")
    st.stop()

# Initialize unit selection state if not present
if 'unit_compare_selection' not in st.session_state:
    # Default to first 4 units (or all if fewer than 4)
    st.session_state.unit_compare_selection = list(all_units[:4])

# Check for button actions (must be before multiselect to update state first)
col1, col2 = st.columns([3, 1])

with col2:
    select_all = st.button("Select All")
    clear_all = st.button("Clear All")

# Handle button clicks before rendering multiselect
if select_all:
    st.session_state.unit_compare_selection = list(all_units)
if clear_all:
    st.session_state.unit_compare_selection = []

with col1:
    # Use session state directly as default (no key to avoid widget state conflict)
    selected_units = st.multiselect(
        "Select properties to compare",
        options=all_units,
        default=st.session_state.unit_compare_selection
    )
    # Update state when selection changes
    st.session_state.unit_compare_selection = selected_units

# Rerun after button click to refresh the multiselect
if select_all or clear_all:
    st.rerun()

if len(selected_units) == 0:
    st.warning("Please select at least one property to compare")
    st.stop()

st.divider()

# Filter data
comparison_df = units_df[units_df['Unit_ID'].isin(selected_units)].copy()
comparison_df['Time'] = (comparison_df['Year'] - 1) * 12 + comparison_df['Month']

# Side-by-side charts
st.subheader("Property Value Over Time")
st.plotly_chart(
    unit_comparison_chart(units_df, selected_units, 'Unit_Value', 'Property Value Over Time'),
    use_container_width=True
)

st.subheader("Debt Over Time")
st.plotly_chart(
    unit_comparison_chart(units_df, selected_units, 'Unit_Debt', 'Debt Over Time'),
    use_container_width=True
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("LTV % Over Time")
    st.plotly_chart(
        unit_comparison_chart(units_df, selected_units, 'Unit_LTV', 'LTV % Over Time'),
        use_container_width=True
    )

with col2:
    st.subheader("Operating CF Over Time")
    st.plotly_chart(
        unit_comparison_chart(units_df, selected_units, 'Unit_Operating_CF', 'Operating Cash Flow'),
        use_container_width=True
    )

col1, col2 = st.columns(2)

with col1:
    st.subheader("Cash-on-Cash Return")
    st.plotly_chart(
        unit_comparison_chart(units_df, selected_units, 'Unit_Cash_On_Cash_Return', 'Cash-on-Cash Return %'),
        use_container_width=True
    )

with col2:
    st.subheader("Cap Rate")
    st.plotly_chart(
        unit_comparison_chart(units_df, selected_units, 'Unit_Cap_Rate', 'Cap Rate %'),
        use_container_width=True
    )

st.divider()

# Performance comparison table
st.subheader("Current Performance Comparison")

# Year selector for comparison
available_years = sorted(units_df['Year'].unique())
selected_year = st.selectbox("Select Year for Comparison", available_years, index=len(available_years)-1)

# Get data for selected year (last month of that year)
latest_data = []
for unit_id in selected_units:
    unit_year_data = units_df[(units_df['Unit_ID'] == unit_id) & (units_df['Year'] == selected_year)]
    if len(unit_year_data) > 0:
        unit_latest = unit_year_data.iloc[-1]  # Last month of that year
        latest_data.append({
            'Unit ID': unit_id,
            'Value': unit_latest['Unit_Value'],
            'Debt': unit_latest['Unit_Debt'],
            'Equity': unit_latest['Unit_Equity'],
            'LTV %': unit_latest['Unit_LTV'],
            'Monthly CF': unit_latest['Unit_Operating_CF'],
            'CoC %': unit_latest['Unit_Cash_On_Cash_Return'],
            'Cap Rate %': unit_latest['Unit_Cap_Rate'],
            'DSCR': unit_latest['Unit_DSCR'],
            'ROI %': unit_latest['Unit_ROI']
        })

perf_df = pd.DataFrame(latest_data)

# Highlight best/worst
def highlight_best_worst(s):
    if s.name in ['Value', 'Equity', 'Monthly CF', 'CoC %', 'Cap Rate %', 'DSCR', 'ROI %']:
        is_max = s == s.max()
        is_min = s == s.min()
        return ['background-color: #00ff8840' if v else 'background-color: #ff6b6b40' if m else ''
                for v, m in zip(is_max, is_min)]
    elif s.name in ['Debt', 'LTV %']:
        is_max = s == s.max()
        is_min = s == s.min()
        return ['background-color: #ff6b6b40' if v else 'background-color: #00ff8840' if m else ''
                for v, m in zip(is_max, is_min)]
    else:
        return ['' for _ in s]

styled_df = perf_df.style.apply(highlight_best_worst).format({
    'Value': '${:,.0f}',
    'Debt': '${:,.0f}',
    'Equity': '${:,.0f}',
    'LTV %': '{:.1f}%',
    'Monthly CF': '${:,.0f}',
    'CoC %': '{:.1f}%',
    'Cap Rate %': '{:.1f}%',
    'DSCR': '{:.2f}',
    'ROI %': '{:.1f}%'
})

st.dataframe(styled_df, use_container_width=True)

st.caption("Green = best, Red = worst for each metric")

st.divider()

# Unit lifecycle analysis
st.subheader("Unit Lifecycle Analysis")

unit_to_analyze = st.selectbox("Select unit for detailed analysis", selected_units)

unit_data = units_df[units_df['Unit_ID'] == unit_to_analyze].copy()
unit_data['Time'] = (unit_data['Year'] - 1) * 12 + unit_data['Month']

# Show key lifecycle events
first_month = unit_data.iloc[0]
last_month = unit_data.iloc[-1]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Acquisition", f"Year {int(first_month['Year'])}, Month {int(first_month['Month'])}")
    st.metric("Initial Value", f"${first_month['Unit_Value']:,.0f}")
    st.metric("Initial Debt", f"${first_month['Unit_Debt']:,.0f}")

with col2:
    st.metric("Final Value", f"${last_month['Unit_Value']:,.0f}")
    st.metric("Final Debt", f"${last_month['Unit_Debt']:,.0f}")
    st.metric("Final Equity", f"${last_month['Unit_Equity']:,.0f}")

with col3:
    value_appreciation = (last_month['Unit_Value'] - first_month['Unit_Value']) / first_month['Unit_Value'] * 100
    st.metric("Total Appreciation", f"{value_appreciation:.1f}%")
    st.metric("Cash Invested", f"${first_month['Unit_Cash_Invested']:,.0f}")
    st.metric(
        "Total ROI",
        f"{last_month['Unit_ROI']:.1f}%",
        help="ROI = (Current Equity - Cash Invested) / Cash Invested. Includes both appreciation AND debt paydown equity gains. Does NOT include cumulative cash flow."
    )

# Was this unit ever the feeder?
feeder_months = portfolio_df[portfolio_df['_FeederIndex'] == unit_to_analyze]
if len(feeder_months) > 0:
    st.info(f"This unit was the feeder property in {len(feeder_months)} month(s)")
else:
    st.info("This unit was never selected as the feeder property")

# Unit income/expense breakdown for final year
st.subheader(f"Unit {unit_to_analyze} - Final Year Income/Expense Breakdown")

final_year = int(last_month['Year'])
final_year_data = unit_data[unit_data['Year'] == final_year]

if len(final_year_data) > 0:
    annual_income = final_year_data['Unit_Rental_Income'].sum()
    annual_expenses = {
        'Property Management': final_year_data['Unit_Property_Mgmt'].sum(),
        'CapEx': final_year_data['Unit_CapEx'].sum(),
        'HOA': final_year_data['Unit_HOA'].sum(),
        'Insurance': final_year_data['Unit_Insurance'].sum(),
        'Property Tax': final_year_data['Unit_Property_Tax'].sum(),
        'Debt Service': final_year_data['Unit_Debt_Service'].sum()
    }
    annual_noi = final_year_data['Unit_NOI'].sum()
    annual_cf = final_year_data['Unit_Operating_CF'].sum()

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Annual Rental Income:** ${annual_income:,.0f}")
        st.write("**Expenses:**")
        for name, value in annual_expenses.items():
            st.write(f"  - {name}: ${value:,.0f}")

    with col2:
        st.write(f"**Annual NOI:** ${annual_noi:,.0f}")
        st.write(f"**Annual Operating CF:** ${annual_cf:,.0f}")

        expense_ratio = sum(annual_expenses.values()) / annual_income * 100 if annual_income > 0 else 0
        noi_margin = annual_noi / annual_income * 100 if annual_income > 0 else 0

        st.write(f"**Expense Ratio:** {expense_ratio:.1f}%")
        st.write(f"**NOI Margin:** {noi_margin:.1f}%")
