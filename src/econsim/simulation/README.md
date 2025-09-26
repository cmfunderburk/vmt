# Simulation Core (`econsim.simulation`)

Deterministic environment and agent orchestration layer. Responsible for advancing world state one tick at a time under strict performance and ordering constraints.

## Design Constraints
- Per-step complexity: O(agents + resources).
- Determinism invariants: ordered agent iteration, stable resource ordering (`Grid.iter_resources_sorted` / `serialize()`), tie-breaking for target selection, separated RNG streams.
- Single-threaded; called from GUI QTimer or manual stepping via controller.

## File Inventory
### `config.py`
Defines `SimConfig` dataclass (seed, grid size, perception radius, respawn parameters, preference selection, metrics enable flag, viewport size). Used by factories / tests to standardize simulation construction.

### `constants.py`
Holds immutable tunable constants (e.g., `EPSILON_UTILITY`, default perception radius). Alter only with determinism test updates.

### `agent.py`
Defines `Agent` class and supporting enums.
- Attributes: id, position (x,y), mode (`AgentMode`), carrying inventory, home inventory (wealth), preference, target, home coordinates.
- Key methods:
  - `step_decision(grid)`: Decision-mode step (select/move/deposit/collect) returning whether a collection occurred.
  - `move_random(grid, rng)`: Legacy random walk.
  - `maybe_deposit()`: Transfer carrying goods to home inventory at home.
  - `withdraw_all()`: Move all home inventory into carrying (for trading).
  - `at_home()`, `distance_to(x,y)` helpers.
  - Target selection / movement helpers (compute ΔU, pursue target). Tie-breaking uses (-ΔU, distance, x, y).
- `AgentMode` enum: FORAGE, RETURN_HOME, IDLE, TRADE (potential extension), etc.

### `grid.py`
Grid model storing resources.
- Represents a 2D discrete lattice with resources as list/sets of tuples (x,y,type).
- Core methods:
  - `iter_resources()` / sorted variant: Deterministic iteration.
  - `consume(x,y)`: Remove resource at cell.
  - `place(x,y,type)`: Add new resource.
  - `resource_count()` and `serialize()` for metrics/hash.
  - Bounds checking utilities.

### `world.py`
`Simulation` dataclass orchestrating full step pipeline.
- Fields: grid, agents list, internal step counter, config, internal RNG, respawn scheduler, metrics collector, trade intents, last trade highlight.
- `step(rng, use_decision)`: Core per-tick logic:
  1. Decision or legacy movement / foraging.
  2. Optional bilateral exchange intent enumeration + single execution.
  3. Metrics & respawn hooks.
  4. Step counter increment (implicitly via metrics structure usage).
- Trade integration: builds co-location index per tick, enumerates intents, executes one (priority ordering), updates metrics via `MetricsCollector.register_executed_trade`.
- Foraging/trade gating based on environment variables.

### `trade.py`
Bilateral trade primitives.
- `TradeIntent` dataclass: seller_id, buyer_id, give_type, take_type, quantity, delta_utility, priority tuple.
- `enumerate_intents_for_cell(agents)`: Produce feasible reciprocal single-unit swap intents using preference marginal utility comparisons.
- `execute_single_intent(intents, agents_by_id)`: Deterministically select and apply exactly one intent (if any), adjust inventories, return executed intent.
- Priority ordering must preserve multiset when feature flag `ECONSIM_TRADE_PRIORITY_DELTA` disabled; only reorders when enabled.

### `metrics.py`
`MetricsCollector` capturing aggregate state + advisory trade metrics.
- Records per-step aggregates (agent/resource counts, carrying/home goods totals) and maintains streaming determinism hash (excluding trade & debug metrics).
- Trade metrics: `trade_intents_generated`, `trades_executed`, `trade_ticks`, `no_trade_ticks`, `realized_utility_gain_total`, `fairness_round`, `agent_trade_histories`, `last_executed_trade`.
- `register_executed_trade(...)`: Unified per-trade metric update point (counters + histories) to avoid double counting.
- `record_bilateral_trade(...)`: History-only helper (no counters) invoked by `register_executed_trade`.

### `respawn.py`
Resource respawn scheduler.
- Deterministic placement using secondary RNG seeded from simulation seed + offset.
- Alternating assignment patterns and interval gating: only active when `(step % interval)==0`.
- Methods: `step(grid, rng, step_index)` processes deficit and places new resources up to rate.

### `snapshot.py`
Serialization for persistence / replay.
- Functions to capture and restore simulation state (agents, grid, inventories) while respecting append-only field ordering for hash parity.
- Facilitates regression tests (hash equality across runs) and future save/load UX.

### `agent.py` (covered above) & `__init__.py`
`__init__` exposes convenient imports (e.g., `Simulation`, `Agent`).

## Refactor Targets
- Extract decision movement logic into strategy object for easier testing.
- Normalize trade delta utility computation (currently approximates buyer delta).
- Introduce profiling hooks (timing per phase) behind debug flag.

## Testing Notes
- Determinism test suite relies on stable hash: avoid reordering agents/resources, altering tie-break keys, or changing serialization format without updating reference hashes.
- Performance tests assert overlay rendering under 2% overhead and maintain FPS floor.
