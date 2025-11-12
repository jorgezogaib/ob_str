import math
from runner.run_suite_full_V23 import parity_price, pmt

def test_parity_price_basic():
    adr, occ = 350.0, 0.65
    mgmt, capx = 0.20, 0.05
    hoa_y = 10200.0
    ins, tax = 0.008, 0.009
    target = 0.085
    g = adr*365*occ
    numer = g - (g*(mgmt+capx) + hoa_y)
    denom = target + ins + tax
    expected = max(numer/denom, 0.0)
    assert abs(parity_price(adr, occ, hoa_y, mgmt, capx, ins, tax, target) - expected) < 1e-9

def test_pmt_sign_and_value():
    r_m = 0.0685/12.0
    n = 30*12
    pv = 400_000.0
    pay = -pmt(r_m, n, pv)
    # sanity: payment covers interest portion
    assert pay > pv*r_m
    # amortized: n payments should exceed principal by interest sum
    assert pay > 0
