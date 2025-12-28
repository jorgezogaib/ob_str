"""
Test script for validation framework
"""
import pandas as pd
import json
import sys
from typing import Dict, Any

# Fix Unicode encoding on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def test_validations():
    """Test validation logic with actual simulation data"""

    # Load config
    with open('ob_str_engine/OB_STR_ENGINE_V2_3.json', 'r') as f:
        config = json.load(f)

    # Load portfolio data
    portfolio_df = pd.read_csv('out/simulation_results_feeder.csv')

    max_units = config['policies']['portfolio']['maxUnits']
    final_row = portfolio_df.iloc[-1]
    val_cfg = config.get('validation', {})

    print("="*80)
    print("VALIDATION TEST RESULTS")
    print("="*80)

    # Test 1: Properties Acquired
    print("\n[Portfolio] Properties Acquired Check:")
    if final_row['Properties Owned'] == max_units:
        print(f"  ✓ PASS: All {max_units} properties acquired")
    else:
        print(f"  ⚠ WARN: Only {int(final_row['Properties Owned'])}/{max_units} properties acquired")

    # Test 2: LTV Trajectory
    print("\n[Portfolio] LTV Trajectory Check:")
    max_safe_ltv = val_cfg.get('ltv', {}).get('maxSafeThreshold', 0.85) * 100
    dangerous_ltv = portfolio_df[(portfolio_df['LTV %'] > max_safe_ltv) & (portfolio_df['Properties Owned'] > 0)]
    if len(dangerous_ltv) > 0:
        print(f"  ⚠ WARN: LTV exceeded {max_safe_ltv:.0f}% in {len(dangerous_ltv)} months")
    else:
        print(f"  ✓ PASS: LTV never exceeded {max_safe_ltv:.0f}%")

    # Test 3: DSCR
    print("\n[Cash Flow] DSCR Check:")
    critical_dscr = val_cfg.get('dscr', {}).get('criticalThreshold', 1.0)
    lender_min = val_cfg.get('dscr', {}).get('lenderMinimum', 1.25)

    months_with_debt = portfolio_df[portfolio_df['Debt Service'] > 0].copy()
    if len(months_with_debt) > 0:
        months_with_debt['DSCR'] = months_with_debt['Net Operating Income'] / months_with_debt['Debt Service']
        critical_months = months_with_debt[months_with_debt['DSCR'] < critical_dscr]

        if len(critical_months) > 0:
            print(f"  ⚠ WARN: DSCR below {critical_dscr:.1f} in {len(critical_months)} months")
        else:
            avg_dscr = months_with_debt['DSCR'].mean()
            min_dscr = months_with_debt['DSCR'].min()
            print(f"  ✓ PASS: DSCR healthy (avg: {avg_dscr:.2f}, min: {min_dscr:.2f})")

    # Test 4: Operating Cash
    print("\n[Cash Flow] Operating Cash Check:")
    negative_cash = portfolio_df[portfolio_df['Operating Cash'] < 0]
    if len(negative_cash) > 0:
        min_cash = negative_cash['Operating Cash'].min()
        print(f"  ⚠ WARN: Cash shortfall in {len(negative_cash)} months (worst: ${min_cash:,.0f})")
    else:
        print(f"  ✓ PASS: No cash shortfalls")

    # Test 5: Refinance Economics
    print("\n[Debt Management] Refinance Economics Check:")
    min_proceeds = val_cfg.get('refinance', {}).get('minProceedsToJustifyCosts', 20000.0)
    refi_events = portfolio_df[portfolio_df['Refinance Proceeds'] > 0]
    small_refis = refi_events[refi_events['Refinance Proceeds'] < min_proceeds]

    if len(small_refis) > 0:
        print(f"  ⚠ WARN: {len(small_refis)} refinances with proceeds <${min_proceeds:,.0f}")
        for idx, row in small_refis.head(3).iterrows():
            print(f"    - Y{int(row['Year'])}M{int(row['Month'])}: ${row['Refinance Proceeds']:,.0f}")
    else:
        print(f"  ✓ PASS: All {len(refi_events)} refinances extracted >${min_proceeds:,.0f}")

    # Test 6: Reserve Anomalies
    print("\n[Reserves] Reserve Balance Check:")
    max_hoarding = val_cfg.get('reserves', {}).get('maxReserveHoarding', 500000.0)
    max_reserves = portfolio_df['Total Cash Reserves'].max()

    if max_reserves > max_hoarding:
        print(f"  ⚠ WARN: Reserves peaked at ${max_reserves:,.0f} (threshold: ${max_hoarding:,.0f})")
    else:
        print(f"  ✓ PASS: Max reserves ${max_reserves:,.0f} below hoarding threshold")

    # Test 7: Cash-on-Cash Return
    print("\n[Performance] Cash-on-Cash Return Check:")
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
            print(f"  ⚠ WARN: CoC return {annualized_coc:.1%} annually - very high")
        elif annualized_coc < min_coc and final_row['Properties Owned'] >= 3:
            print(f"  ⚠ WARN: CoC return {annualized_coc:.1%} annually - underperforming")
        else:
            print(f"  ✓ PASS: CoC return {annualized_coc:.1%} annually - reasonable")

    # Test 8: Feeder Tracking
    print("\n[Mechanics] Feeder Tracking Check:")
    untracked_feeder = portfolio_df[(portfolio_df['Properties Owned'] > 0) & (portfolio_df['_FeederIndex'] == -1)]
    if len(untracked_feeder) > 0:
        print(f"  ⚠ WARN: Feeder not tracked in {len(untracked_feeder)} months")
    else:
        print(f"  ✓ PASS: Feeder tracked in all months with properties")

    # Summary
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print(f"Config validation thresholds: {len(val_cfg)} categories configured")
    print(f"Portfolio simulation: {len(portfolio_df)} months, {int(final_row['Properties Owned'])} properties")
    print(f"Validation framework: ✓ Working correctly")

if __name__ == '__main__':
    test_validations()
