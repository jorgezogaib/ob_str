# Validation Framework - Quick Reference

## Default Threshold Values

### LTV & DSCR
| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| Max Safe LTV | 85% | 75-95% | Flag if LTV exceeds (lender limits) |
| Max LTV Drop Without Event | 10% | 5-20% | Flag drops >this without refi/purchase |
| Critical DSCR | 1.0 | 0.8-1.1 | Below this = unsustainable |
| Lender Minimum DSCR | 1.25 | 1.1-1.5 | Required for refinancing |
| Max Months Below Lender | 12 | 0-36 | Tolerate poor DSCR this long |

### Acquisition & Refinance
| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| Min Liquidity to Flag | $50,000 | $10k-$200k | Flag if stuck with this much cash |
| Max Months Stuck | 60 | 12-120 | Flag if stuck this long despite liquidity |
| Year to Stop Checking Stuck | 25 | 15-30 | Stop flagging stuck after this year |
| Max Consecutive Acquisitions | 0 | 0-3 | Allow back-to-back month buys |
| Min Refi Proceeds | $20,000 | $5k-$50k | Min extraction to justify refi costs |
| Max Refis Per Property | 3 | 1-10 | Theoretical max over 30 years |

### Reserves
| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| Min Reserve Cushion at Purchase | 80% | 50-100% | Required % of target after buy |
| Max Reserve Hoarding | $500,000 | $100k-$1M | Flag if reserves exceed this |
| Max Monthly Drop % | 50% | 25-75% | Flag if reserves drop >this |
| Sweep Tolerance (Months) | 12 | 3-36 | Max months sweep can fail |

### Cash Flow
| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| Max Months Negative | 6 | 0-24 | Max months burning cash |
| NOI Volatility Threshold | $3,000 | $500-$10k | Flag swings >this amount |
| Min Cash-on-Cash Return | 5% | 0-15% | Flag if below (underperform) |
| Max Cash-on-Cash Return | 30% | 15-50% | Flag if above (unrealistic) |

### Portfolio & Performance
| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| Min Properties by Year 5 | 3 | 1-10 | Diversification target |
| Equity Growth Tolerance | 70% | 50-100% | Min % of appreciation-implied |
| Portfolio Growth Tolerance | 60% | 50-100% | Min % of appreciation-implied |
| Min Debt-Free Year | 15 | 10-25 | Flag if paid off before this |
| Max Debt-Free Year | 30 | 20-30 | Flag if still in debt after |
| Min Units for Debt Check | 5 | 1-10 | Only check timing if ≥this |

### Feeder & Timing
| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| Min Annual Feeder LTV Decrease | 5% | 1-15% | Target prepayment rate |
| Max Months Same Feeder | 36 | 12-60 | Flag if no rotation/refi |
| Max Months at Same Count | 24 | 12-60 | Flag if stuck despite growth |
| Min Equity Growth While Stuck | 20% | 10-50% | Flag if grows >this while stuck |

## Validation Category Breakdown

### 21 Total Checks

**Portfolio (6)**
- Properties acquired target
- Acquisition pacing (consecutive, stuck)
- LTV trajectory (max, suspicious drops)
- Portfolio concentration
- Equity growth rate
- Debt-free timeline

**Cash Flow (4)**
- Operating cash shortfalls
- DSCR sustainability
- NOI volatility
- Negative cash flow duration

**Debt Management (2)**
- Refi economic rationality
- Refi frequency limits

**Reserves (4)**
- Sufficiency at purchase
- Emergency reserve maintenance
- Balance anomalies (drops, hoarding)
- Sweep mechanics

**Performance (2)**
- Cash-on-cash return range
- Portfolio value growth rate

**Mechanics (3)**
- Feeder tracking continuity
- Feeder prepayment effectiveness
- Acquisition timing vs equity

## Validation Tuning Strategies

### Conservative Investor Profile
```
DSCR Lender Min: 1.35 (vs 1.25 default)
Max Safe LTV: 75% (vs 85%)
Min Reserve Cushion: 100% (vs 80%)
Max Reserve Hoarding: $750k (vs $500k)
Min CoC Return: 8% (vs 5%)
```

### Aggressive Growth Profile
```
DSCR Lender Min: 1.20 (vs 1.25 default)
Max Safe LTV: 85% (keep default)
Min Reserve Cushion: 70% (vs 80%)
Max Reserve Hoarding: $300k (vs $500k)
Min CoC Return: 12% (vs 5%)
Max Months Stuck: 36 (vs 60) - want faster growth
```

### Lender Standards Profile
```
DSCR Lender Min: 1.25 (industry standard)
Max Safe LTV: 75% (typical investment cap)
Min Reserve Cushion: 80% (conservative)
DSCR Critical: 1.0 (break-even floor)
Max Consecutive Acquisitions: 0 (realistic pacing)
```

## Common Validation Warnings & Fixes

### "LTV exceeded 85% in N months"
**Cause**: Refinanced too aggressively or took on too much debt
**Fix**: Lower `maxPostRefiLTV` in Acquisition & Debt config OR raise validation threshold if intentional

### "DSCR below 1.25 in N months"
**Cause**: Debt service too high vs. NOI
**Fix**: Increase revenue assumptions, decrease expenses, or lower leverage

### "Cash shortfall: N months, worst: $X"
**Cause**: Negative operating cash - model parameters unsustainable
**Fix**: Increase starting cash, annual savings, or reduce expenses

### "Reserves peaked at $X - may be hoarding"
**Cause**: Late-stage portfolio accumulating cash (often debt payoff phase)
**Fix**: Expected behavior in Year 25+. Raise threshold or ignore if intentional.

### "Stuck at N properties for M months despite liquidity"
**Cause**: Acquisition logic too conservative or refi not triggering
**Fix**: Lower `targetYieldUnlevered`, check `refiLTVTrigger`, or review `dscrThresholdForRefi`

### "Refi in YXM extracted only $Y (min: $Z)"
**Cause**: Refinancing small amounts, costs may exceed benefits
**Fix**: Raise `refiLTVTrigger` to wait for more equity OR lower validation threshold

### "Feeder LTV decreased X%/year (target: 5%)"
**Cause**: Insufficient prepayment to feeder property
**Fix**: Increase `feederPrepaymentPct` in Capital Allocation

### "CoC return X% annually - very high"
**Cause**: Overly optimistic assumptions (appreciation, occupancy, ADR)
**Fix**: Validate market assumptions or raise threshold if confident

### "Equity grew X% over Yy, expected ≥Z%"
**Cause**: Refinancing extracting equity faster than appreciation builds it
**Fix**: Reduce refi frequency or lower `maxPostRefiLTV`

## Validation UI Location

**Config Editor → ✓ Validation Tab**

6 Sub-tabs:
1. LTV & DSCR
2. Acquisition & Refi
3. Reserves
4. Cash Flow
5. Portfolio & Performance
6. Feeder & Timing

All thresholds tunable via sliders and number inputs with real-time updates.

## Exporting Validation Results

**Export Button**: Located in validation summary header (📥 Export)

**What Gets Exported:**
- Timestamp of validation run
- Summary stats (total checks, warnings, passes)
- Final portfolio state (properties, value, equity, debt, LTV)
- All validation thresholds used
- Detailed results by category (each check's status and message)

**File Format**: JSON with timestamp filename `validation_results_YYYYMMDD_HHMMSS.json`

**Usage Tips:**
- Export before/after config changes to compare impact
- Track validation trends across multiple runs
- Document validation state for specific scenarios
- Share results with advisors or team members
- Build historical validation database

## Testing Your Thresholds

1. Run baseline simulation with default validation thresholds
2. Note which checks pass/fail
3. Adjust validation thresholds to match your risk tolerance
4. Re-run simulation - validation should align with expectations
5. Compare scenarios using consistent validation criteria

**Remember**: Validation warnings are **informational**, not blocking. Review, understand root cause, decide if acceptable for your strategy.
