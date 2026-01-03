"""
Insurance Modeling Module - Phase 1.2

Provides coastal-specific insurance modeling for STR investments.

Key features:
- Market-specific base rates (OB: 4% vs generic: 3.3%)
- Insurance inflation (7% coastal, 3% inland)
- Named storm deductibles (2% of property value)
- Flood insurance for units in flood zones ($2,500/yr)
- Premium surcharge after claims (20% for 5 years)

Insurance is a significant expense for coastal properties and this module
provides more realistic modeling than flat percentage assumptions.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple, List


# Default insurance configuration
DEFAULT_INSURANCE_CONFIG = {
    "enabled": False,
    "base_rate": 0.033,  # 3.3% of property value for generic
    "inflation_rate": 0.03,  # 3% annual increase
    "named_storm_deductible_pct": 0.02,  # 2% of property value
    "flood_insurance_annual": 2500.0,  # Annual flood insurance premium
    "claim_surcharge_pct": 0.20,  # 20% premium increase after claim
    "claim_surcharge_years": 5,  # Years surcharge lasts
}

# Market-specific insurance defaults
MARKET_INSURANCE_DEFAULTS = {
    "orange_beach": {
        "base_rate": 0.04,  # 4% for coastal
        "inflation_rate": 0.07,  # 7% for coastal
        "named_storm_deductible_pct": 0.02,
        "flood_insurance_annual": 2500.0,
        "claim_surcharge_pct": 0.20,
        "claim_surcharge_years": 5,
    },
    "generic": {
        "base_rate": 0.033,  # 3.3% for inland
        "inflation_rate": 0.03,  # 3% for inland
        "named_storm_deductible_pct": 0.01,
        "flood_insurance_annual": 1500.0,
        "claim_surcharge_pct": 0.15,
        "claim_surcharge_years": 3,
    },
}


@dataclass
class InsurancePremium:
    """Insurance premium breakdown for a unit."""
    base_premium: float
    inflation_adjustment: float
    adjusted_premium: float
    flood_insurance: float
    surcharge_amount: float
    total_premium: float
    deductible_amount: float


@dataclass
class InsuranceClaim:
    """Insurance claim details."""
    claim_month: int
    claim_amount: float
    deductible_paid: float
    payout_amount: float
    payout_delay_months: int
    surcharge_until_month: int


def get_insurance_config(config: Dict[str, Any], market_name: str = None) -> Dict[str, Any]:
    """
    Get insurance configuration for a market.

    Args:
        config: Engine configuration
        market_name: Name of the market (for market-specific rates)

    Returns:
        Insurance configuration dict
    """
    # Check for market-specific config in market_profiles
    if market_name:
        market_profiles = config.get("market_profiles", {})
        profile = market_profiles.get(market_name, {})
        expenses = profile.get("expenses", {})

        if "insurance_rate" in expenses:
            return {
                "enabled": True,
                "base_rate": expenses.get("insurance_rate", DEFAULT_INSURANCE_CONFIG["base_rate"]),
                "inflation_rate": expenses.get("insurance_inflation_rate", DEFAULT_INSURANCE_CONFIG["inflation_rate"]),
                "named_storm_deductible_pct": expenses.get("named_storm_deductible_pct", DEFAULT_INSURANCE_CONFIG["named_storm_deductible_pct"]),
                "flood_insurance_annual": expenses.get("flood_insurance_annual", DEFAULT_INSURANCE_CONFIG["flood_insurance_annual"]),
                "claim_surcharge_pct": expenses.get("claim_surcharge_pct", DEFAULT_INSURANCE_CONFIG["claim_surcharge_pct"]),
                "claim_surcharge_years": expenses.get("claim_surcharge_years", DEFAULT_INSURANCE_CONFIG["claim_surcharge_years"]),
            }

        # Fall back to market defaults if known market
        if market_name in MARKET_INSURANCE_DEFAULTS:
            defaults = MARKET_INSURANCE_DEFAULTS[market_name]
            return {**defaults, "enabled": True}

    # Check for global insurance config
    insurance_cfg = config.get("insurance", {})
    if insurance_cfg:
        return {
            "enabled": insurance_cfg.get("enabled", False),
            "base_rate": insurance_cfg.get("base_rate", DEFAULT_INSURANCE_CONFIG["base_rate"]),
            "inflation_rate": insurance_cfg.get("inflation_rate", DEFAULT_INSURANCE_CONFIG["inflation_rate"]),
            "named_storm_deductible_pct": insurance_cfg.get("named_storm_deductible_pct", DEFAULT_INSURANCE_CONFIG["named_storm_deductible_pct"]),
            "flood_insurance_annual": insurance_cfg.get("flood_insurance_annual", DEFAULT_INSURANCE_CONFIG["flood_insurance_annual"]),
            "claim_surcharge_pct": insurance_cfg.get("claim_surcharge_pct", DEFAULT_INSURANCE_CONFIG["claim_surcharge_pct"]),
            "claim_surcharge_years": insurance_cfg.get("claim_surcharge_years", DEFAULT_INSURANCE_CONFIG["claim_surcharge_years"]),
        }

    return DEFAULT_INSURANCE_CONFIG.copy()


def is_insurance_enhanced(config: Dict[str, Any]) -> bool:
    """
    Check if enhanced insurance modeling is enabled.

    Enhanced means using market-specific rates, inflation, etc.
    Returns True if any market profile has insurance config or global insurance is enabled.
    """
    # Check global insurance config
    insurance_cfg = config.get("insurance", {})
    if insurance_cfg.get("enabled", False):
        return True

    # Check market profiles
    market_profiles = config.get("market_profiles", {})
    for profile in market_profiles.values():
        expenses = profile.get("expenses", {})
        if "insurance_rate" in expenses or "insurance_inflation_rate" in expenses:
            return True

    return False


def calculate_base_premium(
    property_value: float,
    base_rate: float
) -> float:
    """
    Calculate base annual insurance premium.

    Args:
        property_value: Current property value
        base_rate: Annual insurance rate as decimal (e.g., 0.04 for 4%)

    Returns:
        Annual base premium
    """
    return property_value * base_rate


def apply_insurance_inflation(
    base_premium: float,
    years_owned: int,
    inflation_rate: float
) -> float:
    """
    Apply insurance inflation to base premium.

    Coastal insurance has been increasing at ~7% annually.

    Args:
        base_premium: Base annual premium
        years_owned: Years the property has been owned
        inflation_rate: Annual inflation rate for insurance

    Returns:
        Inflation-adjusted premium
    """
    if years_owned <= 0:
        return base_premium
    return base_premium * ((1 + inflation_rate) ** (years_owned - 1))


def calculate_flood_insurance(
    in_flood_zone: bool,
    base_flood_premium: float = 2500.0,
    years_owned: int = 1,
    inflation_rate: float = 0.03
) -> float:
    """
    Calculate flood insurance premium.

    Args:
        in_flood_zone: Whether property is in a flood zone
        base_flood_premium: Base annual flood premium
        years_owned: Years property has been owned
        inflation_rate: Annual inflation rate

    Returns:
        Annual flood insurance premium (0 if not in flood zone)
    """
    if not in_flood_zone:
        return 0.0
    return base_flood_premium * ((1 + inflation_rate) ** max(0, years_owned - 1))


def calculate_surcharge(
    base_premium: float,
    has_claim: bool,
    months_since_claim: int,
    surcharge_pct: float,
    surcharge_months: int
) -> float:
    """
    Calculate premium surcharge after a claim.

    Args:
        base_premium: Annual base premium
        has_claim: Whether there's been a claim
        months_since_claim: Months since the claim
        surcharge_pct: Surcharge percentage (e.g., 0.20 for 20%)
        surcharge_months: How many months surcharge lasts

    Returns:
        Annual surcharge amount
    """
    if not has_claim or months_since_claim >= surcharge_months:
        return 0.0
    return base_premium * surcharge_pct


def calculate_deductible(
    property_value: float,
    deductible_pct: float,
    is_named_storm: bool = False
) -> float:
    """
    Calculate insurance deductible.

    Named storms often have percentage-based deductibles.

    Args:
        property_value: Current property value
        deductible_pct: Deductible as percentage of value
        is_named_storm: Whether this is a named storm claim

    Returns:
        Deductible amount
    """
    if is_named_storm:
        return property_value * deductible_pct
    # Standard claims typically have lower fixed deductibles
    return min(property_value * 0.01, 2500.0)


def calculate_unit_insurance(
    property_value: float,
    years_owned: int,
    in_flood_zone: bool,
    has_claim: bool,
    months_since_claim: int,
    config: Dict[str, Any],
    market_name: str = "orange_beach"
) -> InsurancePremium:
    """
    Calculate complete insurance premium for a unit.

    Args:
        property_value: Current property value
        years_owned: Years property has been owned
        in_flood_zone: Whether property is in flood zone
        has_claim: Whether there's been a claim
        months_since_claim: Months since claim
        config: Engine configuration
        market_name: Name of the market

    Returns:
        InsurancePremium with all details
    """
    ins_cfg = get_insurance_config(config, market_name)

    base_rate = ins_cfg["base_rate"]
    inflation_rate = ins_cfg["inflation_rate"]
    flood_annual = ins_cfg.get("flood_insurance_annual", 2500.0)
    surcharge_pct = ins_cfg["claim_surcharge_pct"]
    surcharge_years = ins_cfg["claim_surcharge_years"]
    deductible_pct = ins_cfg["named_storm_deductible_pct"]

    # Base premium (on original value, but we use current for simplicity)
    base_premium = calculate_base_premium(property_value, base_rate)

    # Apply inflation
    inflation_adj = apply_insurance_inflation(base_premium, years_owned, inflation_rate) - base_premium
    adjusted_premium = base_premium + inflation_adj

    # Flood insurance
    flood_ins = calculate_flood_insurance(in_flood_zone, flood_annual, years_owned, 0.03)

    # Surcharge
    surcharge_months = surcharge_years * 12
    surcharge = calculate_surcharge(
        adjusted_premium, has_claim, months_since_claim, surcharge_pct, surcharge_months
    )

    # Total
    total = adjusted_premium + flood_ins + surcharge

    # Deductible (for reference)
    deductible = calculate_deductible(property_value, deductible_pct, is_named_storm=True)

    return InsurancePremium(
        base_premium=base_premium,
        inflation_adjustment=inflation_adj,
        adjusted_premium=adjusted_premium,
        flood_insurance=flood_ins,
        surcharge_amount=surcharge,
        total_premium=total,
        deductible_amount=deductible
    )


def calculate_monthly_insurance(premium: InsurancePremium) -> float:
    """
    Get monthly insurance cost from annual premium.

    Args:
        premium: InsurancePremium object

    Returns:
        Monthly insurance cost
    """
    return premium.total_premium / 12


def process_insurance_claim(
    claim_amount: float,
    property_value: float,
    is_named_storm: bool,
    current_month: int,
    config: Dict[str, Any],
    market_name: str = "orange_beach",
    coverage_pct: float = 0.90,
    payout_delay_months: int = 4
) -> InsuranceClaim:
    """
    Process an insurance claim.

    Args:
        claim_amount: Total damage/repair cost
        property_value: Current property value
        is_named_storm: Whether claim is from named storm
        current_month: Current simulation month
        config: Engine configuration
        market_name: Market name
        coverage_pct: Percentage of damages covered
        payout_delay_months: Months until payout

    Returns:
        InsuranceClaim with all details
    """
    ins_cfg = get_insurance_config(config, market_name)

    deductible_pct = ins_cfg["named_storm_deductible_pct"]
    surcharge_years = ins_cfg["claim_surcharge_years"]

    deductible = calculate_deductible(property_value, deductible_pct, is_named_storm)
    covered_amount = claim_amount * coverage_pct
    payout = max(0, covered_amount - deductible)

    surcharge_until = current_month + (surcharge_years * 12)

    return InsuranceClaim(
        claim_month=current_month,
        claim_amount=claim_amount,
        deductible_paid=min(deductible, claim_amount),
        payout_amount=payout,
        payout_delay_months=payout_delay_months,
        surcharge_until_month=surcharge_until
    )


def calculate_portfolio_insurance(
    units_data: List[Dict[str, Any]],
    config: Dict[str, Any]
) -> Dict[str, float]:
    """
    Calculate total insurance for portfolio.

    Args:
        units_data: List of unit data dicts
        config: Engine configuration

    Returns:
        Dict with portfolio insurance totals
    """
    total_base = 0.0
    total_adjusted = 0.0
    total_flood = 0.0
    total_surcharge = 0.0
    total_premium = 0.0
    total_deductible_exposure = 0.0

    for unit in units_data:
        premium = calculate_unit_insurance(
            property_value=unit.get("value", 0),
            years_owned=unit.get("years_owned", 1),
            in_flood_zone=unit.get("in_flood_zone", False),
            has_claim=unit.get("has_claim", False),
            months_since_claim=unit.get("months_since_claim", 0),
            config=config,
            market_name=unit.get("market_name", "orange_beach")
        )

        total_base += premium.base_premium
        total_adjusted += premium.adjusted_premium
        total_flood += premium.flood_insurance
        total_surcharge += premium.surcharge_amount
        total_premium += premium.total_premium
        total_deductible_exposure += premium.deductible_amount

    return {
        "base_premium": total_base,
        "adjusted_premium": total_adjusted,
        "flood_insurance": total_flood,
        "surcharge_amount": total_surcharge,
        "total_premium": total_premium,
        "monthly_cost": total_premium / 12,
        "deductible_exposure": total_deductible_exposure,
    }


def validate_insurance_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate insurance configuration.

    Args:
        config: Engine configuration

    Returns:
        List of validation issues (empty if valid)
    """
    issues = []

    # Check market profiles for insurance config
    market_profiles = config.get("market_profiles", {})
    for market_name, profile in market_profiles.items():
        expenses = profile.get("expenses", {})

        if "insurance_rate" in expenses:
            rate = expenses["insurance_rate"]
            if rate < 0.01 or rate > 0.15:
                issues.append(f"{market_name}: Insurance rate {rate} seems unusual (expected 1-15%)")

        if "insurance_inflation_rate" in expenses:
            infl = expenses["insurance_inflation_rate"]
            if infl < 0 or infl > 0.20:
                issues.append(f"{market_name}: Insurance inflation {infl} out of range (0-20%)")

    # Check global insurance config
    insurance_cfg = config.get("insurance", {})
    if insurance_cfg.get("enabled", False):
        rate = insurance_cfg.get("base_rate", 0)
        if rate < 0.01 or rate > 0.15:
            issues.append(f"Global insurance rate {rate} seems unusual (expected 1-15%)")

    return issues


def estimate_annual_insurance_trend(
    initial_value: float,
    years: int,
    appreciation_rate: float,
    config: Dict[str, Any],
    market_name: str = "orange_beach"
) -> List[Dict[str, float]]:
    """
    Estimate insurance costs over time.

    Args:
        initial_value: Initial property value
        years: Number of years to project
        appreciation_rate: Annual property appreciation
        config: Engine configuration
        market_name: Market name

    Returns:
        List of yearly insurance estimates
    """
    ins_cfg = get_insurance_config(config, market_name)
    base_rate = ins_cfg["base_rate"]
    inflation_rate = ins_cfg["inflation_rate"]

    results = []
    current_value = initial_value

    for year in range(1, years + 1):
        # Base premium on current value
        base = current_value * base_rate

        # Apply inflation to premium
        adjusted = base * ((1 + inflation_rate) ** (year - 1))

        results.append({
            "year": year,
            "property_value": current_value,
            "base_premium": base,
            "adjusted_premium": adjusted,
            "effective_rate": adjusted / current_value,
        })

        # Appreciate property for next year
        current_value *= (1 + appreciation_rate)

    return results
