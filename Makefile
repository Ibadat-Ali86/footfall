# Makefile

.PHONY: install test lint types check reproduce clean phase0

## Install all dependencies (frozen lockfile)
install:
	uv sync --frozen --group dev

## Run the full test suite
test:
	uv run pytest -q --cov=footfall --cov-report=term-missing

## Run linter
lint:
	uv run ruff check .
	uv run ruff format --check .

## Run type checker
types:
	uv run mypy src

## Run all checks (lint + types + tests)
check: lint types test

## Run Phase 0 hypothesis evaluation (task T0.9)
phase0:
	uv run python scripts/evaluate_h1.py

## Rebuild derived tables from raw snapshots and verify output hashes match.
## Fails CI if any hash differs (section 11.5 of the build documentation).
reproduce:
	@echo "reproduce: not yet implemented (task T1.7)"
	@exit 1

## Remove build artifacts
clean:
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage dist build
	find . -type d -name __pycache__ -exec rm -rf {} +
