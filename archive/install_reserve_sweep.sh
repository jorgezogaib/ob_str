#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="${1:-.}"
cd "$REPO_ROOT"
cp "run_suite_full_V23.reserve_sweep.py" "run_suite_full_V23.py"
echo "Installed runner with Reserve Sweep (RainyTopUp/CapexTopUp)."