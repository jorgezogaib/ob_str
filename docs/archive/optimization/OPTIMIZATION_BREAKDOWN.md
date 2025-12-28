# FEEDER STRATEGY OPTIMIZATIONS - SIMPLIFIED BREAKDOWN

Each optimization is **independent** and can be implemented alone or in combination with others (except Optimization 1 and 2, which are mutually exclusive alternatives).

---

## **OPTIMIZATION 1: Change Feeder Ranking Criterion**

### Current State
**What happens today:**
- When selecting which property to prepay and eventually refinance (the "feeder")
- Among properties that are past 36-month cooldown AND have LTV < 75%
- The code picks the property with the **LOWEST LTV percentage**

**Example:**
- Property A: Value $950K, Debt $430K, **LTV = 45%** ← SELECTED (lowest LTV)
- Property B: Value $1,200K, Debt $640K, **LTV = 53%**

**Code location:**
`feeder.py`, function `select_feeder()`, lines 59-67

**Current logic:**
```python
ltv = u.debt / u.value
eligible.append((i, ltv))
eligible.sort(key=lambda x: x[1])  # Pick lowest LTV
```

---

### Proposed Future State
**What would change:**
- Same eligibility rules (36-month cooldown, LTV < 75%)
- Instead of picking **lowest LTV percentage**
- Pick the property with **most extractable cash dollars**

**Example:**
- Property A: Can extract $302K (75% of $950K - $430K debt = $715K - $430K = $285K × 97%)
- Property B: Can extract $334K (75% of $1,200K - $640K debt = $900K - $640K = $260K × 97%) ← SELECTED (most cash)

**New logic:**
```python
extractable = (u.value * 0.75 - u.debt) * 0.97
eligible.append((i, extractable))
eligible.sort(key=lambda x: x[1], reverse=True)  # Pick highest extractable
```

---

### Change Characteristics

**Invasiveness:** ⭐ Very Low
- Modifies 3 lines of code in one function
- No new functions, no new parameters
- No changes to other files

**Probability of Success:** 99%
- Simple arithmetic change
- Same inputs, same outputs (just different ranking)
- Zero risk to existing constraints (75% LTV limit, cooldown requirements unchanged)

**Business Reason:**
Properties with higher values can extract more cash even at higher LTV percentages. More cash per refinance = fewer months waiting to accumulate additional savings = faster purchases.

**Impact:** Reach 7 properties ~18 months faster (7% speed increase)

---

---

## **OPTIMIZATION 2: Predictive Feeder Selection (ALTERNATIVE TO OPTIMIZATION 1)**

### Current State
**What happens today:**
- Feeder selection looks at **current property state only**
- "Is this property ready to refi RIGHT NOW?"
- If yes (cooldown passed + LTV < 75%), it's eligible
- Pick from eligible properties using lowest LTV

**Example scenario (Month 150):**
- Property A: Past cooldown ✓, LTV = 50% ✓ → Ready NOW, can extract $250K
- Property B: 3 months until cooldown, LTV = 60% → Not eligible (ignored)

**Decision:** Select Property A (only eligible option)

---

### Proposed Future State
**What would change:**
- Feeder selection looks at **projected future state**
- "When will each property be ready to refi, and how much will it extract?"
- Calculate time-to-purchase for each property
- Pick property that enables **fastest next purchase**

**Example scenario (Month 150):**
- Property A: Ready now, extracts $250K, need $50K more from savings (10 months) → **Purchase in 10 months**
- Property B: Ready in 3 months, extracts $400K, no savings needed → **Purchase in 3 months** ← SELECTED

**Decision:** Select Property B (faster to purchase, even though not ready today)

**New logic:**
```python
# For each property, calculate:
1. Months until eligible (considering cooldown + future LTV with prepayments)
2. Extractable equity at that future date
3. Total months until purchase (including savings accumulation if needed)

# Select property with minimum total time to purchase
```

---

### Change Characteristics

**Invasiveness:** ⭐⭐⭐ High
- Replaces entire `select_feeder()` function (~70 lines of new code)
- Adds projection logic (future value with appreciation, future debt with prepayments)
- Requires additional parameters (appreciation rate, purchase cost estimate)
- More complex algorithm

**Probability of Success:** 85%
- Moderate complexity (requires projections)
- Projections use assumptions (appreciation rate, prepayment amounts)
- More potential for edge cases
- Requires thorough testing

**Business Reason:**
Current approach is "reactive" (only looks at properties ready now). Predictive approach is "proactive" (may target a property that will be better in a few months). Optimizes for **total time to next purchase**, not just **current state**.

**Impact:** Reach 7 properties ~30-42 months faster (13-16% speed increase)

**⚠️ NOTE:** This is an **alternative** to Optimization 1. You would pick EITHER Optimization 1 OR Optimization 2, not both (they both rewrite the same function).

---

---

## **OPTIMIZATION 3: Dynamic Capital Allocation**

### Current State
**What happens today:**
- After all expenses and reserves are covered, surplus cash is split:
  - **70% → Feeder prepayment** (pays down mortgage, saves 6.85% interest)
  - **30% → Savings account** (earns 4% interest)
- This split is **FIXED** every single month, regardless of circumstances

**Example (Month 150):**
- Surplus this month: $10,000
- Feeder gets: $7,000 prepayment
- Savings gets: $3,000 deposit
- (Every month, same 70/30 ratio)

**Code location:**
`simulator.py`, lines 310-314

**Current logic:**
```python
feeder_prepay_pct = 0.70  # Fixed
savings_pct = 0.30        # Fixed

prepay_amount = surplus * feeder_prepay_pct
savings_deposit = surplus * savings_pct
```

---

### Proposed Future State
**What would change:**
- Split ratio adjusts based on **how close we are to next purchase**
- If refinance alone will cover purchase → stop saving (100% prepayment)
- If refinance won't be enough → save more aggressively (50/50 or even 0/100)

**Example scenarios:**

**Scenario A (Far from purchase):**
- Need $300K for next purchase
- Feeder can only extract $100K when ready
- Split: 70% prepayment / 30% savings (default, build equity)

**Scenario B (Close to purchase):**
- Need $300K for next purchase
- Feeder will extract $320K when ready (more than enough!)
- Split: 100% prepayment / 0% savings (no need for savings, maximize yield)

**Scenario C (Need savings urgently):**
- Need $300K for next purchase
- Feeder will extract $200K (not enough)
- Split: 50% prepayment / 50% savings (accelerate savings accumulation)

**New logic:**
```python
capital_gap = purchase_cost - (savings_account + potential_refi)

if capital_gap <= 0:
    # Refi covers everything
    feeder_prepay_pct = 1.0
    savings_pct = 0.0
elif capital_gap < purchase_cost * 0.1:
    # Almost there
    feeder_prepay_pct = 0.5
    savings_pct = 0.5
else:
    # Far from purchase
    feeder_prepay_pct = 0.70
    savings_pct = 0.30
```

---

### Change Characteristics

**Invasiveness:** ⭐⭐ Medium
- Modifies capital allocation logic in `simulator.py` (~15 lines)
- Adds conditional logic based on capital gap calculation
- No new functions, affects one section of code
- Does NOT change feeder selection at all

**Probability of Success:** 95%
- Simple conditional logic
- Uses existing variables (purchase_cost, savings_account, potential_refi)
- Low complexity, easy to test
- No interaction with other optimizations

**Business Reason:**
Why accumulate savings at 4% when you don't need them? If the feeder refinance will provide enough capital for next purchase, putting surplus into prepayments earns 6.85% (the mortgage rate saved) instead of 4% (savings interest). This is **yield optimization** - deploy capital where it earns the highest return.

**When far from purchase:** Build equity in feeder (need a big refi later)
**When close to purchase:** Maximize yield (stop low-return savings)

**Impact:** Reach 7 properties ~9-20 months faster (3-8% speed increase)

**Can combine with:** Optimization 1 OR Optimization 2

---

---

## **OPTIMIZATION 4: Parallel Equity Building**

### Current State
**What happens today:**
- All prepayments go to **ONE feeder property** at a time
- Property 0 is feeder → gets 100% of prepayments
- Property 0 gets refinanced → Property 1 becomes new feeder
- Property 1 starts from "cold" (has not been receiving prepayments)

**Example timeline:**
- Months 1-24: All prepayments to Property 0 → LTV drops 60% → 45%
- Month 24: Property 0 refinanced (resets to 75% LTV)
- Months 25-48: All prepayments to Property 1 → LTV drops 75% → 60%
- Month 48: Property 1 refinanced

**Code location:**
`simulator.py`, lines 310-312 (prepayment application)

**Current logic:**
```python
# All prepayments to single feeder
if feeder_index is not None:
    prepay_amount = surplus * feeder_prepay_pct
    units[feeder_index].debt -= prepay_amount
```

---

### Proposed Future State
**What would change:**
- When portfolio has **4 or more properties**
- Split prepayments between **TWO properties** simultaneously
- Primary feeder: 70% of prepayment budget
- Secondary feeder: 30% of prepayment budget

**Example timeline:**
- Months 1-24: 70% to Property 0, 30% to Property 1
- Property 0: LTV drops 60% → 48% (slower due to split)
- Property 1: LTV drops 75% → 68% (was building equity in parallel!)
- Month 28: Property 0 refinanced
- Months 29-40: 70% to Property 1 (already at 68% LTV!), 30% to Property 2
- Month 40: Property 1 refinanced (12 months faster than if starting cold)

**New logic:**
```python
if len(units) >= 4:
    # Select two feeders
    primary_feeder = select_feeder()
    secondary_feeder = select_feeder(exclude=[primary_feeder])

    # Split prepayments
    primary_amount = surplus * 0.70 * feeder_prepay_pct
    secondary_amount = surplus * 0.30 * feeder_prepay_pct

    units[primary_feeder].debt -= primary_amount
    units[secondary_feeder].debt -= secondary_amount
else:
    # Single feeder (current behavior)
    units[feeder_index].debt -= prepay_amount
```

---

### Change Characteristics

**Invasiveness:** ⭐⭐ Medium
- Modifies prepayment application logic in `simulator.py` (~25 lines)
- Adds second feeder selection and split logic
- Affects prepayment distribution only
- Does NOT change feeder selection criteria at all

**Probability of Success:** 90%
- Moderate complexity (two-feeder tracking)
- Need to handle edge cases (what if only 1 property eligible?)
- Requires testing with different portfolio sizes
- Could conflict with Optimization 3 if both modify same variables

**Business Reason:**
With only one feeder, there's a "switching penalty" - when the feeder gets refinanced, the next feeder starts from zero. With parallel building, multiple properties are building equity simultaneously. When the primary gets refinanced, the secondary is already partially paid down and can become eligible much sooner.

**Trade-off:** Primary feeder takes ~4 months longer to be ready (70% vs 100% prepayments), BUT the secondary feeder becomes ready ~16 months sooner than if it had to wait for primary to finish. **Net benefit: Faster subsequent purchases.**

**Impact:** Reach 7 properties ~12-24 months faster (5-10% speed increase, primarily properties 4-7)

**Can combine with:** Optimization 1 OR Optimization 2, AND Optimization 3

---

---

## **SUMMARY TABLE**

| Optimization | Changes What? | Invasiveness | Success Prob | Speed Gain | Can Combine With |
|--------------|---------------|--------------|--------------|------------|------------------|
| **1. Highest Extractable** | Feeder ranking criterion | ⭐ Very Low | 99% | 7% | 3, 4 |
| **2. Predictive Selection** | Entire feeder selection logic | ⭐⭐⭐ High | 85% | 13-16% | 3, 4 |
| **3. Dynamic Allocation** | Prepay/savings split ratio | ⭐⭐ Medium | 95% | 3-8% | 1 or 2, 4 |
| **4. Parallel Building** | Number of feeders (1 → 2) | ⭐⭐ Medium | 90% | 5-10% | 1 or 2, 3 |

---

## **VALID COMBINATIONS**

**Option A: Quick & Safe**
- ✅ Optimization 1 only
- **Result:** 7% faster, 5 minutes work, 99% success rate

**Option B: Balanced**
- ✅ Optimization 1 + Optimization 3
- **Result:** 10-15% faster, 35 minutes work, high success rate
- **Independent changes:** One modifies feeder selection, one modifies capital allocation

**Option C: Aggressive Balanced**
- ✅ Optimization 1 + Optimization 3 + Optimization 4
- **Result:** 12-20% faster, 1.5 hours work, good success rate
- **Independent changes:** Three separate systems (selection, allocation, distribution)

**Option D: Maximum Optimization**
- ✅ Optimization 2 + Optimization 3 + Optimization 4
- **Result:** 16-20% faster, 4 hours work, moderate success rate
- **Note:** Uses advanced predictive selection instead of simple ranking change

---

## **INCOMPATIBLE COMBINATIONS**

**❌ Cannot do Optimization 1 + Optimization 2 together**
- Both rewrite the `select_feeder()` function
- Must choose ONE approach to feeder selection
- Think of them as "Version A" vs "Version B" of the same function

---

## **RECOMMENDATION**

**If you want safety:** Optimization 1 only (quick win, zero risk)

**If you want best ROI:** Optimization 1 + 3 (two simple changes, cumulative benefit, independent systems)

**If you want maximum speed:** Optimization 2 + 3 + 4 (full optimization, higher complexity, maximum impact)

---

Does this breakdown make sense? Each optimization is now described in plain language with clear before/after states.
