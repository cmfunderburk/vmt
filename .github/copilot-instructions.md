## VMT EconSim – AI Coding Agent Guide (Updated Oct 2025)
Mission: Deterministic educational micro‑economics simulation (PyQt6 + Pygame). Absolute rule: economic coherence > cosmetic determinism. Never add ghost/rollback logic to "preserve hashes." If you change ordering, RNG draws, tie‑breaks, or asymptotic step cost—stop and add/update tests first.

Core flow (single thread): PyQt6 QTimer (≈16ms) → `Simulation.step(ext_rng)` → `StepExecutor` → ordered handlers → Pygame blit → Qt paint. Core code: `src/econsim/simulation/`; GUI + launcher: `src/econsim/gui/`, `src/econsim/tools/launcher/`.

**Primary Development Interface**: `make launcher` (canonical build with enhanced GUI, scenario registry, and optimized logging). Use this over `make dev` for development work.

**CURRENT STATUS (Oct 2025)**: Post-unified refactor cleanup in progress. The unified refactor (Phases 1-4) successfully introduced modern architecture with observer patterns and decomposed step handlers. **Phase 2 COMPLETE**: Monolithic 450-line `Simulation.step()` method decomposed into 5 focused handlers (Movement → Collection → Trading → Metrics → Respawn) executed by `StepExecutor`. Current priority: Phase A legacy cleanup (removing 82+ deprecated flags, parameters, obsolete tests) and planning GUILogger migration to observer pattern. See `tmp_plans/CURRENT/REVIEWS/` for active plans.

**Active Phase A**: Eliminating `ECONSIM_LEGACY_RANDOM` flag system (26 references), legacy mode test scenarios (15+ files), deprecated documentation, and `use_decision=False` parameters (51 calls). These create maintenance overhead and test noise without functional value.

Canonical construction:
```python
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
cfg = SimConfig(grid_size=(12,12), seed=123, enable_respawn=True, enable_metrics=True)
sim = Simulation.from_config(cfg, agent_positions=[(0,0)])
```

Determinism invariants (DO NOT break):
1. Resources only via `Grid.iter_resources_sorted()` / stable serialization
2. Selection tie key `(-ΔU, distance, x, y)`; trade tie key `(-ΔU, seller_id, buyer_id, give_type, take_type)`
3. Preserve original agent list order every step
4. External RNG passed to `step` separate from internal `_rng` (no extra / reordered draws)
5. ≤ 1 trade executed per step when execution enabled

**Step Execution Architecture (Phase 2 complete)**: `Simulation.step()` now orchestrates via `StepExecutor` with handler pipeline: Movement → Collection → Trading → Metrics → Respawn. Each handler inherits `BaseStepHandler`, receives immutable `StepContext`, returns structured `StepResult`. Add new per‑step logic as handlers in `src/econsim/simulation/execution/handlers/`, not back into `Simulation.step()`.

Selection / decision system: Distance‑discounted utility `ΔU' = ΔU / (1 + k*d^2)`; reject non‑positive ΔU early. Complexity must remain O(agents + visible_resources); avoid quadratic partner scans.

Feature flags (env): `ECONSIM_FORAGE_ENABLED=0`, `ECONSIM_TRADE_DRAFT=1`, `ECONSIM_TRADE_EXEC=1`, `ECONSIM_HEADLESS_RENDER=1`, debug: `ECONSIM_DEBUG_AGENT_MODES=1`, `ECONSIM_DEBUG_FPS=1`.

Events & observability: Emit events via `observability/events.py`; never call GUI directly from simulation. Add collection/trade/mode events rather than inline prints. Keep logging overhead <2%.

**CRITICAL REFACTORING PATTERN**: Mode changes MUST use `agent._set_mode(new_mode, reason, observer_registry, step_number)` helper—never direct `agent.mode = ` assignments. This ensures `AgentModeChangeEvent` emission. **ONGOING MIGRATION**: ~80% of direct assignments in `world.py` still need conversion (check before modifying mode-related code).

Performance guardrails: Per‑step O(n). Movement handler budget ≤3ms typical. Avoid new large per‑frame allocations or hidden loops. Run `make perf` after impactful changes.

Hash & schema rules: Dataclasses / snapshot / trade tuples are append‑only. Determinism hash excludes debug & trade metrics; if legitimate behavioral change alters hash, refresh `baselines/determinism_hashes.json` with rationale.

**Development Workflow**: `make venv && source vmt-dev/bin/activate` → `make launcher` (primary dev interface). Full test suite: `pytest -q` (210+ tests). Performance validation: `make perf`. Baseline capture: `make phase0-capture`. Headless GUI: `QT_QPA_PLATFORM=offscreen SDL_VIDEODRIVER=dummy`. Always construct sims with `Simulation.from_config` in tests.

**Interface Hierarchy**: `make launcher` (canonical) > `make manual-tests` (GUI test suite) > `make batch-tests` (sequential runner) > `make bookmarks` (config manager) > `make dev` (legacy). Programmatic access: `from econsim.tools.launcher.test_runner import create_test_runner`. Add scenarios via `TestConfiguration` in `src/econsim/tools/launcher/framework/test_configs.py`.

Safe extension checklist: tests green; perf within baseline; no new unordered iterations; tie keys unchanged; RNG draw count stable; new metrics either excluded from hash or baseline updated; events (not silent state mutation) for new mode changes; economic coherence preserved.

Common pitfalls: resorting agents mid‑step; iterating unsorted resource containers; multiple trades per step; silent RNG draws; quadratic partner scans; per‑frame big object creation; modifying inventories from rendering/observer code; adding parity hacks that undo real trades; direct `agent.mode = ` assignments (use `_set_mode()` helper instead).

Where to look first: `simulation/world.py` (step orchestration, ~70 lines), `simulation/execution/step_executor.py` (handler coordination), `simulation/execution/handlers/` (5 focused handlers), `simulation/agent.py` (decision logic), `simulation/grid.py` (spatial indexing), `observability/events.py` (event system), `simulation/trade.py` (bilateral exchange), `metrics.py` (determinism hashing), `tools/launcher/` (primary dev interface).

When unsure: add a focused determinism or perf test instead of speculative refactor. Commit messages: concise WHAT + WHY (e.g. `selection: prune zero ΔU early (perf +1.2%, hash stable)`).

**Development Environment Setup**:
```bash
make venv && source vmt-dev/bin/activate  # Essential first step
make launcher                             # Primary development interface
ECONSIM_DEBUG_AGENT_MODES=1 make launcher # Debug mode transitions
```

**Core Architecture Boundaries**:
- Simulation Core: `src/econsim/simulation/` (deterministic step execution)
- Step Pipeline: `src/econsim/simulation/execution/` (Movement → Collection → Trading → Metrics → Respawn)
- Event System: `src/econsim/observability/` (NO direct GUI calls from simulation)
- Launcher Framework: `src/econsim/tools/launcher/` (enhanced GUI + scenario registry)
- Configuration Registry: Use `TestConfiguration` dataclass pattern, not scattered manual setup

**Legacy System Cleanup (Oct 2025)**: `ECONSIM_LEGACY_RANDOM` flag deprecated and ignored—decision system is always enabled. Remove any `use_decision=False` parameters and legacy flag references. When modifying mode-related code, check for direct assignments and convert to `_set_mode()` helper pattern with proper `observer_registry` and `step_number` parameters.

**Active Legacy Deprecation (Phase A)**: Currently executing systematic removal of 82+ low-risk legacy references across 4 component categories:

**Component 1 - ECONSIM_LEGACY_RANDOM Flag System**: 26 references across files
- 16 test files setting `ECONSIM_LEGACY_RANDOM=1`
- 51 uses of `use_decision=False` parameter calls
- GUI components: `embedded_pygame.py`, `main_window.py` references
- Status: Flag processed but ignored, warnings emitted, decision system always enabled

**Component 2 - Legacy Mode Test Scenarios**: 15+ test files
- Legacy determinism hash validation (marked xfail)
- Legacy mode test scenarios using deprecated flags
- Manual test placeholders with example templates
- Performance tests comparing legacy vs. new systems

**Component 3 - Documentation References**: README.md, Makefile, developer guides
- Makefile comments referencing legacy random movement
- README.md sections with obsolete flag instructions
- AI coding instructions with outdated patterns

**Component 4 - Legacy Parameters**: Function signatures, handler configurations
- 51 `use_decision=False` calls that default to True
- Legacy configuration parameters in test setups
- Deprecated feature toggles in configuration classes

**Phase A Implementation Pattern**:
1. **Days 1-2**: Automated detection and cataloging (inventory all components)
2. **Days 3-4**: Cleanup tool development (flag removal, test cleanup, docs updater)
3. **Days 5-7**: Component-by-component removal (flags → docs → tests → parameters)
4. **Days 8-10**: Validation and testing (functional, documentation, integration)

**When encountering legacy patterns**:
1. **Flag processing**: Remove `ECONSIM_LEGACY_RANDOM` environment variable checks entirely
2. **Parameter calls**: Change `sim.step(rng, use_decision=False)` → `sim.step(rng)`
3. **Function signatures**: Remove `use_decision` parameter from method definitions
4. **Test configurations**: Remove `os.environ["ECONSIM_LEGACY_RANDOM"] = "1"`
5. **Documentation**: Remove legacy flag references from README/Makefile comments
6. **xfail tests**: Remove xfail markers for legacy determinism tests

**Success Criteria**: Zero legacy flags, clean parameters, updated docs, test stability, no deprecation warnings.

**Development Environment Setup**:
```bash
make venv && source vmt-dev/bin/activate  # Essential first step
make launcher                             # Primary development interface
ECONSIM_DEBUG_AGENT_MODES=1 make launcher # Debug mode transitions
```

**Core Architecture Boundaries**:
- Simulation Core: `src/econsim/simulation/` (deterministic step execution)
- Step Pipeline: `src/econsim/simulation/execution/` (Movement → Collection → Trading → Metrics → Respawn)
- Event System: `src/econsim/observability/` (NO direct GUI calls from simulation)
- Launcher Framework: `src/econsim/tools/launcher/` (enhanced GUI + scenario registry)
- Configuration Registry: Use `TestConfiguration` dataclass pattern, not scattered manual setup

Performance note: Legacy compatibility layers currently cause ~65% regression. Removing them is high priority for Phase C.