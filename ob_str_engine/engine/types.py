from dataclasses import dataclass
import pandas as pd

@dataclass
class SimulationResult:
    monthly: pd.DataFrame
    yearly: pd.DataFrame

@dataclass
class Unit:
    value: float
    debt: float
    monthly_payment: float
    rate: float
    last_refi_month: int