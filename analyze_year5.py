import pandas as pd

# Load the data
df = pd.read_csv('out/simulation_results_feeder.csv')

# Filter Year 5
year5 = df[df['Year'] == 5]

print('Year 5 Monthly Breakdown:')
print('=' * 80)
print(year5[['Year', 'Month', 'Operating Cash Flow', 'Distributable Cash Flow', '_RainyTopup']].to_string(index=False))

print('\n\nYear 5 Totals:')
print('=' * 80)
print(f'Total Operating Cash Flow:     ${year5["Operating Cash Flow"].sum():,.2f}')
print(f'Total Distributable Cash Flow: ${year5["Distributable Cash Flow"].sum():,.2f}')
print(f'Difference:                    ${year5["Operating Cash Flow"].sum() - year5["Distributable Cash Flow"].sum():,.2f}')
print(f'\nTotal Reserve Topups:          ${year5["_RainyTopup"].sum():,.2f}')

# Check months where DCF differs from OCF
print('\n\nMonths where Distributable CF < Operating CF:')
print('=' * 80)
diff_months = year5[year5['Distributable Cash Flow'] < year5['Operating Cash Flow']]
if len(diff_months) > 0:
    print(diff_months[['Year', 'Month', 'Operating Cash Flow', 'Distributable Cash Flow', '_RainyTopup']].to_string(index=False))
    print(f'\nTotal difference in these months: ${(diff_months["Operating Cash Flow"] - diff_months["Distributable Cash Flow"]).sum():,.2f}')
