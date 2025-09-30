## VMT EconSim AI Coding Agent Instructions
**VMT**: Educational microeconomic simulation platform with deterministic spatial agents, PyQt6/Pygame rendering, and feature-gated bilateral exchange system.

**Critical Goal**: Maintain determinism, ~60-62 FPS performance, and educational clarity. If changes affect ordering, hashing, or per-step complexity, STOP and add/adjust tests first.

## Architecture Overview
- **Single-threaded**: PyQt6 `QTimer(16ms)` drives simulation → rendering pipeline
- **Deterministic**: Ordered iteration, stable tie-breaking, separated RNG streams  
- **Educational**: Feature flags gate foraging, trading, visualization for teaching flexibility
- **Factory Pattern**: `SimConfig` + `Simulation.from_config()` for reproducible builds

## 1. Core Development Workflows

**Primary Interface**: `make launcher` (Enhanced TestRunner with PyQt6 GUI)
```bash
make venv && source vmt-dev/bin/activate  # Setup
make launcher      # Primary development (7 educational scenarios)
make dev          # Fallback basic GUI  
pytest -q         # Full test suite (210+ tests)
make perf         # Performance validation
```

**Factory Construction Pattern** (preferred):
```python
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation

cfg = SimConfig(
    grid_size=(12,12), seed=123, enable_respawn=True, enable_metrics=True,
    distance_scaling_factor=1.5,  # k=0.0 for no distance penalty
    initial_resources=[(2,2,'A'), (4,5,'B')]
)
sim = Simulation.from_config(cfg, agent_positions=[(0,0)])
```

## 2. Immutable Frame Pipeline
`QTimer(16ms)` → `Simulation.step(ext_rng, use_decision)` → `EmbeddedPygameWidget._update_scene()` → `paintEvent()`. No extra timers/threads/sleeps. Never recreate the single Pygame surface; no per‑pixel Python loops.

## 3. Determinism Invariants (DO NOT VIOLATE)
1. Resource iteration only via `Grid.iter_resources_sorted()`.
2. Tie-breaks: resources / selection `(-ΔU, distance, x, y)`; trades `(-ΔU, seller_id, buyer_id, give_type, take_type)` (priority flag may reorder ONLY, not alter multiset).
3. Agent list order is priority; never mutate or sort in-place mid step.
4. RNG separation: external `ext_rng` passed into `Simulation.step` vs internal `Simulation._rng` (respawn, home placement). Do not change call counts.
5. One executed trade max per step when execution flag enabled.

## 4. Core Edit Surface (no ad‑hoc clones)
`simulation/world.py`, `simulation/agent.py`, `simulation/grid.py`, `simulation/trade.py`, `simulation/config.py`, `simulation/metrics.py`, `simulation/respawn.py`, `simulation/snapshot.py`, `preferences/factory.py`, `gui/embedded_pygame.py`, `gui/simulation_controller.py`, launcher under `tools/launcher/`. Extend here; keep schema append‑only.

## 5. Unified Selection Algorithm
Distance‑discounted utility: ΔU' = ΔU / (1 + k·d²). Ranks resource pickups vs (flagged) trade intents in O(agents + visible resources). Use existing spatial index; never introduce quadratic scans. Filter out non‑positive base ΔU early. Preserve tie‑break key ordering.

## 6. Feature / Teaching Flags
- **Movement**: `ECONSIM_LEGACY_RANDOM=1` (disable decision system, use random walk)
- **Foraging**: `ECONSIM_FORAGE_ENABLED=0` (disable resource collection)  
- **Trading**: `ECONSIM_TRADE_DRAFT=1` (enumerate intents), `ECONSIM_TRADE_EXEC=1` (execute ≤1 intent)
- **Debug**: `ECONSIM_DEBUG_AGENT_MODES=1` (mode logs), `ECONSIM_DEBUG_FPS=1` (show FPS)
- **Testing**: `ECONSIM_HEADLESS_RENDER=1` (skip drawing for CI)
- **Idle semantics**: When both foraging & trading disabled (no auto‑deposit)

## 7. Structured Debug Logging
Use builders in `gui/debug_logger.py`; never raw print. Flags: `ECONSIM_LOG_LEVEL`, `ECONSIM_LOG_FORMAT`, `ECONSIM_LOG_CATEGORIES`, `ECONSIM_LOG_EXPLANATIONS=1`, `ECONSIM_LOG_DECISION_REASONING=1`.

## 8. Performance Guardrails
Per step O(n) (n = agents + resources). Overlay & logging overhead <2%. Avoid per‑frame allocations (reuse surfaces, fonts). Maintain FPS floor ≥30 (CI) / target ~60. Keep intent enumeration linear in co‑located agents.

## 9. Metrics & Hash
Determinism hash excludes trade/debug metrics. Adding a metric? Either exclude from hash or update reference expectations + tests. Do not mutate inventories in hash-neutral debug modes unless flag explicitly set.

## 10. Schema & Serialization Rules
Append-only fields in snapshots, agent/grid/world dataclasses, trade intent tuples. Never reorder or remove existing fields/keys. New overlays must be state‑neutral (pure view). Any added flag requires doc update + test if it changes behavior.

## 11. Common Pitfalls (AVOID)
Unsorted resource scans; re-sorting agents; extra RNG draws; modifying tie-break tuple shape; quadratic partner searches; blocking sleeps; allocating large objects in render loop; multi-trade execution per step; modifying carried/home inventories in view code.

## 12. Minimal Deterministic Factory Example
```python
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
cfg = SimConfig(grid_size=(12,12), seed=123, distance_scaling_factor=1.5, enable_respawn=True, enable_metrics=True)
sim = Simulation.from_config(cfg, agent_positions=[(0,0)])
```

## 13. Safe Extension Checklist
1. Tests: `pytest -q` all green. 2. Perf: `make perf` within FPS expectations. 3. No unordered iteration added. 4. Tie-break & ordering untouched (or tests updated). 5. Metrics hash unaffected (or expectations updated). 6. Docs + this file updated for any new flag/param. 7. Logging uses structured system.

## 14. Commit Message Pattern
Imperative WHAT + WHY (+ optional PERF/DET). Example: `agent: cache distance map cutting selection O(n)→O(1) (hash stable)`.

## 15. TestRunner Framework Architecture
Modern launcher under `src/econsim/tools/launcher/` replaces subprocess-based testing. Key components: `TestRegistry` loads from `framework/test_configs.py` (7 educational scenarios), `TestRunner` provides programmatic test execution, `app_window.py` is the main GUI. Pattern: `TestConfiguration` dataclass → `SimulationFactory.create()` → GUI test window. Add tests via config registry, not hardcoded file mappings.

## 16. Educational Test Structure
All 7 tests follow `StandardPhaseTest` pattern: config-driven setup → 6 educational phases (Observation, Resource Competition, etc.) → GUI controls for respawn/trade features. Test files in `MANUAL_TESTS/` are thin wrappers; business logic in framework. Never bypass the config registry for new educational content.

## 17. Test Patterns & Environment Setup
**Headless Testing**: Always set `os.environ["QT_QPA_PLATFORM"] = "offscreen"` and `os.environ["SDL_VIDEODRIVER"] = "dummy"` for PyQt6/Pygame tests. Use `QApplication.instance() or QApplication([])` pattern.

**SimConfig Factory Pattern**: Use `SimConfig` + `Simulation.from_config()` for all test construction. Standard pattern:
```python
cfg = SimConfig(grid_size=(10,10), seed=123, enable_respawn=True, enable_metrics=True)
sim = Simulation.from_config(cfg, agent_positions=[(0,0)])
ext_rng = random.Random(999)
sim.step(ext_rng, use_decision=True)
```

**Fixture Isolation**: Use `@pytest.fixture(autouse=True)` in `tests/conftest.py` to clear trade/forage flags between tests. All environment flags must be reset or tests will interfere. Critical flags: `ECONSIM_TRADE_*`, `ECONSIM_FORAGE_ENABLED`.

**Mock Patterns**: For launcher tests, mock PyQt6 availability with `patch('src.econsim.tools.launcher.test_runner._qt_available', True)`. Use `TestConfiguration` mocks with proper `.id`, `.name` attributes.

**Widget Testing**: For EmbeddedPygameWidget tests, use module-scoped QApplication fixtures. Process events with timeouts and verify frame advancement: `getattr(widget, "_frame", 0) > 0`.

## 18. Programmatic API Patterns
**TestRunner Integration**: Prefer programmatic execution over subprocess launching:
```python
from econsim.tools.launcher.test_runner import create_test_runner
runner = create_test_runner()  # ~0.004s initialization
runner.run_by_id(1, "framework")  # Direct framework instantiation
status = runner.get_status()  # Monitor health and availability
health = runner.get_health_check()  # Comprehensive diagnostics
```

**TestConfiguration Registry**: Use config registry instead of hardcoded file mappings:
```python
from econsim.tools.launcher.framework.test_configs import ALL_TEST_CONFIGS
config = ALL_TEST_CONFIGS.get(test_id)  # Type-safe configuration lookup
```

**Structured Logging**: Use dedicated launcher logging system in `launcher_logs/` separate from simulation logs. Never use raw `print()` - use builders from `gui/debug_logger.py` or launcher logger.

**Development Dependencies**: Requires Python >=3.11, PyQt6 >=6.5.0, pygame >=2.5.0, numpy >=1.24.0. Use `make venv` for canonical environment setup with all dev dependencies.

## 19. Token Management & Performance
**LLM Token Counter**: Use `make token` to generate comprehensive token analysis reports. Output in `llm_counter/vmt_token_report.md` tracks codebase size and complexity for LLM context optimization.

**Performance Monitoring**: Use `make perf` for synthetic benchmarks. Widget performance testing with `--mode widget --duration 3 --json` for JSON output. Maintain FPS ≥60 target, ≥30 floor.

## 20. When Unsure
Add / extend a determinism or perf test instead of guessing. If change spans decision + trade layers, isolate in one commit with explicit rationale. For launcher changes, validate with `pytest tests/unit/launcher/`.

Expand via `README.md`, `src/econsim/simulation/README.md`, `docs/launcher_architecture.md`, and the config registry for deeper context.

**Exception: Widget Testing Patterns**
For PyQt6/Pygame integration tests, use these patterns:
- Headless setup: `os.environ["QT_QPA_PLATFORM"] = "offscreen"` + `os.environ["SDL_VIDEODRIVER"] = "dummy"`
- QApplication reuse: `app = QApplication.instance() or QApplication([])` 
- Frame verification: `getattr(widget, "_frame", 0) > 0` for animation progress
- Event processing: `app.processEvents()` + small sleeps for timer advancement
- Widget lifecycle: Always call `widget.close()` and `app.processEvents()` for cleanup