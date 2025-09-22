PYTHON ?= python
PACKAGE = econsim

.PHONY: install dev lint format type test perf clean

install:
	$(PYTHON) -m pip install -e .[dev]

dev:
	$(PYTHON) -m $(PACKAGE).main

lint:
	ruff check src tests
	black --check src tests

format:
	black src tests
	ruff check --fix src tests || true

type:
	mypy src

test:
	pytest -q

perf:
	$(PYTHON) scripts/perf_stub.py

clean:
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	 rm -rf .mypy_cache .ruff_cache .pytest_cache
