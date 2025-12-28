"""
Page 3: Cash Flow Anatomy

Deep dive into cash flow movements for any specific period.
- Interactive waterfall chart
- Month or Year navigation
- Running commentary on what happened
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from components.charts import waterfall_chart, get_template
from utils.simulation_runner import run_simulation, get_base_config
from ob_str_engine.engine.reports import cash_flow_waterfall

st.set_page_config(page_title="Cash Flow Anatomy", page_icon="💰", layout="wide")

st.title("Cash Flow Anatomy")

# Initialize if needed
if 'config' not in st.session_state:
    st.session_state.config = get_base_config()
    result = run_simulation(st.session_state.config)
    st.session_state.portfolio_df = result.monthly
    st.session_state.units_df = result.units

# Initialize jump target state (separate from widget keys)
if 'cf_jump_year' not in st.session_state:
    st.session_state.cf_jump_year = None
if 'cf_jump_month' not in st.session_state:
    st.session_state.cf_jump_month = None

portfolio_df = st.session_state.portfolio_df

# Time scale toggle at the top
time_scale = st.radio("View", ["Monthly", "Annual"], horizontal=True)

st.divider()

if time_scale == "Monthly":
    # === MONTHLY VIEW ===

    # Determine default values for selectors
    if st.session_state.cf_jump_year is not None:
        default_year_idx = st.session_state.cf_jump_year - 1
        default_month_idx = st.session_state.cf_jump_month - 1
        st.session_state.cf_jump_year = None
        st.session_state.cf_jump_month = None
    else:
        default_year_idx = 4
        default_month_idx = 11

    st.subheader("Select Month to Analyze")

    col1, col2 = st.columns([1, 1])

    with col1:
        year = st.selectbox("Year", range(1, 31), index=default_year_idx)
    with col2:
        month = st.selectbox("Month", range(1, 13), index=default_month_idx)

    # Quick jump buttons
    st.write("**Quick Jump:**")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("First Acquisition"):
            first_acq = portfolio_df[portfolio_df['Property Purchase'] > 0]
            if len(first_acq) > 0:
                st.session_state.cf_jump_year = int(first_acq.iloc[0]['Year'])
                st.session_state.cf_jump_month = int(first_acq.iloc[0]['Month'])
                st.rerun()

    with col2:
        if st.button("First Refi"):
            first_refi = portfolio_df[portfolio_df['Refinance Proceeds'] > 0]
            if len(first_refi) > 0:
                st.session_state.cf_jump_year = int(first_refi.iloc[0]['Year'])
                st.session_state.cf_jump_month = int(first_refi.iloc[0]['Month'])
                st.rerun()

    with col3:
        if st.button("Max Units Reached"):
            max_units = st.session_state.config['policies']['portfolio']['maxUnits']
            max_rows = portfolio_df[portfolio_df['Properties Owned'] == max_units]
            if len(max_rows) > 0:
                st.session_state.cf_jump_year = int(max_rows.iloc[0]['Year'])
                st.session_state.cf_jump_month = int(max_rows.iloc[0]['Month'])
                st.rerun()

    with col4:
        if st.button("Debt-Free"):
            debt_free = portfolio_df[portfolio_df['Total Debt'] == 0]
            if len(debt_free) > 0:
                st.session_state.cf_jump_year = int(debt_free.iloc[0]['Year'])
                st.session_state.cf_jump_month = int(debt_free.iloc[0]['Month'])
                st.rerun()

    st.divider()

    # Get waterfall data
    waterfall_df = cash_flow_waterfall(portfolio_df, year=year, month=month)

    if len(waterfall_df) > 0:
        fig = waterfall_chart(waterfall_df, title=f"Cash Flow Waterfall - Year {year}, Month {month}")
        st.plotly_chart(fig, use_container_width=True)

        row = portfolio_df[(portfolio_df['Year'] == year) & (portfolio_df['Month'] == month)].iloc[0]

        st.subheader("What Happened This Month")

        narrative = []

        if row.get('Property Purchase', 0) > 0:
            narrative.append(
                f"**Property Acquired:** Purchased property for ${row.get('Property Market Value', row['Property Purchase']):,.0f} "
                f"(${row['Down Payment']:,.0f} down + ${row['Closing Costs']:,.0f} closing costs)"
            )

        if row.get('Refinance Proceeds', 0) > 0:
            narrative.append(f"**Refinance Event:** Extracted ${row['Refinance Proceeds']:,.0f} in cash from refinancing")

        if row.get('Principal Prepayment', 0) > 0:
            narrative.append(f"**Debt Paydown:** Made ${row['Principal Prepayment']:,.0f} in extra principal payments")

        if row.get('_RainyTopup', 0) > 0:
            narrative.append(f"**Reserve Topup:** Deposited ${row['_RainyTopup']:,.0f} to emergency reserves")

        if row.get('Savings Deposit', 0) > 0:
            narrative.append(f"**Savings Deposit:** Added ${row['Savings Deposit']:,.0f} to growth savings")

        if row['Operating Cash Flow'] > 0:
            narrative.append(f"**Positive Operating CF:** Generated ${row['Operating Cash Flow']:,.0f} in operating cash flow")
        elif row['Operating Cash Flow'] < 0:
            narrative.append(f"**Negative Operating CF:** Expenses exceeded income by ${abs(row['Operating Cash Flow']):,.0f}")

        if len(narrative) == 0:
            narrative.append("Standard operating month with no special events")

        for item in narrative:
            st.markdown(f"- {item}")

        st.subheader("Month Summary")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Properties", int(row['Properties Owned']))
        with col2:
            st.metric("Rental Income", f"${row['Monthly Rental Income']:,.0f}")
        with col3:
            st.metric("NOI", f"${row['Net Operating Income']:,.0f}")
        with col4:
            st.metric("Operating CF", f"${row['Operating Cash Flow']:,.0f}")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Operating Cash", f"${row['Operating Cash']:,.0f}")
        with col2:
            st.metric("Emergency Reserve", f"${row['Emergency Reserve']:,.0f}")
        with col3:
            st.metric("Growth Savings", f"${row['Growth Savings']:,.0f}")
        with col4:
            st.metric("Total Debt", f"${row['Total Debt']:,.0f}")

    else:
        st.warning("No data for selected month")

else:
    # === ANNUAL VIEW ===
    st.subheader("Select Year to Analyze")

    year = st.selectbox("Year", range(1, 31), index=4)

    # Aggregate annual data
    year_data = portfolio_df[portfolio_df['Year'] == year]

    if len(year_data) > 0:
        # Build annual waterfall
        annual_income = year_data['Monthly Rental Income'].sum()
        annual_mgmt = year_data['Property Management'].sum()
        annual_capex = year_data['CapEx & Maintenance'].sum()
        annual_hoa = year_data['HOA Fees'].sum()
        annual_insurance = year_data['Property Insurance'].sum()
        annual_taxes = year_data['Property Taxes'].sum()
        annual_debt_service = year_data['Debt Service'].sum()
        annual_noi = year_data['Net Operating Income'].sum()
        annual_ocf = year_data['Operating Cash Flow'].sum()

        # Annual summary metrics
        final_month = year_data.iloc[-1]

        st.subheader(f"Year {year} Summary")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Properties (EOY)", int(final_month['Properties Owned']))
        with col2:
            st.metric("Annual Revenue", f"${annual_income:,.0f}")
        with col3:
            st.metric("Annual NOI", f"${annual_noi:,.0f}")
        with col4:
            st.metric("Annual Op. CF", f"${annual_ocf:,.0f}")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Portfolio Value", f"${final_month['Total Portfolio Value']:,.0f}")
        with col2:
            st.metric("Total Debt", f"${final_month['Total Debt']:,.0f}")
        with col3:
            st.metric("Total Equity", f"${final_month['Total Equity']:,.0f}")
        with col4:
            st.metric("Cash Reserves", f"${final_month['Total Cash Reserves']:,.0f}")

        st.divider()

        # Annual waterfall chart
        annual_waterfall = pd.DataFrame([
            {'Category': 'Rental Income', 'Amount': annual_income},
            {'Category': '- Property Mgmt', 'Amount': -annual_mgmt},
            {'Category': '- CapEx', 'Amount': -annual_capex},
            {'Category': '- HOA', 'Amount': -annual_hoa},
            {'Category': '- Insurance', 'Amount': -annual_insurance},
            {'Category': '- Taxes', 'Amount': -annual_taxes},
            {'Category': '= NOI', 'Amount': annual_noi},
            {'Category': '- Debt Service', 'Amount': -annual_debt_service},
            {'Category': '= Operating CF', 'Amount': annual_ocf},
        ])

        fig = waterfall_chart(annual_waterfall, title=f"Annual Cash Flow Waterfall - Year {year}")
        st.plotly_chart(fig, use_container_width=True)

        # Annual events
        st.subheader(f"Key Events in Year {year}")

        acquisitions = year_data[year_data['Property Purchase'] > 0]
        refis = year_data[year_data['Refinance Proceeds'] > 0]
        prepayments = year_data['Principal Prepayment'].sum()

        if len(acquisitions) > 0:
            for _, acq in acquisitions.iterrows():
                st.markdown(f"- **Month {int(acq['Month'])}:** Acquired property for ${acq.get('Property Market Value', acq['Property Purchase']):,.0f}")

        if len(refis) > 0:
            for _, refi in refis.iterrows():
                st.markdown(f"- **Month {int(refi['Month'])}:** Refinanced, extracted ${refi['Refinance Proceeds']:,.0f}")

        if prepayments > 0:
            st.markdown(f"- **Total prepayments:** ${prepayments:,.0f}")

        if len(acquisitions) == 0 and len(refis) == 0 and prepayments == 0:
            st.markdown("- No major capital events this year")

    else:
        st.warning("No data for selected year")

st.divider()

# Data table section
st.subheader("Cash Flow Data Table")

# Time scale for table
table_view = st.radio("Table View", ["Monthly", "Annual Summary"], horizontal=True, key="table_view")

if table_view == "Monthly":
    filter_option = st.radio(
        "Filter",
        ["All months", "Acquisition months", "Refinance months", "Negative CF months"],
        horizontal=True
    )

    if filter_option == "Acquisition months":
        display_df = portfolio_df[portfolio_df['Property Purchase'] > 0]
    elif filter_option == "Refinance months":
        display_df = portfolio_df[portfolio_df['Refinance Proceeds'] > 0]
    elif filter_option == "Negative CF months":
        display_df = portfolio_df[portfolio_df['Operating Cash Flow'] < 0]
    else:
        display_df = portfolio_df

    display_cols = [
        'Year', 'Month', 'Properties Owned',
        'Monthly Rental Income', 'Net Operating Income',
        'Debt Service', 'Operating Cash Flow',
        'Principal Prepayment', 'Operating Cash'
    ]
    display_cols = [c for c in display_cols if c in display_df.columns]

    st.dataframe(
        display_df[display_cols].style.format({
            'Monthly Rental Income': '${:,.0f}',
            'Net Operating Income': '${:,.0f}',
            'Debt Service': '${:,.0f}',
            'Operating Cash Flow': '${:,.0f}',
            'Principal Prepayment': '${:,.0f}',
            'Operating Cash': '${:,.0f}'
        }),
        height=400,
        use_container_width=True
    )

    st.caption(f"Showing {len(display_df)} of {len(portfolio_df)} months")

else:
    # Annual summary table
    annual_df = portfolio_df.groupby('Year').agg({
        'Properties Owned': 'last',
        'Monthly Rental Income': 'sum',
        'Net Operating Income': 'sum',
        'Debt Service': 'sum',
        'Operating Cash Flow': 'sum',
        'Principal Prepayment': 'sum',
        'Total Portfolio Value': 'last',
        'Total Debt': 'last',
        'Total Cash Reserves': 'last'
    }).reset_index()

    annual_df.columns = [
        'Year', 'Properties', 'Annual Revenue', 'Annual NOI',
        'Annual Debt Service', 'Annual Op. CF', 'Annual Prepayment',
        'Portfolio Value', 'Total Debt', 'Cash Reserves'
    ]

    st.dataframe(
        annual_df.style.format({
            'Annual Revenue': '${:,.0f}',
            'Annual NOI': '${:,.0f}',
            'Annual Debt Service': '${:,.0f}',
            'Annual Op. CF': '${:,.0f}',
            'Annual Prepayment': '${:,.0f}',
            'Portfolio Value': '${:,.0f}',
            'Total Debt': '${:,.0f}',
            'Cash Reserves': '${:,.0f}'
        }),
        height=400,
        use_container_width=True
    )

    st.caption("Annual summary (year-end values for stocks, annual sums for flows)")
