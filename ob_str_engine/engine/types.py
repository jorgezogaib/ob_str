from dataclasses import dataclass, field
from typing import Dict
import pandas as pd

@dataclass
class SimulationResult:
    monthly: pd.DataFrame
    yearly: pd.DataFrame
    units: pd.DataFrame  # Unit-level breakdown by month

@dataclass
class Unit:
    value: float
    debt: float
    monthly_payment: float
    rate: float
    last_refi_month: int
    unit_id: int = 0  # Unique identifier for feeder tracking (0-indexed)
    cash_invested: float = 0.0  # Down payment + closing costs (for return calculations)
    purchase_month: int = 0  # Month unit was purchased (for age tracking)

    # Phase 1.1: Market profile assignment
    market_profile: str = "orange_beach"  # Name reference to market_profiles config

    # Phase 1.4: Tax/Depreciation tracking
    purchase_price: float = 0.0  # Original purchase price (for depreciation basis)
    depreciation_basis: float = 0.0  # Building value (purchase_price * (1 - land_pct))
    accumulated_depreciation: float = 0.0  # Total depreciation taken to date

    # Phase 1.2: Insurance tracking
    in_flood_zone: bool = False  # Whether unit is in a flood zone
    insurance_claim_month: int = 0  # Month of last insurance claim (0 = no claim)
    insurance_surcharge_until: int = 0  # Month when surcharge ends

    # Phase 1.5: CapEx Schedule tracking
    system_ages: Dict[str, int] = field(default_factory=dict)  # System name -> age in months

    # Phase 1.6: Financing Dashboard tracking
    original_loan: float = 0.0  # Original loan amount at purchase
    interest_paid_to_date: float = 0.0  # Cumulative interest paid
    principal_paid_to_date: float = 0.0  # Cumulative principal paid