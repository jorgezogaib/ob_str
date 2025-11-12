.PHONY: test smoke ci

VENV?=.venv
PY?=python

test:
	pytest -q

smoke:
	pytest -q tests/schema tests/integration tests/diag

ci:
	pytest -q -k "not golden"
