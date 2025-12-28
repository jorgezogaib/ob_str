# Data Completeness Assessment for UI Development

**Purpose:** Confirm what data/functionality exists for building a UI that seasoned STR investors would love.

**Context:** You plan to build a UI with a Config page (edit JSON, rerun simulation). This assessment focuses on what data is available in the simulation output, not UI/UX design.

---

## ✅ DATA AVAILABLE - Ready for UI

### Portfolio-Level Data (360 monthly rows)

#### Financial Metrics
| Metric | Column Name | Format | Notes |
|--------|-------------|--------|-------|
| **Portfolio Value** | Total Portfolio Value | Currency | Monthly snapshot |
| **Total Debt** | Total Debt | Currency | All mortgages combined |
| **Total Equity** | Total Equity | Currency | Value - Debt |
| **LTV %** | LTV % | Percentage | Loan-to-value ratio |
| **Properties Owned** | Properties Owned | Integer | Count of units |
| **Property Market Value** | Property Market Value | Currency | Most recently acquired property |

#### Income & Expenses
| Metric | Column Name | Format | Notes |
|--------|-------------|--------|-------|
| **Rental Income** | Monthly Rental Income | Currency | Gross rental revenue |
| **Property Management** | Property Management | Currency | Management fees (20% baseline) |
| **CapEx & Maintenance** | CapEx & Maintenance | Currency | 10% of revenue |
| **HOA Fees** | HOA Fees | Currency | Monthly HOA |
| **Property Insurance** | Property Insurance | Currency | Insurance expense |
| **Property Taxes** | Property Taxes | Currency | Monthly property tax |
| **Debt Service** | Debt Service | Currency | All mortgage payments |

#### Cash Flow Metrics
| Metric | Column Name | Format | Notes |
|--------|-------------|--------|-------|
| **Net Operating Income** | Net Operating Income | Currency | Income - Operating Expenses |
| **Operating Cash Flow** | Operating Cash Flow | Currency | NOI - Debt Service |
| **Distributable Cash Flow** | Distributable Cash Flow | Currency | Operating CF - Reserve Topups |
| **Cash Flow After Debt Service** | Cash Flow After Debt Service | Currency | Legacy metric |

#### Cash Reserves
| Metric | Column Name | Format | Notes |
|--------|-------------|--------|-------|
| **Operating Cash** | Operating Cash | Currency | Main checking account |
| **Emergency Reserve** | Emergency Reserve | Currency | Rainy day fund (5 months expenses) |
| **Growth Savings** | Growth Savings | Currency | Accumulation for acquisitions |
| **Total Cash Reserves** | Total Cash Reserves | Currency | Sum of all cash accounts |
| **Required Reserves** | Required Reserves | Currency | Minimum reserve requirement |
| **Available Liquidity** | Available Liquidity | Currency | Cash available for use |

#### Interest & Earnings
| Metric | Column Name | Format | Notes |
|--------|-------------|--------|-------|
| **Total Interest Earned** | Total Interest Earned | Currency | All interest income |
| **Interest - Operating** | Interest - Operating | Currency | Operating account interest |
| **Interest - Reserve** | Interest - Reserve | Currency | Reserve account interest |
| **Interest - Savings** | Interest - Savings | Currency | Savings account interest |

#### Acquisition & Financing
| Metric | Column Name | Format | Notes |
|--------|-------------|--------|-------|
| **Property Purchase** | Property Purchase | Currency | Purchase price (if acquisition month) |
| **Down Payment** | Down Payment | Currency | Down payment paid |
| **Closing Costs** | Closing Costs | Currency | Closing costs paid |
| **Total Acquisition Cost** | Total Acquisition Cost | Currency | Down + Closing |
| **Refinance Proceeds** | Refinance Proceeds | Currency | Cash-out from refi |
| **Principal Prepayment** | Principal Prepayment | Currency | Extra principal paid |
| **Savings Deposit** | Savings Deposit | Currency | Deposits to growth savings |

#### Internal Tracking (for debugging/validation)
| Metric | Column Name | Format | Notes |
|--------|-------------|--------|-------|
| **_RainyTarget** | _RainyTarget | Currency | Emergency reserve target |
| **_RainyTopup** | _RainyTopup | Currency | Emergency reserve deposits |
| **_RainySweep** | _RainySweep | Currency | Emergency reserve sweeps |
| **_CapexBalance** | _CapexBalance | Currency | CapEx reserve balance |
| **_CapexSweep** | _CapexSweep | Currency | CapEx reserve sweeps |
| **_FreezeFlag** | _FreezeFlag | Boolean | Acquisition freeze flag |
| **_FeederIndex** | _FeederIndex | Integer | Index of feeder property |
| **_FeederLTV** | _FeederLTV | Percentage | Feeder property LTV |
| **_RefiPropertyIndex** | _RefiPropertyIndex | Integer | Index of property being refinanced |

**Total Portfolio Columns:** 46

---

### Unit-Level Data (1,604 unit-month rows)

#### Property Identification
| Metric | Column Name | Format | Notes |
|--------|-------------|--------|-------|
| **Year** | Year | Integer | Simulation year (1-30) |
| **Month** | Month | Integer | Month (1-12) |
| **Unit ID** | Unit_ID | Integer | Unique property identifier (0-6) |
| **Is Feeder** | Is_Feeder | Boolean | True if current feeder property |
| **Unit Age** | Unit_Age_Months | Integer | Months since purchase |

#### Property Valuation
| Metric | Column Name | Format | Notes |
|--------|-------------|--------|-------|
| **Property Value** | Unit_Value | Currency | Current market value |
| **Mortgage Balance** | Unit_Debt | Currency | Remaining loan balance |
| **Equity** | Unit_Equity | Currency | Value - Debt |
| **LTV %** | Unit_LTV | Percentage | Loan-to-value ratio |

#### Debt & Payments
| Metric | Column Name | Format | Notes |
|--------|-------------|--------|-------|
| **Monthly Payment** | Unit_Monthly_Payment | Currency | Monthly debt service |
| **Interest Rate** | Unit_Interest_Rate | Percentage | Current mortgage rate |
| **Months Since Refi** | Months_Since_Last_Refi | Integer | Refi cooldown tracking |

#### Income (Allocated)
| Metric | Column Name | Format | Notes |
|--------|-------------|--------|-------|
| **Rental Income** | Unit_Rental_Income | Currency | Proportional by value |

#### Expenses (Allocated)
| Metric | Column Name | Format | Notes |
|--------|-------------|--------|-------|
| **Property Management** | Unit_Property_Mgmt | Currency | Proportional by value |
| **CapEx & Maintenance** | Unit_CapEx | Currency | Proportional by value |
| **HOA Fees** | Unit_HOA | Currency | Proportional by value |
| **Insurance** | Unit_Insurance | Currency | Proportional by value |
| **Property Taxes** | Unit_Property_Tax | Currency | Proportional by value |
| **Total Expenses** | Unit_Total_Expenses | Currency | Sum of all expenses |
| **Debt Service** | Unit_Debt_Service | Currency | Actual payment (not allocated) |

#### Cash Flow Metrics
| Metric | Column Name | Format | Notes |
|--------|-------------|--------|-------|
| **Net Operating Income** | Unit_NOI | Currency | Income - Operating Expenses |
| **Operating Cash Flow** | Unit_Operating_CF | Currency | NOI - Debt Service |

#### Expense Ratios (% of Revenue)
| Metric | Column Name | Format | Notes |
|--------|-------------|--------|-------|
| **Total Expense Ratio** | Unit_Expense_Ratio | Percentage | All expenses / revenue |
| **Management Fee Ratio** | Unit_Mgmt_Fee_Ratio | Percentage | Mgmt fees / revenue |
| **CapEx Ratio** | Unit_CapEx_Ratio | Percentage | CapEx / revenue |
| **NOI Margin** | Unit_NOI_Margin | Percentage | NOI / revenue |

#### Return Metrics ✅ **NEWLY ADDED**
| Metric | Column Name | Format | Notes |
|--------|-------------|--------|-------|
| **Cash Invested** | Unit_Cash_Invested | Currency | Down payment + closing costs |
| **Cash-on-Cash Return** | Unit_Cash_On_Cash_Return | Percentage | Annual Operating CF / Cash Invested |
| **Cap Rate** | Unit_Cap_Rate | Percentage | Annual NOI / Property Value |
| **DSCR** | Unit_DSCR | Ratio | NOI / Debt Service (>1.0 = healthy) |
| **ROI** | Unit_ROI | Percentage | (Equity - Cash Invested) / Cash Invested |

**Total Unit Columns:** 31

---

### Cash Flow Waterfall Data (via reports.py functions)

#### Portfolio Waterfall
**Function:** `cash_flow_waterfall(df, year, month=12)`

**Returns:** DataFrame with sequential cash flow for any month
- Starting Operating Cash
- All income sources (rental, interest, refinance proceeds)
- All expenses (management, capex, HOA, insurance, taxes)
- Checkpoints: NOI, Operating CF, Distributable CF
- All uses of cash (prepayments, savings, acquisitions)
- Running balance throughout
- Ending Operating Cash

**Use Case:** "Show me exactly where every dollar went in Year 5, Month 4"

#### Per-Unit Waterfall
**Function:** `unit_cash_flow_waterfall(unit_df, unit_id, year, month=12)`

**Returns:** DataFrame with cash flow for individual property
- Rental income
- All allocated expenses
- Unit NOI
- Unit debt service
- Unit operating cash flow

**Use Case:** "Show me cash flow breakdown for Unit 3 in Year 15"

---

## ⚠️ DATA GAPS - Missing for UI

### STR-Specific Operational Metrics (CRITICAL GAP)

#### Occupancy Tracking
| What's Missing | Why It Matters | Current State |
|----------------|----------------|---------------|
| **Actual Occupancy Rate** | Can't track performance vs baseline | Fixed 78% assumption |
| **Nights Booked** | Can't calculate RevPAR | Not tracked |
| **Nights Available** | Can't analyze seasonal patterns | Not tracked |
| **Occupancy by Month** | Can't identify high/low seasons | Not tracked |
| **Occupancy by Unit** | Can't compare property performance | Not tracked |

**Impact:** UI can show revenue but NOT the drivers (was it ADR increase or occupancy increase?)

#### ADR (Average Daily Rate) Tracking
| What's Missing | Why It Matters | Current State |
|----------------|----------------|---------------|
| **Actual ADR** | Can't track pricing trends | Fixed $425 baseline (2BR) |
| **ADR by Month** | Can't optimize seasonal pricing | Not tracked |
| **ADR by Unit** | Can't identify pricing opportunities | Not tracked |
| **ADR Growth Rate** | Can't measure pricing power | Not tracked |

**Impact:** UI shows total revenue but can't answer "Should I raise rates on Unit 3?"

#### Revenue Metrics
| What's Missing | Why It Matters | Current State |
|----------------|----------------|---------------|
| **RevPAR** | Key STR performance metric | Not calculated |
| **Revenue per Night** | Industry benchmark | Not calculated |
| **Booking Pace** | Forward-looking indicator | Not tracked |

**Impact:** Can't benchmark against market or other STR portfolios

---

### Seasonality & Trends (MEDIUM GAP)

| What's Missing | Why It Matters | Current State |
|----------------|----------------|---------------|
| **Monthly Patterns** | Identify high/low seasons | Assumes constant performance |
| **Year-over-Year Growth** | Track historical trends | Can calculate from data |
| **Market Appreciation vs Rent Growth** | Separate value drivers | Both use fixed rates |

**Impact:** UI can't show "Q1 is historically weak (65% occupancy) vs Q3 (90%)"

---

### Performance Benchmarking (SMALL GAP)

| What's Missing | Why It Matters | Current State |
|----------------|----------------|---------------|
| **Market Comparisons** | Context for performance | No market data |
| **Property Rankings** | Identify top/bottom performers | ✅ Can calculate from existing data |
| **Peer Benchmarks** | Compare to similar portfolios | No peer data |

**Impact:** Can rank your own properties but can't say "Your 6% Cap Rate is above/below market average of 5%"

---

### Historical Events & Milestones (SMALL GAP)

| What's Missing | Why It Matters | Current State |
|----------------|----------------|---------------|
| **Acquisition Events Table** | Timeline of purchases | ✅ Can filter from monthly data |
| **Refinance Events Table** | Timeline of refis | ✅ Can filter from monthly data |
| **Debt Payoff Events** | When properties became debt-free | ✅ Can detect from unit data |
| **Feeder Changes** | When feeder switched | ✅ Can detect from monthly data |

**Impact:** Minor - can extract events from existing data, but dedicated tables would be cleaner

---

### Tax & Accounting (MEDIUM GAP - if needed)

| What's Missing | Why It Matters | Current State |
|----------------|----------------|---------------|
| **Depreciation Schedule** | Tax deductions | Not tracked |
| **Adjusted Basis** | Capital gains calculation | Not tracked |
| **1031 Exchange Planning** | Tax-deferred swaps | Not tracked |
| **Interest vs Principal Split** | Tax deductibility | Not tracked separately |

**Impact:** Can't answer "What's my depreciation deduction for Unit 2?" without manual calculation

---

### Scenario Comparison (NOT A DATA GAP - WORKFLOW GAP)

| What's Missing | Why It Matters | Current State |
|----------------|----------------|---------------|
| **Side-by-Side Scenarios** | Compare strategies | Run simulation once per scenario |
| **Sensitivity Analysis** | Stress-test assumptions | Manual re-runs required |
| **Monte Carlo Results** | Risk-adjusted projections | Not implemented |

**Impact:** This is a **workflow** issue, not a data issue. Your planned Config page + rerun button handles this perfectly. UI just needs to store/compare multiple simulation results.

---

## 🎯 RECOMMENDATIONS FOR UI DEVELOPMENT

### TIER 1: Use Existing Data (No Code Changes Needed)

Your UI can immediately support:

✅ **Portfolio Dashboard**
- Total value, debt, equity, LTV over time (line charts)
- Cash reserves breakdown (stacked area chart)
- Monthly/annual income and expenses (bar charts)
- Properties owned progression

✅ **Unit Performance Comparison**
- Property rankings by Cash-on-Cash, ROI, Operating CF
- Side-by-side unit comparison (table or bar chart)
- Expense ratio analysis by property
- Return metrics dashboard

✅ **Cash Flow Analysis**
- Portfolio-level waterfall for any month
- Per-unit waterfall for any property
- Cash flow trends over time

✅ **Acquisition & Debt Tracking**
- Purchase timeline visualization
- Refinancing events timeline
- Debt payoff progression
- Feeder property tracking

✅ **Config Page with Rerun**
- Edit all JSON parameters
- Run new simulation
- Compare old vs new results side-by-side

### TIER 2: Add Seasonality (Small Code Change)

**What to add:**
```json
"seasonality": {
  "monthlyOccupancyFactors": [0.85, 0.80, 0.90, 0.95, 1.05, 1.10, 1.15, 1.10, 1.00, 0.90, 0.75, 0.80],
  "monthlyADRFactors": [0.90, 0.90, 1.00, 1.05, 1.10, 1.15, 1.20, 1.15, 1.05, 1.00, 0.85, 0.95]
}
```

**Impact:**
- Monthly revenue heatmap (occupancy/ADR by month and property)
- Seasonal trend analysis
- Peak/off-peak identification

**Effort:** ~4 hours to implement in simulator

### TIER 3: Add Actual STR Metrics (Medium Code Change)

**What to add:**
- Track actual occupancy rate (nights booked / nights available)
- Track actual ADR per booking
- Calculate RevPAR (Revenue Per Available Room)
- Calculate revenue per night

**Impact:**
- Industry-standard STR metrics
- Identify operational improvement opportunities
- Benchmark against market

**Effort:** ~8-12 hours to implement

### TIER 4: Add Tax Tracking (Optional - Low Priority)

**What to add:**
- Per-property depreciation schedules
- Adjusted basis tracking
- Interest vs principal breakdown

**Impact:**
- Tax planning capability
- 1031 exchange planning
- Depreciation deduction tracking

**Effort:** ~6-8 hours to implement

---

## ✅ FINAL ASSESSMENT: DATA READINESS FOR UI

### What You Have Now (Excellent Foundation)

**Financial Modeling:** ⭐⭐⭐⭐⭐ World-class
- 30-year projections
- Monthly granularity
- Portfolio & unit-level tracking
- Cash flow waterfalls
- Return metrics (Cash-on-Cash, ROI, Cap Rate, DSCR)
- Expense ratios

**Acquisition Strategy:** ⭐⭐⭐⭐⭐ Complete
- Purchase timeline
- Refinancing strategy
- Feeder property logic
- Debt payoff tracking

**Cash Management:** ⭐⭐⭐⭐⭐ Complete
- Reserve management
- Interest earnings
- Capital allocation
- Liquidity tracking

**Property-Level Insights:** ⭐⭐⭐⭐⭐ Excellent
- Individual property tracking
- Per-unit cash flow
- Performance metrics
- Comparative analysis capability

### What's Missing for Seasoned STR Investors

**STR Operational Metrics:** ⭐⚪⚪⚪⚪ Critical Gap
- No occupancy tracking
- No ADR trends
- No RevPAR calculation
- No seasonality analysis

**Market Benchmarking:** ⭐⚪⚪⚪⚪ Nice-to-Have
- No market comparisons
- No peer benchmarks
- Can rank your own properties ✅

**Tax & Accounting:** ⭐⚪⚪⚪⚪ Optional
- No depreciation tracking
- No adjusted basis
- No 1031 planning

### Bottom Line: Can You Build a Great UI Today?

**YES - with caveats:**

✅ **Excellent for Financial Analysis**
- Portfolio performance tracking
- Property comparison
- Return metrics
- Cash flow analysis
- Debt strategy visualization

✅ **Excellent for Strategy Planning**
- Config page with rerun
- Scenario comparison (run multiple configs)
- Acquisition timeline
- Refinance opportunities

⚠️ **Limited for STR Operations**
- Can't track occupancy trends
- Can't analyze pricing power
- Can't identify seasonal patterns
- Can't calculate RevPAR

### Recommendation

**Build the UI now** with existing data. You have everything needed for:
1. Portfolio dashboard with key metrics
2. Property comparison and rankings
3. Cash flow analysis and waterfalls
4. Config editor with scenario comparison
5. Acquisition and debt tracking

**Then add STR metrics** (Tier 2/3) if operational analysis becomes important. For pure financial modeling and strategy planning, current data is **excellent**.

---

## Data Export Summary

### Current Export Capability

**Portfolio Monthly:** `out/simulation_results_feeder.csv` (360 rows, 46 columns)
**Unit Monthly:** Available in `result.units` DataFrame (1,604 rows, 31 columns) - not auto-exported yet
**Waterfalls:** Generated on-demand via report functions

### Recommended Exports for UI

```python
# Standard exports
result.monthly.to_csv('out/portfolio_monthly.csv')
result.units.to_csv('out/units_monthly.csv')

# Derived reports
executive_summary_report(result.monthly, annual=True).to_csv('out/executive_summary.csv')
year_over_year_summary(result.monthly).to_csv('out/year_over_year.csv')
unit_breakdown_report(result.units, year=15).to_csv('out/units_year15.csv')

# Event tables (filter from monthly data)
acquisitions = result.monthly[result.monthly['Property Purchase'] > 0]
acquisitions.to_csv('out/acquisition_events.csv')

refis = result.monthly[result.monthly['Refinance Proceeds'] > 0]
refis.to_csv('out/refinance_events.csv')
```

---

## Conclusion

**You have excellent data** for building a UI that seasoned investors would love. The financial modeling, property tracking, and return metrics are world-class.

**The main gap** is STR-specific operational metrics (occupancy, ADR, RevPAR), which are more relevant for active operators than passive investors.

**Your planned UI approach** (Config page + rerun) is perfect for scenario analysis and strategic planning.

**Next steps:**
1. Build UI with existing data (portfolio dashboard, property comparison, config editor)
2. Add seasonality (Tier 2) if you want monthly patterns
3. Add full STR metrics (Tier 3) if operational optimization becomes a priority

**Data is UI-ready today.** Go build!
