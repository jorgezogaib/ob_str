"""
Config Editor Component - Tabbed form for editing configuration
"""

import streamlit as st
from typing import Dict, Any


def render_config_editor(form_values: Dict[str, Any]) -> Dict[str, Any]:
    """
    Render the configuration editor with tabs.

    Args:
        form_values: Current form values

    Returns:
        Updated form values dict
    """
    updated = form_values.copy()

    # Create tabs for all sections with improved spacing and visibility
    st.markdown("""
        <style>
        /* Make tabs more pronounced and clickable */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: rgba(28, 131, 225, 0.1);
            padding: 10px;
            border-radius: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: rgba(38, 39, 48, 0.8);
            border-radius: 5px;
            padding: 10px 20px;
            font-weight: 600;
            font-size: 14px;
        }
        .stTabs [aria-selected="true"] {
            background-color: rgba(28, 131, 225, 0.8);
        }
        .stTabs [data-baseweb="tab"]:hover {
            background-color: rgba(28, 131, 225, 0.4);
        }
        </style>
    """, unsafe_allow_html=True)

    tabs = st.tabs([
        "💰 Financial",
        "🏠 Operations",
        "📈 Acquisition & Debt",
        "🏦 Reserves & Banking",
        "💸 Distributions",
        "📊 Market",
        "📅 Seasonality",
        "🏛️ Tax",
        "🛡️ Insurance",
        "⚡ Events",
        "🔧 CapEx",
        "💳 Financing",
        "🚪 Exit Strategy",
        "✓ Validation"
    ])

    # Tab 1: Financial & Capital Allocation
    with tabs[0]:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Initial Capital**")
            updated["startingCash"] = st.number_input(
                "Starting Cash ($)",
                min_value=0.0,
                value=float(form_values["startingCash"]),
                step=1000.0,
                format="%.0f",
                help="Initial cash on hand before any investments. Used for first property down payment."
            )
            updated["annualSavings"] = st.number_input(
                "Annual Savings ($)",
                min_value=0.0,
                value=float(form_values["annualSavings"]),
                step=5000.0,
                format="%.0f",
                help="Amount added to cash each year from external income (salary, business, etc). Divided by 12 and added monthly."
            )

        with col2:
            st.markdown("**Loan Terms**")
            updated["amortizationYears"] = st.number_input(
                "Amortization Years",
                min_value=10,
                max_value=40,
                value=int(form_values["amortizationYears"]),
                step=1,
                help="Loan term length for mortgage calculations. Affects monthly payment amount."
            )

        with col3:
            st.markdown("**Capital Allocation**")

            # Single slider that controls both allocations
            feeder_pct = st.slider(
                "Feeder Prepayment % (remainder goes to Savings)",
                min_value=0.0,
                max_value=1.0,
                value=float(form_values["feederPrepaymentPct"]),
                step=0.05,
                format="%.2f",
                help="% of surplus cash flow to feeder property prepayment. The remainder automatically goes to savings accumulation."
            )

            updated["feederPrepaymentPct"] = feeder_pct
            updated["savingsAccumulationPct"] = 1.0 - feeder_pct

            # Show current allocation status
            st.info(f"Feeder: {feeder_pct:.0%} | Savings: {(1.0-feeder_pct):.0%}")

    # Tab 2: Property Operations
    with tabs[1]:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Revenue**")
            updated["adrBaseline2BR"] = st.number_input(
                "ADR Baseline 2BR ($)",
                min_value=100.0,
                max_value=1000.0,
                value=float(form_values["adrBaseline2BR"]),
                step=25.0,
                format="%.0f",
                help="Average Daily Rate for a 2-bedroom unit. Base rental income before occupancy adjustment."
            )
            updated["occupancyBaseline"] = st.slider(
                "Occupancy Baseline",
                min_value=0.50,
                max_value=1.0,
                value=float(form_values["occupancyBaseline"]),
                step=0.01,
                format="%.2f",
                help="Expected occupancy rate (0.78 = 78%). Multiplied by ADR to get actual revenue."
            )
            updated["mgmtPct"] = st.slider(
                "Management %",
                min_value=0.0,
                max_value=0.50,
                value=float(form_values["mgmtPct"]),
                step=0.01,
                format="%.2f",
                help="Property management fee as % of gross revenue. Covers booking, cleaning coordination, guest communication."
            )

        with col2:
            st.markdown("**Expenses**")
            updated["capexPct"] = st.slider(
                "CapEx %",
                min_value=0.0,
                max_value=0.30,
                value=float(form_values["capexPct"]),
                step=0.01,
                format="%.2f",
                help="Capital expenditure reserve as % of revenue. Funds furniture replacement, repairs, upgrades."
            )
            updated["hoaAnnual"] = st.number_input(
                "HOA Annual ($)",
                min_value=0.0,
                value=float(form_values["hoaAnnual"]),
                step=500.0,
                format="%.0f",
                help="Annual HOA fees per property. Covers common area maintenance, amenities, building insurance."
            )
            updated["hoaInflationRate"] = st.slider(
                "HOA Inflation Rate",
                min_value=0.0,
                max_value=0.10,
                value=float(form_values["hoaInflationRate"]),
                step=0.005,
                format="%.3f",
                help="Annual increase in HOA fees. HOA fees tend to rise faster than general inflation."
            )

        with col3:
            st.markdown("**Taxes & Other**")
            updated["insuranceRate"] = st.slider(
                "Insurance Rate",
                min_value=0.0,
                max_value=0.10,
                value=float(form_values["insuranceRate"]),
                step=0.001,
                format="%.3f",
                help="Annual insurance cost as % of property value. Covers hazard, liability, loss of income."
            )
            updated["propertyTaxRate"] = st.slider(
                "Property Tax Rate",
                min_value=0.0,
                max_value=0.02,
                value=float(form_values["propertyTaxRate"]),
                step=0.0005,
                format="%.4f",
                help="Annual property tax as % of assessed value. Varies by location (AZ ~0.55%)."
            )
            updated["liquidityReserveMultiplier"] = st.slider(
                "Liquidity Reserve Multiplier",
                min_value=0.5,
                max_value=2.0,
                value=float(form_values.get("liquidityReserveMultiplier", 1.0)),
                step=0.1,
                format="%.1f",
                help="Multiplier for liquidity reserve requirements. Higher = more conservative cash management."
            )

    # Tab 3: Acquisition & Debt
    with tabs[2]:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Acquisition**")
            updated["downPaymentFirst"] = st.slider(
            "Down Payment (First)",
            min_value=0.10,
            max_value=1.0,
            value=float(form_values["downPaymentFirst"]),
            step=0.05,
            format="%.2f",
            help="Down payment % for first property. 1.0 = all-cash purchase. Often lower (20%) for owner-occupied."
            )
            updated["downPaymentSubsequent"] = st.slider(
                "Down Payment (Subsequent)",
                min_value=0.10,
                max_value=1.0,
                value=float(form_values["downPaymentSubsequent"]),
                step=0.05,
                format="%.2f",
                help="Down payment % for properties 2+. 1.0 = all-cash. Investment properties typically require 25%."
            )
            updated["closingCostPct"] = st.slider(
                "Closing Cost %",
                min_value=0.01,
                max_value=0.10,
                value=float(form_values["closingCostPct"]),
                step=0.005,
                format="%.3f",
                help="Closing costs as % of purchase price. Includes title, escrow, lender fees, inspections."
            )
            updated["maxUnits"] = st.number_input(
                "Max Units",
                min_value=1,
                max_value=20,
                value=int(form_values["maxUnits"]),
                step=1,
                help="Maximum properties to acquire. Model stops buying and shifts to debt payoff at this limit."
            )

        with col2:
            st.markdown("**Refinance**")
            updated["targetYieldUnlevered"] = st.slider(
                "Target Yield (Unlevered)",
                min_value=0.03,
                max_value=0.10,
                value=float(form_values["targetYieldUnlevered"]),
                step=0.005,
                format="%.3f",
                help="Required cap rate for acquisitions. NOI / Purchase Price. Higher = more conservative pricing."
            )
            updated["maxPostRefiLTV"] = st.slider(
                "Max Post-Refi LTV",
                min_value=0.60,
                max_value=0.85,
                value=float(form_values["maxPostRefiLTV"]),
                step=0.05,
                format="%.2f",
                help="Maximum LTV after cash-out refinance. Lenders typically cap at 75% for investment properties."
            )
            updated["refiCooldownYears"] = st.number_input(
                "Refi Cooldown (Years)",
                min_value=0,
                max_value=10,
                value=int(form_values["refiCooldownYears"]),
                step=1,
                help="Minimum years between refinances on same property. 0 = no cooldown. Lenders typically require seasoning."
            )
            updated["dscrThresholdForRefi"] = st.slider(
                "DSCR Threshold for Refi",
                min_value=1.0,
                max_value=2.0,
                value=float(form_values["dscrThresholdForRefi"]),
                step=0.05,
                format="%.2f",
                help="Debt Service Coverage Ratio required for refi. NOI / Debt Service. Lenders want 1.2+."
            )

        with col3:
            st.markdown("**Debt & Strategy**")
            updated["refiCashoutStrategy"] = st.selectbox(
                "Refi Cashout Strategy",
                options=["max", "min"],
                index=0 if form_values["refiCashoutStrategy"] == "max" else 1,
                help="'max' extracts maximum equity to LTV limit. 'min' takes only what's needed for next purchase."
            )
            updated["stopRefiAtMaxUnits"] = st.checkbox(
                "Stop Refi at Max Units",
                value=bool(form_values["stopRefiAtMaxUnits"]),
                help="If checked, no more refinances after reaching max units. Focuses on debt payoff instead."
            )
            updated["mortgageRate"] = st.slider(
                "Mortgage Rate",
                min_value=0.03,
                max_value=0.10,
                value=float(form_values["mortgageRate"]),
                step=0.0025,
                format="%.4f",
                help="Interest rate for new purchase mortgages. Current market rates for investment properties."
            )
            updated["refiRate"] = st.slider(
                "Refi Rate",
            min_value=0.03,
            max_value=0.10,
                value=float(form_values["refiRate"]),
                step=0.0025,
                format="%.4f",
                help="Interest rate for refinances. May be lower than purchase rates due to existing equity."
            )

    # Tab 4: Reserves & Banking
    with tabs[3]:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**CapEx Reserves**")
            updated["capexMonthsTarget"] = st.number_input(
            "CapEx Months Target",
            min_value=1,
            max_value=24,
                value=int(form_values["capexMonthsTarget"]),
                step=1,
                help="Target CapEx reserve in months of fixed costs. Funds major repairs and replacements."
            )
            updated["enableCapexCeiling"] = st.checkbox(
                "Enable CapEx Ceiling",
                value=bool(form_values["enableCapexCeiling"]),
                help="If enabled, excess CapEx reserves above ceiling are swept to debt prepayment."
            )
            updated["capexCeilingMonths"] = st.number_input(
                "CapEx Ceiling Months",
                min_value=1,
                max_value=24,
                value=int(form_values["capexCeilingMonths"]),
                step=1,
                help="Max CapEx reserve in months. Excess is deployed to debt reduction."
            )

        with col2:
            st.markdown("**Emergency Reserves**")
            updated["rainyCoverageMonths"] = st.number_input(
                "Rainy Coverage Months",
                min_value=1,
                max_value=12,
                value=int(form_values["rainyCoverageMonths"]),
                step=1,
                help="Emergency reserve target in months of fixed costs. Covers vacancies, repairs, surprises."
            )
            updated["enableRainySweep"] = st.checkbox(
                "Enable Rainy Sweep",
                value=bool(form_values["enableRainySweep"]),
                help="If enabled, emergency reserves above buffer % are swept to debt prepayment."
            )
            updated["rainyBufferPct"] = st.slider(
                "Rainy Buffer %",
                min_value=1.0,
                max_value=2.0,
                value=float(form_values["rainyBufferPct"]),
                step=0.1,
                format="%.1f",
                help="Buffer above target before sweep (1.2 = 120% of target). Prevents over-accumulation."
            )

        with col3:
            st.markdown("**Operating & Banking**")
            updated["operatingCashMonths"] = st.number_input(
                "Operating Cash Months",
                min_value=0,
                max_value=6,
                value=int(form_values["operatingCashMonths"]),
                step=1,
                help="Minimum operating cash to maintain in months of costs. Working capital for day-to-day."
            )
            updated["purchaseReserveMonths"] = st.number_input(
                "Purchase Reserve Months",
                min_value=1,
                max_value=12,
                value=int(form_values["purchaseReserveMonths"]),
                step=1,
                help="Cash cushion required when buying. Months of new property's costs held back for safety."
            )
            updated["seasoningMonths"] = st.number_input(
                "Seasoning Months",
                min_value=0,
                max_value=24,
                value=int(form_values.get("seasoningMonths", 6)),
                step=1,
                help="Minimum months property must be owned before refinancing. Lender requirement."
            )
            updated["refiLTVTrigger"] = st.slider(
                "Refi LTV Trigger",
                min_value=0.50,
                max_value=0.85,
                value=float(form_values.get("refiLTVTrigger", 0.75)),
                step=0.05,
                format="%.2f",
                help="LTV threshold that triggers consideration for cash-out refinance."
            )
            updated["cashoutCostPct"] = st.slider(
                "Cashout Cost %",
                min_value=0.01,
                max_value=0.05,
                value=float(form_values.get("cashoutCostPct", 0.03)),
                step=0.005,
                format="%.3f",
                help="Closing costs for cash-out refinance as % of loan amount."
            )
            updated["cashInterestRate"] = st.slider(
                "Cash Interest Rate",
                min_value=0.0,
                max_value=0.10,
                value=float(form_values.get("cashInterestRate", 0.04)),
                step=0.005,
                format="%.3f",
                help="Interest rate earned on cash reserves (savings accounts, money market)."
            )

    # Tab 5: Distributions (Financial Freedom)
    with tabs[4]:
        st.markdown("### Investor Distributions - 'Financial Freedom' Settings")
        st.caption("Distribute available cash after all reserves and obligations are met.")

        # Initialize distribution dict if not present
        if "distribution" not in updated:
            updated["distribution"] = {}
        if "triggers" not in updated["distribution"]:
            updated["distribution"]["triggers"] = {}
        if "distribution" not in updated["distribution"]:
            updated["distribution"]["distribution"] = {}

        # Main enable/disable toggle
        updated["distribution"]["enabled"] = st.checkbox(
            "Enable Distributions",
            value=bool(form_values.get("distribution", {}).get("enabled", False)),
            help="Turn on/off investor distributions. Distributions only occur AFTER all reserves are fully funded."
        )

        if updated["distribution"]["enabled"]:
            st.markdown("---")

            # Trigger Selection
            st.markdown("### 🎯 When to Start Distributions")
            st.caption("Choose ONE trigger type (others will be ignored)")

            # Detect current trigger type from form values
            triggers = form_values.get("distribution", {}).get("triggers", {})
            if "startYear" in triggers:
                default_index = 0
            elif "maxLTV" in triggers:
                default_index = 1
            elif "minDistributableAmount" in triggers:
                default_index = 2
            else:
                default_index = 0  # Default to Year-Based if nothing set

            trigger_type = st.radio(
                "Trigger Type",
                options=["Year-Based", "LTV-Based", "Distributable Amount"],
                index=default_index,
                help="Select when distributions should begin",
                key="distribution_trigger_type"
            )

            # Preserve all trigger values, but only the selected one will be used by the engine
            # Keep existing trigger dict to preserve values when user switches between types
            if "triggers" not in updated["distribution"]:
                updated["distribution"]["triggers"] = form_values.get("distribution", {}).get("triggers", {}).copy()

            col1, col2 = st.columns(2)

            if trigger_type == "Year-Based":
                with col1:
                    start_year_value = int(form_values.get("distribution", {}).get("triggers", {}).get("startYear", 22))
                    updated["distribution"]["triggers"]["startYear"] = st.number_input(
                        "Start Year",
                        min_value=1,
                        max_value=30,
                        value=start_year_value,
                        step=1,
                        help="Begin distributions in this year of the simulation"
                    )
                    # Clear other trigger types so only one is active
                    updated["distribution"]["triggers"].pop("maxLTV", None)
                    updated["distribution"]["triggers"].pop("minDistributableAmount", None)
                with col2:
                    st.info(f"Distributions will start in Year {updated['distribution']['triggers']['startYear']}")

            elif trigger_type == "LTV-Based":
                with col1:
                    max_ltv_value = float(form_values.get("distribution", {}).get("triggers", {}).get("maxLTV", 30.0))
                    updated["distribution"]["triggers"]["maxLTV"] = st.slider(
                        "Max Portfolio LTV (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=max_ltv_value,
                        step=5.0,
                        format="%.0f",
                        help="Start distributions when LTV falls to or below this level"
                    )
                    # Clear other trigger types so only one is active
                    updated["distribution"]["triggers"].pop("startYear", None)
                    updated["distribution"]["triggers"].pop("minDistributableAmount", None)
                with col2:
                    st.info(f"Distributions start when LTV ≤ {updated['distribution']['triggers']['maxLTV']:.0f}%")

            else:  # Distributable Amount
                with col1:
                    min_dist_value = float(form_values.get("distribution", {}).get("triggers", {}).get("minDistributableAmount", 50000.0))
                    updated["distribution"]["triggers"]["minDistributableAmount"] = st.number_input(
                        "Min Distributable Amount ($)",
                        min_value=1000.0,
                        max_value=500000.0,
                        value=min_dist_value,
                        step=5000.0,
                        format="%.0f",
                        help="Start when this much cash is available after reserves/obligations"
                    )
                    # Clear other trigger types so only one is active
                    updated["distribution"]["triggers"].pop("startYear", None)
                    updated["distribution"]["triggers"].pop("maxLTV", None)
                with col2:
                    st.info(f"Distributions start when ${updated['distribution']['triggers']['minDistributableAmount']:,.0f} is available")

            st.markdown("---")

            # Distribution Amount
            st.markdown("### 💰 Distribution Amount")
            st.caption("What percentage of distributable cash to pay out")

            col1, col2 = st.columns([2, 1])

            with col1:
                dist_pct_value = float(form_values.get("distribution", {}).get("distribution", {}).get("distributionPct", 1.0))
                updated["distribution"]["distribution"]["distributionPct"] = st.slider(
                    "Distribution Percentage",
                    min_value=0.0,
                    max_value=1.0,
                    value=dist_pct_value,
                    step=0.05,
                    format="%.2f",
                    help="What % of distributable cash to distribute each month (0 = none, 1.0 = all)"
                )

                pct_display = int(updated["distribution"]["distribution"]["distributionPct"] * 100)
                st.caption(f"Currently set to: {pct_display}% of distributable cash")

            with col2:
                example_available = 75000
                example_dist = example_available * updated["distribution"]["distribution"]["distributionPct"]
                example_retained = example_available - example_dist
                st.info(f"**Example:**\n\n${example_available:,} available\n\n${example_dist:,.0f} distributed\n\n${example_retained:,.0f} retained")

            st.markdown("---")

            # Quick presets
            st.markdown("### 🎚️ Quick Presets")
            preset_col1, preset_col2, preset_col3 = st.columns(3)

            with preset_col1:
                if st.button("📅 Debt-Free (Year 22)", help="Distribute 100% when debt-free"):
                    updated["distribution"]["triggers"] = {"startYear": 22}
                    updated["distribution"]["distribution"]["distributionPct"] = 1.0
                    st.rerun()

            with preset_col2:
                if st.button("📉 Low Leverage (30% LTV)", help="Distribute 80% at 30% LTV or below"):
                    updated["distribution"]["triggers"] = {"maxLTV": 30.0}
                    updated["distribution"]["distribution"]["distributionPct"] = 0.80
                    st.rerun()

            with preset_col3:
                if st.button("💵 $50k Threshold", help="Distribute 100% when $50k+ available"):
                    updated["distribution"]["triggers"] = {"minDistributableAmount": 50000.0}
                    updated["distribution"]["distribution"]["distributionPct"] = 1.0
                    st.rerun()

        else:
            st.info("ℹ️ Distributions are currently disabled. Enable above to configure.")

    # Tab 6: Market
    with tabs[5]:
        col1, col2 = st.columns(2)

        with col1:
            updated["annualAppreciation"] = st.slider(
            "Annual Appreciation",
            min_value=0.0,
            max_value=0.10,
                value=float(form_values["annualAppreciation"]),
                step=0.005,
                format="%.3f",
                help="Annual property value appreciation rate. Historical average ~3-4% nationally."
            )

        with col2:
            updated["revenueInflationRate"] = st.slider(
                "Revenue Inflation Rate",
                min_value=0.0,
                max_value=0.10,
                value=float(form_values["revenueInflationRate"]),
                step=0.005,
                format="%.3f",
                help="Annual rent/ADR increase rate. STR rates often grow faster than traditional rent."
            )

    # Tab 7: Seasonality / Market Profiles
    with tabs[6]:
        st.markdown("### Seasonality & Market Profiles")
        st.caption("Configure monthly ADR and occupancy variations by market")

        # Initialize market_profiles if not present
        if "market_profiles" not in updated:
            updated["market_profiles"] = form_values.get("market_profiles", {})

        # Get current market profiles
        profiles = updated["market_profiles"]
        profile_names = list(profiles.keys())

        if profile_names:
            selected_profile = st.selectbox(
                "Select Market Profile to Edit",
                options=profile_names,
                format_func=lambda x: profiles[x].get("display_name", x),
                help="Choose which market profile to configure"
            )

            if selected_profile:
                profile = profiles[selected_profile]

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Profile Settings**")
                    profile["display_name"] = st.text_input(
                        "Display Name",
                        value=profile.get("display_name", selected_profile),
                        help="Friendly name for this market"
                    )
                    profile["description"] = st.text_input(
                        "Description",
                        value=profile.get("description", ""),
                        help="Brief description of this market"
                    )
                    profile["seasonality_enabled"] = st.checkbox(
                        "Enable Seasonality",
                        value=profile.get("seasonality_enabled", False),
                        help="Apply monthly multipliers to ADR and occupancy"
                    )

                with col2:
                    st.markdown("**Baseline Values**")
                    if "baseline" not in profile:
                        profile["baseline"] = {}
                    profile["baseline"]["adr"] = st.number_input(
                        "Baseline ADR ($)",
                        min_value=50.0,
                        max_value=1000.0,
                        value=float(profile.get("baseline", {}).get("adr", 200.0)),
                        step=25.0,
                        help="Base average daily rate before seasonal adjustments"
                    )
                    profile["baseline"]["occupancy"] = st.slider(
                        "Baseline Occupancy",
                        min_value=0.40,
                        max_value=1.0,
                        value=float(profile.get("baseline", {}).get("occupancy", 0.70)),
                        step=0.01,
                        format="%.2f",
                        help="Base occupancy rate before seasonal adjustments"
                    )

                if profile.get("seasonality_enabled", False):
                    st.markdown("---")
                    st.markdown("### Monthly Multipliers")
                    st.caption("Values > 1.0 increase rates, < 1.0 decrease rates")

                    if "seasonality" not in profile:
                        profile["seasonality"] = {
                            "adr_multipliers": [1.0] * 12,
                            "occupancy_multipliers": [1.0] * 12
                        }

                    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

                    # ADR multipliers
                    st.markdown("**ADR Multipliers**")
                    adr_cols = st.columns(12)
                    adr_mults = profile["seasonality"].get("adr_multipliers", [1.0] * 12)
                    for i, (month, col) in enumerate(zip(months, adr_cols)):
                        with col:
                            adr_mults[i] = st.number_input(
                                month,
                                min_value=0.5,
                                max_value=2.0,
                                value=float(adr_mults[i]),
                                step=0.05,
                                format="%.2f",
                                key=f"adr_{selected_profile}_{i}"
                            )
                    profile["seasonality"]["adr_multipliers"] = adr_mults

                    # Occupancy multipliers
                    st.markdown("**Occupancy Multipliers**")
                    occ_cols = st.columns(12)
                    occ_mults = profile["seasonality"].get("occupancy_multipliers", [1.0] * 12)
                    for i, (month, col) in enumerate(zip(months, occ_cols)):
                        with col:
                            occ_mults[i] = st.number_input(
                                month,
                                min_value=0.3,
                                max_value=1.5,
                                value=float(occ_mults[i]),
                                step=0.05,
                                format="%.2f",
                                key=f"occ_{selected_profile}_{i}"
                            )
                    profile["seasonality"]["occupancy_multipliers"] = occ_mults

                updated["market_profiles"][selected_profile] = profile
        else:
            st.warning("No market profiles defined. Add profiles in the JSON config.")

    # Tab 8: Tax / Depreciation
    with tabs[7]:
        st.markdown("### Tax & Depreciation Settings")
        st.caption("Configure tax rates and depreciation for accurate after-tax analysis")

        # Initialize tax dict if not present
        if "tax" not in updated:
            updated["tax"] = form_values.get("tax", {})

        tax = updated["tax"]

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Tax Configuration**")
            tax["enabled"] = st.checkbox(
                "Enable Tax Calculations",
                value=tax.get("enabled", True),
                help="Include tax effects in financial projections"
            )

            if tax.get("enabled", True):
                tax["marginal_rate"] = st.slider(
                    "Marginal Tax Rate",
                    min_value=0.10,
                    max_value=0.50,
                    value=float(tax.get("marginal_rate", 0.32)),
                    step=0.01,
                    format="%.2f",
                    help="Your marginal income tax bracket (federal + state combined)"
                )

                tax["depreciation_years"] = st.number_input(
                    "Depreciation Years",
                    min_value=15.0,
                    max_value=39.0,
                    value=float(tax.get("depreciation_years", 27.5)),
                    step=0.5,
                    format="%.1f",
                    help="Depreciation period (27.5 for residential rental, 39 for commercial)"
                )

        with col2:
            if tax.get("enabled", True):
                st.markdown("**Depreciation Basis**")
                tax["land_percentage"] = st.slider(
                    "Land Percentage",
                    min_value=0.05,
                    max_value=0.40,
                    value=float(tax.get("land_percentage", 0.15)),
                    step=0.01,
                    format="%.2f",
                    help="Portion of purchase price allocated to land (not depreciable)"
                )

                # Show calculated example
                example_price = 500000
                depreciable_basis = example_price * (1 - tax["land_percentage"])
                annual_depreciation = depreciable_basis / tax["depreciation_years"]
                tax_savings = annual_depreciation * tax["marginal_rate"]

                st.info(f"""**Example ($500k property):**
- Depreciable Basis: ${depreciable_basis:,.0f}
- Annual Depreciation: ${annual_depreciation:,.0f}
- Annual Tax Savings: ${tax_savings:,.0f}""")

        updated["tax"] = tax

    # Tab 9: Insurance
    with tabs[8]:
        st.markdown("### Insurance Configuration")
        st.caption("Configure property insurance rates and inflation")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Insurance Rates**")
            updated["insuranceRate"] = st.slider(
                "Base Insurance Rate",
                min_value=0.01,
                max_value=0.10,
                value=float(form_values.get("insuranceRate", 0.033)),
                step=0.001,
                format="%.3f",
                help="Annual insurance cost as % of property value"
            )

            # Get insurance inflation from market_profiles or set default
            insurance_inflation = 0.03
            if "market_profiles" in updated:
                default_market = updated.get("policies", {}).get("portfolio", {}).get("default_market", "orange_beach")
                if default_market in updated["market_profiles"]:
                    insurance_inflation = updated["market_profiles"][default_market].get("expenses", {}).get("insurance_inflation_rate", 0.03)

            new_insurance_inflation = st.slider(
                "Insurance Inflation Rate",
                min_value=0.01,
                max_value=0.15,
                value=float(insurance_inflation),
                step=0.01,
                format="%.2f",
                help="Annual increase in insurance premiums (coastal areas often 5-10%)"
            )

            # Update in market profiles
            if "market_profiles" in updated:
                for profile_name, profile in updated["market_profiles"].items():
                    if "expenses" not in profile:
                        profile["expenses"] = {}
                    profile["expenses"]["insurance_inflation_rate"] = new_insurance_inflation

        with col2:
            st.markdown("**Coverage Examples**")
            property_value = 500000
            annual_premium = property_value * updated["insuranceRate"]
            monthly_premium = annual_premium / 12

            st.info(f"""**For a $500k property:**
- Annual Premium: ${annual_premium:,.0f}
- Monthly Cost: ${monthly_premium:,.0f}
- Rate: {updated['insuranceRate']:.1%} of value""")

            st.markdown("**Insurance Inflation Impact**")
            year5_rate = updated["insuranceRate"] * ((1 + new_insurance_inflation) ** 5)
            year10_rate = updated["insuranceRate"] * ((1 + new_insurance_inflation) ** 10)

            st.info(f"""**Premium Growth (at {new_insurance_inflation:.0%}/yr):**
- Year 5: ${property_value * year5_rate:,.0f}/yr
- Year 10: ${property_value * year10_rate:,.0f}/yr""")

    # Tab 10: Events / Stress Testing
    with tabs[9]:
        st.markdown("### Events & Stress Testing")
        st.caption("Configure catastrophic events and stress scenarios")

        # Initialize events dict if not present
        if "events" not in updated:
            updated["events"] = form_values.get("events", {"enabled": False, "scenarios": []})

        events = updated["events"]

        events["enabled"] = st.checkbox(
            "Enable Event Simulation",
            value=events.get("enabled", False),
            help="Activate stress testing with catastrophic events"
        )

        if events.get("enabled", False):
            st.markdown("---")

            # Get existing scenarios
            scenarios = events.get("scenarios", [])

            if scenarios:
                st.markdown("### Configured Events")

                for idx, scenario in enumerate(scenarios):
                    with st.expander(f"📌 {scenario.get('name', f'Event {idx+1}')} ({scenario.get('type', 'unknown')})", expanded=False):
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.markdown("**Event Details**")
                            scenario["name"] = st.text_input(
                                "Event Name",
                                value=scenario.get("name", ""),
                                key=f"event_name_{idx}"
                            )
                            scenario["type"] = st.selectbox(
                                "Event Type",
                                options=["catastrophic", "market_downturn", "regulatory", "maintenance"],
                                index=["catastrophic", "market_downturn", "regulatory", "maintenance"].index(scenario.get("type", "catastrophic")),
                                key=f"event_type_{idx}"
                            )
                            scenario["description"] = st.text_area(
                                "Description",
                                value=scenario.get("description", ""),
                                key=f"event_desc_{idx}"
                            )

                        with col2:
                            st.markdown("**Timing & Scope**")
                            scenario["year"] = st.number_input(
                                "Year",
                                min_value=1,
                                max_value=30,
                                value=int(scenario.get("year", 3)),
                                key=f"event_year_{idx}"
                            )
                            scenario["month"] = st.number_input(
                                "Month",
                                min_value=1,
                                max_value=12,
                                value=int(scenario.get("month", 9)),
                                key=f"event_month_{idx}"
                            )
                            scenario["scope"] = st.selectbox(
                                "Scope",
                                options=["portfolio", "single_unit", "market"],
                                index=["portfolio", "single_unit", "market"].index(scenario.get("scope", "portfolio")),
                                key=f"event_scope_{idx}"
                            )

                        with col3:
                            st.markdown("**Impacts**")
                            if "impacts" not in scenario:
                                scenario["impacts"] = {}
                            impacts = scenario["impacts"]

                            impacts["vacancy_months"] = st.number_input(
                                "Vacancy Months",
                                min_value=0,
                                max_value=12,
                                value=int(impacts.get("vacancy_months", 2)),
                                key=f"event_vacancy_{idx}"
                            )
                            impacts["repair_cost"] = st.number_input(
                                "Repair Cost ($)",
                                min_value=0.0,
                                max_value=500000.0,
                                value=float(impacts.get("repair_cost", 50000)),
                                step=5000.0,
                                key=f"event_repair_{idx}"
                            )
                            impacts["adr_reduction_pct"] = st.slider(
                                "ADR Reduction %",
                                min_value=0.0,
                                max_value=0.50,
                                value=float(impacts.get("adr_reduction_pct", 0.10)),
                                step=0.05,
                                key=f"event_adr_{idx}"
                            )
                            impacts["recovery_months"] = st.number_input(
                                "Recovery Months",
                                min_value=1,
                                max_value=24,
                                value=int(impacts.get("recovery_months", 6)),
                                key=f"event_recovery_{idx}"
                            )

                        st.markdown("**Insurance Claim**")
                        if "insurance_claim" not in scenario:
                            scenario["insurance_claim"] = {}
                        claim = scenario["insurance_claim"]

                        claim_col1, claim_col2, claim_col3 = st.columns(3)
                        with claim_col1:
                            claim["coverage_pct"] = st.slider(
                                "Coverage %",
                                min_value=0.0,
                                max_value=1.0,
                                value=float(claim.get("coverage_pct", 0.90)),
                                step=0.05,
                                key=f"claim_coverage_{idx}"
                            )
                        with claim_col2:
                            claim["deductible_pct"] = st.slider(
                                "Deductible %",
                                min_value=0.0,
                                max_value=0.10,
                                value=float(claim.get("deductible_pct", 0.02)),
                                step=0.005,
                                key=f"claim_deductible_{idx}"
                            )
                        with claim_col3:
                            claim["payout_delay_months"] = st.number_input(
                                "Payout Delay (months)",
                                min_value=0,
                                max_value=12,
                                value=int(claim.get("payout_delay_months", 4)),
                                key=f"claim_delay_{idx}"
                            )

                        # Delete button
                        if st.button(f"🗑️ Delete Event", key=f"delete_event_{idx}"):
                            scenarios.pop(idx)
                            st.rerun()

                        scenarios[idx] = scenario

            # Add new event button
            st.markdown("---")
            if st.button("➕ Add New Event"):
                new_event = {
                    "name": "New Event",
                    "type": "catastrophic",
                    "year": 5,
                    "month": 6,
                    "scope": "portfolio",
                    "impacts": {
                        "vacancy_months": 1,
                        "repair_cost": 25000,
                        "adr_reduction_pct": 0.05,
                        "recovery_months": 3
                    },
                    "insurance_claim": {
                        "coverage_pct": 0.80,
                        "deductible_pct": 0.02,
                        "payout_delay_months": 2
                    },
                    "description": "Describe the event"
                }
                scenarios.append(new_event)
                st.rerun()

            events["scenarios"] = scenarios
        else:
            st.info("ℹ️ Event simulation is disabled. Enable above to configure stress scenarios.")

        updated["events"] = events

    # Tab 11: CapEx Schedule
    with tabs[10]:
        st.markdown("### CapEx Schedule")
        st.caption("Configure per-unit system tracking for major replacements")

        # Initialize capex_schedule if not present
        if "capex_schedule" not in updated:
            updated["capex_schedule"] = form_values.get("capex_schedule", {"enabled": False, "systems": {}})

        capex = updated["capex_schedule"]

        capex["enabled"] = st.checkbox(
            "Enable CapEx Tracking",
            value=capex.get("enabled", False),
            help="Track system ages and schedule replacements per unit"
        )

        if capex.get("enabled", False):
            st.markdown("---")
            st.markdown("### System Configuration")

            if "systems" not in capex:
                capex["systems"] = {}

            systems = capex["systems"]

            # Default systems if none exist
            default_systems = {
                "hvac": {"lifespan_years": 15, "replacement_cost": 12000, "description": "HVAC System"},
                "roof": {"lifespan_years": 25, "replacement_cost": 25000, "description": "Roof"},
                "appliances": {"lifespan_years": 10, "replacement_cost": 8000, "description": "Kitchen Appliances"},
                "flooring": {"lifespan_years": 7, "replacement_cost": 10000, "description": "Flooring"},
                "furniture": {"lifespan_years": 5, "replacement_cost": 15000, "description": "Furniture Package"},
                "water_heater": {"lifespan_years": 12, "replacement_cost": 1500, "description": "Water Heater"}
            }

            if not systems:
                systems = default_systems

            # Display each system
            for sys_key, sys_data in systems.items():
                with st.expander(f"🔧 {sys_data.get('description', sys_key)}", expanded=False):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        sys_data["description"] = st.text_input(
                            "System Name",
                            value=sys_data.get("description", sys_key),
                            key=f"capex_desc_{sys_key}"
                        )

                    with col2:
                        sys_data["lifespan_years"] = st.number_input(
                            "Lifespan (years)",
                            min_value=1,
                            max_value=50,
                            value=int(sys_data.get("lifespan_years", 10)),
                            key=f"capex_lifespan_{sys_key}"
                        )

                    with col3:
                        sys_data["replacement_cost"] = st.number_input(
                            "Replacement Cost ($)",
                            min_value=500.0,
                            max_value=100000.0,
                            value=float(sys_data.get("replacement_cost", 5000)),
                            step=500.0,
                            key=f"capex_cost_{sys_key}"
                        )

                    systems[sys_key] = sys_data

            capex["systems"] = systems

            # Summary
            st.markdown("---")
            st.markdown("### 30-Year CapEx Summary")
            total_per_unit = sum(
                sys_data.get("replacement_cost", 0) * (30 / max(sys_data.get("lifespan_years", 10), 1))
                for sys_data in systems.values()
            )
            st.info(f"""**Per Unit (30 years):**
- Total CapEx: ${total_per_unit:,.0f}
- Annual Average: ${total_per_unit / 30:,.0f}
- Monthly Average: ${total_per_unit / 360:,.0f}""")
        else:
            st.info("ℹ️ CapEx tracking is disabled. Enable above to configure per-unit system tracking.")

        updated["capex_schedule"] = capex

    # Tab 12: Financing Dashboard
    with tabs[11]:
        st.markdown("### Financing Dashboard Settings")
        st.caption("Configure debt analytics and tracking options")

        # Initialize financing_dashboard if not present
        if "financing_dashboard" not in updated:
            updated["financing_dashboard"] = form_values.get("financing_dashboard", {"enabled": True})

        financing = updated["financing_dashboard"]

        financing["enabled"] = st.checkbox(
            "Enable Financing Dashboard",
            value=financing.get("enabled", True),
            help="Enable comprehensive debt and financing analytics"
        )

        if financing.get("enabled", True):
            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Tracking Options**")
                financing["track_interest_paid"] = st.checkbox(
                    "Track Interest Paid",
                    value=financing.get("track_interest_paid", True),
                    help="Track cumulative interest paid per unit and portfolio-wide"
                )
                financing["project_payoff_timeline"] = st.checkbox(
                    "Project Payoff Timeline",
                    value=financing.get("project_payoff_timeline", True),
                    help="Calculate projected loan payoff dates"
                )
                financing["analyze_refi_opportunities"] = st.checkbox(
                    "Analyze Refi Opportunities",
                    value=financing.get("analyze_refi_opportunities", True),
                    help="Identify potential refinancing opportunities"
                )

            with col2:
                st.markdown("**Debt Strategy Info**")
                st.info("""**The Financing Dashboard tracks:**
- Amortization schedules per unit
- Interest vs principal breakdown
- Projected payoff dates
- Refinance opportunity analysis
- Portfolio-wide debt metrics""")

        updated["financing_dashboard"] = financing

    # Tab 13: Exit Strategy
    with tabs[12]:
        st.markdown("### Exit Strategy Settings")
        st.caption("Configure sale, liquidation, and 1031 exchange parameters")

        # Initialize exit_strategy if not present
        if "exit_strategy" not in updated:
            updated["exit_strategy"] = form_values.get("exit_strategy", {"enabled": True})

        exit_strat = updated["exit_strategy"]

        exit_strat["enabled"] = st.checkbox(
            "Enable Exit Strategy Modeling",
            value=exit_strat.get("enabled", True),
            help="Enable sale proceeds and exit analysis calculations"
        )

        if exit_strat.get("enabled", True):
            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Selling Costs**")
                exit_strat["selling_cost_pct"] = st.slider(
                    "Selling Cost %",
                    min_value=0.03,
                    max_value=0.10,
                    value=float(exit_strat.get("selling_cost_pct", 0.06)),
                    step=0.01,
                    format="%.2f",
                    help="Agent commission and selling costs (typically 5-6%)"
                )
                exit_strat["closing_cost_pct"] = st.slider(
                    "Closing Cost %",
                    min_value=0.01,
                    max_value=0.05,
                    value=float(exit_strat.get("closing_cost_pct", 0.02)),
                    step=0.005,
                    format="%.3f",
                    help="Title, escrow, and other closing costs"
                )

                st.markdown("**Capital Gains**")
                exit_strat["capital_gains_rate"] = st.slider(
                    "Capital Gains Rate",
                    min_value=0.0,
                    max_value=0.30,
                    value=float(exit_strat.get("capital_gains_rate", 0.15)),
                    step=0.01,
                    format="%.2f",
                    help="Federal long-term capital gains rate (0%, 15%, or 20%)"
                )
                exit_strat["state_tax_rate"] = st.slider(
                    "State Tax Rate",
                    min_value=0.0,
                    max_value=0.15,
                    value=float(exit_strat.get("state_tax_rate", 0.05)),
                    step=0.01,
                    format="%.2f",
                    help="State capital gains tax rate"
                )

            with col2:
                st.markdown("**Depreciation Recapture**")
                exit_strat["depreciation_recapture_rate"] = st.slider(
                    "Depreciation Recapture Rate",
                    min_value=0.20,
                    max_value=0.30,
                    value=float(exit_strat.get("depreciation_recapture_rate", 0.25)),
                    step=0.01,
                    format="%.2f",
                    help="Tax rate on recaptured depreciation (typically 25%)"
                )

                st.markdown("**Holding Period**")
                exit_strat["min_hold_months_ltcg"] = st.number_input(
                    "Min Hold for LTCG (months)",
                    min_value=6,
                    max_value=24,
                    value=int(exit_strat.get("min_hold_months_ltcg", 12)),
                    help="Minimum hold period for long-term capital gains treatment"
                )

                # Example calculation
                st.markdown("---")
                st.markdown("**Example Sale ($600k property)**")
                example_sale = 600000
                example_basis = 500000
                example_depreciation = 50000
                selling_costs = example_sale * exit_strat["selling_cost_pct"]
                closing_costs = example_sale * exit_strat["closing_cost_pct"]
                net_sale = example_sale - selling_costs - closing_costs
                capital_gain = net_sale - example_basis
                depreciation_recapture = example_depreciation * exit_strat["depreciation_recapture_rate"]
                cap_gains_tax = capital_gain * (exit_strat["capital_gains_rate"] + exit_strat["state_tax_rate"])
                total_tax = depreciation_recapture + cap_gains_tax
                net_proceeds = net_sale - total_tax

                st.info(f"""- Net Sale: ${net_sale:,.0f}
- Capital Gain: ${capital_gain:,.0f}
- Total Tax: ${total_tax:,.0f}
- Net Proceeds: ${net_proceeds:,.0f}""")

        updated["exit_strategy"] = exit_strat

    # Tab 14: Validation Thresholds
    with tabs[13]:
        st.markdown("### Model Validation Thresholds")
        st.caption("Configure thresholds for validation checks. Lower values = stricter validation.")

        # Initialize validation dict if not present
        if "validation" not in updated:
            updated["validation"] = {}

        val_tabs = st.tabs(["LTV & DSCR", "Acquisition & Refi", "Reserves", "Cash Flow", "Portfolio & Performance", "Feeder & Timing"])

        # Sub-tab 1: LTV & DSCR
        with val_tabs[0]:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**LTV Thresholds**")
                if "ltv" not in updated["validation"]:
                    updated["validation"]["ltv"] = {}

                updated["validation"]["ltv"]["maxSafeThreshold"] = st.slider(
                    "Max Safe LTV Threshold",
                    min_value=0.75,
                    max_value=0.95,
                    value=float(form_values.get("validation", {}).get("ltv", {}).get("maxSafeThreshold", 0.85)),
                    step=0.05,
                    format="%.2f",
                    help="Flag if LTV exceeds this % (investment property lenders cap at 75-85%)"
                )

                updated["validation"]["ltv"]["maxMonthlyDropWithoutEvent"] = st.slider(
                    "Max LTV Drop Without Event",
                    min_value=0.05,
                    max_value=0.20,
                    value=float(form_values.get("validation", {}).get("ltv", {}).get("maxMonthlyDropWithoutEvent", 0.10)),
                    step=0.01,
                    format="%.2f",
                    help="Flag if LTV drops >this % in month without refi/purchase (likely calculation bug)"
                )

            with col2:
                st.markdown("**DSCR Thresholds**")
                if "dscr" not in updated["validation"]:
                    updated["validation"]["dscr"] = {}

                updated["validation"]["dscr"]["criticalThreshold"] = st.slider(
                    "Critical DSCR Threshold",
                    min_value=0.80,
                    max_value=1.10,
                    value=float(form_values.get("validation", {}).get("dscr", {}).get("criticalThreshold", 1.0)),
                    step=0.05,
                    format="%.2f",
                    help="DSCR below this is unsustainable (1.0 = break-even)"
                )

                updated["validation"]["dscr"]["lenderMinimum"] = st.slider(
                    "Lender Minimum DSCR",
                    min_value=1.10,
                    max_value=1.50,
                    value=float(form_values.get("validation", {}).get("dscr", {}).get("lenderMinimum", 1.25)),
                    step=0.05,
                    format="%.2f",
                    help="Minimum DSCR for refinancing (lenders typically require 1.2-1.25)"
                )

                updated["validation"]["dscr"]["maxMonthsBelowLender"] = st.number_input(
                    "Max Months Below Lender Min",
                    min_value=0,
                    max_value=36,
                    value=int(form_values.get("validation", {}).get("dscr", {}).get("maxMonthsBelowLender", 12)),
                    step=6,
                    help="Tolerate DSCR below lender min for this many months"
                )

        # Sub-tab 2: Acquisition & Refinance
        with val_tabs[1]:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Acquisition Pacing**")
                if "acquisition" not in updated["validation"]:
                    updated["validation"]["acquisition"] = {}

                updated["validation"]["acquisition"]["minLiquidityToFlag"] = st.number_input(
                    "Min Liquidity to Flag Stuck ($)",
                    min_value=10000.0,
                    max_value=200000.0,
                    value=float(form_values.get("validation", {}).get("acquisition", {}).get("minLiquidityToFlag", 50000.0)),
                    step=10000.0,
                    format="%.0f",
                    help="Flag if stuck at same property count with this much available liquidity"
                )

                updated["validation"]["acquisition"]["maxMonthsStuck"] = st.number_input(
                    "Max Months Stuck",
                    min_value=12,
                    max_value=120,
                    value=int(form_values.get("validation", {}).get("acquisition", {}).get("maxMonthsStuck", 60)),
                    step=12,
                    help="Flag if stuck at same property count for this many months despite liquidity"
                )

                updated["validation"]["acquisition"]["yearToStopCheckingStuck"] = st.number_input(
                    "Year to Stop Checking Stuck",
                    min_value=15,
                    max_value=30,
                    value=int(form_values.get("validation", {}).get("acquisition", {}).get("yearToStopCheckingStuck", 25)),
                    step=5,
                    help="Don't flag stuck properties after this year (acceptable to stop buying)"
                )

                updated["validation"]["acquisition"]["maxConsecutiveMonths"] = st.number_input(
                    "Max Consecutive Acquisition Months",
                    min_value=0,
                    max_value=3,
                    value=int(form_values.get("validation", {}).get("acquisition", {}).get("maxConsecutiveMonths", 0)),
                    step=1,
                    help="Allow this many back-to-back month acquisitions (0=none, unrealistic for due diligence)"
                )

            with col2:
                st.markdown("**Refinance Economics**")
                if "refinance" not in updated["validation"]:
                    updated["validation"]["refinance"] = {}

                updated["validation"]["refinance"]["minProceedsToJustifyCosts"] = st.number_input(
                    "Min Refi Proceeds to Justify ($)",
                    min_value=5000.0,
                    max_value=50000.0,
                    value=float(form_values.get("validation", {}).get("refinance", {}).get("minProceedsToJustifyCosts", 20000.0)),
                    step=5000.0,
                    format="%.0f",
                    help="Flag refis extracting less than this (refi costs may not be justified)"
                )

                updated["validation"]["refinance"]["maxRefisPerPropertyLifetime"] = st.number_input(
                    "Max Refis Per Property",
                    min_value=1,
                    max_value=10,
                    value=int(form_values.get("validation", {}).get("refinance", {}).get("maxRefisPerPropertyLifetime", 3)),
                    step=1,
                    help="Theoretical max times a property can be refinanced over simulation"
                )

        # Sub-tab 3: Reserves
        with val_tabs[2]:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Reserve Sufficiency**")
                if "reserves" not in updated["validation"]:
                    updated["validation"]["reserves"] = {}

                updated["validation"]["reserves"]["minCushionPctAtPurchase"] = st.slider(
                    "Min Reserve Cushion at Purchase",
                    min_value=0.50,
                    max_value=1.0,
                    value=float(form_values.get("validation", {}).get("reserves", {}).get("minCushionPctAtPurchase", 0.80)),
                    step=0.05,
                    format="%.2f",
                    help="Require reserves to be at least this % of required after purchase"
                )

                updated["validation"]["reserves"]["maxReserveHoarding"] = st.number_input(
                    "Max Reserve Hoarding ($)",
                    min_value=100000.0,
                    max_value=1000000.0,
                    value=float(form_values.get("validation", {}).get("reserves", {}).get("maxReserveHoarding", 500000.0)),
                    step=50000.0,
                    format="%.0f",
                    help="Flag if reserves exceed this (hoarding vs deploying capital)"
                )

            with col2:
                st.markdown("**Reserve Volatility**")
                updated["validation"]["reserves"]["maxMonthlyDropPct"] = st.slider(
                    "Max Monthly Reserve Drop %",
                    min_value=0.25,
                    max_value=0.75,
                    value=float(form_values.get("validation", {}).get("reserves", {}).get("maxMonthlyDropPct", 0.50)),
                    step=0.05,
                    format="%.2f",
                    help="Flag if reserves drop >this % in single month (outside purchases)"
                )

                updated["validation"]["reserves"]["sweepToleranceMonths"] = st.number_input(
                    "Sweep Tolerance (Months)",
                    min_value=3,
                    max_value=36,
                    value=int(form_values.get("validation", {}).get("reserves", {}).get("sweepToleranceMonths", 12)),
                    step=3,
                    help="Max months reserves can exceed buffer without sweep triggering"
                )

        # Sub-tab 4: Cash Flow
        with val_tabs[3]:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Cash Flow Stability**")
                if "cashFlow" not in updated["validation"]:
                    updated["validation"]["cashFlow"] = {}

                updated["validation"]["cashFlow"]["maxMonthsNegative"] = st.number_input(
                    "Max Months Negative Cash Flow",
                    min_value=0,
                    max_value=24,
                    value=int(form_values.get("validation", {}).get("cashFlow", {}).get("maxMonthsNegative", 6)),
                    step=3,
                    help="Max months of negative cash flow after debt service (burn rate)"
                )

                updated["validation"]["cashFlow"]["noiVolatilityThreshold"] = st.number_input(
                    "NOI Volatility Threshold ($)",
                    min_value=500.0,
                    max_value=10000.0,
                    value=float(form_values.get("validation", {}).get("cashFlow", {}).get("noiVolatilityThreshold", 3000.0)),
                    step=500.0,
                    format="%.0f",
                    help="Flag if NOI swings >this amount month-over-month (outside acquisitions)"
                )

            with col2:
                st.markdown("**Return Expectations**")
                updated["validation"]["cashFlow"]["minCashOnCashReturn"] = st.slider(
                    "Min Cash-on-Cash Return",
                    min_value=0.0,
                    max_value=0.15,
                    value=float(form_values.get("validation", {}).get("cashFlow", {}).get("minCashOnCashReturn", 0.05)),
                    step=0.01,
                    format="%.2f",
                    help="Flag if annualized CoC return below this (strategy underperforming)"
                )

                updated["validation"]["cashFlow"]["maxCashOnCashReturn"] = st.slider(
                    "Max Cash-on-Cash Return",
                    min_value=0.15,
                    max_value=0.50,
                    value=float(form_values.get("validation", {}).get("cashFlow", {}).get("maxCashOnCashReturn", 0.30)),
                    step=0.05,
                    format="%.2f",
                    help="Flag if annualized CoC return above this (too good to be true)"
                )

        # Sub-tab 5: Portfolio & Performance
        with val_tabs[4]:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Portfolio Targets**")
                if "portfolio" not in updated["validation"]:
                    updated["validation"]["portfolio"] = {}

                updated["validation"]["portfolio"]["minPropertiesByYear5"] = st.number_input(
                    "Min Properties by Year 5",
                    min_value=1,
                    max_value=10,
                    value=int(form_values.get("validation", {}).get("portfolio", {}).get("minPropertiesByYear5", 3)),
                    step=1,
                    help="Expect at least this many properties by Year 5 (diversification)"
                )

                updated["validation"]["portfolio"]["equityGrowthTolerancePct"] = st.slider(
                    "Equity Growth Tolerance %",
                    min_value=0.50,
                    max_value=1.0,
                    value=float(form_values.get("validation", {}).get("portfolio", {}).get("equityGrowthTolerancePct", 0.70)),
                    step=0.05,
                    format="%.2f",
                    help="Equity must grow at least this % of appreciation-implied minimum"
                )

                updated["validation"]["portfolio"]["portfolioGrowthTolerancePct"] = st.slider(
                    "Portfolio Growth Tolerance %",
                    min_value=0.50,
                    max_value=1.0,
                    value=float(form_values.get("validation", {}).get("portfolio", {}).get("portfolioGrowthTolerancePct", 0.60)),
                    step=0.05,
                    format="%.2f",
                    help="Portfolio value must grow at least this % of appreciation-implied minimum"
                )

            with col2:
                st.markdown("**Debt Payoff Timeline**")
                updated["validation"]["portfolio"]["minDebtFreeYear"] = st.number_input(
                    "Min Debt-Free Year",
                    min_value=10,
                    max_value=25,
                    value=int(form_values.get("validation", {}).get("portfolio", {}).get("minDebtFreeYear", 15)),
                    step=5,
                    help="Flag if debt-free before this year (unrealistic prepayment)"
                )

                updated["validation"]["portfolio"]["maxDebtFreeYear"] = st.number_input(
                    "Max Debt-Free Year",
                    min_value=20,
                    max_value=30,
                    value=int(form_values.get("validation", {}).get("portfolio", {}).get("maxDebtFreeYear", 30)),
                    step=5,
                    help="Flag if still in debt after this year"
                )

                updated["validation"]["portfolio"]["minUnitsForDebtFreeCheck"] = st.number_input(
                    "Min Units for Debt-Free Check",
                    min_value=1,
                    max_value=10,
                    value=int(form_values.get("validation", {}).get("portfolio", {}).get("minUnitsForDebtFreeCheck", 5)),
                    step=1,
                    help="Only check debt-free timing if portfolio has at least this many units"
                )

        # Sub-tab 6: Feeder & Timing
        with val_tabs[5]:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Feeder Strategy**")
                if "feeder" not in updated["validation"]:
                    updated["validation"]["feeder"] = {}

                updated["validation"]["feeder"]["minAnnualLTVDecrease"] = st.slider(
                    "Min Annual Feeder LTV Decrease",
                    min_value=0.01,
                    max_value=0.15,
                    value=float(form_values.get("validation", {}).get("feeder", {}).get("minAnnualLTVDecrease", 0.05)),
                    step=0.01,
                    format="%.2f",
                    help="Feeder LTV should decrease at least this much per year (prepayment effectiveness)"
                )

                updated["validation"]["feeder"]["maxMonthsSameFeeder"] = st.number_input(
                    "Max Months Same Feeder",
                    min_value=12,
                    max_value=60,
                    value=int(form_values.get("validation", {}).get("feeder", {}).get("maxMonthsSameFeeder", 36)),
                    step=6,
                    help="Flag if same property is feeder for >this many months (should rotate or refi)"
                )

            with col2:
                st.markdown("**Acquisition Timing**")
                if "timing" not in updated["validation"]:
                    updated["validation"]["timing"] = {}

                updated["validation"]["timing"]["maxMonthsAtSamePropertyCount"] = st.number_input(
                    "Max Months at Same Property Count",
                    min_value=12,
                    max_value=60,
                    value=int(form_values.get("validation", {}).get("timing", {}).get("maxMonthsAtSamePropertyCount", 24)),
                    step=6,
                    help="Flag if stuck at same property count for this long despite equity growth"
                )

                updated["validation"]["timing"]["minEquityGrowthWhileStuck"] = st.slider(
                    "Min Equity Growth While Stuck",
                    min_value=0.10,
                    max_value=0.50,
                    value=float(form_values.get("validation", {}).get("timing", {}).get("minEquityGrowthWhileStuck", 0.20)),
                    step=0.05,
                    format="%.2f",
                    help="Flag if equity grows >this % while stuck at same property count"
                )

    return updated
