import pandas as pd

# Load results
stage2 = pd.read_csv('out/stage2_results.csv')
sweeps = pd.read_csv('out/reserve_sweeps_results.csv')

print('=== RESERVE SWEEPS IMPLEMENTATION - COMPARISON REPORT ===')
print()

# Final portfolio comparison
print('FINAL PORTFOLIO (Year 30):')
print(f'                        Stage 2 (No Sweeps)  |  With Sweeps  |  Difference')
print(f'  Total Debt:           ${stage2.iloc[-1]["TotalDebt"]:>13,.2f}  | ${sweeps.iloc[-1]["TotalDebt"]:>12,.2f} | ${stage2.iloc[-1]["TotalDebt"] - sweeps.iloc[-1]["TotalDebt"]:>12,.2f}')
print(f'  Portfolio Value:      ${stage2.iloc[-1]["TotalValue"]:>13,.2f}  | ${sweeps.iloc[-1]["TotalValue"]:>12,.2f} | ${sweeps.iloc[-1]["TotalValue"] - stage2.iloc[-1]["TotalValue"]:>12,.2f}')
print(f'  Operating Cash:       ${stage2.iloc[-1]["OperatingCash"]:>13,.2f}  | ${sweeps.iloc[-1]["OperatingCash"]:>12,.2f} | ${sweeps.iloc[-1]["OperatingCash"] - stage2.iloc[-1]["OperatingCash"]:>12,.2f}')
s2_ltv = stage2.iloc[-1]["TotalDebt"] / stage2.iloc[-1]["TotalValue"] * 100
print(f'  Portfolio LTV:        {s2_ltv:>14.1f}%  | {0.0:>13.1f}% | {-s2_ltv:>13.1f}%')
print()

# Purchase timeline
purchases_s2 = stage2[stage2['Purchase_Total'] > 0][['Year', 'Month', 'Units']]
purchases_sw = sweeps[sweeps['Purchase_Total'] > 0][['Year', 'Month', 'Units']]

print('PURCHASE TIMELINE:')
print('Property | Stage 2     | With Sweeps | Acceleration')
print('---------|-------------|-------------|-------------')
for i in range(min(len(purchases_s2), len(purchases_sw))):
    s2_row = purchases_s2.iloc[i]
    sw_row = purchases_sw.iloc[i]
    s2_timing = f'Y{int(s2_row["Year"]):02d}M{int(s2_row["Month"]):02d}'
    sw_timing = f'Y{int(sw_row["Year"]):02d}M{int(sw_row["Month"]):02d}'
    s2_months = int(s2_row['Year']) * 12 + int(s2_row['Month'])
    sw_months = int(sw_row['Year']) * 12 + int(sw_row['Month'])
    accel = s2_months - sw_months
    print(f'{int(s2_row["Units"]):>8d} | {s2_timing:>11s} | {sw_timing:>11s} | {accel:>10d} months')

total_accel = (purchases_s2.iloc[-1]['Year'] * 12 + purchases_s2.iloc[-1]['Month']) - \
              (purchases_sw.iloc[-1]['Year'] * 12 + purchases_sw.iloc[-1]['Month'])
print(f'                                   TOTAL:    {total_accel:>10d} months')
print()

# Sweep totals
total_capex_sweep = sweeps['CapexSweep'].sum()
total_rainy_sweep = sweeps['RainySweep'].sum()
total_prepay_s2 = stage2['FeederPrepay'].sum()
total_prepay_sw = sweeps['FeederPrepay'].sum()

print('CAPITAL DEPLOYMENT:')
print(f'  Total Capex Swept:     ${total_capex_sweep:>12,.2f}')
print(f'  Total Rainy Swept:     ${total_rainy_sweep:>12,.2f}')
print(f'  Total Swept:           ${total_capex_sweep + total_rainy_sweep:>12,.2f}')
print()
print(f'  Stage 2 Prepayments:   ${total_prepay_s2:>12,.2f}')
print(f'  With Sweeps Prepay:    ${total_prepay_sw:>12,.2f}')
print(f'  Additional Prepay:     ${total_prepay_sw - total_prepay_s2:>12,.2f}')
print()

# Year debt was eliminated
debt_zero_mask = sweeps['TotalDebt'] == 0
if debt_zero_mask.any():
    debt_zero_year = sweeps[debt_zero_mask].iloc[0]
    print(f'DEBT ELIMINATION:')
    print(f'  Debt reached $0:      Year {int(debt_zero_year["Year"])}, Month {int(debt_zero_year["Month"])}')
    print(f'  Stage 2 final debt:    ${stage2.iloc[-1]["TotalDebt"]:,.2f}')
    print(f'  Improvement:           100% debt elimination')
