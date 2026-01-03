"""
Simple test runner for CapEx tests (no pytest required).
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

from capex import (
    get_capex_config,
    is_capex_schedule_enabled,
    get_systems_config,
    initialize_unit_systems,
    get_system_status,
    get_unit_capex_status,
    age_systems,
    check_replacements_needed,
    process_replacements,
    calculate_annual_capex_budget,
    calculate_portfolio_capex_status,
    validate_capex_config,
    get_replacement_schedule,
    summarize_systems,
    DEFAULT_SYSTEMS,
)


def test_default_systems():
    """Default systems exist with correct structure."""
    assert len(DEFAULT_SYSTEMS) == 6
    assert "hvac" in DEFAULT_SYSTEMS
    assert "roof" in DEFAULT_SYSTEMS
    assert "appliances" in DEFAULT_SYSTEMS
    assert "flooring" in DEFAULT_SYSTEMS
    assert "furniture" in DEFAULT_SYSTEMS
    assert "water_heater" in DEFAULT_SYSTEMS

    assert DEFAULT_SYSTEMS["hvac"]["lifespan_years"] == 15
    assert DEFAULT_SYSTEMS["hvac"]["replacement_cost"] == 12000
    print("OK test_default_systems")


def test_get_capex_config_disabled():
    """CapEx disabled by default."""
    config = {}
    capex_cfg = get_capex_config(config)
    assert capex_cfg["enabled"] is False
    assert len(capex_cfg["systems"]) == 6  # Uses defaults
    print("OK test_get_capex_config_disabled")


def test_get_capex_config_enabled():
    """Get CapEx config when enabled."""
    config = {
        "capex_schedule": {
            "enabled": True,
            "systems": {
                "hvac": {"lifespan_years": 20, "replacement_cost": 15000}
            }
        }
    }
    capex_cfg = get_capex_config(config)
    assert capex_cfg["enabled"] is True
    assert capex_cfg["systems"]["hvac"]["lifespan_years"] == 20
    print("OK test_get_capex_config_enabled")


def test_is_capex_schedule_enabled():
    """Check if CapEx schedule is enabled."""
    config_enabled = {"capex_schedule": {"enabled": True}}
    config_disabled = {"capex_schedule": {"enabled": False}}
    config_none = {}

    assert is_capex_schedule_enabled(config_enabled) is True
    assert is_capex_schedule_enabled(config_disabled) is False
    assert is_capex_schedule_enabled(config_none) is False
    print("OK test_is_capex_schedule_enabled")


def test_initialize_unit_systems():
    """Initialize systems for new unit."""
    config = {}
    systems = initialize_unit_systems(0, config)

    assert len(systems) == 6
    assert systems["hvac"] == 0  # All start at age 0
    assert systems["roof"] == 0
    print("OK test_initialize_unit_systems")


def test_initialize_unit_systems_with_age():
    """Initialize systems with initial age."""
    config = {}
    systems = initialize_unit_systems(0, config, initial_age_months=60)

    assert systems["hvac"] == 60
    assert systems["roof"] == 60
    print("OK test_initialize_unit_systems_with_age")


def test_get_system_status_new():
    """New system status."""
    config = {}
    status = get_system_status("hvac", 0, config)

    assert status.name == "hvac"
    assert status.age_months == 0
    assert status.lifespan_months == 180  # 15 years
    assert status.remaining_months == 180
    assert status.needs_replacement is False
    assert status.health_pct == 100.0
    print("OK test_get_system_status_new")


def test_get_system_status_mid_life():
    """Mid-life system status."""
    config = {}
    status = get_system_status("hvac", 90, config)  # 7.5 years

    assert status.age_months == 90
    assert status.remaining_months == 90
    assert status.needs_replacement is False
    assert 45 < status.health_pct < 55  # About 50%
    print("OK test_get_system_status_mid_life")


def test_get_system_status_expired():
    """Expired system status."""
    config = {}
    status = get_system_status("hvac", 200, config)  # Past 15 years

    assert status.remaining_months == 0
    assert status.needs_replacement is True
    assert status.health_pct == 0.0
    print("OK test_get_system_status_expired")


def test_get_unit_capex_status():
    """Get complete unit CapEx status."""
    config = {}
    system_ages = {
        "hvac": 170,  # Near end of life
        "roof": 0,    # New
        "appliances": 120,  # Past lifespan (10 years)
        "flooring": 84,  # Exactly at lifespan (7 years)
        "furniture": 60,  # At lifespan (5 years)
        "water_heater": 50,  # Mid-life
    }

    status = get_unit_capex_status(0, system_ages, config)

    assert status.unit_id == 0
    assert len(status.systems) == 6
    assert status.total_deferred_maintenance > 0  # Some systems past life
    print("OK test_get_unit_capex_status")


def test_age_systems():
    """Age all systems."""
    systems = {"hvac": 10, "roof": 20}
    aged = age_systems(systems, 12)

    assert aged["hvac"] == 22
    assert aged["roof"] == 32
    print("OK test_age_systems")


def test_check_replacements_needed():
    """Check which systems need replacement."""
    config = {}
    system_ages = {
        "hvac": 180,  # At lifespan
        "roof": 0,    # New
        "appliances": 120,  # At lifespan
        "flooring": 50,  # Mid-life
        "furniture": 60,  # At lifespan
        "water_heater": 50,  # Mid-life
    }

    needs = check_replacements_needed(system_ages, config)

    assert "hvac" in needs
    assert "appliances" in needs
    assert "furniture" in needs
    assert "roof" not in needs
    assert "water_heater" not in needs
    print("OK test_check_replacements_needed")


def test_process_replacements_with_reserve():
    """Process replacements with sufficient reserve."""
    config = {}
    system_ages = {
        "hvac": 180,  # Needs replacement ($12,000)
        "roof": 0,
        "appliances": 120,  # Needs replacement ($8,000)
        "flooring": 50,
        "furniture": 60,  # Needs replacement ($15,000)
        "water_heater": 50,
    }

    updated, remaining, replacements, deferred = process_replacements(
        unit_id=0,
        system_ages=system_ages,
        capex_reserve=50000,  # Enough for all
        current_month=36,
        current_year=3,
        config=config
    )

    assert len(replacements) == 3
    assert all(r.from_reserve for r in replacements)
    assert deferred == 0
    assert updated["hvac"] == 0  # Reset
    assert updated["appliances"] == 0
    assert updated["furniture"] == 0
    print("OK test_process_replacements_with_reserve")


def test_process_replacements_insufficient_reserve():
    """Defer replacements when reserve is low."""
    config = {}
    system_ages = {
        "hvac": 180,  # $12,000
        "roof": 0,
        "appliances": 120,  # $8,000
        "flooring": 50,
        "furniture": 60,  # $15,000
        "water_heater": 50,
    }

    updated, remaining, replacements, deferred = process_replacements(
        unit_id=0,
        system_ages=system_ages,
        capex_reserve=15000,  # Only enough for one
        current_month=36,
        current_year=3,
        config=config
    )

    paid = [r for r in replacements if r.from_reserve]
    deferred_items = [r for r in replacements if not r.from_reserve]

    assert len(paid) >= 1  # At least one should be paid
    assert len(deferred_items) >= 1  # At least one deferred
    assert deferred > 0
    print("OK test_process_replacements_insufficient_reserve")


def test_calculate_annual_capex_budget():
    """Calculate recommended annual budget."""
    config = {}
    budget = calculate_annual_capex_budget(1, config)

    # Sum of (cost / lifespan) for all systems
    expected = (
        12000 / 15 +  # HVAC
        25000 / 25 +  # Roof
        8000 / 10 +   # Appliances
        10000 / 7 +   # Flooring
        15000 / 5 +   # Furniture
        1500 / 12     # Water heater
    )
    assert abs(budget - expected) < 1
    print("OK test_calculate_annual_capex_budget")


def test_calculate_annual_capex_budget_multiple_units():
    """Budget scales with units."""
    config = {}
    budget_1 = calculate_annual_capex_budget(1, config)
    budget_3 = calculate_annual_capex_budget(3, config)

    assert budget_3 == budget_1 * 3
    print("OK test_calculate_annual_capex_budget_multiple_units")


def test_calculate_portfolio_capex_status():
    """Calculate portfolio-level CapEx status."""
    config = {}
    units_data = [
        {
            "unit_id": 0,
            "system_ages": {
                "hvac": 180,
                "roof": 0,
                "appliances": 120,
                "flooring": 50,
                "furniture": 60,
                "water_heater": 50,
            }
        },
        {
            "unit_id": 1,
            "system_ages": {
                "hvac": 0,
                "roof": 0,
                "appliances": 0,
                "flooring": 0,
                "furniture": 0,
                "water_heater": 0,
            }
        }
    ]

    status = calculate_portfolio_capex_status(units_data, config)

    assert status["total_deferred_maintenance"] > 0
    assert status["systems_needing_replacement"] >= 3  # From unit 0
    assert status["recommended_annual_budget"] > 0
    print("OK test_calculate_portfolio_capex_status")


def test_validate_capex_config_valid():
    """Valid config returns no issues."""
    config = {
        "capex_schedule": {
            "enabled": True,
            "systems": {
                "hvac": {"lifespan_years": 15, "replacement_cost": 12000}
            }
        }
    }
    issues = validate_capex_config(config)
    assert len(issues) == 0
    print("OK test_validate_capex_config_valid")


def test_validate_capex_config_disabled():
    """Disabled config skips validation."""
    config = {
        "capex_schedule": {
            "enabled": False,
            "systems": {"bad": {}}  # Invalid but should be skipped
        }
    }
    issues = validate_capex_config(config)
    assert len(issues) == 0
    print("OK test_validate_capex_config_disabled")


def test_validate_capex_config_missing_lifespan():
    """Missing lifespan is flagged."""
    config = {
        "capex_schedule": {
            "enabled": True,
            "systems": {
                "test": {"replacement_cost": 5000}
            }
        }
    }
    issues = validate_capex_config(config)
    assert len(issues) > 0
    assert any("lifespan" in issue.lower() for issue in issues)
    print("OK test_validate_capex_config_missing_lifespan")


def test_validate_capex_config_zero_cost():
    """Zero cost is flagged."""
    config = {
        "capex_schedule": {
            "enabled": True,
            "systems": {
                "test": {"lifespan_years": 10, "replacement_cost": 0}
            }
        }
    }
    issues = validate_capex_config(config)
    assert len(issues) > 0
    assert any("replacement_cost" in issue for issue in issues)
    print("OK test_validate_capex_config_zero_cost")


def test_get_replacement_schedule():
    """Get projected replacement schedule."""
    config = {}
    system_ages = {
        "hvac": 0,
        "roof": 0,
        "appliances": 0,
        "flooring": 0,
        "furniture": 0,
        "water_heater": 0,
    }

    schedule = get_replacement_schedule(0, system_ages, config, years_ahead=10)

    # Should have multiple replacements projected
    assert len(schedule) > 0

    # First should be furniture (5 year lifespan)
    first = schedule[0]
    assert first["system"] == "furniture"
    assert first["month_offset"] == 60  # 5 years
    print("OK test_get_replacement_schedule")


def test_get_replacement_schedule_with_overdue():
    """Schedule includes overdue systems."""
    config = {}
    system_ages = {
        "hvac": 200,  # Overdue
        "roof": 0,
        "appliances": 0,
        "flooring": 0,
        "furniture": 0,
        "water_heater": 0,
    }

    schedule = get_replacement_schedule(0, system_ages, config, years_ahead=5)

    # First should be overdue HVAC
    overdue = [s for s in schedule if s["status"] == "overdue"]
    assert len(overdue) >= 1
    assert overdue[0]["system"] == "hvac"
    print("OK test_get_replacement_schedule_with_overdue")


def test_summarize_systems():
    """Summarize configured systems."""
    config = {}
    summaries = summarize_systems(config)

    assert len(summaries) == 6
    hvac = next(s for s in summaries if s["name"] == "hvac")
    assert hvac["lifespan_years"] == 15
    assert hvac["replacement_cost"] == 12000
    assert hvac["annual_reserve_per_unit"] == 800  # 12000 / 15
    print("OK test_summarize_systems")


def test_system_lifecycle():
    """Test full system lifecycle."""
    config = {}

    # Start with new systems
    system_ages = initialize_unit_systems(0, config)

    # Age for 5 years (60 months)
    for _ in range(60):
        system_ages = age_systems(system_ages, 1)

    # Check furniture should now need replacement
    needs = check_replacements_needed(system_ages, config)
    assert "furniture" in needs

    # Process replacement
    updated, remaining, replacements, deferred = process_replacements(
        unit_id=0,
        system_ages=system_ages,
        capex_reserve=20000,
        current_month=60,
        current_year=5,
        config=config
    )

    # Furniture should be reset
    assert updated["furniture"] == 0
    assert any(r.system_name == "furniture" for r in replacements)
    print("OK test_system_lifecycle")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Running CapEx Tests")
    print("=" * 60 + "\n")

    tests = [
        test_default_systems,
        test_get_capex_config_disabled,
        test_get_capex_config_enabled,
        test_is_capex_schedule_enabled,
        test_initialize_unit_systems,
        test_initialize_unit_systems_with_age,
        test_get_system_status_new,
        test_get_system_status_mid_life,
        test_get_system_status_expired,
        test_get_unit_capex_status,
        test_age_systems,
        test_check_replacements_needed,
        test_process_replacements_with_reserve,
        test_process_replacements_insufficient_reserve,
        test_calculate_annual_capex_budget,
        test_calculate_annual_capex_budget_multiple_units,
        test_calculate_portfolio_capex_status,
        test_validate_capex_config_valid,
        test_validate_capex_config_disabled,
        test_validate_capex_config_missing_lifespan,
        test_validate_capex_config_zero_cost,
        test_get_replacement_schedule,
        test_get_replacement_schedule_with_overdue,
        test_summarize_systems,
        test_system_lifecycle,
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
