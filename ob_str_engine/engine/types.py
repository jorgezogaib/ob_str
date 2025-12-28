from dataclasses import dataclass, field
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