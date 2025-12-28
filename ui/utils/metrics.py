"""
Shared metric calculation utilities for the UI.

Centralized location for common calculations used across multiple pages.
"""

import pandas as pd
from typing import Union


def calculate_debt_free_year(portfolio_df: pd.DataFrame) -> Union[int, str]:
    """
    Calculate the year when the portfolio becomes debt-free.

    Args:
        portfolio_df: Portfolio DataFrame with 'Total Debt' and 'Year' columns

    Returns:
        Year number when debt-free, or descriptive string if not achieved/applicable

    Examples:
        >>> df = pd.DataFrame({'Total Debt': [100, 50, 0, 0], 'Year': [1, 2, 3, 4]})
        >>> calculate_debt_free_year(df)
        3
    """
    # Check if DataFrame is empty
    if portfolio_df.empty:
        return "No data"

    # Check required columns exist
    if 'Total Debt' not in portfolio_df.columns:
        return "Debt data unavailable"

    if 'Year' not in portfolio_df.columns:
        return "Year data unavailable"

    # Find rows with debt
    debt_rows = portfolio_df[portfolio_df['Total Debt'] > 0]

    # If no debt ever existed
    if len(debt_rows) == 0:
        return "Never had debt"

    # Check if model ran long enough (at least 12 months with debt)
    if len(debt_rows) < 12:
        return "Not yet"

    # Find rows without debt
    debt_free_rows = portfolio_df[portfolio_df['Total Debt'] == 0]

    # If debt-free state achieved
    if len(debt_free_rows) > 0:
        # Get the first month where debt becomes zero
        debt_free_year = int(debt_free_rows.iloc[0]['Year'])
        return debt_free_year

    # Still has debt at end of simulation
    return "Not achieved"


def calculate_total_distributions(portfolio_df: pd.DataFrame) -> float:
    """
    Calculate total distributions paid out over the simulation period.

    Args:
        portfolio_df: Portfolio DataFrame with 'Distribution Amount' column

    Returns:
        Total distribution amount, or 0.0 if column doesn't exist

    Examples:
        >>> df = pd.DataFrame({'Distribution Amount': [0, 0, 100, 200]})
        >>> calculate_total_distributions(df)
        300.0
    """
    if portfolio_df.empty:
        return 0.0

    if 'Distribution Amount' not in portfolio_df.columns:
        return 0.0

    return float(portfolio_df['Distribution Amount'].sum())


def calculate_cumulative_cash_flow(portfolio_df: pd.DataFrame, column: str = 'Operating Cash Flow') -> pd.Series:
    """
    Calculate cumulative cash flow over time.

    Args:
        portfolio_df: Portfolio DataFrame
        column: Name of cash flow column to accumulate

    Returns:
        Series of cumulative cash flow values

    Examples:
        >>> df = pd.DataFrame({'Operating Cash Flow': [100, 200, 150]})
        >>> calculate_cumulative_cash_flow(df, 'Operating Cash Flow').tolist()
        [100.0, 300.0, 450.0]
    """
    if portfolio_df.empty or column not in portfolio_df.columns:
        return pd.Series([0] * len(portfolio_df))

    return portfolio_df[column].cumsum()


def calculate_irr_approximation(portfolio_df: pd.DataFrame) -> Union[float, str]:
    """
    Calculate approximate IRR based on cash flows and final value.

    This is a simplified approximation for UI display purposes.
    For accurate IRR, use numpy_financial.irr() with proper cash flows.

    Args:
        portfolio_df: Portfolio DataFrame with cash flow data

    Returns:
        Approximate annualized IRR as decimal (e.g., 0.15 for 15%), or error string

    Note:
        This is a placeholder for future implementation
    """
    # TODO: Implement proper IRR calculation
    # Requires defining initial investment and periodic cash flows
    return "Not implemented"


def calculate_coc_return(
    total_cash_invested: float,
    annual_cash_flow: float
) -> Union[float, None]:
    """
    Calculate Cash-on-Cash return.

    Args:
        total_cash_invested: Total cash invested (down payments + closing costs)
        annual_cash_flow: Annual cash flow from operations

    Returns:
        CoC return as decimal (e.g., 0.12 for 12%), or None if invalid

    Examples:
        >>> calculate_coc_return(100000, 12000)
        0.12
        >>> calculate_coc_return(0, 12000)  # Invalid
        None
    """
    if total_cash_invested <= 0:
        return None

    return annual_cash_flow / total_cash_invested


def calculate_equity_multiple(
    total_cash_invested: float,
    current_equity: float,
    cumulative_distributions: float = 0.0
) -> Union[float, None]:
    """
    Calculate equity multiple (total value returned / cash invested).

    Args:
        total_cash_invested: Total cash invested
        current_equity: Current equity value (property value - debt)
        cumulative_distributions: Total distributions received

    Returns:
        Equity multiple (e.g., 2.5x), or None if invalid

    Examples:
        >>> calculate_equity_multiple(100000, 150000, 50000)
        2.0
    """
    if total_cash_invested <= 0:
        return None

    total_value = current_equity + cumulative_distributions
    return total_value / total_cash_invested


__all__ = [
    'calculate_debt_free_year',
    'calculate_total_distributions',
    'calculate_cumulative_cash_flow',
    'calculate_irr_approximation',
    'calculate_coc_return',
    'calculate_equity_multiple',
]
