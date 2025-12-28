# Distribution Display in UI - Quick Win Implementation

## What Was Added

Distribution metrics are now visible in the UI at the **portfolio-level** (aggregated).

## 1. Homepage (`app.py`)

**New 5th Metric Card:**
- **Total Distributions** - Shows total distributed over 30 years in $M

Located at the top alongside Portfolio Value, Properties, Debt-Free, and Cash Reserves.

---

## 2. Time Series Page (`pages/4_time_series.py`)

### A. Distribution Summary Section (Top of Page)

When distributions occur, a summary appears with 4 KPIs:

- **Total Distributed** - Total amount over 30 years ($M)
- **Avg Monthly** - Average monthly distribution amount ($k)
- **Started** - Year and month distributions began
- **Duration** - How many years distributions ran

### B. Distribution Amount Checkbox

New checkbox in the **Cash Flow Metrics** section:
- ✅ **Distribution Amount** - Toggle to show/hide distribution amounts on the time series chart

### C. Visual Chart Markers

- **Gold vertical line** marks when distributions start
- Labeled "Distributions Start" on the chart
- Works in both Monthly and Yearly views

### D. Annual Summary Table

The annual breakdown table at the bottom now includes:
- **Annual Distributions** column showing total distributions per year
- Appears between "Annual NOI" and "Total Portfolio Value"
- Formatted as currency

---

## How to View

### Homepage:
1. Launch UI: `streamlit run ui/app.py`
2. Look at the 5 metric cards at the top
3. See "Total Distributions" on the far right

### Time Series Page:
1. Navigate to **Page 4: Time Series Analysis**
2. See distribution summary at the top (if distributions occurred)
3. Check **"Distribution Amount"** in Cash Flow Metrics section
4. Chart will show distribution amounts over time
5. Gold line marks when distributions start
6. Scroll down to see annual table with distribution column

---

## Example Output

With current configuration (Year 22 start, 100% distribution):

**Homepage:**
```
Total Distributions: $10.58M
```

**Time Series Summary:**
```
Total Distributed: $10.58M
Avg Monthly: $98k
Started: Year 22, Mo 1
Duration: 9.0 years
```

**Annual Table:**
```
Year | Properties | Annual Revenue | Annual NOI | Annual Distributions | Total Value
-----|-----------|----------------|------------|---------------------|-------------
 22  |     7     |    $389k       |   $982k    |      $970k          |  $10.13M
 23  |     7     |    $407k       |  $1.02M    |      $988k          |  $10.44M
 24  |     7     |    $422k       |  $1.06M    |     $1.04M          |  $10.75M
...
```

---

## Portfolio-Level Aggregation

All metrics shown are **portfolio-level totals**:
- ✅ Total distributions across all properties
- ✅ Average monthly distribution for the entire portfolio
- ✅ Cumulative over entire simulation period
- ✅ No per-unit breakdown (future enhancement)

---

## Next Steps (Future Enhancements)

If you want unit-level distribution tracking:

1. **Unit Comparison Page** - Show which properties fund distributions
2. **Distribution Allocation Logic** - Track distribution source by unit
3. **Dedicated Distributions Page** - Deep-dive analysis with:
   - Cumulative distribution chart
   - Distribution vs NOI comparison
   - Monthly detail table
   - Distribution rate trends

For now, the portfolio-level aggregation shows total distributions clearly and simply.

---

## Files Modified

- `ui/app.py` - Added 5th metric card for total distributions
- `ui/pages/4_time_series.py` - Added:
  - Distribution summary section (4 KPIs)
  - Distribution Amount checkbox
  - Chart marker for distribution start
  - Annual Distributions column in table

---

## Testing

1. **Run simulation with distributions enabled:**
   ```bash
   python run_quick.py
   ```

2. **Launch UI:**
   ```bash
   streamlit run ui/app.py
   ```

3. **Check homepage** - See total distributions metric

4. **Go to Time Series page** - See:
   - Summary at top
   - Distribution Amount checkbox
   - Gold line on chart
   - Annual Distributions column in table

---

## Current Configuration

Default setup distributes **$10.58M** over 9 years starting in Year 22.

To change:
- Edit `ob_str_engine/OB_STR_ENGINE_V2_3.json`
- Or use UI **Run Control → Distributions** tab
- Change trigger (startYear, maxLTV, or minDistributableAmount)
- Adjust distributionPct (0.0-1.0)
