# OB STR Engine - Quick Start Guide

Get up and running with the STR Investment Model in under 5 minutes.

---

## 1. Run Simulation (Command Line)

```bash
make obrun
```

**Alternative commands:**
```bash
python run_quick.py       # Direct Python execution
make run                   # Equivalent to make obrun
```

**Output:**
- `out/OB_STR_V2_3_Monthly_YYYY-MM-DD.csv` - Monthly detail (360 rows)
- `out/OB_STR_V2_3_YearOverYear_YYYY-MM-DD.csv` - Annual summary (30 rows)
- `out/reports/*.csv` - Investor reports and unit breakdowns

**Programmatic API:**
```python
from ob_str_engine.engine.simulator import simulate
from pathlib import Path

result = simulate(Path("ob_str_engine/OB_STR_ENGINE_V2_3.json"))
# result.monthly → pandas DataFrame
# result.yearly  → pandas DataFrame
```

---

## 2. Launch Interactive Dashboard

**Windows:**
```bash
Launch_STR_Dashboard.bat
```

**Mac/Linux:**
```bash
streamlit run ui/app.py
```

**Opens:** http://localhost:8501 in your browser

**Dashboard Features:**
- **Run Control:** Edit parameters, run simulations, compare results
- **Model Validation:** Verify acquisition logic and safety checks
- **Cash Flow Anatomy:** Interactive waterfall charts
- **Time Series:** 30-year metric trends
- **Unit Comparison:** Property performance rankings
- **Scenario Comparison:** Save and compare strategies

---

## 3. Modify Simulation Parameters

**Edit:** `ob_str_engine/OB_STR_ENGINE_V2_3.json`

**Common Changes:**
```json
{
  "constants": {
    "debt": {
      "mortgageRate": 0.0685,     // Purchase mortgage rate
      "refiRate": 0.0685           // Refinance rate
    },
    "acquisition": {
      "downPaymentFirst": 0.25,    // 25% down on first property
      "downPaymentSubsequent": 0.25 // 25% down on subsequent
    }
  },
  "policies": {
    "portfolio": {
      "maxUnits": 7                // Maximum properties to acquire
    }
  },
  "market": {
    "revenueInflationRate": 0.04,  // 4% annual revenue growth
    "annualAppreciation": 0.03     // 3% annual property appreciation
  }
}
```

**After editing:** Re-run `obrun` or use dashboard "Run Simulation" button

---

## 4. Run Tests

```bash
make test
```

**Or manually:**
```bash
pytest tests/ -v
```

**Test Coverage:**
- Unit tests (primitives, calculations)
- Integration tests (liquidity, reserves, metrics)
- Golden outputs (regression tests)
- Performance tests (runtime checks)

---

## 5. View Results

**CSV Output Location:** `out/`
- Monthly detail files
- Year-over-year summary files
- Investor reports (in `out/reports/`)

**Dashboard:** Use the UI for interactive exploration and visualization

---

## Project Structure

```
gracious-golick/
├── ob_str_engine/           # Core simulation engine
│   ├── engine/              # Calculation modules
│   └── OB_STR_ENGINE_V2_3.json  # Configuration
├── ui/                      # Streamlit dashboard
│   ├── pages/               # 6 dashboard pages
│   ├── components/          # Reusable UI components
│   └── utils/               # Simulation runner, scenario manager
├── tests/                   # Pytest test suite
├── out/                     # CSV outputs
├── docs/                    # Documentation
│   └── archive/             # Historical documentation
├── README.md                # Technical reference manual
└── Makefile                 # Build commands
```

---

## Common Commands

| Task | Command |
|------|---------|
| Run simulation | `make obrun` or `python run_quick.py` |
| Launch dashboard | `Launch_STR_Dashboard.bat` |
| Run tests | `make test` |
| Clean cache | `make clean` |
| Install dependencies | `pip install -r requirements.txt` |
| Install UI dependencies | `pip install -r ui/requirements.txt` |

---

## Next Steps

1. **Read the README.md** - Complete technical reference
2. **Explore the Dashboard** - Interactive model refinement workbench
3. **Review Validation** - Check model behavior meets expectations
4. **Compare Scenarios** - Test different strategies
5. **Consult Documentation** - See `docs/` for detailed guides

---

## Need Help?

- **Technical Reference:** See `README.md`
- **Project Status:** See `docs/PROJECT_STATUS.md`
- **Code Review:** See `CODE_REVIEW_REPORT.md`
- **Validation Framework:** See `VALIDATION_FRAMEWORK_SUMMARY.md`
- **Distribution Policy:** See `DISTRIBUTION_POLICY_DESIGN.md`
- **Historical Documentation:** See `docs/archive/`

---

**Version:** v2.3
**Last Updated:** December 2025
