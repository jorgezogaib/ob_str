#!/usr/bin/env python3
"""
Test Unit-Level Expense Ratios and Return Metrics
"""
from pathlib import Path
from ob_str_engine.engine.simulator import simulate

# Run simulation
print("Running simulation...")
result = simulate(Path('ob_str_engine/OB_STR_ENGINE_V2_3.json'), years=30)
unit_df = result.units

print(f"\nLoaded {len(unit_df)} unit-month records\n")

# Show Year 15 metrics (peak portfolio)
year15 = unit_df[(unit_df['Year'] == 15) & (unit_df['Month'] == 12)].sort_values('Unit_ID')

print("="*120)
print("YEAR 15 UNIT PERFORMANCE METRICS (7 Properties)")
print("="*120)

# Display key columns
display_cols = [
    'Unit_ID',
    'Unit_Rental_Income',
    'Unit_Total_Expenses',
    'Unit_Expense_Ratio',
    'Unit_NOI',
    'Unit_NOI_Margin',
    'Unit_Operating_CF',
    'Unit_Cash_Invested',
    'Unit_Cash_On_Cash_Return',
    'Unit_Cap_Rate',
    'Unit_DSCR',
    'Unit_ROI'
]

print(year15[display_cols].to_string(index=False))

print("\n" + "="*120)
print("EXPENSE RATIO BREAKDOWN")
print("="*120)

expense_cols = [
    'Unit_ID',
    'Unit_Rental_Income',
    'Unit_Mgmt_Fee_Ratio',
    'Unit_CapEx_Ratio',
    'Unit_Expense_Ratio',
    'Unit_NOI_Margin'
]

print(year15[expense_cols].to_string(index=False))

print("\n" + "="*120)
print("RETURN METRICS SUMMARY")
print("="*120)

return_cols = [
    'Unit_ID',
    'Unit_Cash_Invested',
    'Unit_Equity',
    'Unit_Cash_On_Cash_Return',
    'Unit_Cap_Rate',
    'Unit_ROI'
]

print(year15[return_cols].to_string(index=False))

# Portfolio averages
print("\n" + "="*120)
print("PORTFOLIO AVERAGES (Year 15)")
print("="*120)
print(f"Average Expense Ratio:     {year15['Unit_Expense_Ratio'].mean():.2f}%")
print(f"Average NOI Margin:        {year15['Unit_NOI_Margin'].mean():.2f}%")
print(f"Average Cash-on-Cash:      {year15['Unit_Cash_On_Cash_Return'].mean():.2f}%")
print(f"Average Cap Rate:          {year15['Unit_Cap_Rate'].mean():.2f}%")
print(f"Average DSCR:              {year15['Unit_DSCR'].mean():.2f}")
print(f"Average ROI:               {year15['Unit_ROI'].mean():.2f}%")

# Rankings
print("\n" + "="*120)
print("PROPERTY RANKINGS (by Cash-on-Cash Return)")
print("="*120)

rankings = year15[['Unit_ID', 'Unit_Cash_On_Cash_Return', 'Unit_Operating_CF', 'Unit_NOI_Margin']].sort_values(
    'Unit_Cash_On_Cash_Return', ascending=False
)
rankings['Rank'] = range(1, len(rankings) + 1)
print(rankings[['Rank', 'Unit_ID', 'Unit_Cash_On_Cash_Return', 'Unit_Operating_CF', 'Unit_NOI_Margin']].to_string(index=False))

print("\n" + "="*120)
print("AVAILABLE COLUMNS IN UNIT DATAFRAME")
print("="*120)
print(f"Total columns: {len(unit_df.columns)}")
print("\nAll columns:")
for col in unit_df.columns:
    print(f"  - {col}")
