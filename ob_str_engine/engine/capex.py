"""
CapEx Schedule Module - Phase 1.5

Provides per-unit capital expenditure tracking for major system replacements.

Tracks 6 systems per unit:
- HVAC: 15 years, $12,000
- Roof: 25 years, $25,000
- Appliances: 10 years, $8,000
- Flooring: 7 years, $10,000
- Furniture: 5 years, $15,000
- Water Heater: 12 years, $1,500

Systems age is tracked from unit purchase. When a system reaches end-of-life,
it generates a replacement event that draws from the shared CapEx reserve pool.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple


# Default system configurations
DEFAULT_SYSTEMS = {
    "hvac": {"lifespan_years": 15, "replacement_cost": 12000, "description": "HVAC System"},
    "roof": {"lifespan_years": 25, "replacement_cost": 25000, "description": "Roof"},
    "appliances": {"lifespan_years": 10, "replacement_cost": 8000, "description": "Kitchen Appliances"},
    "flooring": {"lifespan_years": 7, "replacement_cost": 10000, "description": "Flooring"},
    "furniture": {"lifespan_years": 5, "replacement_cost": 15000, "description": "Furniture Package"},
    "water_heater": {"lifespan_years": 12, "replacement_cost": 1500, "description": "Water Heater"},
}


@dataclass
class SystemStatus:
    """Status of a single system."""
    name: str
    age_months: int
    lifespan_months: int
    remaining_months: int
    replacement_cost: float
    needs_replacement: bool
    health_pct: float  # 100% = new, 0% = end of life


@dataclass
class CapExReplacement:
    """A scheduled or triggered replacement."""
    system_name: str
    unit_id: int
    cost: float
    month: int
    year: int
    from_reserve: bool  # True if paid from reserve, False if deferred


@dataclass
class UnitCapExStatus:
    """CapEx status for a single unit."""
    unit_id: int
    systems: Dict[str, SystemStatus]
    total_deferred_maintenance: float
    next_replacement_month: Optional[int]
    next_replacement_system: Optional[str]
    next_replacement_cost: Optional[float]


def get_capex_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get CapEx configuration from engine config.

    Args:
        config: Engine configuration

    Returns:
        CapEx configuration dict
    """
    capex_cfg = config.get("capex_schedule", {})

    return {
        "enabled": capex_cfg.get("enabled", False),
        "systems": capex_cfg.get("systems", DEFAULT_SYSTEMS),
    }


def is_capex_schedule_enabled(config: Dict[str, Any]) -> bool:
    """Check if CapEx schedule tracking is enabled."""
    capex_cfg = get_capex_config(config)
    return capex_cfg["enabled"]


def get_systems_config(config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Get systems configuration.

    Args:
        config: Engine configuration

    Returns:
        Dict of system configurations
    """
    capex_cfg = get_capex_config(config)
    return capex_cfg["systems"]


def initialize_unit_systems(
    unit_id: int,
    config: Dict[str, Any],
    initial_age_months: int = 0
) -> Dict[str, int]:
    """
    Initialize system ages for a new unit.

    Args:
        unit_id: Unit identifier
        config: Engine configuration
        initial_age_months: Initial age of systems (0 for new)

    Returns:
        Dict mapping system name to age in months
    """
    systems = get_systems_config(config)
    return {name: initial_age_months for name in systems.keys()}


def get_system_status(
    system_name: str,
    age_months: int,
    config: Dict[str, Any]
) -> SystemStatus:
    """
    Get status of a specific system.

    Args:
        system_name: Name of the system
        age_months: Current age in months
        config: Engine configuration

    Returns:
        SystemStatus for the system
    """
    systems = get_systems_config(config)
    system = systems.get(system_name, DEFAULT_SYSTEMS.get(system_name, {}))

    lifespan_months = system.get("lifespan_years", 10) * 12
    replacement_cost = system.get("replacement_cost", 5000)

    remaining = max(0, lifespan_months - age_months)
    needs_replacement = remaining <= 0
    health_pct = max(0, min(100, (remaining / lifespan_months) * 100))

    return SystemStatus(
        name=system_name,
        age_months=age_months,
        lifespan_months=lifespan_months,
        remaining_months=remaining,
        replacement_cost=replacement_cost,
        needs_replacement=needs_replacement,
        health_pct=health_pct
    )


def get_unit_capex_status(
    unit_id: int,
    system_ages: Dict[str, int],
    config: Dict[str, Any]
) -> UnitCapExStatus:
    """
    Get complete CapEx status for a unit.

    Args:
        unit_id: Unit identifier
        system_ages: Dict mapping system name to age in months
        config: Engine configuration

    Returns:
        UnitCapExStatus with all system details
    """
    systems = {}
    total_deferred = 0.0
    next_replacement_month = None
    next_replacement_system = None
    next_replacement_cost = None

    for name, age in system_ages.items():
        status = get_system_status(name, age, config)
        systems[name] = status

        if status.needs_replacement:
            total_deferred += status.replacement_cost

        # Track next scheduled replacement
        if status.remaining_months > 0:
            if next_replacement_month is None or status.remaining_months < next_replacement_month:
                next_replacement_month = status.remaining_months
                next_replacement_system = name
                next_replacement_cost = status.replacement_cost

    return UnitCapExStatus(
        unit_id=unit_id,
        systems=systems,
        total_deferred_maintenance=total_deferred,
        next_replacement_month=next_replacement_month,
        next_replacement_system=next_replacement_system,
        next_replacement_cost=next_replacement_cost
    )


def age_systems(
    system_ages: Dict[str, int],
    months: int = 1
) -> Dict[str, int]:
    """
    Age all systems by specified months.

    Args:
        system_ages: Current system ages
        months: Months to age

    Returns:
        Updated system ages
    """
    return {name: age + months for name, age in system_ages.items()}


def check_replacements_needed(
    system_ages: Dict[str, int],
    config: Dict[str, Any]
) -> List[str]:
    """
    Check which systems need replacement.

    Args:
        system_ages: Current system ages
        config: Engine configuration

    Returns:
        List of system names needing replacement
    """
    needs_replacement = []

    for name, age in system_ages.items():
        status = get_system_status(name, age, config)
        if status.needs_replacement:
            needs_replacement.append(name)

    return needs_replacement


def process_replacements(
    unit_id: int,
    system_ages: Dict[str, int],
    capex_reserve: float,
    current_month: int,
    current_year: int,
    config: Dict[str, Any]
) -> Tuple[Dict[str, int], float, List[CapExReplacement], float]:
    """
    Process system replacements for a unit.

    Args:
        unit_id: Unit identifier
        system_ages: Current system ages
        capex_reserve: Available CapEx reserve
        current_month: Current simulation month
        current_year: Current year
        config: Engine configuration

    Returns:
        Tuple of (updated_ages, remaining_reserve, replacements_made, deferred_amount)
    """
    systems_config = get_systems_config(config)
    replacements = []
    deferred = 0.0
    updated_ages = system_ages.copy()
    reserve = capex_reserve

    for name, age in system_ages.items():
        status = get_system_status(name, age, config)

        if status.needs_replacement:
            cost = status.replacement_cost

            if reserve >= cost:
                # Can afford replacement
                reserve -= cost
                updated_ages[name] = 0  # Reset age
                replacements.append(CapExReplacement(
                    system_name=name,
                    unit_id=unit_id,
                    cost=cost,
                    month=current_month,
                    year=current_year,
                    from_reserve=True
                ))
            else:
                # Defer replacement
                deferred += cost
                replacements.append(CapExReplacement(
                    system_name=name,
                    unit_id=unit_id,
                    cost=cost,
                    month=current_month,
                    year=current_year,
                    from_reserve=False
                ))

    return updated_ages, reserve, replacements, deferred


def calculate_annual_capex_budget(
    units_count: int,
    config: Dict[str, Any]
) -> float:
    """
    Calculate recommended annual CapEx budget.

    Based on sum of (replacement_cost / lifespan_years) for all systems.

    Args:
        units_count: Number of units
        config: Engine configuration

    Returns:
        Recommended annual CapEx budget
    """
    systems = get_systems_config(config)
    annual_per_unit = 0.0

    for system in systems.values():
        cost = system.get("replacement_cost", 0)
        years = system.get("lifespan_years", 10)
        annual_per_unit += cost / years

    return annual_per_unit * units_count


def calculate_portfolio_capex_status(
    units_data: List[Dict[str, Any]],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate CapEx status for entire portfolio.

    Args:
        units_data: List of unit data with system_ages
        config: Engine configuration

    Returns:
        Portfolio-level CapEx summary
    """
    total_deferred = 0.0
    systems_needing_replacement = 0
    upcoming_replacements = []
    total_annual_budget = 0.0

    for unit in units_data:
        unit_id = unit.get("unit_id", 0)
        system_ages = unit.get("system_ages", {})

        if not system_ages:
            continue

        status = get_unit_capex_status(unit_id, system_ages, config)
        total_deferred += status.total_deferred_maintenance

        for sys_status in status.systems.values():
            if sys_status.needs_replacement:
                systems_needing_replacement += 1
            elif sys_status.remaining_months <= 12:
                upcoming_replacements.append({
                    "unit_id": unit_id,
                    "system": sys_status.name,
                    "months_remaining": sys_status.remaining_months,
                    "cost": sys_status.replacement_cost
                })

    total_annual_budget = calculate_annual_capex_budget(len(units_data), config)

    # Sort upcoming by months remaining
    upcoming_replacements.sort(key=lambda x: x["months_remaining"])

    return {
        "total_deferred_maintenance": total_deferred,
        "systems_needing_replacement": systems_needing_replacement,
        "upcoming_replacements_12mo": upcoming_replacements,
        "recommended_annual_budget": total_annual_budget,
        "recommended_monthly_reserve": total_annual_budget / 12,
    }


def validate_capex_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate CapEx configuration.

    Args:
        config: Engine configuration

    Returns:
        List of validation issues
    """
    issues = []
    capex_cfg = config.get("capex_schedule", {})

    if not capex_cfg.get("enabled", False):
        return issues

    systems = capex_cfg.get("systems", {})

    for name, system in systems.items():
        if "lifespan_years" not in system:
            issues.append(f"{name}: Missing 'lifespan_years'")
        elif system["lifespan_years"] <= 0:
            issues.append(f"{name}: lifespan_years must be positive")

        if "replacement_cost" not in system:
            issues.append(f"{name}: Missing 'replacement_cost'")
        elif system["replacement_cost"] <= 0:
            issues.append(f"{name}: replacement_cost must be positive")

    return issues


def get_replacement_schedule(
    unit_id: int,
    system_ages: Dict[str, int],
    config: Dict[str, Any],
    years_ahead: int = 10
) -> List[Dict[str, Any]]:
    """
    Project replacement schedule for a unit.

    Args:
        unit_id: Unit identifier
        system_ages: Current system ages
        config: Engine configuration
        years_ahead: Years to project

    Returns:
        List of projected replacements
    """
    schedule = []
    months_ahead = years_ahead * 12

    for name, age in system_ages.items():
        status = get_system_status(name, age, config)

        # First replacement
        if status.needs_replacement:
            schedule.append({
                "system": name,
                "unit_id": unit_id,
                "month_offset": 0,
                "cost": status.replacement_cost,
                "status": "overdue"
            })
            age = 0  # Reset for calculating future

        # Future replacements within projection window
        lifespan = status.lifespan_months
        remaining = status.remaining_months
        next_replacement = remaining

        while next_replacement < months_ahead:
            schedule.append({
                "system": name,
                "unit_id": unit_id,
                "month_offset": next_replacement,
                "cost": status.replacement_cost,
                "status": "scheduled"
            })
            next_replacement += lifespan

    # Sort by month
    schedule.sort(key=lambda x: x["month_offset"])

    return schedule


def summarize_systems(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Create summary of configured systems.

    Args:
        config: Engine configuration

    Returns:
        List of system summaries
    """
    systems = get_systems_config(config)
    summaries = []

    for name, system in systems.items():
        summaries.append({
            "name": name,
            "description": system.get("description", name),
            "lifespan_years": system.get("lifespan_years", 0),
            "replacement_cost": system.get("replacement_cost", 0),
            "annual_reserve_per_unit": system.get("replacement_cost", 0) / system.get("lifespan_years", 1),
        })

    return summaries
