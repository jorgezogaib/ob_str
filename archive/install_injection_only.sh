#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="${1:-.}"
cd "$REPO_ROOT"
cp "run_suite_full_V23.injection_only.py" "run_suite_full_V23.py"
echo "Installed runner with monthly capital injection (NewMoneyIn)."