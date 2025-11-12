#!/usr/bin/env bash
set -euo pipefail

# Usage: bash install_mvp_v23.sh <repo_root>
REPO_ROOT="${1:-.}"
cd "$REPO_ROOT"

# Backup originals if present
[[ -f run_suite_full_V23.py ]] && cp run_suite_full_V23.py run_suite_full_V23.py.bak || true
[[ -f OB_STR_ENGINE_V2_3.json ]] && cp OB_STR_ENGINE_V2_3.json OB_STR_ENGINE_V2_3.json.bak || true

# Install new engine JSON and runner
cp "OB_STR_ENGINE_V2_3.MVP.json" "$REPO_ROOT/OB_STR_ENGINE_V2_3.json"
cp "run_suite_full_V23.MVP.py" "$REPO_ROOT/run_suite_full_V23.py"


echo "Installed MVP v2.3 engine+runner."
echo "Run:  python run_suite_full_V23.py"