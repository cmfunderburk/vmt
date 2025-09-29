PYTHON ?= python3
PACKAGE = econsim

.PHONY: install dev lint format type test-unit perf manual-tests launcher enhanced-tests batch-tests bookmarks test tests clean venv token

# Create canonical development virtual environment (vmt-dev) and install deps
.PHONY: venv
venv:
	@if [ -d "vmt-dev" ]; then \
		echo "[venv] Existing vmt-dev directory detected; skipping creation."; \
	else \
		python3 -m venv vmt-dev && echo "[venv] Created vmt-dev virtual environment."; \
	fi
	@. vmt-dev/bin/activate && pip install --upgrade pip >/dev/null 2>&1 && echo "[venv] Upgraded pip." && pip install -e .[dev]
	@echo "[venv] Environment ready. Activate with: source vmt-dev/bin/activate"

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
	@echo "=== Synthetic Performance Test ==="
	$(PYTHON) scripts/perf_stub.py
	@echo ""
	@echo "=== Widget Performance Test ==="
	$(PYTHON) scripts/perf_stub.py --mode widget --duration 3 --json

token:
	# Generate VMT repository token analysis report
	@echo "📄 Generating token analysis report..."
	@if [ -d "vmt-dev" ]; then \
		. vmt-dev/bin/activate && cd llm_counter && $(PYTHON) generate_report.py; \
	else \
		cd llm_counter && $(PYTHON) generate_report.py; \
	fi
	@echo "✅ Report saved to llm_counter/vmt_token_report.md"

manual-tests:
	# Launch comprehensive manual GUI tests for unified target selection
	# 7 educational scenarios with visual observation and phase transitions  
	@if [ -d "vmt-dev" ]; then \
		echo "Using virtual environment..."; \
		. vmt-dev/bin/activate && cd MANUAL_TESTS && $(PYTHON) test_start_menu.py; \
	else \
		cd MANUAL_TESTS && $(PYTHON) test_start_menu.py; \
	fi

launcher:
	# Launch New VMT Enhanced Test Launcher with modular architecture
	# Launcher logs suppressed by default - set ECONSIM_LAUNCHER_SUPPRESS_LOGS=0 to re-enable.
	@if [ -d "vmt-dev" ]; then \
		echo "[launcher] Using virtual environment (new launcher system)."; \
		. vmt-dev/bin/activate && ECONSIM_LAUNCHER_SUPPRESS_LOGS=1 $(PYTHON) -m econsim.tools.launcher.runner; \
	else \
		echo "[launcher] Using system Python (new launcher system)."; \
		ECONSIM_LAUNCHER_SUPPRESS_LOGS=1 $(PYTHON) -m econsim.tools.launcher.runner; \
	fi

batch-tests:
	# Launch standalone batch test runner for sequential execution
	# Professional interface with progress tracking and time estimates
	@if [ -d "vmt-dev" ]; then \
		echo "Using virtual environment..."; \
		. vmt-dev/bin/activate && cd MANUAL_TESTS && $(PYTHON) batch_test_runner.py; \
	else \
		cd MANUAL_TESTS && $(PYTHON) batch_test_runner.py; \
	fi

bookmarks:
	# Launch standalone bookmark manager for organizing favorite configurations
	# Save, categorize, search, and quick-launch test configurations
	@if [ -d "vmt-dev" ]; then \
		echo "Using virtual environment..."; \
		. vmt-dev/bin/activate && cd MANUAL_TESTS && $(PYTHON) test_bookmarks.py; \
	else \
		cd MANUAL_TESTS && $(PYTHON) test_bookmarks.py; \
	fi

# Legacy aliases for backward compatibility
test: test-unit
	@echo "Note: 'make test' is now 'make test-unit'. Use 'make manual-tests' for GUI tests."

tests: manual-tests
	@echo "Note: 'make tests' is now 'make manual-tests'."

enhanced-tests:
	@echo "Note: 'make enhanced-tests' is now 'make launcher'."
	@$(MAKE) launcher

clean:
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	 rm -rf .mypy_cache .ruff_cache .pytest_cache
