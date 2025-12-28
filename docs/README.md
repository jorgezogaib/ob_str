# OB STR Engine v2.3 — Technical Reference Manual

This document is the single source of truth for how the refactored modular engine works.  
It is written for developers (including future Grok) who need to understand interconnections and safely modify behavior.

## Current Status — November 2025
- Config file: `ob_str_engine/OB_STR_ENGINE_V2_3.json`
- Permanent one-word runner: `obrun` → instantly generates fresh dated CSVs in `out/`
- All obsolete folders removed (archive/, runner/, golden/, tools/, etc.)
- Engine is minimal, pristine, and fully functional

## How to Run Forever

``bash
obrun
→ Instantly creates:

out/OB_STR_V2_3_Monthly_YYYY-MM-DD.csv
out/OB_STR_V2_3_YearOverYear_YYYY-MM-DD.csv

(No long commands ever again.)

## Core Execution Flow (monthly loop in simulator.py)

1. Load JSON config → `engine/config.py`
2. Every month:
   - Add monthly savings to cash
   - Calculate gross revenue → `engine/revenue.py`
   - Calculate all expenses → `engine/expenses.py`
   - Service debt (fixed)
   - Calculate NOI and operating cash flow
   - Top up rainy-day reserve → `engine/reserves.py`
   - Run liquidity freeze check → `engine/liquidity.py`
   - Attempt refi cash-out → `engine/feeder.py` (attempt_refi_cashout)
   - If cash sufficient and not frozen → purchase next unit at parity price → `engine/acquisition.py`
   - Amortize all loans + apply 3% annual appreciation (monthly) → `engine/debt.py`
   - If at max units (7) → prepay surplus on lowest-LTV unit → `engine/feeder.py` (prepay_surplus)
   - Record row with 29 columns (exact original order) → `simulator.py`

## Critical Interconnections & Fragile Points

| Behavior                        | Primary File(s)                          | Key Variables / Functions                                  | If you change this → check these side effects |
|--------------------------------|------------------------------------------|-------------------------------------------------------------|------------------------------------------------|
| Purchase price (parity)        | acquisition.py                           | calculate_parity_price()                                    | Affects liquidity freeze, purchase timing, TotalValue curve |
| Liquidity freeze (blocks buys) | liquidity.py                             | liquidity_check()                                           | Uses crude 5% proxy of property value for fixed costs — very sensitive |
| Refi cash-out trigger          | feeder.py                                | attempt_refi_cashout()                                      | Uses lowest LTV unit, 75% trigger, 3-year cooldown, 3% closing cost |
| Surplus prepay when at 7 units | feeder.py                                | prepay_surplus()                                            | Targets lowest LTV unit — directly affects final debt level |
| Rainy-day reserve target       | reserves.py                              | update_rainy_day_reserve()                                  | 6 × estimated fixed monthly costs |
| Revenue growth                 | revenue.py + market.revenueInflationRate | get_adr_for_year()                                          | 4% annual on base ADR of $425 |
| HOA inflation                  | operations.hoaInflationRate = 4%         | Applied in expenses.py and acquisition.py (must match)      | Must be inflated in both places or parity price explodes/implodes |
| Property appreciation         | market.annualAppreciation = 3%           | Applied monthly in simulator.py                             | Compounded monthly (correct) |

## Safe Ways to Modify Common Levers

| Desired change                    | Where to change                                    | What else you MUST update |
|-----------------------------------|----------------------------------------------------|---------------------------|
| Change purchase mortgage rate     | constants.debt.mortgageRate                        | None — automatically used in pmt() |
| Change refi rate                  | constants.debt.refiRate                            | None |
| Change max units                  | policies.portfolio.maxUnits                        | None |
| Change down payment % (first)     | constants.acquisition.downPaymentFirst             | None |
| Change down payment % (subsequent)| constants.acquisition.downPaymentSubsequent        | None |
| Change refi LTV trigger           | banking.refiLTVTrigger                             | None |
| Change refi closing cost %        | banking.cashoutCostPct                             | None |
| Change revenue growth             | market.revenueInflationRate                        | None (automatically used in get_adr_for_year) |
| Change HOA growth                 | operations.hoaInflationRate                        | MUST also update acquisition.py to inflate HOA in parity price (current bug fixed in v2.3) |
| Change rainy-day coverage         | banking.rainyCoverageMonths                        | None |

## Another way to say Safe Levers (Change in JSON Only — No Code Touch Required)

| Desired Change      | JSON Path                                           |
|---------------------|-----------------------------------------------------|
| Mortgage rate       | `constants.debt.mortgageRate`                       |
| Refi rate           | `constants.debt.refiRate`                           |
| Max units           | `policies.portfolio.maxUnits`                       |
| Down payment %      | `constants.acquisition.downPaymentFirst/Subsequent` |
| Refi LTV trigger    | `banking.refiLTVTrigger`                            |
| Refi closing cost   | `banking.cashoutCostPct`                            |
| Revenue growth      | `market.revenueInflationRate`                       |
| HOA inflation       | `operations.hoaInflationRate`                       |
| Rainy-day coverage  | `banking.rainyCoverageMonths`                       |

## Canonical Programmatic Entry Point

``python
from ob_str_engine.engine.simulator import simulate
from pathlib import Path

result = simulate(Path("ob_str_engine/OB_STR_ENGINE_V2_3.json"))
### result.monthly → pandas DataFrame
### result.yearly  → pandas DataFrame (currently empty)

## File-by-File Responsibility Matrix

| File                        | Owns                                               | Must stay in sync with |
|-----------------------------|----------------------------------------------------|------------------------|
| config.py                   | JSON loading only                                  | — |
| types.py                    | Unit dataclass, SimulationResult                   | simulator.py |
| revenue.py                  | Gross revenue, ADR inflation                       | acquisition.py (uses get_adr_for_year) |
| expenses.py                 | All operating expenses                             | simulator.py |
| acquisition.py              | Parity price calculation, purchase eligibility     | Must inflate HOA exactly like expenses.py |
| debt.py                     | pmt() and one-month amortization                   | feeder.py, simulator.py |
| reserves.py                 | Rainy-day top-up logic                             | simulator.py |
| liquidity.py                | Freeze flag calculation (very sensitive)           | simulator.py |
| feeder.py                   | Refi cash-out + surplus prepay                     | simulator.py |
| simulator.py                | Master loop, row recording, state management      | All other modules |

## Known “Gotchas” That Break Byte-for-Byte Parity

1. HOA inflation must be identical in expenses and parity price
2. Liquidity freeze uses crude 5% proxy — extremely sensitive
3. `prepay_surplus` always targets lowest-LTV unit
4. Appreciation is monthly-compounded (correct)
5. All monetary values rounded with `cents()` exactly as original



This document is the service manual.  
Keep it updated only when logic changes, never for cosmetic reasons.

## Current Clean Repo Contents
.github/workflows/ci.yml
.streamlit/config.toml
Makefile
README_RUN.txt
app.py
current_structure.txt
ob_str_engine/
├── init.py
├── engine/
│   ├── init.py
│   ├── acquisition.py
│   ├── config.py
│   ├── debt.py
│   ├── expenses.py
│   ├── feeder.py
│   ├── liquidity.py
│   ├── reserves.py
│   ├── revenue.py
│   ├── simulator.py
│   └── types.py
├── run_simulation.py          # (optional — can be ignored or fixed later)
├── OB_STR_ENGINE_V2_3.json     # ← THE CONFIG
├── init.py                     # (empty, harmless)
└── init.py
requirements.txt
tests/                          # full pytest suite
ui/                             # Streamlit UI
out/                            # ← fresh CSVs land here




— End of technical reference —