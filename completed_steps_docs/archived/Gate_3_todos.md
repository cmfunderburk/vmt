# Gate 3 — Spatial & Agent Foundations (Planning Draft)

Date: 2025-09-22
Prereqs: Gates 1–2 accepted (render loop + preferences stable)

## Goal
Introduce minimal spatial grid and agent scaffolding with a deterministic simulation step separate from rendering, enabling future economic decision behavior without prematurely locking in full optimization mechanics.

## Objectives
1. Grid abstraction (cells, resource placement, lookup/remove) — O(1) average operations.
2. Agent skeleton (position, inventory, reference to Preference, placeholder tick logic).
3. Simulation coordinator (`World`/`Simulation`) orchestrating agent iteration & resource collection.
4. Optional integration with existing render loop (invoke `world.step()` each frame or every N frames) behind a toggle.
5. Maintain performance (≥30 FPS with simulation active, target ~55–60 on baseline machine).
6. Preserve current architectural simplicity (single thread, single event loop, QTimer only).

## Out of Scope (Explicit Deferrals)
- Pathfinding or utility-based movement heuristics.
- Budgets/prices and optimization-based consumption decisions.
- Dynamic resource respawn / regeneration.
- GUI parameter controls or overlays.
- Multi-good expansion (still two goods for consistency with preferences).
- Persistent save/load beyond trivial grid serialization stub.

## Acceptance Criteria
1. `Grid` class: construct with width/height; supports adding resources and querying/removing them (`has_resource(x,y)`, `take_resource(x,y)`).
2. Coordinates validated (no out-of-bounds writes/reads); invalid access raises `ValueError`.
3. Resources stored in a structure supporting O(1) membership (e.g., `set[(int,int)]`).
4. `Agent` class: id, position tuple, inventory dict with keys `good1`,`good2`, `preference` reference.
5. `Agent.move_random(grid, rng)` stays within bounds (4-neighborhood or stay-put); deterministic under seeded RNG.
6. `Agent.collect(grid)` increments inventory if resource present at its cell and removes resource from grid.
7. `Simulation`/`World` class: holds list of agents + grid; `step(rng)` invokes move + collect for each agent exactly once per step.
8. Deterministic stepping test: same seed → identical positions & inventories after N steps.
9. Performance test: with 10 agents and 50 resources, FPS ≥30 (reuse perf harness or new targeted test).
10. Optional widget integration can be disabled (flag or None simulation) without code changes to existing tests.
11. Clean teardown: simulation references released on widget close (no resource leaks, existing shutdown tests still pass).
12. All existing tests (27) remain green; new tests added: grid ops, agent movement bounds, collect mechanics, deterministic simulation, perf guard.
13. Documentation: module docstrings plus this plan + checklist committed before implementation.

## Metrics & Instrumentation
- New perf test extends `test_perf_widget` or adds `test_perf_simulation.py` measuring average FPS over short run with simulation active.
- Optional counters: steps executed (internal attribute) for debugging; kept private (`_steps`).

## Risks & Mitigations
Risk | Mitigation
-----|-----------
Over-engineering simulation loop | Keep single `step()`; no scheduling abstraction yet.
Performance degradation | Use sets & simple lists; avoid per-step allocations in hot path.
Scope creep into economic logic | Guard with deferral list & keep `move_random` placeholder.
Future pathfinding redesign | Encapsulate movement in method so replacement is localized.

## Implementation Phases
Phase | Tasks | Notes
------|-------|------
P1 | Create `simulation/` package, implement `Grid` + tests | Independent of agents
P2 | Implement `Agent` + tests (movement, collect) | Use seeded RNG fixture
P3 | Implement `Simulation` + deterministic step test | Compose grid + agents
P4 | Integrate (optional) into widget behind flag | Default off for existing tests
P5 | Performance test + tuning (if needed) | Adjust movement frequency if borderline
P6 | Docs polish & retrospective prep | Update README phase section

## Test Plan (New Files)
- `tests/unit/test_grid.py`
- `tests/unit/test_agent.py`
- `tests/unit/test_simulation.py`
- `tests/unit/test_perf_simulation.py` (may reuse existing perf harness structure)

## Future Extension Hooks
- Replace `move_random` with preference-weighted target selection.
- Add `Budget`/`PriceSystem` once spatial economic exchanges needed.
- Introduce resource types differentiating goods spatially.

## Go / No-Go Gate Exit Condition
All acceptance criteria satisfied; documented retrospective drafted (Gate 3 Eval) demonstrating stable performance & deterministic simulation.

-- END DRAFT --
