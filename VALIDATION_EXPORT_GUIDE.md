# Validation Export & Comparison Guide

## Overview

The validation framework now includes a **one-click export** feature to save validation results as JSON files. This enables tracking validation history, comparing scenarios, and documenting model behavior over time.

## Exporting Validation Results

### How to Export

1. Run your simulation in the Streamlit UI
2. Scroll to the **Model Validation** section
3. Click the **📥 Export** button in the header
4. Browser will download `validation_results_YYYYMMDD_HHMMSS.json`

### What Gets Exported

The JSON file contains:

```json
{
  "timestamp": "2025-12-27T14:30:45.123456",
  "summary": {
    "total_checks": 21,
    "total_warnings": 2,
    "total_passed": 19
  },
  "portfolio_stats": {
    "properties_owned": 7,
    "total_portfolio_value": 9284567.89,
    "total_equity": 9284567.89,
    "total_debt": 0.0,
    "ltv_percent": 0.0,
    "simulation_years": 30
  },
  "validation_thresholds": {
    "ltv": {...},
    "dscr": {...},
    ...
  },
  "results_by_category": {
    "Portfolio": [
      {"status": "pass", "message": "All properties acquired (7/7)"},
      ...
    ],
    ...
  }
}
```

**Key sections:**
- **timestamp**: ISO format datetime when validation ran
- **summary**: Quick stats (total checks, warnings, passed)
- **portfolio_stats**: Final portfolio state (properties, value, equity, debt, LTV, years)
- **validation_thresholds**: All config values used for this validation run
- **results_by_category**: Detailed pass/warn status for each of 21 checks

## Use Cases

### 1. Track Parameter Tuning

**Scenario**: You're adjusting `feederPrepaymentPct` to optimize debt payoff timeline.

**Workflow**:
1. Run baseline with `feederPrepaymentPct = 0.70`, export validation
2. Run test with `feederPrepaymentPct = 0.80`, export validation
3. Compare exports to see impact on warnings

**Compare**:
```bash
python compare_validations.py \
  validation_results_baseline.json \
  validation_results_test.json
```

**Output shows**:
- Warning changes (new, resolved)
- Portfolio stat differences (properties, value, equity)
- Threshold changes applied

### 2. Document Scenario Analysis

**Scenario**: Comparing "Conservative" vs "Aggressive" strategies for presentation.

**Workflow**:
1. Configure conservative parameters (80% down payment, low leverage)
2. Run simulation, export → `validation_conservative.json`
3. Configure aggressive parameters (25% down payment, max leverage)
4. Run simulation, export → `validation_aggressive.json`
5. Include both exports in documentation

**Benefits**:
- Timestamped snapshot of exact thresholds used
- Clear documentation of which warnings triggered
- Reproducible results (thresholds saved with results)

### 3. Track Validation Over Time

**Scenario**: Building a validation history database.

**Workflow**:
1. After each major model change, export validation
2. Store in `validation_history/` folder
3. Periodically run comparison script across all files
4. Identify trends (are warnings increasing? decreasing?)

**File organization**:
```
validation_history/
  2025-12-01_baseline.json
  2025-12-05_increased_capex.json
  2025-12-10_adjusted_dscr.json
  2025-12-15_final_config.json
```

### 4. Share Results with Team/Advisors

**Scenario**: Presenting model to lender or investor.

**Workflow**:
1. Run final approved configuration
2. Export validation → `validation_final_proposal.json`
3. Email JSON file to stakeholder
4. Stakeholder can review:
   - All 21 validation checks passed/warned
   - Exact thresholds used (DSCR, LTV, etc.)
   - Final portfolio stats (properties, value, equity)
   - Timestamp proves when validation ran

**Professional presentation**:
- Self-documenting (includes all thresholds)
- Machine-readable (JSON can be programmatically analyzed)
- Lightweight (typically <10KB file)

## Comparison Tool Usage

### Basic Comparison

Compare two validation exports:

```bash
python compare_validations.py file1.json file2.json
```

**Output sections**:

1. **Summary Comparison** - Checks, warnings, passed for each file
2. **Portfolio Stats Comparison** - Properties, value, equity, LTV side-by-side
3. **Warning Changes** - What warnings appeared/disappeared
4. **Threshold Differences** - Which validation thresholds changed

### Multi-File Comparison

Compare multiple exports sequentially:

```bash
python compare_validations.py baseline.json test1.json test2.json test3.json
```

**Compares**:
- baseline → test1
- baseline → test2
- baseline → test3

Shows how each test differs from baseline.

### Example Output

```
================================================================================
VALIDATION COMPARISON
================================================================================

### SUMMARY COMPARISON ###

File                                     Checks     Warnings   Passed
--------------------------------------------------------------------------------
validation_baseline.json                 21         3          18
validation_improved.json                 21         1          20

### PORTFOLIO STATS COMPARISON ###

File                                     Properties   Total Value     Equity          LTV %
--------------------------------------------------------------------------------
validation_baseline.json                 7            $9.28M          $9.28M          0.0%
validation_improved.json                 7            $9.45M          $9.45M          0.0%

### WARNING CHANGES ###

Comparing validation_baseline.json → validation_improved.json:
  ✓ Resolved Warnings (2):
    - Reserves: Reserves peaked at $12,409,736 - may be hoarding vs deploying
    - Mechanics: Feeder not tracked in 106 month(s)

### THRESHOLD DIFFERENCES ###

Comparing validation_baseline.json → validation_improved.json:
  reserves.maxReserveHoarding: 500000.0 → 15000000.0

================================================================================
COMPARISON COMPLETE
================================================================================
```

## Best Practices

### Naming Conventions

Use descriptive filenames when saving exports:

```
validation_baseline_70pct_prepay.json
validation_test_80pct_prepay.json
validation_final_approved_config.json
validation_conservative_strategy.json
validation_aggressive_strategy.json
```

Better than timestamp-only names when you have many exports.

### Folder Organization

```
project/
  validation_history/
    2025-12/
      baseline.json
      test_configs/
        test_prepay_70.json
        test_prepay_80.json
        test_prepay_90.json
      approved/
        final_config.json
```

### Version Control

**Do commit**: Representative exports for key scenarios
**Don't commit**: Every single test run (too much noise)

**Example `.gitignore`**:
```
validation_results_*.json  # Ignore timestamped exports
!validation_baseline.json  # But keep baseline
!validation_final.json     # And final approved
```

### Documentation

In your project README or docs:

```markdown
## Validation Results

**Baseline Configuration** (as of 2025-12-27):
- File: `validation_baseline.json`
- Properties: 7/7 acquired
- Warnings: 2 (reserves hoarding, feeder tracking)
- Key metrics: 23.5% CoC return, debt-free Year 23

**Approved Configuration** (as of 2025-12-30):
- File: `validation_final.json`
- Properties: 7/7 acquired
- Warnings: 0 (all checks passed)
- Key metrics: 21.8% CoC return, debt-free Year 24
```

## Integration Ideas

### 1. Automated Testing

```python
# test_validation_regression.py
import json

def test_no_new_warnings():
    """Ensure new config doesn't introduce warnings vs baseline"""
    with open('validation_baseline.json') as f:
        baseline = json.load(f)

    with open('validation_current.json') as f:
        current = json.load(f)

    baseline_warnings = baseline['summary']['total_warnings']
    current_warnings = current['summary']['total_warnings']

    assert current_warnings <= baseline_warnings, \
        f"New warnings introduced: {current_warnings} vs {baseline_warnings}"
```

### 2. CI/CD Integration

```yaml
# .github/workflows/validation.yml
name: Validation Check

on: [push]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run simulation
        run: python run_simulation.py
      - name: Export validation
        run: python export_validation.py
      - name: Compare to baseline
        run: python compare_validations.py validation_baseline.json validation_current.json
```

### 3. Dashboard/Reporting

Build a simple dashboard that:
- Loads all validation exports from a folder
- Shows trends over time (warnings increasing/decreasing?)
- Highlights which checks fail most frequently
- Suggests threshold adjustments

## Troubleshooting

### "Export button not appearing"

**Cause**: Old version of `kpi_cards.py` without export feature
**Fix**: Ensure you have latest version with `import json` and export button code

### "JSON file won't open"

**Cause**: File may be corrupted or incomplete
**Fix**: Check file size (should be several KB), re-export if needed

### "Comparison script errors"

**Cause**: Validation files from different versions may have different schemas
**Fix**: Only compare exports from same model version

## Summary

**Export Feature Benefits**:
- ✅ One-click export of full validation state
- ✅ Self-documenting (includes all thresholds)
- ✅ Enables historical tracking
- ✅ Facilitates scenario comparison
- ✅ Professional documentation for stakeholders
- ✅ Machine-readable for automation

**Files**:
- `ui/components/kpi_cards.py` - Export button implementation
- `compare_validations.py` - Comparison utility script
- `validation_export_example.json` - Sample export format

**Next Steps**:
1. Run your simulation
2. Click Export button
3. Save the JSON file
4. Use `compare_validations.py` to compare multiple runs
5. Build your validation history database!
