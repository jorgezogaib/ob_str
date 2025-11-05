Short Term Rentals — V2_3 Codex Run Card
========================================
Goal: Execute the STR runner with the locked engine to produce two CSVs.

1) If you uploaded a ZIP, unzip it:
   unzip -o STR_V2_3_Codex_Boot_Pack.zip

2) Run the simulation:
   python -u run_suite_full_V23.py

   Expected stdout (no FAIL lines):
     Engine path: ... exists: True
     Will write: V2_3_Monthly.csv V2_3_YearOverYear.csv
     DONE

3) Artifacts to download from Codex:
   - V2_3_Monthly.csv
   - V2_3_YearOverYear.csv
   - (optional) copy/paste the full stdout block

4) If you need to point to a different engine path, set:
   ENGINE_OVERRIDE=/mnt/data/OB_STR_ENGINE_V2_3.json python -u run_suite_full_V23.py

5) Bring the two CSVs + stdout back to the design chat for verification.
