"""
Page 7: Market Profiles & Seasonality

Configure and visualize market-specific seasonal revenue patterns.
- View and edit market profiles (Orange Beach, Generic, Custom)
- Interactive seasonality curve editor
- Revenue impact comparison (seasonal vs flat)
- Parity price impact visualization
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.simulation_runner import run_simulation, get_base_config
from components.styles import apply_custom_styles

# Page config
st.set_page_config(
    page_title="Market Profiles",
    page_icon="🏖️",
    layout="wide"
)

apply_custom_styles()

# Month names for display
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

MONTH_FULL_NAMES = ["January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"]


def get_template():
    """Get Plotly template based on dark mode setting."""
    return "plotly_dark" if st.session_state.get('dark_mode', True) else "plotly_white"


def initialize_session_state():
    """Initialize session state with base config and simulation results."""
    if 'config' not in st.session_state:
        st.session_state.config = get_base_config()

    if 'portfolio_df' not in st.session_state:
        result = run_simulation(st.session_state.config)
        if result:
            st.session_state.portfolio_df = result.monthly
            st.session_state.units_df = result.units


def get_market_profiles(config):
    """Extract market profiles from config."""
    return config.get("market_profiles", {})


def get_default_market(config):
    """Get the default market name."""
    policies = config.get("policies", {})
    portfolio = policies.get("portfolio", {})
    return portfolio.get("default_market", "orange_beach")


def create_seasonality_chart(market_profile, market_name):
    """Create interactive chart showing ADR and occupancy multipliers."""
    seasonality = market_profile.get("seasonality", {})
    adr_mults = seasonality.get("adr_multipliers", [1.0] * 12)
    occ_mults = seasonality.get("occupancy_multipliers", [1.0] * 12)

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("ADR Multipliers", "Occupancy Multipliers"),
        vertical_spacing=0.15
    )

    # ADR multipliers
    colors_adr = ['#FF6B6B' if m < 1 else '#00FF88' if m > 1 else '#00D9FF' for m in adr_mults]
    fig.add_trace(
        go.Bar(
            x=MONTH_NAMES,
            y=adr_mults,
            name="ADR Multiplier",
            marker_color=colors_adr,
            text=[f"{m:.2f}x" for m in adr_mults],
            textposition="outside"
        ),
        row=1, col=1
    )

    # Occupancy multipliers
    colors_occ = ['#FF6B6B' if m < 1 else '#00FF88' if m > 1 else '#00D9FF' for m in occ_mults]
    fig.add_trace(
        go.Bar(
            x=MONTH_NAMES,
            y=occ_mults,
            name="Occupancy Multiplier",
            marker_color=colors_occ,
            text=[f"{m:.2f}x" for m in occ_mults],
            textposition="outside"
        ),
        row=2, col=1
    )

    # Add reference line at 1.0
    fig.add_hline(y=1.0, line_dash="dash", line_color="gray", row=1, col=1)
    fig.add_hline(y=1.0, line_dash="dash", line_color="gray", row=2, col=1)

    fig.update_layout(
        title=f"Seasonal Multipliers - {market_profile.get('display_name', market_name)}",
        height=500,
        showlegend=False,
        template=get_template()
    )

    fig.update_yaxes(range=[0, 1.6], row=1, col=1)
    fig.update_yaxes(range=[0, 1.4], row=2, col=1)

    return fig


def create_revenue_comparison_chart(market_profile, base_adr=425.0):
    """Create chart comparing seasonal vs flat revenue."""
    seasonality = market_profile.get("seasonality", {})
    adr_mults = seasonality.get("adr_multipliers", [1.0] * 12)
    occ_mults = seasonality.get("occupancy_multipliers", [1.0] * 12)

    baseline = market_profile.get("baseline", {})
    base_occ = baseline.get("occupancy", 0.78)

    days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    seasonal_revenue = []
    flat_revenue = []

    for i in range(12):
        # Seasonal
        adr_eff = base_adr * adr_mults[i]
        occ_eff = base_occ * occ_mults[i]
        seasonal_rev = adr_eff * occ_eff * days_per_month[i]
        seasonal_revenue.append(seasonal_rev)

        # Flat
        flat_rev = base_adr * base_occ * days_per_month[i]
        flat_revenue.append(flat_rev)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=MONTH_NAMES,
        y=seasonal_revenue,
        name="Seasonal Revenue",
        marker_color='#00D9FF'
    ))

    fig.add_trace(go.Scatter(
        x=MONTH_NAMES,
        y=flat_revenue,
        name="Flat Revenue (Baseline)",
        mode='lines+markers',
        line=dict(color='#FFB347', width=3, dash='dash'),
        marker=dict(size=8)
    ))

    annual_seasonal = sum(seasonal_revenue)
    annual_flat = sum(flat_revenue)
    delta = annual_seasonal - annual_flat
    delta_pct = (delta / annual_flat) * 100 if annual_flat > 0 else 0

    fig.update_layout(
        title=f"Monthly Revenue Comparison (Annual: ${annual_seasonal:,.0f} seasonal vs ${annual_flat:,.0f} flat = {delta_pct:+.1f}%)",
        xaxis_title="Month",
        yaxis_title="Revenue ($)",
        height=400,
        template=get_template(),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig, annual_seasonal, annual_flat


def render_market_profile_editor(market_name, market_profile, is_default=False):
    """Render editor for a single market profile."""
    with st.expander(f"📊 {market_profile.get('display_name', market_name)}" +
                     (" (Default)" if is_default else ""), expanded=is_default):

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"**Description:** {market_profile.get('description', 'No description')}")

            seasonality_enabled = market_profile.get("seasonality_enabled", False)
            st.markdown(f"**Seasonality:** {'Enabled' if seasonality_enabled else 'Disabled'}")

            baseline = market_profile.get("baseline", {})
            st.markdown(f"**Baseline ADR:** ${baseline.get('adr', 0):,.2f}")
            st.markdown(f"**Baseline Occupancy:** {baseline.get('occupancy', 0)*100:.1f}%")

        with col2:
            expenses = market_profile.get("expenses", {})
            st.markdown(f"**Insurance Rate:** {expenses.get('insurance_rate', 0)*100:.2f}%")
            st.markdown(f"**Property Tax Rate:** {expenses.get('property_tax_rate', 0)*100:.3f}%")
            st.markdown(f"**HOA Annual:** ${expenses.get('hoa_annual', 0):,.0f}")

        if seasonality_enabled:
            # Seasonality chart
            st.plotly_chart(
                create_seasonality_chart(market_profile, market_name),
                use_container_width=True
            )

            # Revenue comparison
            base_adr = baseline.get("adr", 425.0)
            fig, annual_seasonal, annual_flat = create_revenue_comparison_chart(
                market_profile, base_adr
            )
            st.plotly_chart(fig, use_container_width=True)

            # Key metrics
            delta = annual_seasonal - annual_flat
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Annual Seasonal Revenue", f"${annual_seasonal:,.0f}")
            with col2:
                st.metric("Annual Flat Revenue", f"${annual_flat:,.0f}")
            with col3:
                st.metric("Seasonal Impact", f"${delta:,.0f}",
                         delta=f"{(delta/annual_flat)*100:.1f}%" if annual_flat > 0 else "0%")


def render_seasonality_editor_table(market_profile):
    """Render editable table for seasonality multipliers."""
    seasonality = market_profile.get("seasonality", {})
    adr_mults = seasonality.get("adr_multipliers", [1.0] * 12)
    occ_mults = seasonality.get("occupancy_multipliers", [1.0] * 12)

    st.subheader("Seasonality Multiplier Editor")

    df = pd.DataFrame({
        "Month": MONTH_FULL_NAMES,
        "ADR Multiplier": adr_mults,
        "Occupancy Multiplier": occ_mults
    })

    # Display as formatted table
    st.dataframe(
        df.style.format({
            "ADR Multiplier": "{:.2f}",
            "Occupancy Multiplier": "{:.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )

    return df


def render_parity_price_impact(config):
    """Show how seasonality affects parity price over time."""
    st.subheader("Parity Price Impact")

    # Import calculation functions
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ob_str_engine" / "engine"))
    from acquisition import calculate_parity_price

    years = [1, 5, 10, 15, 20, 25, 30]

    # Calculate with seasonality
    prices_seasonal = []
    for year in years:
        price = calculate_parity_price(year, config)
        prices_seasonal.append(price)

    # Calculate without seasonality (remove market_profiles temporarily)
    config_flat = json.loads(json.dumps(config))
    if "market_profiles" in config_flat:
        del config_flat["market_profiles"]

    prices_flat = []
    for year in years:
        price = calculate_parity_price(year, config_flat)
        prices_flat.append(price)

    # Create comparison chart
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=years,
        y=prices_seasonal,
        name="Seasonal Parity Price",
        mode='lines+markers',
        line=dict(color='#00D9FF', width=3),
        marker=dict(size=10)
    ))

    fig.add_trace(go.Scatter(
        x=years,
        y=prices_flat,
        name="Flat Parity Price",
        mode='lines+markers',
        line=dict(color='#FFB347', width=3, dash='dash'),
        marker=dict(size=10)
    ))

    fig.update_layout(
        title="Parity Price Comparison: Seasonal vs Flat",
        xaxis_title="Year",
        yaxis_title="Parity Price ($)",
        height=400,
        template=get_template(),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Summary table
    delta_pct = [(s - f) / f * 100 if f > 0 else 0 for s, f in zip(prices_seasonal, prices_flat)]

    summary_df = pd.DataFrame({
        "Year": years,
        "Seasonal Price": [f"${p:,.0f}" for p in prices_seasonal],
        "Flat Price": [f"${p:,.0f}" for p in prices_flat],
        "Difference": [f"{d:+.1f}%" for d in delta_pct]
    })

    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    # Key insight
    avg_delta = sum(delta_pct) / len(delta_pct)
    if avg_delta < 0:
        st.info(f"**Insight:** Seasonal pricing results in {abs(avg_delta):.1f}% lower parity prices on average, "
                "reflecting more realistic revenue expectations for seasonal markets.")
    else:
        st.info(f"**Insight:** Seasonal pricing results in {avg_delta:.1f}% higher parity prices on average.")


# Main page
st.title("🏖️ Market Profiles & Seasonality")

st.markdown("""
Configure market-specific seasonal revenue patterns. Seasonality adjusts ADR and occupancy
by month, providing more realistic projections for vacation rental markets.
""")

initialize_session_state()

config = st.session_state.config
market_profiles = get_market_profiles(config)
default_market = get_default_market(config)

st.divider()

# Check if market profiles exist
if not market_profiles:
    st.warning("No market profiles configured. Using default flat assumptions (v2.3 behavior).")
    st.info("Add a `market_profiles` section to your config to enable seasonality.")
else:
    # Display current default market
    st.subheader("Portfolio Default Market")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**Current Default:** {default_market}")
        if default_market in market_profiles:
            profile = market_profiles[default_market]
            st.markdown(f"*{profile.get('description', 'No description')}*")
    with col2:
        enabled = market_profiles.get(default_market, {}).get("seasonality_enabled", False)
        if enabled:
            st.success("Seasonality ON")
        else:
            st.warning("Seasonality OFF")

    st.divider()

    # Market Profile Details
    st.subheader("Market Profile Details")

    for market_name, market_profile in market_profiles.items():
        is_default = (market_name == default_market)
        render_market_profile_editor(market_name, market_profile, is_default)

    st.divider()

    # Parity Price Impact
    render_parity_price_impact(config)

st.divider()

# Footer with explanation
with st.expander("About Seasonality Modeling"):
    st.markdown("""
    ### How Seasonality Works

    **ADR Multipliers** adjust the Average Daily Rate by month:
    - Values > 1.0 = Higher rates (peak season)
    - Values < 1.0 = Lower rates (off-season)
    - Value = 1.0 = No adjustment

    **Occupancy Multipliers** adjust occupancy rates:
    - Values > 1.0 = Higher occupancy (peak season)
    - Values < 1.0 = Lower occupancy (off-season)
    - Value = 1.0 = No adjustment

    ### Orange Beach Seasonal Pattern

    | Season | Months | ADR | Occupancy |
    |--------|--------|-----|-----------|
    | Peak | Jun-Aug | +35% | 90% |
    | Shoulder | Mar-May, Sep-Oct | +10% | 70% |
    | Off-Season | Nov-Feb | -15% | 45% |

    ### Impact on Parity Price

    Seasonal revenue calculations typically result in **lower annual revenue** compared
    to flat assumptions, because the higher peak-season revenue doesn't fully offset
    the lower off-season revenue. This leads to:

    - **Lower parity prices** (more realistic target purchase price)
    - **Faster acquisition timeline** (need less capital per property)
    - **More accurate cash flow projections** (monthly variance visible)
    """)
