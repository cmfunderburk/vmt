## VMT EconSim – AI Agent Guide (Oct 2025)

**Goal**: Maintain a deterministic educational microeconomics simulation (PyQt6 + Pygame) while safely refactoring legacy systems. Economic coherence > visual consistency. Never add rollback/ghost state to "preserve hashes."

### Architecture Overview
**Core Loop**: PyQt6 QTimer (16ms) → `Simulation.step(ext_rng)` → `StepExecutor` pipeline (Movement → Collection → Trading → Metrics → Respawn) → Pygame blit → Qt paint

**Key Directories**:
- `src/econsim/simulation/` - Core simulation logic & execution pipeline
- `src/econsim/gui/` - PyQt6 GUI with embedded Pygame surface  
- `src/econsim/observability/` - Event system & logging infrastructure
- `src/econsim/tools/launcher/` - Main GUI application entry point

### Development Workflow
```bash
make venv && source vmt-dev/bin/activate  # Create dev environment
make launcher                             # Primary development interface (canonical)
pytest -q                               # Run 210+ tests for validation
make perf                               # Performance comparison vs baselines
make token                              # Generate LLM token usage report
```

**CRITICAL**: `make launcher` is the **canonical user-facing environment**. `make dev` is **outdated** and scheduled for deprecation - its functionality needs migration into the new launcher architecture.

**Development Commands**:
- `make dev` - **DEPRECATED** Enhanced GUI (legacy bootstrap with `ECONSIM_NEW_GUI=0`)
- `make test-unit` - Full test suite alias
- `make lint` - Ruff + Black code quality checks
- `make format` - Auto-format with Black + Ruff

**Headless mode**: `QT_QPA_PLATFORM=offscreen SDL_VIDEODRIVER=dummy make launcher`

### Simulation Construction Pattern
**ALWAYS use factory method** - never direct instantiation:
```python
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
cfg = SimConfig(grid_size=(12,12), seed=123, enable_respawn=True, enable_metrics=True)
sim = Simulation.from_config(cfg, agent_positions=[(0,0)])
```

### Critical Determinism Invariants
1. Resources: iterate only via `Grid.iter_resources_sorted()`
2. Selection tie-breaking: `(-ΔU, distance, x, y)`; trade priority: `(-ΔU, seller_id, buyer_id, give_type, take_type)`
3. Agent order: preserve original list order within each step (no mid-step resorting)
4. RNG separation: external `step(ext_rng)` parameter vs internal `_rng` (no extra draws)
5. Trade execution: maximum one executed trade per step when enabled

### Modular Handler Architecture
**Add new step logic**: Create handlers in `simulation/execution/handlers/` subclassing `BaseStepHandler`. Never expand `Simulation.step()` directly.

Handler pattern:
- Input: `StepContext` (immutable simulation view)
- Output: `StepResult` (metrics + event counts)
- Orchestration: `StepExecutor` aggregates results

### Observer Event System
**Current Status**: Legacy GUILogger eliminated. Observer pattern is authoritative.

**Use Observer Events**: Emit via `observability/events.py` (e.g., `AgentModeChangeEvent`, `TradeExecutionEvent`, `DebugLogEvent`)
- Simulation never calls GUI directly
- Agent mode changes: `agent._set_mode(new_mode, reason, observer_registry, step_number)`
- Performance target: <2% logging overhead per step

**Current Architecture**: Use `FileObserver`, `EducationalObserver`, `PerformanceObserver` with `ObserverRegistry` for all logging needs.

### Performance & Testing
**Complexity**: Maintain O(n) per-step performance. No quadratic partner scans or large per-frame allocations.

**Baselines**: 
- Determinism: `baselines/determinism_hashes.json` - only refresh with rationale
- Performance: `baselines/performance_baseline.json` - compare after algorithm changes
- Canonical: `baselines/CANONICAL_REFACTOR_BASELINE.md` - refactor start point

**Performance Targets**: Mean ≥999.3 steps/sec across 7 educational scenarios. Leontief preferences are 6x slower than sparse scenarios (246.8 vs 1545.7 steps/sec).

**Hash invariant**: Excludes trade & debug metrics. Behavioral changes require: (1) focused test, (2) baseline refresh with commit message explaining WHAT + WHY.

### Feature Flags (Active)
**Core Behavior**:
- `ECONSIM_FORAGE_ENABLED` - agent foraging behavior
- `ECONSIM_TRADE_DRAFT` - enumerate trade intents (no execution)  
- `ECONSIM_TRADE_EXEC` - execute up to one trade per step
- `ECONSIM_NEW_GUI` - enhanced GUI vs legacy bootstrap (default: 1)

**Debugging**:
- `ECONSIM_DEBUG_AGENT_MODES` - mode transition logging
- `ECONSIM_DEBUG_FPS` - FPS debugging output
- `ECONSIM_LOG_LEVEL` - DEBUG/INFO logging level
- `ECONSIM_LOG_FORMAT` - structured vs plain log format
- `ECONSIM_LOG_CATEGORIES` - filter event categories (ALL, PAIRING, etc.)

**Performance**:
- `ECONSIM_HEADLESS_RENDER` - skip rendering for CI/testing
- `ECONSIM_LEGACY_ANIM_BG` - restore animated background (default: static)

### Current Refactoring Status
**Active Cleanup** (as of Oct 2025): GUILogger elimination complete ✅
- Legacy GUILogger and LegacyLoggerAdapter removed
- Observer system infrastructure complete and operational
- GUI panels use observer events exclusively
- Remove any remaining `use_decision=False` parameters and legacy random artifacts

### Common Pitfalls
- Resorting agents mid-step (breaks determinism)
- Iterating unsorted resource containers
- Multiple trade executions per step
- Hidden RNG draws in new code
- Per-frame heavy allocations
- Direct GUI calls from simulation
- Raw agent mode assignments (use `_set_mode`)

### Key Files for Understanding
- `simulation/world.py` - Main orchestration
- `simulation/execution/step_executor.py` - Handler pipeline  
- `simulation/execution/handlers/` - Step-specific logic
- `simulation/agent.py` - Decision & mode system
- `observability/events.py` - Event types
- `baselines/` - Determinism & performance references

### Pre-commit Checklist
1. All tests pass (`pytest -q`)
2. Performance within baseline (`make perf`)  
3. Determinism invariants unchanged (or explicit test + baseline update)
4. New metrics hash-excluded unless justified
5. Mode transitions emit proper events
6. No new non-deterministic iteration sources

**Commit format**: `component: concise change (perf/determinism impact, hash stable|updated)`