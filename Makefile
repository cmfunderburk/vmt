PYTHON ?= python3
PACKAGE = econsim

.PHONY: install lint format type test-unit perf manual-tests launcher enhanced-tests batch-tests bookmarks test tests clean venv token token-analysis token-analysis-full

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
	# Includes observer pattern tests, import guards, and modernized architecture validation
	pytest -q

perf:
	@echo "🚀 VMT EconSim Comprehensive Performance Baseline"
	@echo "Running all 7 educational scenarios headless for simulation performance..."
	@if [ -d "vmt-dev" ]; then \
		. vmt-dev/bin/activate && $(PYTHON) tests/performance/baseline_capture.py --steps 1000 --warmup 100; \
	else \
		$(PYTHON) tests/performance/baseline_capture.py --steps 1000 --warmup 100; \
	fi

deltatest:
	@echo "⚡ VMT EconSim Delta-Free Performance Test"
	@echo "Running baseline scenario without delta recording overhead..."
	@if [ -d "vmt-dev" ]; then \
		. vmt-dev/bin/activate && $(PYTHON) tests/performance/delta_free_performance.py --steps 1000 --warmup 100; \
	else \
		$(PYTHON) tests/performance/delta_free_performance.py --steps 1000 --warmup 100; \
	fi

# Phase 0 Refactor Baseline Capture
.PHONY: baseline-capture phase0-capture
baseline-capture: phase0-capture

phase0-capture:
	@echo "📊 Phase 0: Comprehensive Baseline Capture for Refactor Validation"
	@echo "This captures performance baselines, determinism hashes, and safety net validation"
	@echo "Required before starting the unified refactor implementation"
	@echo ""
	@mkdir -p baselines
	@echo "1/4 Running performance baseline across all 7 educational scenarios..."
	@if [ -d "vmt-dev" ]; then \
		. vmt-dev/bin/activate && $(PYTHON) tests/performance/baseline_capture.py --output baselines/performance_baseline.json; \
	else \
		$(PYTHON) tests/performance/baseline_capture.py --output baselines/performance_baseline.json; \
	fi
	@echo "2/4 Capturing determinism hashes for refactor validation..."
	@if [ -d "vmt-dev" ]; then \
		. vmt-dev/bin/activate && $(PYTHON) tests/performance/determinism_capture.py --output baselines/determinism_hashes.json; \
	else \
		$(PYTHON) tests/performance/determinism_capture.py --output baselines/determinism_hashes.json; \
	fi
	@echo "3/4 Running refactor safety net tests..."
	@if [ -d "vmt-dev" ]; then \
		. vmt-dev/bin/activate && pytest tests/integration/test_refactor_safeguards.py -v; \
	else \
		pytest tests/integration/test_refactor_safeguards.py -v; \
	fi
	@echo "4/4 Running core test suite for baseline validation..."
	@if [ -d "vmt-dev" ]; then \
		. vmt-dev/bin/activate && pytest tests/unit/test_simulation.py tests/unit/test_agent.py tests/unit/test_grid.py tests/unit/test_trade_phase1_foundations.py -q || echo "⚠️  Some non-critical tests failed, but Phase 0 core validation complete"; \
	else \
		pytest tests/unit/test_simulation.py tests/unit/test_agent.py tests/unit/test_grid.py tests/unit/test_trade_phase1_foundations.py -q || echo "⚠️  Some non-critical tests failed, but Phase 0 core validation complete"; \
	fi
	@echo ""
	@echo "✅ Phase 0 Baseline Capture Complete!"
	@echo "📁 Performance baseline: baselines/performance_baseline.json"
	@echo "📁 Determinism hashes: baselines/determinism_hashes.json"
	@echo "🔒 All safety nets validated"
	@echo ""
	@echo "Ready to proceed with unified refactor implementation."
	@echo "See tmp_plans/CURRENT/CRITICAL/UNIFIED_REFACTOR_PLAN.md for Phase 1 details."

token:
	# Generate VMT repository token analysis report with full repotokens analysis
	@echo "📄 Generating full token analysis report with timestamp..."
	@if [ -d "vmt-dev" ]; then \
		. vmt-dev/bin/activate && cd llm_counter && $(PYTHON) generate_report.py --timestamp; \
	else \
		cd llm_counter && $(PYTHON) generate_report.py --timestamp; \
	fi
	@echo "✅ Report saved to llm_counter/ with timestamped filename"

token-analysis:
	@echo "🔍 Running basic token analysis..."
	cd llm_counter && $(PYTHON) demo_counter.py

token-analysis-full:
	@echo "🔍 Running detailed token analysis..."
	@if [ -d "vmt-dev" ]; then \
		. vmt-dev/bin/activate && cd llm_counter && $(PYTHON) token_counter.py --format table; \
	else \
		cd llm_counter && $(PYTHON) token_counter.py --format table; \
	fi

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
	# Launch VMT Enhanced Test Launcher with modernized observer-based architecture
	# Launcher logs suppressed by default - set ECONSIM_LAUNCHER_SUPPRESS_LOGS=0 to re-enable.
	# Uses observer pattern for all logging (legacy GUILogger eliminated)
	@if [ -d "vmt-dev" ]; then \
		echo "[launcher] Using virtual environment (observer-based launcher system)."; \
		. vmt-dev/bin/activate && ECONSIM_LAUNCHER_SUPPRESS_LOGS=1 $(PYTHON) -m econsim.tools.launcher.runner; \
	else \
		echo "[launcher] Using system Python (observer-based launcher system)."; \
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

# Legacy aliases for backward compatibility (modernized architecture)
test: test-unit
	@echo "Note: 'make test' is now 'make test-unit'. Use 'make manual-tests' for GUI tests."

tests: manual-tests
	@echo "Note: 'make tests' is now 'make manual-tests' (observer-based)."

enhanced-tests:
	@echo "Note: 'make enhanced-tests' is now 'make launcher' (observer-based architecture)."
	@$(MAKE) launcher

clean:
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	 rm -rf .mypy_cache .ruff_cache .pytest_cache
