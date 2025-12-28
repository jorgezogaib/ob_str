"""
KPI Cards Component - Display key performance indicators
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from typing import Optional, Dict, Any


def format_large_number(value: float, include_sign: bool = False) -> str:
    """Format large numbers with K/M suffix for compact display."""
    sign = "+" if include_sign and value > 0 else ""
    if abs(value) >= 1_000_000:
        return f"{sign}${value/1_000_000:.2f}M"
    elif abs(value) >= 1_000:
        return f"{sign}${value/1_000:.1f}K"
    else:
        return f"{sign}${value:,.0f}"


def format_delta(value: float) -> str:
    """Format delta values - positive with +, negative with - (no $ prefix for Streamlit)."""
    if abs(value) >= 1_000_000:
        return f"{value/1_000_000:+.2f}M"
    elif abs(value) >= 1_000:
        return f"{value/1_000:+.1f}K"
    else:
        return f"{value:+,.0f}"


def render_kpi_cards(
    portfolio_df: pd.DataFrame,
    config: Dict[str, Any],
    previous_df: Optional[pd.DataFrame] = None
):
    """
    Render KPI cards for current simulation results (single row, 6 metrics).

    Args:
        portfolio_df: Current simulation portfolio DataFrame
        config: Current configuration
        previous_df: Previous run's portfolio DataFrame (for deltas)
    """
    final_row = portfolio_df.iloc[-1]
    max_units = config['policies']['portfolio']['maxUnits']

    # Calculate deltas if previous run available
    if previous_df is not None:
        prev_final = previous_df.iloc[-1]

    # Single row: 6 metrics
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        delta_str = None
        if previous_df is not None:
            delta_val = final_row['Total Portfolio Value'] - prev_final['Total Portfolio Value']
            delta_str = format_delta(delta_val)
        st.metric(
            "Portfolio Value",
            format_large_number(final_row['Total Portfolio Value']),
            delta=delta_str
        )

    with col2:
        delta_str = None
        if previous_df is not None:
            delta_val = final_row['Total Equity'] - prev_final['Total Equity']
            delta_str = format_delta(delta_val)
        st.metric(
            "Equity",
            format_large_number(final_row['Total Equity']),
            delta=delta_str
        )

    with col3:
        st.metric("Properties", f"{int(final_row['Properties Owned'])}/{max_units}")

    with col4:
        # Find year when max units reached
        max_units_rows = portfolio_df[portfolio_df['Properties Owned'] == max_units]
        if len(max_units_rows) > 0:
            year_hit_max = int(max_units_rows.iloc[0]['Year'])
            st.metric("Max Units", f"Y{year_hit_max}")
        else:
            st.metric("Max Units", "N/A")

    with col5:
        # Find year when debt-free
        had_debt = portfolio_df[portfolio_df['Total Debt'] > 0]
        if len(had_debt) >= 12:
            last_debt_idx = had_debt.index[-1]
            after_last_debt = portfolio_df.loc[last_debt_idx + 1:] if last_debt_idx + 1 < len(portfolio_df) else pd.DataFrame()
            if len(after_last_debt) > 0 and after_last_debt.iloc[0]['Total Debt'] == 0:
                debt_free_year = int(after_last_debt.iloc[0]['Year'])
                st.metric("Debt-Free", f"Y{debt_free_year}")
            else:
                st.metric("Debt-Free", "N/A")
        elif len(had_debt) > 0:
            last_debt_idx = had_debt.index[-1]
            after_last_debt = portfolio_df.loc[last_debt_idx + 1:] if last_debt_idx + 1 < len(portfolio_df) else pd.DataFrame()
            if len(after_last_debt) > 0 and after_last_debt.iloc[0]['Total Debt'] == 0:
                debt_free_year = int(after_last_debt.iloc[0]['Year'])
                st.metric("Debt-Free", f"Y{debt_free_year}")
            else:
                st.metric("Debt-Free", "N/A")
        else:
            st.metric("Debt-Free", "No debt")

    with col6:
        delta_str = None
        if previous_df is not None:
            delta_val = final_row['Total Cash Reserves'] - prev_final['Total Cash Reserves']
            delta_str = format_delta(delta_val)
        st.metric(
            "Cash Reserves",
            format_large_number(final_row['Total Cash Reserves']),
            delta=delta_str
        )


def render_validation_summary(portfolio_df: pd.DataFrame, config: Dict[str, Any]):
    """
    Render validation status summary with categorized checks.

    Args:
        portfolio_df: Portfolio DataFrame
        config: Configuration dict
    """
    max_units = config['policies']['portfolio']['maxUnits']
    final_row = portfolio_df.iloc[-1]

    # Extract validation config with defaults
    val_cfg = config.get('validation', {})

    # Categorize validations
    validations = {
        'Portfolio': [],
        'Cash Flow': [],
        'Reserves': [],
        'Debt Management': [],
        'Performance': [],
        'Mechanics': []
    }

    # === PORTFOLIO CHECKS ===

    # Check 1: All properties acquired
    if final_row['Properties Owned'] == max_units:
        validations['Portfolio'].append(('pass', f"All properties acquired ({max_units}/{max_units})"))
    else:
        validations['Portfolio'].append(('warn', f"Only {int(final_row['Properties Owned'])}/{max_units} properties acquired"))

    # Check 2: Acquisition Pacing Sanity Check
    acquisition_months = portfolio_df[portfolio_df['Property Purchase'] > 0]
    if len(acquisition_months) > 1:
        consecutive_buys = (acquisition_months.index.to_series().diff() == 1).sum()
        max_consecutive = val_cfg.get('acquisition', {}).get('maxConsecutiveMonths', 0)
        if consecutive_buys > max_consecutive:
            validations['Portfolio'].append(('warn', f"Back-to-back acquisitions in {consecutive_buys} instances - unrealistic for due diligence"))

    # Check if stuck despite liquidity
    min_liquidity = val_cfg.get('acquisition', {}).get('minLiquidityToFlag', 50000.0)
    max_months_stuck = val_cfg.get('acquisition', {}).get('maxMonthsStuck', 60)
    year_stop_checking = val_cfg.get('acquisition', {}).get('yearToStopCheckingStuck', 25)

    stuck_periods = portfolio_df[
        (portfolio_df['Properties Owned'] < max_units) &
        (portfolio_df['Available Liquidity'] > min_liquidity) &
        (portfolio_df['Year'] < year_stop_checking)
    ]
    if len(stuck_periods) > max_months_stuck:
        props_owned = stuck_periods.iloc[0]['Properties Owned'] if len(stuck_periods) > 0 else 0
        validations['Portfolio'].append(('warn', f"Stuck at {int(props_owned)} properties for {len(stuck_periods)} months despite ${min_liquidity:,.0f}+ liquidity"))

    # Check 3: LTV Trajectory Validation
    max_safe_ltv = val_cfg.get('ltv', {}).get('maxSafeThreshold', 0.85) * 100
    dangerous_ltv = portfolio_df[(portfolio_df['LTV %'] > max_safe_ltv) & (portfolio_df['Properties Owned'] > 0)]
    if len(dangerous_ltv) > 0:
        max_ltv_seen = dangerous_ltv['LTV %'].max()
        validations['Portfolio'].append(('warn', f"LTV exceeded {max_safe_ltv:.0f}% in {len(dangerous_ltv)} months (max: {max_ltv_seen:.1f}%) - exceeds lender limits"))

    # Check for impossible LTV drops
    portfolio_df_temp = portfolio_df.copy()
    portfolio_df_temp['LTV_Drop'] = portfolio_df_temp['LTV %'].diff().abs()
    max_drop_threshold = val_cfg.get('ltv', {}).get('maxMonthlyDropWithoutEvent', 0.10) * 100
    big_drops = portfolio_df_temp[
        (portfolio_df_temp['LTV_Drop'] > max_drop_threshold) &
        (portfolio_df_temp['Refinance Proceeds'] == 0) &
        (portfolio_df_temp['Property Purchase'] == 0)
    ]
    if len(big_drops) > 0:
        validations['Portfolio'].append(('warn', f"Suspicious LTV drop >{max_drop_threshold:.0f}% without refi/purchase in {len(big_drops)} months"))

    # Check 4: Portfolio Concentration
    min_props_year5 = val_cfg.get('portfolio', {}).get('minPropertiesByYear5', 3)
    years_under_min = portfolio_df[(portfolio_df['Properties Owned'] < min_props_year5) & (portfolio_df['Year'] > 5)]
    if len(years_under_min) > 60:
        validations['Portfolio'].append(('warn', f"Portfolio under {min_props_year5} properties for {len(years_under_min)/12:.1f} years after Year 5 - concentration risk"))

    # Check 5: Equity Growth Validation
    appreciation_rate = config['market']['annualAppreciation']
    equity_tolerance = val_cfg.get('portfolio', {}).get('equityGrowthTolerancePct', 0.70)
    years_with_props = portfolio_df[portfolio_df['Properties Owned'] > 0]

    if len(years_with_props) > 12:
        equity_start = years_with_props.iloc[12]['Total Equity']
        equity_end = years_with_props.iloc[-1]['Total Equity']
        if equity_start > 0:
            equity_growth = (equity_end / equity_start) - 1
            years = (len(years_with_props) - 12) / 12
            expected_min_growth = (1 + appreciation_rate) ** years - 1

            if equity_growth < expected_min_growth * equity_tolerance:
                validations['Portfolio'].append(('warn', f"Equity grew {equity_growth:.1%} over {years:.1f}y, expected ≥{expected_min_growth*equity_tolerance:.1%}"))

    # Check 6: Debt-Free Timeline Realism
    min_debt_free = val_cfg.get('portfolio', {}).get('minDebtFreeYear', 15)
    max_debt_free = val_cfg.get('portfolio', {}).get('maxDebtFreeYear', 30)
    min_units_check = val_cfg.get('portfolio', {}).get('minUnitsForDebtFreeCheck', 5)

    had_debt = portfolio_df[portfolio_df['Total Debt'] > 0]
    if len(had_debt) >= 12:
        last_debt_idx = had_debt.index[-1]
        after_last_debt = portfolio_df.loc[last_debt_idx + 1:] if last_debt_idx + 1 < len(portfolio_df) else pd.DataFrame()
        if len(after_last_debt) > 0 and after_last_debt.iloc[0]['Total Debt'] == 0:
            debt_free_year = int(after_last_debt.iloc[0]['Year'])

            # Check if too fast
            if debt_free_year < min_debt_free and max_units >= min_units_check:
                validations['Portfolio'].append(('warn', f"Debt-free by Year {debt_free_year} with {max_units} units - validate prepayment assumptions"))
            else:
                validations['Portfolio'].append(('pass', f"Debt payoff completed (Year {debt_free_year})"))
        else:
            validations['Portfolio'].append(('warn', f"Debt not fully paid off by Year {max_debt_free}"))
    elif len(had_debt) > 0:
        last_debt_idx = had_debt.index[-1]
        after_last_debt = portfolio_df.loc[last_debt_idx + 1:] if last_debt_idx + 1 < len(portfolio_df) else pd.DataFrame()
        if len(after_last_debt) > 0 and after_last_debt.iloc[0]['Total Debt'] == 0:
            debt_free_year = int(after_last_debt.iloc[0]['Year'])
            if debt_free_year < min_debt_free and max_units >= min_units_check:
                validations['Portfolio'].append(('warn', f"Debt-free by Year {debt_free_year} with {max_units} units - validate prepayment assumptions"))
            else:
                validations['Portfolio'].append(('pass', f"Debt payoff completed (Year {debt_free_year})"))
        else:
            validations['Portfolio'].append(('warn', f"Debt not fully paid off by Year {max_debt_free}"))
    else:
        validations['Portfolio'].append(('pass', "No debt taken (all-cash purchases)"))

    # === CASH FLOW CHECKS ===

    # Check 7: Operating Cash Never Goes Negative (enhanced)
    negative_cash = portfolio_df[portfolio_df['Operating Cash'] < 0]
    if len(negative_cash) == 0:
        validations['Cash Flow'].append(('pass', "No cash shortfalls (Operating Cash never negative)"))
    else:
        min_cash = negative_cash['Operating Cash'].min()
        total_shortfall = abs(negative_cash['Operating Cash'].sum())
        validations['Cash Flow'].append(('warn', f"Cash shortfall: {len(negative_cash)} months, worst: ${min_cash:,.0f}, total: ${total_shortfall:,.0f}"))

    # Check 8: DSCR Validation
    critical_dscr = val_cfg.get('dscr', {}).get('criticalThreshold', 1.0)
    lender_min = config.get('constants', {}).get('acquisition', {}).get('dscrThresholdForRefi',
                 val_cfg.get('dscr', {}).get('lenderMinimum', 1.25))
    max_months_below = val_cfg.get('dscr', {}).get('maxMonthsBelowLender', 12)

    months_with_debt = portfolio_df[portfolio_df['Debt Service'] > 0].copy()
    if len(months_with_debt) > 0:
        months_with_debt['DSCR'] = months_with_debt['Net Operating Income'] / months_with_debt['Debt Service']

        critical_months = months_with_debt[months_with_debt['DSCR'] < critical_dscr]
        if len(critical_months) > 0:
            min_dscr = critical_months['DSCR'].min()
            validations['Cash Flow'].append(('warn', f"DSCR below {critical_dscr:.1f} (critical) in {len(critical_months)} months (worst: {min_dscr:.2f})"))
        else:
            poor_dscr = months_with_debt[months_with_debt['DSCR'] < lender_min]
            if len(poor_dscr) > max_months_below:
                avg_dscr = poor_dscr['DSCR'].mean()
                validations['Cash Flow'].append(('warn', f"DSCR below {lender_min:.2f} in {len(poor_dscr)} months (avg: {avg_dscr:.2f})"))
            else:
                avg_dscr = months_with_debt['DSCR'].mean()
                min_dscr = months_with_debt['DSCR'].min()
                validations['Cash Flow'].append(('pass', f"DSCR healthy (avg: {avg_dscr:.2f}, min: {min_dscr:.2f})"))

    # Check 9: Cash Flow Volatility
    portfolio_df_temp = portfolio_df.copy()
    portfolio_df_temp['NOI_Change'] = portfolio_df_temp['Net Operating Income'].diff()
    noi_threshold = val_cfg.get('cashFlow', {}).get('noiVolatilityThreshold', 3000.0)
    volatile_months = portfolio_df_temp[
        (portfolio_df_temp['NOI_Change'].abs() > noi_threshold) &
        (portfolio_df_temp['Property Purchase'] == 0) &
        (portfolio_df_temp['Properties Owned'] == portfolio_df_temp['Properties Owned'].shift(1))
    ]
    if len(volatile_months) > 12:
        validations['Cash Flow'].append(('warn', f"NOI volatility >${noi_threshold:,.0f}/month in {len(volatile_months)} months without acquisitions"))

    # Check 10: Negative Cash Flow After Debt Service
    max_negative_months = val_cfg.get('cashFlow', {}).get('maxMonthsNegative', 6)
    negative_cashflow = portfolio_df[portfolio_df['Cash Flow After Debt Service'] < 0]
    if len(negative_cashflow) > max_negative_months:
        validations['Cash Flow'].append(('warn', f"Negative cash flow after debt service for {len(negative_cashflow)} months (max: {max_negative_months})"))

    # === DEBT MANAGEMENT CHECKS ===

    # Check 11: Refinance Economic Rationality
    min_proceeds = val_cfg.get('refinance', {}).get('minProceedsToJustifyCosts', 20000.0)
    refi_events = portfolio_df[portfolio_df['Refinance Proceeds'] > 0]
    small_refis = refi_events[refi_events['Refinance Proceeds'] < min_proceeds]
    if len(small_refis) > 0:
        for idx, row in small_refis.iterrows():
            validations['Debt Management'].append(('warn', f"Refi in Y{int(row['Year'])}M{int(row['Month'])} extracted only ${row['Refinance Proceeds']:,.0f} (min: ${min_proceeds:,.0f})"))

    # Check 12: Refinance Frequency Validation
    total_refis = len(refi_events)
    refi_cooldown = config.get('constants', {}).get('acquisition', {}).get('refiCooldownYears', 3)
    years_simulated = portfolio_df['Year'].max()
    theoretical_max_refis = max_units * (years_simulated / max(refi_cooldown, 1)) if refi_cooldown > 0 else max_units * years_simulated

    if total_refis > theoretical_max_refis * 1.2:
        validations['Debt Management'].append(('warn', f"Model performed {total_refis} refis vs theoretical max {theoretical_max_refis:.0f} - check refi logic"))

    # === RESERVE CHECKS ===

    # Check 13: Reserve Sufficiency at Acquisition
    min_cushion = val_cfg.get('reserves', {}).get('minCushionPctAtPurchase', 0.80)
    purchase_events = portfolio_df[portfolio_df['Property Purchase'] > 0]
    for idx, row in purchase_events.iterrows():
        post_purchase_reserves = row['Total Cash Reserves']
        required_reserves = row['Required Reserves']

        if post_purchase_reserves < required_reserves * min_cushion:
            validations['Reserves'].append(('warn', f"Property purchased Y{int(row['Year'])}M{int(row['Month'])} with ${post_purchase_reserves:,.0f} reserves (required: ${required_reserves:,.0f})"))

    # Check 14: Emergency reserves maintained
    below_target = portfolio_df[portfolio_df['Emergency Reserve'] < portfolio_df['_RainyTarget'] * 0.9]
    if len(below_target) <= 5:
        validations['Reserves'].append(('pass', "Emergency reserves maintained adequately"))
    else:
        validations['Reserves'].append(('warn', f"Emergency reserves below target in {len(below_target)} month(s)"))

    # Check 15: Reserve Balance Anomalies
    portfolio_df_temp = portfolio_df.copy()
    portfolio_df_temp['Reserve_Change_Pct'] = portfolio_df_temp['Total Cash Reserves'].pct_change()
    max_drop_pct = val_cfg.get('reserves', {}).get('maxMonthlyDropPct', 0.50)

    big_drops = portfolio_df_temp[
        (portfolio_df_temp['Reserve_Change_Pct'] < -max_drop_pct) &
        (portfolio_df_temp['Property Purchase'] == 0)
    ]
    if len(big_drops) > 0:
        validations['Reserves'].append(('warn', f"Reserve balance dropped >{max_drop_pct:.0%} in single month ({len(big_drops)} occurrences)"))

    max_hoarding = val_cfg.get('reserves', {}).get('maxReserveHoarding', 500000.0)
    max_reserves = portfolio_df['Total Cash Reserves'].max()
    if max_reserves > max_hoarding:
        validations['Reserves'].append(('warn', f"Reserves peaked at ${max_reserves:,.0f} - may be hoarding vs deploying"))

    # Check 16: Reserve Sweep Mechanics
    enable_rainy_sweep = config.get('constants', {}).get('reserves', {}).get('enableRainySweep', False)
    if enable_rainy_sweep:
        buffer_pct = config.get('constants', {}).get('reserves', {}).get('rainyBufferPct', 1.2)
        sweep_tolerance = val_cfg.get('reserves', {}).get('sweepToleranceMonths', 12)
        should_sweep = portfolio_df[
            (portfolio_df['Emergency Reserve'] > portfolio_df['_RainyTarget'] * buffer_pct) &
            (portfolio_df['_RainySweep'] == 0) &
            (portfolio_df['Total Debt'] > 0)
        ]

        if len(should_sweep) > sweep_tolerance:
            validations['Reserves'].append(('warn', f"Emergency reserves exceeded buffer in {len(should_sweep)} months but no sweep"))

    # === PERFORMANCE CHECKS ===

    # Check 17: Cash-on-Cash Return Reasonability
    min_coc = val_cfg.get('cashFlow', {}).get('minCashOnCashReturn', 0.05)
    max_coc = val_cfg.get('cashFlow', {}).get('maxCashOnCashReturn', 0.30)

    initial_cash = config.get('constants', {}).get('financial', {}).get('startingCash', 0)
    annual_savings = config.get('constants', {}).get('financial', {}).get('annualSavings', 0)
    years = final_row['Year']
    total_contributed = initial_cash + (annual_savings * years)

    if total_contributed > 0:
        total_distributions = portfolio_df['Distributable Cash Flow'].sum()
        annualized_coc = (total_distributions / total_contributed) / years if years > 0 else 0

        if annualized_coc > max_coc:
            validations['Performance'].append(('warn', f"Cash-on-cash return {annualized_coc:.1%} annually - validate assumptions (very high)"))
        elif annualized_coc < min_coc and final_row['Properties Owned'] >= 3:
            validations['Performance'].append(('warn', f"Cash-on-cash return only {annualized_coc:.1%} annually - strategy underperforming"))
        else:
            validations['Performance'].append(('pass', f"Cash-on-cash return {annualized_coc:.1%} annually - reasonable"))

    # Check 18: Portfolio Value Growth Reasonability
    portfolio_growth_tolerance = val_cfg.get('portfolio', {}).get('portfolioGrowthTolerancePct', 0.60)
    first_prop = portfolio_df[portfolio_df['Properties Owned'] > 0]
    if len(first_prop) > 0:
        first_prop = first_prop.iloc[0]
        years_held = (final_row['Year'] - first_prop['Year'])
        if years_held >= 5 and first_prop['Total Portfolio Value'] > 0:
            portfolio_growth = (final_row['Total Portfolio Value'] / first_prop['Total Portfolio Value']) - 1
            expected_growth = (1 + appreciation_rate) ** years_held - 1

            if portfolio_growth < expected_growth * portfolio_growth_tolerance:
                validations['Performance'].append(('warn', f"Portfolio grew {portfolio_growth:.1%} over {years_held:.0f}y, expected {expected_growth*portfolio_growth_tolerance:.1%}"))

    # === MECHANICS CHECKS ===

    # Check 19: Feeder tracking
    untracked_feeder = portfolio_df[(portfolio_df['Properties Owned'] > 0) & (portfolio_df['_FeederIndex'] == -1)]
    if len(untracked_feeder) == 0:
        validations['Mechanics'].append(('pass', "Feeder tracked in all months with properties"))
    else:
        validations['Mechanics'].append(('warn', f"Feeder not tracked in {len(untracked_feeder)} month(s)"))

    # Check 20: Feeder Property Prepayment Effectiveness
    min_ltv_decrease = val_cfg.get('feeder', {}).get('minAnnualLTVDecrease', 0.05)
    feeder_months = portfolio_df[portfolio_df['_FeederIndex'] >= 0]
    if len(feeder_months) > 24:
        feeder_ltv_start = feeder_months.iloc[12]['_FeederLTV']
        feeder_ltv_end = feeder_months.iloc[-1]['_FeederLTV']
        years_elapsed = (len(feeder_months) - 12) / 12

        if feeder_ltv_start > 0 and years_elapsed > 0:
            annual_decrease = (feeder_ltv_start - feeder_ltv_end) / years_elapsed
            if annual_decrease < min_ltv_decrease:
                validations['Mechanics'].append(('warn', f"Feeder LTV decreased {annual_decrease:.1%}/year (target: {min_ltv_decrease:.1%}) - prepayment insufficient"))

    # Check 21: Acquisition Starvation Despite Growth
    max_months_same_count = val_cfg.get('timing', {}).get('maxMonthsAtSamePropertyCount', 24)
    min_equity_growth = val_cfg.get('timing', {}).get('minEquityGrowthWhileStuck', 0.20)

    for prop_count in range(1, max_units):
        at_this_count = portfolio_df[portfolio_df['Properties Owned'] == prop_count]
        if len(at_this_count) > max_months_same_count:
            equity_start = at_this_count['Total Equity'].iloc[0]
            equity_end = at_this_count['Total Equity'].iloc[-1]
            if equity_start > 0:
                equity_growth_ratio = equity_end / equity_start
                if equity_growth_ratio > (1 + min_equity_growth):
                    validations['Mechanics'].append(('warn', f"Stuck at {prop_count} properties for {len(at_this_count)} months despite {(equity_growth_ratio-1):.0%} equity growth"))
                    break

    # Count issues across all categories
    total_issues = sum(1 for cat in validations.values() for status, _ in cat if status == 'warn')
    total_checks = sum(len(cat) for cat in validations.values())

    # Prepare export data
    export_data = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_checks': total_checks,
            'total_warnings': total_issues,
            'total_passed': total_checks - total_issues
        },
        'portfolio_stats': {
            'properties_owned': int(final_row['Properties Owned']),
            'total_portfolio_value': float(final_row['Total Portfolio Value']),
            'total_equity': float(final_row['Total Equity']),
            'total_debt': float(final_row['Total Debt']),
            'ltv_percent': float(final_row['LTV %']),
            'simulation_years': int(final_row['Year'])
        },
        'validation_thresholds': val_cfg,
        'results_by_category': {}
    }

    # Convert validations to export format
    for category, checks in validations.items():
        export_data['results_by_category'][category] = [
            {'status': status, 'message': msg} for status, msg in checks
        ]

    # Render summary with categories and export button
    col1, col2 = st.columns([6, 1])

    with col1:
        if total_issues == 0:
            st.markdown(f"✓ **Model Validation: All {total_checks} Checks Passed**")
        else:
            st.markdown(f"⚠ **Model Validation: {total_issues}/{total_checks} Warning(s)**")

    with col2:
        # Export button
        export_json = json.dumps(export_data, indent=2)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="📥 Export",
            data=export_json,
            file_name=f"validation_results_{timestamp}.json",
            mime="application/json",
            help="Download validation results as JSON"
        )

    # Expandable detail view
    if total_issues == 0:
        with st.expander("View Details", expanded=False):
            for category, checks in validations.items():
                if checks:
                    st.markdown(f"**{category}**")
                    for status, msg in checks:
                        st.success(f"  • {msg}")
    else:
        with st.expander("View Details", expanded=True):
            for category, checks in validations.items():
                if checks:
                    st.markdown(f"**{category}**")
                    for status, msg in checks:
                        if status == 'pass':
                            st.success(f"  • {msg}")
                        else:
                            st.warning(f"  • {msg}")
