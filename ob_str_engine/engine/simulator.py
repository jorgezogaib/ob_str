"""
Real Estate Portfolio Simulator - Feeder Strategy Implementation

This simulator implements a two-phase investment strategy:

PHASE 1: Acquisition (< max_units)
- Three separate cash accounts: Operating, Rainy-Day Reserve, Savings
- All accounts earn configurable interest (default 4% annual)
- Surplus cash flow is split: 70% to feeder prepayment, 30% to savings
- Feeder property is selected based on lowest LTV past cooldown
- Purchases triggered when: feeder refi potential + savings >= purchase cost

PHASE 2: Debt Payoff (>= max_units)
- No more refinancing
- All surplus goes to prepaying feeder property
- Once feeder is paid off, select next lowest LTV property
- Continue until all properties are debt-free
"""

import pandas as pd
from pathlib import Path
from typing import List, Optional
from .config import load_engine_config
from .types import Unit, SimulationResult
from .revenue import calculate_gross_revenue, get_adr_for_year, calculate_gross_revenue_seasonal
from .expenses import calculate_expenses
from .acquisition import calculate_parity_price, get_default_market_for_acquisition
from .seasonality import (
    is_seasonality_enabled,
    get_seasonal_factors,
    get_default_market_name,
    get_market_baseline,
)
from .tax import (
    is_tax_enabled,
    get_tax_config,
    calculate_depreciation_basis,
    process_monthly_depreciation,
)
from .insurance import (
    is_insurance_enhanced,
    calculate_unit_insurance,
    calculate_monthly_insurance,
)
from .events import (
    is_events_enabled,
    get_scheduled_events,
    check_event_triggers,
    process_event,
    get_active_effects,
    get_pending_payouts,
)
from .capex import (
    is_capex_schedule_enabled,
    get_capex_config,
    initialize_unit_systems,
    age_systems,
    process_replacements,
    calculate_annual_capex_budget,
)
from .financing import (
    is_financing_dashboard_enabled,
    get_monthly_interest_principal_split,
)
from .debt import pmt, amortize_one_month
from .reserves import update_rainy_day_reserve
from .liquidity import liquidity_check
from .distributions import process_distribution
from .feeder import (
    attempt_refi_cashout,
    prepay_surplus,
    select_feeder,
    calculate_potential_refi_cashout,
    is_feeder_refi_eligible,
    get_feeder_ltv,
    prepay_feeder,
)


def cents(x: float) -> float:
    """Round to cents — exactly like original script."""
    return round(float(x), 2)


def estimate_fixed_costs_for_new_property(
    price: float,
    hoa_annual: float,
    ins_rate: float,
    tax_rate: float,
    rate_purchase: float,
    amort_years: int,
    down_pct: float,
) -> float:
    """
    Estimate monthly fixed costs for a NEW property (for reserve calculation).
    """
    loan = price * (1 - down_pct)
    monthly_payment = pmt(rate_purchase, amort_years, loan)
    hoa_monthly = hoa_annual / 12
    insurance = price * ins_rate / 12
    tax = price * tax_rate / 12
    return hoa_monthly + insurance + tax + monthly_payment


def simulate(engine_path: Path, years: int = 30) -> SimulationResult:
    engine = load_engine_config(engine_path)
    const = engine["constants"]
    fin = const["financial"]
    ops = const["operations"]
    acq = const["acquisition"]
    debt_cfg = const["debt"]
    calendar = engine["calendar"]["monthlyDays"]
    banking = engine["banking"]
    policies = engine.get("policies", {})
    portfolio = policies.get("portfolio", {})
    capital_alloc = policies.get("capitalAllocation", {})

    # === Constants ===
    starting_cash = float(fin["startingCash"])
    annual_savings = float(fin["annualSavings"])
    amort_years = int(fin["amortizationYears"])

    base_adr = float(ops["adrBaseline2BR"])
    occ = float(ops["occupancyBaseline"])
    mgmt_pct = float(ops["mgmtPct"])
    capex_pct = float(ops["capexPct"])
    hoa_annual_base = float(ops["hoaAnnual"])
    hoa_infl_rate = float(ops["hoaInflationRate"])
    ins_rate = float(ops["insuranceRate"])
    tax_rate = float(ops["propertyTaxRate"])

    dp_first = float(acq["downPaymentFirst"])
    dp_sub = float(acq["downPaymentSubsequent"])
    closing_pct = float(acq["closingCostPct"])
    max_ltv = float(acq["maxPostRefiLTV"])
    cooldown_years = int(acq["refiCooldownYears"])
    cooldown_months = cooldown_years * 12

    rate_purchase = float(debt_cfg["mortgageRate"])
    rate_refi = float(debt_cfg["refiRate"])

    appreciation = float(engine["market"]["annualAppreciation"])
    revenue_infl_rate = float(engine["market"].get("revenueInflationRate", 0.04))

    rainy_months = float(banking["rainyCoverageMonths"])
    operating_cash_months = float(banking.get("operatingCashMonths", 1))
    ltv_trigger = float(banking["refiLTVTrigger"])
    cashout_cost = float(banking["cashoutCostPct"])
    cash_interest_rate = float(banking.get("cashInterestRate", 0.04))
    purchase_reserve_months = int(banking.get("purchaseReserveMonths", 6))

    max_units = int(portfolio.get("maxUnits", 7))
    stop_refi_at_max = bool(portfolio.get("stopRefiAtMaxUnits", True))

    feeder_prepay_pct = float(capital_alloc.get("feederPrepaymentPct", 0.70))
    savings_pct = float(capital_alloc.get("savingsAccumulationPct", 0.30))

    # Reserve sweep configuration
    reserves_cfg = const.get("reserves", {})
    enable_capex_ceiling = bool(reserves_cfg.get("enableCapexCeiling", False))
    capex_ceiling_months = int(reserves_cfg.get("capexCeilingMonths", 6))
    enable_rainy_sweep = bool(reserves_cfg.get("enableRainySweep", False))
    rainy_buffer_pct = float(reserves_cfg.get("rainyBufferPct", 1.2))

    # Distribution configuration
    distribution_cfg = engine.get("distribution", {})

    # Phase 1.1: Seasonality configuration
    use_seasonality = is_seasonality_enabled(engine)
    default_market = get_default_market_name(engine)

    # Phase 1.4: Tax/Depreciation configuration
    use_tax = is_tax_enabled(engine)
    tax_cfg = get_tax_config(engine)
    land_percentage = tax_cfg["land_percentage"]
    marginal_tax_rate = tax_cfg["marginal_rate"]

    # Phase 1.2: Insurance configuration
    use_enhanced_insurance = is_insurance_enhanced(engine)

    # Phase 1.3: Events configuration
    use_events = is_events_enabled(engine)
    scheduled_events = get_scheduled_events(engine) if use_events else []
    event_results = []  # Track processed events for insurance payouts

    # Phase 1.5: CapEx Schedule configuration
    use_capex_schedule = is_capex_schedule_enabled(engine)
    capex_replacements_log = []  # Track all replacements for reporting

    # Phase 1.6: Financing Dashboard configuration
    use_financing_dashboard = is_financing_dashboard_enabled(engine)

    # === State Variables ===
    # Three separate cash accounts
    cash = starting_cash  # Operating cash
    rainy_reserve = 0.0   # Rainy-day reserve (6 months fixed costs)
    savings_account = 0.0  # Savings for down payments
    capex_reserve = 0.0

    units_owned = 0
    units: List[Unit] = []
    pending_cashout = 0.0
    month_global = 0
    next_unit_id = 0

    # Feeder tracking
    feeder_index: Optional[int] = None

    rows = []
    unit_rows = []  # Track individual unit data

    for year in range(1, years + 1):
        adr_this_year = get_adr_for_year(base_adr, revenue_infl_rate, year)
        hoa_annual_this_year = hoa_annual_base * (1 + hoa_infl_rate) ** (year - 1)
        price_parity = calculate_parity_price(year, engine)

        for m, days in enumerate(calendar, 1):
            month_global += 1

            # === MONTHLY INTEREST ON ALL CASH ACCOUNTS ===
            monthly_interest_rate = cash_interest_rate / 12
            cash_interest_earned = cash * monthly_interest_rate
            rainy_interest_earned = rainy_reserve * monthly_interest_rate
            savings_interest_earned = savings_account * monthly_interest_rate

            cash += cash_interest_earned
            rainy_reserve += rainy_interest_earned
            savings_account += savings_interest_earned

            # === INCOME ===
            cash += pending_cashout
            pending_cashout = 0.0
            cash += annual_savings / 12

            # Collect rental revenue into operating cash
            # Phase 1.1: Use seasonal revenue if enabled, otherwise flat (v2.3 behavior)
            if use_seasonality and units:
                gross, revenue_details = calculate_gross_revenue_seasonal(
                    units, engine, year, month_global, days
                )
                seasonal_enabled = revenue_details.get("seasonality_enabled", False)
                seasonal_delta = revenue_details.get("seasonal_delta", 0.0)
            else:
                gross = calculate_gross_revenue(units_owned, adr_this_year, occ, days)
                revenue_details = None
                seasonal_enabled = False
                seasonal_delta = 0.0
            cash += gross

            total_value = sum(u.value for u in units)

            exp = calculate_expenses(
                gross, units_owned, total_value, hoa_annual_this_year,
                mgmt_pct, capex_pct, ins_rate, tax_rate
            )

            # Phase 1.2: Enhanced insurance calculation
            enhanced_insurance_total = 0.0
            if use_enhanced_insurance and units:
                for u in units:
                    years_owned = max(1, (month_global - u.purchase_month) // 12 + 1)
                    has_claim = u.insurance_claim_month > 0
                    months_since_claim = month_global - u.insurance_claim_month if has_claim else 0

                    premium = calculate_unit_insurance(
                        property_value=u.value,
                        years_owned=years_owned,
                        in_flood_zone=u.in_flood_zone,
                        has_claim=has_claim,
                        months_since_claim=months_since_claim,
                        config=engine,
                        market_name=getattr(u, 'market_profile', default_market)
                    )
                    enhanced_insurance_total += calculate_monthly_insurance(premium)

                # Override the basic insurance calculation
                exp["insurance"] = round(enhanced_insurance_total, 2)
                exp["insurance_enhanced"] = True
            else:
                exp["insurance_enhanced"] = False

            # === EXPENSES (paid from operating cash) ===
            cash -= exp["mgmt"]
            cash -= exp["hoa_monthly"]
            cash -= exp["insurance"]
            cash -= exp["tax"]

            # Debt service paid from operating cash
            debt_service = sum(u.monthly_payment for u in units)
            cash -= debt_service

            # Calculate NOI for reporting
            noi = gross - exp["mgmt"] - exp["hoa_monthly"] - exp["insurance"] - exp["tax"]

            # Phase 1.3: Event processing
            event_cost_this_month = 0.0
            event_payout_this_month = 0.0
            events_triggered_this_month = []

            if use_events and units:
                # Check for events to trigger
                triggered_events = check_event_triggers(scheduled_events, year, m)

                for event in triggered_events:
                    result = process_event(
                        event=event,
                        simulation_month=month_global,
                        current_year=year,
                        current_month=m,
                        units_count=units_owned,
                        unit_ids=[u.unit_id for u in units],
                        property_values=[u.value for u in units]
                    )
                    event_results.append(result)
                    event_cost_this_month += result.total_repair_cost
                    events_triggered_this_month.append(result.event_name)

                    # Mark affected units as having a claim
                    for affected_id in result.affected_units:
                        for u in units:
                            if u.unit_id == affected_id:
                                u.insurance_claim_month = month_global
                                break

                # Pay repair costs from operating cash
                cash -= event_cost_this_month

                # Check for insurance payouts due
                payouts = get_pending_payouts(event_results, month_global)
                for payout in payouts:
                    event_payout_this_month += payout["payout_amount"]

                # Receive insurance payouts
                cash += event_payout_this_month

            # Move capex allocation to capex reserve
            capex_reserve += exp["capex_ops"]

            # Phase 1.5: CapEx Schedule - Age systems and process replacements
            capex_replacements_this_month = []
            capex_deferred_this_month = 0.0
            if use_capex_schedule and units:
                for unit in units:
                    if unit.system_ages:
                        # Age systems by one month
                        unit.system_ages = age_systems(unit.system_ages, 1)

                        # Process replacements (systems at end-of-life)
                        updated_ages, capex_reserve, replacements, deferred = process_replacements(
                            unit_id=unit.unit_id,
                            system_ages=unit.system_ages,
                            capex_reserve=capex_reserve,
                            current_month=month_global,
                            current_year=year,
                            config=engine
                        )
                        unit.system_ages = updated_ages
                        capex_replacements_this_month.extend(replacements)
                        capex_deferred_this_month += deferred

                # Log replacements for tracking
                capex_replacements_log.extend(capex_replacements_this_month)

            # Capex ceiling sweep (if enabled)
            capex_sweep = 0.0
            if enable_capex_ceiling and units_owned > 0:
                fixed_monthly = exp["hoa_monthly"] + exp["insurance"] + exp["tax"] + debt_service
                capex_ceiling = fixed_monthly * capex_ceiling_months
                if capex_reserve > capex_ceiling:
                    capex_sweep = capex_reserve - capex_ceiling
                    capex_reserve = capex_ceiling

            # Calculate fixed monthly costs for reserve operations
            fixed_monthly = exp["hoa_monthly"] + exp["insurance"] + exp["tax"] + debt_service

            # Top up rainy reserve FROM operating cash, but protect minimum operating balance
            # Operating cash must retain configured months of fixed costs (default: 1 month)
            min_operating_cash = operating_cash_months * fixed_monthly
            cash_available_for_rainy = max(0.0, cash - min_operating_cash)

            rainy_topup, rainy_reserve = update_rainy_day_reserve(
                fixed_monthly, rainy_reserve, 0.0, cash_available_for_rainy, rainy_months
            )
            # Only subtract what won't violate minimum
            actual_topup = min(rainy_topup, cash_available_for_rainy)
            cash -= actual_topup

            # If we couldn't top up the full amount, adjust rainy reserve accordingly
            if actual_topup < rainy_topup:
                rainy_reserve = rainy_reserve - (rainy_topup - actual_topup)

            # Rainy reserve excess sweep (if enabled)
            rainy_sweep = 0.0
            if enable_rainy_sweep and units_owned > 0:
                rainy_target = rainy_months * fixed_monthly
                rainy_max = rainy_target * rainy_buffer_pct
                if rainy_reserve > rainy_max:
                    rainy_sweep = rainy_reserve - rainy_target
                    rainy_reserve = rainy_target

            cash = max(0.0, cents(cash))

            # === DISTRIBUTION PROCESSING ===
            # Process investor distributions if enabled and triggers are met
            total_value_dist = sum(u.value for u in units)
            total_debt_dist = sum(u.debt for u in units)
            ltv_pct_dist = (total_debt_dist / total_value_dist * 100) if total_value_dist > 0 else 0.0
            total_reserves_dist = cash + rainy_reserve + savings_account

            # Calculate distributable cash = operating cash above minimum operating balance
            # After all reserves are funded, this is what's available for distribution
            min_operating_cash = operating_cash_months * fixed_monthly
            distributable_cash_amount = max(0.0, cash - min_operating_cash)

            dist_result = process_distribution(
                distribution_cfg,
                units_owned,
                noi,
                ltv_pct_dist,
                total_debt_dist,
                total_reserves_dist,
                debt_service,
                fixed_monthly,
                current_year=year,
                distributable_cash=distributable_cash_amount,
                reserve_topup_needed=max(0.0, rainy_topup),
            )

            distribution_amount = dist_result["distribution_amount"]

            # Execute distribution by reducing operating cash
            if distribution_amount > 0:
                cash -= distribution_amount

            freeze, liquidity_req, liquidity_act = liquidity_check(
                cash, rainy_reserve, price_parity, engine, units_owned, max_units, fixed_monthly
            )

            # === FEEDER SELECTION ===
            # Select feeder for prepayment (any with debt, not past cooldown required)
            # This is the property we'll prepay to build equity
            if units and feeder_index is None:
                # Always try to select feeder for prepayment first (regardless of phase)
                feeder_index = select_feeder(units, month_global, cooldown_months, for_refi=False)

            # === PHASE 1: ACQUISITION MODE ===
            purchase_total = dp = closing = 0.0
            purchased_this_month = False
            feeder_cashout = 0.0
            feeder_prepay = 0.0
            savings_deposit = 0.0
            refi_property_index = -1  # Track which property was refinanced

            # Initialize sweep amounts (will be added to feeder prepayment)
            total_sweep = capex_sweep + rainy_sweep

            if units_owned < max_units:
                # Calculate available capital for purchase
                potential_refi = 0.0
                feeder_refi_eligible = False

                if feeder_index is not None and units:
                    is_eligible, _ = is_feeder_refi_eligible(
                        units, feeder_index, month_global, ltv_trigger, cooldown_months
                    )
                    if is_eligible:
                        feeder_refi_eligible = True
                        potential_refi = calculate_potential_refi_cashout(
                            units[feeder_index], max_ltv, cashout_cost
                        )

                # Calculate purchase cost including reserves for NEW property
                dp_pct = dp_first if units_owned == 0 else dp_sub
                down_payment = price_parity * dp_pct
                closing_cost = price_parity * closing_pct

                # Reserve cushion = 6 months of NEW property's fixed costs
                new_prop_fixed = estimate_fixed_costs_for_new_property(
                    price_parity, hoa_annual_this_year, ins_rate, tax_rate,
                    rate_purchase, amort_years, dp_pct
                )
                reserve_cushion = purchase_reserve_months * new_prop_fixed

                total_purchase_cost = down_payment + closing_cost + reserve_cushion

                # Available capital depends on whether we have units yet
                if units_owned == 0:
                    # First purchase: use operating cash + savings
                    available_capital = cash + savings_account
                else:
                    # Subsequent purchases: savings + potential refi
                    available_capital = savings_account + potential_refi

                # Check if we can purchase
                # Note: We use our own capital check, not the legacy freeze flag
                # The feeder strategy has explicit capital requirements
                can_buy = available_capital >= total_purchase_cost

                if can_buy:
                    if units_owned == 0:
                        # First purchase: use savings first, then operating cash
                        if savings_account >= total_purchase_cost:
                            savings_account -= total_purchase_cost
                        else:
                            shortfall = total_purchase_cost - savings_account
                            savings_account = 0.0
                            cash -= shortfall
                    else:
                        # Deploy capital: use savings first, then refi
                        if savings_account >= total_purchase_cost:
                            # Savings alone is enough
                            savings_account -= total_purchase_cost
                            feeder_cashout = 0.0
                        else:
                            # Need to tap refi
                            shortfall = total_purchase_cost - savings_account
                            savings_account = 0.0  # Use all savings

                            if feeder_refi_eligible and feeder_index is not None:
                                # Track which property we're refinancing
                                refi_property_index = units[feeder_index].unit_id
                                # Execute refi (strategy determines max vs min cashout)
                                feeder_cashout, feeder_index = attempt_refi_cashout(
                                    month_global, units, engine, amort_years,
                                    feeder_index, units_owned, shortfall
                                )
                                # Refi cash goes to pending, then used for purchase
                                pending_cashout = 0.0  # Use immediately
                                # Leftover from refi goes to operating cash
                                refi_leftover = feeder_cashout - shortfall
                                if refi_leftover > 0:
                                    cash += refi_leftover
                                # Total cost comes from the refi proceeds
                                # (already extracted, shortfall covered)

                    # Create the new unit
                    purchase_total = down_payment + closing_cost
                    dp = down_payment
                    closing = closing_cost
                    loan = price_parity - down_payment

                    # Phase 1.4: Calculate depreciation basis for new unit
                    unit_depreciation_basis = calculate_depreciation_basis(
                        price_parity, land_percentage
                    ) if use_tax else 0.0

                    # Phase 1.5: Initialize system ages for new unit
                    unit_system_ages = initialize_unit_systems(
                        next_unit_id, engine
                    ) if use_capex_schedule else {}

                    units.append(Unit(
                        value=price_parity,
                        debt=loan,
                        monthly_payment=pmt(rate_purchase, amort_years, loan),
                        rate=rate_purchase,
                        last_refi_month=month_global,
                        unit_id=next_unit_id,
                        cash_invested=purchase_total,
                        purchase_month=month_global,
                        market_profile=default_market,  # Phase 1.1: Assign market profile
                        # Phase 1.4: Tax/Depreciation fields
                        purchase_price=price_parity,
                        depreciation_basis=unit_depreciation_basis,
                        accumulated_depreciation=0.0,
                        # Phase 1.5: CapEx Schedule fields
                        system_ages=unit_system_ages,
                        # Phase 1.6: Financing Dashboard fields
                        original_loan=loan,
                        interest_paid_to_date=0.0,
                        principal_paid_to_date=0.0,
                    ))
                    next_unit_id += 1
                    units_owned += 1
                    purchased_this_month = True

                    # Deposit the reserve cushion into operating cash
                    # This ensures we have funds to top up rainy reserve and maintain operating minimum
                    cash += reserve_cushion

                    # Re-select feeder after purchase
                    feeder_index = select_feeder(units, month_global, cooldown_months, for_refi=True)

                    # Skip surplus allocation this month - reserve cushion needs to stay in cash
                    # to fund rainy reserve and operating minimum in subsequent months

                elif not purchased_this_month:
                    # Can't purchase yet - split surplus between prepay and savings
                    # Calculate surplus after maintaining operating cushion
                    min_operating = operating_cash_months * fixed_monthly if fixed_monthly > 0 else 1000
                    surplus = max(0.0, cash - min_operating)

                    if surplus > 0:
                        if units_owned > 0 and feeder_index is not None:
                            # Dynamic allocation based on capital gap to next purchase
                            capital_gap = total_purchase_cost - available_capital

                            if capital_gap <= 0:
                                # Refi alone covers purchase - maximize yield, stop saving
                                dynamic_feeder_pct = 1.0
                                dynamic_savings_pct = 0.0
                            elif capital_gap < total_purchase_cost * 0.1:
                                # Close to goal (within 10%) - balance prepay and savings
                                dynamic_feeder_pct = 0.5
                                dynamic_savings_pct = 0.5
                            else:
                                # Far from goal - use default split
                                dynamic_feeder_pct = feeder_prepay_pct
                                dynamic_savings_pct = savings_pct

                            # Apply dynamic allocation
                            prepay_amount = surplus * dynamic_feeder_pct
                            feeder_prepay, feeder_index = prepay_feeder(prepay_amount, units, feeder_index)

                            # Savings allocation
                            savings_deposit = surplus * dynamic_savings_pct
                            savings_account += savings_deposit

                            # Deduct from operating cash
                            cash -= (feeder_prepay + savings_deposit)
                            cash = max(0.0, cents(cash))

                            # If feeder was paid off, reselect
                            if feeder_index is None:
                                feeder_index = select_feeder(units, month_global, cooldown_months, for_refi=True)
                        else:
                            # No units yet: all surplus goes to savings for first purchase
                            savings_deposit = surplus
                            savings_account += savings_deposit
                            cash -= savings_deposit
                            cash = max(0.0, cents(cash))

            # === PHASE 2: DEBT PAYOFF MODE ===
            else:
                # At max units - focus on paying off debt
                # No more refis, just prepay the feeder
                feeder_prepay, cash, feeder_index = prepay_surplus(
                    cash, liquidity_req, rainy_reserve, units, fixed_monthly, feeder_index, operating_cash_months
                )

                # If feeder was paid off, reselect from remaining mortgaged properties
                if feeder_index is None:
                    feeder_index = select_feeder(units, month_global, cooldown_months, for_refi=False)

            # === APPLY RESERVE SWEEPS TO FEEDER PREPAYMENT ===
            # Swept reserves are deployed to debt reduction
            if total_sweep > 0 and feeder_index is not None and units:
                sweep_prepay, feeder_index = prepay_feeder(total_sweep, units, feeder_index)
                feeder_prepay += sweep_prepay
                # If feeder was paid off by sweep, reselect
                if feeder_index is None:
                    feeder_index = select_feeder(units, month_global, cooldown_months, for_refi=False)

            # === AMORTIZATION + APPRECIATION + DEPRECIATION ===
            total_monthly_depreciation = 0.0
            total_interest_this_month = 0.0
            total_principal_this_month = 0.0
            for idx, u in enumerate(units):
                # Phase 1.6: Track interest/principal split before amortization
                if use_financing_dashboard and u.debt > 0:
                    interest_portion, principal_portion = get_monthly_interest_principal_split(
                        u.debt, u.monthly_payment, u.rate
                    )
                    u.interest_paid_to_date += interest_portion
                    u.principal_paid_to_date += principal_portion
                    total_interest_this_month += interest_portion
                    total_principal_this_month += principal_portion

                u.debt = amortize_one_month(u.debt, u.monthly_payment, u.rate)
                # Check if unit is now paid off
                if u.debt <= 0:
                    u.debt = 0.0
                    u.monthly_payment = 0.0
                # Skip appreciation for unit purchased this month
                if not (purchased_this_month and idx == len(units) - 1):
                    u.value *= (1 + appreciation / 12)

                # Phase 1.4: Process depreciation for this unit
                if use_tax and u.depreciation_basis > 0:
                    monthly_dep, new_accum = process_monthly_depreciation(
                        u.depreciation_basis,
                        u.accumulated_depreciation,
                        engine
                    )
                    u.accumulated_depreciation = new_accum
                    total_monthly_depreciation += monthly_dep

            # Get current feeder LTV for output
            current_feeder_ltv = get_feeder_ltv(units, feeder_index)

            # Get feeder unit_id for display (use -1 if no feeder)
            feeder_display = units[feeder_index].unit_id if feeder_index is not None else -1

            # === RECORD ROW ===
            total_value = cents(sum(u.value for u in units))
            total_debt = cents(sum(u.debt for u in units))
            total_equity = cents(total_value - total_debt)
            ltv_pct = round((total_debt / total_value * 100) if total_value > 0 else 0.0, 2)
            total_cash_reserves = cents(cash + rainy_reserve + savings_account)
            total_interest_earned = cents(cash_interest_earned + rainy_interest_earned + savings_interest_earned)
            cash_flow_after_debt = cents(noi - debt_service)
            # Operating Cash Flow = operational cash generation (before reserve movements)
            # Shows portfolio profitability from operations
            operating_cash_flow = cents(noi - debt_service - exp["capex_ops"])

            # Distributable Cash Flow = cash available for distribution after reserve obligations
            # Key insight: If operating CF < reserve topup, reserves are funded from existing cash
            # This is a balance sheet transfer, NOT a need for external capital
            # Therefore: Distributable CF should be 0 (can't distribute) not negative (need capital)
            if actual_topup > operating_cash_flow and operating_cash_flow >= 0:
                # Reserves funded partially/fully from existing cash reserves (not operations)
                # Can't distribute anything, but don't need external capital
                distributable_cash_flow = 0.0
            else:
                # Either no reserve topup, or operating CF covers it
                distributable_cash_flow = cents(operating_cash_flow - actual_topup)

            row_dict = {
                # Timeline
                "Year": year,
                "Month": m,
                # Portfolio metrics
                "Properties Owned": units_owned,
                "Property Market Value": cents(price_parity),
                "Total Portfolio Value": total_value,
                "Total Debt": total_debt,
                "Total Equity": total_equity,
                "LTV %": ltv_pct,
                # Income statement
                "Monthly Rental Income": gross,
                "Property Management": exp["mgmt"],
                "CapEx & Maintenance": exp["capex_ops"],
                "HOA Fees": exp["hoa_monthly"],
                "Property Insurance": exp["insurance"],
                "Property Taxes": exp["tax"],
                "Debt Service": cents(debt_service),
                "Net Operating Income": noi,
                "Cash Flow After Debt Service": cash_flow_after_debt,
                "Operating Cash Flow": operating_cash_flow,
                "Distributable Cash Flow": distributable_cash_flow,
                "Monthly Savings Contribution": cents(annual_savings / 12),
                # Cash accounts
                "Operating Cash": cents(cash),
                "Emergency Reserve": cents(rainy_reserve),
                "Growth Savings": cents(savings_account),
                "Total Cash Reserves": total_cash_reserves,
                # Interest earned
                "Total Interest Earned": total_interest_earned,
                "Interest - Operating": cents(cash_interest_earned),
                "Interest - Reserve": cents(rainy_interest_earned),
                "Interest - Savings": cents(savings_interest_earned),
                # Liquidity
                "Required Reserves": cents(liquidity_req),
                "Available Liquidity": cents(liquidity_act),
                # Acquisition details
                "Property Purchase": purchase_total,
                "Down Payment": dp,
                "Closing Costs": closing,
                "Total Acquisition Cost": purchase_total,
                # Financing activity
                "Refinance Proceeds": feeder_cashout,
                "Principal Prepayment": feeder_prepay,
                "Savings Deposit": cents(savings_deposit),
                # Distribution tracking
                "Distribution Enabled": 1 if dist_result["enabled"] else 0,
                "Distribution Eligible": 1 if dist_result["eligible"] else 0,
                "Distribution Safe": 1 if dist_result["safe"] else 0,
                "Distribution Amount": cents(distribution_amount),
                "Distribution Reason": dist_result["reason"],
                # Phase 1.1: Seasonality tracking
                "Seasonality Enabled": 1 if seasonal_enabled else 0,
                "Seasonal Revenue Delta": cents(seasonal_delta),
                # Phase 1.4: Tax/Depreciation tracking
                "Tax Modeling Enabled": 1 if use_tax else 0,
                "Monthly Depreciation": cents(total_monthly_depreciation),
                "Annual Depreciation": cents(total_monthly_depreciation * 12),
                "Total Accumulated Depreciation": cents(sum(u.accumulated_depreciation for u in units)),
                "Total Depreciation Basis": cents(sum(u.depreciation_basis for u in units)),
                # Phase 1.2: Enhanced insurance tracking
                "Enhanced Insurance Enabled": 1 if use_enhanced_insurance else 0,
                "Insurance Cost": exp["insurance"],
                # Phase 1.3: Event tracking
                "Events Enabled": 1 if use_events else 0,
                "Event Cost": cents(event_cost_this_month),
                "Insurance Payout": cents(event_payout_this_month),
                "Events Triggered": "; ".join(events_triggered_this_month) if events_triggered_this_month else "",
                # Internal tracking (hidden from standard reports)
                "_RainyTarget": cents(rainy_months * fixed_monthly),
                "_RainyTopup": cents(rainy_topup),
                "_RainySweep": cents(rainy_sweep),
                "_CapexBalance": cents(capex_reserve),
                "_CapexSweep": cents(capex_sweep),
                "_FreezeFlag": int(freeze),
                "_FeederIndex": feeder_display,
                "_FeederLTV": round(current_feeder_ltv, 4),
                "_RefiPropertyIndex": refi_property_index,
                # Phase 1.5: CapEx Schedule tracking
                "_CapexScheduleEnabled": 1 if use_capex_schedule else 0,
                "_CapexReplacementCount": len(capex_replacements_this_month),
                "_CapexReplacementCost": cents(sum(r.cost for r in capex_replacements_this_month if r.from_reserve)),
                "_CapexDeferredMaintenance": cents(capex_deferred_this_month),
                # Phase 1.6: Financing Dashboard tracking
                "_FinancingDashboardEnabled": 1 if use_financing_dashboard else 0,
                "_InterestPaidThisMonth": cents(total_interest_this_month),
                "_PrincipalPaidThisMonth": cents(total_principal_this_month),
                "_TotalInterestPaid": cents(sum(u.interest_paid_to_date for u in units)),
                "_TotalPrincipalPaid": cents(sum(u.principal_paid_to_date for u in units)),
            }

            rows.append(row_dict)

            # Record individual unit data
            for idx, unit in enumerate(units):
                unit_equity = cents(unit.value - unit.debt)
                unit_ltv = round((unit.debt / unit.value * 100) if unit.value > 0 else 0.0, 2)
                is_feeder = (idx == feeder_index)

                # Allocate income/expenses proportionally by value
                num_units = len(units)
                if num_units > 0 and total_value > 0:
                    # Option 2: Proportional by value (more accurate)
                    unit_share = unit.value / total_value
                else:
                    unit_share = 0.0

                # Allocate portfolio-level income/expenses to this unit
                unit_rental_income = cents(gross * unit_share)
                unit_property_mgmt = cents(exp["mgmt"] * unit_share)
                unit_capex = cents(exp["capex_ops"] * unit_share)
                unit_hoa = cents(exp["hoa_monthly"] * unit_share)
                unit_insurance = cents(exp["insurance"] * unit_share)
                unit_property_tax = cents(exp["tax"] * unit_share)

                # Unit already has its own debt service
                unit_debt_service = cents(unit.monthly_payment)

                # Calculate unit-level metrics
                unit_noi = cents(
                    unit_rental_income - unit_property_mgmt - unit_capex -
                    unit_hoa - unit_insurance - unit_property_tax
                )
                unit_operating_cf = cents(unit_noi - unit_debt_service)

                # Calculate expense ratios (expenses as % of revenue)
                total_unit_expenses = cents(unit_property_mgmt + unit_capex + unit_hoa + unit_insurance + unit_property_tax)
                unit_expense_ratio = round((total_unit_expenses / unit_rental_income * 100) if unit_rental_income > 0 else 0.0, 2)
                unit_mgmt_ratio = round((unit_property_mgmt / unit_rental_income * 100) if unit_rental_income > 0 else 0.0, 2)
                unit_capex_ratio = round((unit_capex / unit_rental_income * 100) if unit_rental_income > 0 else 0.0, 2)
                unit_noi_margin = round((unit_noi / unit_rental_income * 100) if unit_rental_income > 0 else 0.0, 2)

                # Calculate return metrics
                # Cash-on-Cash Return: Annual Operating CF / Initial Cash Invested
                annual_operating_cf = unit_operating_cf * 12
                unit_coc_return = round((annual_operating_cf / unit.cash_invested * 100) if unit.cash_invested > 0 else 0.0, 2)

                # Cap Rate: Annual NOI / Property Value
                annual_noi = unit_noi * 12
                unit_cap_rate = round((annual_noi / unit.value * 100) if unit.value > 0 else 0.0, 2)

                # Debt Service Coverage Ratio: NOI / Debt Service
                unit_dscr = round((unit_noi / unit_debt_service) if unit_debt_service > 0 else 999.99, 2)

                # ROI: (Current Equity - Cash Invested) / Cash Invested
                unit_roi = round(((unit_equity - unit.cash_invested) / unit.cash_invested * 100) if unit.cash_invested > 0 else 0.0, 2)

                # Note: Reserve topup allocation would require more complex logic
                # For now, we'll just show operating CF at unit level

                unit_rows.append({
                    "Year": year,
                    "Month": m,
                    "Unit_ID": unit.unit_id,
                    "Unit_Value": cents(unit.value),
                    "Unit_Debt": cents(unit.debt),
                    "Unit_Equity": unit_equity,
                    "Unit_LTV": unit_ltv,
                    "Unit_Monthly_Payment": unit_debt_service,
                    "Unit_Interest_Rate": round(unit.rate * 100, 2),  # Convert to percentage
                    "Is_Feeder": is_feeder,
                    "Months_Since_Last_Refi": month_global - unit.last_refi_month,
                    "Unit_Age_Months": month_global - unit.purchase_month,
                    # Income/Expense allocation
                    "Unit_Rental_Income": unit_rental_income,
                    "Unit_Property_Mgmt": unit_property_mgmt,
                    "Unit_CapEx": unit_capex,
                    "Unit_HOA": unit_hoa,
                    "Unit_Insurance": unit_insurance,
                    "Unit_Property_Tax": unit_property_tax,
                    "Unit_Debt_Service": unit_debt_service,
                    "Unit_NOI": unit_noi,
                    "Unit_Operating_CF": unit_operating_cf,
                    # Expense ratios
                    "Unit_Total_Expenses": total_unit_expenses,
                    "Unit_Expense_Ratio": unit_expense_ratio,
                    "Unit_Mgmt_Fee_Ratio": unit_mgmt_ratio,
                    "Unit_CapEx_Ratio": unit_capex_ratio,
                    "Unit_NOI_Margin": unit_noi_margin,
                    # Return metrics
                    "Unit_Cash_Invested": cents(unit.cash_invested),
                    "Unit_Cash_On_Cash_Return": unit_coc_return,
                    "Unit_Cap_Rate": unit_cap_rate,
                    "Unit_DSCR": unit_dscr,
                    "Unit_ROI": unit_roi,
                    # Phase 1.1: Market profile
                    "Unit_Market_Profile": getattr(unit, 'market_profile', default_market),
                    # Phase 1.4: Depreciation tracking
                    "Unit_Purchase_Price": cents(getattr(unit, 'purchase_price', 0.0)),
                    "Unit_Depreciation_Basis": cents(getattr(unit, 'depreciation_basis', 0.0)),
                    "Unit_Accumulated_Depreciation": cents(getattr(unit, 'accumulated_depreciation', 0.0)),
                    # Phase 1.2: Insurance tracking
                    "Unit_In_Flood_Zone": 1 if getattr(unit, 'in_flood_zone', False) else 0,
                    "Unit_Has_Insurance_Claim": 1 if getattr(unit, 'insurance_claim_month', 0) > 0 else 0,
                    # Phase 1.6: Financing Dashboard tracking
                    "Unit_Original_Loan": cents(getattr(unit, 'original_loan', 0.0)),
                    "Unit_Interest_Paid_To_Date": cents(getattr(unit, 'interest_paid_to_date', 0.0)),
                    "Unit_Principal_Paid_To_Date": cents(getattr(unit, 'principal_paid_to_date', 0.0)),
                })

    monthly_df = pd.DataFrame(rows)
    unit_df = pd.DataFrame(unit_rows)
    return SimulationResult(monthly=monthly_df, yearly=pd.DataFrame(), units=unit_df)
