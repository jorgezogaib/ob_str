#!/usr/bin/env python3
"""
Test Cash Flow Waterfall Reports

Demonstrates portfolio-level and per-unit cash flow waterfalls.
Shows sequential cash movements from income through expenses to ending cash.
"""
from pathlib import Path
from ob_str_engine.engine.simulator import simulate
from ob_str_engine.engine.reports import (
    cash_flow_waterfall,
    unit_cash_flow_waterfall,
)

# Run simulation
print("Running simulation...")
result = simulate(Path('ob_str_engine/OB_STR_ENGINE_V2_3.json'), years=30)
df = result.monthly
unit_df = result.units

print(f"Loaded {len(df)} months and {len(unit_df)} unit-month records\n")

# Test portfolio waterfall for key moments
test_cases = [
    (5, 4, "First property acquisition month"),
    (5, 12, "First year-end with property"),
    (15, 12, "Peak acquisition (7 properties)"),
    (22, 12, "All properties paid off"),
]

for year, month, description in test_cases:
    print("="*70)
    print(f"PORTFOLIO CASH FLOW WATERFALL - Year {year}, Month {month}")
    print(f"({description})")
    print("="*70)

    waterfall = cash_flow_waterfall(df, year, month)

    # Format for display
    print(f"{'Category':<35} {'Amount':>15} {'Running Balance':>15}")
    print("-"*70)
    for _, row in waterfall.iterrows():
        category = row['Category']
        amount = row['Amount']
        balance = row['Running_Balance']

        # Format with appropriate signs
        if category.startswith('='):
            print(f"{category:<35} {amount:>15,.2f} {balance:>15,.2f}")
            print("-"*70)
        elif category.startswith('+'):
            print(f"{category:<35} +{amount:>14,.2f} {balance:>15,.2f}")
        elif category.startswith('-'):
            print(f"{category:<35} {amount:>15,.2f} {balance:>15,.2f}")
        else:
            print(f"{category:<35} {amount:>15,.2f} {balance:>15,.2f}")

    print("\n")

# Test unit-level waterfalls
print("\n")
print("="*70)
print("PER-UNIT CASH FLOW WATERFALLS - Year 15 (All 7 Properties)")
print("="*70)

year = 15
month = 12

# Get all units in year 15
units_in_year = unit_df[(unit_df['Year'] == year) & (unit_df['Month'] == month)]['Unit_ID'].unique()

for unit_id in sorted(units_in_year):
    print(f"\n--- Unit {unit_id} (Property ID: {unit_id}) ---")

    unit_waterfall = unit_cash_flow_waterfall(unit_df, unit_id, year, month)

    if len(unit_waterfall) == 0:
        print("No data available")
        continue

    print(f"{'Category':<30} {'Amount':>15}")
    print("-"*45)
    for _, row in unit_waterfall.iterrows():
        category = row['Category']
        amount = row['Amount']

        if category.startswith('='):
            print(f"{category:<30} {amount:>15,.2f}")
            print("-"*45)
        elif '- ' in category:
            print(f"{category:<30} {amount:>15,.2f}")
        else:
            print(f"{category:<30} {amount:>15,.2f}")

# Summary Statistics
print("\n\n")
print("="*70)
print("UNIT INCOME/EXPENSE SUMMARY - Year 15")
print("="*70)

year15_units = unit_df[(unit_df['Year'] == 15) & (unit_df['Month'] == 12)]
if len(year15_units) > 0:
    summary_cols = ['Unit_ID', 'Unit_Rental_Income', 'Unit_NOI', 'Unit_Debt_Service', 'Unit_Operating_CF']
    summary = year15_units[summary_cols].sort_values('Unit_ID')
    print(summary.to_string(index=False))

    print(f"\nTotal Portfolio:")
    print(f"  Total Rental Income: ${summary['Unit_Rental_Income'].sum():,.2f}")
    print(f"  Total NOI:           ${summary['Unit_NOI'].sum():,.2f}")
    print(f"  Total Debt Service:  ${summary['Unit_Debt_Service'].sum():,.2f}")
    print(f"  Total Operating CF:  ${summary['Unit_Operating_CF'].sum():,.2f}")

print("\n")
print("="*70)
print("WATERFALL REPORT TESTING COMPLETE")
print("="*70)
print("\nWaterfall reports demonstrate:")
print("  1. Portfolio-level cash flow sequencing")
print("  2. Per-property income and expense allocation")
print("  3. Individual property profitability")
print("  4. Cash movement tracking from start to end")
