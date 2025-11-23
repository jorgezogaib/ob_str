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
	@if lsof -i :8501 >/dev/null 2>&1; then \
		echo "Killing stale Streamlit process on port 8501..."; \
		kill -9 $$(lsof -t -i :8501); \
	fi
	@echo "Clearing Codespaces port forwarding..."
	@gp ports close --port 8501 >/dev/null 2>&1 || true
	streamlit run app.py --server.port=8501 --server.address=0.0.0.0


# One-off engine run + quick peek at the monthly CSV header
run:
	@export PYTHONPATH=$(PROJECT_DIR); \
	QUIET=1 $(PYTHON) runner/run_suite_full_V23.py && \
	head -n 5 runner/V2_3_Monthly.csv

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
	@rm -f runner/V2_3_Monthly.csv runner/V2_3_YearOverYear.csv || true
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
