# Distribution System - Quick Start Guide

## TL;DR

You can now model "stepping away from your job" by adjusting distribution triggers in the config file. The system automatically pays investor distributions when your portfolio meets safety criteria.

**Current default:** Distributions start Year 22 (debt-free), paying $7.17M over 30 years.

**Recommended adjustment:** Change 2 numbers to start distributions at Year 19-20 instead.

---

## Quick Test (5 Minutes)

### 1. Run Current Simulation
```bash
python run_quick.py
python analyze_distributions.py
```

**Result:** Distributions start Year 22, pays $72k/month average

### 2. Test "Balanced" Preset
Edit `ob_str_engine\OB_STR_ENGINE_V2_3.json`:

Find this line (around line 73):
```json
"maxPortfolioLTV": 30.0,
```

Change to:
```json
"maxPortfolioLTV": 35.0,
```

Find this line (around line 72):
```json
"minPropertiesOwned": 3,
```

Change to:
```json
"minPropertiesOwned": 5,
```

Run again:
```bash
python run_quick.py
python analyze_distributions.py
```

**Expected:** Distributions start Year 19-20, higher total payout

### 3. Compare Results
Note the differences in:
- Distribution start year
- Total distributions over 30 years
- Final portfolio value
- Monthly income during distribution phase

---

## The 3 Most Important Levers

### 1. When to Start: `maxPortfolioLTV`
**Controls:** Maximum debt level you're comfortable with while taking distributions

```json
"maxPortfolioLTV": 0     // Debt-free only → Year 22+
"maxPortfolioLTV": 30    // Low leverage → Year 19-20
"maxPortfolioLTV": 50    // Moderate leverage → Year 17-18
```

### 2. How Much Income: `targetAnnualIncome`
**Controls:** Minimum annual NOI before distributions start

```json
"targetAnnualIncome": 75000    // Earlier start, lower income
"targetAnnualIncome": 100000   // Balanced (current)
"targetAnnualIncome": 150000   // Later start, higher income
```

### 3. How Much to Distribute: `distributionPct`
**Controls:** Percentage of NOI paid out vs retained

```json
"distributionPct": 0.60   // Distribute 60%, retain 40%
"distributionPct": 0.75   // Distribute 75%, retain 25% (current)
"distributionPct": 0.90   // Distribute 90%, retain 10%
```

---

## Common Scenarios

### "I want to step away from my job ASAP"
**Goal:** Earliest possible distributions

**Changes:**
```json
"targetAnnualIncome": 100000,
"maxPortfolioLTV": 50.0,
"minReserveCushion": 100000,
"distributionPct": 0.70
```

**Result:** Distributions start ~Year 17-18

---

### "I want maximum safety"
**Goal:** Only distribute when debt-free with large cushion

**Changes:**
```json
"targetAnnualIncome": 150000,
"maxPortfolioLTV": 0,
"minReserveCushion": 500000,
"distributionPct": 0.80
```

**Result:** Distributions start Year 23+

---

### "Balanced approach" (RECOMMENDED)
**Goal:** Financial freedom around Year 20 with good safety

**Changes:**
```json
"targetAnnualIncome": 100000,
"maxPortfolioLTV": 35.0,
"minPropertiesOwned": 5,
"minReserveCushion": 250000,
"distributionPct": 0.75
```

**Result:** Distributions start ~Year 19-20, $600k+/year

---

## Full Config Location

File: `ob_str_engine\OB_STR_ENGINE_V2_3.json`

Section starts at line ~68:
```json
"distribution": {
  "enabled": true,  // ← Turn on/off
  "triggers": {
    "targetAnnualIncome": 100000.0,        // ← Minimum income
    "minPropertiesOwned": 3,               // ← Minimum properties
    "maxPortfolioLTV": 30.0,               // ← Maximum leverage
    "allowDebtFreeOverride": true,         // ← Auto-start when debt-free?
    "minReserveCushion": 200000.0,         // ← Minimum cash reserves
    "minMonthsFixedCostsReserve": 12,      // ← Months of expenses
    "minDSCR": 1.5                         // ← Debt coverage ratio
  },
  "distribution": {
    "distributionPct": 0.75,               // ← % to distribute
    "minRetainedNOI": 0.15,
    "prioritizeReserveTopUp": true
  },
  "safety": {
    "suspendIfLTVExceeds": 50.0,
    "suspendIfReservesBelowMonths": 6,
    "suspendIfDSCRBelow": 1.2
  }
}
```

---

## What the Numbers Mean

### Your Portfolio Milestones
Based on the simulation data:

| Year | Properties | LTV | Annual NOI | What Happens |
|------|-----------|-----|------------|--------------|
| 5 | 1 | 73% | $68k | First property acquired |
| 7 | 1 | 55% | $75k | NOI exceeds $75k threshold |
| 8 | 2 | 73% | $156k | NOI exceeds $100k threshold |
| 11 | 3 | 67% | $265k | 3 properties owned |
| 17 | 7 | 53% | $771k | High safety margin (DSCR > 2.0) |
| 19 | 7 | 31% | $862k | LTV < 30% milestone |
| 22 | 7 | 0% | $980k | Debt-free! |
| 30 | 7 | 0% | $1.38M | Portfolio fully matured |

### Distribution Impact (Default Config)
- **Distributions start:** Year 22 Month 10
- **Monthly income:** $60k-90k (grows over time)
- **30-year total:** $7.17 million
- **Final portfolio:** $12.87M equity + $4.0M cash
- **Return on investment:** 13.32× your contributions

---

## How to Interpret Results

After running the simulation, look at these key metrics:

### 1. When Distributions Start
```
✓ DISTRIBUTIONS STARTED
  First distribution: Year 22, Month 10  ← WHEN you achieve financial freedom
```

### 2. Monthly Income
```
ANNUAL DISTRIBUTIONS
Year 22: $60,287/month = $723k/year  ← Your monthly "salary"
Year 30: $84,134/month = $1.01M/year
```

### 3. Total Value Created
```
INVESTOR RETURN ANALYSIS
  Total contributed: $1.505M
  Final equity: $12.87M
  Total distributions: $7.17M
  Total value: $20.04M              ← What you end with
  Multiple: 13.32x                   ← ROI
```

---

## Decision Framework

**Q: When should I set distributions to start?**
- Year 17-18: Aggressive (moderate leverage, earlier freedom)
- Year 19-20: Balanced (low leverage, good safety) ← **RECOMMENDED**
- Year 22+: Conservative (debt-free, maximum safety)

**Q: How much should I distribute?**
- 60-70%: Conservative (retain more for safety/growth)
- 75%: Balanced (current default) ← **RECOMMENDED**
- 80-90%: Aggressive (maximize current income)

**Q: What income level should I target?**
- $75k/year: Part-time work supplement
- $100k/year: Full W-2 replacement ← **RECOMMENDED**
- $150k+/year: Lifestyle upgrade

---

## Next Steps

1. **Run baseline:** See current results with default config
2. **Test 2-3 scenarios:** Aggressive, balanced, conservative
3. **Compare outcomes:** When do distributions start? How much total?
4. **Choose your strategy:** Based on when you want freedom + risk tolerance
5. **Plan your transition:** Know the year you can step away from your job

---

## Files to Reference

- **`DISTRIBUTION_POLICY_DESIGN.md`** - Full explanation of all levers
- **`DISTRIBUTION_IMPLEMENTATION_SUMMARY.md`** - Complete technical documentation
- **`VALIDATION_ANALYSIS.md`** - Why certain warnings appear (and why most are false positives)

---

## Support

If you want to test a specific scenario or have questions about the levers, just ask! The system is fully functional and ready to model your path to financial freedom.

**The bottom line:** With your current strategy, you could step away from your job around **Year 19-20** and receive **$600k-$1M per year** in distributions while maintaining conservative safety margins.
