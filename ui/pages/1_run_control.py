"""
Page 1: Run Control & Config

Primary command center for rapid iteration.
- Edit configuration parameters
- Run simulations
- View immediate results
- Compare runs
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from components.config_editor import render_config_editor
from components.kpi_cards import render_kpi_cards, render_validation_summary
from components.charts import portfolio_value_chart, properties_timeline_chart
from utils.simulation_runner import (
    run_simulation, get_base_config,
    config_to_form_values, form_values_to_config
)
from utils.scenario_manager import list_scenarios, save_scenario, load_scenario, delete_scenario
from components.styles import apply_custom_styles

st.set_page_config(page_title="Run Control", page_icon="🎮", layout="wide")

# Apply custom CSS for tight spacing
apply_custom_styles()
# Initialize session state if needed
if 'config' not in st.session_state:
    st.session_state.config = get_base_config()

if 'portfolio_df' not in st.session_state:
    with st.spinner("Running initial simulation..."):
        result = run_simulation(st.session_state.config)
        st.session_state.portfolio_df = result.monthly
        st.session_state.units_df = result.units

if 'run_history' not in st.session_state:
    st.session_state.run_history = []

if 'form_values' not in st.session_state:
    st.session_state.form_values = config_to_form_values(st.session_state.config)

if 'previous_portfolio_df' not in st.session_state:
    st.session_state.previous_portfolio_df = None

# === HEADER with action buttons ===
header_col1, header_col2, header_col3, header_col4 = st.columns([5, 1, 2, 2])

with header_col1:
    st.title("Run Control & Config")

with header_col2:
    # Initialize simulation years if not set
    if 'simulation_years' not in st.session_state:
        st.session_state.simulation_years = 30

    sim_years = st.number_input(
        "Years",
        min_value=1,
        max_value=100,
        value=st.session_state.simulation_years,
        step=1,
        key="sim_years_input",
        help="Number of years to simulate (1-100)"
    )
    st.session_state.simulation_years = sim_years

with header_col3:
    run_button = st.button("▶ Run Simulation", type="primary", use_container_width=True, key="run_sim_header")

with header_col4:
    load_base_button = st.button("Load Base Case", use_container_width=True, key="load_base_header")

# Handle Load Base Case
if load_base_button:
    st.session_state.config = get_base_config()
    st.session_state.form_values = config_to_form_values(st.session_state.config)
    st.rerun()

# Handle simulation run
if run_button:
    # Save previous results for comparison
    st.session_state.previous_portfolio_df = st.session_state.portfolio_df.copy()

    # Build config from form values
    config = form_values_to_config(st.session_state.form_values)
    st.session_state.config = config

    # Get simulation years from session state (default to 30)
    sim_years = st.session_state.get('simulation_years', 30)

    with st.spinner(f"Running {sim_years}-year simulation..."):
        result = run_simulation(config, years=sim_years)
        st.session_state.portfolio_df = result.monthly
        st.session_state.units_df = result.units

    # Add to history
    final_row = result.monthly.iloc[-1]
    # Find debt-free year (must have had meaningful debt first, then paid it off)
    had_debt = result.monthly[result.monthly['Total Debt'] > 0]
    if len(had_debt) >= 12:
        last_debt_idx = had_debt.index[-1]
        after_last_debt = result.monthly.loc[last_debt_idx + 1:] if last_debt_idx + 1 < len(result.monthly) else pd.DataFrame()
        if len(after_last_debt) > 0 and after_last_debt.iloc[0]['Total Debt'] == 0:
            debt_free_year = int(after_last_debt.iloc[0]['Year'])
        else:
            debt_free_year = "N/A"
    elif len(had_debt) > 0:
        last_debt_idx = had_debt.index[-1]
        after_last_debt = result.monthly.loc[last_debt_idx + 1:] if last_debt_idx + 1 < len(result.monthly) else pd.DataFrame()
        if len(after_last_debt) > 0 and after_last_debt.iloc[0]['Total Debt'] == 0:
            debt_free_year = int(after_last_debt.iloc[0]['Year'])
        else:
            debt_free_year = "N/A"
    else:
        debt_free_year = "No debt"

    st.session_state.run_history.insert(0, {
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'scenario': 'Custom',
        'final_value': final_row['Total Portfolio Value'],
        'properties': int(final_row['Properties Owned']),
        'debt_free_year': debt_free_year,
        'form_values': st.session_state.form_values.copy()
    })

    # Keep only last 10 runs
    st.session_state.run_history = st.session_state.run_history[:10]

    st.success("Simulation complete!")
    st.rerun()

st.divider()

# === FULL-WIDTH RESULTS SECTION ===
st.subheader("Results")

if 'portfolio_df' in st.session_state:
    # KPI Cards - single row, 6 metrics
    render_kpi_cards(
        st.session_state.portfolio_df,
        st.session_state.config,
        st.session_state.previous_portfolio_df
    )

st.divider()

# === CONFIGURATION SECTION (Full Width) ===
st.subheader("Configuration")

# Render config editor
updated_values = render_config_editor(st.session_state.form_values)
st.session_state.form_values = updated_values

st.divider()

# === CHARTS SECTION ===
if 'portfolio_df' in st.session_state:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.plotly_chart(
            portfolio_value_chart(st.session_state.portfolio_df),
            use_container_width=True
        )

    with chart_col2:
        st.plotly_chart(
            properties_timeline_chart(st.session_state.portfolio_df),
            use_container_width=True
        )

    st.divider()

    # === HISTORY & VALIDATION (Bottom) ===
    col_history, col_validation = st.columns([1, 1])

    # === LEFT: Run History ===
    with col_history:
        st.subheader("Run History")

        if st.button("Clear History", key="clear_history", use_container_width=True):
            st.session_state.run_history = []
            st.session_state.previous_portfolio_df = None
            st.rerun()

        if st.session_state.run_history:
            # Build history table
            history_data = []
            for i, run in enumerate(st.session_state.run_history):
                history_data.append({
                    'Time': run['timestamp'],
                    'Final Value': f"${run['final_value']:,.0f}",
                    'Props': run['properties'],
                    'Debt-Free': run['debt_free_year']
                })

            history_df = pd.DataFrame(history_data)

            # Display with selection
            st.dataframe(
                history_df,
                use_container_width=True,
                height=250
            )

            # Select run to load
            run_to_load = st.selectbox(
                "Load previous run",
                options=range(len(st.session_state.run_history)),
                format_func=lambda x: f"{st.session_state.run_history[x]['timestamp']} - ${st.session_state.run_history[x]['final_value']:,.0f}",
                key="select_run_to_load"
            )

            if st.button("Load Selected Run", key="load_selected_run", use_container_width=True):
                selected_run = st.session_state.run_history[run_to_load]
                st.session_state.form_values = selected_run['form_values'].copy()
                st.success(f"Loaded run from {selected_run['timestamp']}")
                st.rerun()

        else:
            st.info("Run simulations to build history")

    # === RIGHT: Validation ===
    with col_validation:
        st.subheader("Validation")

        # Validation summary
        render_validation_summary(st.session_state.portfolio_df, st.session_state.config)

st.divider()

# === SCENARIO MANAGEMENT (Full Width) ===
col_scenarios, col_export = st.columns([2, 1])

with col_scenarios:
    st.subheader("Scenarios")

    scenarios = list_scenarios()
    if scenarios:
        selected_scenario = st.selectbox(
            "Load Saved Scenario",
            options=["-- Select --"] + scenarios,
            index=0
        )

        col_load, col_del, col_save_expand = st.columns(3)
        with col_load:
            if st.button("Load", disabled=selected_scenario == "-- Select --", use_container_width=True, key="load_scenario"):
                try:
                    loaded_config = load_scenario(selected_scenario)
                    st.session_state.config = loaded_config
                    st.session_state.form_values = config_to_form_values(loaded_config)
                    st.success(f"Loaded: {selected_scenario}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading scenario: {e}")
        with col_del:
            if st.button("Delete", disabled=selected_scenario == "-- Select --", use_container_width=True, key="delete_scenario"):
                if delete_scenario(selected_scenario):
                    st.success(f"Deleted: {selected_scenario}")
                    st.rerun()
                else:
                    st.error(f"Failed to delete: {selected_scenario}")
        with col_save_expand:
            save_scenario_expanded = st.checkbox("Save New", key="save_scenario_toggle")

    else:
        st.info("No saved scenarios found. Save your first scenario below.")
        save_scenario_expanded = True

    # Save scenario (inline or expanded based on checkbox)
    if save_scenario_expanded:
        st.write("**Save Current Config**")
        scenario_name = st.text_input("Scenario Name", value="my_scenario", key="scenario_name_input")
        if st.button("Save Scenario", key="save_scenario"):
            try:
                config = form_values_to_config(st.session_state.form_values)
                save_scenario(scenario_name, config)
                st.success(f"Saved: {scenario_name}")
            except Exception as e:
                st.error(f"Error saving: {e}")

with col_export:
    st.subheader("Export")

    # Export current config as JSON
    if st.button("📋 Export Config JSON", use_container_width=True, key="export_config_json"):
        import json
        config = form_values_to_config(st.session_state.form_values)
        config_json = json.dumps(config, indent=2)

        st.download_button(
            label="Download config.json",
            data=config_json,
            file_name=f"str_config_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            key="download_config_json",
            use_container_width=True
        )

    # Export current results as CSV
    if st.button("📊 Export Results CSV", use_container_width=True, key="export_results_csv"):
        csv_data = st.session_state.portfolio_df.to_csv(index=False)

        st.download_button(
            label="Download results.csv",
            data=csv_data,
            file_name=f"str_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_results_csv",
            use_container_width=True
        )
