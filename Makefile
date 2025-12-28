# Makefile for ob_str project
# Assumes: Python + pip + streamlit available in the environment.

PYTHON      := python
PIP         := pip
PROJECT_DIR := $(PWD)

export PYTHONPATH := $(PROJECT_DIR)

.DEFAULT_GOAL := smoke

.PHONY: setup ui run smoke test golden clean

# Install Python deps (idempotent, safe to re-run)
setup:
	$(PIP) install -q -r requirements.txt

# Launch Streamlit UI
ui:
	streamlit run ui/app.py --server.port=8501 --server.address=0.0.0.0

# One-off engine run (using run_quick.py helper script)
run:
	@export PYTHONPATH=$(PROJECT_DIR); \
	$(PYTHON) run_quick.py

# Fast safety net: schema + integration identities + diagnostics only
smoke:
	@export PYTHONPATH=$(PROJECT_DIR); \
	pytest -q tests/schema tests/integration tests/diag

# Full test suite (everything under tests/)
test:
	@export PYTHONPATH=$(PROJECT_DIR); \
	pytest -q

# Regenerate golden snapshots to match current engine behavior
golden:
	@export PYTHONPATH=$(PROJECT_DIR); \
	$(PYTHON) tools/update_golden.py

# Cleanup artifacts / caches (non-destructive to source)
clean:
	@rm -f out/*.csv 2>/dev/null || true
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
