# run_suite_full_V23.reserve_sweep.py
# --- Reserve sweep (targets → move from HY_Unres into reserves) ---
monthly_HOA     = HOA_Y / 12.0
rainy_target_m  = rainyMonths * (ds_total + monthly_HOA)
capex_target_m  = capexAnnualTarget / 12.0

gap_rainy  = max(0.0, rainy_target_m - HY_Rainy)
RainyTopUp = min(HY_Unres, gap_rainy)
HY_Unres  -= RainyTopUp
HY_Rainy  += RainyTopUp

gap_capex  = max(0.0, capex_target_m - HY_Capex)
CapexTopUp = min(HY_Unres, gap_capex)
HY_Unres  -= CapexTopUp
HY_Capex  += CapexTopUp
# --- end sweep ---
