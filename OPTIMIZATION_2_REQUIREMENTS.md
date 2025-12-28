# OPTIMIZATION 2: PREDICTIVE FEEDER SELECTION - REQUIREMENTS DOCUMENT

**Status:** Not Implemented (Alternative to Optimization 1)
**Priority:** Low (Research/Experimental)
**Estimated Complexity:** High
**Estimated Implementation Time:** 3-4 hours
**Risk Level:** Medium-High

---

## EXECUTIVE SUMMARY

### Current State (Optimization 1)
The feeder selection algorithm chooses which property to prepay based on **current state**:
- "Which property has the highest extractable equity RIGHT NOW?"
- If Property A can extract $350K today and Property B can extract $300K today, select Property A

### Proposed Future State (Optimization 2)
The feeder selection algorithm would choose based on **projected future state**:
- "Which property will enable the fastest next purchase?"
- Even if Property B has less extractable equity today, if it will be ready sooner (accounting for cooldown, prepayments, and appreciation), select Property B

### Business Justification
- Current approach is **reactive** (optimizes for current state)
- Predictive approach is **proactive** (optimizes for total time to purchase)
- May reduce time to reach 7 properties by 30-42 months (13-16% speed increase)
- Enables smarter capital deployment when multiple properties are near refi-ready status

---

## BUSINESS REQUIREMENTS

### BR-1: Selection Criterion
**Requirement:** Select the property that minimizes **total months until next purchase can occur**

**Calculation:**
```
For each eligible property:
  1. Calculate months until property is refi-eligible
     - Account for cooldown period remaining
     - Project future LTV accounting for prepayments and appreciation

  2. Calculate extractable equity when eligible
     - Use projected property value (with appreciation)
     - Use projected debt (with amortization and prepayments)

  3. Calculate capital gap
     - Total purchase cost (down payment + closing + reserves)
     - Minus: extractable equity from this property's refi
     - Minus: current savings account balance

  4. Calculate months to accumulate capital gap (if positive)
     - Based on monthly surplus and savings allocation %

  5. Total time = months_until_eligible + months_to_accumulate_gap

Select property with MINIMUM total time
```

### BR-2: Fallback Behavior
**Requirement:** If projection logic fails or produces invalid results, fall back to Optimization 1 behavior (highest extractable equity)

**Triggers for fallback:**
- No properties past cooldown or within projection window
- Projection calculations result in negative or infinite values
- All properties have identical total time (tie-breaking)

### BR-3: Projection Window
**Requirement:** Only consider properties that will be eligible within a reasonable timeframe

**Suggested constraint:** Only project forward 24 months maximum
- Properties requiring >24 months to become eligible should be excluded
- Prevents unrealistic long-term projections with compounding uncertainty

### BR-4: Consistency
**Requirement:** Use the same predictive selection logic for BOTH:
1. Prepayment targeting (which property to pay down this month)
2. Refinance execution (which property to refi for next purchase)

**Rationale:** Per user's feedback: "Prepayment targeting should also use the same logic. Prepayment is a precursor to refi, a part of the same tool."

---

## TECHNICAL REQUIREMENTS

### TR-1: Function Signature
**Location:** `ob_str_engine/engine/feeder.py`

**Function to replace:**
```python
def select_feeder(
    units: List[Unit],
    month_global: int,
    cooldown_months: int,
    for_refi: bool = True
) -> Optional[int]:
```

**New signature (same interface, different implementation):**
```python
def select_feeder(
    units: List[Unit],
    month_global: int,
    cooldown_months: int,
    for_refi: bool = True,
    # NEW PARAMETERS NEEDED:
    appreciation_rate: float,          # Annual appreciation (e.g., 0.06)
    mortgage_rate: float,              # Current mortgage rate for amortization
    current_savings: float,            # Current savings account balance
    monthly_surplus: float,            # Average monthly surplus available
    savings_allocation_pct: float,     # % of surplus going to savings
    purchase_cost_estimate: float,     # Estimated cost of next purchase
) -> Optional[int]:
```

**⚠️ BREAKING CHANGE:** Adding new required parameters will require updating all call sites in `simulator.py`

### TR-2: Required Projection Functions

Create new helper functions in `feeder.py`:

#### TR-2.1: Project Property Value
```python
def project_property_value(
    current_value: float,
    months_forward: int,
    annual_appreciation: float
) -> float:
    """
    Project future property value with appreciation.

    Returns:
        Projected value after N months of appreciation
    """
    monthly_rate = annual_appreciation / 12
    return current_value * ((1 + monthly_rate) ** months_forward)
```

#### TR-2.2: Project Property Debt
```python
def project_property_debt(
    current_debt: float,
    monthly_payment: float,
    mortgage_rate: float,
    monthly_prepayment: float,
    months_forward: int
) -> float:
    """
    Project future debt accounting for:
    - Regular amortization (monthly payment)
    - Prepayments (concentrated on this property)
    - Interest accrual

    Returns:
        Projected debt after N months
    """
    # Month-by-month simulation (not closed-form due to prepayments)
    debt = current_debt
    monthly_rate = mortgage_rate / 12

    for _ in range(months_forward):
        # Accrue interest
        interest = debt * monthly_rate

        # Apply payment (principal portion)
        principal = monthly_payment - interest
        debt -= principal

        # Apply prepayment (all goes to principal)
        debt -= monthly_prepayment

        # Stop if fully paid off
        if debt <= 0:
            return 0.0

    return max(0.0, debt)
```

#### TR-2.3: Calculate Months Until Eligible
```python
def calculate_months_until_eligible(
    unit: Unit,
    month_global: int,
    cooldown_months: int,
    ltv_threshold: float,
    monthly_prepayment: float,
    mortgage_rate: float,
    appreciation_rate: float,
    max_months: int = 24
) -> Optional[int]:
    """
    Calculate how many months until property is refi-eligible.

    A property is eligible when:
    1. Cooldown period has passed (months since last refi >= cooldown)
    2. LTV < threshold (typically 75%)

    Args:
        unit: The property to evaluate
        month_global: Current simulation month
        cooldown_months: Required months between refis
        ltv_threshold: Maximum LTV for refi eligibility
        monthly_prepayment: Prepayment amount this property receives
        mortgage_rate: Interest rate for debt projection
        appreciation_rate: Annual appreciation rate
        max_months: Maximum projection window

    Returns:
        Months until eligible, or None if not eligible within max_months
    """
    months_since_refi = month_global - unit.last_refi_month

    # Check each month forward
    for months_forward in range(max_months + 1):
        total_months_since_refi = months_since_refi + months_forward

        # Check cooldown
        if total_months_since_refi < cooldown_months:
            continue  # Still on cooldown

        # Project value and debt
        future_value = project_property_value(
            unit.value, months_forward, appreciation_rate
        )
        future_debt = project_property_debt(
            unit.debt, unit.monthly_payment, mortgage_rate,
            monthly_prepayment, months_forward
        )

        # Check LTV
        future_ltv = future_debt / future_value if future_value > 0 else 1.0
        if future_ltv < ltv_threshold:
            return months_forward  # This is when it becomes eligible

    return None  # Not eligible within projection window
```

#### TR-2.4: Calculate Total Time to Purchase
```python
def calculate_time_to_purchase(
    unit: Unit,
    month_global: int,
    cooldown_months: int,
    ltv_threshold: float,
    max_ltv_refi: float,
    cashout_cost_pct: float,
    monthly_prepayment: float,
    mortgage_rate: float,
    appreciation_rate: float,
    current_savings: float,
    monthly_surplus: float,
    savings_allocation_pct: float,
    purchase_cost: float,
    max_projection_months: int = 24
) -> Optional[float]:
    """
    Calculate total months until this property can enable a purchase.

    Returns:
        Total months, or None if property cannot enable purchase within window
    """
    # Step 1: Months until refi-eligible
    months_until_eligible = calculate_months_until_eligible(
        unit, month_global, cooldown_months, ltv_threshold,
        monthly_prepayment, mortgage_rate, appreciation_rate,
        max_projection_months
    )

    if months_until_eligible is None:
        return None  # Won't be eligible in time

    # Step 2: Calculate extractable equity when eligible
    future_value = project_property_value(
        unit.value, months_until_eligible, appreciation_rate
    )
    future_debt = project_property_debt(
        unit.debt, unit.monthly_payment, mortgage_rate,
        monthly_prepayment, months_until_eligible
    )

    extractable = (future_value * max_ltv_refi - future_debt) * (1 - cashout_cost_pct)
    extractable = max(0.0, extractable)

    # Step 3: Calculate capital gap
    # Project savings account growth during wait period
    future_savings = current_savings
    future_savings += months_until_eligible * monthly_surplus * savings_allocation_pct

    capital_gap = purchase_cost - (extractable + future_savings)

    if capital_gap <= 0:
        # No additional savings needed
        return float(months_until_eligible)

    # Step 4: Calculate months to accumulate gap
    monthly_savings_rate = monthly_surplus * savings_allocation_pct
    if monthly_savings_rate <= 0:
        return None  # Can't accumulate, won't reach goal

    months_to_accumulate = capital_gap / monthly_savings_rate

    # Step 5: Total time
    total_time = months_until_eligible + months_to_accumulate

    if total_time > max_projection_months:
        return None  # Too far in future

    return total_time
```

### TR-3: New select_feeder Implementation

```python
def select_feeder(
    units: List[Unit],
    month_global: int,
    cooldown_months: int,
    for_refi: bool = True,
    appreciation_rate: float = 0.06,
    mortgage_rate: float = 0.0685,
    current_savings: float = 0.0,
    monthly_surplus: float = 10000.0,
    savings_allocation_pct: float = 0.30,
    purchase_cost_estimate: float = 400000.0,
) -> Optional[int]:
    """
    Select the property best positioned to enable the fastest next purchase.

    Uses predictive modeling to project when each property will be refi-eligible
    and how long until total capital (refi + savings) covers purchase cost.

    Args:
        units: List of owned properties
        month_global: Current simulation month
        cooldown_months: Number of months required since last refi
        for_refi: If True, only consider properties that will be refi-eligible
        appreciation_rate: Annual appreciation rate for projections
        mortgage_rate: Mortgage rate for debt amortization projections
        current_savings: Current savings account balance
        monthly_surplus: Average monthly surplus cash flow
        savings_allocation_pct: Percentage of surplus allocated to savings
        purchase_cost_estimate: Estimated total cost of next purchase

    Returns:
        Index of the optimal feeder property, or None if no eligible properties
    """
    if not units:
        return None

    # Configuration
    ltv_threshold = 0.75
    max_ltv_refi = 0.75
    cashout_cost_pct = 0.03
    max_projection_months = 24

    # Calculate monthly prepayment per property (assumes concentrated on one)
    # This is the prepayment the selected property would receive
    monthly_prepayment = monthly_surplus * (1 - savings_allocation_pct)

    eligible = []

    for i, u in enumerate(units):
        if u.debt <= 0:
            continue  # Skip paid-off properties

        # Calculate time to purchase for this property
        time_to_purchase = calculate_time_to_purchase(
            unit=u,
            month_global=month_global,
            cooldown_months=cooldown_months,
            ltv_threshold=ltv_threshold,
            max_ltv_refi=max_ltv_refi,
            cashout_cost_pct=cashout_cost_pct,
            monthly_prepayment=monthly_prepayment,
            mortgage_rate=mortgage_rate,
            appreciation_rate=appreciation_rate,
            current_savings=current_savings,
            monthly_surplus=monthly_surplus,
            savings_allocation_pct=savings_allocation_pct,
            purchase_cost=purchase_cost_estimate,
            max_projection_months=max_projection_months
        )

        if time_to_purchase is not None:
            eligible.append((i, time_to_purchase))

    if not eligible:
        # Fallback: use Optimization 1 logic (highest extractable equity)
        return select_feeder_fallback(units, month_global, cooldown_months, for_refi)

    # Select property with minimum time to purchase
    eligible.sort(key=lambda x: x[1])  # Ascending (shortest time)
    return eligible[0][0]


def select_feeder_fallback(
    units: List[Unit],
    month_global: int,
    cooldown_months: int,
    for_refi: bool
) -> Optional[int]:
    """
    Fallback selection using Optimization 1 logic (highest extractable equity).
    Used when predictive selection fails or produces no results.
    """
    eligible = []
    for i, u in enumerate(units):
        if u.debt <= 0:
            continue

        if for_refi:
            months_since_refi = month_global - u.last_refi_month
            if months_since_refi < cooldown_months:
                continue

        max_ltv = 0.75
        extractable = (u.value * max_ltv - u.debt) * 0.97 if u.value > 0 else 0
        eligible.append((i, extractable))

    if not eligible:
        return None

    eligible.sort(key=lambda x: x[1], reverse=True)
    return eligible[0][0]
```

### TR-4: Call Site Updates in simulator.py

**Current call sites that need updating:**

1. **Line 191:** Initial feeder selection
2. **Line 254:** Feeder refi attempt
3. **Line 300:** Feeder reselection after purchase
4. **Line 340:** Feeder reselection after payoff
5. **Line 357:** Feeder reselection in Phase 2

**Example update (Line 191):**
```python
# BEFORE:
feeder_index = select_feeder(units, month_global, cooldown_months, for_refi=False)

# AFTER:
feeder_index = select_feeder(
    units=units,
    month_global=month_global,
    cooldown_months=cooldown_months,
    for_refi=False,
    appreciation_rate=appreciation / 12,  # Convert to monthly (WAIT: already annual?)
    mortgage_rate=rate_purchase,
    current_savings=savings_account,
    monthly_surplus=surplus if surplus > 0 else 0.0,  # Need to calculate average?
    savings_allocation_pct=savings_pct,
    purchase_cost_estimate=total_purchase_cost  # Use actual calculation
)
```

**⚠️ CHALLENGE:** `monthly_surplus` is not constant - varies month to month. Options:
1. Pass current month's surplus (simple but noisy)
2. Calculate rolling average (more stable but requires tracking)
3. Use a heuristic (e.g., average NOI - fixed costs)

---

## GOTCHAS AND OPEN QUESTIONS

### G-1: Monthly Surplus Variability
**Issue:** Monthly surplus varies significantly due to:
- Seasonal occupancy fluctuations
- Property purchases (spike in expenses)
- Refinance proceeds (spike in income)

**Question:** Should we use:
- Current month's surplus (reactive, volatile)
- 12-month rolling average (stable, lags reality)
- Fixed estimate from configuration (simple, may be inaccurate)

**Recommended approach:** Start with current month's surplus, monitor if volatility causes selection thrashing (feeder changes every month)

### G-2: Appreciation Rate Source
**Issue:** Appreciation rate in config is `"annualAppreciation": 0.06`

**Question:** When projecting monthly, do we:
- Divide by 12? (`0.06 / 12 = 0.005` monthly)
- Use compound formula? `(1.06)^(1/12) - 1 = 0.00487`

**Recommended approach:** Use compound formula for accuracy:
```python
monthly_appreciation = (1 + annual_appreciation) ** (1/12) - 1
```

### G-3: Purchase Cost Estimation
**Issue:** Purchase cost varies based on property price parity, which inflates over time

**Question:** Should we:
- Use current year's parity price (available in simulator)
- Project parity price forward (requires knowing which year property will be purchased)
- Use a conservative estimate (e.g., current parity × 1.1)

**Recommended approach:** Use current year's `price_parity` calculation (already available in simulator context)

### G-4: Dynamic Allocation Interaction
**Issue:** Optimization 3 (dynamic allocation) changes `savings_allocation_pct` based on capital gap

**Question:** When projecting savings accumulation, which percentage to use:
- Current month's dynamic percentage (may change next month)
- Assume default 30% throughout projection
- Try to predict future dynamic allocation (complex)

**Recommended approach:** Use current month's `dynamic_savings_pct` for simplicity. This creates a feedback loop where:
- If close to purchase → higher savings % → faster accumulation → validates the projection
- If far from purchase → lower savings % → slower accumulation → also validates

### G-5: Prepayment Assumption
**Issue:** Projection assumes the selected property will receive ALL prepayments going forward

**Reality check:** This is only true if it remains the feeder. If another property becomes a better candidate next month, prepayments shift.

**Question:** How to handle this circular dependency?

**Recommended approach:** Assume selected property receives prepayments (same assumption Opt 1 makes implicitly). Re-evaluate each month, so if conditions change, selection can change.

### G-6: Tie-Breaking
**Issue:** What if two properties have identical `time_to_purchase`?

**Recommended approach:**
1. First tie-break: Prefer property with higher extractable equity (more buffer)
2. Second tie-break: Prefer property with lower unit_id (stable, deterministic)

```python
eligible.sort(key=lambda x: (x[1], -x[2], x[0]))  # (time, -extractable, index)
```

Where `x = (index, time_to_purchase, extractable_equity)`

### G-7: Phase 2 Behavior
**Issue:** In Phase 2 (debt payoff mode), there are no more purchases

**Question:** Does predictive selection still make sense, or should we fall back to Opt 1?

**Recommended approach:** In Phase 2, use Opt 1 logic (highest extractable equity). Predictive selection is only valuable when planning next purchase.

Update `attempt_refi_cashout` to check phase:
```python
if stop_refi_at_max and units_owned >= max_units:
    # Phase 2: Use simple selection (no purchases to predict)
    feeder_index = select_feeder_fallback(...)
else:
    # Phase 1: Use predictive selection
    feeder_index = select_feeder(...)
```

### G-8: Numerical Stability
**Issue:** Projection errors can compound over 24 months

**Concerns:**
- Rounding errors in debt/value calculations
- Assumption that prepayment rate stays constant
- Assumption that no other properties are purchased during projection

**Recommended approach:**
- Limit projection window to 12 months (instead of 24) for more accurate projections
- Add validation: if projected values seem unrealistic (LTV < 0 or > 100%), fall back to Opt 1

---

## TESTING REQUIREMENTS

### Test Case 1: Same Result as Opt 1
**Scenario:** All properties have same cooldown status and similar LTV
**Expected:** Predictive selection should match Opt 1 (highest extractable equity)
**Validation:** Compare feeder selections month-by-month

### Test Case 2: Cooldown Advantage
**Scenario:**
- Property A: Ready now, extracts $250K
- Property B: Ready in 2 months, extracts $350K
**Expected:** Select Property B (wait 2 months for $100K more capital)
**Validation:** Verify selection and purchase timing

### Test Case 3: Savings vs Refi Trade-off
**Scenario:**
- Property A: Ready now, extracts $200K, need $100K from savings (10 months)
- Property B: Ready in 5 months, extracts $300K, no savings needed
**Expected:** Select Property B (5 months < 10 months)
**Validation:** Verify faster purchase timeline

### Test Case 4: Fallback Trigger
**Scenario:** All properties on cooldown for 30+ months
**Expected:** Fall back to Opt 1 logic, select highest extractable equity among ALL properties
**Validation:** Verify fallback message in logs

### Test Case 5: Regression Test
**Scenario:** Run full 30-year simulation with Opt 2
**Expected:**
- Should reach 7 properties faster than Opt 1 (target: 30-42 months sooner)
- Final debt should be equal or better than Opt 1
- No errors or crashes
**Validation:** Generate comparison report vs Stage 2 baseline

---

## IMPLEMENTATION CHECKLIST

- [ ] Create helper functions in `feeder.py`:
  - [ ] `project_property_value()`
  - [ ] `project_property_debt()`
  - [ ] `calculate_months_until_eligible()`
  - [ ] `calculate_time_to_purchase()`
  - [ ] `select_feeder_fallback()`

- [ ] Rewrite `select_feeder()` function with new parameters

- [ ] Update all call sites in `simulator.py`:
  - [ ] Line 191: Initial feeder selection
  - [ ] Line 254: Feeder refi attempt
  - [ ] Line 300: Post-purchase reselection
  - [ ] Line 340: Post-payoff reselection
  - [ ] Line 357: Phase 2 reselection

- [ ] Add Phase 2 check to use fallback logic

- [ ] Handle edge cases:
  - [ ] No eligible properties (return None)
  - [ ] All projections invalid (fall back to Opt 1)
  - [ ] Tie-breaking logic
  - [ ] Negative or zero monthly_surplus

- [ ] Add unit tests:
  - [ ] Test projection functions independently
  - [ ] Test selection with known scenarios
  - [ ] Test fallback behavior

- [ ] Run regression tests:
  - [ ] Compare to Opt 1 baseline
  - [ ] Validate purchase timeline
  - [ ] Check final portfolio metrics

- [ ] Generate comparison report:
  - [ ] Purchase timeline comparison
  - [ ] Final debt comparison
  - [ ] Feeder selection patterns
  - [ ] Validation of 13-16% speed increase claim

- [ ] Documentation:
  - [ ] Update docstrings
  - [ ] Add inline comments for projection logic
  - [ ] Create comparison report (like stage2_comparison.md)

---

## SUCCESS CRITERIA

**Minimum (Must Have):**
1. ✅ Code runs without errors
2. ✅ Reaches 7 properties (doesn't break acquisition logic)
3. ✅ Final debt is not worse than Opt 1 baseline
4. ✅ Feeder selection is deterministic (same inputs → same output)

**Target (Should Have):**
1. ✅ Reaches 7 properties at least 12 months faster than Opt 1
2. ✅ Final debt is equal to or better than Opt 1
3. ✅ Selection logic is explainable (can articulate why each property was chosen)
4. ✅ Falls back gracefully when projections fail

**Stretch (Nice to Have):**
1. ✅ Reaches 7 properties 30-42 months faster (13-16% improvement)
2. ✅ Final debt is significantly better than Opt 1
3. ✅ Reduces total prepayments (more efficient capital deployment)

---

## ROLLBACK PLAN

If Optimization 2 performs worse than Optimization 1:

1. **Revert `select_feeder()` to Opt 1 implementation**
   - Keep helper functions (may be useful for future features)
   - Restore simple "highest extractable equity" logic

2. **Update call sites to remove extra parameters**
   - Restore original 4-parameter signature
   - Remove parameter passing in simulator.py

3. **Document findings**
   - Create rejection report (like stage3_comparison.md for Opt 4)
   - Explain why predictive selection didn't outperform reactive selection
   - Preserve lessons learned for future optimization attempts

---

## ALTERNATIVE APPROACHES

If full predictive selection proves too complex, consider these simpler alternatives:

### Alternative A: Hybrid Approach
- Use Opt 1 (highest extractable equity) as base
- Add cooldown awareness: penalize properties that won't be eligible for 6+ months
- Simpler than full projection, but captures some forward-looking benefit

### Alternative B: Two-Property Lookahead
- Calculate time-to-purchase for current feeder
- Calculate time-to-purchase for second-best property
- Only switch if second-best is 3+ months faster (avoid thrashing)
- Less volatile than full predictive, more stable selections

### Alternative C: Staged Rollout
- Implement projection functions first (without changing selection)
- Add logging to compare "what Opt 1 chose" vs "what Opt 2 would choose"
- Analyze differences before committing to implementation
- Lower risk, more data-driven decision

---

## ESTIMATED IMPACT

**Based on hypothesis (not validated):**

| Metric | Baseline | Opt 1 | Opt 2 (Est.) |
|--------|----------|-------|--------------|
| Time to 7 properties | Y22M05 | Y22M05 | **Y19M11** (-30 months) |
| Final debt | $1,410,683 | $1,379,611 | **$1,320,000** (est.) |
| Improvement vs baseline | - | 2.2% | **6.4%** (est.) |

**⚠️ WARNING:** These estimates are speculative. Optimization 4 was estimated at 5-10% improvement but actually performed 8.8% WORSE. Trust validation testing over estimates.

---

## DEPENDENCIES

**Code Dependencies:**
- No new external libraries required
- Uses existing `types.py` Unit dataclass
- Uses existing `debt.py` pmt() and amortization functions

**Data Dependencies:**
- Requires access to engine configuration (appreciation rate, mortgage rate)
- Requires current savings account balance (already tracked in simulator)
- Requires purchase cost calculation (already available in simulator)

**Knowledge Dependencies:**
- Understanding of compound interest calculations
- Understanding of mortgage amortization
- Understanding of LTV thresholds and refi eligibility rules

---

## REFERENCES

**Related Documents:**
- `OPTIMIZATION_BREAKDOWN.md` - Original optimization proposal
- `comparison_report.md` - Stage 1 validation (Opt 1)
- `stage2_comparison.md` - Stage 2 validation (Opt 1+3)
- `stage3_comparison.md` - Stage 3 rejection (Opt 4)
- `OPTIMIZATION_FINAL_SUMMARY.md` - Current state summary

**Code Files:**
- `ob_str_engine/engine/feeder.py` - Main implementation file
- `ob_str_engine/engine/simulator.py` - Call sites to update
- `ob_str_engine/engine/types.py` - Unit dataclass definition
- `ob_str_engine/engine/debt.py` - Amortization functions

**Configuration:**
- `ob_str_engine/OB_STR_ENGINE_V2_3.json` - Engine parameters

---

## FINAL NOTES

**Why Not Implemented Yet:**
- Optimization 1 (simpler alternative) was chosen first
- Opt 1 + Opt 3 provided 2.2% improvement with minimal risk
- Opt 2 is significantly more complex (70 lines vs 3 lines)
- Higher risk of bugs and unintended consequences
- User's philosophy prioritizes "well-capitalized foundation" over "maximum speed"

**When to Consider Implementation:**
- If user wants to explore maximum theoretical speed (research project)
- If running Monte Carlo simulations and want to test multiple strategies
- If user is willing to accept higher risk for potentially higher reward
- After gaining more confidence with the model through parameter exploration

**Recommendation:**
Keep as **future research project**. Current implementation (Opt 1 + Opt 3) provides good balance of safety, simplicity, and improvement. Only pursue Opt 2 if:
1. User explicitly requests it, AND
2. Sufficient time for thorough testing (3-4 hours minimum), AND
3. Acceptance that it may not outperform Opt 1 (like Opt 4)

---

*Document Version: 1.0*
*Created: December 26, 2024*
*Status: Ready for Implementation (Pending User Approval)*
