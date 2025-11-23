#!/usr/bin/env bash
mkdir -p diag_bundle
cp runner/run_suite_full_V23.py diag_bundle/
cp engines/OB_STR_ENGINE_V2_3.json diag_bundle/
cp runner/*Monthly*.csv diag_bundle/ 2>/dev/null || true
zip -r diag_bundle.zip diag_bundle/
echo "DONE: Created diag_bundle.zip"
