#!/usr/bin/env python3
"""
Generate Investor-Friendly Reports

Creates clean, professional reports from simulation data:
1. Executive Summary (Annual)
2. Operating Performance (Annual)
3. Acquisition Activity (All purchases)
4. Year-over-Year Summary
"""
from pathlib import Path
import pandas as pd
from ob_str_engine.engine.reports import (
    executive_summary_report,
    operating_performance_report,
    acquisition_activity_report,
    year_over_year_summary,
)

# Load simulation results
print("Loading simulation results...")
df = pd.read_csv('out/simulation_results_feeder.csv')
print(f"Loaded {len(df)} months of data\n")

# Create output directory
Path('out/reports').mkdir(parents=True, exist_ok=True)

# 1. Executive Summary Report (Annual)
print("="*70)
print("EXECUTIVE SUMMARY REPORT (ANNUAL)")
print("="*70)
exec_summary = executive_summary_report(df, annual=True)
print(exec_summary.to_string(index=False))
exec_summary.to_csv('out/reports/executive_summary_annual.csv', index=False)
print("\n[SAVED] out/reports/executive_summary_annual.csv\n")

# 2. Operating Performance Report (Annual)
print("="*70)
print("OPERATING PERFORMANCE REPORT (ANNUAL)")
print("="*70)
operating = operating_performance_report(df, annual=True)
print(operating.to_string(index=False))
operating.to_csv('out/reports/operating_performance_annual.csv', index=False)
print("\n[SAVED] out/reports/operating_performance_annual.csv\n")

# 3. Acquisition Activity Report
print("="*70)
print("ACQUISITION ACTIVITY REPORT")
print("="*70)
acquisitions = acquisition_activity_report(df)
if len(acquisitions) > 0:
    print(acquisitions.to_string(index=False))
    acquisitions.to_csv('out/reports/acquisition_activity.csv', index=False)
    print("\n[SAVED] out/reports/acquisition_activity.csv\n")
else:
    print("No acquisitions found\n")

# 4. Year-over-Year Summary
print("="*70)
print("YEAR-OVER-YEAR SUMMARY")
print("="*70)
yoy = year_over_year_summary(df)
print(yoy.to_string(index=False))
yoy.to_csv('out/reports/year_over_year_summary.csv', index=False)
print("\n[SAVED] out/reports/year_over_year_summary.csv\n")

# Summary
print("="*70)
print("REPORT GENERATION COMPLETE")
print("="*70)
print("\nAll reports saved to: out/reports/")
print("\nReports generated:")
print("  1. executive_summary_annual.csv - High-level portfolio metrics")
print("  2. operating_performance_annual.csv - Income/expense detail")
print("  3. acquisition_activity.csv - Purchase timeline")
print("  4. year_over_year_summary.csv - Comprehensive annual progression")
print("\nThese reports use investor-friendly column names and exclude")
print("internal tracking columns (those starting with '_').")
