"""
Analyze portfolio performance to design optimal distribution triggers
"""
import pandas as pd
import json
import sys

# Fix Unicode encoding on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_csv('out/simulation_results_feeder.csv')

with open('ob_str_engine/OB_STR_ENGINE_V2_3.json', 'r') as f:
    config = json.load(f)

annual_savings = config['constants']['financial']['annualSavings']

print('='*80)
print('DISTRIBUTION TRIGGER ANALYSIS')
print('='*80)
print()

# Year-end snapshots
key_years = df[df['Month'] == 12].copy()
print('=== Portfolio Evolution by Year ===')
print()
print('Year | Units | Total Debt | LTV %  | NOI/Mo   | NOI/Year  | Cash Reserves | Dist CF/Mo')
print('-----|-------|------------|--------|----------|-----------|---------------|------------')
for _, row in key_years.iterrows():
    year = int(row['Year'])
    units = int(row['Properties Owned'])
    debt = row['Total Debt']
    ltv = row['LTV %']
    noi_mo = row['Net Operating Income']
    noi_yr = noi_mo * 12
    reserves = row['Total Cash Reserves']
    dist_cf = row['Distributable Cash Flow']
    print(f'{year:4d} | {units:5d} | ${debt:>10,.0f} | {ltv:5.1f}% | ${noi_mo:>8,.0f} | ${noi_yr:>9,.0f} | ${reserves:>13,.0f} | ${dist_cf:>10,.0f}')

print()
print('='*80)
print('KEY MILESTONES')
print('='*80)
print()

# Find debt-free milestone
debt_free_all = df[(df['Properties Owned'] >= 5) & (df['Total Debt'] == 0)]
if len(debt_free_all) > 0:
    debt_free = debt_free_all.iloc[0]
    print(f'🎯 DEBT-FREE MILESTONE')
    print(f'   When: Year {int(debt_free["Year"])}, Month {int(debt_free["Month"])}')
    print(f'   Properties: {int(debt_free["Properties Owned"])}')
    print(f'   NOI: ${debt_free["Net Operating Income"]:,.2f}/month = ${debt_free["Net Operating Income"]*12:,.2f}/year')
    print(f'   Reserves: ${debt_free["Total Cash Reserves"]:,.2f}')
    print(f'   Portfolio Value: ${debt_free["Total Portfolio Value"]:,.2f}')
    print()

# Find when NOI > annual savings contribution
noi_exceeds_savings = df[(df['Properties Owned'] > 0) & (df['Net Operating Income'] * 12 > annual_savings)]
if len(noi_exceeds_savings) > 0:
    milestone = noi_exceeds_savings.iloc[0]
    print(f'💰 NOI EXCEEDS SAVINGS MILESTONE')
    print(f'   When: Year {int(milestone["Year"])}, Month {int(milestone["Month"])}')
    print(f'   NOI/year: ${milestone["Net Operating Income"]*12:,.2f} > ${annual_savings:,.2f} savings')
    print(f'   Properties: {int(milestone["Properties Owned"])}')
    print(f'   LTV: {milestone["LTV %"]:.1f}%')
    print()

# Find when 3+ properties at <50% LTV
low_ltv = df[(df['Properties Owned'] >= 3) & (df['LTV %'] < 50) & (df['LTV %'] > 0)]
if len(low_ltv) > 0:
    milestone = low_ltv.iloc[0]
    print(f'🏆 LOW LEVERAGE MILESTONE (3+ properties, <50% LTV)')
    print(f'   When: Year {int(milestone["Year"])}, Month {int(milestone["Month"])}')
    print(f'   Properties: {int(milestone["Properties Owned"])}')
    print(f'   LTV: {milestone["LTV %"]:.1f}%')
    print(f'   NOI/year: ${milestone["Net Operating Income"]*12:,.2f}')
    print()

# Calculate DSCR for all months with debt
df_with_debt = df[df['Debt Service'] > 0].copy()
df_with_debt['DSCR'] = df_with_debt['Net Operating Income'] / df_with_debt['Debt Service']

# Find when DSCR > 2.0 sustained
high_dscr = df_with_debt[df_with_debt['DSCR'] > 2.0]
if len(high_dscr) > 0:
    milestone = high_dscr.iloc[0]
    print(f'📊 HIGH DSCR MILESTONE (DSCR > 2.0)')
    print(f'   When: Year {int(milestone["Year"])}, Month {int(milestone["Month"])}')
    print(f'   DSCR: {milestone["DSCR"]:.2f}')
    print(f'   Properties: {int(milestone["Properties Owned"])}')
    print(f'   LTV: {milestone["LTV %"]:.1f}%')
    print(f'   NOI: ${milestone["Net Operating Income"]:,.2f}/month')
    print()

print()
print('='*80)
print('DISTRIBUTION SCENARIOS - "STEPPING AWAY FROM JOB"')
print('='*80)
print()

# Scenario 1: Target income replacement
target_incomes = [50000, 75000, 100000, 150000, 200000]
print('When could NOI support different income levels?')
print()
print('Target Income | Year Achieved | Properties | LTV % | Monthly NOI')
print('--------------|---------------|------------|-------|-------------')
for target in target_incomes:
    achieves = df[(df['Net Operating Income'] * 12 >= target)]
    if len(achieves) > 0:
        m = achieves.iloc[0]
        print(f'${target:>12,} | Year {int(m["Year"]):>8} | {int(m["Properties Owned"]):>10} | {m["LTV %"]:>5.1f}% | ${m["Net Operating Income"]:>11,.0f}')
    else:
        print(f'${target:>12,} | Never achieved')

print()
print('='*80)
print('RECOMMENDED DISTRIBUTION TRIGGER OPTIONS')
print('='*80)
print()

print('OPTION 1: DUAL-TRIGGER (Conservative)')
print('  - Debt-free (LTV = 0%) AND')
print('  - Minimum reserve cushion ($500k)')
print('  - Distribute: 80% of monthly NOI')
print('  - Rationale: Maximum safety, guaranteed income')
print()

print('OPTION 2: LTV-BASED (Balanced)')
print('  - Portfolio LTV < 25% AND')
print('  - Minimum 3 properties AND')
print('  - Minimum reserve cushion ($250k)')
print('  - Distribute: 70% of monthly NOI')
print('  - Rationale: Maintain some leverage for flexibility')
print()

print('OPTION 3: INCOME-BASED (Aggressive)')
print('  - Annual NOI >= target income (e.g., $100k) AND')
print('  - DSCR > 2.0 (if debt exists) AND')
print('  - Minimum reserve cushion ($100k)')
print('  - Distribute: 60% of monthly NOI')
print('  - Rationale: Earliest possible financial freedom')
print()

print('OPTION 4: HYBRID (Recommended)')
print('  - (LTV < 30% OR debt-free) AND')
print('  - Annual NOI >= target income AND')
print('  - Reserve cushion >= max(12 months fixed costs, $200k)')
print('  - Distribute: 75% of (monthly NOI - reserve top-up needed)')
print('  - Rationale: Balances safety, timing, and flexibility')
print()

# Calculate Option 4 example
print('OPTION 4 SIMULATION:')
for target_income in [75000, 100000, 150000]:
    eligible = df[
        ((df['LTV %'] < 30) | (df['Total Debt'] == 0)) &
        (df['Net Operating Income'] * 12 >= target_income) &
        (df['Total Cash Reserves'] >= 200000)
    ]
    if len(eligible) > 0:
        first = eligible.iloc[0]
        monthly_dist = first['Net Operating Income'] * 0.75
        annual_dist = monthly_dist * 12
        print(f"  Target ${target_income:,}/year:")
        print(f"    Achievable: Year {int(first['Year'])}, Month {int(first['Month'])}")
        print(f"    Distribution: ${monthly_dist:,.0f}/month = ${annual_dist:,.0f}/year")
        print(f"    Properties: {int(first['Properties Owned'])}, LTV: {first['LTV %']:.1f}%")
        print()
