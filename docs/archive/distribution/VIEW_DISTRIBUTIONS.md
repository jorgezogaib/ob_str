# How to View Distributions - Quick Reference

## Portfolio-Level Distribution Display

Distributions are now visible in the UI at the **portfolio aggregated level**.

---

## 1. Homepage Dashboard

**Location:** Main page when you launch the UI

**What you'll see:**
- 5 metric cards at the top
- **5th card = "Total Distributions"** showing total over 30 years

**Example:**
```
Total Distributions: $10.58M
```

---

## 2. Time Series Analysis Page

**Location:** Page 4 in sidebar navigation

**What you'll see:**

### A. Distribution Summary (Top Section)
4 KPI metrics when distributions occur:
- **Total Distributed:** $10.58M over 30 years
- **Avg Monthly:** $98k average per month
- **Started:** Year 22, Month 1
- **Duration:** 9.0 years of distributions

### B. Time Series Chart
1. Check the **"Distribution Amount"** checkbox under "Cash Flow Metrics"
2. Chart shows distribution amounts over time
3. **Gold vertical line** marks when distributions start (labeled "Distributions Start")
4. Works in both Monthly and Yearly views

### C. Annual Summary Table (Bottom)
- Scroll to bottom of page
- Table includes **"Annual Distributions"** column
- Shows distributions by year
- Example:
  ```
  Year 22: $970,462
  Year 23: $988,382
  Year 24: $1,042,162
  ...
  ```

---

## 3. CSV Export (Most Detailed)

**Location:** `out/simulation_results_feeder.csv`

**Distribution Columns:**
- `Distribution Amount` - Monthly distribution ($)
- `Distribution Enabled` - Whether distributions are on (0/1)
- `Distribution Eligible` - Whether trigger met (0/1)
- `Distribution Reason` - Why distribution occurred or didn't
- `Distributable Cash Flow` - Available cash for distribution

**How to use:**
1. Open in Excel/Google Sheets
2. Filter to `Distribution Amount > 0` to see distribution months
3. Pivot by Year to get annual totals
4. Chart over time for trends

---

## 4. Python Analysis Script

**Location:** `analyze_distributions_simple.py`

**How to run:**
```bash
python analyze_distributions_simple.py
```

**What you get:**
- Total distributions over 30 years
- First distribution details (year, month, amount)
- Annual breakdown by year
- Monthly average per year
- Final portfolio state

**Example output:**
```
================================================================================
DISTRIBUTION ANALYSIS
================================================================================

Total Distributions (30 years): $10,582,683
Distribution Months: 108

================================================================================
FIRST DISTRIBUTION
================================================================================
Year: 22
Month: 1
Amount: $105,190
Portfolio LTV: 6.5%
Properties Owned: 7

================================================================================
ANNUAL DISTRIBUTION SUMMARY
================================================================================
Year 22: $   970,462 total  ($  80,872/month)
Year 23: $   988,382 total  ($  82,365/month)
Year 24: $ 1,042,162 total  ($  86,847/month)
...
```

---

## Quick Launch

### To see distributions in UI:

```bash
# Launch dashboard
streamlit run ui/app.py

# Or use batch file
Launch_STR_Dashboard.bat
```

**Then:**
1. Check homepage for total
2. Navigate to "Time Series Analysis" page
3. Enable "Distribution Amount" checkbox
4. Scroll down to see annual table

---

## Current Configuration

**Default setup (Year 22 trigger):**
- Distributions: **Enabled**
- Trigger: Start in **Year 22**
- Distribution %: **100%** of available cash
- Results: **$10.58M** over 9 years

---

## To Change Distribution Settings

### Option 1: Via UI
1. Go to **Run Control** page
2. Click **"Distributions"** tab
3. Toggle "Enable Distributions"
4. Choose trigger type (Year-Based, LTV-Based, or Distributable Amount)
5. Adjust distribution percentage
6. Use Quick Presets for common scenarios
7. Save and run simulation

### Option 2: Via JSON
Edit `ob_str_engine/OB_STR_ENGINE_V2_3.json`:

```json
{
  "distribution": {
    "enabled": true,
    "triggers": {
      "startYear": 22
    },
    "distribution": {
      "distributionPct": 1.0
    }
  }
}
```

---

## What's Portfolio-Level?

All metrics shown are **aggregated across the entire portfolio**:
- ✅ Total distributions from all properties combined
- ✅ Not broken down by individual unit
- ✅ Portfolio-wide averages and totals

**Unit-level tracking** (showing which properties fund distributions) would be a future enhancement.

---

## Summary

**Quickest view:** Homepage metric card
**Most detailed view:** Time Series page
**Raw data:** CSV export
**Analysis:** Python script

All show the same data - just different levels of detail!
