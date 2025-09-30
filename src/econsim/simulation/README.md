# Simulation Core (`econsim.simulation`)

Deterministic environment and agent orchestration layer. Responsible for advancing world state one tick at a time under strict performance and ordering constraints.

## Design Constraints
- Per-step complexity: O(agents + resources).
- Determinism invariants: ordered agent iteration, stable resource ordering (`Grid.iter_resources_sorted` / `serialize()`), tie-breaking for target selection, separated RNG streams.
- Single-threaded; called from GUI QTimer or manual stepping via controller.

## Step Decomposition (Phase 2)
The former monolithic `Simulation.step()` (≈400 lines) has been decomposed into focused handlers executed by a `StepExecutor`:

```
Simulation.step() -> StepContext -> StepExecutor.execute_step()
  Handlers (ordered):
    1. MovementHandler      # movement + foraging + mode transitions
    2. CollectionHandler    # legacy explicit collection + decision diff metrics
    3. TradingHandler       # (when enabled) intent enumeration + optional execution
    4. MetricsHandler       # step timing, spike detection, steps/sec estimate
    5. RespawnHandler       # resource replenishment & density tracking
```

### Components
| Component | Responsibility | Determinism Notes |
|-----------|----------------|-------------------|
| `StepContext` | Immutable per-step inputs (simulation ref, step number, external RNG, feature flags, observer registry) | No side-effects; not hashed |
| `StepExecutor` | Sequentially invokes handlers, aggregates metrics, measures per-handler execution time | Preserves handler ordering; stable iteration |
| `BaseStepHandler` | Timing wrapper + exception isolation | Exceptions are trapped; failure does not alter ordering |

### Metrics & Hash Update Order
Determinism hash (`MetricsCollector.record`) is invoked after all handlers complete but *before* the step counter increments. This preserves the historical interpretation of step numbers in hash payloads (hash includes `step = current_step_number`).

### Transient Cross-Handler State
A few ephemeral attributes on `Simulation` support coordination without mutating shared structures:
- `_transient_foraged_ids`: Set of agent IDs that collected during movement/collection pass (used to gate trade intents). Deleted post-flush each step.
- `pre_step_resource_count`: Snapshot for collection diff metrics.
- `last_step_metrics`: Aggregated handler metrics (debug/testing only, excluded from hash).

### Handler Design Guidelines
- Single responsibility (movement vs collection vs trading, etc.).
- Return only structured metrics (no direct mutation of unrelated subsystems).
- Emit observer events instead of directly updating GUI or logging.
- Avoid quadratic scans: resource & agent pairing limited to localized structures.
- Do not introduce additional RNG draws; always reuse provided external RNG for legacy movement only; internal `_rng` remains reserved for future systems.

### Performance Guardrails
- Per-handler time is captured (`handler_timings` in ms). Movement dominates typical steps; others are sub-millisecond.
- Performance tests now focus on absolute per-tick delta (added overhead ceiling) rather than fragile relative percentages on very small baselines.
- Movement handler average per-step budget: ≤ 3 ms (asserted in perf test). Additional per-tick overhead cap currently 1.5 ms over baseline scenario.

### Trading Determinism
- Intent enumeration ordering must remain stable (co-location index build order + tie-break key).
- Only one trade may execute per step when execution flag enabled.
- Hash-neutral trade mode (if enabled) restores pre-trade inventories to keep determinism hashes stable during exploratory debugging.

### Observer Integration
Current coverage: All mode transitions routed via `AgentModeChangeEvent`. Future events planned:
- `ResourceCollectionEvent`
- `TradeExecutionEvent`
- `AgentMovementEvent`

A helper will centralize remaining direct `agent.mode =` sites to ensure 100% event coverage.

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
`Simulation` dataclass orchestrating full step pipeline via `StepExecutor` and handlers (see decomposition section). Maintains RNG separation, transient step state, observer registry, metrics collector, and optional respawn scheduler.

### `execution/`
Step decomposition framework (context, result, executor, handlers). Each handler file focuses on a single phase of the step.

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

## Testing & Quality Gates
- Determinism: Hash equality tests ensure no ordering or serialization drift. RNG draw count parity test verifies no silent randomness additions.
- Performance: Per-tick delta and movement budget enforced in `test_perf_overhead` (post-decomposition form).
- Handler Metrics: `last_step_metrics['handler_timings']` provides ms timings for quick profiling.
- Observer Coverage: Mode change events validated; future events will expand coverage of collection/trade actions.

## Future Refactor Targets
- Centralize remaining direct `agent.mode` assignments behind an event-emitting helper.
- Introduce dedicated events: collection, trade execution, movement decision.
- Expand metrics handler with rolling variance & optional structured export (without entering hash path).
- Add configuration-driven handler enabling/disabling for educational scenarios.

## Change Log (Phase 2 Highlights)
- Added step execution framework + handlers (movement, collection, trading, metrics, respawn).
- Reintroduced determinism hash update in orchestration after decomposition.
- Added RNG call count parity test.
- Adjusted performance test philosophy (absolute per-tick overhead vs fragile relative % on ultra-fast baselines).
