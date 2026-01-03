"""
Simple test runner for events tests (no pytest required).
"""
import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add paths
engine_path = str(Path(__file__).parent.parent / "ob_str_engine" / "engine")
sys.path.insert(0, engine_path)

from events import (
    get_events_config,
    is_events_enabled,
    get_scheduled_events,
    get_simulation_month,
    check_event_triggers,
    calculate_event_repair_cost,
    calculate_insurance_payout,
    process_event,
    get_active_effects,
    get_pending_payouts,
    validate_events_config,
    summarize_events,
    create_event,
    DEFAULT_EVENT_SCENARIOS,
    ScheduledEvent,
    EventResult,
)


def test_default_event_scenarios():
    """Default scenarios exist."""
    assert len(DEFAULT_EVENT_SCENARIOS) == 5
    names = [s["name"] for s in DEFAULT_EVENT_SCENARIOS]
    assert "Hurricane Hit" in names
    assert "Pandemic" in names
    print("OK test_default_event_scenarios")


def test_get_events_config_disabled():
    """Events disabled by default."""
    config = {}
    events_cfg = get_events_config(config)
    assert events_cfg["enabled"] is False
    assert events_cfg["scenarios"] == []
    print("OK test_get_events_config_disabled")


def test_get_events_config_enabled():
    """Get events config when enabled."""
    config = {
        "events": {
            "enabled": True,
            "scenarios": [{"name": "Test", "year": 1, "month": 1}]
        }
    }
    events_cfg = get_events_config(config)
    assert events_cfg["enabled"] is True
    assert len(events_cfg["scenarios"]) == 1
    print("OK test_get_events_config_enabled")


def test_is_events_enabled():
    """Check if events are enabled."""
    config_enabled = {"events": {"enabled": True}}
    config_disabled = {"events": {"enabled": False}}
    config_none = {}

    assert is_events_enabled(config_enabled) is True
    assert is_events_enabled(config_disabled) is False
    assert is_events_enabled(config_none) is False
    print("OK test_is_events_enabled")


def test_get_scheduled_events():
    """Get scheduled events from config."""
    config = {
        "events": {
            "enabled": True,
            "scenarios": [
                {
                    "name": "Test Event",
                    "type": "minor",
                    "year": 3,
                    "month": 6,
                    "scope": "unit",
                    "unit_id": 0,
                    "impacts": {"repair_cost": 5000}
                }
            ]
        }
    }
    events = get_scheduled_events(config)
    assert len(events) == 1
    assert isinstance(events[0], ScheduledEvent)
    assert events[0].name == "Test Event"
    assert events[0].year == 3
    assert events[0].month == 6
    print("OK test_get_scheduled_events")


def test_get_scheduled_events_disabled():
    """Returns empty list when disabled."""
    config = {"events": {"enabled": False, "scenarios": [{"name": "Test"}]}}
    events = get_scheduled_events(config)
    assert len(events) == 0
    print("OK test_get_scheduled_events_disabled")


def test_get_simulation_month():
    """Convert year/month to simulation month."""
    assert get_simulation_month(1, 1) == 1
    assert get_simulation_month(1, 12) == 12
    assert get_simulation_month(2, 1) == 13
    assert get_simulation_month(3, 6) == 30
    print("OK test_get_simulation_month")


def test_check_event_triggers():
    """Check which events should trigger."""
    events = [
        ScheduledEvent("Event1", "minor", 1, 1, "unit"),
        ScheduledEvent("Event2", "minor", 1, 6, "unit"),
        ScheduledEvent("Event3", "minor", 2, 1, "unit"),
    ]

    # Year 1, Month 1 should trigger Event1
    triggered = check_event_triggers(events, 1, 1)
    assert len(triggered) == 1
    assert triggered[0].name == "Event1"

    # Year 1, Month 6 should trigger Event2
    triggered = check_event_triggers(events, 1, 6)
    assert len(triggered) == 1
    assert triggered[0].name == "Event2"
    print("OK test_check_event_triggers")


def test_check_event_triggers_already_triggered():
    """Already triggered events don't trigger again."""
    event = ScheduledEvent("Event1", "minor", 1, 1, "unit")
    event.triggered = True

    triggered = check_event_triggers([event], 1, 1)
    assert len(triggered) == 0
    print("OK test_check_event_triggers_already_triggered")


def test_calculate_event_repair_cost_unit():
    """Unit-scope event cost."""
    event = ScheduledEvent("Test", "minor", 1, 1, "unit", unit_id=0)
    event.impacts = {"repair_cost": 5000}

    cost = calculate_event_repair_cost(event, 3, [700000, 700000, 700000])
    assert cost == 5000  # Only one unit
    print("OK test_calculate_event_repair_cost_unit")


def test_calculate_event_repair_cost_portfolio():
    """Portfolio-scope event cost multiplied by units."""
    event = ScheduledEvent("Test", "major", 1, 1, "portfolio")
    event.impacts = {"repair_cost": 10000}

    cost = calculate_event_repair_cost(event, 3, [700000, 700000, 700000])
    assert cost == 30000  # 10k * 3 units
    print("OK test_calculate_event_repair_cost_portfolio")


def test_calculate_insurance_payout_no_claim():
    """No insurance claim returns zero payout."""
    event = ScheduledEvent("Test", "minor", 1, 1, "unit")
    event.insurance_claim = None

    payout, delay = calculate_insurance_payout(event, 5000, 700000)
    assert payout == 0
    assert delay == 0
    print("OK test_calculate_insurance_payout_no_claim")


def test_calculate_insurance_payout_with_claim():
    """Insurance claim calculates payout correctly."""
    event = ScheduledEvent("Test", "major", 1, 1, "portfolio")
    event.insurance_claim = {
        "coverage_pct": 0.90,
        "deductible_pct": 0.02,
        "payout_delay_months": 4
    }

    # 50k repair, 90% covered = 45k, minus 2% of 700k = 14k deductible = 31k payout
    payout, delay = calculate_insurance_payout(event, 50000, 700000)
    expected_payout = (50000 * 0.90) - (700000 * 0.02)  # 45000 - 14000 = 31000
    assert payout == expected_payout
    assert delay == 4
    print("OK test_calculate_insurance_payout_with_claim")


def test_calculate_insurance_payout_small_claim():
    """Payout is zero when claim is less than deductible."""
    event = ScheduledEvent("Test", "minor", 1, 1, "unit")
    event.insurance_claim = {
        "coverage_pct": 0.90,
        "deductible_pct": 0.02,
        "payout_delay_months": 4
    }

    # 1k repair, 90% = 900, but deductible is 2% of 700k = 14k
    payout, delay = calculate_insurance_payout(event, 1000, 700000)
    assert payout == 0  # Claim less than deductible
    print("OK test_calculate_insurance_payout_small_claim")


def test_process_event():
    """Process an event and get result."""
    event = ScheduledEvent("Test Event", "minor", 1, 1, "unit", unit_id=0)
    event.impacts = {"repair_cost": 5000, "vacancy_months": 1}

    result = process_event(
        event=event,
        simulation_month=1,
        current_year=1,
        current_month=1,
        units_count=2,
        unit_ids=[0, 1],
        property_values=[700000, 800000]
    )

    assert isinstance(result, EventResult)
    assert result.event_name == "Test Event"
    assert result.total_repair_cost == 5000
    assert result.affected_units == [0]
    assert event.triggered is True
    print("OK test_process_event")


def test_process_event_portfolio():
    """Process a portfolio-scope event."""
    event = ScheduledEvent("Hurricane", "catastrophic", 1, 1, "portfolio")
    event.impacts = {"repair_cost": 25000, "vacancy_months": 2}

    result = process_event(
        event=event,
        simulation_month=1,
        current_year=1,
        current_month=1,
        units_count=3,
        unit_ids=[0, 1, 2],
        property_values=[700000, 700000, 700000]
    )

    assert result.total_repair_cost == 75000  # 25k * 3 units
    assert result.affected_units == [0, 1, 2]
    assert result.total_vacancy_months == 6  # 2 months * 3 units
    print("OK test_process_event_portfolio")


def test_get_active_effects():
    """Get active effects from triggered events."""
    event = ScheduledEvent("Pandemic", "major", 1, 1, "portfolio")
    event.impacts = {"adr_reduction_pct": 0.30, "recovery_months": 18}
    event.triggered = True
    event.trigger_month = 1

    # 9 months later, should be half recovered
    effects = get_active_effects([event], 10)

    assert effects["adr_reduction_pct"] > 0
    assert effects["adr_reduction_pct"] < 0.30  # Partially recovered
    assert len(effects["active_events"]) == 1
    print("OK test_get_active_effects")


def test_get_active_effects_fully_recovered():
    """No effects after full recovery."""
    event = ScheduledEvent("Pandemic", "major", 1, 1, "portfolio")
    event.impacts = {"adr_reduction_pct": 0.30, "recovery_months": 12}
    event.triggered = True
    event.trigger_month = 1

    # 24 months later, should be fully recovered
    effects = get_active_effects([event], 25)

    assert effects["adr_reduction_pct"] == 0
    assert len(effects["active_events"]) == 0
    print("OK test_get_active_effects_fully_recovered")


def test_get_pending_payouts():
    """Get insurance payouts due this month."""
    results = [
        EventResult("Event1", 1, 1, 1, [0], 50000, 2, 30000, 5, 20000),  # Payout at month 5
        EventResult("Event2", 1, 1, 1, [0], 10000, 0, 0, 1, 10000),  # No payout
        EventResult("Event3", 3, 1, 3, [0], 20000, 1, 15000, 7, 5000),  # Payout at month 7
    ]

    payouts_month_5 = get_pending_payouts(results, 5)
    assert len(payouts_month_5) == 1
    assert payouts_month_5[0]["payout_amount"] == 30000

    payouts_month_7 = get_pending_payouts(results, 7)
    assert len(payouts_month_7) == 1
    assert payouts_month_7[0]["payout_amount"] == 15000

    payouts_month_1 = get_pending_payouts(results, 1)
    assert len(payouts_month_1) == 0
    print("OK test_get_pending_payouts")


def test_validate_events_config_valid():
    """Valid config returns no issues."""
    config = {
        "events": {
            "enabled": True,
            "scenarios": [
                {
                    "name": "Test",
                    "type": "minor",
                    "year": 1,
                    "month": 6,
                    "scope": "unit",
                    "unit_id": 0
                }
            ]
        }
    }
    issues = validate_events_config(config)
    assert len(issues) == 0
    print("OK test_validate_events_config_valid")


def test_validate_events_config_disabled():
    """Disabled config skips validation."""
    config = {
        "events": {
            "enabled": False,
            "scenarios": [{"name": "Bad Event"}]  # Missing required fields
        }
    }
    issues = validate_events_config(config)
    assert len(issues) == 0  # Skipped because disabled
    print("OK test_validate_events_config_disabled")


def test_validate_events_config_missing_year():
    """Missing year is flagged."""
    config = {
        "events": {
            "enabled": True,
            "scenarios": [{"name": "Test", "month": 1}]
        }
    }
    issues = validate_events_config(config)
    assert len(issues) > 0
    assert any("year" in issue.lower() for issue in issues)
    print("OK test_validate_events_config_missing_year")


def test_validate_events_config_invalid_month():
    """Invalid month is flagged."""
    config = {
        "events": {
            "enabled": True,
            "scenarios": [{"name": "Test", "year": 1, "month": 13}]
        }
    }
    issues = validate_events_config(config)
    assert len(issues) > 0
    assert any("month" in issue.lower() for issue in issues)
    print("OK test_validate_events_config_invalid_month")


def test_validate_events_config_invalid_type():
    """Invalid type is flagged."""
    config = {
        "events": {
            "enabled": True,
            "scenarios": [{"name": "Test", "year": 1, "month": 1, "type": "invalid"}]
        }
    }
    issues = validate_events_config(config)
    assert len(issues) > 0
    assert any("type" in issue.lower() for issue in issues)
    print("OK test_validate_events_config_invalid_type")


def test_validate_events_config_unit_scope_no_id():
    """Unit-scope without unit_id is flagged."""
    config = {
        "events": {
            "enabled": True,
            "scenarios": [{"name": "Test", "year": 1, "month": 1, "scope": "unit"}]
        }
    }
    issues = validate_events_config(config)
    assert len(issues) > 0
    assert any("unit_id" in issue.lower() for issue in issues)
    print("OK test_validate_events_config_unit_scope_no_id")


def test_summarize_events():
    """Create event summary."""
    events = [
        ScheduledEvent("Event1", "minor", 1, 1, "unit", unit_id=0),
        ScheduledEvent("Event2", "major", 2, 6, "portfolio"),
    ]
    events[0].impacts = {"repair_cost": 5000}
    events[1].impacts = {"repair_cost": 50000, "vacancy_months": 2}

    summaries = summarize_events(events)
    assert len(summaries) == 2
    assert summaries[0]["name"] == "Event1"  # Sorted by year, month
    assert summaries[1]["name"] == "Event2"
    print("OK test_summarize_events")


def test_create_event():
    """Create event configuration."""
    event = create_event(
        name="Hurricane",
        event_type="catastrophic",
        year=3,
        month=9,
        scope="portfolio",
        repair_cost=50000,
        vacancy_months=2,
        adr_reduction_pct=0.10,
        recovery_months=6,
        insurance_coverage=0.90,
        insurance_deductible=0.02,
        insurance_delay=4,
        description="Major hurricane"
    )

    assert event["name"] == "Hurricane"
    assert event["type"] == "catastrophic"
    assert event["year"] == 3
    assert event["month"] == 9
    assert event["scope"] == "portfolio"
    assert event["impacts"]["repair_cost"] == 50000
    assert event["impacts"]["vacancy_months"] == 2
    assert event["impacts"]["adr_reduction_pct"] == 0.10
    assert event["insurance_claim"]["coverage_pct"] == 0.90
    print("OK test_create_event")


def test_create_event_minimal():
    """Create minimal event configuration."""
    event = create_event(
        name="Minor Repair",
        event_type="minor",
        year=2,
        month=6,
        scope="unit",
        unit_id=0,
        repair_cost=1500
    )

    assert event["name"] == "Minor Repair"
    assert event["unit_id"] == 0
    assert "insurance_claim" not in event
    print("OK test_create_event_minimal")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Running Events Tests")
    print("=" * 60 + "\n")

    tests = [
        test_default_event_scenarios,
        test_get_events_config_disabled,
        test_get_events_config_enabled,
        test_is_events_enabled,
        test_get_scheduled_events,
        test_get_scheduled_events_disabled,
        test_get_simulation_month,
        test_check_event_triggers,
        test_check_event_triggers_already_triggered,
        test_calculate_event_repair_cost_unit,
        test_calculate_event_repair_cost_portfolio,
        test_calculate_insurance_payout_no_claim,
        test_calculate_insurance_payout_with_claim,
        test_calculate_insurance_payout_small_claim,
        test_process_event,
        test_process_event_portfolio,
        test_get_active_effects,
        test_get_active_effects_fully_recovered,
        test_get_pending_payouts,
        test_validate_events_config_valid,
        test_validate_events_config_disabled,
        test_validate_events_config_missing_year,
        test_validate_events_config_invalid_month,
        test_validate_events_config_invalid_type,
        test_validate_events_config_unit_scope_no_id,
        test_summarize_events,
        test_create_event,
        test_create_event_minimal,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"FAIL {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR {test.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)
