# STR Investment Platform - Long-Term Roadmap

**Created:** December 28, 2025
**Vision Owner:** Jorge
**Current Version:** v2.3-PHOENIX-3BR-FAMILY-2025
**Target Market:** Orange Beach, AL (primary) with flexibility for lake properties

---

## Executive Summary

This roadmap outlines the evolution of the OB STR Investment Model from a **simulation engine** into a comprehensive **STR investment platform**. The platform will span the entire investment lifecycle:

1. **Model Refinement** - Complete the investment simulation with missing financial realism
2. **Monte Carlo & AI Insights** - Probabilistic analysis with actionable intelligence
3. **Deal Analysis Tool** - Rapid screening of real estate listings against strategy
4. **Due Diligence Manager** - Task management for offers and inspections
5. **Financing Workbench** - Loan package preparation and lender communication
6. **Property Management System** - Bring the model to reality with actual performance data

---

## Current State Assessment

### What's Working Well (80% Complete)
- 30-year monthly simulation engine with feeder strategy
- 7-property acquisition model with strategic refinancing
- Three-tier reserve management (operating, rainy-day, growth)
- Distribution policy engine with configurable triggers
- Interactive Streamlit dashboard with 6 pages
- 21-point validation framework
- Scenario save/load and comparison
- Comprehensive test suite (100% passing)

### Known Gaps in Current Model
| Gap | Impact | Priority |
|-----|--------|----------|
| **Seasonality** | Revenue assumes flat 78% occupancy year-round; misses OB peak (Jun-Aug) vs off-season | High |
| **Event Modeling** | No modeling of minor repairs through catastrophic events (hurricanes, pandemics) | High |
| **Insurance Modeling** | Flat 3.3% rate; no named storm deductibles, coverage gaps, or claim timing | High |
| **CapEx Schedule** | Flat 10% reserve; no unit-specific maintenance tracking | Medium |
| **Tax Modeling** | No depreciation schedule (need for CPA, not full tax software) | High |
| **Portfolio Financing UI** | Limited visibility into debt structure and refi timing | Medium |
| **Market Profiles** | Single market assumptions; need configurable profiles for OB vs lake properties | Medium |
| **Exit Strategy** | No modeling of staggered unit sales or portfolio liquidation | Medium |

---

## Phase 1: Model Refinement

**Timeline Context:** ~4 years before first purchase. Build comprehensively; no rush to "good enough."

**Milestone:** Phase 1 complete = Model accurately reflects OB market realities and supports confident purchase decisions.

---

### Phase 1A: Core Revenue & Expense Accuracy

*Focus: Get the numbers right before anything else*

### 1.1 Seasonality Engine & Market Profiles
**Goal:** Model market-specific seasonal revenue patterns accurately

**Market Profile Architecture:**
Each market (Orange Beach, lake property, etc.) gets its own profile with:
- Base ADR and occupancy assumptions
- Monthly seasonality multipliers
- Market-specific expense patterns
- Local appreciation and inflation rates
- Insurance cost structure (coastal vs inland)

**Orange Beach Profile (Primary):**
- Monthly occupancy curves (not flat 78%)
  - Peak season (Jun-Aug): 85-95% occupancy, ADR +30-50%
  - Shoulder (Mar-May, Sep-Oct): 65-75%, ADR +10-15%
  - Off-season (Nov-Feb): 35-50%, ADR -10-20%
- Seasonal expense patterns
  - Higher utilities in summer (AC)
  - Hurricane prep costs (Jun-Nov)
- Coastal insurance rates (higher base + named storm deductibles)

**Lake Property Profile (Future):**
- Different seasonality (summer peak, potential winter lull)
- Lower insurance costs (no hurricane/flood zone typically)
- Different guest demographics (families, fishermen, weekenders)
- Potentially different ADR and occupancy baselines

**Data Sources:**
- AirDNA seasonal trends
- Your own booking data (once operational)
- Local property manager insights

**Implementation Notes:**
- Add `market_profiles` section to config JSON
- Each unit assigned to a market profile
- Monthly multipliers for ADR and occupancy per market
- Enable/disable seasonality toggle for comparison
- Portfolio-level reporting aggregates across markets

### 1.2 Insurance Modeling (Coastal-Specific)
**Goal:** Accurately model coastal insurance costs and claim dynamics

**Why This Matters for Orange Beach:**
- Named storm deductibles: 2-5% of property value ($8k-$20k on a $400k condo)
- Flood insurance requirements (if in flood zone)
- Wind/hail separate from standard coverage
- Premium volatility after major storms

**Insurance Cost Components:**
| Component | Current Model | Enhanced Model |
|-----------|---------------|----------------|
| Base rate | 3.3% flat | Market-specific (OB higher than lake) |
| Named storm deductible | Not modeled | 2-5% of value, triggered by event |
| Flood insurance | Not modeled | Required if in flood zone (~$1,500-3,000/yr) |
| Liability/umbrella | Not modeled | $500-1,000/yr for STR coverage |
| Premium inflation | Not modeled | 5-10% annual increases typical |

**Claim Dynamics:**
- Deductible applies before payout
- Payout delay (30-180 days typical, longer after major storms)
- Coverage gaps (cosmetic damage, code upgrades, loss of rents)
- Premium increase after claim (15-30% for 3-5 years)

**Implementation:**
- Add `insurance` section to market profiles
- Per-unit insurance tracking (age of policy, claims history)
- Event integration (hurricane triggers claim logic)
- Dashboard showing insurance exposure and upcoming renewals

---

### Phase 1B: Stress Testing & Tax Planning

*Focus: Understand risks and tax implications before committing capital*

### 1.3 Event Modeling (Minor to Catastrophic)
**Goal:** Stress test the portfolio against real-world disruptions

**Event Categories:**
| Category | Examples | Financial Impact |
|----------|----------|------------------|
| **Minor** | Appliance failure (dishwasher, microwave), guest damage, plumbing issue | $500-5,000 per incident |
| **Moderate** | HVAC replacement, roof repair, extended vacancy | $5,000-25,000 |
| **Major** | Market downturn, lawsuit, major storm damage | $25,000-100,000+ |
| **Catastrophic** | Hurricane (OB-specific), pandemic, total loss | Portfolio-wide impact |

**Implementation Approach:**
Events are **scheduled by year and month** (not random) to enable:
- Precise stress testing ("What if hurricane hits in Year 3, Month 9?")
- Monte Carlo compatibility (randomize event timing across runs)
- Scenario comparison (same portfolio with/without events)

**Event Definition Structure:**
```json
{
  "events": [
    {
      "name": "Hurricane Sally",
      "year": 3,
      "month": 9,
      "type": "catastrophic",
      "scope": "portfolio",
      "impacts": {
        "vacancy_months": 2,
        "repair_cost": 50000,
        "adr_reduction_pct": 0.20,
        "adr_recovery_months": 6
      },
      "insurance": {
        "claim_amount": 45000,
        "deductible_pct": 0.02,
        "payout_delay_months": 4
      }
    }
  ]
}
```

**Per-Unit vs Portfolio-Wide Events:**
- **Unit events:** Dishwasher failure, HVAC replacement, guest damage
- **Portfolio events:** Hurricane, pandemic, market crash, regulatory change

**Key Scenarios to Model (5 initial set):**
1. **Hurricane Hit** - 2 months vacancy, $50k repairs, insurance claim with 2% deductible, 4-month payout delay
2. **Pandemic** - 3 months zero bookings, gradual 12-month recovery to baseline
3. **Major Repair** - $15k HVAC failure in off-season on Unit 2
4. **Dishwasher Failure** - $800 replacement, 3-day vacancy for install
5. **Market Softening** - 20% ADR decline for 18 months (no physical damage)

**Future Enhancement (Phase 2):**
- Monte Carlo randomizes event timing based on probability distributions
- E.g., "Hurricane has 15% annual probability" → randomly placed in MC runs

### 1.4 Tax Modeling (Depreciation Focus)
**Goal:** Generate depreciation schedules and estimate tax impact for CPA handoff

**Scope Clarification:**
This is NOT a tax software replacement. The goal is to:
1. Generate accurate depreciation schedules per property
2. Estimate tax liability for cash flow planning
3. Export data in CPA-friendly format

**What We Model:**
| Component | Implementation |
|-----------|----------------|
| **Depreciation Schedule** | 27.5-year straight-line on building (not land); land typically 15-20% of purchase |
| **Expense Summary** | Annual totals for deductible expenses (management, maintenance, insurance, HOA, interest) |
| **Taxable Income Estimate** | Revenue - expenses - depreciation = taxable income |
| **After-Tax Cash Flow** | Cash flow adjusted for estimated tax liability |

**What We DON'T Model (CPA Territory):**
- Passive activity loss rules and carryforwards
- Alternative Minimum Tax implications
- State-specific tax nuances
- Cost segregation studies
- Depreciation recapture on sale (flag it, don't calculate)

**Key Outputs:**
- Per-property depreciation schedule (for CPA)
- Annual taxable income estimate per property
- Portfolio-level tax liability rough estimate
- "Consult CPA" flags on complex situations

**Implementation:**
- Add `tax` section to config (marginal rate assumption, land percentage)
- Generate depreciation schedule at acquisition
- Annual tax summary report exportable for CPA

### 1.5 Unit-Level CapEx Schedule
**Goal:** Replace flat 10% reserve with realistic capital planning

**Per-Unit Tracking:**
- Age of property and major systems
- Expected replacement schedule:
  - HVAC: 15-20 years ($8,000-15,000)
  - Roof: 20-25 years ($15,000-30,000)
  - Appliances: 8-12 years ($3,000-8,000 full suite)
  - Flooring/paint: 5-7 years ($5,000-10,000)
  - Furniture/decor: 3-5 years ($5,000-15,000)
- Actual vs planned spending tracking
- Deferred maintenance accumulation (risk metric)

**Implementation:**
- `capex_schedule` per unit in config
- Monthly accrual based on replacement timeline
- Event triggers when items due
- Dashboard showing upcoming major expenses

---

### Phase 1C: Financing & Exit Planning

*Focus: Long-term financial visibility and eventual exit*

### 1.6 Enhanced Financing Dashboard
**Goal:** Deep visibility into debt structure and optimization opportunities

**Portfolio View:**
- Total debt by property with maturity dates
- Weighted average interest rate
- Monthly debt service breakdown (P&I per unit)
- Equity position visualization
- Refi opportunity alerts (rate drops, equity available)

**Per-Unit View:**
- Amortization schedule with prepayment impact
- LTV history and projection
- Interest savings from prepayment scenarios
- "What-if" refi calculator

**DSCR Loan Considerations:**
- Track DSCR requirements per lender (typically 1.2-1.25)
- Alert when property approaches DSCR covenant breach
- Model rate adjustments on ARM products if applicable

### 1.7 Exit Strategy Modeling
**Goal:** Plan for eventual portfolio liquidation (staggered or full sale)

**Exit Scenarios:**
The model should support two primary exit strategies:
1. **Staggered Exit** - Sell units individually over time
2. **Portfolio Sale** - Sell all units at once (potentially to an investor)

**Staggered Exit Modeling:**
- Select which unit(s) to sell and when (year/month)
- Calculate sale proceeds (value - debt - closing costs)
- Model capital gains (rough estimate, flag for CPA)
- Reinvest proceeds or distribute
- Continue simulation with remaining portfolio

**Portfolio Sale Modeling:**
- Set target exit year
- Calculate total portfolio value and equity
- Model bulk sale discount (if applicable, 5-15%)
- Estimate total capital gains exposure
- Final distribution to owner

**Key Outputs:**
- Net proceeds per unit or portfolio
- After-tax proceeds estimate (with CPA flag)
- Comparison: "What if I exit in Year 15 vs Year 20?"
- IRR calculation to exit date

**Implementation:**
- Add `exit_strategy` section to config
- Support multiple scheduled sales in events array
- Dashboard showing exit scenario comparisons

---

## Phase 2: Monte Carlo & AI Insights

### 2.1 Monte Carlo Simulation Framework
**Goal:** Move from single-path projections to probability distributions

**Variable Randomization:**
- Occupancy (seasonal + random variance)
- ADR (market trends + volatility)
- Appreciation (mean reversion around 3%)
- Interest rates (for future refi decisions)
- Event occurrence (per probability model from 1.2)
- Expense inflation (range around 4%)

**Output Distributions:**
- Portfolio value at Year 10, 20, 30 (5th, 50th, 95th percentile)
- Debt-free year probability curve
- Cash flow risk (months of negative CF probability)
- Maximum drawdown scenarios
- Probability of hitting target distributions

**Run Parameters:**
- 1,000-10,000 simulation runs
- Configurable random seed for reproducibility
- Parallel execution for performance

### 2.2 AI-Powered Insights Engine
**Goal:** Transform simulation output into actionable intelligence

**Analysis Capabilities:**
1. **Pattern Recognition**
   - Identify which assumptions most impact outcomes
   - Sensitivity analysis on key variables
   - Correlation between inputs and results

2. **Scenario Recommendations**
   - "Your portfolio is resilient to moderate rate increases"
   - "Consider delaying Unit 5 acquisition if occupancy drops below 70%"
   - "Hurricane risk is your largest tail event - consider additional reserves"

3. **Strategy Optimization**
   - Optimal prepayment allocation
   - Best refi timing under various rate scenarios
   - Diversification benefits (OB vs lake property)

4. **Narrative Generation**
   - Executive summaries for lender packages
   - Investment thesis documentation
   - Risk disclosure drafting

**Technical Approach:**
- Export simulation data to structured format (CSV/JSON)
- Use Claude or local LLM for analysis
- Prompt engineering for consistent, actionable outputs
- Human-in-the-loop for validation

---

## Phase 3: Deal Analysis Tool

### 3.1 Listing Analyzer
**Goal:** Rapidly screen listings against your strategy criteria

**Data Inputs:**
- MLS/listing data (price, beds, baths, sqft, HOA)
- Location coordinates (beach access, amenities)
- Listing photos (for condition assessment)
- Rental history if available

**Automated Analysis:**
| Metric | Calculation | Pass Criteria |
|--------|-------------|---------------|
| **Parity Price** | NOI / target yield | Listing ≤ parity |
| **Gross Yield** | Projected revenue / price | ≥ 8-10% |
| **Cash-on-Cash** | Year 1 CF / cash invested | ≥ 6-8% |
| **HOA Ratio** | HOA / gross revenue | ≤ 15% |
| **Insurance Estimate** | 3.3% of value | Flagged if excessive |

**Strategy Fit Scoring:**
- Location quality (beachfront, pools, amenities)
- Building age and condition
- Rental restriction risk
- HOA financial health indicators
- Comparable rental performance

**Output:**
- Quick Pass/Fail/Review score
- Key metrics at a glance
- Red flags and opportunities
- "Add to portfolio simulation" button

### 3.2 Market Intelligence
**Goal:** Understand market dynamics for better decisions

**Data Sources:**
- AirDNA (rental performance)
- Redfin/Zillow (sales data)
- Local MLS (active/pending/sold)
- County records (permits, assessments)

**Dashboards:**
- Average DOM (days on market) trends
- Price per sqft by location
- Rental revenue trends
- Supply/demand indicators
- Seasonal booking patterns

---

## Phase 4: Due Diligence Manager

### 4.1 Offer Pipeline Tracker
**Goal:** Never miss a task when making offers

**Pipeline Stages:**
1. **Initial Interest** - Listing saved, preliminary analysis done
2. **Tour Scheduled** - On-site visit planned
3. **Analysis Complete** - Full underwriting done
4. **Offer Submitted** - Formal offer in
5. **Under Contract** - Offer accepted, DD period active
6. **Due Diligence** - Inspections, financing, title
7. **Closing** - Final steps
8. **Closed / Dead** - Outcome

**Per-Deal Task Templates:**
- Request HOA financials and meeting minutes
- Order inspection
- Get insurance quotes (3 minimum)
- Review title commitment
- Verify rental history with management
- Check permit history
- Review condo docs (CC&Rs, bylaws)
- Confirm assessment history

### 4.2 Document Management
**Goal:** Organize all due diligence materials

**Categories:**
- Listing materials (photos, floorplans, disclosures)
- HOA documents (financials, reserves, meeting minutes)
- Inspection reports
- Insurance quotes
- Title documents
- Rental projections
- Correspondence

**Features:**
- Upload and tag documents
- Version tracking
- Expiration alerts (quotes, etc.)
- Share links for lender/attorney

### 4.3 Risk Checklist
**Goal:** Systematic risk assessment for each deal

**Categories:**
| Risk Area | Key Questions |
|-----------|---------------|
| **Physical** | Age of systems, deferred maintenance, flood zone |
| **HOA** | Reserve adequacy, special assessments, rental restrictions |
| **Market** | Supply trends, regulation risk, seasonal patterns |
| **Financial** | Cash flow stress test, insurance costs, tax implications |
| **Legal** | Clear title, CC&R compliance, permit issues |

---

## Phase 5: Financing Workbench

### 5.1 Lender Package Generator
**Goal:** Build compelling loan applications with AI assistance

**Package Components:**
1. **Executive Summary** - Investment thesis, strategy overview
2. **Borrower Profile** - Net worth, income, experience
3. **Property Analysis** - Underwriting, comps, projections
4. **Portfolio Context** - How this fits your strategy
5. **Risk Mitigation** - Reserves, insurance, contingencies
6. **Exit Strategy** - Hold period, sale scenarios, refinance options

**AI-Assisted Features:**
- Generate narrative summaries from simulation data
- Highlight strengths of the deal
- Anticipate lender questions
- Format for different lender types (bank, DSCR, portfolio)

### 5.2 Loan Comparison Tool
**Goal:** Optimize financing decisions

**Inputs:**
- Multiple loan quotes (rate, points, fees, terms)
- Expected hold period
- Prepayment plans
- Refi probability

**Outputs:**
- Effective APR comparison
- Break-even on points paid
- Cash flow impact analysis
- Optimal loan selection recommendation

### 5.3 Lender Relationship Tracker
**Goal:** Manage lender relationships over time

**Features:**
- Lender contact database
- Rate sheet history
- Application status tracking
- Closing timeline management
- Post-close relationship notes

---

## Phase 6: Portfolio & Property Management

**Scope Clarification:**
This is a **portfolio management layer**, not a replacement for booking platforms (Airbnb, VRBO) or full PMS tools (Hospitable, Guesty, OwnerRez). Those tools handle guest-facing operations. This system:
- Aggregates data from those platforms
- Provides owner-focused analytics and planning
- Connects actual performance back to the investment model

**Buy vs Make Decision:**
Evaluate existing PMS tools for operational features before building. Focus custom development on:
- Investment model integration (the unique value)
- Owner reporting and analytics
- Forward planning from actual data

### 6.1 Actual vs Model Reconciliation
**Goal:** Connect the simulation to reality

**Data Integration:**
- Booking calendar sync (Airbnb, VRBO, direct) via API
- Actual revenue tracking (nightly, cleaning, fees)
- Expense categorization (manual or bank feed)
- Payout reconciliation

**Model Calibration:**
- Compare projected vs actual by month
- Adjust assumptions based on real data
- Track forecast accuracy over time
- Identify systematic over/under estimation

### 6.2 Real-Time Portfolio Dashboard
**Goal:** Operational visibility across all units

**Metrics:**
- Current occupancy (booked nights this month)
- Revenue MTD vs budget
- Upcoming turnovers
- Maintenance tickets
- Guest reviews and ratings
- Cash position by account

### 6.3 Cleaning & Supplies Tracker
**Goal:** Manage turnover operations and consumables inventory

**Note:** This may be handled by existing PMS tools. Evaluate before building.

**If Building Custom:**
- Cleaning schedule per unit (synced with booking calendar)
- Cleaner assignment and payment tracking
- Supplies inventory per unit (toiletries, linens, kitchen items)
- Reorder alerts when supplies low
- Cost tracking per turnover

**Integration Points:**
- Pull checkout dates from Airbnb/VRBO
- Push cleaning tasks to cleaner (or integrate with Turno, etc.)
- Track actual cleaning costs for model accuracy

### 6.4 Forward Planning from Reality
**Goal:** Use actual data as new baseline for projections

**Features:**
- "What-if" from current state (not theoretical Day 1)
- Reforecast based on actual performance
- Scenario planning with real constraints
- Goal tracking (debt-free year, distribution targets)

### 6.5 Owner Reporting
**Goal:** Professional reports for your records and external sharing

**Report Types:**
- Monthly performance summary
- Annual tax package (for CPA)
- Portfolio valuation updates
- Cash flow statements
- Capital activity log

**Shareable Reports:**
- Lender updates (portfolio performance for refinancing)
- Insurance documentation (for claims or renewals)
- Exit preparation (due diligence package for buyers)

---

## Design Decisions & Context

### Confirmed Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Timeline** | ~4 years to first purchase | Build comprehensively; no "good enough" shortcuts |
| **Property Management** | Use PM (20% fee) | Already in model; owner focuses on portfolio, not operations |
| **Loan Type** | DSCR loans for OB condos | Required for investment properties; model already has DSCR validation |
| **Exit Strategy** | Variable timing, no 1031 | Will exit STR entirely; model staggered or portfolio sale |
| **Target Market** | STR only | No long-term rentals or flips; focused strategy |
| **Tool Philosophy** | Personal use, shareable outputs | Not productizing; lender reports and CPA exports shared externally |
| **Ownership Structure** | Solo investor | No partner/investor reporting or waterfall distributions |
| **Market Profiles** | Generic/configurable | Support OB + future markets (lake, etc.) via flexible profile system |
| **Notifications** | None | Dashboard-focused; no alerts or push notifications |

### Future Exploration (Lower Priority)
| Topic | Notes |
|-------|-------|
| **Regulation Tracking** | Gulf Shores/Orange Beach have been STR-friendly; monitor but don't over-engineer |
| **Competitive Intelligence** | Track supply trends in Phase 3 Market Intelligence; not critical for model |

### What's Strong About This Vision
1. **End-to-end thinking** - Covering analysis through management closes the loop
2. **Model-first approach** - Building strategy before buying prevents expensive mistakes
3. **Feeder strategy is sophisticated** - Concentrated equity building accelerates timeline
4. **Reserve management is prudent** - Three-tier system shows understanding of cash flow risks

---

## Implementation Approach

### Recommended Phasing

**Timeline:** ~4 years before first purchase. Build comprehensively.

```
Phase 1A: Core Revenue & Expense Accuracy
├── 1.1 Seasonality & Market Profiles    [Foundation - revenue accuracy]
└── 1.2 Insurance Modeling               [Foundation - expense accuracy]

Phase 1B: Stress Testing & Tax Planning
├── 1.3 Event Modeling (5 scenarios)     [Risk understanding]
├── 1.4 Tax/Depreciation                 [CPA handoff prep]
└── 1.5 CapEx Schedule                   [Realistic maintenance costs]

Phase 1C: Financing & Exit Planning
├── 1.6 Financing Dashboard              [Debt visibility]
└── 1.7 Exit Strategy                    [Long-term planning]

Phase 2: Monte Carlo & AI
├── 2.1 Monte Carlo Framework    [Probability distributions]
└── 2.2 AI Insights (v1)         [Summaries and sensitivity]

Phase 3: Deal Analysis           [Can start parallel with Phase 2]
├── 3.1 Listing Analyzer         [Screen listings quickly]
└── 3.2 Market Intelligence      [Market trends]

Phase 4: Due Diligence           [Before first offer]
├── 4.1 Offer Pipeline           [Task tracking]
├── 4.2 Document Management      [Organize DD materials]
└── 4.3 Risk Checklist           [Systematic assessment]

Phase 5: Financing               [Before first DSCR loan]
├── 5.1 Lender Package           [AI-assisted narrative]
├── 5.2 Loan Comparison          [Optimize loan selection]
└── 5.3 Lender Tracker           [Relationship management]

Phase 6: Portfolio Management    [After first property closes]
├── 6.1 Actual vs Model          [Close the loop]
├── 6.2 Real-Time Dashboard      [Operational visibility]
├── 6.3 Cleaning/Supplies        [Buy vs Make decision]
├── 6.4 Forward Planning         [Reforecast from reality]
└── 6.5 Owner Reporting          [Tax and lender reports]
```

### Technical Considerations

1. **Stay Modular** - Each phase should be independently useful
2. **Data First** - Establish data schemas early for integration
3. **API-Ready** - Build to integrate with external tools (AirDNA, PMS, etc.)
4. **Export-Friendly** - Always allow CSV/JSON export for analysis elsewhere
5. **Mobile Access** - Consider Streamlit mobile or simple PWA for field use

---

## Success Metrics

### Phase 1A Complete When:
- [ ] Seasonality affects projections with OB-specific curves
- [ ] Market profiles exist for OB (and placeholder for generic/lake)
- [ ] Insurance modeling includes named storm deductibles and flood
- [ ] Parity price calculation uses seasonal revenue (not flat)

### Phase 1B Complete When:
- [ ] 5 event scenarios can be scheduled by year/month
- [ ] Events correctly draw from reserves and trigger insurance claims
- [ ] Depreciation schedule generates automatically (CPA-ready export)
- [ ] CapEx schedules exist per unit with replacement timelines

### Phase 1C Complete When:
- [ ] Dashboard shows portfolio debt structure by unit
- [ ] Exit scenarios (staggered and portfolio sale) can be modeled
- [ ] IRR calculation works for any exit year

### Phase 2 Complete When:
- [ ] 1000-run Monte Carlo executes in <30 seconds
- [ ] Events randomized based on probability in MC runs
- [ ] Probability distributions visualize on dashboard
- [ ] AI generates readable executive summaries
- [ ] Sensitivity analysis identifies key drivers

### Phase 3 Complete When:
- [ ] Listing URL → analysis report in <60 seconds
- [ ] Pass/fail scoring aligns with manual analysis
- [ ] "Add to simulation" works seamlessly

### Phase 4 Complete When:
- [ ] First real offer uses the system end-to-end
- [ ] No due diligence task was missed
- [ ] Documents organized and accessible

### Phase 5 Complete When:
- [ ] DSCR lender package generated for first loan
- [ ] Lender commented positively on professionalism
- [ ] Loan comparison saved measurable money or time

### Phase 6 Complete When:
- [ ] Actual revenue flows into model monthly
- [ ] Projections reforecast from current state
- [ ] Year-end report generated for taxes
- [ ] Buy vs Make decision made on cleaning/supplies tracker

---

## Resolved Questions

| Question | Answer | Implication |
|----------|--------|-------------|
| **Partnership Plans?** | Solo investor only | No waterfall distributions or investor reporting needed |
| **Lake Property Market?** | Market TBD; flexibility is key | Build market profile system to be generic/configurable |
| **Active Monitoring Cadence?** | Frequent, manual checks | No alert/notification system needed; dashboard-focused |

---

## Appendix: Current Model Quick Reference

### Key Parameters (v2.3)
| Parameter | Value | Location in Config |
|-----------|-------|-------------------|
| Starting Cash | $5,000 | constants.financial.startingCash |
| Annual Savings | $50,000 | constants.financial.annualSavings |
| ADR Baseline | $425 | constants.operations.adrBaseline2BR |
| Occupancy | 78% | constants.operations.occupancyBaseline |
| Target Portfolio | 7 units | policies.portfolio.maxUnits |
| Mortgage Rate | 6.85% | constants.debt.mortgageRate |
| Refi Rate | 5.875% | constants.debt.refiRate |
| Appreciation | 3% | market.annualAppreciation |
| Revenue Inflation | 4% | market.revenueInflationRate |

### Key Outcomes (Baseline Simulation)
- **Year 5:** 3+ properties, NOI exceeds $50k annual contribution
- **Year 8:** ~$100k/year NOI
- **Year 17:** DSCR > 2.0, LTV ~57%
- **Year 22:** Debt-free, ~$980k/year NOI
- **Final Portfolio:** ~$3.5M+ value

---

## Phase 1 Requirements (To Be Developed)

*Next session: Build detailed requirements for Phase 1A, 1B, 1C*

### Questions to Answer During Requirements Session

**1.1 Seasonality & Market Profiles:**
- What data source will populate the initial OB seasonality curves?
- How should the model handle the first partial year (if purchase isn't January)?
- Should seasonality be adjustable per-unit or only per-market?

**1.2 Insurance Modeling:**
- What's the actual insurance rate for OB condos today? (Research needed)
- How should the model handle insurance renewals mid-year?
- What's a reasonable named storm deductible assumption (2%, 3%, 5%)?

**1.3 Event Modeling:**
- Should events be defined in the main config or a separate events file?
- How should overlapping events be handled (hurricane + market downturn)?
- What's the recovery curve shape for each event type?

**1.4 Tax Modeling:**
- What marginal tax rate assumption to use?
- How to handle land vs building split (use county assessment or fixed %)?
- What format does your CPA prefer for depreciation schedules?

**1.5 CapEx Schedule:**
- How to estimate system ages when purchasing existing condos?
- Should CapEx draw from the existing 10% reserve or a separate pool?
- How to handle HOA-covered items (roof, exterior) vs owner items (HVAC, appliances)?

**1.6 Financing Dashboard:**
- What visualizations would be most useful for refi decisions?
- Should the dashboard show "what-if" scenarios inline or as separate views?

**1.7 Exit Strategy:**
- What selling costs to assume (agent commission, closing costs)?
- How to model capital gains without recreating tax software?

### Data Gathering Before Requirements Session

Consider gathering before next session:
- [ ] Sample OB insurance quote (or typical rates from PM)
- [ ] AirDNA seasonal data for Orange Beach 2BR condos
- [ ] Typical HOA fee breakdown (what's covered vs owner responsibility)
- [ ] Sample depreciation schedule format from CPA

---

*This document should be treated as a living roadmap. Update as priorities shift, features complete, and new requirements emerge.*
