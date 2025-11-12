from ui.lender_metrics import dscr, icr, cap_rate, breakeven_occupancy

def test_dscr_basic():
    assert dscr(2000, 1000) == 2.0
    assert dscr(0, 1000) == 0.0
    assert dscr(2000, 0) is None

def test_icr_basic():
    assert icr(1500, 500) == 3.0
    assert icr(0, 500) == 0.0
    assert icr(1500, 0) is None

def test_cap_rate_basic():
    assert round(cap_rate(24000, 300000), 6) == round(0.08, 6)
    assert cap_rate(24000, 0) is None

def test_breakeven_occ_sane():
    adr = 300.0; days = 30.0
    mgmt = 0.2; capx = 0.05
    fixed = 1500.0  # HOA+Ins+Tax
    ds = 1800.0
    occ = breakeven_occupancy(adr, days, mgmt, capx, fixed, ds)
    assert occ is not None and 0.0 <= occ <= 1.0
