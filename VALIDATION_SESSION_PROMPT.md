# STR Investment Model - Add Comprehensive Validations & Anomaly Detection

## Context
I have a working STR (Short-Term Rental) investment simulation model built in Python with a Streamlit UI. The model simulates a 30-year portfolio growth strategy using cash-out refinancing (BRRRR method) to scale from 1 to N properties. I'm currently in a refinement phase where I'm tuning model parameters and need robust validation and anomaly detection to identify issues quickly.

## Current State
The model currently has 5 basic validations organized into 4 categories:
- **Portfolio**: Property acquisition count, debt payoff timeline
- **Cash Flow**: Operating cash shortfalls
- **Reserves**: Emergency reserve maintenance
- **Mechanics**: Feeder property tracking

**Location**: `ui/components/kpi_cards.py` in the `render_validation_summary()` function (lines 122-214)

The validation framework uses a categorized dictionary structure:
```python
validations = {
    'Portfolio': [('pass'/'warn', 'message'), ...],
    'Cash Flow': [...],
    'Reserves': [...],
    'Mechanics': [...]
}
```

## Your Task

**Phase 1: Review & Recommend**
1. Read and analyze the existing validation code in `ui/components/kpi_cards.py`
2. Review the portfolio DataFrame structure by examining sample output in `out/simulation_results_feeder.csv`
3. From the perspective of a **seasoned STR investor who has scaled multiple portfolios**, recommend:
   - Additional validation checks that would catch model errors or unrealistic scenarios
   - Anomaly detection rules for red flags in the simulation (e.g., sudden reserve depletion, suspicious LTV spikes, acquisition timing issues)
   - Performance metrics that would help me evaluate whether the model is producing realistic results

**Phase 2: Prioritize & Categorize**
Organize your recommendations into:
- **Critical**: Must-have validations that catch fundamental modeling errors
- **Important**: Strong signals of model issues or unrealistic assumptions
- **Helpful**: Nice-to-have checks for model refinement

Within each priority, categorize by: Portfolio, Cash Flow, Reserves, Debt Management, Performance, Mechanics

**Phase 3: Implementation Guidance**
For the top 5-10 recommendations, provide:
- Exact validation logic (Python pseudocode)
- Which DataFrame columns are needed
- Suggested threshold values based on real-world STR investing experience
- What it detects and why it matters

## Key Modeling Concepts to Validate Against

- **BRRRR Strategy**: Buy, Rehab, Rent, Refinance, Repeat
- **Feeder Property**: The property designated for aggressive prepayment to build equity for next cash-out refi
- **Cash-Out Refinance**: Extract equity when property LTV drops below trigger threshold (default 75%)
- **Reserve Sweeps**: Excess reserves above ceiling are deployed to debt prepayment
- **Liquidity Requirements**: Must maintain operating cash, emergency reserves, CapEx reserves, purchase reserves
- **Acquisition Criteria**: Properties must meet target yield (cap rate), DSCR thresholds

## Output Format

Please structure your response as:

```markdown
## Existing Validation Analysis
[Brief analysis of current 5 checks - strengths and gaps]

## Recommended Validations

### Critical Priority
**Category: [Portfolio/Cash Flow/etc.]**
1. **[Validation Name]**
   - **Detects**: [What problem this catches]
   - **Logic**: [Pseudocode or description]
   - **Threshold**: [Suggested values]
   - **Why It Matters**: [Real-world impact from investor perspective]

### Important Priority
[Same structure...]

### Helpful Priority
[Same structure...]

## Anomaly Detection Patterns
[Specific patterns to watch for - e.g., "Reserve balance drops >50% month-over-month"]

## Implementation Roadmap
[Suggested order to implement these validations]
```

## Constraints
- Validations must be computationally cheap (run on every simulation)
- Keep categorized structure for UI display
- Focus on actionable warnings, not noise
- Thresholds should reflect real-world STR investing, not theoretical finance

## Success Criteria
Your recommendations should help me:
1. Quickly identify when model parameters produce unrealistic scenarios
2. Catch mechanical bugs in acquisition, refinance, or reserve logic
3. Validate that the model behaves like a real STR portfolio would
4. Build confidence in the model's outputs before using it for decision-making

## Available DataFrame Columns
Based on `out/simulation_results_feeder.csv`, the portfolio DataFrame includes:
- **Time**: Year, Month, Period
- **Portfolio Metrics**: Properties Owned, Total Portfolio Value, Total Equity, Total Debt
- **Cash Positions**: Operating Cash, Emergency Reserve, CapEx Reserve, Total Cash Reserves
- **Cash Flows**: Monthly Revenue, Monthly Expenses, Operating Income, Debt Service, Net Cash Flow
- **Debt Metrics**: Total Debt, weighted average interest rate
- **Internal Tracking**: _FeederIndex, _RainyTarget, _CapExTarget, etc.

## Configuration Parameters
The model has the following tunable parameters (from `ui/components/config_editor.py`):

**Financial**
- startingCash, annualSavings, amortizationYears
- feederPrepaymentPct, savingsAccumulationPct

**Operations**
- adrBaseline2BR, occupancyBaseline, mgmtPct, capexPct
- hoaAnnual, hoaInflationRate, insuranceRate, propertyTaxRate
- liquidityReserveMultiplier

**Acquisition & Debt**
- downPaymentFirst, downPaymentSubsequent, closingCostPct, maxUnits
- targetYieldUnlevered, maxPostRefiLTV, refiCooldownYears, dscrThresholdForRefi
- refiCashoutStrategy, stopRefiAtMaxUnits, mortgageRate, refiRate

**Reserves & Banking**
- capexMonthsTarget, enableCapexCeiling, capexCeilingMonths
- rainyCoverageMonths, enableRainySweep, rainyBufferPct
- operatingCashMonths, purchaseReserveMonths
- seasoningMonths, refiLTVTrigger, cashoutCostPct, cashInterestRate

**Market**
- annualAppreciation, revenueInflationRate

---

**Begin with Phase 1**: Analyze the existing validations in `ui/components/kpi_cards.py` and provide your expert recommendations from the perspective of a seasoned STR investor.
