"""
Analyze distribution results from simulation
"""
import pandas as pd
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_csv('out/simulation_results_feeder.csv')

print('='*80)
print('DISTRIBUTION ANALYSIS')
print('='*80)
print()

# When did distributions start?
distributions = df[df['Distribution Amount'] > 0]

if len(distributions) == 0:
    print('❌ NO DISTRIBUTIONS PAID')
    print()
    print('Checking eligibility status:')
    enabled = df[df['Distribution Enabled'] == 1]
    eligible = df[df['Distribution Eligible'] == 1]
    safe = df[df['Distribution Safe'] == 1]

    print(f'  Months enabled: {len(enabled)}')
    print(f'  Months eligible: {len(eligible)}')
    print(f'  Months safe: {len(safe)}')
    print()

    # Show last reason
    last_reason = df.iloc[-1]['Distribution Reason']
    print(f'Last month reason: {last_reason}')

else:
    first_dist = distributions.iloc[0]
    last_dist = distributions.iloc[-1]

    print(f'✓ DISTRIBUTIONS STARTED')
    print(f'  First distribution: Year {int(first_dist["Year"])}, Month {int(first_dist["Month"])}')
    print(f'  Amount: ${first_dist["Distribution Amount"]:,.2f}')
    print(f'  Portfolio LTV at start: {first_dist["LTV %"]:.1f}%')
    print(f'  Properties owned: {int(first_dist["Properties Owned"])}')
    print(f'  Monthly NOI: ${first_dist["Net Operating Income"]:,.2f}')
    print(f'  Annual NOI: ${first_dist["Net Operating Income"] * 12:,.2f}')
    print()

    # Distribution summary
    total_distributed = distributions['Distribution Amount'].sum()
    months_distributed = len(distributions)
    avg_monthly_dist = distributions['Distribution Amount'].mean()
    max_monthly_dist = distributions['Distribution Amount'].max()
    min_monthly_dist = distributions['Distribution Amount'].min()

    print(f'DISTRIBUTION SUMMARY')
    print(f'  Total distributed: ${total_distributed:,.2f}')
    print(f'  Months with distributions: {months_distributed}')
    print(f'  Average monthly: ${avg_monthly_dist:,.2f}')
    print(f'  Min monthly: ${min_monthly_dist:,.2f}')
    print(f'  Max monthly: ${max_monthly_dist:,.2f}')
    print()

    # Distribution by year
    print('ANNUAL DISTRIBUTIONS')
    print()
    print('Year | Months Paid | Total Distributed | Avg Monthly | NOI Coverage')
    print('-----|-------------|-------------------|-------------|-------------')

    for year in range(1, 31):
        year_data = df[df['Year'] == year]
        year_dists = year_data[year_data['Distribution Amount'] > 0]

        if len(year_dists) > 0:
            total_year = year_dists['Distribution Amount'].sum()
            months_paid = len(year_dists)
            avg_mo = total_year / months_paid
            avg_noi = year_data['Net Operating Income'].mean()
            coverage_pct = (avg_mo / avg_noi * 100) if avg_noi > 0 else 0

            print(f'{year:4d} | {months_paid:>11d} | ${total_year:>16,.0f} | ${avg_mo:>10,.0f} | {coverage_pct:>10.1f}%')

    print()

    # Impact on cash reserves
    no_dist_last_row = df.iloc[-1]
    final_reserves_with_dist = no_dist_last_row['Total Cash Reserves']

    # Compare to baseline (no distributions)
    # We'd need to run baseline separately, but we can estimate
    cumulative_dist = df['Distribution Amount'].cumsum()
    final_cumulative = cumulative_dist.iloc[-1]

    print(f'IMPACT ON PORTFOLIO')
    print(f'  Final reserves (with distributions): ${final_reserves_with_dist:,.2f}')
    print(f'  Total distributed over 30 years: ${final_cumulative:,.2f}')
    print(f'  Estimated reserves without distributions: ${final_reserves_with_dist + final_cumulative:,.2f}')
    print()

    # Cash-on-cash return including distributions
    initial_contribution = 5000
    annual_savings = 50000
    years = 30
    total_contributed = initial_contribution + (annual_savings * years)

    total_distributions_received = df['Distribution Amount'].sum()
    final_equity = df.iloc[-1]['Total Equity']
    final_cash = df.iloc[-1]['Total Cash Reserves']

    total_value = final_equity + total_distributions_received
    total_return = total_value - total_contributed
    annualized_return = (total_value / total_contributed) ** (1/years) - 1

    print(f'INVESTOR RETURN ANALYSIS')
    print(f'  Total contributed (30 years): ${total_contributed:,.2f}')
    print(f'  Final equity: ${final_equity:,.2f}')
    print(f'  Total distributions received: ${total_distributions_received:,.2f}')
    print(f'  Total value created: ${total_value:,.2f}')
    print(f'  Total return: ${total_return:,.2f}')
    print(f'  Multiple on invested capital: {total_value / total_contributed:.2f}x')
    print(f'  Annualized return (IRR approx): {annualized_return:.1%}')
    print()

    # Compare distribution starting conditions to config
    print(f'STARTING CONDITIONS vs CONFIG TRIGGERS')
    print(f'  Annual NOI required: $100,000')
    print(f'  Annual NOI at start: ${first_dist["Net Operating Income"] * 12:,.2f}')
    print(f'  Max LTV allowed: 30.0%')
    print(f'  Actual LTV at start: {first_dist["LTV %"]:.1f}%')
    print(f'  Min properties required: 3')
    print(f'  Properties at start: {int(first_dist["Properties Owned"])}')
    print(f'  Min reserves required: $200,000')
    print(f'  Reserves at start: ${first_dist["Total Cash Reserves"]:,.2f}')
    print()

    # Monthly income breakdown during distribution phase
    dist_years = distributions.groupby('Year').agg({
        'Net Operating Income': 'mean',
        'Distribution Amount': 'mean',
        'Operating Cash': 'mean'
    })

    print('MONTHLY INCOME DURING DISTRIBUTION PHASE')
    print()
    print('Year |  Avg NOI  | Avg Distribution | Retention Rate | Operating Cash')
    print('-----|-----------|------------------|----------------|---------------')
    for year, row in dist_years.iterrows():
        retention = (row['Net Operating Income'] - row['Distribution Amount']) / row['Net Operating Income'] if row['Net Operating Income'] > 0 else 0
        print(f'{int(year):4d} | ${row["Net Operating Income"]:>8,.0f} | ${row["Distribution Amount"]:>15,.0f} | {retention:>13.1%} | ${row["Operating Cash"]:>13,.0f}')

print()
print('='*80)
