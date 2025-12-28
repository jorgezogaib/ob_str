"""
Analyze distribution results from simulation
"""
import pandas as pd

df = pd.read_csv('out/simulation_results_feeder.csv')

print('='*80)
print('DISTRIBUTION ANALYSIS')
print('='*80)
print()

# Check if distributions occurred
total_dist = df['Distribution Amount'].sum()
dist_months = (df['Distribution Amount'] > 0).sum()

print(f'Total Distributions (30 years): ${total_dist:,.0f}')
print(f'Distribution Months: {dist_months}')
print()

# Find first distribution
first_dist = df[df['Distribution Amount'] > 0]

if len(first_dist) > 0:
    first_row = first_dist.iloc[0]
    print('='*80)
    print('FIRST DISTRIBUTION')
    print('='*80)
    print(f'Year: {int(first_row["Year"])}')
    print(f'Month: {int(first_row["Month"])}')
    print(f'Amount: ${first_row["Distribution Amount"]:,.0f}')
    print(f'Portfolio LTV: {first_row["LTV %"]:,.1f}%')
    print(f'Properties Owned: {int(first_row["Properties Owned"])}')
    print(f'Operating Cash: ${first_row["Operating Cash"]:,.0f}')
    print(f'Distributable Cash: ${first_row["Distributable Cash Flow"]:,.0f}')
    print()

    # Annual summary
    print('='*80)
    print('ANNUAL DISTRIBUTION SUMMARY')
    print('='*80)
    annual = df[df['Distribution Amount'] > 0].groupby('Year').agg({
        'Distribution Amount': 'sum'
    }).reset_index()

    for _, row in annual.iterrows():
        year = int(row['Year'])
        amount = row['Distribution Amount']
        monthly_avg = amount / 12
        print(f'Year {year:2d}: ${amount:>10,.0f} total  (${monthly_avg:>8,.0f}/month)')

    print()

    # Final stats
    last_dist = first_dist.iloc[-1]
    print('='*80)
    print('FINAL STATE (Year 30)')
    print('='*80)
    print(f'Total Equity: ${last_dist["Total Equity"]:,.0f}')
    print(f'Operating Cash: ${last_dist["Operating Cash"]:,.0f}')
    print(f'Emergency Reserve: ${last_dist["Emergency Reserve"]:,.0f}')
    print(f'Growth Savings: ${last_dist["Growth Savings"]:,.0f}')
    total_value = last_dist["Total Equity"] + last_dist["Operating Cash"] + last_dist["Emergency Reserve"] + last_dist["Growth Savings"]
    print(f'Total Value: ${total_value:,.0f}')
    print()

else:
    print('❌ NO DISTRIBUTIONS OCCURRED')
    print()
    print('Checking eligibility:')
    print(df[['Year', 'Month', 'Distribution Enabled', 'Distribution Eligible', 'Distribution Reason']].head(300).tail(20))
