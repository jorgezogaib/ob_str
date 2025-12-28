# OB STR Engine v2.3

**Short-Term Rental Investment Portfolio Simulation Model**

---

## Quick Start

**Run Simulation:**
```bash
make obrun
# or: python run_quick.py
```

**Launch Dashboard:**
```bash
Launch_STR_Dashboard.bat
# or: streamlit run ui/app.py
```

**Run Tests:**
```bash
make test
```

---

## Documentation

All documentation is in the **`docs/`** folder:

### Getting Started
- **[Quick Start Guide](docs/QUICKSTART.md)** - Get running in 5 minutes
- **[Project Status](docs/PROJECT_STATUS.md)** - Current capabilities and features
- **[Technical Reference](docs/README.md)** - Complete technical documentation

### Current Features
- **[Validation Framework](docs/VALIDATION_FRAMEWORK_SUMMARY.md)** - 21 validation checks
- **[Distribution Policy](docs/DISTRIBUTION_POLICY_DESIGN.md)** - Financial freedom planning
- **[UI Guide](docs/UI_UAT_HANDOFF.md)** - Dashboard user guide

### Development
- **[Code Review Report](docs/CODE_REVIEW_REPORT.md)** - Comprehensive analysis
- **[Phase 1 Changes](docs/PHASE_1_CHANGES.md)** - Recent fixes and improvements

### Historical Archives
- **[docs/archive/](docs/archive/)** - Development history organized by topic

---

## Project Structure

```
gracious-golick/
├── docs/                    # All documentation
│   ├── QUICKSTART.md        # Start here!
│   ├── PROJECT_STATUS.md    # Current capabilities
│   ├── README.md            # Technical reference
│   └── archive/             # Historical documentation
├── ob_str_engine/           # Core simulation engine
├── ui/                      # Streamlit dashboard
├── tests/                   # Test suite
├── out/                     # CSV outputs
└── Makefile                 # Build commands
```

---

## Key Commands

| Command | Description |
|---------|-------------|
| `make obrun` | Run 30-year simulation |
| `python run_quick.py` | Alternative simulation command |
| `Launch_STR_Dashboard.bat` | Open interactive dashboard |
| `make test` | Run full test suite |
| `make clean` | Clean cache and outputs |

---

**Version:** v2.3
**Documentation:** See `docs/` folder
**Status:** Production Ready
