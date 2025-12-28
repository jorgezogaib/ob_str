"""
Page 6: Scenario Comparison Matrix

Compare multiple saved scenarios side-by-side.
- Run multiple scenarios
- Comparison table
- Overlay charts
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from components.charts import scenario_comparison_chart
from utils.simulation_runner import run_simulation, get_base_config
from utils.scenario_manager import list_scenarios, load_scenario

st.set_page_config(page_title="Scenario Comparison", page_icon="📊", layout="wide")

st.title("Scenario Comparison Matrix")

# Initialize session state for scenario results
if 'scenario_results' not in st.session_state:
    st.session_state.scenario_results = {}

# Scenario manager
st.subheader("Scenario Manager")

# List saved scenarios
scenario_files = list_scenarios()

col1, col2 = st.columns([3, 1])

with col1:
    if scenario_files:
        selected_scenarios = st.multiselect(
            "Select scenarios to compare",
            options=scenario_files,
            default=scenario_files[:3] if len(scenario_files) >= 3 else scenario_files
        )
    else:
        st.info("No saved scenarios found. Save scenarios from the Run Control page.")
        selected_scenarios = []

    # Option to include base case
    include_base = st.checkbox("Include Base Case", value=True)

with col2:
    run_selected = st.button("Run All Selected", type="primary", use_container_width=True)

    if st.button("Clear Results", use_container_width=True):
        st.session_state.scenario_results = {}
        st.rerun()

# Run scenarios
if run_selected:
    scenarios_to_run = []

    if include_base:
        scenarios_to_run.append(("Base Case", get_base_config()))

    for scenario_name in selected_scenarios:
        try:
            config = load_scenario(scenario_name)
            scenarios_to_run.append((scenario_name, config))
        except Exception as e:
            st.error(f"Error loading {scenario_name}: {e}")

    if scenarios_to_run:
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, (name, config) in enumerate(scenarios_to_run):
            status_text.text(f"Running {name}...")
            result = run_simulation(config)

            st.session_state.scenario_results[name] = {
                'portfolio_df': result.monthly,
                'units_df': result.units,
                'config': config
            }

            progress_bar.progress((i + 1) / len(scenarios_to_run))

        status_text.text(f"Completed {len(scenarios_to_run)} scenario(s)")
        st.success(f"Ran {len(scenarios_to_run)} scenario(s)")
        st.rerun()

st.divider()

# Display results
if st.session_state.scenario_results:
    st.subheader("Scenario Comparison")

    # Build comparison table
    comparison_data = []

    for scenario_name, results in st.session_state.scenario_results.items():
        portfolio_df = results['portfolio_df']
        units_df = results['units_df']
        config = results['config']

        final_row = portfolio_df.iloc[-1]

        # Find debt-free year (must have had meaningful debt first, then paid it off)
        had_debt = portfolio_df[portfolio_df['Total Debt'] > 0]
        if len(had_debt) >= 12:
            last_debt_idx = had_debt.index[-1]
            after_last_debt = portfolio_df.loc[last_debt_idx + 1:] if last_debt_idx + 1 < len(portfolio_df) else pd.DataFrame()
            if len(after_last_debt) > 0 and after_last_debt.iloc[0]['Total Debt'] == 0:
                debt_free_year = int(after_last_debt.iloc[0]['Year'])
            else:
                debt_free_year = "N/A"
        elif len(had_debt) > 0:
            last_debt_idx = had_debt.index[-1]
            after_last_debt = portfolio_df.loc[last_debt_idx + 1:] if last_debt_idx + 1 < len(portfolio_df) else pd.DataFrame()
            if len(after_last_debt) > 0 and after_last_debt.iloc[0]['Total Debt'] == 0:
                debt_free_year = int(after_last_debt.iloc[0]['Year'])
            else:
                debt_free_year = "N/A"
        else:
            debt_free_year = "No debt"

        # Find year when max units reached
        max_units = config['policies']['portfolio']['maxUnits']
        max_unit_rows = portfolio_df[portfolio_df['Properties Owned'] == max_units]
        if len(max_unit_rows) > 0:
            max_units_year = int(max_unit_rows.iloc[0]['Year'])
        else:
            max_units_year = "N/A"

        # Calculate average CoC if units exist
        if len(units_df) > 0:
            final_units = units_df.groupby('Unit_ID').last()
            avg_coc = final_units['Unit_Cash_On_Cash_Return'].mean()
        else:
            avg_coc = 0

        comparison_data.append({
            'Scenario': scenario_name,
            'Final Value': final_row['Total Portfolio Value'],
            'Final Debt': final_row['Total Debt'],
            'Final Equity': final_row['Total Equity'],
            'Final Cash': final_row['Total Cash Reserves'],
            'Properties': int(final_row['Properties Owned']),
            'Year Max Units': max_units_year,
            'Year Debt-Free': debt_free_year,
            'Avg CoC %': avg_coc
        })

    comp_df = pd.DataFrame(comparison_data)

    # Highlight best values
    def highlight_best(s):
        if s.name in ['Final Value', 'Final Equity', 'Final Cash', 'Properties', 'Avg CoC %']:
            is_max = s == s.max()
            return ['background-color: #00ff8840' if v else '' for v in is_max]
        elif s.name in ['Final Debt']:
            is_min = s == s.min()
            return ['background-color: #00ff8840' if v else '' for v in is_min]
        elif s.name in ['Year Debt-Free', 'Year Max Units']:
            # For year columns, lower is better (but handle N/A)
            numeric_vals = pd.to_numeric(s, errors='coerce')
            is_min = numeric_vals == numeric_vals.min()
            return ['background-color: #00ff8840' if v else '' for v in is_min]
        else:
            return ['' for _ in s]

    styled_comp = comp_df.style.apply(highlight_best).format({
        'Final Value': '${:,.0f}',
        'Final Debt': '${:,.0f}',
        'Final Equity': '${:,.0f}',
        'Final Cash': '${:,.0f}',
        'Avg CoC %': '{:.1f}%'
    })

    st.dataframe(styled_comp, use_container_width=True)

    st.caption("Green = best value for each metric")

    st.divider()

    # Overlay charts
    st.subheader("Portfolio Value Over Time (All Scenarios)")

    fig_value = go.Figure()

    colors = ['#00D9FF', '#FF6B6B', '#00FF88', '#FFB347', '#E066FF', '#77DD77']

    for i, (scenario_name, results) in enumerate(st.session_state.scenario_results.items()):
        portfolio_df = results['portfolio_df']
        portfolio_df = portfolio_df.copy()
        portfolio_df['Time'] = portfolio_df['Year'] + portfolio_df['Month']/12

        fig_value.add_trace(go.Scatter(
            x=portfolio_df['Time'],
            y=portfolio_df['Total Portfolio Value'],
            mode='lines',
            name=scenario_name,
            line=dict(color=colors[i % len(colors)], width=2)
        ))

    fig_value.update_layout(
        title="Portfolio Value Comparison",
        xaxis_title="Year",
        yaxis_title="Portfolio Value ($)",
        hovermode='x unified',
        height=500,
        template=st.session_state.get('plotly_template', 'plotly_dark')
    )

    st.plotly_chart(fig_value, use_container_width=True)

    # Debt comparison
    st.subheader("Debt Payoff Trajectories")

    fig_debt = go.Figure()

    for i, (scenario_name, results) in enumerate(st.session_state.scenario_results.items()):
        portfolio_df = results['portfolio_df']
        portfolio_df = portfolio_df.copy()
        portfolio_df['Time'] = portfolio_df['Year'] + portfolio_df['Month']/12

        fig_debt.add_trace(go.Scatter(
            x=portfolio_df['Time'],
            y=portfolio_df['Total Debt'],
            mode='lines',
            name=scenario_name,
            line=dict(color=colors[i % len(colors)], width=2)
        ))

    fig_debt.update_layout(
        title="Debt Payoff Comparison",
        xaxis_title="Year",
        yaxis_title="Total Debt ($)",
        hovermode='x unified',
        height=500,
        template=st.session_state.get('plotly_template', 'plotly_dark')
    )

    st.plotly_chart(fig_debt, use_container_width=True)

    # Properties comparison
    st.subheader("Acquisition Pace Comparison")

    fig_props = go.Figure()

    for i, (scenario_name, results) in enumerate(st.session_state.scenario_results.items()):
        portfolio_df = results['portfolio_df']
        portfolio_df = portfolio_df.copy()
        portfolio_df['Time'] = portfolio_df['Year'] + portfolio_df['Month']/12

        fig_props.add_trace(go.Scatter(
            x=portfolio_df['Time'],
            y=portfolio_df['Properties Owned'],
            mode='lines',
            name=scenario_name,
            line=dict(color=colors[i % len(colors)], width=2, shape='hv')
        ))

    fig_props.update_layout(
        title="Properties Owned Over Time",
        xaxis_title="Year",
        yaxis_title="Properties",
        hovermode='x unified',
        height=400,
        template=st.session_state.get('plotly_template', 'plotly_dark')
    )

    st.plotly_chart(fig_props, use_container_width=True)

    st.divider()

    # Config differences
    st.subheader("Configuration Differences")

    if len(st.session_state.scenario_results) >= 2:
        scenario_names = list(st.session_state.scenario_results.keys())

        col1, col2 = st.columns(2)
        with col1:
            scenario_a = st.selectbox("Scenario A", scenario_names, index=0)
        with col2:
            scenario_b = st.selectbox("Scenario B", scenario_names, index=min(1, len(scenario_names)-1))

        if scenario_a != scenario_b:
            config_a = st.session_state.scenario_results[scenario_a]['config']
            config_b = st.session_state.scenario_results[scenario_b]['config']

            # Flatten configs for comparison
            def flatten_config(cfg, prefix=''):
                items = {}
                for k, v in cfg.items():
                    key = f"{prefix}{k}" if prefix else k
                    if isinstance(v, dict):
                        items.update(flatten_config(v, f"{key}."))
                    else:
                        items[key] = v
                return items

            flat_a = flatten_config(config_a)
            flat_b = flatten_config(config_b)

            # Find differences
            diffs = []
            for key in set(flat_a.keys()) | set(flat_b.keys()):
                val_a = flat_a.get(key, 'N/A')
                val_b = flat_b.get(key, 'N/A')

                if val_a != val_b:
                    diffs.append({
                        'Parameter': key,
                        scenario_a: val_a,
                        scenario_b: val_b
                    })

            if diffs:
                diff_df = pd.DataFrame(diffs)
                st.dataframe(diff_df, use_container_width=True)
            else:
                st.info("No configuration differences found")
        else:
            st.info("Select two different scenarios to compare")

else:
    st.info("Run scenarios to see comparison results")

    # Quick start
    st.subheader("Quick Start")
    st.markdown("""
    1. **Save scenarios** from the Run Control page with different configurations
    2. **Select scenarios** to compare from the list above
    3. **Run All Selected** to simulate each scenario
    4. **Compare results** using the tables and charts

    Or check "Include Base Case" and click "Run All Selected" to start with the default configuration.
    """)
