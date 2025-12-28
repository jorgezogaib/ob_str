# Documentation Consolidation Plan
**Date:** 2025-12-28
**Purpose:** Reduce documentation clutter, consolidate related content, and archive outdated materials

---

## Current State Assessment

**Total Documentation Files:** 41 markdown files in root directory
**Issue:** Significant overlap, outdated content, and difficult to navigate

---

## Consolidation Strategy

### Phase 1: Keep as Primary Documentation (7 files)

These files represent the current source of truth and should remain in root:

1. **README.md** ✅
   - Primary technical reference manual
   - Current and comprehensive
   - **ACTION:** Keep as-is

2. **CODE_REVIEW_REPORT.md** ✅
   - Comprehensive codebase analysis (Dec 27, 2025)
   - Recent and valuable
   - **ACTION:** Keep as-is

3. **PHASE_1_CHANGES.md** ✅
   - Documents critical fixes completed
   - Recent completion report (Dec 27, 2025)
   - **ACTION:** Keep as-is

4. **UI_UAT_HANDOFF.md** ✅
   - Current UI status and UAT session guide
   - Actively used for UI refinement
   - **ACTION:** Keep as-is

5. **VALIDATION_FRAMEWORK_SUMMARY.md** ✅
   - Documents implemented validation system
   - Current feature documentation
   - **ACTION:** Keep as-is

6. **DISTRIBUTION_POLICY_DESIGN.md** ✅
   - Financial freedom milestones and configuration
   - Strategic planning document
   - **ACTION:** Keep as-is

7. **.gitignore** (if exists) ✅
   - **ACTION:** Keep as-is

---

### Phase 2: Consolidate into Archive Folders

Create organized archive structure for completed work and historical analysis.

#### A. Create `docs/archive/optimization/` folder

**Purpose:** Historical record of optimization work

**Files to move:**
1. FEEDER_OPTIMIZATION_MEMO.md (original proposal)
2. OPTIMIZATION_BREAKDOWN.md (detailed breakdown)
3. OPTIMIZATION_2_REQUIREMENTS.md (unimplemented alternative)
4. comparison_report.md (Stage 1 results)
5. stage2_comparison.md (Stage 2 results)
6. stage3_comparison.md (Stage 3 rejection)

**Create consolidation:** `docs/archive/optimization/OPTIMIZATION_HISTORY.md`
- Consolidates: OPTIMIZATION_FINAL_SUMMARY.md content
- Links to individual stage reports
- Summary of what was implemented (Opt 1+3), what was rejected (Opt 4), what was not pursued (Opt 2)

**Total:** Move 6 files, create 1 summary → Net: +1 file in archive, -6 in root

---

#### B. Create `docs/archive/validation/` folder

**Purpose:** Historical validation work and analysis

**Files to move:**
1. VALIDATION_RECOMMENDATIONS.md
2. VALIDATION_SESSION_PROMPT.md
3. VALIDATION_QUICK_REFERENCE.md
4. VALIDATION_EXPORT_GUIDE.md
5. VALIDATION_ANALYSIS.md
6. RESERVE_VALIDATION_REPORT.md
7. RESERVE_SWEEPS_RESULTS.md
8. test_reserve_mechanics.md
9. ALIGNMENT_GAP_ANALYSIS.md
10. OPERATING_CASH_DEBUG_HANDOFF.md

**Note:** VALIDATION_FRAMEWORK_SUMMARY.md stays in root (current documentation)

**Total:** Move 10 files to archive

---

#### C. Create `docs/archive/ui_implementation/` folder

**Purpose:** UI development history and session prompts

**Files to move:**
1. STR_INVESTOR_UI_ASSESSMENT.md
2. UI_FEATURE_GAP_SUMMARY.md
3. DATA_COMPLETENESS_FOR_UI.md
4. EXPENSE_RATIOS_AND_RETURN_METRICS_SUMMARY.md
5. UI_IMPLEMENTATION_PROMPT.md
6. UI_IMPLEMENTATION_PROMPT_FINAL.md
7. READY_FOR_NEW_SESSION.md
8. UI_CONFIG_FIX.md

**Note:** UI_UAT_HANDOFF.md stays in root (current UAT guide)

**Total:** Move 8 files to archive

---

#### D. Create `docs/archive/distribution/` folder

**Purpose:** Distribution feature implementation history

**Files to move:**
1. DISTRIBUTION_IMPLEMENTATION_SUMMARY.md
2. DISTRIBUTION_QUICK_START.md
3. DISTRIBUTION_SIMPLE_MODE.md
4. UI_DISTRIBUTION_CONTROLS.md
5. UI_DISTRIBUTION_DISPLAY.md
6. VIEW_DISTRIBUTIONS.md
7. DISTRIBUTION_UI_FIX.md
8. WATERFALL_IMPLEMENTATION.md
9. INVESTOR_REPORTS_SUMMARY.md
10. UNIT_LEVEL_REPORTING.md

**Note:** DISTRIBUTION_POLICY_DESIGN.md stays in root (strategic document)

**Total:** Move 10 files to archive

---

#### E. Create `docs/archive/phase2_candidates/` folder

**Purpose:** Documents for potential Phase 2 refactoring work

**File to move:**
1. PHASE_2_CHANGES.md (outlines future refactoring work)

**Total:** Move 1 file to archive

---

### Phase 3: Delete Obsolete/Redundant Files

#### Temporary Analysis Scripts (Delete - 9 files)

These were one-time analysis scripts, no longer needed:

1. ❌ analyze_distribution_triggers.py
2. ❌ analyze_distributions.py
3. ❌ analyze_distributions_simple.py
4. ❌ analyze_year5.py
5. ❌ compare_stage3.py
6. ❌ compare_sweeps.py
7. ❌ compare_validations.py
8. ❌ generate_investor_reports.py
9. ❌ generate_unit_reports.py

**Rationale:** These were exploratory scripts. Analysis is complete, results documented. UI now provides these capabilities.

---

#### Obsolete Test Scripts (Delete - 4 files)

1. ❌ test_reserve_mechanics.md → Already archived above
2. ❌ test_unit_metrics.py → Unit metrics now integrated into simulator
3. ❌ test_validations.py → Validation now in test suite
4. ❌ test_waterfalls.py → Waterfall logic now in UI

**Rationale:** Functionality integrated into main codebase or test suite.

---

### Phase 4: Create New Consolidated Documentation

#### Create `docs/QUICKSTART.md`

**Purpose:** Simple getting-started guide

**Content:**
```markdown
# OB STR Engine - Quick Start

## Run Simulation
```bash
obrun
```
Outputs: `out/OB_STR_V2_3_Monthly_YYYY-MM-DD.csv` and YoY file

## Launch Dashboard
```bash
Launch_STR_Dashboard.bat
```
Opens browser at http://localhost:8501

## Modify Parameters
Edit: `ob_str_engine/OB_STR_ENGINE_V2_3.json`

## Run Tests
```bash
make test
```

See README.md for complete technical reference.
```

---

#### Create `docs/PROJECT_STATUS.md`

**Purpose:** Current project status snapshot

**Content:**
- Current version (v2.3)
- Implemented features
- Recent completions (optimization, UI, validation)
- Known issues (if any)
- Next planned work (if any)

---

## Summary of Changes

### File Count Impact

| Category | Current | After Consolidation | Change |
|----------|---------|---------------------|--------|
| Root .md files | 41 | 9 | -32 |
| Root .py scripts | 9 | 1 (run_quick.py) | -8 |
| Archive files | 0 | 35 | +35 |
| New docs | 0 | 2 | +2 |

### New Root Directory Structure

```
/
├── README.md                              # Technical reference
├── CODE_REVIEW_REPORT.md                  # Codebase analysis
├── PHASE_1_CHANGES.md                     # Critical fixes completion
├── UI_UAT_HANDOFF.md                      # UI status
├── VALIDATION_FRAMEWORK_SUMMARY.md        # Validation docs
├── DISTRIBUTION_POLICY_DESIGN.md          # Strategic planning
├── .gitignore                             # Git config
├── Makefile                               # Build commands
├── requirements.txt                       # Python deps
├── run_quick.py                           # Quick runner script
├── Launch_STR_Dashboard.bat               # UI launcher
├── docs/
│   ├── QUICKSTART.md                      # NEW - Getting started
│   ├── PROJECT_STATUS.md                  # NEW - Current status
│   └── archive/
│       ├── optimization/                  # Optimization history
│       ├── validation/                    # Validation work
│       ├── ui_implementation/             # UI dev history
│       ├── distribution/                  # Distribution feature
│       └── phase2_candidates/             # Future work
├── ob_str_engine/                         # Engine code
├── ui/                                    # Dashboard UI
├── tests/                                 # Test suite
└── out/                                   # Output CSVs
```

---

## Implementation Steps

1. **Backup first** - Git commit all current work
2. **Create folder structure** - `docs/archive/` with subfolders
3. **Move files** to appropriate archive folders (35 files)
4. **Delete obsolete scripts** (9 analysis scripts + 4 test scripts)
5. **Create new docs** (QUICKSTART.md, PROJECT_STATUS.md)
6. **Verify** - Ensure all cross-references still work
7. **Git commit** - Document consolidation in commit message

---

## Risks & Mitigation

**Risk:** Breaking links in documentation
- **Mitigation:** Search all .md files for cross-references before moving

**Risk:** Accidentally deleting important files
- **Mitigation:** Git commit before consolidation, can revert if needed

**Risk:** Confusion about where to find things
- **Mitigation:** Create PROJECT_STATUS.md with clear pointers to key docs

---

## Decision Required

**Option A: Full Consolidation (Recommended)**
- Move 35 files to archive
- Delete 13 obsolete files
- Create 2 new summary docs
- **Result:** Clean root with 9 essential docs

**Option B: Conservative Consolidation**
- Move 35 files to archive
- Keep all scripts (no deletion)
- Create 2 new summary docs
- **Result:** Cleaner root, but some clutter remains

**Option C: Archive Only (No Deletion)**
- Move files to archive
- Don't delete anything
- **Result:** Root is cleaner, but redundant files preserved

---

## Recommendation

**Choose Option A (Full Consolidation)**

**Rationale:**
1. All obsolete scripts have completed their purpose
2. Functionality is integrated into main codebase or UI
3. Git history preserves everything if needed
4. Clean root makes project more approachable
5. Archive preserves historical context for future reference

---

## Post-Consolidation Validation

After consolidation, verify:
- [ ] UI launches correctly (no broken imports)
- [ ] Tests run successfully
- [ ] `obrun` command works
- [ ] All links in README.md still valid
- [ ] Git status shows expected moves/deletes
