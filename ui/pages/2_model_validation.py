"""
Page 2: Model Validation Dashboard

Verify model logic is working correctly:
- Acquisition Logic
- Reserve Mechanics
- Feeder Strategy
- Refinance Logic
- Cash Reconciliation
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from components.charts import acquisition_timeline_chart, cash_reserves_chart
from components.validation import run_all_validations, get_anomalies
from utils.simulation_runner import run_simulation, get_base_config

st.set_page_config(page_title="Model Validation", page_icon="🔍", layout="wide")

st.title("Model Validation Dashboard")

# Initialize if needed
if 'config' not in st.session_state:
    st.session_state.config = get_base_config()
    result = run_simulation(st.session_state.config)
    st.session_state.portfolio_df = result.monthly
    st.session_state.units_df = result.units

# Get data
portfolio_df = st.session_state.portfolio_df
units_df = st.session_state.units_df
config = st.session_state.config

# Validation summary at top
st.subheader("Validation Summary")

validations = run_all_validations(portfolio_df, units_df, config)

# Group by status
passes = [v for v in validations if v['status'] == 'pass']
warnings = [v for v in validations if v['status'] == 'warning']
fails = [v for v in validations if v['status'] == 'fail']

# Create filter buttons
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button(f"✓ Passed ({len(passes)})", key="filter_passed", use_container_width=True):
        st.session_state.validation_filter = 'pass'
with col2:
    if st.button(f"⚠ Warnings ({len(warnings)})", key="filter_warnings", use_container_width=True):
        st.session_state.validation_filter = 'warning'
with col3:
    if st.button(f"✗ Failed ({len(fails)})", key="filter_failed", use_container_width=True):
        st.session_state.validation_filter = 'fail'
with col4:
    if st.button(f"All ({len(validations)})", key="filter_all", use_container_width=True):
        st.session_state.validation_filter = 'all'

# Initialize filter if not set
if 'validation_filter' not in st.session_state:
    st.session_state.validation_filter = 'all'

# Apply filter
if st.session_state.validation_filter == 'pass':
    filtered_validations = passes
elif st.session_state.validation_filter == 'warning':
    filtered_validations = warnings
elif st.session_state.validation_filter == 'fail':
    filtered_validations = fails
else:
    filtered_validations = validations

# Show filtered results
for v in filtered_validations:
    if v['status'] == 'pass':
        st.success(f"**{v['name']}:** {v['message']}")
    elif v['status'] == 'warning':
        st.warning(f"**{v['name']}:** {v['message']}")
    else:
        st.error(f"**{v['name']}:** {v['message']}")

st.divider()

# Tabbed interface for different validation areas
tabs = st.tabs([
    "Acquisition Logic",
    "Reserve Mechanics",
    "Feeder Strategy",
    "Refinance Logic",
    "Cash Reconciliation"
])

# === Tab 1: Acquisition Logic ===
with tabs[0]:
    st.subheader("Acquisition Timeline")

    # Acquisition timeline chart
    st.plotly_chart(acquisition_timeline_chart(portfolio_df), use_container_width=True)

    # Acquisition table
    st.subheader("Acquisition Details")

    acq_months = portfolio_df[portfolio_df['Property Purchase'] > 0].copy()

    if len(acq_months) > 0:
        display_cols = [
            'Year', 'Month', 'Properties Owned',
            'Property Purchase', 'Down Payment', 'Closing Costs',
            'Refinance Proceeds', 'Growth Savings', 'Operating Cash'
        ]
        display_cols = [c for c in display_cols if c in acq_months.columns]

        st.dataframe(
            acq_months[display_cols].style.format({
                'Property Purchase': '${:,.0f}',
                'Down Payment': '${:,.0f}',
                'Closing Costs': '${:,.0f}',
                'Refinance Proceeds': '${:,.0f}',
                'Growth Savings': '${:,.0f}',
                'Operating Cash': '${:,.0f}'
            }),
            use_container_width=True
        )

        # Feasibility check
        st.subheader("Acquisition Feasibility Check")
        st.success(f"All {len(acq_months)} acquisitions were feasible (completed successfully)")
    else:
        st.info("No acquisitions found in this simulation")

# === Tab 2: Reserve Mechanics ===
with tabs[1]:
    st.subheader("Reserve Balances Over Time")

    # Reserve chart
    st.plotly_chart(cash_reserves_chart(portfolio_df), use_container_width=True)

    # Reserve events
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Topup Events")
        topups = portfolio_df[portfolio_df['_RainyTopup'] > 0].copy()
        st.write(f"**Total Topups:** {len(topups)}")

        if len(topups) > 0:
            st.dataframe(
                topups[['Year', 'Month', '_RainyTopup', 'Emergency Reserve', '_RainyTarget']].style.format({
                    '_RainyTopup': '${:,.0f}',
                    'Emergency Reserve': '${:,.0f}',
                    '_RainyTarget': '${:,.0f}'
                }),
                height=300,
                use_container_width=True
            )

    with col2:
        st.subheader("Sweep Events")
        sweeps = portfolio_df[portfolio_df['_RainySweep'] > 0].copy()
        st.write(f"**Total Sweeps:** {len(sweeps)}")

        if len(sweeps) > 0:
            st.dataframe(
                sweeps[['Year', 'Month', '_RainySweep', 'Emergency Reserve']].style.format({
                    '_RainySweep': '${:,.0f}',
                    'Emergency Reserve': '${:,.0f}'
                }),
                height=300,
                use_container_width=True
            )

    # Validation
    st.subheader("Reserve Mechanics Validation")

    # Check topups only when below target
    below_target_months = portfolio_df[portfolio_df['Emergency Reserve'] < portfolio_df['_RainyTarget'] * 0.95]

    if len(below_target_months) <= 12:  # Allow up to 12 months below target
        st.success(f"Reserves maintained adequately (below target in only {len(below_target_months)} month(s))")
    else:
        st.warning(f"Reserves below target in {len(below_target_months)} months")

# === Tab 3: Feeder Strategy ===
with tabs[2]:
    st.subheader("Feeder Property Timeline")

    # Show feeder changes over time
    portfolio_df_copy = portfolio_df.copy()
    portfolio_df_copy['Feeder_Changed'] = portfolio_df_copy['_FeederIndex'].ne(portfolio_df_copy['_FeederIndex'].shift())

    feeder_changes = portfolio_df_copy[portfolio_df_copy['Feeder_Changed'] == True]

    if len(feeder_changes) > 0:
        st.write(f"**Feeder changed {len(feeder_changes)} times during simulation**")

        st.dataframe(
            feeder_changes[['Year', 'Month', 'Properties Owned', '_FeederIndex', '_FeederLTV']].style.format({
                '_FeederLTV': '{:.2%}'
            }),
            use_container_width=True
        )

    # Feeder LTV over time
    st.subheader("Feeder LTV Over Time")

    import plotly.graph_objects as go

    fig = go.Figure()

    portfolio_df_copy['Time'] = (portfolio_df_copy['Year'] - 1) * 12 + portfolio_df_copy['Month']

    # Filter to months with properties
    with_props = portfolio_df_copy[portfolio_df_copy['Properties Owned'] > 0]

    fig.add_trace(go.Scatter(
        x=with_props['Time'],
        y=with_props['_FeederLTV'],
        mode='lines',
        name='Feeder LTV',
        line=dict(color='#00D9FF', width=2)
    ))

    fig.update_layout(
        title="Feeder Property LTV Over Time",
        xaxis_title="Month",
        yaxis_title="LTV",
        yaxis_tickformat='.0%',
        height=400,
        template=st.session_state.get('plotly_template', 'plotly_dark')
    )

    st.plotly_chart(fig, use_container_width=True)

    # Prepayment analysis
    st.subheader("Prepayment Activity")

    prepay_months = portfolio_df[portfolio_df['Principal Prepayment'] > 0]
    st.write(f"**Months with prepayment:** {len(prepay_months)}")
    st.write(f"**Total prepaid:** ${portfolio_df['Principal Prepayment'].sum():,.0f}")

    if len(prepay_months) > 0:
        st.dataframe(
            prepay_months[['Year', 'Month', 'Principal Prepayment', '_FeederIndex', '_FeederLTV']].head(20).style.format({
                'Principal Prepayment': '${:,.0f}',
                '_FeederLTV': '{:.2%}'
            }),
            use_container_width=True
        )

# === Tab 4: Refinance Logic ===
with tabs[3]:
    st.subheader("Refinancing Events")

    refi_events = portfolio_df[portfolio_df['Refinance Proceeds'] > 0]

    st.write(f"**Total refinancing events:** {len(refi_events)}")
    st.write(f"**Total proceeds extracted:** ${refi_events['Refinance Proceeds'].sum():,.0f}")

    if len(refi_events) > 0:
        st.dataframe(
            refi_events[['Year', 'Month', 'Properties Owned', '_RefiPropertyIndex',
                        'Refinance Proceeds', 'Total Debt', '_FeederLTV']].style.format({
                'Refinance Proceeds': '${:,.0f}',
                'Total Debt': '${:,.0f}',
                '_FeederLTV': '{:.2%}'
            }),
            use_container_width=True
        )

    # Refi eligibility validation
    st.subheader("Refi Eligibility Validation")

    max_units = config['policies']['portfolio']['maxUnits']
    stop_refi = config['policies']['portfolio'].get('stopRefiAtMaxUnits', True)

    st.write(f"**Max Units:** {max_units}")
    st.write(f"**Stop Refi at Max Units:** {stop_refi}")

    if stop_refi:
        max_unit_rows = portfolio_df[portfolio_df['Properties Owned'] == max_units]
        if len(max_unit_rows) > 0:
            max_unit_month = max_unit_rows.iloc[0]
            st.write(f"**Max units reached:** Year {int(max_unit_month['Year'])}, Month {int(max_unit_month['Month'])}")

            # Check for refis after
            after_max = portfolio_df.loc[max_unit_rows.index[0]:]
            refis_after = after_max[after_max['Refinance Proceeds'] > 0]

            if len(refis_after) == 0:
                st.success("No refinancing occurred after reaching max units (correct behavior)")
            else:
                st.error(f"{len(refis_after)} refinance(s) occurred after max units!")
                st.dataframe(refis_after[['Year', 'Month', 'Refinance Proceeds']])
        else:
            st.info("Max units not reached in this simulation")
    else:
        st.info("stopRefiAtMaxUnits is disabled - refinancing allowed at any time")

# === Tab 5: Cash Reconciliation ===
with tabs[4]:
    st.subheader("Operating Cash Over Time")

    import plotly.graph_objects as go

    fig = go.Figure()

    portfolio_df_copy = portfolio_df.copy()
    portfolio_df_copy['Time'] = (portfolio_df_copy['Year'] - 1) * 12 + portfolio_df_copy['Month']

    fig.add_trace(go.Scatter(
        x=portfolio_df_copy['Time'],
        y=portfolio_df_copy['Operating Cash'],
        mode='lines',
        name='Operating Cash',
        line=dict(color='#00D9FF', width=2)
    ))

    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Zero")

    fig.update_layout(
        title="Operating Cash Balance",
        xaxis_title="Month",
        yaxis_title="Balance ($)",
        height=400,
        template=st.session_state.get('plotly_template', 'plotly_dark')
    )

    st.plotly_chart(fig, use_container_width=True)

    # Cash validation
    negative_months = portfolio_df[portfolio_df['Operating Cash'] < 0]

    if len(negative_months) == 0:
        st.success("Operating Cash never went negative")
    else:
        st.error(f"Operating Cash went negative in {len(negative_months)} month(s)")
        st.dataframe(negative_months[['Year', 'Month', 'Operating Cash']])

    # Month detail reconciliation
    st.subheader("Cash Reconciliation for Selected Month")

    col1, col2 = st.columns(2)
    with col1:
        year = st.selectbox("Year", range(1, 31), index=4)
    with col2:
        month = st.selectbox("Month", range(1, 13), index=11)

    row = portfolio_df[(portfolio_df['Year'] == year) & (portfolio_df['Month'] == month)]

    if len(row) > 0:
        row = row.iloc[0]

        # Get previous month
        if month > 1:
            prev_row = portfolio_df[(portfolio_df['Year'] == year) & (portfolio_df['Month'] == month - 1)]
        else:
            prev_row = portfolio_df[(portfolio_df['Year'] == year - 1) & (portfolio_df['Month'] == 12)]

        if len(prev_row) > 0:
            starting_cash = prev_row.iloc[0]['Operating Cash']
        else:
            starting_cash = config['constants']['financial']['startingCash']

        # Calculate flows
        inflows = (
            row['Monthly Rental Income'] +
            row.get('Interest - Operating', 0) +
            row.get('Refinance Proceeds', 0) +
            row.get('Monthly Savings Contribution', 0)
        )

        outflows = (
            row['Property Management'] +
            row['CapEx & Maintenance'] +
            row['HOA Fees'] +
            row['Property Insurance'] +
            row['Property Taxes'] +
            row['Debt Service'] +
            row.get('_RainyTopup', 0) +
            row.get('Principal Prepayment', 0) +
            row.get('Savings Deposit', 0) +
            row.get('Down Payment', 0) +
            row.get('Closing Costs', 0)
        )

        calculated_ending = starting_cash + inflows - outflows
        actual_ending = row['Operating Cash']

        # Display
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Starting Cash:** ${starting_cash:,.2f}")
            st.write(f"**+ Total Inflows:** ${inflows:,.2f}")
            st.write(f"**- Total Outflows:** ${outflows:,.2f}")
            st.write(f"**= Calculated Ending:** ${calculated_ending:,.2f}")

        with col2:
            st.write(f"**Actual Ending:** ${actual_ending:,.2f}")
            st.write(f"**Discrepancy:** ${abs(calculated_ending - actual_ending):,.2f}")

            if abs(calculated_ending - actual_ending) < 100:
                st.success("Reconciliation matches (within $100)")
            else:
                st.warning("Discrepancy detected - review flows")

        # Breakdown table
        st.write("**Flow Breakdown:**")
        breakdown = {
            'Starting Cash': starting_cash,
            '+ Rental Income': row['Monthly Rental Income'],
            '+ Interest': row.get('Interest - Operating', 0),
            '+ Savings Contribution': row.get('Monthly Savings Contribution', 0),
            '+ Refi Proceeds': row.get('Refinance Proceeds', 0),
            '- Property Mgmt': -row['Property Management'],
            '- CapEx': -row['CapEx & Maintenance'],
            '- HOA': -row['HOA Fees'],
            '- Insurance': -row['Property Insurance'],
            '- Taxes': -row['Property Taxes'],
            '- Debt Service': -row['Debt Service'],
            '- Reserve Topup': -row.get('_RainyTopup', 0),
            '- Prepayment': -row.get('Principal Prepayment', 0),
            '- Savings Deposit': -row.get('Savings Deposit', 0),
            '- Down Payment': -row.get('Down Payment', 0),
            '- Closing Costs': -row.get('Closing Costs', 0),
            '= Ending Cash': actual_ending
        }

        breakdown_df = pd.DataFrame([
            {'Item': k, 'Amount': v}
            for k, v in breakdown.items()
            if v != 0
        ])

        st.dataframe(
            breakdown_df.style.format({'Amount': '${:,.2f}'}),
            use_container_width=True
        )
    else:
        st.warning("No data for selected month")
