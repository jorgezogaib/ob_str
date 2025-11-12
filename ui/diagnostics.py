# ui/diagnostics.py
# Pure functions for CSV/DF diagnostics. No I/O side effects.

from typing import Tuple, Dict, Optional
import pandas as pd

PURCHASE_COL = "Purchase Out (Total)"
LR_COL = "Liquidity Ratio"
FREEZE_COL = "Freeze Flag"
DATE_COL = "YYYY-MM"

def first_purchase(df: pd.DataFrame) -> Optional[Tuple[int, str, float]]:
    """Return (idx, yyyymm, purchase_total) of first purchase row, else None."""
    mask = (df[PURCHASE_COL].astype(float) > 0)
    if not mask.any():
        return None
    idx = int(mask.idxmax())
    row = df.loc[idx]
    return idx, str(row[DATE_COL]), float(row[PURCHASE_COL])

def next_ready(df: pd.DataFrame, start_idx: Optional[int] = None) -> Optional[Tuple[int, str, float]]:
    """
    First month with Liquidity Ratio >= 1 AND Freeze Flag == 0
    after a given index (default: after first purchase).
    """
    if start_idx is None:
        fp = first_purchase(df)
        if fp is None:
            return None
        start_idx = fp[0]
    sub = df.loc[start_idx+1:].copy()
    mask = (sub[LR_COL].astype(float) >= 1.0) & (sub[FREEZE_COL].astype(float) == 0.0)
    if not mask.any():
        return None
    idx = int(mask.idxmax())
    row = sub.loc[idx]
    return idx, str(row[DATE_COL]), float(row[LR_COL])

def gate_breakdown(row: pd.Series) -> Dict[str, float]:
    """Return components that should sum to purchase total."""
    dp = float(row.get("Purchase: Down Payment", 0.0))
    cc = float(row.get("Purchase: Closing Costs", 0.0))
    ir = float(row.get("Purchase: Initial Rainy Funding", 0.0))
    total = float(row.get(PURCHASE_COL, 0.0))
    return {"down_payment": dp, "closing_costs": cc, "initial_rainy": ir, "total": total, "components_sum": dp + cc + ir}
