import json
import pandas as pd
from pathlib import Path
from runner.run_suite_full_V23 import simulate

ENGINE = Path("engines/OB_STR_ENGINE_V2_3.json")

EXPECTED = [
 "YYYY-MM","UnitID","Starting Cash","Savings In","Gross Revenue","Mgmt Expense","CapEx Operating","HOA",
 "Insurance","Property Tax","Debt Service (Total)","Scheduled Principal","Interest Portion","Ops Net",
 "HY Interest (Cash)","HY Interest (Rainy)","HY Interest (Capex)",
 "Rainy Top-Up","Capex Top-Up","Rainy Balance","Capex Balance",
 "Liquidity Required","Liquidity Actual","Liquidity Ratio","Freeze Flag",
 "Accessible Principal","Deployable (Cash+Accessible)",
 "Feeder Draw (Net)","Feeder Prepay",
 "Purchase: Down Payment","Purchase: Closing Costs","Purchase: Initial Rainy Funding","Purchase Out (Total)",
 "New Loan Principal","Loan Balance (End)","End Cash","Units Owned"
]

def test_monthly_columns_match_expected_order():
    e = json.loads(ENGINE.read_text())
    rows = simulate(e, mmax=2)
    df = pd.DataFrame(rows)
    assert list(df.columns) == EXPECTED
