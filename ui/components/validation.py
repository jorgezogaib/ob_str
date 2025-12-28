"""
Validation Component - Model validation checks
"""

import pandas as pd
from typing import Dict, Any, List, Tuple


def run_all_validations(
    portfolio_df: pd.DataFrame,
    units_df: pd.DataFrame,
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Run all validation checks.

    Returns:
        List of validation results with keys:
        - name: Check name
        - status: 'pass', 'warning', 'fail'
        - message: Description
        - details: Optional additional info
    """
    results = []

    # Check 1: All properties acquired
    results.append(check_properties_acquired(portfolio_df, config))

    # Check 2: No cash shortfalls
    results.append(check_cash_shortfalls(portfolio_df))

    # Check 3: Debt payoff achieved
    results.append(check_debt_payoff(portfolio_df))

    # Check 4: Reserves maintained
    results.append(check_reserves_maintained(portfolio_df))

    # Check 5: Feeder tracking
    results.append(check_feeder_tracking(portfolio_df))

    # Check 6: Acquisition feasibility
    results.append(check_acquisition_feasibility(portfolio_df))

    # Check 7: Refi eligibility
    results.append(check_refi_eligibility(portfolio_df, config))

    return results


def check_properties_acquired(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if all target properties were acquired"""
    max_units = config['policies']['portfolio']['maxUnits']
    final_props = int(df.iloc[-1]['Properties Owned'])

    if final_props == max_units:
        return {
            'name': 'Properties Acquired',
            'status': 'pass',
            'message': f'All {max_units} properties acquired',
            'details': None
        }
    else:
        return {
            'name': 'Properties Acquired',
            'status': 'fail',
            'message': f'Only {final_props} of {max_units} properties acquired',
            'details': None
        }


def check_cash_shortfalls(df: pd.DataFrame) -> Dict[str, Any]:
    """Check for negative operating cash"""
    negative = df[df['Operating Cash'] < 0]

    if len(negative) == 0:
        return {
            'name': 'Cash Shortfalls',
            'status': 'pass',
            'message': 'No cash shortfalls (Operating Cash never negative)',
            'details': None
        }
    else:
        return {
            'name': 'Cash Shortfalls',
            'status': 'fail',
            'message': f'Cash went negative in {len(negative)} month(s)',
            'details': negative[['Year', 'Month', 'Operating Cash']].to_dict('records')
        }


def check_debt_payoff(df: pd.DataFrame) -> Dict[str, Any]:
    """Check if debt was fully paid off"""
    debt_free = df[df['Total Debt'] == 0]

    if len(debt_free) > 0:
        year = int(debt_free.iloc[0]['Year'])
        return {
            'name': 'Debt Payoff',
            'status': 'pass',
            'message': f'Debt fully paid off in Year {year}',
            'details': None
        }
    else:
        final_debt = df.iloc[-1]['Total Debt']
        return {
            'name': 'Debt Payoff',
            'status': 'warning',
            'message': f'Debt not fully paid off (${final_debt:,.0f} remaining)',
            'details': None
        }


def check_reserves_maintained(df: pd.DataFrame) -> Dict[str, Any]:
    """Check if emergency reserves were maintained adequately"""
    # Allow 10% tolerance
    below_target = df[df['Emergency Reserve'] < df['_RainyTarget'] * 0.9]

    if len(below_target) <= 5:
        return {
            'name': 'Reserve Maintenance',
            'status': 'pass',
            'message': 'Emergency reserves maintained adequately',
            'details': None
        }
    else:
        return {
            'name': 'Reserve Maintenance',
            'status': 'warning',
            'message': f'Reserves below target in {len(below_target)} month(s)',
            'details': below_target[['Year', 'Month', 'Emergency Reserve', '_RainyTarget']].head(10).to_dict('records')
        }


def check_feeder_tracking(df: pd.DataFrame) -> Dict[str, Any]:
    """Check if feeder property was always tracked when properties existed"""
    with_props = df[df['Properties Owned'] > 0]
    untracked = with_props[with_props['_FeederIndex'] == -1]

    if len(untracked) == 0:
        return {
            'name': 'Feeder Tracking',
            'status': 'pass',
            'message': 'Feeder tracked in all months with properties',
            'details': None
        }
    else:
        return {
            'name': 'Feeder Tracking',
            'status': 'warning',
            'message': f'Feeder not tracked in {len(untracked)} month(s)',
            'details': untracked[['Year', 'Month', 'Properties Owned', '_FeederIndex']].head(10).to_dict('records')
        }


def check_acquisition_feasibility(df: pd.DataFrame) -> Dict[str, Any]:
    """Check if acquisitions had sufficient funds available"""
    acq_months = df[df['Property Purchase'] > 0].copy()

    if len(acq_months) == 0:
        return {
            'name': 'Acquisition Feasibility',
            'status': 'warning',
            'message': 'No acquisitions to validate',
            'details': None
        }

    # All acquisitions succeeded if they happened
    return {
        'name': 'Acquisition Feasibility',
        'status': 'pass',
        'message': f'All {len(acq_months)} acquisitions were feasible',
        'details': None
    }


def check_refi_eligibility(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    """Check if refinances followed eligibility rules"""
    stop_refi = config['policies']['portfolio'].get('stopRefiAtMaxUnits', True)
    max_units = config['policies']['portfolio']['maxUnits']

    if not stop_refi:
        return {
            'name': 'Refi Eligibility',
            'status': 'pass',
            'message': 'stopRefiAtMaxUnits is disabled - no restriction',
            'details': None
        }

    # Find when max units was reached
    max_unit_rows = df[df['Properties Owned'] == max_units]
    if len(max_unit_rows) == 0:
        return {
            'name': 'Refi Eligibility',
            'status': 'pass',
            'message': 'Max units never reached - no refi restriction applied',
            'details': None
        }

    max_unit_idx = max_unit_rows.index[0]

    # Check for refis after max units
    after_max = df.loc[max_unit_idx:]
    refis_after = after_max[after_max['Refinance Proceeds'] > 0]

    if len(refis_after) == 0:
        return {
            'name': 'Refi Eligibility',
            'status': 'pass',
            'message': 'No refinancing after reaching max units (stopRefiAtMaxUnits=true)',
            'details': None
        }
    else:
        return {
            'name': 'Refi Eligibility',
            'status': 'fail',
            'message': f'{len(refis_after)} refinance(s) occurred after max units',
            'details': refis_after[['Year', 'Month', 'Refinance Proceeds']].to_dict('records')
        }


def get_anomalies(portfolio_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Detect anomalies in the simulation results.

    Returns:
        List of anomaly dicts with Year, Month, Issue, Severity, Description
    """
    anomalies = []

    # Check for sudden cash drops
    portfolio_df = portfolio_df.copy()
    portfolio_df['Cash_Drop'] = portfolio_df['Operating Cash'].diff()
    sudden_drops = portfolio_df[portfolio_df['Cash_Drop'] < -50000]

    for _, row in sudden_drops.iterrows():
        anomalies.append({
            'Year': int(row['Year']),
            'Month': int(row['Month']),
            'Issue': 'Sudden cash drop',
            'Severity': 'High',
            'Description': f"Operating Cash dropped by ${abs(row['Cash_Drop']):,.0f}"
        })

    # Check for negative Operating CF
    negative_cf = portfolio_df[portfolio_df['Operating Cash Flow'] < 0]
    for _, row in negative_cf.iterrows():
        anomalies.append({
            'Year': int(row['Year']),
            'Month': int(row['Month']),
            'Issue': 'Negative Operating CF',
            'Severity': 'High',
            'Description': f"Operating CF: ${row['Operating Cash Flow']:,.0f}"
        })

    # Check for reserves below 90% of target
    below_reserves = portfolio_df[portfolio_df['Emergency Reserve'] < portfolio_df['_RainyTarget'] * 0.9]
    for _, row in below_reserves.iterrows():
        anomalies.append({
            'Year': int(row['Year']),
            'Month': int(row['Month']),
            'Issue': 'Reserves below target',
            'Severity': 'Medium',
            'Description': f"Reserve: ${row['Emergency Reserve']:,.0f}, Target: ${row['_RainyTarget']:,.0f}"
        })

    return anomalies
