# STR Model Refinement Workbench - UI Visual/Layout UAT Session

## Context
I have a working Streamlit dashboard for an STR (Short-Term Rental) investment simulation model. The functional features are complete and working. This session focuses on **visual polish, layout adjustments, and placement refinements** - no functional changes needed.

## Tech Stack
- Streamlit (multi-page app)
- Plotly for charts
- Dark mode theme (default via config.toml)
- Python 3.13

## Project Location
Working directory: `C:\Users\jorge\.claude-worktrees\ob_str\gracious-golick`

## UI File Structure
```
ui/
├── app.py                      # Main entry point
├── .streamlit/config.toml      # Theme and server config
├── requirements.txt
├── components/
│   ├── config_editor.py        # Tabbed config form (7 tabs)
│   ├── kpi_cards.py            # KPI metrics display
│   ├── charts.py               # Plotly chart generators
│   └── validation.py           # Validation displays
├── pages/
│   ├── 1_run_control.py        # Main control panel (3-column layout)
│   ├── 2_model_validation.py   # Validation checks
│   ├── 3_cash_flow_anatomy.py  # Waterfall charts, Monthly/Annual toggle
│   ├── 4_time_series.py        # 30-year metric trends
│   ├── 5_unit_comparison.py    # Property comparisons
│   └── 6_scenario_comparison.py # Side-by-side scenarios
├── utils/
│   ├── simulation_runner.py    # Runs simulation engine
│   ├── scenario_manager.py     # Save/load scenarios
│   └── data_loader.py          # Data utilities
└── scenarios/                  # Saved scenario JSON files
```

## Launch Command
```batch
Launch_STR_Dashboard.bat
# or: streamlit run ui/app.py --server.port 8501 --server.address localhost
```

## Current Page Layouts

### Page 1: Run Control (1_run_control.py)
- **Header row**: Title | Run Simulation button | Load Base Case button
- **3-column layout below** (ratios [3, 4, 3]):
  - Left: Configuration editor (7 tabs), Scenarios section (load/delete/save)
  - Middle: Results KPIs (2 rows of 3), validation summary, 2 mini charts
  - Right: Run History table, load previous run, compare runs

### Page 3: Cash Flow Anatomy (3_cash_flow_anatomy.py)
- Monthly/Annual toggle at top
- Year/Month selectors with Quick Jump buttons
- Waterfall chart
- Events list
- Table view toggle

### Page 5: Unit Comparison (5_unit_comparison.py)
- Unit multiselect with Select All / Clear All buttons
- Multiple comparison charts
- Performance table with highlighting
- Unit lifecycle analysis section

### Page 6: Scenario Comparison (6_scenario_comparison.py)
- Scenario multiselect
- Run All Selected / Clear Results buttons
- Comparison table with best-value highlighting
- Overlay charts (portfolio value, debt, properties)
- Config differences viewer

## Design Aesthetic
- "Bloomberg Terminal vibes" - data-dense, professional
- Monospace numbers in tables
- Dark mode default
- Compact KPI cards with K/M suffixes for large numbers
- Green = good, Red = bad for deltas and highlights

## Key Components

### KPI Cards (kpi_cards.py)
- 2 rows of 3 metrics each
- Row 1: Final Portfolio Value, Total Equity, Properties (X of Y)
- Row 2: Max Units Reached (Year X), Debt-Free (Year X), Cash Reserves
- Deltas shown with +/- formatting when comparing runs

### Config Editor (config_editor.py)
- 7 horizontal tabs: Financial, Operations, Acquisition, Debt, Reserves, Capital, Market
- Mix of sliders, number inputs, checkboxes, selectboxes
- All inputs have help tooltips
- Capital Allocation tab shows warning if allocations don't sum to 100%

### Charts (charts.py)
- Portfolio value over time
- Properties owned timeline with acquisition annotations
- Waterfall charts for cash flow
- Unit comparison multi-line charts
- All use plotly_dark template

## Known Visual Considerations
- Header buttons (Run Simulation, Load Base Case) are in top row but not sticky/frozen when scrolling
- Config editor tabs may be cramped on smaller screens
- KPI cards use st.metric which has fixed styling
- Charts default to full container width

## Ready for UAT
The UI is functional. Please provide feedback on:
- Element placement and positioning
- Column widths and spacing
- Visual hierarchy
- Chart sizes and proportions
- Button locations and groupings
- Any layout that feels awkward or misaligned
- Text sizing and readability
- Spacing between sections
- Mobile/responsive concerns (if applicable)

I'll describe what I see and what I'd like changed, and you can make the CSS/layout adjustments.

---

## Session Notes
- All buttons have unique `key` parameters to avoid Streamlit duplicate ID errors
- Session state is used extensively for persistence across reruns
- The simulation engine is in `ob_str_engine/` (separate from UI)
