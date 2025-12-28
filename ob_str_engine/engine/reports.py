"""
Investor-Friendly Reporting Functions

Provides clean, professional reports for real estate investors:
- Executive Summary: High-level portfolio metrics
- Operating Performance: Income/expense detail
- Acquisition Activity: Purchase timeline
- Cash Flow Detail: Full cash movement analysis
"""

import pandas as pd
from typing import Optional


def executive_summary_report(df: pd.DataFrame, annual: bool = False) -> pd.DataFrame:
    """
    Executive Summary Report - High-level portfolio snapshot

    Shows: Properties, Portfolio Value, Debt, Equity, LTV%, Income, NOI, Cash Flows, Reserves
    Frequency: Monthly or Annual

    Note:
    - NOI = Gross Income - Operating Expenses (before debt service)
    - Operating Cash Flow = NOI - Debt Service - CapEx (operational profitability)
    - Distributable Cash Flow = Operating CF - Reserve Topups (true distributable cash)
    """
    columns = [
        "Year",
        "Month",
        "Properties Owned",
        "Total Portfolio Value",
        "Total Debt",
        "Total Equity",
        "LTV %",
        "Monthly Rental Income",
        "Net Operating Income",
        "Operating Cash Flow",
        "Distributable Cash Flow",
        "Total Cash Reserves",
    ]

    if annual:
        # Annual summary: last month of each year
        result = df.groupby("Year").tail(1)[columns].copy()
        result = result.drop(columns=["Month"])
        # Sum rental income, NOI, and cash flows for the year
        annual_income = df.groupby("Year")["Monthly Rental Income"].sum()
        annual_noi = df.groupby("Year")["Net Operating Income"].sum()
        annual_ocf = df.groupby("Year")["Operating Cash Flow"].sum()
        annual_dcf = df.groupby("Year")["Distributable Cash Flow"].sum()
        result["Annual Rental Income"] = result["Year"].map(annual_income)
        result["Annual NOI"] = result["Year"].map(annual_noi)
        result["Annual Operating Cash Flow"] = result["Year"].map(annual_ocf)
        result["Annual Distributable Cash Flow"] = result["Year"].map(annual_dcf)
        result = result.drop(columns=["Monthly Rental Income", "Net Operating Income", "Operating Cash Flow", "Distributable Cash Flow"])
    else:
        # Monthly view
        result = df[columns].copy()

    return result


def operating_performance_report(df: pd.DataFrame, annual: bool = True) -> pd.DataFrame:
    """
    Operating Performance Report - Income and expense detail

    Shows: Income, all expense categories, NOI, Cash Flow
    Frequency: Typically Annual
    """
    if annual:
        # Annual aggregation
        result = df.groupby("Year").agg({
            "Properties Owned": "last",
            "Monthly Rental Income": "sum",
            "Property Management": "sum",
            "CapEx & Maintenance": "sum",
            "HOA Fees": "sum",
            "Property Insurance": "sum",
            "Property Taxes": "sum",
            "Debt Service": "sum",
            "Net Operating Income": "sum",
            "Cash Flow After Debt Service": "sum",
        }).reset_index()

        # Rename for clarity
        result.columns = [
            "Year",
            "Properties Owned",
            "Annual Rental Income",
            "Annual Property Management",
            "Annual CapEx & Maintenance",
            "Annual HOA Fees",
            "Annual Property Insurance",
            "Annual Property Taxes",
            "Annual Debt Service",
            "Annual NOI",
            "Annual Cash Flow",
        ]
    else:
        # Monthly view
        columns = [
            "Year",
            "Month",
            "Properties Owned",
            "Monthly Rental Income",
            "Property Management",
            "CapEx & Maintenance",
            "HOA Fees",
            "Property Insurance",
            "Property Taxes",
            "Debt Service",
            "Net Operating Income",
            "Cash Flow After Debt Service",
        ]
        result = df[columns].copy()

    return result


def acquisition_activity_report(df: pd.DataFrame) -> pd.DataFrame:
    """
    Acquisition Activity Report - Purchase timeline and details

    Shows: Only months with purchases, including financing details
    Frequency: Event-based (filtered to purchase months only)
    """
    # Filter to months with purchases
    purchases = df[df["Property Purchase"] > 0].copy()

    if len(purchases) == 0:
        return pd.DataFrame()

    columns = [
        "Year",
        "Month",
        "Properties Owned",
        "Property Market Value",
        "Down Payment",
        "Closing Costs",
        "Total Acquisition Cost",
        "Refinance Proceeds",
        "Growth Savings",
        "Total Cash Reserves",
    ]

    result = purchases[columns].copy()

    # Add financing amount
    result["Financing Amount"] = result["Property Market Value"] - result["Down Payment"]

    return result


def cash_flow_detail_report(df: pd.DataFrame, exclude_internal: bool = True) -> pd.DataFrame:
    """
    Cash Flow Detail Report - Complete cash movement analysis

    Shows: All cash-related columns with investor-friendly names
    Frequency: Monthly (for detailed analysis)
    """
    if exclude_internal:
        # Exclude internal tracking columns (those starting with _)
        columns = [col for col in df.columns if not col.startswith("_")]
    else:
        # Include everything
        columns = df.columns.tolist()

    return df[columns].copy()


def year_over_year_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Year-over-Year Summary - Annual progression

    Comprehensive year-end snapshot including all key metrics

    Note:
    - Annual NOI = Operating profit before debt service
    - Annual Operating Cash Flow = Operational profitability (NOI - Debt - CapEx)
    - Annual Distributable Cash Flow = True distributable cash after reserve obligations
    """
    result = df.groupby("Year").agg({
        "Properties Owned": "last",
        "Total Portfolio Value": "last",
        "Total Debt": "last",
        "Total Equity": "last",
        "LTV %": "last",
        "Operating Cash": "last",
        "Emergency Reserve": "last",
        "Growth Savings": "last",
        "Total Cash Reserves": "last",
        "Monthly Rental Income": "sum",
        "Net Operating Income": "sum",
        "Operating Cash Flow": "sum",
        "Distributable Cash Flow": "sum",
        "Principal Prepayment": "sum",
        "Total Interest Earned": "sum",
    }).reset_index()

    # Rename summed columns for clarity
    result = result.rename(columns={
        "Monthly Rental Income": "Annual Rental Income",
        "Net Operating Income": "Annual NOI",
        "Operating Cash Flow": "Annual Operating Cash Flow",
        "Distributable Cash Flow": "Annual Distributable Cash Flow",
        "Principal Prepayment": "Annual Principal Prepayment",
        "Total Interest Earned": "Annual Interest Earned",
    })

    return result


def unit_breakdown_report(unit_df: pd.DataFrame, year: Optional[int] = None) -> pd.DataFrame:
    """
    Unit-Level Breakdown Report - Individual property details

    Shows detailed metrics for each property by year or for a specific year

    Args:
        unit_df: DataFrame from SimulationResult.units
        year: Optional specific year to report on. If None, shows all years (year-end snapshot)

    Returns:
        DataFrame with unit-level details
    """
    if len(unit_df) == 0:
        return pd.DataFrame()

    if year is not None:
        # Filter to specific year, last month
        result = unit_df[unit_df['Year'] == year].copy()
        result = result[result['Month'] == result['Month'].max()]
    else:
        # Year-end snapshot for all years (December of each year)
        result = unit_df.groupby('Year').tail(unit_df['Unit_ID'].nunique()).copy()

    # Sort by Year, then Unit_ID
    result = result.sort_values(['Year', 'Unit_ID'])

    return result


def cash_flow_waterfall(df: pd.DataFrame, year: int, month: int = 12) -> pd.DataFrame:
    """
    Cash Flow Waterfall - Sequential cash flow breakdown for a specific month

    Shows how cash flows from starting balance through income, expenses, and financing
    to ending balance. Perfect for understanding cash movements in detail.

    Args:
        df: Portfolio-level monthly DataFrame (from SimulationResult.monthly)
        year: Year to analyze
        month: Month to analyze (default: 12 = December)

    Returns:
        DataFrame with Category, Amount, and Running_Balance columns
    """
    # Get the specific month's data
    month_data = df[(df['Year'] == year) & (df['Month'] == month)]

    if len(month_data) == 0:
        return pd.DataFrame(columns=['Category', 'Amount', 'Running_Balance'])

    row = month_data.iloc[0]

    # Get previous month for starting cash
    if month > 1:
        prev_month_data = df[(df['Year'] == year) & (df['Month'] == month - 1)]
    else:
        prev_month_data = df[(df['Year'] == year - 1) & (df['Month'] == 12)]

    if len(prev_month_data) > 0:
        starting_cash = prev_month_data.iloc[0]['Operating Cash']
    else:
        # First month - calculate backwards
        starting_cash = row['Operating Cash'] - (
            row['Monthly Rental Income'] +
            row['Interest - Operating'] +
            row.get('Refinance Proceeds', 0) -
            row['Property Management'] -
            row['CapEx & Maintenance'] -
            row['HOA Fees'] -
            row['Property Insurance'] -
            row['Property Taxes'] -
            row['Debt Service'] -
            row.get('_RainyTopup', 0) -
            row.get('Principal Prepayment', 0) -
            row.get('Savings Deposit', 0) -
            row.get('Down Payment', 0) -
            row.get('Closing Costs', 0)
        )

    # Build waterfall
    waterfall_data = []
    running_balance = starting_cash

    # Starting position
    waterfall_data.append({
        'Category': 'Starting Operating Cash',
        'Amount': starting_cash,
        'Running_Balance': running_balance
    })

    # Income
    rental_income = row['Monthly Rental Income']
    running_balance += rental_income
    waterfall_data.append({
        'Category': '+ Rental Income',
        'Amount': rental_income,
        'Running_Balance': running_balance
    })

    interest_income = row['Interest - Operating']
    running_balance += interest_income
    waterfall_data.append({
        'Category': '+ Interest Earned',
        'Amount': interest_income,
        'Running_Balance': running_balance
    })

    # Refinance proceeds (if any)
    refi_proceeds = row.get('Refinance Proceeds', 0)
    if refi_proceeds > 0:
        running_balance += refi_proceeds
        waterfall_data.append({
            'Category': '+ Refinance Proceeds',
            'Amount': refi_proceeds,
            'Running_Balance': running_balance
        })

    # Operating Expenses
    prop_mgmt = row['Property Management']
    running_balance -= prop_mgmt
    waterfall_data.append({
        'Category': '- Property Management',
        'Amount': -prop_mgmt,
        'Running_Balance': running_balance
    })

    capex = row['CapEx & Maintenance']
    running_balance -= capex
    waterfall_data.append({
        'Category': '- CapEx & Maintenance',
        'Amount': -capex,
        'Running_Balance': running_balance
    })

    hoa = row['HOA Fees']
    running_balance -= hoa
    waterfall_data.append({
        'Category': '- HOA Fees',
        'Amount': -hoa,
        'Running_Balance': running_balance
    })

    insurance = row['Property Insurance']
    running_balance -= insurance
    waterfall_data.append({
        'Category': '- Property Insurance',
        'Amount': -insurance,
        'Running_Balance': running_balance
    })

    taxes = row['Property Taxes']
    running_balance -= taxes
    waterfall_data.append({
        'Category': '- Property Taxes',
        'Amount': -taxes,
        'Running_Balance': running_balance
    })

    # NOI checkpoint
    waterfall_data.append({
        'Category': '= Net Operating Income',
        'Amount': row['Net Operating Income'],
        'Running_Balance': running_balance
    })

    # Debt Service
    debt_service = row['Debt Service']
    running_balance -= debt_service
    waterfall_data.append({
        'Category': '- Debt Service',
        'Amount': -debt_service,
        'Running_Balance': running_balance
    })

    # Operating Cash Flow checkpoint
    waterfall_data.append({
        'Category': '= Operating Cash Flow',
        'Amount': row['Operating Cash Flow'],
        'Running_Balance': running_balance
    })

    # Reserve movements
    reserve_topup = row.get('_RainyTopup', 0)
    if reserve_topup > 0:
        running_balance -= reserve_topup
        waterfall_data.append({
            'Category': '- Reserve Topup',
            'Amount': -reserve_topup,
            'Running_Balance': running_balance
        })

    # Distributable Cash Flow checkpoint
    waterfall_data.append({
        'Category': '= Distributable Cash Flow',
        'Amount': row['Distributable Cash Flow'],
        'Running_Balance': running_balance
    })

    # Uses of cash

    # Distribution amount (if any)
    distribution_amount = row.get('Distribution Amount', 0)
    if distribution_amount > 0:
        running_balance -= distribution_amount
        waterfall_data.append({
            'Category': '- Distribution to Investors',
            'Amount': -distribution_amount,
            'Running_Balance': running_balance
        })

    principal_prepay = row.get('Principal Prepayment', 0)
    if principal_prepay > 0:
        running_balance -= principal_prepay
        waterfall_data.append({
            'Category': '- Principal Prepayment',
            'Amount': -principal_prepay,
            'Running_Balance': running_balance
        })

    savings_deposit = row.get('Savings Deposit', 0)
    if savings_deposit > 0:
        running_balance -= savings_deposit
        waterfall_data.append({
            'Category': '- Savings Deposit',
            'Amount': -savings_deposit,
            'Running_Balance': running_balance
        })

    # Acquisition costs (if any)
    down_payment = row.get('Down Payment', 0)
    if down_payment > 0:
        running_balance -= down_payment
        waterfall_data.append({
            'Category': '- Down Payment',
            'Amount': -down_payment,
            'Running_Balance': running_balance
        })

    closing_costs = row.get('Closing Costs', 0)
    if closing_costs > 0:
        running_balance -= closing_costs
        waterfall_data.append({
            'Category': '- Closing Costs',
            'Amount': -closing_costs,
            'Running_Balance': running_balance
        })

    # Ending position
    waterfall_data.append({
        'Category': 'Ending Operating Cash',
        'Amount': row['Operating Cash'],
        'Running_Balance': running_balance
    })

    return pd.DataFrame(waterfall_data)


def unit_cash_flow_waterfall(unit_df: pd.DataFrame, unit_id: int, year: int, month: int = 12) -> pd.DataFrame:
    """
    Per-Unit Cash Flow Waterfall - Sequential cash flow for individual property

    Shows cash flow breakdown for a specific property. Useful for understanding
    individual property profitability.

    Args:
        unit_df: Unit-level DataFrame (from SimulationResult.units)
        unit_id: Unit ID to analyze (0-6 for 7 properties)
        year: Year to analyze
        month: Month to analyze (default: 12 = December)

    Returns:
        DataFrame with Category and Amount columns
    """
    # Get the specific unit-month data
    unit_data = unit_df[
        (unit_df['Unit_ID'] == unit_id) &
        (unit_df['Year'] == year) &
        (unit_df['Month'] == month)
    ]

    if len(unit_data) == 0:
        return pd.DataFrame(columns=['Category', 'Amount'])

    row = unit_data.iloc[0]

    # Build waterfall
    waterfall_data = []

    # Income
    rental_income = row.get('Unit_Rental_Income', 0)
    waterfall_data.append({
        'Category': 'Rental Income',
        'Amount': rental_income
    })

    # Operating Expenses
    prop_mgmt = row.get('Unit_Property_Mgmt', 0)
    waterfall_data.append({
        'Category': '- Property Management',
        'Amount': -prop_mgmt
    })

    capex = row.get('Unit_CapEx', 0)
    waterfall_data.append({
        'Category': '- CapEx & Maintenance',
        'Amount': -capex
    })

    hoa = row.get('Unit_HOA', 0)
    waterfall_data.append({
        'Category': '- HOA Fees',
        'Amount': -hoa
    })

    insurance = row.get('Unit_Insurance', 0)
    waterfall_data.append({
        'Category': '- Property Insurance',
        'Amount': -insurance
    })

    taxes = row.get('Unit_Property_Tax', 0)
    waterfall_data.append({
        'Category': '- Property Taxes',
        'Amount': -taxes
    })

    # NOI checkpoint
    noi = row.get('Unit_NOI', 0)
    waterfall_data.append({
        'Category': '= Net Operating Income',
        'Amount': noi
    })

    # Debt Service
    debt_service = row.get('Unit_Debt_Service', 0)
    waterfall_data.append({
        'Category': '- Debt Service',
        'Amount': -debt_service
    })

    # Operating Cash Flow
    operating_cf = row.get('Unit_Operating_CF', 0)
    waterfall_data.append({
        'Category': '= Operating Cash Flow',
        'Amount': operating_cf
    })

    return pd.DataFrame(waterfall_data)


def format_currency_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Format all numeric columns as currency for display
    """
    result = df.copy()
    for col in result.columns:
        if col not in ["Year", "Month", "Properties Owned", "LTV %"] and pd.api.types.is_numeric_dtype(result[col]):
            result[col] = result[col].apply(lambda x: f"${x:,.2f}" if pd.notna(x) else "")
    return result
