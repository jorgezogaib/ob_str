"""
Simulation Runner - Wrapper for running simulations with config overrides
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import sys

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ob_str_engine.engine.simulator import simulate
from ob_str_engine.engine.types import SimulationResult

# Import streamlit only if available (for error display)
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


@st.cache_data(show_spinner=False)
def get_base_config() -> Dict[str, Any]:
    """
    Load the base configuration from OB_STR_ENGINE_V2_3.json.

    Returns:
        Base engine configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If JSON is invalid
    """
    config_path = Path(__file__).parent.parent.parent / "ob_str_engine" / "OB_STR_ENGINE_V2_3.json"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Base configuration file not found at: {config_path}\n"
            f"Expected location: {config_path.absolute()}"
        )

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON in base config file: {config_path}\n"
            f"Error at line {e.lineno}, column {e.colno}: {e.msg}"
        ) from e
    except Exception as e:
        raise ValueError(f"Error loading base config: {e}") from e


def run_simulation(config: Dict[str, Any], years: int = 30) -> Optional[SimulationResult]:
    """
    Run simulation with the given config.

    Args:
        config: Configuration dictionary (will be written to temp file)
        years: Number of years to simulate (must be between 1 and 100)

    Returns:
        SimulationResult with monthly and units DataFrames, or None if simulation fails

    Note:
        Displays error messages in Streamlit UI if available and simulation fails
    """
    # Validate inputs
    if not isinstance(config, dict):
        error_msg = "Invalid configuration: must be a dictionary"
        if HAS_STREAMLIT and hasattr(st, 'error'):
            st.error(error_msg)
        else:
            print(f"ERROR: {error_msg}")
        return None

    if not isinstance(years, int) or years < 1 or years > 100:
        error_msg = f"Invalid years parameter: {years}. Must be between 1 and 100."
        if HAS_STREAMLIT and hasattr(st, 'error'):
            st.error(error_msg)
        else:
            print(f"ERROR: {error_msg}")
        return None

    temp_path = None
    try:
        # Write config to a temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(config, f, indent=2)
            temp_path = Path(f.name)

        # Run simulation with spinner if Streamlit available
        if HAS_STREAMLIT and hasattr(st, 'spinner'):
            with st.spinner(f"Running {years}-year simulation..."):
                result = simulate(temp_path, years=years)
        else:
            result = simulate(temp_path, years=years)

        return result

    except FileNotFoundError as e:
        error_msg = f"Configuration file error: {e}"
        if HAS_STREAMLIT and hasattr(st, 'error'):
            st.error(error_msg)
        else:
            print(f"ERROR: {error_msg}")
        return None
    except ValueError as e:
        error_msg = f"Invalid configuration: {e}"
        if HAS_STREAMLIT and hasattr(st, 'error'):
            st.error(error_msg)
        else:
            print(f"ERROR: {error_msg}")
        return None
    except Exception as e:
        error_msg = f"Simulation failed: {str(e)}"
        if HAS_STREAMLIT and hasattr(st, 'error'):
            st.error(error_msg)
            if hasattr(st, 'exception'):
                st.exception(e)  # Show full traceback in expander
        else:
            print(f"ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
        return None
    finally:
        # Clean up temp file
        if temp_path and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass  # Ignore cleanup errors


def config_to_form_values(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract form-editable values from config.

    Returns flat dict of form field values.
    """
    const = config.get("constants", {})
    fin = const.get("financial", {})
    ops = const.get("operations", {})
    acq = const.get("acquisition", {})
    debt = const.get("debt", {})
    reserves = const.get("reserves", {})
    market = config.get("market", {})
    banking = config.get("banking", {})
    policies = config.get("policies", {})
    portfolio = policies.get("portfolio", {})
    capital = policies.get("capitalAllocation", {})
    distribution = config.get("distribution", {})

    return {
        # Financial
        "startingCash": fin.get("startingCash", 5000.0),
        "annualSavings": fin.get("annualSavings", 50000.0),
        "amortizationYears": fin.get("amortizationYears", 30),

        # Operations
        "adrBaseline2BR": ops.get("adrBaseline2BR", 425.0),
        "occupancyBaseline": ops.get("occupancyBaseline", 0.78),
        "mgmtPct": ops.get("mgmtPct", 0.20),
        "capexPct": ops.get("capexPct", 0.10),
        "hoaAnnual": ops.get("hoaAnnual", 12800.0),
        "hoaInflationRate": ops.get("hoaInflationRate", 0.04),
        "insuranceRate": ops.get("insuranceRate", 0.033),
        "propertyTaxRate": ops.get("propertyTaxRate", 0.0055),
        "liquidityReserveMultiplier": ops.get("liquidityReserveMultiplier", 1.0),

        # Acquisition
        "downPaymentFirst": acq.get("downPaymentFirst", 0.20),
        "downPaymentSubsequent": acq.get("downPaymentSubsequent", 0.25),
        "closingCostPct": acq.get("closingCostPct", 0.03),
        "maxUnits": portfolio.get("maxUnits", 7),
        "targetYieldUnlevered": acq.get("targetYieldUnlevered", 0.065),
        "maxPostRefiLTV": acq.get("maxPostRefiLTV", 0.75),
        "refiCooldownYears": acq.get("refiCooldownYears", 3),
        "dscrThresholdForRefi": acq.get("dscrThresholdForRefi", 1.20),
        "refiCashoutStrategy": acq.get("refiCashoutStrategy", "max"),
        "stopRefiAtMaxUnits": portfolio.get("stopRefiAtMaxUnits", True),

        # Debt
        "mortgageRate": debt.get("mortgageRate", 0.0685),
        "refiRate": debt.get("refiRate", 0.05875),

        # Reserves
        "capexMonthsTarget": reserves.get("capexMonthsTarget", 6),
        "enableCapexCeiling": reserves.get("enableCapexCeiling", True),
        "capexCeilingMonths": reserves.get("capexCeilingMonths", 6),
        "enableRainySweep": reserves.get("enableRainySweep", True),
        "rainyBufferPct": reserves.get("rainyBufferPct", 1.2),
        "rainyCoverageMonths": banking.get("rainyCoverageMonths", 5),
        "operatingCashMonths": banking.get("operatingCashMonths", 1),
        "purchaseReserveMonths": banking.get("purchaseReserveMonths", 6),
        "seasoningMonths": banking.get("seasoningMonths", 6),
        "refiLTVTrigger": banking.get("refiLTVTrigger", 0.75),
        "cashoutCostPct": banking.get("cashoutCostPct", 0.03),
        "cashInterestRate": banking.get("cashInterestRate", 0.04),

        # Capital Allocation
        "feederPrepaymentPct": capital.get("feederPrepaymentPct", 0.70),
        "savingsAccumulationPct": capital.get("savingsAccumulationPct", 0.30),

        # Market
        "annualAppreciation": market.get("annualAppreciation", 0.03),
        "revenueInflationRate": market.get("revenueInflationRate", 0.04),

        # Distribution (preserve entire structure)
        "distribution": distribution,
    }


def form_values_to_config(form_values: Dict[str, Any], base_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convert form values back to full config structure.

    Args:
        form_values: Dict of form field values
        base_config: Base config to merge with (for fields not in form)

    Returns:
        Complete config dict
    """
    if base_config is None:
        base_config = get_base_config()

    # Deep copy base config
    config = json.loads(json.dumps(base_config))

    # Update values
    config["constants"]["financial"]["startingCash"] = form_values["startingCash"]
    config["constants"]["financial"]["annualSavings"] = form_values["annualSavings"]
    config["constants"]["financial"]["amortizationYears"] = form_values["amortizationYears"]

    config["constants"]["operations"]["adrBaseline2BR"] = form_values["adrBaseline2BR"]
    config["constants"]["operations"]["occupancyBaseline"] = form_values["occupancyBaseline"]
    config["constants"]["operations"]["mgmtPct"] = form_values["mgmtPct"]
    config["constants"]["operations"]["capexPct"] = form_values["capexPct"]
    config["constants"]["operations"]["hoaAnnual"] = form_values["hoaAnnual"]
    config["constants"]["operations"]["hoaInflationRate"] = form_values["hoaInflationRate"]
    config["constants"]["operations"]["insuranceRate"] = form_values["insuranceRate"]
    config["constants"]["operations"]["propertyTaxRate"] = form_values["propertyTaxRate"]
    config["constants"]["operations"]["liquidityReserveMultiplier"] = form_values.get("liquidityReserveMultiplier", 1.0)

    config["constants"]["acquisition"]["downPaymentFirst"] = form_values["downPaymentFirst"]
    config["constants"]["acquisition"]["downPaymentSubsequent"] = form_values["downPaymentSubsequent"]
    config["constants"]["acquisition"]["closingCostPct"] = form_values["closingCostPct"]
    config["constants"]["acquisition"]["targetYieldUnlevered"] = form_values["targetYieldUnlevered"]
    config["constants"]["acquisition"]["maxPostRefiLTV"] = form_values["maxPostRefiLTV"]
    config["constants"]["acquisition"]["refiCooldownYears"] = form_values["refiCooldownYears"]
    config["constants"]["acquisition"]["dscrThresholdForRefi"] = form_values["dscrThresholdForRefi"]
    config["constants"]["acquisition"]["refiCashoutStrategy"] = form_values["refiCashoutStrategy"]

    config["constants"]["debt"]["mortgageRate"] = form_values["mortgageRate"]
    config["constants"]["debt"]["refiRate"] = form_values["refiRate"]

    config["constants"]["reserves"]["capexMonthsTarget"] = form_values["capexMonthsTarget"]
    config["constants"]["reserves"]["enableCapexCeiling"] = form_values["enableCapexCeiling"]
    config["constants"]["reserves"]["capexCeilingMonths"] = form_values["capexCeilingMonths"]
    config["constants"]["reserves"]["enableRainySweep"] = form_values["enableRainySweep"]
    config["constants"]["reserves"]["rainyBufferPct"] = form_values["rainyBufferPct"]

    config["market"]["annualAppreciation"] = form_values["annualAppreciation"]
    config["market"]["revenueInflationRate"] = form_values["revenueInflationRate"]

    config["banking"]["rainyCoverageMonths"] = form_values["rainyCoverageMonths"]
    config["banking"]["operatingCashMonths"] = form_values["operatingCashMonths"]
    config["banking"]["purchaseReserveMonths"] = form_values["purchaseReserveMonths"]
    config["banking"]["seasoningMonths"] = form_values.get("seasoningMonths", 6)
    config["banking"]["refiLTVTrigger"] = form_values.get("refiLTVTrigger", 0.75)
    config["banking"]["cashoutCostPct"] = form_values.get("cashoutCostPct", 0.03)
    config["banking"]["cashInterestRate"] = form_values.get("cashInterestRate", 0.04)

    config["policies"]["portfolio"]["maxUnits"] = form_values["maxUnits"]
    config["policies"]["portfolio"]["stopRefiAtMaxUnits"] = form_values["stopRefiAtMaxUnits"]

    config["policies"]["capitalAllocation"]["feederPrepaymentPct"] = form_values["feederPrepaymentPct"]
    config["policies"]["capitalAllocation"]["savingsAccumulationPct"] = form_values["savingsAccumulationPct"]

    # Distribution (preserve entire structure from form values)
    if "distribution" in form_values:
        config["distribution"] = form_values["distribution"]

    return config
