"""
STR Investment Model - Refinement Workbench

Main entry point for the Streamlit dashboard.
A power tool for rapid model iteration and validation.
"""

import streamlit as st
from pathlib import Path
import sys
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import shared styles
from components.styles import apply_custom_styles
from utils.simulation_runner import run_simulation, get_base_config, config_to_form_values
from utils.scenario_manager import list_scenarios, save_scenario, load_scenario, delete_scenario

st.set_page_config(
    page_title="STR Model Refinement Workbench",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set plotly template (dark mode is default via config.toml)
if 'plotly_template' not in st.session_state:
    st.session_state.plotly_template = "plotly_dark"

# Sidebar
with st.sidebar:
    st.title("STR Workbench")
    st.divider()
    st.caption("Navigate using sidebar pages")
    st.caption("Start with Run Control to configure and run simulations")

# Main content
st.title("STR Investment Model")
st.subheader("Refinement Workbench")

# Initialize session state
if 'initialized' not in st.session_state:
    from utils.simulation_runner import run_simulation, get_base_config

    # Load base case config
    st.session_state.config = get_base_config()

    # Run initial simulation
    with st.spinner("Running initial simulation..."):
        result = run_simulation(st.session_state.config)
        st.session_state.portfolio_df = result.monthly
        st.session_state.units_df = result.units

    st.session_state.run_history = []
    st.session_state.initialized = True

# Display quick status
col1, col2, col3, col4, col5 = st.columns(5)

if 'portfolio_df' in st.session_state:
    df = st.session_state.portfolio_df
    final_row = df.iloc[-1]

    with col1:
        val = final_row['Total Portfolio Value']
        st.metric("Portfolio Value", f"${val/1_000_000:.2f}M")

    with col2:
        st.metric(
            "Properties",
            f"{int(final_row['Properties Owned'])} of {st.session_state.config['policies']['portfolio']['maxUnits']}"
        )

    with col3:
        # Find debt-free year (must have had meaningful debt first, then paid it off)
        had_debt = df[df['Total Debt'] > 0]
        if len(had_debt) >= 12:  # Had at least 12 months of debt
            last_debt_idx = had_debt.index[-1]
            after_last_debt = df.loc[last_debt_idx + 1:] if last_debt_idx + 1 < len(df) else pd.DataFrame()
            if len(after_last_debt) > 0 and after_last_debt.iloc[0]['Total Debt'] == 0:
                debt_free_year = int(after_last_debt.iloc[0]['Year'])
                st.metric("Debt-Free", f"Year {debt_free_year}")
            else:
                st.metric("Debt-Free", "Not achieved")
        elif len(had_debt) > 0:
            st.metric("Debt-Free", "Not achieved")
        else:
            st.metric("Debt-Free", "No debt")

    with col4:
        cash = final_row['Total Cash Reserves']
        st.metric("Cash Reserves", f"${cash/1_000_000:.2f}M")

    with col5:
        if 'Distribution Amount' in df.columns:
            total_dist = df['Distribution Amount'].sum()
            if total_dist > 0:
                st.metric("Total Distributions", f"${total_dist/1_000_000:.2f}M")
            else:
                st.metric("Total Distributions", "$0")
        else:
            st.metric("Total Distributions", "N/A")

st.divider()

# === SCENARIO MANAGEMENT & RUN SIMULATION ===
st.subheader("Scenario Management")

col_scenarios, col_actions = st.columns([2, 1])

with col_scenarios:
    scenarios = list_scenarios()
    if scenarios:
        selected_scenario = st.selectbox(
            "Load Saved Scenario",
            options=["-- Select --"] + scenarios,
            index=0
        )

        col_load, col_del, col_save_expand = st.columns(3)
        with col_load:
            if st.button("Load", disabled=selected_scenario == "-- Select --", use_container_width=True, key="load_scenario_app"):
                try:
                    loaded_config = load_scenario(selected_scenario)
                    st.session_state.config = loaded_config
                    if 'form_values' not in st.session_state:
                        st.session_state.form_values = {}
                    st.session_state.form_values = config_to_form_values(loaded_config)
                    st.success(f"Loaded: {selected_scenario}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading scenario: {e}")
        with col_del:
            if st.button("Delete", disabled=selected_scenario == "-- Select --", use_container_width=True, key="delete_scenario_app"):
                if delete_scenario(selected_scenario):
                    st.success(f"Deleted: {selected_scenario}")
                    st.rerun()
                else:
                    st.error(f"Failed to delete: {selected_scenario}")
        with col_save_expand:
            save_scenario_expanded = st.checkbox("Save New", key="save_scenario_toggle_app")
    else:
        st.info("No saved scenarios found. Save your first scenario below.")
        save_scenario_expanded = True

    # Save scenario (inline or expanded based on checkbox)
    if save_scenario_expanded or not scenarios:
        st.write("**Save Current Config**")
        scenario_name = st.text_input("Scenario Name", value="my_scenario", key="scenario_name_input_app")
        if st.button("Save Scenario", key="save_scenario_app"):
            try:
                save_scenario(scenario_name, st.session_state.config)
                st.success(f"Saved: {scenario_name}")
            except Exception as e:
                st.error(f"Error saving: {e}")

with col_actions:
    st.write("**Run Simulation**")

    # Initialize simulation years if not set
    if 'simulation_years' not in st.session_state:
        st.session_state.simulation_years = 30

    sim_years = st.number_input(
        "Simulation Years",
        min_value=1,
        max_value=100,
        value=st.session_state.simulation_years,
        step=1,
        key="sim_years_input_app",
        help="Number of years to simulate (1-100)"
    )
    st.session_state.simulation_years = sim_years

    if st.button("▶ Run Simulation", type="primary", use_container_width=True, key="run_sim_app"):
        # Save previous results for comparison
        if 'portfolio_df' in st.session_state:
            st.session_state.previous_portfolio_df = st.session_state.portfolio_df.copy()

        with st.spinner(f"Running {sim_years}-year simulation..."):
            result = run_simulation(st.session_state.config, years=sim_years)
            if result is not None:
                st.session_state.portfolio_df = result.monthly
                st.session_state.units_df = result.units
                st.success("Simulation complete!")
                st.rerun()
            else:
                st.error("Simulation failed - check configuration")

    st.write("**Export**")
    # Export current config as JSON
    if st.button("📋 Config JSON", use_container_width=True, key="export_config_json_app"):
        import json
        config_json = json.dumps(st.session_state.config, indent=2)

        st.download_button(
            label="Download config.json",
            data=config_json,
            file_name=f"str_config_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            key="download_config_json_app",
            use_container_width=True
        )

    # Export current results as CSV
    if 'portfolio_df' in st.session_state:
        if st.button("📊 Results CSV", use_container_width=True, key="export_results_csv_app"):
            csv_data = st.session_state.portfolio_df.to_csv(index=False)

            st.download_button(
                label="Download results.csv",
                data=csv_data,
                file_name=f"str_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_results_csv_app",
                use_container_width=True
            )

st.divider()

# Apply custom CSS for styling
apply_custom_styles()
