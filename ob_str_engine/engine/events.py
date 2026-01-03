"""
Event Modeling Module - Phase 1.3

Provides scheduled event processing for stress testing and scenario analysis.

Event types:
- minor: Small repairs/maintenance ($1-5k, no vacancy)
- moderate: Significant repairs ($5-25k, 1-2 weeks vacancy)
- major: Major repairs/renovations ($25-75k, 1-3 months vacancy)
- catastrophic: Natural disaster/total renovation ($75k+, 2-6 months vacancy)

Event scope:
- unit: Affects a single unit
- portfolio: Affects all units

Per Amendment 3: Simple chronological table, not Gantt chart.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


class EventType(Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CATASTROPHIC = "catastrophic"


class EventScope(Enum):
    UNIT = "unit"
    PORTFOLIO = "portfolio"


@dataclass
class EventImpact:
    """Impact of an event on operations."""
    vacancy_months: int = 0
    repair_cost: float = 0.0
    adr_reduction_pct: float = 0.0
    recovery_months: int = 0


@dataclass
class InsuranceClaim:
    """Insurance claim associated with an event."""
    coverage_pct: float = 0.0
    deductible_pct: float = 0.0
    payout_delay_months: int = 0


@dataclass
class ScheduledEvent:
    """A scheduled event in the simulation."""
    name: str
    event_type: str  # minor, moderate, major, catastrophic
    year: int
    month: int
    scope: str  # unit or portfolio
    unit_id: Optional[int] = None  # Only for unit-scope events
    impacts: Dict[str, Any] = field(default_factory=dict)
    insurance_claim: Optional[Dict[str, Any]] = None
    description: str = ""
    triggered: bool = False
    trigger_month: int = 0


@dataclass
class EventResult:
    """Result of processing an event."""
    event_name: str
    simulation_month: int
    year: int
    month: int
    affected_units: List[int]
    total_repair_cost: float
    total_vacancy_months: int
    insurance_payout: float
    insurance_payout_month: int
    net_cost: float


# Default event scenarios
DEFAULT_EVENT_SCENARIOS = [
    {
        "name": "Hurricane Hit",
        "type": "catastrophic",
        "year": 3,
        "month": 9,
        "scope": "portfolio",
        "impacts": {
            "vacancy_months": 2,
            "repair_cost": 50000,
            "adr_reduction_pct": 0.10,
            "recovery_months": 6
        },
        "insurance_claim": {
            "coverage_pct": 0.90,
            "deductible_pct": 0.02,
            "payout_delay_months": 4
        },
        "description": "Major hurricane causes widespread damage"
    },
    {
        "name": "Pandemic",
        "type": "major",
        "year": 5,
        "month": 3,
        "scope": "portfolio",
        "impacts": {
            "vacancy_months": 0,
            "repair_cost": 0,
            "adr_reduction_pct": 0.30,
            "recovery_months": 18
        },
        "description": "Pandemic reduces travel demand significantly"
    },
    {
        "name": "Major HVAC Failure",
        "type": "moderate",
        "year": 7,
        "month": 6,
        "scope": "unit",
        "unit_id": 0,
        "impacts": {
            "vacancy_months": 1,
            "repair_cost": 12000
        },
        "description": "HVAC system failure requiring full replacement"
    },
    {
        "name": "Dishwasher Failure",
        "type": "minor",
        "year": 2,
        "month": 8,
        "scope": "unit",
        "unit_id": 0,
        "impacts": {
            "vacancy_months": 0,
            "repair_cost": 1500
        },
        "description": "Appliance failure requiring replacement"
    },
    {
        "name": "Market Softening",
        "type": "moderate",
        "year": 10,
        "month": 1,
        "scope": "portfolio",
        "impacts": {
            "vacancy_months": 0,
            "repair_cost": 0,
            "adr_reduction_pct": 0.15,
            "recovery_months": 24
        },
        "description": "Market correction reduces rental rates"
    }
]


def get_events_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get events configuration from engine config.

    Args:
        config: Engine configuration

    Returns:
        Events configuration dict
    """
    events_cfg = config.get("events", {})

    return {
        "enabled": events_cfg.get("enabled", False),
        "scenarios": events_cfg.get("scenarios", []),
    }


def is_events_enabled(config: Dict[str, Any]) -> bool:
    """Check if event modeling is enabled."""
    events_cfg = get_events_config(config)
    return events_cfg["enabled"]


def get_scheduled_events(config: Dict[str, Any]) -> List[ScheduledEvent]:
    """
    Get list of scheduled events from config.

    Args:
        config: Engine configuration

    Returns:
        List of ScheduledEvent objects
    """
    events_cfg = get_events_config(config)

    if not events_cfg["enabled"]:
        return []

    scenarios = events_cfg.get("scenarios", [])

    events = []
    for scenario in scenarios:
        event = ScheduledEvent(
            name=scenario.get("name", "Unnamed Event"),
            event_type=scenario.get("type", "minor"),
            year=scenario.get("year", 1),
            month=scenario.get("month", 1),
            scope=scenario.get("scope", "unit"),
            unit_id=scenario.get("unit_id"),
            impacts=scenario.get("impacts", {}),
            insurance_claim=scenario.get("insurance_claim"),
            description=scenario.get("description", ""),
        )
        events.append(event)

    return events


def get_simulation_month(year: int, month: int) -> int:
    """Convert year/month to simulation month."""
    return (year - 1) * 12 + month


def check_event_triggers(
    events: List[ScheduledEvent],
    current_year: int,
    current_month: int
) -> List[ScheduledEvent]:
    """
    Check which events should trigger this month.

    Args:
        events: List of scheduled events
        current_year: Current simulation year
        current_month: Current calendar month (1-12)

    Returns:
        List of events to trigger
    """
    triggered = []

    for event in events:
        if event.triggered:
            continue

        if event.year == current_year and event.month == current_month:
            triggered.append(event)

    return triggered


def calculate_event_repair_cost(
    event: ScheduledEvent,
    units_count: int,
    property_values: List[float]
) -> float:
    """
    Calculate total repair cost for an event.

    Args:
        event: The event to process
        units_count: Number of units
        property_values: List of property values

    Returns:
        Total repair cost
    """
    base_cost = event.impacts.get("repair_cost", 0)

    if event.scope == "portfolio":
        # Cost applies to all units
        return base_cost * units_count
    else:
        # Cost applies to single unit
        return base_cost


def calculate_insurance_payout(
    event: ScheduledEvent,
    repair_cost: float,
    property_value: float
) -> Tuple[float, int]:
    """
    Calculate insurance payout for an event.

    Args:
        event: The event
        repair_cost: Total repair cost
        property_value: Property value for deductible

    Returns:
        Tuple of (payout amount, delay months)
    """
    if not event.insurance_claim:
        return 0.0, 0

    coverage_pct = event.insurance_claim.get("coverage_pct", 0)
    deductible_pct = event.insurance_claim.get("deductible_pct", 0)
    delay_months = event.insurance_claim.get("payout_delay_months", 0)

    covered_amount = repair_cost * coverage_pct
    deductible = property_value * deductible_pct

    payout = max(0, covered_amount - deductible)

    return payout, delay_months


def process_event(
    event: ScheduledEvent,
    simulation_month: int,
    current_year: int,
    current_month: int,
    units_count: int,
    unit_ids: List[int],
    property_values: List[float]
) -> EventResult:
    """
    Process an event and calculate its impact.

    Args:
        event: The event to process
        simulation_month: Current simulation month
        current_year: Current year
        current_month: Current calendar month
        units_count: Number of units
        unit_ids: List of unit IDs
        property_values: List of property values

    Returns:
        EventResult with all impact details
    """
    # Determine affected units
    if event.scope == "portfolio":
        affected_units = unit_ids.copy()
    else:
        # Unit-specific event
        target_id = event.unit_id if event.unit_id is not None else 0
        affected_units = [target_id] if target_id in unit_ids else []

    # Calculate costs
    repair_cost = calculate_event_repair_cost(event, units_count, property_values)
    vacancy_months = event.impacts.get("vacancy_months", 0)

    # Total vacancy (multiply by affected units for portfolio events)
    total_vacancy = vacancy_months * len(affected_units)

    # Insurance payout (use average property value for deductible calculation)
    avg_value = sum(property_values) / len(property_values) if property_values else 0
    payout, delay = calculate_insurance_payout(event, repair_cost, avg_value)
    payout_month = simulation_month + delay if delay > 0 else simulation_month

    # Net cost after insurance
    net_cost = repair_cost - payout

    # Mark event as triggered
    event.triggered = True
    event.trigger_month = simulation_month

    return EventResult(
        event_name=event.name,
        simulation_month=simulation_month,
        year=current_year,
        month=current_month,
        affected_units=affected_units,
        total_repair_cost=repair_cost,
        total_vacancy_months=total_vacancy,
        insurance_payout=payout,
        insurance_payout_month=payout_month,
        net_cost=net_cost
    )


def get_active_effects(
    events: List[ScheduledEvent],
    simulation_month: int
) -> Dict[str, Any]:
    """
    Get active effects from previously triggered events.

    Args:
        events: List of all events
        simulation_month: Current simulation month

    Returns:
        Dict with active effects (ADR reduction, etc.)
    """
    adr_reduction = 0.0
    active_events = []

    for event in events:
        if not event.triggered:
            continue

        trigger_month = event.trigger_month
        recovery_months = event.impacts.get("recovery_months", 0)

        if recovery_months > 0:
            months_since = simulation_month - trigger_month
            if months_since < recovery_months:
                # Calculate declining impact
                remaining_pct = 1 - (months_since / recovery_months)
                reduction = event.impacts.get("adr_reduction_pct", 0) * remaining_pct
                adr_reduction += reduction
                active_events.append({
                    "name": event.name,
                    "remaining_months": recovery_months - months_since,
                    "current_adr_reduction": reduction
                })

    return {
        "adr_reduction_pct": adr_reduction,
        "active_events": active_events
    }


def get_pending_payouts(
    event_results: List[EventResult],
    simulation_month: int
) -> List[Dict[str, Any]]:
    """
    Get insurance payouts due this month.

    Args:
        event_results: List of processed event results
        simulation_month: Current simulation month

    Returns:
        List of payouts due this month
    """
    payouts = []

    for result in event_results:
        if result.insurance_payout > 0 and result.insurance_payout_month == simulation_month:
            payouts.append({
                "event_name": result.event_name,
                "payout_amount": result.insurance_payout
            })

    return payouts


def validate_events_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate events configuration.

    Args:
        config: Engine configuration

    Returns:
        List of validation issues
    """
    issues = []
    events_cfg = config.get("events", {})

    if not events_cfg.get("enabled", False):
        return issues

    scenarios = events_cfg.get("scenarios", [])

    for i, scenario in enumerate(scenarios):
        name = scenario.get("name", f"Scenario {i}")

        # Check required fields
        if "year" not in scenario:
            issues.append(f"{name}: Missing 'year' field")
        if "month" not in scenario:
            issues.append(f"{name}: Missing 'month' field")

        # Check month validity
        month = scenario.get("month", 0)
        if month < 1 or month > 12:
            issues.append(f"{name}: Month {month} must be 1-12")

        # Check type validity
        event_type = scenario.get("type", "")
        valid_types = ["minor", "moderate", "major", "catastrophic"]
        if event_type not in valid_types:
            issues.append(f"{name}: Type '{event_type}' not in {valid_types}")

        # Check scope
        scope = scenario.get("scope", "")
        if scope not in ["unit", "portfolio"]:
            issues.append(f"{name}: Scope must be 'unit' or 'portfolio'")

        # Check unit_id for unit-scope events
        if scope == "unit" and scenario.get("unit_id") is None:
            issues.append(f"{name}: Unit-scope event missing 'unit_id'")

    return issues


def summarize_events(events: List[ScheduledEvent]) -> List[Dict[str, Any]]:
    """
    Create summary of scheduled events for display.

    Args:
        events: List of scheduled events

    Returns:
        List of event summaries
    """
    summaries = []

    # Sort by year, then month
    sorted_events = sorted(events, key=lambda e: (e.year, e.month))

    for event in sorted_events:
        summary = {
            "name": event.name,
            "type": event.event_type,
            "year": event.year,
            "month": event.month,
            "scope": event.scope,
            "repair_cost": event.impacts.get("repair_cost", 0),
            "vacancy_months": event.impacts.get("vacancy_months", 0),
            "adr_reduction": event.impacts.get("adr_reduction_pct", 0),
            "has_insurance": event.insurance_claim is not None,
            "description": event.description,
            "triggered": event.triggered
        }
        summaries.append(summary)

    return summaries


def create_event(
    name: str,
    event_type: str,
    year: int,
    month: int,
    scope: str = "unit",
    unit_id: int = None,
    repair_cost: float = 0,
    vacancy_months: int = 0,
    adr_reduction_pct: float = 0,
    recovery_months: int = 0,
    insurance_coverage: float = 0,
    insurance_deductible: float = 0.02,
    insurance_delay: int = 4,
    description: str = ""
) -> Dict[str, Any]:
    """
    Helper function to create an event configuration.

    Args:
        name: Event name
        event_type: minor/moderate/major/catastrophic
        year: Year event occurs
        month: Month event occurs (1-12)
        scope: unit or portfolio
        unit_id: Unit ID for unit-scope events
        repair_cost: Cost of repairs
        vacancy_months: Months of lost revenue
        adr_reduction_pct: Temporary ADR reduction
        recovery_months: Months for ADR to recover
        insurance_coverage: Insurance coverage percentage
        insurance_deductible: Deductible as percentage of value
        insurance_delay: Months until insurance payout
        description: Event description

    Returns:
        Event configuration dict
    """
    event = {
        "name": name,
        "type": event_type,
        "year": year,
        "month": month,
        "scope": scope,
        "impacts": {
            "repair_cost": repair_cost,
            "vacancy_months": vacancy_months,
        },
        "description": description
    }

    if unit_id is not None:
        event["unit_id"] = unit_id

    if adr_reduction_pct > 0:
        event["impacts"]["adr_reduction_pct"] = adr_reduction_pct
        event["impacts"]["recovery_months"] = recovery_months

    if insurance_coverage > 0:
        event["insurance_claim"] = {
            "coverage_pct": insurance_coverage,
            "deductible_pct": insurance_deductible,
            "payout_delay_months": insurance_delay
        }

    return event
