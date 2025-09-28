# REFACTOR TARGET STEPS

## Goal Snapshot
- Make unified target selection the default agent decision path by implementing `Agent.select_unified_target` with distance-discounted utility (`ΔU_base / (1 + k·distance²)`), deterministic tiebreaks, and profitability filtering.
- Introduce an O(n) spatial index (`AgentSpatialGrid`) rebuilt each step so partner lookups stay linear-time and deterministic.
- Maintain commitment semantics (`current_task`) so agents stay focused on their chosen target until completion or invalidation, while preserving bilateral exchange stagnation safeguards.
- Expose distance scaling constant `k` (0–10, default configurable in GUI + `SimConfig`) with live updates and immediate impact on decision logic.
- Update determinism, behavior, and spatial index tests/hashes to reflect the new selection ordering while protecting existing invariants (single QTimer loop, metrics hash contract, O(agents+resources) complexity).

## Critical Evaluation & Risk Notes
1. **Determinism Pressure Points**
   - Resource + agent iteration order must remain stable; spatial index must preserve insertion ordering when enumerating candidates.
   - Hash updates are unavoidable; need explicit documentation and gated expectation adjustments to avoid mystery regressions.
   - Unified path must respect bilateral cooldown + stagnation behavior to avoid divergent trajectories between `k` values.

2. **Performance Considerations**
   - Spatial index rebuild each step must allocate minimally—prefer dictionary-of-lists with pre-sized list reuse or pooling to avoid frame churn.
   - Distance discount arithmetic adds per-agent overhead; ensure vectorized-style operations stay simple (no Python lambdas in hot loops).
   - Unified path removes the previous “forage first” guard; trading decisions will be evaluated more often—keep heuristics (conservative trade utility estimate, profitable-only filter) cheap.

3. **Behavioral Shifts**
   - Distance scaling default has large effect. Choose a baseline (e.g., `k=1.0`) that produces reasonable agent movement across tutorials; verify educational scenarios still behave.
   - Unified logic must play nicely with forced-deposit/stagnation states. Agents in return-home or forced deposit cycles should skip target selection until reset.

4. **Integration Pitfalls**
   - `Simulation.step` currently has several branches; replacing them demands careful sequencing so external RNG path and legacy random mode stay untouched.
   - Trading-only path still relies on `_handle_bilateral_exchange_movement` for meeting point logic. Decide how much of that survives vs. migrates into unified commitment. The plan assumes keeping bilateral movement for now; ensure API boundaries are clean.
   - GUI update for `k` must synchronize with running simulation via controller signal without blocking the render loop.

5. **Testing Scope**
   - Determinism hashes, decision precedence tests, respawn determinism, and snapshot round-trips must all be refreshed. Budget time for rewriting fixtures.
   - Need new coverage for spatial index (equivalence vs direct scan) and for `k` parameter extremes (0 and 10) in foraging-only and trading-only modes.

## Implementation Plan (Sequential)

### Phase 0 – Baseline Capture & Guardrails
- [ ] Record current determinism hashes + behavior snapshots for main scenarios (`make test`, targeted determinism tests) to reference during migration notes.
- [ ] Confirm GUI controller surfaces for new config knobs (`SimulationController`, panel models) and note where live updates hook into `SimConfig`.
- [ ] Identify all tests asserting the old tie-break ordering (search for `-delta_u`/`select_target`).

### Phase 1 – Core Data Structures & Constants
- [ ] Add `distance_scaling_factor` default constant to `simulation/constants.py` (value 1.0 unless product requirements diverge).
- [ ] Extend `SimConfig` (plus serialization & snapshot schema) to include the new float field with validation (0 ≤ k ≤ 10) and ensure append-only ordering.
- [ ] Create `AgentSpatialGrid` (likely `simulation/spatial.py`) implementing:
  * `add_agent(x, y, agent)` preserving agent order.
  * `iter_within_radius(x, y, radius)` returning agents sorted by deterministic key (distance then id).
- [ ] Wire `Simulation.from_config` to pass `k` to the simulation/agents as needed.

### Phase 2 – Agent API Evolution
- [ ] Introduce `Agent.current_task` / metadata (target type, target id/coords, discovery step, optional timeout counters).
- [ ] Implement `Agent.select_unified_target(grid, candidates, *, distance_scale, enable_foraging, enable_trade)` returning a structured task.
  * Compute `ΔU_base` for resources and conservative trade heuristics.
  * Filter to positive base gain before discounting.
  * Apply distance discount and deterministic tie-break (resources by `(x, y)`, partners by `partner_id`).
- [ ] Update `Agent.step_decision` (and helpers) to honor `current_task`: pursue target, re-evaluate on invalidation, respect forced deposit states.
- [ ] Ensure trade-specific movement hooks can recognize when unified logic targets a partner (handoff to existing pairing/movement pipeline as needed).

### Phase 3 – Simulation Loop Integration
- [ ] Refactor `Simulation.step` decision branch to:
  * Build `AgentSpatialGrid` once per step (under decision mode).
  * Iterate agents in stable order running unified selection (skip if forced deposit, stagnation, or legacy random path).
  * Maintain compatibility with `forage_enabled`, `trade_enabled`, unified selection feature flags (`ECONSIM_UNIFIED_SELECTION_*`).
- [ ] Ensure external RNG legacy path remains untouched.
- [ ] Reconcile bilateral movement invocation—unified tasks targeting partners should trigger pairing without double-handling.
- [ ] Maintain `foraged_ids` equivalents if still needed for metrics or gating; otherwise document removal.

### Phase 4 – GUI & Config Plumbing
- [ ] Add `k` control to right-panel GUI (text input or slider) with validation + immediate emission to controller.
- [ ] Update controller to push new value into active simulation (setter or config update) without restarting.
- [ ] Reflect new parameter in Start Menu advanced configuration + scenario serialization (if applicable).

### Phase 5 – Tests & Determinism Updates
- [ ] Refresh determinism tests with new hashes (document rationale in test comments + changelog).
- [ ] Add new unit tests:
  * `tests/unit/test_agent_unified_selection.py` (resource vs trade tie-breaking, profitability filter, `k` extremes).
  * Spatial index determinism/equivalence tests.
  * Trade commitment timeout scenario ensuring agents abandon stale partners.
- [ ] Update snapshot serialization tests for additional config field.
- [ ] Ensure GUI tests (if any) cover `k` control input validation.

### Phase 6 – Documentation & Verification
- [ ] Update `.github/copilot-instructions.md`, `API_GUIDE.md`, and related docs to reflect unified selection as default.
- [ ] Add changelog entry summarizing behavior change + migration guidance for hashes.
- [ ] Run full quality gates: `make test lint type perf`; capture before/after FPS comparison.
- [ ] Deliver summary with regression notes and recommended scenario replays for stakeholders.

## Validation Checklist (Post-Implementation)
- [ ] Determinism: All updated tests green; documented hash deltas.
- [ ] Behavior: Manual spot-check `k=0`, `k=1`, `k=10` across foraging-only, trade-only, combined modes.
- [ ] Performance: `make perf` shows ≥30 FPS floor, ideally ~62 FPS unchanged.
- [ ] GUI: Adjusting `k` live changes agent routing without restart and stays within bounds.
- [ ] Trading: Unified target selection routes into bilateral exchange correctly, respects cooldown/stagnation logic.
