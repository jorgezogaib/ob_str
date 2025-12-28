#!/usr/bin/env python3
"""
Quick simulation runner with results summary

Demonstrates the Feeder Strategy:
- Phase 1: Acquire up to 7 properties using strategic refi + savings
- Phase 2: Pay off all debt systematically, one property at a time
"""
from pathlib import Path
from ob_str_engine.engine.simulator import simulate
from ob_str_engine.engine.reports import (
    executive_summary_report,
    operating_performance_report,
    acquisition_activity_report,
    year_over_year_summary,
)
import pandas as pd

# Run simulation
print("Running 30-year simulation with Feeder Strategy...")
result = simulate(Path('ob_str_engine/OB_STR_ENGINE_V2_3.json'), years=30)
df = result.monthly

# Summary
print("\n" + "="*70)
print("SIMULATION COMPLETE - 30 YEAR PORTFOLIO ANALYSIS (FEEDER STRATEGY)")
print("="*70)

# Final state
final = df.iloc[-1]
print(f"\nFINAL PORTFOLIO (Year {int(final['Year'])}):")
print(f"  Properties Owned:      {int(final['Properties Owned'])}")
print(f"  Total Property Value:  ${final['Total Portfolio Value']:,.2f}")
print(f"  Total Debt:            ${final['Total Debt']:,.2f}")
print(f"  Total Equity:          ${final['Total Equity']:,.2f}")
print(f"  LTV:                   {final['LTV %']:.1f}%")

print(f"\nCASH ACCOUNTS:")
print(f"  Operating Cash:        ${final['Operating Cash']:,.2f}")
print(f"  Emergency Reserve:     ${final['Emergency Reserve']:,.2f}")
print(f"  Growth Savings:        ${final['Growth Savings']:,.2f}")
print(f"  Total Cash Reserves:   ${final['Total Cash Reserves']:,.2f}")

# Purchase timeline using new report
purchases = acquisition_activity_report(df)
if len(purchases) > 0:
    print(f"\nPURCHASE TIMELINE ({len(purchases)} properties):")
    display_purchases = purchases[['Year', 'Month', 'Properties Owned', 'Property Market Value',
                                     'Total Acquisition Cost', 'Refinance Proceeds', 'Growth Savings']]
    print(display_purchases.to_string(index=False))

# Refinancing events (Phase 1 only)
refis = df[df['Refinance Proceeds'] > 0][['Year', 'Month', 'Properties Owned', '_RefiPropertyIndex', 'Refinance Proceeds', 'Total Debt']]
if len(refis) > 0:
    print(f"\nREFINANCING EVENTS ({len(refis)}):")
    print(refis.to_string(index=False))
else:
    print(f"\nREFINANCING EVENTS: None")

# Feeder changes over time
print("\nFEEDER PROPERTY TRACKING:")
feeder_changes = df[df['_FeederIndex'] != df['_FeederIndex'].shift(1)][['Year', 'Month', 'Properties Owned', '_FeederIndex', '_FeederLTV']]
feeder_changes = feeder_changes[feeder_changes['_FeederIndex'] >= 0]
if len(feeder_changes) > 0:
    print(feeder_changes.to_string(index=False))

# Interest earned summary
total_cash_interest = df['Interest - Operating'].sum()
total_rainy_interest = df['Interest - Reserve'].sum()
total_savings_interest = df['Interest - Savings'].sum()
total_all_interest = df['Total Interest Earned'].sum()
print(f"\nINTEREST EARNED (30 years):")
print(f"  Operating Cash Interest:  ${total_cash_interest:,.2f}")
print(f"  Reserve Interest:         ${total_rainy_interest:,.2f}")
print(f"  Savings Interest:         ${total_savings_interest:,.2f}")
print(f"  TOTAL Interest Earned:    ${total_all_interest:,.2f}")

# Prepayment summary
total_prepay = df['Principal Prepayment'].sum()
total_savings_deposits = df['Savings Deposit'].sum()
print(f"\nCAPITAL ALLOCATION (30 years):")
print(f"  Total Principal Prepayments: ${total_prepay:,.2f}")
print(f"  Total Savings Deposits:      ${total_savings_deposits:,.2f}")

# Debt payoff tracking (Phase 2)
max_units_month = df[df['Properties Owned'] == df['Properties Owned'].max()].iloc[0]['Year'] * 12 + df[df['Properties Owned'] == df['Properties Owned'].max()].iloc[0]['Month']
phase2_df = df[(df['Year'] * 12 + df['Month']) >= max_units_month]
if len(phase2_df) > 0:
    print(f"\nPHASE 2 DEBT PAYOFF (after reaching max units):")
    print(f"  Started at Year {int(phase2_df.iloc[0]['Year'])}, Month {int(phase2_df.iloc[0]['Month'])}")
    print(f"  Starting Debt:  ${phase2_df.iloc[0]['Total Debt']:,.2f}")
    print(f"  Ending Debt:    ${phase2_df.iloc[-1]['Total Debt']:,.2f}")
    print(f"  Debt Reduced:   ${phase2_df.iloc[0]['Total Debt'] - phase2_df.iloc[-1]['Total Debt']:,.2f}")

    # Check for fully paid properties
    if phase2_df.iloc[-1]['Total Debt'] == 0:
        print(f"  Status: ALL PROPERTIES PAID OFF!")
    elif phase2_df.iloc[-1]['Total Debt'] < phase2_df.iloc[0]['Total Debt'] * 0.5:
        print(f"  Status: Over 50% of debt eliminated")

# Year-by-year summary using new report function
print("\nYEAR-BY-YEAR SUMMARY:")
yearly = year_over_year_summary(df)
print(yearly.to_string(index=False))

# Export
output_file = 'out/simulation_results_feeder.csv'
Path('out').mkdir(exist_ok=True)
try:
    df.to_csv(output_file, index=False)
    print(f"\n[OK] Full results exported to: {output_file}")
except PermissionError:
    print(f"\n[WARN] Could not write to {output_file} - file may be open in another program")
print(f"[OK] Total rows: {len(df)}")

# Validation checks
print("\n" + "="*70)
print("STRATEGY VALIDATION CHECKS")
print("="*70)

# Check 1: No refis after max units
max_units_reached = df[df['Properties Owned'] == df['Properties Owned'].max()].iloc[0]
post_max_refis = df[(df['Year'] * 12 + df['Month']) > (max_units_reached['Year'] * 12 + max_units_reached['Month'])]
post_max_refis = post_max_refis[post_max_refis['Refinance Proceeds'] > 0]
if len(post_max_refis) == 0:
    print("[PASS] No refinancing after reaching max units")
else:
    print(f"[FAIL] {len(post_max_refis)} refis after max units")

# Check 2: Feeder is tracked throughout
feeder_tracked = df[df['Properties Owned'] > 0]['_FeederIndex']
if (feeder_tracked >= 0).all():
    print("[PASS] Feeder property tracked throughout simulation")
else:
    missing = (feeder_tracked < 0).sum()
    print(f"[WARN] Feeder not tracked in {missing} months")

# Check 3: Debt decreasing in Phase 2
if len(phase2_df) > 1:
    debt_decreasing = phase2_df.iloc[-1]['Total Debt'] <= phase2_df.iloc[0]['Total Debt']
    if debt_decreasing:
        print("[PASS] Debt decreased during Phase 2 (payoff mode)")
    else:
        print("[FAIL] Debt increased during Phase 2")

# Check 4: Interest earned on all accounts
if total_cash_interest > 0 and total_rainy_interest > 0:
    print("[PASS] Interest earned on cash accounts")
else:
    print("[WARN] Some accounts not earning interest")

print("\n" + "="*70)
