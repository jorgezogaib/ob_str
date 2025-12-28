# STR Investment Model - Validation & Anomaly Detection Recommendations

## Existing Validation Analysis

The current validation framework in `ui/components/kpi_cards.py:122-214` implements **5 basic checks across 4 categories**:

**Strengths:**
- Clean categorization (Portfolio, Cash Flow, Reserves, Mechanics)
- Distinguishes pass/warn states clearly
- Checks fundamental outcomes (properties acquired, debt payoff, no bankruptcies)

**Gaps:**
- **No validation of the journey, only the destination** - Missing checks for unrealistic intermediate states
- **No debt service coverage ratio (DSCR) monitoring** - Critical for real-world feasibility
- **No refinance pattern validation** - Could miss timing or LTV issues
- **No acquisition economics checks** - Doesn't verify properties meet cap rate targets
- **No cash flow stability metrics** - Single negative month is flagged, but chronic underperformance is not
- **No leverage monitoring** - Portfolio LTV could spike dangerously without detection
- **No reserve ratio checks** - Doesn't validate reserve levels are adequate for portfolio size
- **No growth rate sanity checks** - Could miss unrealistic scaling (e.g., acquiring 3 properties in one month)

---

## Recommended Validations

### Critical Priority

These validations catch fundamental modeling errors or scenarios that would **never work in reality**.

#### **Category: Debt Management**

**1. Maximum LTV Breach**
- **Detects**: Model allowing refinances that exceed lender limits or creating over-leveraged positions
- **Logic**:
  ```python
  max_ltv = portfolio_df['LTV %'].max()
  months_above_85 = portfolio_df[portfolio_df['LTV %'] > 85].shape[0]

  if max_ltv > 90:
      validations['Debt Management'].append(('warn', f'Dangerous LTV spike to {max_ltv:.1f}% (lenders cap at 80-85%)'))
  elif months_above_85 > 3:
      validations['Debt Management'].append(('warn', f'LTV above 85% for {months_above_85} months'))
  ```
- **Threshold**:
  - **FAIL**: Max LTV > 90% (impossible to obtain)
  - **WARN**: LTV > 85% for more than 3 consecutive months
- **Why It Matters**: No lender will refinance above ~80% LTV for investment properties. If model shows 90%+ LTV, there's a fundamental error in refinance logic. Even sustained 85%+ LTV indicates unrealistic leverage that wouldn't pass underwriting.

**2. DSCR Below Lender Minimum**
- **Detects**: Properties or portfolio operating with insufficient cash flow to service debt
- **Logic**:
  ```python
  # Per-property DSCR = NOI / Annual Debt Service
  # Portfolio DSCR = Total Operating Income / Total Debt Service (monthly)

  portfolio_df['DSCR'] = portfolio_df['Net Operating Income'] / portfolio_df['Debt Service'].replace(0, np.nan)
  below_threshold = portfolio_df[(portfolio_df['DSCR'] < 1.2) & (portfolio_df['Total Debt'] > 0)]

  if len(below_threshold) > 0:
      min_dscr = below_threshold['DSCR'].min()
      validations['Debt Management'].append(('warn', f'DSCR below 1.2 in {len(below_threshold)} months (min: {min_dscr:.2f})'))
  ```
- **Threshold**:
  - **FAIL**: DSCR < 1.0 (negative cash flow on debt service)
  - **WARN**: DSCR < 1.2 for any month with debt outstanding
- **Why It Matters**: Lenders require DSCR ≥ 1.25 for investment properties. Model showing sustained DSCR < 1.2 means refinances wouldn't be approved. DSCR < 1.0 means you can't cover debt payments - instant red flag.

**3. Debt Service Exceeds Operating Income**
- **Detects**: Portfolio is underwater on operations (paying more in debt than earning from properties)
- **Logic**:
  ```python
  underwater = portfolio_df[
      (portfolio_df['Debt Service'] > portfolio_df['Net Operating Income']) &
      (portfolio_df['Total Debt'] > 0)
  ]

  if len(underwater) > 6:
      validations['Debt Management'].append(('warn', f'Debt service exceeded NOI in {len(underwater)} months'))
  ```
- **Threshold**: More than 6 months where debt service > NOI
- **Why It Matters**: This means you're bleeding cash from operations every month. A few months during acquisition/stabilization is acceptable, but chronic negative operating cash flow means the BRRRR strategy isn't working.

#### **Category: Cash Flow**

**4. Chronic Operating Cash Shortfalls**
- **Detects**: Repeated inability to maintain operating cash buffer (different from current single-point check)
- **Logic**:
  ```python
  # Calculate required operating cash (should be in DataFrame as target)
  shortfall_months = portfolio_df[portfolio_df['Operating Cash'] < portfolio_df['Operating Cash'].mean() * 0.25]
  consecutive_shortfalls = count_max_consecutive(portfolio_df['Operating Cash'] < 0)

  if consecutive_shortfalls > 3:
      validations['Cash Flow'].append(('warn', f'{consecutive_shortfalls} consecutive months of negative operating cash'))
  elif len(shortfall_months) > 36:
      validations['Cash Flow'].append(('warn', f'Operating cash critically low in {len(shortfall_months)} months'))
  ```
- **Threshold**:
  - **WARN**: 3+ consecutive months of negative operating cash
  - **WARN**: Operating cash below 25% of average in >36 months
- **Why It Matters**: Negative operating cash means you're dipping into reserves or taking on credit card debt for daily operations. One month is a hiccup. Three consecutive months means something is structurally broken. Over 36 months across 30 years means chronic capital starvation.

**5. Total Liquidity Crisis**
- **Detects**: Complete depletion of all cash reserves (operating + emergency + CapEx)
- **Logic**:
  ```python
  crisis = portfolio_df[portfolio_df['Total Cash Reserves'] < 1000]

  if len(crisis) > 0:
      validations['Cash Flow'].append(('warn', f'Total cash reserves below $1,000 in {len(crisis)} months - bankruptcy risk'))
  ```
- **Threshold**: Total reserves < $1,000 in any month
- **Why It Matters**: If you hit near-zero liquidity, you can't pay bills, can't cover emergencies, and are one bad month from foreclosure. This should almost never happen if the model is working correctly.

#### **Category: Portfolio**

**6. Acquisition Economics Validation**
- **Detects**: Properties being purchased that don't meet minimum yield requirements
- **Logic**:
  ```python
  # This requires checking purchases against target yield
  # DataFrame should track purchase price and estimated NOI at acquisition

  target_yield = config['policies']['portfolio']['targetYieldUnlevered']  # e.g., 0.06

  # For each acquisition event, check if estimated cap rate >= target
  # This needs access to units_df or acquisition events

  failing_purchases = units_df[units_df['PurchaseCapRate'] < target_yield]

  if len(failing_purchases) > 0:
      validations['Portfolio'].append(('warn', f'{len(failing_purchases)} properties acquired below target {target_yield:.1%} cap rate'))
  ```
- **Threshold**: Any property purchased with cap rate < configured `targetYieldUnlevered`
- **Why It Matters**: If you're buying properties with cap rates below your minimum threshold, you're overpaying. This dilutes portfolio returns and violates acquisition discipline. The model should never buy a property that doesn't meet the cap rate filter.

**7. Unrealistic Acquisition Pace**
- **Detects**: Buying properties too fast (violates real-world transaction timelines and due diligence)
- **Logic**:
  ```python
  # Count acquisitions per quarter
  portfolio_df['Quarter'] = portfolio_df['Year'].astype(str) + '-Q' + ((portfolio_df['Month']-1)//3 + 1).astype(str)
  acquisitions_per_quarter = portfolio_df.groupby('Quarter')['Properties Owned'].apply(lambda x: (x.diff() > 0).sum())

  excessive_quarters = acquisitions_per_quarter[acquisitions_per_quarter > 1]

  if len(excessive_quarters) > 0:
      validations['Portfolio'].append(('warn', f'{len(excessive_quarters)} quarters with multiple acquisitions - unrealistic pace'))
  ```
- **Threshold**: More than 1 acquisition per quarter
- **Why It Matters**: Real STR acquisitions take 60-90 days (escrow, inspections, furnishing, permitting). Buying 2+ properties in a 3-month period is nearly impossible for a solo investor. Indicates model may be ignoring transaction friction.

---

### Important Priority

These validations signal **model issues or unrealistic assumptions** that would raise red flags for an experienced investor.

#### **Category: Debt Management**

**8. Refinance Timing Violations**
- **Detects**: Refinances happening too frequently or before seasoning requirements
- **Logic**:
  ```python
  # Track refinance events from units_df or when 'Refinance Proceeds' > 0
  refi_events = portfolio_df[portfolio_df['Refinance Proceeds'] > 0]

  # Check time between refinances on same property (requires property-level tracking)
  # Check if any refi happened within seasoningMonths of purchase

  if refi_events['Month'].diff().min() < config['banking']['seasoningMonths']:
      validations['Debt Management'].append(('warn', 'Refinance occurred before minimum seasoning period'))
  ```
- **Threshold**:
  - Any refi within `seasoningMonths` of purchase (typically 6-12 months)
  - More than 1 refi per property per 2 years
- **Why It Matters**: Lenders require seasoning (6-12 months of payment history). Violating this means model is allowing transactions that wouldn't be approved. Over-refinancing also racks up closing costs and resets amortization.

**9. Reserve Adequacy Ratio**
- **Detects**: Total reserves are insufficient for portfolio size and risk exposure
- **Logic**:
  ```python
  # Reserve adequacy = Total Reserves / (Monthly Fixed Costs * Properties Owned)
  # Want at least 3-6 months of coverage

  portfolio_df['MonthlyFixedCosts'] = (
      portfolio_df['HOA Fees'] +
      portfolio_df['Property Insurance'] +
      portfolio_df['Property Taxes']
  ) / 12

  portfolio_df['ReserveMonths'] = (
      portfolio_df['Total Cash Reserves'] /
      (portfolio_df['MonthlyFixedCosts'] * portfolio_df['Properties Owned'])
  ).replace([np.inf, -np.inf], 0)

  inadequate = portfolio_df[
      (portfolio_df['Properties Owned'] > 0) &
      (portfolio_df['ReserveMonths'] < 3)
  ]

  if len(inadequate) > 12:
      validations['Reserves'].append(('warn', f'Reserve coverage below 3 months in {len(inadequate)} months'))
  ```
- **Threshold**:
  - **WARN**: Reserves < 3 months of fixed costs for >12 months
  - **IDEAL**: 6+ months of coverage
- **Why It Matters**: Reserves are your safety net. With 5-7 properties, you need enough cash to cover multiple months of vacancies, repairs, and emergencies. Less than 3 months means one bad quarter could wipe you out.

**10. Cash Flow Volatility**
- **Detects**: Excessive swings in monthly cash flow (indicates instability or model errors)
- **Logic**:
  ```python
  # Calculate rolling 6-month standard deviation of Operating Cash Flow
  portfolio_df['CashFlowStdDev'] = portfolio_df['Cash Flow After Debt Service'].rolling(6).std()
  portfolio_df['CashFlowMean'] = portfolio_df['Cash Flow After Debt Service'].rolling(6).mean()

  # Coefficient of variation (CV) = StdDev / Mean
  portfolio_df['CV'] = portfolio_df['CashFlowStdDev'] / portfolio_df['CashFlowMean'].abs()

  high_volatility = portfolio_df[portfolio_df['CV'] > 1.0]

  if len(high_volatility) > 12:
      validations['Cash Flow'].append(('warn', f'High cash flow volatility (CV>1.0) in {len(high_volatility)} months'))
  ```
- **Threshold**: Coefficient of variation > 1.0 for more than 12 months
- **Why It Matters**: STR cash flow should stabilize as portfolio grows. Wild swings month-to-month indicate either aggressive refinancing, reserve sweeps causing instability, or missing stabilization logic. Lenders and investors hate volatility.

#### **Category: Reserves**

**11. Emergency Reserve Depletion Rate**
- **Detects**: Emergency reserves dropping rapidly (>30% decline month-over-month)
- **Logic**:
  ```python
  portfolio_df['EmergencyReservePctChange'] = portfolio_df['Emergency Reserve'].pct_change()

  steep_drops = portfolio_df[portfolio_df['EmergencyReservePctChange'] < -0.30]

  if len(steep_drops) > 0:
      max_drop = steep_drops['EmergencyReservePctChange'].min()
      validations['Reserves'].append(('warn', f'Emergency reserve dropped >30% in single month ({max_drop:.1%} max drop)'))
  ```
- **Threshold**: Single-month decline > 30%
- **Why It Matters**: Slow, controlled reserve drawdown is normal during acquisitions. A 30%+ drop in one month suggests an emergency (major repair) or a model error (sweep logic fired incorrectly, purchase reserves not held back properly).

**12. CapEx Reserve Ceiling Violations**
- **Detects**: CapEx reserves building up excessively (not being swept or deployed)
- **Logic**:
  ```python
  if config['banking']['enableCapexCeiling']:
      ceiling_months = config['banking']['capexCeilingMonths']
      # Calculate ceiling dynamically based on fixed costs
      # This column should exist: _CapExTarget

      excessive = portfolio_df[
          portfolio_df['_CapexBalance'] > portfolio_df['_CapExTarget'] * 1.5
      ]

      if len(excessive) > 6:
          validations['Reserves'].append(('warn', f'CapEx reserves 50% above ceiling in {len(excessive)} months - sweep not working'))
  ```
- **Threshold**: CapEx balance > 150% of ceiling for 6+ months
- **Why It Matters**: If you've enabled ceiling sweeps but reserves keep building, the sweep logic isn't working. This is dead capital that should be paying down debt or held in higher-yield savings.

#### **Category: Portfolio**

**13. Equity Growth Rate Anomaly**
- **Detects**: Equity growing too fast or too slow relative to portfolio value
- **Logic**:
  ```python
  # Year-over-year equity growth should roughly match: appreciation + principal paydown - cash-out refis
  portfolio_df_annual = portfolio_df[portfolio_df['Month'] == 12]
  portfolio_df_annual['EquityGrowthRate'] = portfolio_df_annual['Total Equity'].pct_change()

  # Expect 5-15% annual equity growth in most scenarios
  anomalies = portfolio_df_annual[
      (portfolio_df_annual['EquityGrowthRate'] < 0.02) |
      (portfolio_df_annual['EquityGrowthRate'] > 0.30)
  ]

  if len(anomalies) > 3:
      validations['Portfolio'].append(('warn', f'{len(anomalies)} years with unusual equity growth (<2% or >30%)'))
  ```
- **Threshold**: Annual equity growth < 2% or > 30% for more than 3 years
- **Why It Matters**: Equity should compound from appreciation (~3-4%), principal paydown, and operating income. Less than 2% growth suggests over-leveraging or value destruction. More than 30% could indicate unrealistic appreciation assumptions or modeling errors.

**14. Property Count Stagnation**
- **Detects**: Portfolio not growing despite having capital available
- **Logic**:
  ```python
  # Identify periods where properties owned is flat but cash reserves are high
  portfolio_df['PropertiesChange'] = portfolio_df['Properties Owned'].diff()

  max_units = config['policies']['portfolio']['maxUnits']
  stagnant = portfolio_df[
      (portfolio_df['Properties Owned'] < max_units) &
      (portfolio_df['PropertiesChange'] == 0) &
      (portfolio_df['Total Cash Reserves'] > 100000)
  ]

  # Count consecutive stagnant periods
  consecutive_stagnant = count_max_consecutive(
      (portfolio_df['Properties Owned'] < max_units) &
      (portfolio_df['PropertiesChange'] == 0) &
      (portfolio_df['Total Cash Reserves'] > 100000)
  )

  if consecutive_stagnant > 24:
      validations['Portfolio'].append(('warn', f'{consecutive_stagnant} months of stagnation with ample cash - acquisition logic issue'))
  ```
- **Threshold**: 24+ consecutive months with no growth, reserves > $100K, and properties < maxUnits
- **Why It Matters**: If you have $100K+ sitting idle and haven't hit your property cap, something is blocking acquisitions. Could be overly conservative purchase criteria, broken feeder prepayment logic, or missing refinance opportunities.

---

### Helpful Priority

These checks assist with **model refinement and parameter tuning** but aren't critical for validation.

#### **Category: Performance**

**15. Compound Annual Growth Rate (CAGR) - Portfolio Value**
- **Detects**: Whether overall portfolio performance meets investor expectations
- **Logic**:
  ```python
  initial_value = portfolio_df[portfolio_df['Properties Owned'] > 0].iloc[0]['Total Portfolio Value']
  final_value = portfolio_df.iloc[-1]['Total Portfolio Value']
  years = 30

  cagr = (final_value / initial_value) ** (1 / years) - 1

  if cagr < 0.08:
      validations['Performance'].append(('warn', f'Portfolio CAGR {cagr:.1%} below typical STR target (10-12%)'))
  else:
      validations['Performance'].append(('pass', f'Portfolio CAGR {cagr:.1%} - strong performance'))
  ```
- **Threshold**:
  - **WARN**: CAGR < 8%
  - **IDEAL**: CAGR > 10%
- **Why It Matters**: STR investors expect double-digit returns. Sub-8% CAGR means you're underperforming index funds. Useful for comparing scenarios but not a validation failure per se.

**16. Debt Payoff Efficiency**
- **Detects**: How quickly portfolio becomes debt-free relative to portfolio size
- **Logic**:
  ```python
  max_units = config['policies']['portfolio']['maxUnits']
  max_reached = portfolio_df[portfolio_df['Properties Owned'] == max_units]

  if len(max_reached) > 0:
      year_max_reached = max_reached.iloc[0]['Year']
      debt_free = portfolio_df[portfolio_df['Total Debt'] == 0]

      if len(debt_free) > 0:
          year_debt_free = debt_free.iloc[0]['Year']
          payoff_duration = year_debt_free - year_max_reached

          if payoff_duration > 15:
              validations['Performance'].append(('warn', f'{payoff_duration} years to pay off debt after reaching max units'))
          else:
              validations['Performance'].append(('pass', f'Debt paid off {payoff_duration} years after max units'))
  ```
- **Threshold**: > 15 years to pay off debt after reaching max portfolio
- **Why It Matters**: The BRRRR goal is to build equity quickly and then shift to debt payoff. If it takes 15+ years to clear debt after hitting max units, your leverage or prepayment strategy may be too conservative.

**17. Reserve Sweep Effectiveness**
- **Detects**: Whether reserve sweeps are meaningfully accelerating debt payoff
- **Logic**:
  ```python
  # Sum total swept over simulation
  total_rainy_sweep = portfolio_df['_RainySweep'].sum()
  total_capex_sweep = portfolio_df['_CapexSweep'].sum()
  total_swept = total_rainy_sweep + total_capex_sweep

  total_prepayment = portfolio_df['Principal Prepayment'].sum()
  sweep_contribution = total_swept / total_prepayment if total_prepayment > 0 else 0

  if sweep_contribution < 0.05:
      validations['Performance'].append(('warn', f'Reserve sweeps contributed only {sweep_contribution:.1%} of prepayments - consider tuning'))
  else:
      validations['Performance'].append(('pass', f'Sweeps contributed {sweep_contribution:.1%} of total prepayments'))
  ```
- **Threshold**: Sweeps < 5% of total prepayments
- **Why It Matters**: If you've enabled reserve sweeps but they're barely contributing, the ceilings may be too high or buffer percentages too generous. This is optimization guidance, not an error.

#### **Category: Mechanics**

**18. Feeder Property Consistency**
- **Detects**: Feeder property changing too frequently (inefficient prepayment focus)
- **Logic**:
  ```python
  # Count feeder changes
  portfolio_df['FeederChange'] = portfolio_df['_FeederIndex'].diff().abs() > 0
  feeder_changes = portfolio_df['FeederChange'].sum()

  properties_acquired = portfolio_df.iloc[-1]['Properties Owned']

  # Expect ~1 feeder change per acquisition cycle
  if feeder_changes > properties_acquired * 1.5:
      validations['Mechanics'].append(('warn', f'{feeder_changes} feeder changes for {properties_acquired} properties - excessive churn'))
  ```
- **Threshold**: Feeder changes > 1.5× number of properties
- **Why It Matters**: The feeder should shift when you do a cash-out refi or acquire a new property. Changing feeder 10 times for 5 properties suggests unstable logic (e.g., switching based on LTV fluctuations instead of refinance events).

**19. Refinance Proceeds Utilization**
- **Detects**: Refinance proceeds sitting idle instead of being deployed to acquisitions
- **Logic**:
  ```python
  # When a refi happens, proceeds should either:
  # 1. Fund a purchase within 1-3 months, OR
  # 2. Build up purchase reserves for next acquisition

  refi_months = portfolio_df[portfolio_df['Refinance Proceeds'] > 0]

  for idx in refi_months.index:
      refi_amount = portfolio_df.loc[idx, 'Refinance Proceeds']
      next_3_months = portfolio_df.loc[idx:idx+3]

      purchase_in_window = next_3_months['Property Purchase'].sum() > 0

      if not purchase_in_window and idx < len(portfolio_df) - 6:
          # Check if we're at max units (then it's OK)
          if portfolio_df.loc[idx, 'Properties Owned'] < max_units:
              # This is suspicious - money extracted but not deployed
              pass  # Would track this

  # Simplified version: check if long gaps between refi and purchase
  ```
- **Threshold**: Refinance proceeds > $50K sitting idle for >6 months
- **Why It Matters**: Cash-out refis have closing costs (~3% of loan). If you pull out $200K and let it sit for a year, you're paying interest on money you're not using. This indicates either over-extraction or broken acquisition timing.

**20. LTV Compression After Refi**
- **Detects**: Cash-out refis that don't materially reduce LTV on the feeder property
- **Logic**:
  ```python
  # After a refi, the feeder property should drop from ~75% LTV to ~75% LTV on NEW appraised value
  # But portfolio LTV should show meaningful extraction

  # This requires property-level LTV tracking
  # Flag if LTV only drops 5% after a refi (suggests minimal equity extraction)
  ```
- **Threshold**: LTV reduction < 5% after cash-out refi
- **Why It Matters**: If you refinance but LTV barely changes, you either didn't extract much equity (inefficient) or the property didn't appreciate enough (bad feeder choice). You paid closing costs for minimal benefit.

---

## Anomaly Detection Patterns

Beyond discrete validations, watch for these **dynamic patterns** that indicate model instability:

### 1. **Reserve Balance Cliff Drops**
- **Pattern**: Emergency or CapEx reserve drops >50% in a single month
- **Likely Causes**:
  - Sweep logic firing incorrectly
  - Missing purchase reserve hold-back
  - Catastrophic expense not properly modeled
- **Detection**: `portfolio_df['Emergency Reserve'].pct_change() < -0.50`

### 2. **LTV Spikes During Acquisition**
- **Pattern**: Portfolio LTV jumps 20+ percentage points in acquisition month
- **Likely Causes**:
  - Taking on too much debt for new property
  - Not accounting for down payment reducing debt
  - Refinance and purchase happening same month (double leverage)
- **Detection**: `portfolio_df['LTV %'].diff() > 20` during months with `Properties Owned` increase

### 3. **Negative Net Operating Income**
- **Pattern**: NOI goes negative (expenses > revenue)
- **Likely Causes**:
  - Occupancy rate too low
  - Expense inflation outpacing revenue growth
  - Too many vacant properties during acquisition ramp
- **Detection**: `portfolio_df['Net Operating Income'] < 0`

### 4. **Cash Flow Sign Flips (Whipsaw Pattern)**
- **Pattern**: Operating cash alternates positive/negative month-over-month
- **Likely Causes**:
  - Missing monthly smoothing (lumpy expenses like property taxes)
  - Aggressive sweep logic creating instability
  - Refinance timing creating cash injections followed by drain
- **Detection**: `(portfolio_df['Operating Cash'] > 0).astype(int).diff().abs().sum() > 50` (more than 50 sign changes in 360 months)

### 5. **Zombie Properties (Zero Revenue)**
- **Pattern**: Properties owned > 0 but monthly revenue = 0 for extended period
- **Likely Causes**:
  - Acquisition happened but property not marked as operational
  - Occupancy model broken
  - Missing revenue initialization after purchase
- **Detection**: `(portfolio_df['Properties Owned'] > 0) & (portfolio_df['Monthly Rental Income'] == 0)`

### 6. **Refinance Gridlock (No Refis for 5+ Years)**
- **Pattern**: Portfolio stuck at 2-3 properties for 60+ months despite having equity
- **Likely Causes**:
  - LTV trigger too conservative (waiting for 50% LTV instead of 75%)
  - Appreciation rate too low to hit refi thresholds
  - DSCR threshold too high (blocking refis despite positive cash flow)
- **Detection**: `(portfolio_df['Properties Owned'].diff() == 0) & (portfolio_df['Total Equity'] > portfolio_df['Total Debt'] * 0.5)` for 60+ consecutive months

### 7. **Cash Hoarding (Idle Reserves > 12 Months Expenses)**
- **Pattern**: Total reserves exceeding 12+ months of operating costs
- **Likely Causes**:
  - Reserve ceilings disabled or set too high
  - Sweep logic not triggering
  - Over-saving instead of deploying capital to prepayment or acquisitions
- **Detection**: `portfolio_df['Total Cash Reserves'] > (portfolio_df['Monthly Expenses'] * 12)` for extended periods

---

## Implementation Roadmap

**Phase 1: Critical Validations (Week 1)**
Implement in this order (highest impact first):
1. Maximum LTV Breach
2. DSCR Below Lender Minimum
3. Total Liquidity Crisis
4. Debt Service Exceeds Operating Income
5. Acquisition Economics Validation

**Phase 2: Important Validations (Week 2)**
6. Reserve Adequacy Ratio
7. Refinance Timing Violations
8. Chronic Operating Cash Shortfalls
9. Emergency Reserve Depletion Rate
10. Cash Flow Volatility

**Phase 3: Anomaly Detection (Week 3)**
- Implement pattern detection functions (separate module)
- Add anomaly summary section to UI
- Create time-series flags for visualization

**Phase 4: Helpful/Performance Metrics (Week 4)**
- CAGR calculation
- Debt payoff efficiency
- Sweep effectiveness
- Feeder consistency checks

**Phase 5: Refinement & Testing**
- Tune thresholds based on known-good scenarios
- Add configuration to disable specific validations
- Create validation profiles (conservative vs. aggressive)

---

## Technical Implementation Notes

### Required DataFrame Columns
Most validations can use existing columns, but consider adding:
- **`DSCR`**: Calculate as `Net Operating Income / Debt Service` (avoid div-by-zero)
- **`ReserveMonths`**: Total reserves / (monthly fixed costs × properties)
- **`PropertiesChange`**: Diff of `Properties Owned` to track acquisitions
- **`EmergencyReservePctChange`**: For tracking rapid depletion

### Helper Functions Needed

```python
def count_max_consecutive(series: pd.Series) -> int:
    """Count maximum consecutive True values in a boolean series."""
    return series.astype(int).groupby((~series).cumsum()).sum().max()

def calculate_dscr(noi: float, debt_service: float) -> float:
    """Safely calculate DSCR, handling zero debt service."""
    if debt_service == 0:
        return float('inf') if noi >= 0 else 0.0
    return noi / debt_service

def detect_anomaly_pattern(df: pd.DataFrame, pattern_name: str) -> pd.DataFrame:
    """Generic anomaly detector that returns flagged periods."""
    # Implementation per pattern type
    pass
```

### Validation Configuration

Consider adding a `validation_config` section to JSON:

```json
{
  "validations": {
    "ltv_max_warn": 85,
    "ltv_max_fail": 90,
    "dscr_min": 1.2,
    "reserve_months_min": 3,
    "cagr_target": 0.10,
    "enabled": [
      "ltv_breach",
      "dscr_check",
      "liquidity_crisis",
      // ... etc
    ]
  }
}
```

This allows users to tune sensitivity without changing code.

---

## Summary: Value Proposition

These validations transform the model from a calculation engine into a **decision-support system**:

1. **Catch Modeling Errors Early**: LTV breaches, DSCR violations, and acquisition economics checks surface bugs before you waste time analyzing flawed outputs.

2. **Build Investor Confidence**: When a scenario passes all Critical + Important validations, you know it's not just mathematically correct but also **operationally feasible**.

3. **Parameter Tuning Guidance**: Performance metrics and anomaly patterns show you *which knobs to turn* (e.g., "DSCR too low → lower leverage or improve occupancy").

4. **Scenario Comparison**: Run 10 scenarios and filter to only those that pass all validations. Now you're comparing realistic alternatives, not fantasy outcomes.

5. **Communication Tool**: Export validation results alongside scenarios to show partners/lenders that your projections are grounded in real-world constraints.

**Bottom Line**: These 20 validations + 7 anomaly patterns act as an experienced investor sitting on your shoulder, catching the "wait, that doesn't make sense" moments that spreadsheets miss.
