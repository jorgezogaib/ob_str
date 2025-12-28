# STR Investment Model - Refinement Workbench UI Implementation

## Mission

Build a **Model Refinement Workbench** UI that allows rapid iteration on model assumptions, validation of model behavior, and deep analysis of simulation results. This is a tool for **refining the model**, not presenting to investors.

---

## Tech Stack

**Framework:** Streamlit (Python web framework)
- Reason: Fast to build, Python-native, good charting libraries, easy iteration
- Launch: `streamlit run ui/app.py` opens in browser automatically

**Visualization:** Plotly
- Reason: Interactive charts with zoom, pan, hover tooltips
- Good for exploration and understanding model behavior

**Data:** Pandas DataFrames
- Already used by simulation engine
- Direct compatibility with Streamlit

---

## Project Context

### Existing Code Structure

```
ob_str_engine/
├── OB_STR_ENGINE_V2_3.json        # Config file (all model parameters)
├── engine/
│   ├── simulator.py                # Core simulation logic
│   ├── types.py                    # SimulationResult, Unit dataclasses
│   ├── reports.py                  # Report generation functions
│   ├── config.py                   # Config loading
│   └── [other modules]             # Acquisition, debt, reserves, etc.
out/
└── simulation_results_feeder.csv   # Portfolio-level results (360 rows × 46 cols)
run_quick.py                         # Quick test script
```

### How to Run Simulation

```python
from pathlib import Path
from ob_str_engine.engine.simulator import simulate

# Run 30-year simulation
result = simulate(Path('ob_str_engine/OB_STR_ENGINE_V2_3.json'), years=30)

# Access data
portfolio_df = result.monthly    # 360 rows (30 years × 12 months)
units_df = result.units          # 1,604 rows (unit-month records)

# Available columns documented in DATA_COMPLETENESS_FOR_UI.md
```

### Key Data Available

**Portfolio DataFrame (360 rows):**
- Financial: Total Portfolio Value, Total Debt, Total Equity, LTV%
- Income/Expenses: Monthly Rental Income, Property Management, CapEx, HOA, Insurance, Taxes, Debt Service
- Cash Flow: NOI, Operating Cash Flow, Distributable Cash Flow
- Cash Accounts: Operating Cash, Emergency Reserve, Growth Savings
- Events: Property Purchase, Down Payment, Refinance Proceeds, Principal Prepayment
- Internal: _FeederIndex, _FeederLTV, _RefiPropertyIndex, _RainyTopup, _RainySweep, etc.

**Units DataFrame (1,604 rows):**
- Identification: Year, Month, Unit_ID, Is_Feeder, Unit_Age_Months
- Valuation: Unit_Value, Unit_Debt, Unit_Equity, Unit_LTV
- Income/Expenses: Unit_Rental_Income, Unit_Property_Mgmt, Unit_CapEx, Unit_HOA, Unit_Insurance, Unit_Property_Tax, Unit_Debt_Service
- Cash Flow: Unit_NOI, Unit_Operating_CF
- Expense Ratios: Unit_Expense_Ratio, Unit_Mgmt_Fee_Ratio, Unit_CapEx_Ratio, Unit_NOI_Margin
- Return Metrics: Unit_Cash_On_Cash_Return, Unit_Cap_Rate, Unit_DSCR, Unit_ROI

**Report Functions Available:**
```python
from ob_str_engine.engine.reports import (
    cash_flow_waterfall,           # Portfolio waterfall for any month
    unit_cash_flow_waterfall,      # Per-unit waterfall
    executive_summary_report,       # High-level summary
    year_over_year_summary,         # Annual metrics
)

# Example
waterfall_df = cash_flow_waterfall(result.monthly, year=5, month=4)
```

### Config File Structure (JSON)

```json
{
  "version": "2.3-PHOENIX-3BR-FAMILY-2025",
  "constants": {
    "financial": {
      "startingCash": 5000.0,
      "annualSavings": 50000.0,
      "amortizationYears": 30
    },
    "operations": {
      "adrBaseline2BR": 425.0,
      "occupancyBaseline": 0.78,
      "mgmtPct": 0.20,
      "capexPct": 0.10,
      "hoaAnnual": 12800.0,
      "hoaInflationRate": 0.04,
      "insuranceRate": 0.033,
      "propertyTaxRate": 0.0055,
      "liquidityReserveMultiplier": 1.0
    },
    "acquisition": {
      "downPaymentFirst": 0.20,
      "downPaymentSubsequent": 0.25,
      "closingCostPct": 0.03,
      "targetYieldUnlevered": 0.065,
      "maxPostRefiLTV": 0.75,
      "refiCooldownYears": 3,
      "dscrThresholdForRefi": 1.20,
      "refiCashoutStrategy": "max"
    },
    "debt": {
      "mortgageRate": 0.0685,
      "refiRate": 0.05875
    },
    "reserves": {
      "capexMonthsTarget": 6,
      "enableCapexCeiling": true,
      "capexCeilingMonths": 6,
      "enableRainySweep": true,
      "rainyBufferPct": 1.2
    }
  },
  "market": {
    "annualAppreciation": 0.03,
    "revenueInflationRate": 0.04
  },
  "banking": {
    "rainyCoverageMonths": 5,
    "operatingCashMonths": 1,
    "seasoningMonths": 6,
    "refiLTVTrigger": 0.75,
    "cashoutCostPct": 0.03,
    "cashInterestRate": 0.04,
    "purchaseReserveMonths": 6
  },
  "policies": {
    "portfolio": {
      "maxUnits": 7,
      "stopRefiAtMaxUnits": true
    },
    "capitalAllocation": {
      "feederPrepaymentPct": 0.70,
      "savingsAccumulationPct": 0.30
    }
  }
}
```

---

## UI Requirements

### Core User Workflow (The Iteration Loop)

1. **Load or run baseline simulation** → See Year 30 outcomes
2. **Validate model behavior** → Check acquisition timeline, reserve mechanics, feeder logic
3. **Form hypothesis** → "What if I increase CapEx reserves from 6 to 12 months?"
4. **Adjust config** → Edit JSON parameter
5. **Rerun simulation** → Get new results
6. **Compare results** → See what changed (outcomes and behavior)
7. **Gain insight** → Understand why outcomes changed
8. **Iterate** → Refine assumption, test again

**UI must minimize friction in this loop. Target: < 10 seconds from "I want to test X" to "here are results".**

---

## Page Structure (Priority Order)

### Page 1: Run Control & Config (PRIMARY - Command Center)

**Layout:** 3-column layout

**Left Column (30% width): Configuration Editor**
- **Tabbed interface** for JSON editing:
  - Tab: Financial (startingCash, annualSavings, amortizationYears)
  - Tab: Operations (ADR, occupancy, mgmt%, CapEx%, HOA, insurance, taxes)
  - Tab: Acquisition (down payment%, closing costs, max units, refi strategy)
  - Tab: Debt (mortgage rate, refi rate)
  - Tab: Reserves (target months, sweep settings)
  - Tab: Capital Allocation (feeder prepayment%, savings%)
  - Tab: Market (appreciation, revenue inflation)

- **Form inputs** (not raw JSON text):
  - Number inputs for numeric values
  - Sliders for percentages (0-100%)
  - Toggles for booleans
  - Dropdowns for strategy options

- **Preset scenarios** dropdown:
  - Base Case (load current OB_STR_ENGINE_V2_3.json)
  - Conservative (low growth, high reserves)
  - Aggressive (high growth, lower reserves)
  - Custom saved scenarios (stored in ui/scenarios/ folder)

- **Action buttons:**
  - 🔄 Run Simulation (big, primary button)
  - 💾 Save Config As... (save current to scenarios/)
  - 📂 Load Scenario (load from scenarios/)
  - ↩️ Reset to Base Case

**Middle Column (40% width): Immediate Results**
After simulation runs, show:

- **Key Outcomes** (KPI cards):
  - Final Portfolio Value (Year 30)
  - Total Properties Acquired (number + year when hit max)
  - Years to Debt-Free (which year all debt = $0)
  - Total Cash Reserves (Year 30)
  - Total Interest Earned (30 years)
  - Average Cash-on-Cash Return (portfolio average)

- **Validation Status:**
  - ✅ All properties acquired successfully (7 of 7)
  - ✅ No cash shortfalls (Operating Cash never < $0)
  - ✅ Debt payoff completed (Year 22)
  - ✅ Reserves maintained (never below required)
  - ⚠️ Warnings: [List any warnings from validation checks]

- **Mini Charts:**
  - Portfolio Value over 30 years (line chart)
  - Debt over 30 years (line chart)
  - Properties Owned timeline (step chart)

**Right Column (30% width): Run History & Comparison**
- **Run History Table:**
  - Last 10 runs
  - Columns: Timestamp, Scenario Name, Final Value, Properties, Years to Debt-Free
  - Click row to reload that scenario
  - Checkbox to select runs for comparison

- **Compare Mode:**
  - Select 2-3 runs (checkboxes)
  - Show delta table:
    - Metric | Run A | Run B | Delta
    - Final Value | $12.87M | $11.23M | -$1.64M
    - Years to Debt-Free | 22 | 25 | +3 years

- **What Changed:**
  - Automatically detect config differences between selected runs
  - Show: "ADR: $425 → $400 (-5.9%)"
  - Show: "CapEx%: 10% → 12% (+20%)"

---

### Page 2: Model Validation Dashboard (Debug & Verify)

**Purpose:** Ensure model logic is working correctly

**Tab 1: Acquisition Logic**
- **Acquisition Timeline Chart:**
  - X-axis: Time (Years 1-30)
  - Y-axis: Cumulative properties owned (0-7)
  - Step chart showing when each property acquired
  - Annotate each step with: Year, Month, Purchase Price, Down Payment, Refi Proceeds Used

- **Acquisition Feasibility Table:**
  - One row per acquisition month
  - Columns:
    - Year/Month
    - Available Cash (before purchase)
    - Down Payment Required
    - Closing Costs Required
    - Reserve Cushion Needed
    - Total Required
    - Source: Cash / Refi / Savings
    - ✅/❌ Feasible?

- **Visual indicator:** Green if all acquisitions feasible, Red if any shortfalls

**Tab 2: Reserve Mechanics**
- **Reserve Balances Chart:**
  - 3 lines: Emergency Reserve, CapEx Balance (internal), Growth Savings
  - Dashed line: Required Emergency Reserve (target)
  - Shaded area: Above target (sweep zone)
  - Markers: Red dots = topup events, Green dots = sweep events

- **Reserve Event Log Table:**
  - Columns: Year, Month, Event Type (Topup/Sweep), Amount, Trigger, New Balance
  - Filter: Show only Topup events / Show only Sweep events
  - Validate:
    - Topups only when reserve < target ✅
    - Sweeps only when reserve > ceiling ✅

**Tab 3: Feeder Strategy**
- **Feeder Timeline:**
  - Visual showing which unit was feeder at each point
  - Color-coded by Unit ID
  - Hover shows: Unit ID, LTV at selection, Reason for change

- **Feeder Selection Logic Table:**
  - Rows: Each month where feeder changed
  - Columns:
    - Year/Month
    - Old Feeder (Unit ID, LTV)
    - New Feeder (Unit ID, LTV)
    - Reason: Lowest LTV / Refi Cooldown Expired / New Property Acquired
  - Verify: Always selects unit with lowest LTV ✅

- **Prepayment Allocation Chart:**
  - Line chart: Feeder LTV declining over time
  - Bar chart: Monthly prepayment amount to feeder
  - Verify 70% of distributable CF goes to feeder

**Tab 4: Refinance Logic**
- **Refi Decision Table:**
  - One row per month where refi was evaluated
  - Columns:
    - Year/Month
    - Feeder Unit ID
    - Feeder LTV
    - Feeder DSCR
    - Months Since Last Refi
    - Eligible? (Y/N)
    - Reason if No (LTV > 75% / DSCR < 1.20 / Cooldown)
    - Cashout Amount (if executed)

- **Refi Impact Table:**
  - One row per executed refi
  - Columns:
    - Year/Month, Unit ID
    - Old Balance → New Balance
    - Old Rate → New Rate
    - Old Payment → New Payment
    - Cash Extracted

**Tab 5: Cash Reconciliation**
- **Operating Cash Chart:**
  - Line chart: Operating Cash balance over 360 months
  - Red zone: < $0 (critical error)
  - Yellow zone: < Operating Minimum (warning)
  - Green zone: healthy

- **Reconciliation for Selected Month:**
  - Month selector (slider 1-360)
  - Table:
    - Starting Operating Cash: $X
    - + Rental Income: $Y
    - + Interest: $Z
    - - Expenses: $A
    - - Debt Service: $B
    - - Reserve Topup: $C
    - - Prepayment: $D
    - - Acquisition Costs: $E
    - = Ending Operating Cash: $F
  - Verify: Starting + Net = Ending ✅

---

### Page 3: Deep Dive - Cash Flow Anatomy

**Purpose:** Understand cash flow mechanics for any month

**Interactive Waterfall Visualization:**
- **Month Selector:**
  - Slider (1-360) or Year/Month dropdowns
  - Bookmarks: Quickly jump to acquisition months, refi months

- **Waterfall Chart** (Plotly waterfall chart):
  - Starting Operating Cash (base)
  - + Rental Income (green bar up)
  - + Interest Earned (green bar up)
  - + Refinance Proceeds (green bar up, if applicable)
  - - Property Management (red bar down)
  - - CapEx (red bar down)
  - - HOA (red bar down)
  - - Insurance (red bar down)
  - - Taxes (red bar down)
  - = NOI (checkpoint, blue bar)
  - - Debt Service (red bar down)
  - = Operating CF (checkpoint, blue bar)
  - - Reserve Topup (red bar down, if applicable)
  - = Distributable CF (checkpoint, blue bar)
  - - Principal Prepayment (red bar down, if applicable)
  - - Savings Deposit (red bar down, if applicable)
  - - Acquisition Costs (red bar down, if applicable)
  - = Ending Operating Cash (final)

- **Running Commentary:**
  - Text below chart explaining what happened
  - Example: "In Year 8, Month 9, you acquired Property #2 ($914K) using $256K from refinancing Property #1. Operating CF was $951, with $666 going to feeder prepayment."

**Month-by-Month Table:**
- **Scrollable table** with all 360 months
- **Columns:** Year, Month, Rental Income, Total Expenses, NOI, Debt Service, Operating CF, Distributable CF, Prepayment, Ending Cash
- **Row Highlighting:**
  - Blue: Acquisition month
  - Green: Refinance month
  - Red: Negative Operating CF
  - Yellow: Reserve topup occurred

- **Filters:**
  - Show only acquisition months
  - Show only refinance months
  - Show only problem months (negative CF or low cash)

**Reserve Flow Diagram:**
- **For selected month, show decision tree:**
  - Start: Operating CF = $X
  - Decision: Is Operating CF positive?
    - If No → No prepayment, no topup possible
    - If Yes → Continue
  - Decision: Is Emergency Reserve < Target?
    - If Yes → Topup reserve with $Y from Operating CF
    - If No → Continue
  - Decision: Is Emergency Reserve > Ceiling?
    - If Yes → Sweep $Z back to Operating Cash
    - If No → Continue
  - Remaining Distributable CF: $W
  - Split: 70% to Feeder Prepayment ($A), 30% to Savings ($B)

---

### Page 4: Time Series Analysis

**Purpose:** Spot trends, patterns, and anomalies

**Multi-Metric Time Series Chart:**
- **Metric Selector (checkboxes):**
  - Portfolio Value, Total Debt, Total Equity, LTV%
  - Monthly Rental Income, NOI, Operating CF, Distributable CF
  - Operating Cash, Emergency Reserve, Growth Savings
  - Properties Owned, Feeder LTV
  - Principal Prepayment, Interest Earned

- **Chart:**
  - Dual Y-axis: Currency (left), Percentage (right)
  - X-axis: Time (Months 1-360 or Years 1-30, toggle)
  - Up to 5 lines selectable
  - Annotations: Auto-mark acquisition events (▲), refi events (★), debt-free events (✓)

- **Zoom/Pan:** Plotly built-in controls to focus on specific periods

**Anomaly Detection:**
- **Automatic flagging:**
  - ⚠️ Sudden cash drops (> $50K in one month)
  - ⚠️ Operating CF going negative
  - ⚠️ Reserves dropping below target
  - ⚠️ LTV spiking above 75%
  - ⚠️ Long gaps between acquisitions (> 24 months after first property)

- **Anomaly Table:**
  - Columns: Year/Month, Issue, Severity (High/Medium/Low), Description
  - Click row to jump to that month in other views

**Growth Rate Analysis:**
- **Year-over-Year Tables:**
  - Revenue Growth % by year (Actual vs Expected 4%)
  - NOI Growth % by year
  - Equity Growth % by year
  - Highlight years where actual < expected (underperformance)

---

### Page 5: Unit-Level Comparison

**Purpose:** Compare property performance

**Property Selector:**
- Checkboxes to select 2-3 units for comparison
- Default: Select all 7 units

**Side-by-Side Charts:**
- **Value Over Time:** Line chart, one line per selected unit
- **Debt Over Time:** Line chart, one line per selected unit
- **LTV Over Time:** Line chart, one line per selected unit
- **Operating CF Over Time:** Line chart, one line per selected unit
- **Cash-on-Cash Return Over Time:** Line chart, one line per selected unit

**Performance Comparison Table:**
- **Rows:** Selected units
- **Columns:**
  - Purchase Date, Purchase Price, Cash Invested
  - Current Value, Current Debt, Current Equity, LTV%
  - Monthly Operating CF, Cash-on-Cash%, Cap Rate, DSCR, ROI
  - Times as Feeder, Months as Feeder, Total Prepayment Received
- **Sorting:** Click column header to sort
- **Color Coding:** Best (green), Middle (yellow), Worst (red)

**Property Lifecycle Timeline:**
- **Select one unit** (dropdown)
- **Visual timeline showing:**
  - Month 0: Purchase (price, down payment, financing amount)
  - Month X: Refinance event (cashout amount, rate change)
  - Month Y-Z: Feeder period (total prepayments received)
  - Month W: Debt-free milestone
- **Annotations:** Hover over events for details

---

### Page 6: Scenario Comparison Matrix

**Purpose:** Compare multiple saved scenarios side-by-side

**Scenario Manager:**
- **List of Saved Scenarios:**
  - Base Case
  - Conservative (user-saved)
  - Aggressive (user-saved)
  - High Debt (user-saved)
  - Low Debt (user-saved)
  - [Any custom scenarios in ui/scenarios/ folder]

- **Bulk Run:**
  - Checkboxes to select multiple scenarios
  - "Run All Selected" button
  - Progress bar while running

**Comparison Table:**
- **Rows:** Key outcomes
  - Final Portfolio Value
  - Total Debt (Year 30)
  - Total Equity (Year 30)
  - Total Cash Reserves
  - Properties Acquired
  - Year Hit Max Units
  - Year Debt-Free
  - Total Interest Earned
  - Average Cash-on-Cash Return
  - Total Principal Prepayments

- **Columns:** Each scenario
- **Highlighting:** Best value (green cell), Worst value (red cell)
- **Delta Columns:** Show difference vs Base Case
  - Example: "+$2.1M (+16%)" in green if higher, "-$1.5M (-12%)" in red if lower

**Overlay Charts:**
- **Portfolio Value:** All scenarios as different colored lines over 30 years
- **Total Debt:** See different payoff trajectories
- **Properties Owned:** Step chart showing when each scenario hit max units

**Config Diff Table:**
- **Show parameter differences between selected scenarios:**
  - Parameter | Base | Conservative | Aggressive | Notes
  - Occupancy | 78% | 70% | 82% | Conservative assumes lower
  - Appreciation | 3% | 2% | 4.5% | Aggressive assumes higher
  - CapEx Months | 6 | 12 | 4 | Conservative holds more reserves

---

### Page 7: Sensitivity Explorer (OPTIONAL - Phase 2)

**Purpose:** Understand which parameters drive outcomes

**Single Variable Sweep:**
- **Variable Selector:** Dropdown of all numeric parameters
  - ADR Baseline, Occupancy, Management %, CapEx %
  - Mortgage Rate, Refi Rate
  - Appreciation Rate, Revenue Inflation
  - Down Payment %, Max Units
  - Feeder Prepayment %, Savings %

- **Range Definition:**
  - Min value (number input)
  - Max value (number input)
  - Step count (slider: 5-20 steps)

- **Run Sweep Button:**
  - Runs N simulations with variable varying from min to max
  - Shows progress bar

**Results:**
- **Tornado Chart:** Shows impact on final portfolio value
  - Horizontal bars showing outcome range for each variable
  - Sorted by magnitude (biggest impact at top)

- **Sensitivity Line Chart:**
  - X-axis: Variable being swept
  - Y-axis: Selected outcome (Portfolio Value / Years to Debt-Free / Final Cash)
  - Shows non-linear relationships

---

## Technical Implementation Details

### File Structure

```
ui/
├── app.py                          # Main Streamlit app (entry point)
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
├── scenarios/                       # Saved scenario configs
│   ├── base_case.json
│   ├── conservative.json
│   └── aggressive.json
└── cache/                           # Cached simulation results
    └── [run results stored here]
```

### Streamlit Session State Management

Use `st.session_state` to persist:
- Current config parameters
- Last simulation results (portfolio_df, units_df)
- Run history (list of {timestamp, scenario_name, results})
- Selected runs for comparison
- UI state (selected month, selected units, etc.)

### Performance Optimization

**Caching:**
```python
@st.cache_data
def run_simulation(config_dict):
    """Cache simulation results to avoid re-running identical configs"""
    # Convert dict to JSON, save to temp file, run simulation
    # Return (portfolio_df, units_df)
    pass

@st.cache_data
def load_cached_result(run_id):
    """Load previously saved run from cache/"""
    pass
```

**Background Processing:**
- For bulk scenario runs, use Streamlit's progress bar
- Consider using `st.spinner()` for long operations

### Config Editor Implementation

**Use Streamlit form widgets, NOT raw JSON editing:**

```python
# Example for Operations tab
with st.form("operations_config"):
    adr = st.number_input("ADR Baseline (2BR)", value=425.0, step=5.0)
    occupancy = st.slider("Occupancy Baseline", 0.0, 1.0, 0.78, 0.01)
    mgmt_pct = st.slider("Management %", 0.0, 0.50, 0.20, 0.01)
    capex_pct = st.slider("CapEx %", 0.0, 0.30, 0.10, 0.01)
    # ... etc

    submit = st.form_submit_button("Update Config")

    if submit:
        # Update session_state config
        st.session_state.config['constants']['operations']['adrBaseline2BR'] = adr
        # ... etc
```

**Group parameters logically:**
- Financial tab: Starting cash, annual savings, amortization
- Operations tab: ADR, occupancy, expenses
- Acquisition tab: Down payments, closing costs, max units
- Debt tab: Rates, refi strategy
- Reserves tab: Target months, sweep settings
- Capital Allocation tab: Prepayment/savings split
- Market tab: Appreciation, inflation

### Validation Checks (Automatic)

After each simulation run, automatically check:

```python
def validate_simulation(portfolio_df, units_df):
    """Return dict of validation results"""
    checks = {}

    # Check 1: No negative operating cash
    checks['no_negative_cash'] = (portfolio_df['Operating Cash'] >= 0).all()

    # Check 2: All properties acquired
    max_units = st.session_state.config['policies']['portfolio']['maxUnits']
    final_units = portfolio_df.iloc[-1]['Properties Owned']
    checks['all_acquired'] = (final_units == max_units)

    # Check 3: Debt paid off
    final_debt = portfolio_df.iloc[-1]['Total Debt']
    checks['debt_free'] = (final_debt == 0)

    # Check 4: Reserves maintained
    below_target = (portfolio_df['Emergency Reserve'] < portfolio_df['Required Reserves'])
    checks['reserves_maintained'] = not below_target.any()

    return checks
```

**Display validation results:**
```python
checks = validate_simulation(portfolio_df, units_df)

if checks['no_negative_cash']:
    st.success("✅ No cash shortfalls")
else:
    st.error("❌ Operating cash went negative!")

# ... etc for all checks
```

### Chart Components (Reusable)

**Create reusable chart functions:**

```python
import plotly.graph_objects as go

def plot_portfolio_value_over_time(df, scenarios=None):
    """
    df: Portfolio DataFrame (single scenario)
    scenarios: Optional list of (name, df) tuples for overlay
    """
    fig = go.Figure()

    # Add primary line
    fig.add_trace(go.Scatter(
        x=df['Year'] + df['Month']/12,
        y=df['Total Portfolio Value'],
        mode='lines',
        name='Portfolio Value'
    ))

    # Add scenario overlays if provided
    if scenarios:
        for name, scenario_df in scenarios:
            fig.add_trace(go.Scatter(
                x=scenario_df['Year'] + scenario_df['Month']/12,
                y=scenario_df['Total Portfolio Value'],
                mode='lines',
                name=name
            ))

    fig.update_layout(
        title="Portfolio Value Over Time",
        xaxis_title="Year",
        yaxis_title="Portfolio Value ($)",
        hovermode='x unified'
    )

    return fig

# Usage
fig = plot_portfolio_value_over_time(st.session_state.portfolio_df)
st.plotly_chart(fig, use_container_width=True)
```

**Standard chart types needed:**
- Line charts (time series)
- Waterfall charts (cash flow)
- Bar charts (comparisons)
- Stacked area charts (reserves, debt by unit)
- Step charts (properties owned)
- Heatmaps (optional, for sensitivity)
- Tornado charts (optional, for sensitivity)

### Waterfall Chart Example

```python
def plot_cash_flow_waterfall(waterfall_df):
    """
    waterfall_df: Output from cash_flow_waterfall() function
    Columns: Category, Amount, Running_Balance
    """
    fig = go.Figure(go.Waterfall(
        name="Cash Flow",
        orientation="v",
        measure=["absolute"] + ["relative"] * (len(waterfall_df)-2) + ["total"],
        x=waterfall_df['Category'],
        y=waterfall_df['Amount'],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))

    fig.update_layout(
        title="Cash Flow Waterfall",
        showlegend=False,
        height=600
    )

    return fig
```

### Scenario Save/Load

```python
import json
from datetime import datetime

def save_scenario(config_dict, scenario_name):
    """Save current config to ui/scenarios/{scenario_name}.json"""
    filepath = f"ui/scenarios/{scenario_name}.json"
    with open(filepath, 'w') as f:
        json.dump(config_dict, f, indent=2)
    return filepath

def load_scenario(scenario_name):
    """Load config from ui/scenarios/{scenario_name}.json"""
    filepath = f"ui/scenarios/{scenario_name}.json"
    with open(filepath, 'r') as f:
        config_dict = json.load(f)
    return config_dict

def list_scenarios():
    """List all saved scenarios in ui/scenarios/"""
    import os
    scenario_files = [f.replace('.json', '') for f in os.listdir('ui/scenarios') if f.endswith('.json')]
    return scenario_files
```

### Run History Management

```python
def add_to_run_history(scenario_name, config_dict, results_summary):
    """Add run to session_state run history"""
    if 'run_history' not in st.session_state:
        st.session_state.run_history = []

    run_record = {
        'timestamp': datetime.now(),
        'scenario_name': scenario_name,
        'config_hash': hash(json.dumps(config_dict, sort_keys=True)),
        'final_value': results_summary['final_value'],
        'properties_owned': results_summary['properties_owned'],
        'years_to_debt_free': results_summary['years_to_debt_free'],
        # Store full results for quick access
        'portfolio_df': st.session_state.portfolio_df.copy(),
        'units_df': st.session_state.units_df.copy(),
    }

    st.session_state.run_history.insert(0, run_record)  # Newest first

    # Keep only last 10 runs in memory
    st.session_state.run_history = st.session_state.run_history[:10]
```

---

## Desktop Launcher

### Windows Batch File (Recommended)

Create `Launch_STR_Dashboard.bat` in project root:

```batch
@echo off
echo Starting STR Investment Model Dashboard...
echo.

REM Activate virtual environment if using one
REM call venv\Scripts\activate.bat

REM Launch Streamlit
streamlit run ui/app.py

REM Keep window open if there's an error
pause
```

**To create desktop shortcut:**
1. Right-click batch file → Send to → Desktop (create shortcut)
2. Right-click shortcut → Properties
3. Change icon: Browse to a .ico file or use default
4. Click OK

**Auto-open browser:**
Streamlit automatically opens browser by default. To disable: `streamlit run ui/app.py --server.headless=true`

### Alternative: PowerShell Script

Create `Launch_STR_Dashboard.ps1`:

```powershell
Write-Host "Starting STR Investment Model Dashboard..." -ForegroundColor Green

# Set working directory
Set-Location $PSScriptRoot

# Activate virtual environment if using one
# & .\venv\Scripts\Activate.ps1

# Launch Streamlit
streamlit run ui/app.py

# Keep window open
Read-Host -Prompt "Press Enter to exit"
```

**Execution policy:** May need to run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` once

---

## Installation & Setup

### Requirements

Create `ui/requirements.txt`:

```
streamlit>=1.30.0
plotly>=5.18.0
pandas>=2.1.0
```

### Installation Steps

```bash
# From project root
pip install -r ui/requirements.txt

# Test launch
streamlit run ui/app.py
```

**First run should:**
1. Load base case config from `ob_str_engine/OB_STR_ENGINE_V2_3.json`
2. Run initial simulation
3. Display results in Run Control page
4. Create cache/ and scenarios/ folders if they don't exist

---

## Key Implementation Priorities

### Phase 1: MVP (Week 1)
**Goal:** Get basic iteration loop working

1. **Page 1: Run Control** (70% effort)
   - Config editor with tabs
   - Run simulation button
   - KPI cards showing results
   - Run history table (basic)

2. **Page 2: Model Validation** (30% effort)
   - Basic acquisition timeline chart
   - Basic reserve balance chart
   - Validation status indicators

**Deliverable:** Can edit config, run simulation, see results, validate behavior

### Phase 2: Deep Dive (Week 2)
**Goal:** Add analytical depth

3. **Page 3: Cash Flow Anatomy**
   - Interactive waterfall chart
   - Month selector
   - Month-by-month table

4. **Page 4: Time Series Analysis**
   - Multi-metric time series chart
   - Anomaly detection

**Deliverable:** Can understand model behavior in detail

### Phase 3: Comparison (Week 3)
**Goal:** Compare scenarios and properties

5. **Page 5: Unit Comparison**
   - Side-by-side property charts
   - Performance comparison table

6. **Page 6: Scenario Comparison**
   - Save/load scenarios
   - Side-by-side comparison table
   - Overlay charts

**Deliverable:** Can compare strategies and properties

---

## Success Criteria

**The UI is successful if:**

1. ✅ User can adjust any config parameter and rerun in < 30 seconds
2. ✅ User can validate model behavior (acquisitions, reserves, feeder logic)
3. ✅ User can identify which assumptions drive outcomes
4. ✅ User can compare 2-3 scenarios side-by-side
5. ✅ User can understand why outcomes changed between runs
6. ✅ Desktop icon launches UI in browser with one click

**Not required (nice-to-have):**
- Beautiful design (functional > beautiful)
- Mobile responsiveness (desktop-only is fine)
- Real-time data integration (simulation-based only)
- Advanced analytics (keep it simple for v1)

---

## Common Pitfalls to Avoid

1. **Don't make config editor raw JSON text**
   - Use Streamlit form widgets (number_input, slider, selectbox)
   - Group logically by category
   - Validate inputs before running

2. **Don't re-run simulation on every interaction**
   - Only run when user clicks "Run Simulation"
   - Cache results to avoid redundant runs
   - Use session_state to persist data between page loads

3. **Don't build all pages at once**
   - Start with Page 1 (Run Control) and get it working
   - Add pages incrementally
   - Test iteration loop before adding complexity

4. **Don't ignore performance**
   - Simulation takes ~2 seconds - that's fine
   - Cache results with @st.cache_data
   - Don't re-generate charts on every rerun

5. **Don't forget validation**
   - Auto-validate results after each run
   - Show clear ✅/❌ indicators
   - Flag anomalies automatically

---

## Questions to Ask User Before Starting

1. **Python environment:**
   - Using virtual environment? (venv, conda, etc.)
   - Python version? (Recommend 3.10+)

2. **Launcher preference:**
   - Windows batch file OK?
   - Want custom icon? (need .ico file)

3. **Initial scope:**
   - Start with Page 1 only (Run Control)?
   - Or build Pages 1-3 in first iteration?

4. **Design preferences:**
   - Dark mode or light mode?
   - Color scheme preferences?

5. **Data persistence:**
   - How many runs to keep in history? (Suggest 10)
   - Cache simulation results to disk or memory only?

---

## Example app.py Structure

```python
import streamlit as st
from pathlib import Path
import json

# Page config
st.set_page_config(
    page_title="STR Model Refinement Workbench",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'config' not in st.session_state:
    # Load base case config
    with open('ob_str_engine/OB_STR_ENGINE_V2_3.json', 'r') as f:
        st.session_state.config = json.load(f)

if 'portfolio_df' not in st.session_state:
    # Run initial simulation
    from ob_str_engine.engine.simulator import simulate
    result = simulate(Path('ob_str_engine/OB_STR_ENGINE_V2_3.json'), years=30)
    st.session_state.portfolio_df = result.monthly
    st.session_state.units_df = result.units

# Sidebar navigation
st.sidebar.title("STR Model Workbench")
page = st.sidebar.radio(
    "Navigation",
    ["Run Control & Config", "Model Validation", "Cash Flow Anatomy",
     "Time Series", "Unit Comparison", "Scenario Comparison"]
)

# Route to pages
if page == "Run Control & Config":
    from pages import run_control
    run_control.show()
elif page == "Model Validation":
    from pages import model_validation
    model_validation.show()
# ... etc
```

---

## Final Notes

This is a **power tool for model refinement**, not a presentation dashboard. Prioritize:
- Speed of iteration
- Clarity of validation
- Ease of comparison

Over:
- Visual polish
- Marketing appeal
- Investor-facing features

The goal is to rapidly test assumptions, validate logic, and gain insights that lead to model improvements. Once the model is refined, you can build investor-facing dashboards later.

**Start simple, iterate fast, and focus on the core workflow: adjust → run → validate → compare → refine.**
