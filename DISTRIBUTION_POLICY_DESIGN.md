# Distribution Policy Design - "Financial Freedom" Levers

## Executive Summary

Based on your portfolio simulation, here are the key findings for "stepping away from job" planning:

**Critical Milestones:**
- **Year 5**: NOI exceeds your $50k annual contribution (at 79% LTV with 1 property)
- **Year 7**: NOI reaches $75k/year (at 63% LTV with 1 property)
- **Year 8**: NOI reaches $100k/year (at 74% LTV with 2 properties)
- **Year 17**: High safety margin (DSCR > 2.0, LTV 57%)
- **Year 20**: Conservative distribution trigger (LTV < 30%, $576k/year available)
- **Year 22**: Completely debt-free ($980k/year NOI)

---

## Recommended Configuration: Hybrid Trigger System

### Why Hybrid?
Your situation requires balancing three concerns:
1. **Timing**: When can I step away from my job?
2. **Safety**: Will income be reliable/sustainable?
3. **Flexibility**: Can I adjust based on life changes?

A single trigger (year, LTV, or income) is too rigid. I recommend a **multi-condition system** with adjustable levers.

---

## Configuration Structure

```json
{
  "distribution": {
    "enabled": true,
    "mode": "hybrid",

    "triggers": {
      "targetAnnualIncome": 100000,
      "minPropertiesOwned": 3,
      "maxPortfolioLTV": 30,
      "allowDebtFreeOverride": true,
      "minReserveCushion": 200000,
      "minMonthsFixedCostsReserve": 12,
      "minDSCR": 1.5
    },

    "distribution": {
      "distributionPct": 0.75,
      "minRetainedNOI": 0.15,
      "prioritizeReserveTopUp": true
    },

    "safety": {
      "suspendIfLTVExceeds": 50,
      "suspendIfReservesBelowMonths": 6,
      "suspendIfDSCRBelow": 1.2
    }
  }
}
```

---

## Lever Descriptions

### PRIMARY LEVERS (What You'll Adjust)

#### 1. `targetAnnualIncome` (Default: 100000)
**What it is:** The annual income you want from the portfolio

**How to use it:**
- Conservative: $75,000 (achievable Year 20)
- Moderate: $100,000 (achievable Year 20)
- Aggressive: $150,000 (achievable Year 20 debt-free, or earlier with leverage)

**Example scenarios:**
```json
"targetAnnualIncome": 75000   // Part-time work supplement
"targetAnnualIncome": 100000  // Full replacement of W-2 income
"targetAnnualIncome": 150000  // Lifestyle upgrade
```

---

#### 2. `maxPortfolioLTV` (Default: 30)
**What it is:** Maximum leverage you're comfortable with while taking distributions

**How to use it:**
- Ultra-conservative: `0` (debt-free only) → Distributions start Year 22
- Conservative: `25` (very low leverage) → Distributions start ~Year 21
- Balanced: `30` (recommended) → Distributions start Year 19-20
- Aggressive: `50` (moderate leverage) → Distributions start Year 17-18

**Trade-off:**
- Lower LTV = Later start, but safer income
- Higher LTV = Earlier start, but riskier if market drops

---

#### 3. `minReserveCushion` (Default: 200000)
**What it is:** Absolute dollar minimum in reserves before distributing

**How to use it:**
- Conservative: $500,000 (2+ years of expenses)
- Balanced: $200,000 (1 year of expenses)
- Aggressive: $100,000 (6 months of expenses)

**Why it matters:**
If your portfolio hits a rough patch (vacancy, repairs, economic downturn), this is your safety buffer before you need to reduce/stop distributions.

---

#### 4. `distributionPct` (Default: 0.75)
**What it is:** What percentage of NOI you distribute vs retain

**How to use it:**
- Conservative: `0.60` (distribute 60%, retain 40% for growth/cushion)
- Balanced: `0.75` (distribute 75%, retain 25%)
- Aggressive: `0.90` (distribute 90%, minimal retention)

**Example:**
If monthly NOI = $100,000:
- At 0.75: You receive $75,000, $25,000 stays in reserves
- At 0.90: You receive $90,000, $10,000 stays in reserves

---

### SECONDARY LEVERS (Safety Guards)

#### 5. `minMonthsFixedCostsReserve` (Default: 12)
**What it is:** Reserves must cover this many months of debt service + HOA + insurance + taxes

**Common values:**
- 6 months: Minimum safe level
- 12 months: Recommended baseline
- 18-24 months: Ultra-conservative

---

#### 6. `minDSCR` (Default: 1.5)
**What it is:** Debt Service Coverage Ratio - NOI must be this multiple of debt payments

**Interpretation:**
- 1.0: Breakeven (dangerous)
- 1.25: Lender minimum (tight)
- 1.5: Comfortable (recommended)
- 2.0: Very safe

---

#### 7. `allowDebtFreeOverride` (Default: true)
**What it is:** If portfolio is 100% debt-free, bypass LTV and DSCR checks

**Use case:**
If you reach debt-free status early (Year 22), you might want to start distributions immediately regardless of other thresholds, since there's no debt risk.

---

## Distribution Logic Flow

```
Every month, check:

1. ARE DISTRIBUTIONS ENABLED?
   ├─ No → Skip, continue simulation as normal
   └─ Yes → Continue to step 2

2. DO WE MEET ALL TRIGGER CONDITIONS?
   ├─ Annual NOI >= targetAnnualIncome?
   ├─ Properties owned >= minPropertiesOwned?
   ├─ Portfolio LTV <= maxPortfolioLTV (or debt-free if override enabled)?
   ├─ Reserves >= minReserveCushion?
   ├─ Reserves >= minMonthsFixedCostsReserve × monthly fixed costs?
   └─ DSCR >= minDSCR (if debt exists)?

   ├─ All YES → Continue to step 3
   └─ Any NO → No distribution this month

3. CALCULATE DISTRIBUTABLE AMOUNT
   availableNOI = Net Operating Income this month
   reserveTopUpNeeded = (target reserves - current reserves)

   distributionBase = availableNOI - reserveTopUpNeeded

   IF distributionBase > 0:
      distribution = distributionBase × distributionPct
      retained = distributionBase × (1 - distributionPct)
   ELSE:
      distribution = 0 (reserves need topping up first)

4. SAFETY CHECK - SHOULD WE SUSPEND?
   ├─ LTV > suspendIfLTVExceeds? → Suspend
   ├─ Reserves < suspendIfReservesBelowMonths? → Suspend
   └─ DSCR < suspendIfDSCRBelow? → Suspend

   ├─ Any trigger → distribution = 0
   └─ All clear → Pay distribution

5. EXECUTE
   Distribute cash to investor
   Reduce Operating Cash by distribution amount
   Log distribution event
```

---

## Recommended Presets

### Preset A: "Conservative - Debt Free Only"
**Goal:** Maximum safety, willing to wait for debt-free status

```json
"triggers": {
  "targetAnnualIncome": 75000,
  "maxPortfolioLTV": 0,
  "minReserveCushion": 500000,
  "minDSCR": 1.0
},
"distribution": {
  "distributionPct": 0.80
}
```
**Result:** Distributions start Year 23, ~$800k/year

---

### Preset B: "Balanced - Low Leverage"
**Goal:** Start distributions ~5 years before debt-free, maintain safety margin

```json
"triggers": {
  "targetAnnualIncome": 100000,
  "maxPortfolioLTV": 30,
  "minReserveCushion": 200000,
  "minMonthsFixedCostsReserve": 12,
  "minDSCR": 1.5
},
"distribution": {
  "distributionPct": 0.75
}
```
**Result:** Distributions start Year 19-20, ~$575k/year initially

---

### Preset C: "Aggressive - Early Freedom"
**Goal:** Start distributions as soon as income target is met

```json
"triggers": {
  "targetAnnualIncome": 100000,
  "maxPortfolioLTV": 50,
  "minReserveCushion": 100000,
  "minMonthsFixedCostsReserve": 6,
  "minDSCR": 1.3
},
"distribution": {
  "distributionPct": 0.70
}
```
**Result:** Distributions start Year 17, ~$400k/year initially

---

### Preset D: "Hybrid - Recommended for You"
**Goal:** Balance early start with conservative safety

```json
"triggers": {
  "targetAnnualIncome": 100000,
  "maxPortfolioLTV": 35,
  "allowDebtFreeOverride": true,
  "minReserveCushion": 250000,
  "minMonthsFixedCostsReserve": 12,
  "minDSCR": 1.5
},
"distribution": {
  "distributionPct": 0.75,
  "prioritizeReserveTopUp": true
}
```
**Result:** Distributions start Year 19, ~$500-600k/year, ramp up over time

---

## Testing Scenarios

Once implemented, you should test:

1. **Base Case:** Default settings, see when distributions start
2. **Conservative:** Debt-free only, maximum reserves
3. **Aggressive:** 50% LTV allowed, lower reserves
4. **Income Variations:** Test $75k, $100k, $150k targets
5. **Stress Test:** What happens if market drops 20% in Year 18?

---

## Implementation Notes

### Where to Add This Configuration

**File:** `ob_str_engine/OB_STR_ENGINE_V2_3.json`

Add new section after `"policies"`:

```json
"policies": {
  "portfolio": { ... },
  "capitalAllocation": { ... }
},
"distribution": {
  // New section goes here
}
```

### Simulation Output Changes

Add new columns to CSV output:
- `Distribution Enabled`: 0/1 flag
- `Distribution Triggers Met`: 0/1 flag
- `Distribution Amount`: Monthly distribution
- `Cumulative Distributions`: Total paid out to date
- `Retained NOI`: NOI kept in portfolio

### Reporting Enhancements

Create new report: `DISTRIBUTION_SUMMARY.md`
- Year distributions started
- Total distributed over simulation
- Average monthly distribution
- Distribution as % of total equity
- Effective yield on initial capital

---

## Next Steps

1. **Choose your preset** or customize levers
2. **Add configuration** to JSON config file
3. **Implement logic** in simulator.py
4. **Run test scenarios** with different settings
5. **Compare outcomes** - which scenario best fits your risk tolerance?

---

## Key Insights from Your Data

1. **You could step away from your job in Year 8** if you're comfortable with 74% LTV and $100k+ NOI, but...

2. **Year 17-20 is the sweet spot** where you have:
   - High safety (DSCR > 2.0, LTV < 30%)
   - Strong income ($575k-900k potential distributions)
   - Substantial reserves ($400k-800k)

3. **Year 22+ is "cruise control"** - debt-free, $1M+/year NOI, massive reserves building up

**My recommendation:** Use Preset D (Hybrid) with:
- `targetAnnualIncome`: Start at $100k, increase to $150k over time
- `maxPortfolioLTV`: 30-35%
- This gives you financial freedom around Year 19-20 with conservative safety margins
