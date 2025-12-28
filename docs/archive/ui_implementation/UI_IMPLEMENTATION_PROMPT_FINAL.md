# STR Investment Model - Refinement Workbench UI Implementation

## Mission

Build a **Model Refinement Workbench** UI that allows rapid iteration on model assumptions, validation of model behavior, and deep analysis of simulation results. This is a tool for **refining the model**, not presenting to investors.

---

## Tech Stack (User Confirmed)

**Framework:** Streamlit (Python web framework)
- Fast to build, Python-native, good charting libraries
- Launch: `streamlit run ui/app.py` opens in browser automatically

**Visualization:** Plotly
- Interactive charts with zoom, pan, hover tooltips
- Good for exploration and understanding model behavior
- Template: `plotly_dark` for dark mode, `plotly_white` for light mode

**Data:** Pandas DataFrames
- Already used by simulation engine
- Direct compatibility with Streamlit

**Launcher:** Windows Batch File
- Simple double-click to launch
- Desktop shortcut for easy access

**File Location:** `ui/` folder in project root

**Caching Strategy:** Hybrid approach
- Quick load of cached results
- Option to rerun simulation
- Clear cache functionality for historical runs

**Theme Strategy:** Dark/Light mode toggle
- Default: Dark mode (easier on eyes for long sessions)
- Toggle in sidebar to switch themes
- Persist preference in session state
- Custom dark theme config for Streamlit
- Plotly charts adapt to theme automatically

---

## Project Context

### Existing Code Structure

```
C:\Users\jorge\.claude-worktrees\ob_str\gracious-golick\
├── ob_str_engine/
│   ├── OB_STR_ENGINE_V2_3.json        # Config file (all model parameters)
│   └── engine/
│       ├── simulator.py                # Core simulation logic
│       ├── types.py                    # SimulationResult, Unit dataclasses
│       ├── reports.py                  # Report generation functions
│       ├── config.py                   # Config loading
│       └── [other modules]             # Acquisition, debt, reserves, etc.
├── out/
│   └── simulation_results_feeder.csv   # Portfolio-level results (360 rows × 46 cols)
├── run_quick.py                         # Quick test script
├── DATA_COMPLETENESS_FOR_UI.md         # Full data documentation
└── [Create new] ui/                     # NEW FOLDER FOR UI
```

### How to Run Simulation

```python
from pathlib import Path
from ob_str_engine.engine.simulator import simulate

# Run 30-year simulation
result = simulate(Path('ob_str_engine/OB_STR_ENGINE_V2_3.json'), years=30)

# Access data
portfolio_df = result.monthly    # 360 rows (30 years × 12 months), 46 columns
units_df = result.units          # 1,604 rows (unit-month records), 31 columns
```

### Key Data Available

**Portfolio DataFrame (360 rows, 46 columns):**
- Financial: Total Portfolio Value, Total Debt, Total Equity, LTV%
- Income/Expenses: Monthly Rental Income, Property Management, CapEx & Maintenance, HOA Fees, Property Insurance, Property Taxes, Debt Service
- Cash Flow: Net Operating Income, Operating Cash Flow, Distributable Cash Flow
- Cash Accounts: Operating Cash, Emergency Reserve, Growth Savings, Total Cash Reserves
- Events: Property Purchase, Down Payment, Closing Costs, Refinance Proceeds, Principal Prepayment, Savings Deposit
- Internal: _FeederIndex, _FeederLTV, _RefiPropertyIndex, _RainyTopup, _RainySweep, _CapexBalance, _CapexSweep, _FreezeFlag

**Units DataFrame (1,604 rows, 31 columns):**
- Identification: Year, Month, Unit_ID, Is_Feeder, Unit_Age_Months, Months_Since_Last_Refi
- Valuation: Unit_Value, Unit_Debt, Unit_Equity, Unit_LTV, Unit_Monthly_Payment, Unit_Interest_Rate
- Income/Expenses: Unit_Rental_Income, Unit_Property_Mgmt, Unit_CapEx, Unit_HOA, Unit_Insurance, Unit_Property_Tax, Unit_Debt_Service, Unit_Total_Expenses
- Cash Flow: Unit_NOI, Unit_Operating_CF
- Expense Ratios: Unit_Expense_Ratio, Unit_Mgmt_Fee_Ratio, Unit_CapEx_Ratio, Unit_NOI_Margin
- Return Metrics: Unit_Cash_Invested, Unit_Cash_On_Cash_Return, Unit_Cap_Rate, Unit_DSCR, Unit_ROI

**Report Functions Available:**
```python
from ob_str_engine.engine.reports import (
    cash_flow_waterfall,           # Portfolio waterfall for any month
    unit_cash_flow_waterfall,      # Per-unit waterfall
    executive_summary_report,       # High-level summary
    year_over_year_summary,         # Annual metrics
)

# Example: Get waterfall for Year 5, Month 4
waterfall_df = cash_flow_waterfall(result.monthly, year=5, month=4)
# Returns DataFrame with columns: Category, Amount, Running_Balance
```

### Config File Structure (JSON)

See full structure in `ob_str_engine/OB_STR_ENGINE_V2_3.json`

**Key sections:**
- `constants.financial`: startingCash, annualSavings, amortizationYears
- `constants.operations`: adrBaseline2BR, occupancyBaseline, mgmtPct, capexPct, hoaAnnual, insuranceRate, propertyTaxRate
- `constants.acquisition`: downPaymentFirst, downPaymentSubsequent, closingCostPct, targetYieldUnlevered, maxPostRefiLTV, refiCooldownYears, dscrThresholdForRefi, refiCashoutStrategy
- `constants.debt`: mortgageRate, refiRate
- `constants.reserves`: capexMonthsTarget, enableCapexCeiling, capexCeilingMonths, enableRainySweep, rainyBufferPct
- `market`: annualAppreciation, revenueInflationRate
- `banking`: rainyCoverageMonths, operatingCashMonths, refiLTVTrigger, cashoutCostPct, cashInterestRate, purchaseReserveMonths
- `policies.portfolio`: maxUnits, stopRefiAtMaxUnits
- `policies.capitalAllocation`: feederPrepaymentPct, savingsAccumulationPct

---

## Core User Workflow (The Iteration Loop)

1. **Load or run baseline simulation** → See Year 30 outcomes
2. **Validate model behavior** → Check acquisition timeline, reserve mechanics, feeder logic
3. **Form hypothesis** → "What if I increase CapEx reserves from 6 to 12 months?"
4. **Adjust config** → Edit parameter in UI
5. **Rerun simulation** → Get new results
6. **Compare results** → See what changed (outcomes and behavior)
7. **Gain insight** → Understand why outcomes changed
8. **Iterate** → Refine assumption, test again

**UI must minimize friction in this loop. Target: < 10 seconds from "I want to test X" to "here are results".**

---

## File Structure to Create

```
ui/
├── app.py                          # Main Streamlit app (entry point)
├── requirements.txt                # Python dependencies
├── .streamlit/
│   └── config.toml                 # Dark mode theme config
├── pages/
│   ├── 1_run_control.py            # Page 1: Run Control & Config
│   ├── 2_model_validation.py      # Page 2: Validation Dashboard
│   ├── 3_cash_flow_anatomy.py     # Page 3: Cash Flow Deep Dive
│   ├── 4_time_series.py           # Page 4: Time Series Analysis
│   ├── 5_unit_comparison.py       # Page 5: Unit-Level Comparison
│   └── 6_scenario_comparison.py   # Page 6: Scenario Matrix
├── components/
│   ├── config_editor.py            # Reusable config form component
│   ├── kpi_cards.py                # Reusable KPI card component
│   ├── charts.py                   # Chart generation functions
│   └── validation.py               # Validation check functions
├── utils/
│   ├── simulation_runner.py        # Wrapper for running simulations
│   ├── data_loader.py              # Load/cache simulation results
│   └── scenario_manager.py         # Save/load scenarios
├── scenarios/                       # Saved scenario configs (auto-created)
│   ├── base_case.json
│   ├── conservative.json
│   └── aggressive.json
└── cache/                           # Cached simulation results (auto-created)
    └── [timestamp]_[scenario_name].pkl

Project root:
├── Launch_STR_Dashboard.bat        # Desktop launcher (auto-opens browser)
```

---

## Page Structure (Implementation Priority Order)

### Page 1: Run Control & Config ⭐ HIGHEST PRIORITY

**Purpose:** Primary command center for rapid iteration

**Layout:** 3-column layout using `st.columns([3, 4, 3])`

#### Left Column (30% width): Configuration Editor

**Tabbed Interface** (`st.tabs()`) for config editing:

**Tab 1: Financial**
- Starting Cash (number_input, default: $5,000)
- Annual Savings (number_input, default: $50,000)
- Amortization Years (number_input, default: 30)

**Tab 2: Operations**
- ADR Baseline 2BR (number_input, default: $425)
- Occupancy Baseline (slider, 0.0-1.0, default: 0.78)
- Management % (slider, 0.0-0.50, default: 0.20)
- CapEx % (slider, 0.0-0.30, default: 0.10)
- HOA Annual (number_input, default: $12,800)
- HOA Inflation Rate (slider, 0.0-0.10, default: 0.04)
- Insurance Rate (slider, 0.0-0.10, default: 0.033)
- Property Tax Rate (slider, 0.0-0.02, default: 0.0055)

**Tab 3: Acquisition**
- Down Payment First (slider, 0.10-0.50, default: 0.20)
- Down Payment Subsequent (slider, 0.10-0.50, default: 0.25)
- Closing Cost % (slider, 0.01-0.10, default: 0.03)
- Max Units (number_input, default: 7)
- Target Yield Unlevered (slider, 0.03-0.10, default: 0.065)
- Max Post-Refi LTV (slider, 0.60-0.85, default: 0.75)
- Refi Cooldown Years (number_input, default: 3)
- DSCR Threshold for Refi (slider, 1.0-2.0, default: 1.20)
- Refi Cashout Strategy (selectbox: ["max", "conservative"])
- Stop Refi at Max Units (checkbox, default: True)

**Tab 4: Debt**
- Mortgage Rate (slider, 0.03-0.10, default: 0.0685)
- Refi Rate (slider, 0.03-0.10, default: 0.05875)

**Tab 5: Reserves**
- CapEx Months Target (number_input, default: 6)
- Enable CapEx Ceiling (checkbox, default: True)
- CapEx Ceiling Months (number_input, default: 6)
- Enable Rainy Sweep (checkbox, default: True)
- Rainy Buffer % (slider, 1.0-2.0, default: 1.2)
- Rainy Coverage Months (number_input, default: 5)
- Operating Cash Months (number_input, default: 1)
- Purchase Reserve Months (number_input, default: 6)

**Tab 6: Capital Allocation**
- Feeder Prepayment % (slider, 0.0-1.0, default: 0.70)
- Savings Accumulation % (slider, 0.0-1.0, default: 0.30)
- Auto-validate: sum = 1.0, show warning if not

**Tab 7: Market**
- Annual Appreciation (slider, 0.0-0.10, default: 0.03)
- Revenue Inflation Rate (slider, 0.0-0.10, default: 0.04)

**Below Tabs: Preset Scenarios**
- Dropdown: Select from saved scenarios
  - Base Case (current OB_STR_ENGINE_V2_3.json)
  - [List all .json files in ui/scenarios/]
- "Load Selected Scenario" button (loads into form fields)

**Action Buttons (big, prominent):**
- 🔄 **Run Simulation** (primary button, blue/green)
  - Shows spinner while running
  - Updates session_state with results
  - Adds to run history
- 💾 **Save Config As...** (secondary button)
  - Text input for scenario name
  - Saves to ui/scenarios/{name}.json
- 📂 **Load Base Case** (tertiary button)
  - Resets form to OB_STR_ENGINE_V2_3.json values

#### Middle Column (40% width): Immediate Results

**Show AFTER simulation runs** (hide if no results yet)

**KPI Cards** (use `st.metric()` with delta):
- Final Portfolio Value (Year 30)
  - Show: $12,871,116.95
  - Delta vs previous run (if available): +$2.1M (+16%)
- Total Equity (Year 30)
  - Show: $12,871,116.95
  - Delta vs previous: +$1.8M
- Properties Acquired
  - Show: 7 of 7
  - Show year hit max: Year 15
- Years to Debt-Free
  - Show: Year 22
  - Delta vs previous: -2 years (better)
- Total Cash Reserves (Year 30)
  - Show: $12,409,736.42
- Total Interest Earned (30 years)
  - Show: $2,141,813.93

**Validation Status:**
Use expander with summary status:
```python
with st.expander("✅ Model Validation: All Checks Passed", expanded=False):
    st.success("✅ All properties acquired (7 of 7)")
    st.success("✅ No cash shortfalls (Operating Cash never negative)")
    st.success("✅ Debt payoff completed (Year 22)")
    st.success("✅ Reserves maintained (Emergency Reserve always >= required)")
```

If any failures:
```python
with st.expander("⚠️ Model Validation: 1 Warning", expanded=True):
    st.success("✅ All properties acquired (7 of 7)")
    st.warning("⚠️ Feeder not tracked in 106 months")
    st.success("✅ Debt payoff completed (Year 22)")
```

**Mini Charts** (use Plotly):
1. Portfolio Value over 30 years (line chart, green)
2. Total Debt over 30 years (line chart, red declining to 0)
3. Properties Owned timeline (step chart, 0→7)

#### Right Column (30% width): Run History & Comparison

**Run History Table:**
- Use `st.dataframe()` with selection enabled
- Columns: Timestamp, Scenario Name, Final Value, Properties, Years to Debt-Free
- Show last 10 runs (newest first)
- Click row to reload that scenario (repopulate form fields and results)

**Above table: Clear History Button:**
```python
if st.button("🗑️ Clear Run History"):
    st.session_state.run_history = []
    # Also clear cache/ folder
    st.rerun()
```

**Compare Mode:**
- Checkboxes on each row to select 2-3 runs
- "Compare Selected" button
- When clicked, show comparison table below:

**Comparison Table** (when 2-3 runs selected):
```
Metric               | Run A      | Run B      | Delta
---------------------|------------|------------|-------------
Final Value          | $12.87M    | $11.23M    | -$1.64M (-13%)
Properties           | 7          | 7          | 0
Years to Debt-Free   | 22         | 25         | +3 years
Total Cash Reserves  | $12.41M    | $10.85M    | -$1.56M
```

**Config Diff** (when comparing):
- Show which parameters changed between runs
- Example: "ADR: $425 → $400 (-5.9%)"
- Example: "CapEx%: 10% → 12% (+20%)"

---

### Page 2: Model Validation Dashboard

**Purpose:** Verify model logic is working correctly

**Use `st.tabs()` for different validation areas:**

#### Tab 1: Acquisition Logic

**Acquisition Timeline Chart:**
- Step chart showing cumulative properties (0→7) over time
- X-axis: Years 1-30
- Y-axis: Properties owned (0-7)
- Annotations on each step showing: Year, Month, Purchase Price
- Use Plotly `shapes` to annotate

**Acquisition Feasibility Table:**
```python
st.subheader("Acquisition Feasibility Check")

# Filter to acquisition months
acq_months = portfolio_df[portfolio_df['Property Purchase'] > 0]

# Create table
st.dataframe(acq_months[[
    'Year', 'Month',
    'Operating Cash',  # Available cash before purchase
    'Down Payment',    # Required
    'Closing Costs',   # Required
    'Property Purchase',  # Total cost
    'Refinance Proceeds',  # Source (if any)
    'Growth Savings'   # Source (if used)
]], use_container_width=True)
```

**Validation:**
```python
# Check if any month had insufficient cash
shortfalls = acq_months[acq_months['Operating Cash'] < (acq_months['Down Payment'] + acq_months['Closing Costs'])]

if len(shortfalls) == 0:
    st.success("✅ All acquisitions were feasible (sufficient cash available)")
else:
    st.error(f"❌ {len(shortfalls)} acquisition(s) had cash shortfalls!")
    st.dataframe(shortfalls)
```

#### Tab 2: Reserve Mechanics

**Reserve Balances Chart:**
- 3 lines: Emergency Reserve, Growth Savings, Operating Cash
- Dashed line: Required Emergency Reserve
- Markers: Red dots for topup events, Green dots for sweep events
- Plotly line chart with annotations

**Reserve Event Log:**
```python
st.subheader("Reserve Events Log")

# Filter to months with reserve activity
topups = portfolio_df[portfolio_df['_RainyTopup'] > 0]
sweeps = portfolio_df[portfolio_df['_RainySweep'] > 0]

col1, col2 = st.columns(2)

with col1:
    st.write(f"**Topup Events:** {len(topups)}")
    st.dataframe(topups[['Year', 'Month', '_RainyTopup', 'Emergency Reserve', 'Required Reserves']])

with col2:
    st.write(f"**Sweep Events:** {len(sweeps)}")
    st.dataframe(sweeps[['Year', 'Month', '_RainySweep', 'Emergency Reserve']])
```

**Validation:**
```python
# Check topups only happen when below target
invalid_topups = topups[topups['Emergency Reserve'] >= topups['Required Reserves']]

if len(invalid_topups) == 0:
    st.success("✅ Topups only occurred when reserves below target")
else:
    st.error(f"❌ {len(invalid_topups)} topup(s) occurred when reserves already adequate")
```

#### Tab 3: Feeder Strategy

**Feeder Timeline:**
- Visual showing which unit was feeder over time
- Color-coded horizontal bars, one per year
- Hover shows: Unit ID, LTV at selection

**Feeder Changes Table:**
```python
# Detect when feeder changed
portfolio_df['Feeder_Changed'] = portfolio_df['_FeederIndex'].ne(portfolio_df['_FeederIndex'].shift())
feeder_changes = portfolio_df[portfolio_df['Feeder_Changed'] == True]

st.dataframe(feeder_changes[[
    'Year', 'Month', 'Properties Owned', '_FeederIndex', '_FeederLTV'
]], use_container_width=True)

st.success(f"✅ Feeder changed {len(feeder_changes)} times during simulation")
```

**Prepayment Allocation Chart:**
- Line: Feeder LTV declining over time
- Bar: Monthly prepayment amount
- Dual-axis Plotly chart

#### Tab 4: Refinance Logic

**Refi Events Table:**
```python
refi_events = portfolio_df[portfolio_df['Refinance Proceeds'] > 0]

st.subheader(f"Refinancing Events ({len(refi_events)} total)")

st.dataframe(refi_events[[
    'Year', 'Month', 'Properties Owned', '_RefiPropertyIndex',
    'Refinance Proceeds', 'Total Debt', '_FeederLTV'
]], use_container_width=True)
```

**Refi Eligibility Validation:**
```python
# Check if refi occurred after max units with stopRefiAtMaxUnits=true
max_units = st.session_state.config['policies']['portfolio']['maxUnits']
stop_refi = st.session_state.config['policies']['portfolio']['stopRefiAtMaxUnits']

if stop_refi:
    # Find month when hit max units
    max_units_month = portfolio_df[portfolio_df['Properties Owned'] == max_units].iloc[0]
    max_units_index = max_units_month.name

    # Check if any refis after that
    refis_after_max = refi_events[refi_events.index > max_units_index]

    if len(refis_after_max) == 0:
        st.success("✅ No refinancing occurred after reaching max units (stopRefiAtMaxUnits=true)")
    else:
        st.error(f"❌ {len(refis_after_max)} refinance(s) occurred after max units!")
```

#### Tab 5: Cash Reconciliation

**Operating Cash Chart:**
- Line: Operating Cash balance over 360 months
- Horizontal line at $0 (red zone)
- Horizontal line at Operating Minimum (yellow zone)
- Plotly chart with shaded areas

**Validation:**
```python
negative_months = portfolio_df[portfolio_df['Operating Cash'] < 0]

if len(negative_months) == 0:
    st.success("✅ Operating Cash never went negative")
else:
    st.error(f"❌ Operating Cash went negative in {len(negative_months)} month(s)!")
    st.dataframe(negative_months[['Year', 'Month', 'Operating Cash']])
```

**Month Detail Reconciliation:**
```python
st.subheader("Cash Reconciliation for Selected Month")

month_slider = st.slider("Select Month", 1, 360, 60)  # Default to month 60

row = portfolio_df.iloc[month_slider - 1]
prev_row = portfolio_df.iloc[month_slider - 2] if month_slider > 1 else None

# Build reconciliation table
if prev_row is not None:
    starting_cash = prev_row['Operating Cash']
else:
    starting_cash = st.session_state.config['constants']['financial']['startingCash']

inflows = row['Monthly Rental Income'] + row['Interest - Operating'] + row.get('Refinance Proceeds', 0)
outflows = (row['Property Management'] + row['CapEx & Maintenance'] + row['HOA Fees'] +
            row['Property Insurance'] + row['Property Taxes'] + row['Debt Service'] +
            row.get('_RainyTopup', 0) + row.get('Principal Prepayment', 0) +
            row.get('Savings Deposit', 0) + row.get('Down Payment', 0) + row.get('Closing Costs', 0))

calculated_ending = starting_cash + inflows - outflows
actual_ending = row['Operating Cash']

st.write(f"**Year {int(row['Year'])}, Month {int(row['Month'])}**")
st.write(f"Starting Cash: ${starting_cash:,.2f}")
st.write(f"+ Total Inflows: ${inflows:,.2f}")
st.write(f"- Total Outflows: ${outflows:,.2f}")
st.write(f"= Calculated Ending: ${calculated_ending:,.2f}")
st.write(f"Actual Ending: ${actual_ending:,.2f}")

if abs(calculated_ending - actual_ending) < 1.0:  # Allow $1 rounding error
    st.success("✅ Reconciliation matches")
else:
    st.error(f"❌ Discrepancy: ${abs(calculated_ending - actual_ending):,.2f}")
```

---

### Page 3: Deep Dive - Cash Flow Anatomy

**Purpose:** Understand cash movements for any specific month

#### Interactive Waterfall

**Month Selector:**
```python
col1, col2 = st.columns([1, 1])
with col1:
    year = st.selectbox("Year", range(1, 31))
with col2:
    month = st.selectbox("Month", range(1, 13))

# Quick jump buttons
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("First Acquisition"):
        # Jump to first acquisition month
        first_acq = portfolio_df[portfolio_df['Property Purchase'] > 0].iloc[0]
        year = int(first_acq['Year'])
        month = int(first_acq['Month'])
        st.rerun()
with col2:
    if st.button("First Refi"):
        first_refi = portfolio_df[portfolio_df['Refinance Proceeds'] > 0].iloc[0]
        year = int(first_refi['Year'])
        month = int(first_refi['Month'])
        st.rerun()
# ... etc
```

**Waterfall Chart:**
```python
from ob_str_engine.engine.reports import cash_flow_waterfall

waterfall_df = cash_flow_waterfall(portfolio_df, year=year, month=month)

# Create Plotly waterfall chart
import plotly.graph_objects as go

fig = go.Figure(go.Waterfall(
    name="Cash Flow",
    orientation="v",
    measure=["absolute"] + ["relative"] * (len(waterfall_df)-2) + ["total"],
    x=waterfall_df['Category'],
    y=waterfall_df['Amount'],
    text=waterfall_df['Amount'].apply(lambda x: f"${x:,.0f}"),
    textposition="outside",
    connector={"line": {"color": "rgb(63, 63, 63)"}},
    increasing={"marker": {"color": "green"}},
    decreasing={"marker": {"color": "red"}},
    totals={"marker": {"color": "blue"}}
))

fig.update_layout(
    title=f"Cash Flow Waterfall - Year {year}, Month {month}",
    showlegend=False,
    height=600
)

st.plotly_chart(fig, use_container_width=True)
```

**Running Commentary:**
```python
# Get the row for selected month
row = portfolio_df[(portfolio_df['Year'] == year) & (portfolio_df['Month'] == month)].iloc[0]

st.subheader("What Happened This Month")

# Build narrative
narrative = []

if row['Property Purchase'] > 0:
    narrative.append(f"🏠 **Property Acquired:** You purchased property for ${row['Property Purchase']:,.0f} "
                     f"with ${row['Down Payment']:,.0f} down payment and ${row['Closing Costs']:,.0f} closing costs.")

if row['Refinance Proceeds'] > 0:
    narrative.append(f"💰 **Refinance Event:** You refinanced a property and extracted ${row['Refinance Proceeds']:,.0f} in cash.")

if row['Principal Prepayment'] > 0:
    narrative.append(f"📉 **Debt Paydown:** You made ${row['Principal Prepayment']:,.0f} in extra principal payments to the feeder property.")

if row['_RainyTopup'] > 0:
    narrative.append(f"🌧️ **Reserve Topup:** You deposited ${row['_RainyTopup']:,.0f} to emergency reserves.")

if row['Operating Cash Flow'] > 0:
    narrative.append(f"✅ **Positive Operating CF:** After covering all expenses and debt service, you had ${row['Operating Cash Flow']:,.0f} in operating cash flow.")
else:
    narrative.append(f"⚠️ **Negative Operating CF:** Operating expenses and debt service exceeded rental income by ${abs(row['Operating Cash Flow']):,.0f}.")

for item in narrative:
    st.write(item)
```

#### Month-by-Month Table

```python
st.subheader("All Months - Scrollable Table")

# Filter options
show_all = st.checkbox("Show all months", value=True)
if not show_all:
    filter_option = st.radio("Filter", ["Acquisition months", "Refinance months", "Problem months (negative CF or low cash)"])

    if filter_option == "Acquisition months":
        display_df = portfolio_df[portfolio_df['Property Purchase'] > 0]
    elif filter_option == "Refinance months":
        display_df = portfolio_df[portfolio_df['Refinance Proceeds'] > 0]
    else:  # Problem months
        display_df = portfolio_df[(portfolio_df['Operating Cash Flow'] < 0) | (portfolio_df['Operating Cash'] < 1000)]
else:
    display_df = portfolio_df

# Format for display
st.dataframe(
    display_df[[
        'Year', 'Month', 'Monthly Rental Income', 'Net Operating Income',
        'Debt Service', 'Operating Cash Flow', 'Distributable Cash Flow',
        'Principal Prepayment', 'Operating Cash'
    ]].style.format({
        'Monthly Rental Income': '${:,.0f}',
        'Net Operating Income': '${:,.0f}',
        'Debt Service': '${:,.0f}',
        'Operating Cash Flow': '${:,.0f}',
        'Distributable Cash Flow': '${:,.0f}',
        'Principal Prepayment': '${:,.0f}',
        'Operating Cash': '${:,.0f}'
    }).background_gradient(subset=['Operating Cash Flow'], cmap='RdYlGn', vmin=-5000, vmax=5000),
    height=400,
    use_container_width=True
)
```

---

### Page 4: Time Series Analysis

**Purpose:** Spot trends and anomalies over 30 years

#### Multi-Metric Time Series

**Metric Selector:**
```python
st.subheader("Select Metrics to Chart (up to 5)")

col1, col2 = st.columns(2)

with col1:
    st.write("**Financial Metrics**")
    show_value = st.checkbox("Portfolio Value", value=True)
    show_debt = st.checkbox("Total Debt", value=True)
    show_equity = st.checkbox("Total Equity")
    show_ltv = st.checkbox("LTV %")

with col2:
    st.write("**Cash Flow Metrics**")
    show_rental = st.checkbox("Monthly Rental Income")
    show_noi = st.checkbox("Net Operating Income")
    show_opcf = st.checkbox("Operating Cash Flow")
    show_dist_cf = st.checkbox("Distributable Cash Flow")

# Additional metrics...
```

**Time Scale Toggle:**
```python
time_scale = st.radio("Time Scale", ["Monthly (1-360)", "Yearly (1-30)"], horizontal=True)

if time_scale == "Yearly (1-30)":
    # Aggregate to yearly
    display_df = portfolio_df.groupby('Year').last().reset_index()
    x_col = 'Year'
else:
    display_df = portfolio_df.copy()
    display_df['Month_Index'] = (display_df['Year'] - 1) * 12 + display_df['Month']
    x_col = 'Month_Index'
```

**Chart:**
```python
import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(specs=[[{"secondary_y": True}]])

# Add traces based on selections
if show_value:
    fig.add_trace(go.Scatter(x=display_df[x_col], y=display_df['Total Portfolio Value'],
                             mode='lines', name='Portfolio Value'), secondary_y=False)

if show_debt:
    fig.add_trace(go.Scatter(x=display_df[x_col], y=display_df['Total Debt'],
                             mode='lines', name='Total Debt'), secondary_y=False)

# ... add other metrics

# Annotate acquisition events
acq_events = portfolio_df[portfolio_df['Property Purchase'] > 0]
for _, row in acq_events.iterrows():
    x_val = row['Month_Index'] if time_scale == "Monthly (1-360)" else row['Year']
    fig.add_annotation(x=x_val, y=row['Total Portfolio Value'],
                       text="▲", showarrow=False, font=dict(size=20, color="green"))

fig.update_layout(
    title="Portfolio Metrics Over Time",
    xaxis_title="Month" if time_scale == "Monthly (1-360)" else "Year",
    yaxis_title="Value ($)",
    yaxis2_title="Percentage (%)",
    hovermode='x unified',
    height=600
)

st.plotly_chart(fig, use_container_width=True)
```

#### Anomaly Detection

```python
st.subheader("Anomaly Detection")

anomalies = []

# Check for sudden cash drops
portfolio_df['Cash_Drop'] = portfolio_df['Operating Cash'].diff()
sudden_drops = portfolio_df[portfolio_df['Cash_Drop'] < -50000]

for _, row in sudden_drops.iterrows():
    anomalies.append({
        'Year': int(row['Year']),
        'Month': int(row['Month']),
        'Issue': 'Sudden cash drop',
        'Severity': 'High',
        'Description': f"Operating Cash dropped by ${abs(row['Cash_Drop']):,.0f}"
    })

# Check for negative Operating CF
negative_cf = portfolio_df[portfolio_df['Operating Cash Flow'] < 0]
for _, row in negative_cf.iterrows():
    anomalies.append({
        'Year': int(row['Year']),
        'Month': int(row['Month']),
        'Issue': 'Negative Operating CF',
        'Severity': 'High',
        'Description': f"Operating CF: ${row['Operating Cash Flow']:,.0f}"
    })

# Check for reserves below target
below_reserves = portfolio_df[portfolio_df['Emergency Reserve'] < portfolio_df['Required Reserves']]
for _, row in below_reserves.iterrows():
    anomalies.append({
        'Year': int(row['Year']),
        'Month': int(row['Month']),
        'Issue': 'Reserves below target',
        'Severity': 'Medium',
        'Description': f"Reserve: ${row['Emergency Reserve']:,.0f}, Required: ${row['Required Reserves']:,.0f}"
    })

# ... other checks

if len(anomalies) == 0:
    st.success("✅ No anomalies detected")
else:
    st.warning(f"⚠️ {len(anomalies)} anomaly(ies) detected")
    import pandas as pd
    anomaly_df = pd.DataFrame(anomalies)
    st.dataframe(anomaly_df, use_container_width=True)
```

#### Growth Rate Analysis

```python
st.subheader("Year-over-Year Growth Analysis")

# Calculate YoY growth
yearly_df = portfolio_df.groupby('Year').agg({
    'Monthly Rental Income': 'sum',
    'Net Operating Income': 'sum',
    'Total Equity': 'last',
    'Total Portfolio Value': 'last'
}).reset_index()

yearly_df['Revenue_Growth_%'] = yearly_df['Monthly Rental Income'].pct_change() * 100
yearly_df['NOI_Growth_%'] = yearly_df['Net Operating Income'].pct_change() * 100
yearly_df['Equity_Growth_%'] = yearly_df['Total Equity'].pct_change() * 100

# Expected growth rates
expected_revenue_growth = st.session_state.config['market']['revenueInflationRate'] * 100
expected_value_growth = st.session_state.config['market']['annualAppreciation'] * 100

# Chart
fig = go.Figure()

fig.add_trace(go.Bar(x=yearly_df['Year'], y=yearly_df['Revenue_Growth_%'],
                     name='Actual Revenue Growth', marker_color='lightblue'))
fig.add_hline(y=expected_revenue_growth, line_dash="dash", line_color="blue",
              annotation_text=f"Expected ({expected_revenue_growth}%)")

fig.update_layout(title="Revenue Growth % vs Expected", yaxis_title="Growth %", height=400)

st.plotly_chart(fig, use_container_width=True)

# Highlight underperformance years
underperform = yearly_df[yearly_df['Revenue_Growth_%'] < expected_revenue_growth]
if len(underperform) > 0:
    st.warning(f"⚠️ Revenue growth below expected in {len(underperform)} year(s): {list(underperform['Year'])}")
```

---

### Page 5: Unit-Level Comparison

**Purpose:** Compare individual property performance

#### Property Selector

```python
st.subheader("Select Properties to Compare")

# Get list of all unit IDs
all_units = sorted(units_df['Unit_ID'].unique())

# Multi-select
selected_units = st.multiselect(
    "Select 2-3 properties",
    options=all_units,
    default=all_units[:3] if len(all_units) >= 3 else all_units,
    max_selections=3
)

if len(selected_units) == 0:
    st.warning("Please select at least one property to compare")
    st.stop()
```

#### Side-by-Side Charts

```python
# Filter to selected units
comparison_df = units_df[units_df['Unit_ID'].isin(selected_units)].copy()
comparison_df['Time'] = (comparison_df['Year'] - 1) * 12 + comparison_df['Month']

# Value Over Time
fig_value = go.Figure()
for unit_id in selected_units:
    unit_data = comparison_df[comparison_df['Unit_ID'] == unit_id]
    fig_value.add_trace(go.Scatter(x=unit_data['Time'], y=unit_data['Unit_Value'],
                                   mode='lines', name=f'Unit {unit_id}'))

fig_value.update_layout(title="Property Value Over Time", xaxis_title="Month", yaxis_title="Value ($)")
st.plotly_chart(fig_value, use_container_width=True)

# Debt Over Time
fig_debt = go.Figure()
for unit_id in selected_units:
    unit_data = comparison_df[comparison_df['Unit_ID'] == unit_id]
    fig_debt.add_trace(go.Scatter(x=unit_data['Time'], y=unit_data['Unit_Debt'],
                                  mode='lines', name=f'Unit {unit_id}'))

fig_debt.update_layout(title="Debt Over Time", xaxis_title="Month", yaxis_title="Debt ($)")
st.plotly_chart(fig_debt, use_container_width=True)

# LTV Over Time
fig_ltv = go.Figure()
for unit_id in selected_units:
    unit_data = comparison_df[comparison_df['Unit_ID'] == unit_id]
    fig_ltv.add_trace(go.Scatter(x=unit_data['Time'], y=unit_data['Unit_LTV'],
                                 mode='lines', name=f'Unit {unit_id}'))

fig_ltv.update_layout(title="LTV % Over Time", xaxis_title="Month", yaxis_title="LTV %")
st.plotly_chart(fig_ltv, use_container_width=True)

# Operating CF Over Time
fig_cf = go.Figure()
for unit_id in selected_units:
    unit_data = comparison_df[comparison_df['Unit_ID'] == unit_id]
    fig_cf.add_trace(go.Scatter(x=unit_data['Time'], y=unit_data['Unit_Operating_CF'],
                                mode='lines', name=f'Unit {unit_id}'))

fig_cf.update_layout(title="Operating Cash Flow Over Time", xaxis_title="Month", yaxis_title="Operating CF ($)")
st.plotly_chart(fig_cf, use_container_width=True)

# Cash-on-Cash Return Over Time
fig_coc = go.Figure()
for unit_id in selected_units:
    unit_data = comparison_df[comparison_df['Unit_ID'] == unit_id]
    fig_coc.add_trace(go.Scatter(x=unit_data['Time'], y=unit_data['Unit_Cash_On_Cash_Return'],
                                 mode='lines', name=f'Unit {unit_id}'))

fig_coc.update_layout(title="Cash-on-Cash Return Over Time", xaxis_title="Month", yaxis_title="CoC Return %")
st.plotly_chart(fig_coc, use_container_width=True)
```

#### Performance Comparison Table

```python
st.subheader("Current Performance Comparison (Year 30)")

# Get latest data for each selected unit
latest_data = []
for unit_id in selected_units:
    unit_latest = units_df[units_df['Unit_ID'] == unit_id].iloc[-1]
    latest_data.append({
        'Unit ID': unit_id,
        'Value': unit_latest['Unit_Value'],
        'Debt': unit_latest['Unit_Debt'],
        'Equity': unit_latest['Unit_Equity'],
        'LTV %': unit_latest['Unit_LTV'],
        'Operating CF': unit_latest['Unit_Operating_CF'],
        'Cash-on-Cash %': unit_latest['Unit_Cash_On_Cash_Return'],
        'Cap Rate %': unit_latest['Unit_Cap_Rate'],
        'DSCR': unit_latest['Unit_DSCR'],
        'ROI %': unit_latest['Unit_ROI']
    })

import pandas as pd
perf_df = pd.DataFrame(latest_data)

# Color code best/worst
def highlight_best_worst(s):
    # Green for best (max), Red for worst (min)
    if s.name in ['Value', 'Equity', 'Operating CF', 'Cash-on-Cash %', 'Cap Rate %', 'DSCR', 'ROI %']:
        is_max = s == s.max()
        is_min = s == s.min()
        return ['background-color: lightgreen' if v else 'background-color: lightcoral' if m else ''
                for v, m in zip(is_max, is_min)]
    elif s.name in ['Debt', 'LTV %']:
        is_max = s == s.max()
        is_min = s == s.min()
        return ['background-color: lightcoral' if v else 'background-color: lightgreen' if m else ''
                for v, m in zip(is_max, is_min)]
    else:
        return ['' for _ in s]

styled_df = perf_df.style.apply(highlight_best_worst).format({
    'Value': '${:,.0f}',
    'Debt': '${:,.0f}',
    'Equity': '${:,.0f}',
    'LTV %': '{:.2f}%',
    'Operating CF': '${:,.0f}',
    'Cash-on-Cash %': '{:.2f}%',
    'Cap Rate %': '{:.2f}%',
    'DSCR': '{:.2f}',
    'ROI %': '{:.2f}%'
})

st.dataframe(styled_df, use_container_width=True)
```

---

### Page 6: Scenario Comparison Matrix

**Purpose:** Compare multiple saved scenarios side-by-side

#### Scenario Manager

```python
st.subheader("Scenario Manager")

# List saved scenarios
import os
scenario_files = [f.replace('.json', '') for f in os.listdir('ui/scenarios') if f.endswith('.json')]

col1, col2 = st.columns([3, 1])

with col1:
    selected_scenarios = st.multiselect(
        "Select scenarios to compare",
        options=scenario_files,
        default=scenario_files[:3] if len(scenario_files) >= 3 else scenario_files
    )

with col2:
    if st.button("Run All Selected"):
        # Run simulations for all selected scenarios
        with st.spinner("Running scenarios..."):
            scenario_results = {}
            for scenario_name in selected_scenarios:
                # Load scenario config
                from utils.scenario_manager import load_scenario
                config = load_scenario(scenario_name)

                # Run simulation
                from utils.simulation_runner import run_simulation_from_config
                result = run_simulation_from_config(config)

                scenario_results[scenario_name] = {
                    'portfolio_df': result.monthly,
                    'units_df': result.units
                }

            # Store in session state
            st.session_state.scenario_results = scenario_results
            st.success(f"✅ Ran {len(selected_scenarios)} scenario(s)")
            st.rerun()
```

#### Comparison Table

```python
if 'scenario_results' in st.session_state and len(st.session_state.scenario_results) > 0:
    st.subheader("Scenario Comparison")

    # Build comparison table
    comparison_data = []

    for scenario_name, results in st.session_state.scenario_results.items():
        portfolio_df = results['portfolio_df']
        units_df = results['units_df']

        final_row = portfolio_df.iloc[-1]
        units_final = units_df.groupby('Unit_ID').last()

        comparison_data.append({
            'Scenario': scenario_name,
            'Final Value': final_row['Total Portfolio Value'],
            'Final Debt': final_row['Total Debt'],
            'Final Equity': final_row['Total Equity'],
            'Final Cash': final_row['Total Cash Reserves'],
            'Properties': int(final_row['Properties Owned']),
            'Year Debt-Free': int(portfolio_df[portfolio_df['Total Debt'] == 0].iloc[0]['Year']) if len(portfolio_df[portfolio_df['Total Debt'] == 0]) > 0 else 'N/A',
            'Total Interest': final_row['Total Interest Earned'],
            'Avg CoC %': units_final['Unit_Cash_On_Cash_Return'].mean()
        })

    comp_df = pd.DataFrame(comparison_data)

    # Highlight best/worst
    def highlight_best_worst(s):
        if s.name in ['Final Value', 'Final Equity', 'Final Cash', 'Total Interest', 'Avg CoC %', 'Properties']:
            is_max = s == s.max()
            return ['background-color: lightgreen' if v else '' for v in is_max]
        elif s.name in ['Final Debt', 'Year Debt-Free']:
            if s.name == 'Year Debt-Free':
                # Filter out 'N/A' for comparison
                numeric_s = pd.to_numeric(s, errors='coerce')
                is_min = numeric_s == numeric_s.min()
            else:
                is_min = s == s.min()
            return ['background-color: lightgreen' if v else '' for v in is_min]
        else:
            return ['' for _ in s]

    styled_comp = comp_df.style.apply(highlight_best_worst).format({
        'Final Value': '${:,.0f}',
        'Final Debt': '${:,.0f}',
        'Final Equity': '${:,.0f}',
        'Final Cash': '${:,.0f}',
        'Total Interest': '${:,.0f}',
        'Avg CoC %': '{:.2f}%'
    })

    st.dataframe(styled_comp, use_container_width=True)
```

#### Overlay Charts

```python
    st.subheader("Portfolio Value Over Time (All Scenarios)")

    fig = go.Figure()

    for scenario_name, results in st.session_state.scenario_results.items():
        portfolio_df = results['portfolio_df']
        fig.add_trace(go.Scatter(
            x=portfolio_df['Year'] + portfolio_df['Month']/12,
            y=portfolio_df['Total Portfolio Value'],
            mode='lines',
            name=scenario_name
        ))

    fig.update_layout(
        title="Portfolio Value Comparison",
        xaxis_title="Year",
        yaxis_title="Portfolio Value ($)",
        hovermode='x unified',
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    # Total Debt Comparison
    st.subheader("Debt Payoff Trajectories")

    fig_debt = go.Figure()

    for scenario_name, results in st.session_state.scenario_results.items():
        portfolio_df = results['portfolio_df']
        fig_debt.add_trace(go.Scatter(
            x=portfolio_df['Year'] + portfolio_df['Month']/12,
            y=portfolio_df['Total Debt'],
            mode='lines',
            name=scenario_name
        ))

    fig_debt.update_layout(
        title="Debt Payoff Comparison",
        xaxis_title="Year",
        yaxis_title="Total Debt ($)",
        hovermode='x unified',
        height=500
    )

    st.plotly_chart(fig_debt, use_container_width=True)
```

---

## Desktop Launcher (Windows Batch File)

Create `Launch_STR_Dashboard.bat` in project root:

```batch
@echo off
title STR Investment Model Dashboard
color 0A
echo ========================================
echo   STR Investment Model Dashboard
echo   Refinement Workbench
echo ========================================
echo.
echo Starting Streamlit server...
echo Browser will open automatically.
echo.
echo Press Ctrl+C to stop the server.
echo ========================================
echo.

REM Change to project directory
cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Launch Streamlit
streamlit run ui/app.py --server.port 8501 --server.headless false

REM If Streamlit exits with error, pause to show error
if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR: Failed to start dashboard
    echo ========================================
    pause
)
```

**To create desktop shortcut:**
1. Right-click `Launch_STR_Dashboard.bat`
2. Select "Send to" → "Desktop (create shortcut)"
3. (Optional) Right-click shortcut → Properties → Change Icon
4. Click OK

**Icon file (optional):**
- Create or download a `.ico` file
- Place in project root
- In shortcut properties, browse to `.ico` file

---

## Installation Instructions

### Step 1: Create ui/ folder and requirements.txt

```bash
# From project root
mkdir ui
mkdir ui\.streamlit
mkdir ui\pages
mkdir ui\components
mkdir ui\utils
mkdir ui\scenarios
mkdir ui\cache
```

Create `ui/requirements.txt`:
```
streamlit>=1.30.0
plotly>=5.18.0
pandas>=2.1.0
```

### Step 2: Install dependencies

```bash
pip install -r ui/requirements.txt
```

### Step 3: Create theme config

Create `ui/.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#00D9FF"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#1E2127"
textColor = "#FAFAFA"
font = "monospace"

[server]
port = 8501
headless = false
```

### Step 4: Create app.py skeleton

```python
# ui/app.py
import streamlit as st
from pathlib import Path
import json

st.set_page_config(
    page_title="STR Model Refinement Workbench",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark/Light mode toggle in sidebar
with st.sidebar:
    st.title("⚙️ Settings")

    # Theme toggle
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = True  # Default to dark mode

    dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
    st.session_state.dark_mode = dark_mode

    # Set plotly template based on theme
    st.session_state.plotly_template = "plotly_dark" if dark_mode else "plotly_white"

    st.divider()

st.title("STR Investment Model - Refinement Workbench")
st.caption("Model iteration and validation tool for real estate investors")

# Initialize session state
if 'initialized' not in st.session_state:
    # Load base case config
    config_path = Path('../ob_str_engine/OB_STR_ENGINE_V2_3.json')
    with open(config_path, 'r') as f:
        st.session_state.config = json.load(f)

    # Run initial simulation
    from ob_str_engine.engine.simulator import simulate
    result = simulate(config_path, years=30)
    st.session_state.portfolio_df = result.monthly
    st.session_state.units_df = result.units

    st.session_state.run_history = []
    st.session_state.initialized = True

st.success("✅ Dashboard initialized - Ready to build pages!")

# Apply custom CSS for dark mode styling
if st.session_state.dark_mode:
    st.markdown("""
    <style>
        /* Financial tables - monospace numbers */
        .dataframe td {
            font-family: 'Courier New', monospace;
        }

        /* Subtle borders */
        .stDataFrame {
            border: 1px solid #333;
        }

        /* Muted backgrounds for metrics */
        [data-testid="stMetricValue"] {
            font-family: 'Courier New', monospace;
        }
    </style>
    """, unsafe_allow_html=True)
```

### Step 5: Test launch

```bash
streamlit run ui/app.py
```

Should open browser to `http://localhost:8501` with dark mode enabled by default

**Note:** When creating charts in pages, always use:
```python
fig.update_layout(template=st.session_state.plotly_template)
```
This ensures charts adapt to dark/light mode automatically.

---

## Success Criteria

**The UI is successful if:**

1. ✅ User can click desktop icon → Browser opens with dashboard
2. ✅ User can adjust any config parameter in form (not raw JSON)
3. ✅ User can click "Run Simulation" → Results appear in < 10 seconds
4. ✅ User can validate model behavior (acquisitions, reserves, feeder strategy)
5. ✅ User can compare 2-3 runs side-by-side with delta calculations
6. ✅ User can clear run history to free memory
7. ✅ User can save/load custom scenarios
8. ✅ User can understand monthly cash flow with waterfall chart

**Not required (v1):**
- Beautiful design (functional > beautiful)
- Mobile support (desktop-only fine)
- Real-time data (simulation-based only)
- Advanced sensitivity analysis (Phase 2)

---

## Implementation Priority

### Phase 1: MVP (Implement First)
1. **app.py** - Main entry point with session state initialization
2. **Page 1: Run Control** - Config editor + run button + KPI cards
3. **utils/simulation_runner.py** - Wrapper for running simulations
4. **utils/scenario_manager.py** - Save/load scenarios
5. **Desktop launcher** - Batch file

**Deliverable:** Can edit config, run simulation, see results, save scenarios

### Phase 2: Validation (Implement Second)
6. **Page 2: Model Validation** - At least Tabs 1-3 (Acquisition, Reserves, Feeder)
7. **components/validation.py** - Automated validation checks
8. **Page 3: Cash Flow Anatomy** - Waterfall chart + month selector

**Deliverable:** Can validate model behavior and understand cash flow

### Phase 3: Analysis (Implement Third)
9. **Page 4: Time Series** - Multi-metric charts + anomaly detection
10. **Page 5: Unit Comparison** - Side-by-side property charts
11. **Page 6: Scenario Comparison** - Comparison table + overlay charts

**Deliverable:** Can compare scenarios and analyze trends

---

## User Preferences (CONFIRMED)

1. ✅ **Tech stack:** Streamlit + Plotly + Batch file
2. ✅ **File location:** ui/ folder in project root
3. ✅ **Caching:** Hybrid with clear history functionality
4. ✅ **Color scheme:** Dark mode/Light mode toggle available
5. ✅ **Initial scope:** Build all 6 pages (complete implementation)
6. ✅ **Validation strictness:** Show warnings only, don't block re-runs

## Design Philosophy

**Target User:** Seasoned, analytically-minded real estate investor who appreciates clean, data-dense interfaces

**Aesthetic:** "Cool nerd" - Professional but modern, sophisticated but approachable

**Design Principles:**
- **Data density over whitespace** - Investors want to see numbers, not marketing fluff
- **Dark mode friendly** - Easy on the eyes during long analysis sessions
- **Subtle visual hierarchy** - Use color sparingly for emphasis, not decoration
- **Monospace numbers** - Financial figures in tabular data font for easy scanning
- **Muted color palette** - Grays, blues, greens for positive, reds for negative (not garish)
- **Professional charts** - Clean Plotly charts with minimal chrome, maximum information
- **Keyboard-friendly** - Power users should be able to navigate without excessive clicking
- **No emoji overload** - Use sparingly (✅/❌ for status only, not decoration)
- **Bloomberg Terminal vibes** - Information-rich, not pretty for pretty's sake

**What this means in practice:**
- Tables with alternating row colors for readability
- Charts with gridlines, clear axis labels, hover tooltips
- Compact layouts (use columns effectively)
- Dark theme primary, light theme available via toggle
- Status indicators clear but understated
- Focus on functionality over form

---

## Final Notes

This UI is a **power tool for rapid model refinement**. Focus on:
- Speed of iteration (< 10 sec from adjust to results)
- Clarity of validation (instant feedback on model correctness)
- Ease of comparison (side-by-side scenarios with deltas)

Over:
- Visual polish
- Responsive design
- Investor presentation features

**Start simple, iterate fast, focus on the core workflow: adjust → run → validate → compare → refine.**

Once implemented, you'll be able to:
1. Test "what if" scenarios in seconds
2. Validate model logic is working correctly
3. Understand exactly why outcomes change
4. Compare different strategies objectively
5. Gain insights that lead to model improvements

**Ready to implement!**
