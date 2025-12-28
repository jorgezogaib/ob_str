#!/usr/bin/env python3
"""
Generate Unit-Level Reports

Creates detailed property-by-property breakdown reports from simulation data.
Shows individual unit value, debt, equity, LTV, and payment details.
"""
from pathlib import Path
import pandas as pd
from ob_str_engine.engine.simulator import simulate
from ob_str_engine.engine.reports import unit_breakdown_report

# Run simulation
print("Running 30-year simulation with Feeder Strategy...")
result = simulate(Path('ob_str_engine/OB_STR_ENGINE_V2_3.json'), years=30)

# Create output directory
Path('out/reports').mkdir(parents=True, exist_ok=True)

# Get unit data
unit_df = result.units

print(f"\nLoaded {len(unit_df)} unit-month records")
print(f"Tracking {unit_df['Unit_ID'].nunique()} properties over {unit_df['Year'].nunique()} years\n")

# 1. Full Unit Breakdown (All years, year-end snapshot)
print("="*70)
print("UNIT-LEVEL BREAKDOWN - YEAR-END SNAPSHOTS (ALL YEARS)")
print("="*70)
full_breakdown = unit_breakdown_report(unit_df)
print(full_breakdown.to_string(index=False))
full_breakdown.to_csv('out/reports/unit_breakdown_all_years.csv', index=False)
print("\n[SAVED] out/reports/unit_breakdown_all_years.csv\n")

# 2. Key year snapshots
key_years = [5, 10, 15, 20, 25, 30]
for yr in key_years:
    year_data = unit_breakdown_report(unit_df, year=yr)
    if len(year_data) > 0:
        print("="*70)
        print(f"UNIT BREAKDOWN - YEAR {yr}")
        print("="*70)
        print(year_data.to_string(index=False))
        year_data.to_csv(f'out/reports/unit_breakdown_year{yr}.csv', index=False)
        print(f"\n[SAVED] out/reports/unit_breakdown_year{yr}.csv\n")

# 3. Summary statistics by year
print("="*70)
print("UNIT-LEVEL SUMMARY STATISTICS BY YEAR")
print("="*70)
summary_stats = unit_df.groupby('Year').agg({
    'Unit_ID': 'nunique',
    'Unit_Value': 'sum',
    'Unit_Debt': 'sum',
    'Unit_Equity': 'sum',
    'Unit_Monthly_Payment': 'sum',
    'Unit_LTV': 'mean',
}).rename(columns={
    'Unit_ID': 'Properties',
    'Unit_Value': 'Total Value',
    'Unit_Debt': 'Total Debt',
    'Unit_Equity': 'Total Equity',
    'Unit_Monthly_Payment': 'Total Monthly Payment',
    'Unit_LTV': 'Avg LTV %',
}).reset_index()

# Get year-end data only
year_end_data = unit_df[unit_df['Month'] == 12].copy()
summary_stats = year_end_data.groupby('Year').agg({
    'Unit_ID': 'nunique',
    'Unit_Value': 'sum',
    'Unit_Debt': 'sum',
    'Unit_Equity': 'sum',
    'Unit_Monthly_Payment': 'sum',
    'Unit_LTV': 'mean',
}).rename(columns={
    'Unit_ID': 'Properties',
    'Unit_Value': 'Total Value',
    'Unit_Debt': 'Total Debt',
    'Unit_Equity': 'Total Equity',
    'Unit_Monthly_Payment': 'Total Monthly Payment',
    'Unit_LTV': 'Avg LTV %',
}).reset_index()

print(summary_stats.to_string(index=False))
summary_stats.to_csv('out/reports/unit_summary_statistics.csv', index=False)
print("\n[SAVED] out/reports/unit_summary_statistics.csv\n")

# 4. Feeder property tracking
print("="*70)
print("FEEDER PROPERTY TRACKING")
print("="*70)
feeder_history = unit_df[unit_df['Is_Feeder'] == True].copy()
if len(feeder_history) > 0:
    # Get feeder changes (year-end only)
    feeder_year_end = feeder_history[feeder_history['Month'] == 12]
    print(feeder_year_end[['Year', 'Unit_ID', 'Unit_Value', 'Unit_Debt', 'Unit_LTV', 'Unit_Monthly_Payment']].to_string(index=False))
    feeder_year_end.to_csv('out/reports/feeder_property_history.csv', index=False)
    print("\n[SAVED] out/reports/feeder_property_history.csv\n")
else:
    print("No feeder property tracking data found\n")

# Summary
print("="*70)
print("REPORT GENERATION COMPLETE")
print("="*70)
print("\nAll unit-level reports saved to: out/reports/")
print("\nReports generated:")
print("  1. unit_breakdown_all_years.csv - Year-end snapshot for all years")
print("  2. unit_breakdown_yearX.csv - Detailed breakdown for specific years (5, 10, 15, 20, 25, 30)")
print("  3. unit_summary_statistics.csv - Aggregate statistics by year")
print("  4. feeder_property_history.csv - Feeder property tracking over time")
print("\nThese reports show individual property-level details including:")
print("  - Unit Value, Debt, Equity, LTV%")
print("  - Monthly Payment, Interest Rate")
print("  - Feeder status and refinance history")
