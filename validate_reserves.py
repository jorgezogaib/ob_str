import pandas as pd

df = pd.read_csv('out/simulation_results_feeder.csv')

# Analyze Year 30 to validate calculations
y30 = df[df['Year'] == 30].iloc[-1]

print('=== YEAR 30 RESERVE CALCULATION VALIDATION ===')
print()
print('FIXED MONTHLY COSTS BREAKDOWN:')
print(f'  HOA Total:        ${y30["HOA_Monthly_Total"]:>12,.2f}')
print(f'  Insurance:        ${y30["Insurance"]:>12,.2f}')
print(f'  Property Tax:     ${y30["Tax"]:>12,.2f}')
print(f'  Debt Service:     ${y30["DebtService_Total"]:>12,.2f}')
print(f'  -------------------------------------------')
total_fixed = y30['HOA_Monthly_Total'] + y30['Insurance'] + y30['Tax'] + y30['DebtService_Total']
print(f'  TOTAL FIXED:      ${total_fixed:>12,.2f}')
print()

print('RAINY-DAY RESERVE VALIDATION:')
print(f'  Target (6 months): ${y30["RainyTarget"]:>12,.2f}')
print(f'  Calculated:        ${total_fixed * 6:>12,.2f}')
match = 'YES' if abs(y30["RainyTarget"] - total_fixed * 6) < 1 else 'NO'
print(f'  Match?             {match}')
print()
print(f'  Actual Balance:    ${y30["RainyBalance"]:>12,.2f}')
print(f'  Excess over target:${y30["RainyBalance"] - y30["RainyTarget"]:>12,.2f} ({(y30["RainyBalance"] / y30["RainyTarget"] - 1) * 100:.1f}%)')
print()

# Check if capex calculation is reasonable
print('CAPEX RESERVE VALIDATION:')
print(f'  Monthly Capex Ops:  ${y30["CapexOps"]:>12,.2f}')
print(f'  Gross Income:       ${y30["GrossIncome"]:>12,.2f}')
print(f'  Capex % of Gross:   {y30["CapexOps"] / y30["GrossIncome"] * 100:>13,.1f}%')
print(f'  Expected (10%):     {10.0:>13,.1f}%')
match = 'YES' if abs(y30["CapexOps"] / y30["GrossIncome"] - 0.10) < 0.001 else 'NO'
print(f'  Match?              {match}')
print()

# Calculate reasonable capex ceiling
capex_monthly_rate = y30['CapexOps']
print(f'CAPEX CEILING ANALYSIS:')
print(f'  Current monthly capex: ${capex_monthly_rate:,.2f}')
print()
print(f'  Suggested ceilings by target months:')
for months in [6, 12, 18, 24]:
    ceiling = total_fixed * months
    print(f'    {months:2d} months fixed costs: ${ceiling:>12,.2f}')
print()
print(f'  Actual Capex Balance:  ${y30["CapexBalance"]:>12,.2f}')
print(f'  If 6-month ceiling:    ${total_fixed * 6:>12,.2f}')
print(f'  Excess to sweep:       ${y30["CapexBalance"] - total_fixed * 6:>12,.2f}')
print()

# Validate over multiple years to ensure calculation stays correct
print('HISTORICAL VALIDATION (Sample Years):')
print()
print('Year | Units | Fixed/Mo | Rainy Target | Rainy Actual | Target Calc OK?')
print('-----|-------|----------|--------------|--------------|----------------')
for year in [5, 10, 15, 20, 25, 30]:
    year_data = df[df['Year'] == year].iloc[-1]
    fixed_calc = year_data['HOA_Monthly_Total'] + year_data['Insurance'] + year_data['Tax'] + year_data['DebtService_Total']
    target_calc = fixed_calc * 6
    target_actual = year_data['RainyTarget']
    match = 'YES' if abs(target_calc - target_actual) < 1 else 'NO'
    print(f'{year:4d} |   {int(year_data["Units"]):>3d} | ${fixed_calc:>8,.0f} | ${target_actual:>11,.0f} | ${year_data["RainyBalance"]:>11,.0f} | {match}')

print()
print('=== CAPEX RESERVE: IS IT BEING USED? ===')
print()
# Check if capex balance ever decreases (spending)
capex_deltas = df['CapexBalance'].diff()
capex_spending = capex_deltas[capex_deltas < 0]

if len(capex_spending) == 0:
    print('FINDING: Capex reserve NEVER decreases (no spending simulated)')
    print('  - Balance only increases month-over-month')
    print('  - 10% of gross revenue accumulates indefinitely')
    print('  - No major repair/replacement events modeled')
else:
    print(f'FINDING: Capex was spent {len(capex_spending)} times')
    print(f'  Total spent: ${-capex_spending.sum():,.2f}')

print()
print('=== RAINY-DAY RESERVE: IS IT BEING USED? ===')
print()
# Check if rainy reserve ever decreases below target (emergency use)
rainy_below_target = df[df['RainyBalance'] < df['RainyTarget']]

if len(rainy_below_target) == 0:
    print('FINDING: Rainy reserve NEVER falls below target')
    print('  - Always maintained at or above 6-month cushion')
    print('  - No emergency situations that drew it down')
    print('  - Excess accumulation not redeployed')
else:
    print(f'FINDING: Rainy reserve fell below target {len(rainy_below_target)} times')
    for idx, row in rainy_below_target.iterrows():
        shortfall = row['RainyTarget'] - row['RainyBalance']
        print(f'  Year {int(row["Year"])}, Month {int(row["Month"])}: ${shortfall:,.2f} shortfall')

print()
print('=== RESERVE ADEQUACY ASSESSMENT ===')
print()

# Year 30 analysis
print('Year 30 Scenario Test:')
print(f'  Fixed costs per month:     ${total_fixed:,.2f}')
print(f'  Rainy reserve target (6mo):${y30["RainyTarget"]:,.2f}')
print(f'  Actual rainy reserve:      ${y30["RainyBalance"]:,.2f}')
print()
print('What if all 7 properties had ZERO revenue for 6 months?')
print(f'  Needed from reserves:      ${total_fixed * 6:,.2f}')
print(f'  Available (rainy target):  ${y30["RainyTarget"]:,.2f}')
print(f'  Surplus beyond need:       ${y30["RainyBalance"] - total_fixed * 6:,.2f}')
print()

months_covered = y30["RainyBalance"] / total_fixed
print(f'Months of fixed costs covered: {months_covered:.1f} months')
print(f'Target months:                  6.0 months')
print(f'Excess coverage:                {months_covered - 6:.1f} months')
