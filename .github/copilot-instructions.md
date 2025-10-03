**Goal**: Maintain a deterministic educational microeconomics simulation (PyQt6 + Pygame) while safely refactoring legacy systems. Economic coherence > visual consistency. Never add rollback/ghost state to "preserve hashes."

**🚨 CRITICAL REFACTOR CONTEXT (October 2025)**: This codebase is undergoing a **comprehensive refactor pass**. All invariants, patterns, and architectural decisions are open to change during this process, but **ANY invariant change must be explicitly approved by the user first**. When proposing changes that affect determinism, performance baselines, API contracts, or core architectural patterns, always seek user approval before implementation.

### Architecture Overview
**Core Loop**: PyQt6 QTimer (16ms) → `Simulation.step(ext_rng)` → `StepExecutor` pipeline (Movement → Collection → Trading → Metrics → Respawn) → Pygame blit → Qt paint

**Key Directories**:
- `src/econsim/simulation/` - Core simulation logic & execution pipeline
- `src/econsim/gui/` - PyQt6 GUI with embedded Pygame surface  
- `src/econsim/observability/` - Event system & logging infrastructure
- `src/econsim/tools/launcher/` - Main GUI application entry point
- `tests/` - Comprehensive test suite (436 tests) with performance baselines
- `baselines/` - Determinism hashes and performance references for validation
- `MANUAL_TESTS/` - Interactive GUI test scenarios and launcher components

### Development Workflow
```bash
make venv && source vmt-dev/bin/activate  # Create dev environment
make launcher                             # Primary development interface (canonical)
pytest -q                               # Run 436 tests for validation
make perf                               # Performance comparison vs baselines
make token                              # Generate LLM token usage report
```

**CRITICAL**: `make launcher` is the **canonical user-facing environment**. `make dev` is **outdated** and scheduled for deprecation - its functionality needs migration into the new launcher architecture.

**Development Commands**:
- `make dev` - **DEPRECATED** Enhanced GUI (legacy bootstrap with `ECONSIM_NEW_GUI=0`)
- `make test-unit` - Full test suite alias
- `make lint` - Ruff + Black code quality checks
- `make format` - Auto-format with Black + Ruff
- `make token` - Generate LLM context token analysis report (see `llm_counter/`)

**⚠️ ACTIVE LOGGING ARCHITECTURE REWRITE (October 2025)**:
**STATUS**: Raw Data Recording implementation in progress - Phases 1-2 complete, Phase 3+ in active development
**APPROACH**: Zero-overhead raw dictionary storage replacing 6-layer transformation pipeline

**Current Implementation Context**:
- **Phase 1-2 COMPLETE**: `RawDataObserver`, `DataTranslator`, `RawDataWriter` implemented with 112 tests
- **Phase 3+ ACTIVE**: Migrating simulation handlers from event objects to `observer.record_*()` calls
- **Target**: <0.1% overhead (100x improvement), eliminate ~3500 lines of complex serialization
- **Architecture**: Raw dictionaries → DataTranslator → Human-readable (on-demand only)

**AI Agent Guidelines During Active Implementation**:
- **DO** replace `Event.create()` calls with `observer.record_*()` direct dictionary storage
- **DO** use raw data architecture for new event types (simple dictionary append)
- **DO NOT** extend the legacy `optimized_serializer.py` 6-layer pipeline
- **DO NOT** create new event classes - use raw dictionaries exclusively
- **REFERENCE**: `tmp_plans/CURRENT/AAA/LOG_ARCHITECTURE_IMPLEMENTATION_CHECKLIST_RAW_DATA.md` for current status

**Headless mode**: `QT_QPA_PLATFORM=offscreen SDL_VIDEODRIVER=dummy make launcher`

### Development Environment Setup
**Virtual Environment Required**: Always use the canonical development setup to ensure consistent dependencies and avoid environment conflicts:
```bash
make venv                             # Creates vmt-dev/ virtual environment
source vmt-dev/bin/activate           # Activate for development sessions
make install                          # Install package in editable mode with dev dependencies
```

**Key Development Files**:
- `pyproject.toml` - Modern Python packaging with setuptools>=68
- `tests/conftest.py` - Global test fixtures with automatic trade flag cleanup
- `Makefile` - Comprehensive development workflow automation

### Simulation Construction Pattern ⚠️ REFACTOR-MUTABLE
**Current pattern** - factory method (subject to refactor improvement):
```python
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
cfg = SimConfig(grid_size=(12,12), seed=123, enable_respawn=True, enable_metrics=True)
sim = Simulation.from_config(cfg, agent_positions=[(0,0)])
```

**⚠️ REFACTOR PROTOCOL**: If you identify improvements to the construction pattern, propose changes to the user before implementing.

### Critical Determinism Invariants ⚠️ REFACTOR-MUTABLE
**Note**: During comprehensive refactor, these invariants may change with user approval.

1. Resources: iterate only via `Grid.iter_resources_sorted()`
2. Selection tie-breaking: `(-ΔU, distance, x, y)`; trade priority: `(-ΔU, seller_id, buyer_id, give_type, take_type)`
3. Agent order: preserve original list order within each step (no mid-step resorting)
4. RNG separation: external `step(ext_rng)` parameter vs internal `_rng` (no extra draws)
5. Trade execution: maximum one executed trade per step when enabled

**⚠️ REFACTOR PROTOCOL**: If you identify opportunities to improve these invariants (performance, clarity, maintainability), propose the change to the user with rationale before implementing.

### Modular Handler Architecture
**Add new step logic**: Create handlers in `simulation/execution/handlers/` subclassing `BaseStepHandler`. Never expand `Simulation.step()` directly.

Handler pattern:
- Input: `StepContext` (immutable simulation view)
- Output: `StepResult` (metrics + event counts)
- Orchestration: `StepExecutor` aggregates results

### Agent Component Architecture (October 2025)
**Status**: Agent refactor complete with 6 specialized components.

**Component Structure**:
- **Movement**: `AgentMovement` - spatial navigation, pathfinding, collision avoidance
- **Event Emitter**: `AgentEventEmitter` - observer pattern integration, structured logging
- **Inventory**: `AgentInventory` - dual inventory management (carrying + home), mutation-safe
- **Trading Partner**: `TradingPartner` - bilateral exchange coordination, cooldown management
- **Target Selection**: `ResourceTargetStrategy` - deterministic resource/partner targeting
- **Mode State Machine**: `AgentModeStateMachine` - behavioral mode transitions, validation

**Component Integration**: Components initialized in `Agent.__post_init__()` with proper event emitter wiring.

### Observer Event System
**Current Status**: Legacy GUILogger eliminated. Observer pattern is authoritative. ⚠️ **LOGGING PIPELINE COMPLEXITY WARNING** - Current multi-layer compression system is unwieldy (see `tmp_plans/CURRENT/AAA/LOG_ARCHITECTURE_RETHINK.md` for planned simplification).

**Use Observer Events**: Emit via `observability/events.py` (e.g., `AgentModeChangeEvent`, `TradeExecutionEvent`, `DebugLogEvent`)
- Simulation never calls GUI directly
- Agent mode changes: `agent._set_mode(new_mode, reason, observer_registry, step_number)`
- Performance target: <2% logging overhead per step

**Current Architecture**: Use `FileObserver`, `EducationalObserver`, `PerformanceObserver` with `ObserverRegistry` for all logging needs.

**CRITICAL LOGGING CONSTRAINT**: The current `optimized_serializer.py` system (~1500 lines) has a 6-layer transformation pipeline that is complex and fragile. **MAJOR ARCHITECTURAL REWRITE IN ACTIVE IMPLEMENTATION**:

**Legacy Problems Being Eliminated**:
- 6-layer pipeline: `SimulationEvent → Buffer → Dictionary → Optimize → Compress → Semantic → JSON`
- Field transformation hell: `seller_id` → `sid` → `seller_id:1` → `sid:1`
- Multiple serializer classes creating debugging nightmares

**Current Solution Implementation - Raw Data Recording**:
- **Direct storage**: `observer.record_trade(dict)` → Raw dictionary storage → File
- **Zero overhead**: No processing during simulation, only storage
- **On-demand translation**: `DataTranslator` provides human-readable format when needed

**Implementation Status**:
- ✅ **Phase 1-2 Complete**: `RawDataObserver`, `DataTranslator`, `RawDataWriter` with 112 tests
- 🚧 **Phase 3+ Active**: Replacing event objects with raw dictionary recording in simulation handlers
- 🎯 **Target Architecture**: Raw dict storage + optional translation (100x performance improvement)

### Launcher Architecture
**Primary Interface**: `make launcher` provides comprehensive test management with modular design
- **TestRegistry**: Centralized configuration management for all test scenarios
- **TestExecutor**: Programmatic test execution with subprocess fallback
- **LauncherLogger**: Independent logging system (`launcher_logs/`) separate from simulation logs
- **Modular Tabs**: Gallery, comparison, history, batch runner, and config editor components
- **Status Monitoring**: Real-time health checks with actionable error reporting

**Key Launcher Files**:
- `tools/launcher/app_window.py` - Main launcher GUI with tabbed interface
- `tools/launcher/registry.py` - Configuration and test discovery system
- `tools/launcher/executor.py` - Test execution engine with error handling
- `tools/launcher/framework/` - Debug orchestration and comprehensive logging setup

### Performance & Testing
**Complexity**: Maintain O(n) per-step performance. O(nlogn) is acceptable *if absolutely necessary*. No quadratic partner scans or large per-frame allocations.

**Baselines**: 
- Determinism: `baselines/determinism_hashes.json` - only refresh with rationale
- Performance: `baselines/performance_baseline.json` - compare after algorithm changes

**Hash invariant**: Excludes trade & debug metrics. Behavioral changes require: (1) focused test, (2) baseline refresh with commit message explaining WHAT + WHY.

**⚠️ REFACTOR CONTEXT**: During comprehensive refactor, baseline changes may be more frequent. Always document rationale and get user approval for changes that affect core determinism or performance characteristics.

**Test Structure**: Use `tests/conftest.py` fixtures - `clear_trade_flags` and `reset_forage_flag` ensure clean test isolation. All tests use factory construction pattern via `SimConfig`.

**Performance Validation Workflow**:
```bash
pytest -q                    # Run full test suite (436+ tests)
make perf                    # Compare performance against baselines  
make baseline-capture        # Capture new baselines (requires justification)
```

**Test Organization**:
- `tests/unit/` - Component-level tests with determinism validation
- `tests/integration/` - Cross-component behavior verification
- `tests/performance/` - Baseline capture and regression detection
- `MANUAL_TESTS/` - Interactive GUI scenarios for launcher testing

### Feature Flags (Active)
**Core Behavior**:
- `ECONSIM_FORAGE_ENABLED` - agent foraging behavior
- `ECONSIM_TRADE_DRAFT` - enumerate trade intents (no execution)  
- `ECONSIM_TRADE_EXEC` - execute up to one trade per step
- `ECONSIM_NEW_GUI` - enhanced GUI vs legacy bootstrap (default: 1)

**Debugging**:
- `ECONSIM_DEBUG_AGENT_MODES` - mode transition logging
- `ECONSIM_DEBUG_FPS` - FPS debugging output
- `ECONSIM_LOG_LEVEL` - DEBUG/INFO/EVENTS/QUIET logging level
- `ECONSIM_LOG_FORMAT` - STRUCTURED/COMPACT log format
- `ECONSIM_LOG_CATEGORIES` - filter event categories (ALL, PAIRING, etc.)
- `ECONSIM_LOG_EXPLANATIONS` - educational explanations in logs
- `ECONSIM_LOG_DECISION_REASONING` - detailed decision logic logging

**Performance**:
- `ECONSIM_HEADLESS_RENDER` - skip rendering for CI/testing
- `ECONSIM_LEGACY_ANIM_BG` - restore animated background (default: static)
- `ECONSIM_LAUNCHER_SUPPRESS_LOGS` - disable launcher file logging

### Project Dependencies & Environment
**Core Stack**: Python 3.11+, PyQt6 (GUI), Pygame (rendering), NumPy (math). Development tools: pytest, black, ruff, mypy.

**Virtual Environment**: Always use `make venv && source vmt-dev/bin/activate` for consistent development environment. Project uses `pyproject.toml` with `setuptools>=68`.

### Current Refactoring Status
**UNIFIED REFACTOR COMPLETE** (Oct 2025): Major architectural modernization achieved ✅
- **GUILogger elimination complete** - Legacy 2593-line monolith removed, observer pattern established
- **Step decomposition complete** - `Simulation.step()` decomposed from 450+ lines to 70-line orchestration via handler system
- **Agent component refactor complete** - Agent class modularized into 6 specialized components (972→831 lines)
- **Observer system operational** - Event-driven architecture eliminates simulation→GUI coupling
- **Launcher architecture modern** - `make launcher` is canonical development interface with modular design
- **Technical debt reduced 85%** - From 289 legacy references to ~15 minor launcher framework cleanup items

### ⚠️ ACTIVE IMPLEMENTATION: Raw Data Recording Architecture Rewrite
**STATUS**: Major logging system rewrite in active implementation (Oct 2025)
**SOLUTION**: Zero-overhead raw dictionary storage with on-demand translation

**Implementation Progress**:
- ✅ **Phase 1-2 COMPLETE**: Core architecture implemented (112 tests passing)
  - ✅ `RawDataObserver` - Zero-overhead storage with `record_*()` methods
  - ✅ `DataTranslator` - Human-readable translation layer  
  - ✅ `RawDataWriter` - Disk persistence with compression
  - ✅ All 7 observers migrated to raw data architecture
- 🚧 **Phase 3+ ACTIVE**: Simulation handler migration in progress
  - 🚧 Replace `Event.create()` calls with `observer.record_*()` calls
  - 🚧 Update trading, mode change, resource collection handlers
  - 🚧 Migrate debug logging and performance monitoring

**Current Implementation Priorities**:
1. **Handler Migration** - Replace event objects with raw dict recording
2. **GUI Integration** - Real-time translation for display components  
3. **Legacy Cleanup** - Remove ~3500 lines of complex serialization code
4. **Performance Validation** - Achieve <0.1% overhead target (100x improvement)

### Common Pitfalls
- Resorting agents mid-step (breaks determinism)
- Iterating unsorted resource containers  
- Multiple trade executions per step
- Hidden RNG draws in new code
- Per-frame heavy allocations
- Direct GUI calls from simulation
- Raw agent mode assignments (use `_set_mode`)

**⚠️ REFACTOR EXCEPTION**: During comprehensive refactor, these "pitfalls" may become intentional changes if they improve the architecture. Always propose such changes to the user with clear rationale before implementing.

### Key Files for Understanding
- `simulation/world.py` - Main orchestration (70-line step method)
- `simulation/execution/step_executor.py` - Handler pipeline coordinator
- `simulation/execution/handlers/` - Step-specific logic (Movement, Collection, Trading, Metrics, Respawn)
- `simulation/agent.py` - Modular agent with 6 component architecture
- `simulation/components/` - Agent component implementations (Movement, EventEmitter, Inventory, TradingPartner, TargetSelection, ModeStateMachine)
- `observability/events.py` - Event types for observer pattern
- `observability/serializers/optimized_serializer.py` - ⚠️ Complex 1500-line pipeline (needs refactoring)
- `tools/launcher/` - Canonical development interface architecture
- `baselines/` - Determinism & performance references
- `llm_counter/` - Token usage analysis for LLM context optimization
- `tmp_plans/CURRENT/AAA/LOG_ARCHITECTURE_RETHINK.md` - Planned logging system simplification

### Token Usage Analysis
**Unique Feature**: This project includes `llm_counter/` for analyzing LLM token consumption. Use `make token` to generate reports on codebase size for AI context optimization.
- Reports generated in `llm_counter/vmt_token_report_*.md` with comprehensive analysis
- Tracks token usage patterns for efficient LLM context management
- Essential for large codebases to understand AI assistant limitations

### Pre-commit Checklist
1. All tests pass (`pytest -q`)
2. Performance within baseline (`make perf`)  
3. Determinism invariants unchanged (or explicit test + baseline update)
4. New metrics hash-excluded unless justified
5. Mode transitions emit proper events
6. No new non-deterministic iteration sources

**Commit format**: `component: concise change (perf/determinism impact, hash stable|updated)`

### Key Files for Understanding
- `simulation/world.py` - Main orchestration (70-line step method)
- `simulation/execution/step_executor.py` - Handler pipeline coordinator
- `simulation/execution/handlers/` - Step-specific logic (Movement, Collection, Trading, Metrics, Respawn)
- `simulation/agent.py` - Modular agent with 6 component architecture
- `simulation/components/` - Agent component implementations (Movement, EventEmitter, Inventory, TradingPartner, TargetSelection, ModeStateMachine)
- `observability/events.py` - Event types for observer pattern
- `observability/serializers/optimized_serializer.py` - ⚠️ Complex 1500-line pipeline (needs refactoring)
- `tools/launcher/` - Canonical development interface architecture
- `baselines/` - Determinism & performance references
- `llm_counter/` - Token usage analysis for LLM context optimization
- `tmp_plans/CURRENT/AAA/LOG_ARCHITECTURE_RETHINK.md` - Planned logging system simplification

### Token Usage Analysis
**Unique Feature**: This project includes `llm_counter/` for analyzing LLM token consumption. Use `make token` to generate reports on codebase size for AI context optimization.
- Reports generated in `llm_counter/vmt_token_report_*.md` with comprehensive analysis
- Tracks token usage patterns for efficient LLM context management
- Essential for large codebases to understand AI assistant limitations