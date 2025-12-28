import pandas as pd

# Load both datasets
stage2 = pd.read_csv('out/stage2_results.csv')
stage3 = pd.read_csv('out/stage3_results.csv')

# Final portfolio comparison
print('=== FINAL PORTFOLIO (Year 30) ===')
print(f'Stage 2 Total Debt: ${stage2.iloc[-1]["TotalDebt"]:,.2f}')
print(f'Stage 3 Total Debt: ${stage3.iloc[-1]["TotalDebt"]:,.2f}')
print(f'Difference: ${stage2.iloc[-1]["TotalDebt"] - stage3.iloc[-1]["TotalDebt"]:,.2f}')
print()
print(f'Stage 2 Portfolio Value: ${stage2.iloc[-1]["TotalValue"]:,.2f}')
print(f'Stage 3 Portfolio Value: ${stage3.iloc[-1]["TotalValue"]:,.2f}')
print(f'Difference: ${stage3.iloc[-1]["TotalValue"] - stage2.iloc[-1]["TotalValue"]:,.2f}')
print()

# Purchase timeline comparison
purchases_s2 = stage2[stage2['Purchase_Total'] > 0][['Year', 'Month', 'Units', 'RefiPropertyIndex', 'FeederDraw_Net']]
purchases_s3 = stage3[stage3['Purchase_Total'] > 0][['Year', 'Month', 'Units', 'RefiPropertyIndex', 'FeederDraw_Net']]

print('=== PURCHASE TIMELINE ===')
print('Stage 2:')
for i, row in purchases_s2.iterrows():
    print(f"  Property {int(row['Units'])}: Y{int(row['Year'])}M{int(row['Month']):02d}, Refi Property: {int(row['RefiPropertyIndex'])}")
print()
print('Stage 3:')
for i, row in purchases_s3.iterrows():
    print(f"  Property {int(row['Units'])}: Y{int(row['Year'])}M{int(row['Month']):02d}, Refi Property: {int(row['RefiPropertyIndex'])}")
print()

# Capital allocation totals
s2_prepay = stage2['FeederPrepay'].sum()
s3_prepay = stage3['FeederPrepay'].sum()
s2_savings = stage2['SavingsDeposit'].sum()
s3_savings = stage3['SavingsDeposit'].sum()

print('=== CAPITAL ALLOCATION TOTALS ===')
print(f'Stage 2 Prepayments: ${s2_prepay:,.2f}')
print(f'Stage 3 Prepayments: ${s3_prepay:,.2f}')
print(f'Difference: ${s3_prepay - s2_prepay:,.2f}')
print()
print(f'Stage 2 Savings: ${s2_savings:,.2f}')
print(f'Stage 3 Savings: ${s3_savings:,.2f}')
print(f'Difference: ${s3_savings - s2_savings:,.2f}')
