# Copilot Project Instructions (EconSim VMT)

Concise, codebase‑specific rules so AI agents produce safe, deterministic, refactor‑friendly changes.

## Core Principles
1. Simulation is the source of truth; GUI + logging are viewers/playback layers.
2. Determinism first: preserve handler order + stable iteration + isolated RNG.
3. Component & handler architecture over ad‑hoc logic inside `Agent` or `Simulation`.
4. Raw data observability only (no event buffering resurrection).
5. Refactors should reduce technical debt (outdated tests, legacy aliases, dead feature flags) without breaking baselines.

## Runtime / Execution Model
- Single-threaded loop (`Simulation.step()` in `simulation/world.py`). No threads unless a feature flag + determinism validation + docs.
- Handler order (DO NOT REORDER): Movement → Collection → Trading → Metrics → Respawn (see `_initialize_step_executor`).
- Upcoming shift: run-first then playback. Simulation will output a rich artifact (JSONL + metadata) under `sim_runs/` which the GUI replays. Do not re‑couple GUI to live internal objects—shape output for reconstruction instead.

## Near-Term Refactor Targets
- Isolate simulation output writer (extend raw data writer) to emit a reconstructable timeline (steps, agent states, trades, collections, mode changes).
- Prune/modernize outdated early-phase tests (focus on observer primitives + handler sequencing + determinism hash).
- Centralize preference model registration (factory + simple schema) for dynamic inclusion in Custom Tests Generator.
- Prepare abstraction seams for market price formation (future: price discovery handler AFTER Trading, before Metrics—feature-flagged, appended not inserted unless required).

## Preferences Workflow
- All preference implementations in `preferences/` must be pure: no I/O, no mutation outside instance.
- Adding a new preference: implement `marginal_utility` / `utility` interface (see Cobb‑Douglas), export via factory registry, add minimal unit test (utility monotonicity + edge case zero bundle), and update Custom Tests Generator mapping.
- Adjusting parameters for existing scenarios: expose through config object or test fixture; avoid hardcoding in handlers.

## Developer Workflows
- Launch GUI launcher: `make launcher` (primary user path: explore, pick scenario, playback results).
- Run perf baseline: `make perf` (quick) or `make phase0-capture` (full determinism + performance + safeguards) before structural changes.
- Tests: `make test-unit` (avoid sleep/time-based asserts). Keep new tests deterministic by seeding external RNG.
- Lint/Format/Type: `make format && make lint && make type` before commit automation.
- Token / cost audit (LLM support tools): `make token` (keep tooling isolated in `llm_counter/`).

## Extension Patterns
- New per-step logic: create handler in `simulation/execution/handlers/`; append at end unless determinism or dependency requires earlier placement (then update determinism baseline + document rationale at top of handler file).
- New observer event: add `record_*` method to `RawDataObserver` with defaults (primitive fields only), mirror minimal assertion pattern in `tests/test_raw_data_observer.py`.
- Agent capability: add component in `simulation/components/`, wire in `Agent.__post_init__`, keep caches prefixed `_cached_` and invalidated per step.
- Playback pipeline: add writer producing timeline object (index by step) + metadata manifest; reader used by GUI for scrubbing (no back-references into simulation objects).

## Determinism & Performance Guardrails
- No unordered iteration affecting outcome: always sort (use tuple key: (-utility_delta, distance, x, y)).
- All randomness via `context.ext_rng` or `Simulation._rng`; forbid global `random.*` calls.
- Maintain O(agents + resources) per step; spatial structures may cache but must invalidate deterministically.
- If changing target selection or movement heuristics: regenerate baseline (`make phase0-capture`) and update determinism hash fixtures.

## Testing Conventions
- Observer tests: assert small dicts only (no object graphs).
- Writer tests: maintain JSONL, atomic write optional, compression optional; defaults must not break existing readers.
- When adding fields: supply defaults so legacy tests remain green; add one focused new test.
- Prefer parametrized tests for preference variants instead of duplicative files.

## Logging & Output
- Use `observer.record_*` (trade, mode_change, resource_collection, debug_log). No print() in hot path.
- End-of-step flush solely via `ObserverRegistry.flush_step()` (already called in `Simulation.step`). Avoid manual flush except specialized off-cycle observer (justify in docstring).
- Simulation run artifact should be built from accumulated raw events + periodic state snapshots (introduce snapshot cadence configurable in config).

## Common Pitfalls (Avoid)
- Reintroducing live GUI coupling (simulation objects passed directly into widgets).
- Blocking or high-volume I/O inside handlers (batch + defer outside step loop).
- Mutating preference objects after construction.
- Silent handler order changes or implicit insertion mid-sequence.
- Adding side effects to pure utility or preference functions.

## Safe Contribution Checklist
1. Handler order & determinism preserved?
2. New logic isolated (component / handler) with minimal surface area?
3. RNG + ordering constraints respected?
4. Raw observer schema backward compatible (defaults supplied)?
5. Baselines updated if behavior semantics changed?
6. Docs / comments point to key file & rationale for any ordering shift?

## Quick References
- Entry: `econsim/main.py` (feature flag `should_use_new_gui`).
- Core loop: `simulation/world.py`.
- Agent components: `simulation/agent.py` + `simulation/components/`.
- Observability: `observability/raw_data/`, `observability/registry.py`.
- Performance & determinism: `tests/performance/` scripts.
- Preferences: `preferences/` (pure, side‑effect free).

Keep answers concise: cite file paths, avoid duplicate large code excerpts.
