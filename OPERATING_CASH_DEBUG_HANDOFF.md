# OPERATING CASH DEBUG SESSION HANDOFF

**Date:** December 26, 2024
**Session Context:** Debugging why operating cash hits $0 after property purchases
**Token Count at Handoff:** ~100K

---

## PROBLEM STATEMENT

Operating cash is hitting $0 for extended periods (116+ months out of 360), particularly in months immediately following property acquisitions. This is a red flag - operating cash should maintain a minimum buffer of 1 month of fixed costs at all times.

**Current Status:**
- Minimum operating cash: **$0.00**
- Occurs at: Year 5, Month 4 (and many other months)
- Expected minimum: ~$8,000 (1 month of fixed costs)

---

## USER'S REQUIREMENT (CONFIRMED)

Operating cash should be **higher priority** than rainy reserve:

1. **Operating cash:** 1 month of fixed costs (must be funded FIRST)
2. **Rainy reserve:** 5 months of fixed costs (down from 6)
3. **Purchase reserve cushion:** 6 months total (5 for rainy + 1 for operating)

**Philosophy:** Operating cash is the first line of defense for day-to-day operations and must be protected at all times.

---

## CHANGES MADE SO FAR

### 1. Config Changes (`OB_STR_ENGINE_V2_3.json`)

```json
"banking": {
  "rainyCoverageMonths": 5,          // Changed from 6
  "operatingCashMonths": 1,          // NEW parameter
  "seasoningMonths": 6,
  "refiLTVTrigger": 0.75,
  "cashoutCostPct": 0.03,
  "cashInterestRate": 0.04,
  "purchaseReserveMonths": 6         // Stays at 6 (5 rainy + 1 operating)
}
```

### 2. Restructured Monthly Cash Flow (`simulator.py` lines 162-218)

**Before (WRONG):**
```python
# Calculate ops_cashflow as a number
ops_cashflow = noi - capex_ops - debt_service
# Add to cash AFTER rainy topup
cash += ops_cashflow - rainy_topup
```

**After (CORRECT):**
```python
# Income flows INTO operating cash
cash += gross

# Expenses paid FROM operating cash
cash -= exp["mgmt"]
cash -= exp["hoa_monthly"]
cash -= exp["insurance"]
cash -= exp["tax"]
cash -= debt_service

# Rainy topup FROM operating cash (protecting minimum)
min_operating_cash = operating_cash_months * fixed_monthly
cash_available_for_rainy = max(0.0, cash - min_operating_cash)
rainy_topup, rainy_reserve = update_rainy_day_reserve(...)
actual_topup = min(rainy_topup, cash_available_for_rainy)
cash -= actual_topup
```

### 3. Updated `prepay_surplus()` (`feeder.py` line 281)

**Before (WRONG):**
```python
surplus = cash - max(0.0, required_reserves - rainy_reserve)
# This allowed rainy reserve to count toward operating cash minimum
```

**After (CORRECT):**
```python
min_operating_cash = operating_cash_months * fixed_monthly_costs
surplus = cash - min_operating_cash
# Operating cash maintains its own minimum independent of rainy reserve
```

### 4. Purchase Month Logic (`simulator.py` line 358-360)

Added guard to skip surplus allocation in purchase month:
```python
# Skip surplus allocation this month - reserve cushion needs to stay in cash
# to fund rainy reserve and operating minimum in subsequent months

elif not purchased_this_month:
    # Can't purchase yet - split surplus between prepay and savings
```

---

## THE BUG WE'RE DEBUGGING

### Observed Behavior (Year 5, First Purchase)

| Month | Operating Cash | Rainy Balance | Rainy Target | Units | Notes |
|-------|---------------|---------------|--------------|-------|-------|
| 2 | $1,000 | $0 | $0 | 0 | Before purchase |
| 3 | **$1,533** | $0 | $0 | 1 | **Purchase month - should have ~$52K!** |
| 4 | **$0** | $5,734 | $48,691 | 1 | **Rainy draining operating cash** |
| 5 | **$0** | $10,213 | $48,730 | 1 | **Still at zero** |
| 6 | **$0** | $14,430 | $48,770 | 1 | **Still at zero** |

### Expected Behavior

**Month 3 (Purchase):**
- Start with cash: $1,000
- Add annual savings: +$4,167
- Purchase from savings: $186,913 (includes $47,604 reserve cushion)
- Deposit reserve cushion to cash: +$47,604
- **Expected ending cash: $1,000 + $4,167 + $47,604 = $52,771**
- **Actual ending cash: $1,533** ❌

**The reserve cushion is NOT being deposited, or it's being spent immediately!**

---

## RESERVE CUSHION CALCULATION

The reserve cushion is calculated correctly at `simulator.py:279`:

```python
# Reserve cushion = 6 months of NEW property's fixed costs
new_prop_fixed = estimate_fixed_costs_for_new_property(
    price_parity, hoa_annual_this_year, ins_rate, tax_rate,
    rate_purchase, amort_years, dp_pct
)
reserve_cushion = purchase_reserve_months * new_prop_fixed
```

**For first property (Year 5):**
- Price parity: $812,665
- Monthly fixed costs: ~$7,934
- Reserve cushion (6 months): **~$47,604**

This is included in `total_purchase_cost` at line 281.

---

## RESERVE CUSHION DEPOSIT

The deposit happens at `simulator.py:353`:

```python
# Deposit the reserve cushion into operating cash
# This ensures we have funds to top up rainy reserve and maintain operating minimum
cash += reserve_cushion
```

**This code executes for ALL purchases** (it's outside the `if units_owned == 0:` block).

**But somehow operating cash only shows $1,533 at end of Month 3!**

---

## DEBUGGING HYPOTHESIS

Something is draining the $47,604 reserve cushion AFTER it's deposited but BEFORE the month ends.

**Potential culprits:**

1. **Surplus allocation logic running after purchase in same month**
   - We added `elif not purchased_this_month:` guard (line 361)
   - But maybe there's another path that allocates surplus?

2. **Phase 2 prepayment logic**
   - Shouldn't trigger (units_owned < max_units in Month 3)
   - But check `simulator.py:408-410`

3. **Some other cash deduction we're missing**
   - Need to trace ALL places where `cash -=` happens after line 353

4. **The reserve cushion isn't actually being added**
   - Maybe `reserve_cushion` is $0 or being calculated wrong?
   - Add debug print to verify actual value

---

## DEBUGGING STRATEGY

### Step 1: Verify Reserve Cushion Value

Add print statement at `simulator.py:353`:
```python
if purchased_this_month:
    print(f"DEBUG Y{year}M{m}: Depositing reserve cushion ${reserve_cushion:,.2f} to cash")
    cash += reserve_cushion
    print(f"DEBUG Y{year}M{m}: Cash after deposit: ${cash:,.2f}")
```

### Step 2: Trace All Cash Modifications After Purchase

Search for all `cash -=` and `cash +=` operations that occur after line 353 in the monthly loop.

Likely locations:
- Line 392: `cash -= (feeder_prepay + savings_deposit)` (Phase 1 allocation)
- Line 402: `cash = max(0.0, cents(cash))` (Phase 1 allocation)
- Line 409: `prepay_surplus()` returns modified cash (Phase 2)
- Line 425: `cash -= (feeder_prepay + savings_deposit)` (sweep prepayments)

### Step 3: Check Control Flow

Verify that when `purchased_this_month = True`:
- Phase 1 surplus allocation is SKIPPED (line 361 guard should prevent)
- Phase 2 logic doesn't run (units_owned < max_units)
- No other cash modifications happen

### Step 4: Add CSV Output Column

Temporarily add `reserve_cushion` to CSV output to verify calculation:
```python
# At simulator.py line ~450 in the output row
"ReserveCushion": cents(reserve_cushion) if purchased_this_month else 0.0,
```

Then check: `df[df['Year'] == 5][['Month', 'Purchase_Total', 'ReserveCushion', 'OperatingCash']]`

---

## FILES TO FOCUS ON

1. **`ob_str_engine/engine/simulator.py`**
   - Lines 162-218: Monthly cash flow (income/expenses)
   - Lines 243-415: Phase 1 purchase and surplus allocation
   - Lines 351-360: Reserve cushion deposit and purchase month guard

2. **`ob_str_engine/engine/feeder.py`**
   - Lines 281-316: `prepay_surplus()` function

3. **`ob_str_engine/OB_STR_ENGINE_V2_3.json`**
   - Lines 48-56: Banking parameters

---

## VERIFICATION COMMANDS

```bash
# Run simulation
python run_quick.py

# Check operating cash minimum
python -c "import pandas as pd; df = pd.read_csv('out/baseline_current.csv'); print('Min operating cash:', df['OperatingCash'].min())"

# Check Year 5 details
python -c "import pandas as pd; df = pd.read_csv('out/baseline_current.csv'); print(df[(df['Year'] == 5) & (df['Month'] <= 6)][['Year', 'Month', 'Units', 'OperatingCash', 'RainyBalance', 'Purchase_Total']].to_string(index=False))"
```

---

## DESIRED END STATE

After debugging and fixing:

1. **Operating cash NEVER hits zero**
   - Minimum should be ~$8K-$80K (1 month of fixed costs, scales with portfolio)

2. **Reserve cushion properly allocated:**
   - At purchase: Deposit 6 months to operating cash
   - Next month: Rainy topup takes 5 months, leaving 1 month in operating cash

3. **Clear separation of concerns:**
   - Operating cash: Day-to-day operations (1 month buffer)
   - Rainy reserve: Emergency fund (5 months)
   - Both are fully funded after every purchase

---

## QUESTIONS TO ANSWER

1. **What is the actual value of `reserve_cushion` at line 353?**
2. **What is the value of `cash` immediately before and after line 353?**
3. **Does ANY code path execute between line 353 and end of month that modifies `cash`?**
4. **Is the `elif not purchased_this_month:` guard at line 361 working correctly?**

---

## NEXT SESSION SHOULD START WITH

"I'm debugging why operating cash hits $0 after property purchases. The reserve cushion should be $47,604 and deposited at simulator.py:353, but operating cash only shows $1,533 at end of month. I need to trace where the $46K is going. Start by adding debug prints around line 353 to verify the reserve cushion amount and cash balance before/after deposit."

---

*Session ended at 100K tokens - handoff prepared for continuation*
