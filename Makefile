PYTHON ?= python3
PACKAGE = econsim

.PHONY: install dev lint format type test-unit perf manual-tests test tests clean

install:
	$(PYTHON) -m pip install -e .[dev]

dev:
	# Launch the new GUI shell by default (Start Menu + controller stack).
	# To run the legacy minimal bootstrap instead: ECONSIM_NEW_GUI=0 make dev
	ECONSIM_NEW_GUI=1 $(PYTHON) -m $(PACKAGE).main

lint:
	ruff check src tests
	black --check src tests

format:
	black src tests
	ruff check --fix src tests || true

type:
	mypy src

test-unit:
	# Run comprehensive automated unit/integration tests (210+ tests)
	# Used for development validation, determinism checks, and CI/CD
	pytest -q

perf:
	$(PYTHON) scripts/perf_stub.py

manual-tests:
	# Launch comprehensive manual GUI tests for unified target selection
	# 7 educational scenarios with visual observation and phase transitions  
	cd MANUAL_TESTS && $(PYTHON) test_start_menu.py

# Legacy aliases for backward compatibility
test: test-unit
	@echo "Note: 'make test' is now 'make test-unit'. Use 'make manual-tests' for GUI tests."

tests: manual-tests
	@echo "Note: 'make tests' is now 'make manual-tests'."

clean:
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	 rm -rf .mypy_cache .ruff_cache .pytest_cache
