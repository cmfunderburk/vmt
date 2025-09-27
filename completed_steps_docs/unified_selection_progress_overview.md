# Unified Selection Refactor Progress Overview
Date: 2025-09-26
Scope: Target selection unification (resources + partner trade), spatial indexing, distance-based discount factor (k), Leontief prospecting parity, GUI exposure, baseline validation.

---
## 1. High-Level Summary
We have successfully migrated decision-making to a unified selection pass that evaluates both resource foraging and partner trade opportunities under a single scoring model:

  discounted_score = ΔU_base / (1 + k * distance^2),  k ∈ [0,10], default 0.0.

The system preserves determinism invariants (tie-break ordering, stable resource iteration, separate RNG domains) while introducing a tunable locality emphasis (k). Leontief prospecting fallback was reintroduced inside the unified path to maintain behavioral parity for agents with complementarity preferences when no immediate positive single-resource ΔU exists.

All existing tests pass (210/210) plus new distance scaling monotonic test. No determinism hash drift observed so far (hash tests green). Performance has not yet been re‑benchmarked post‑GUI control addition (expected negligible impact).

---
## 2. Implemented Changes
- Added `distance_scaling_factor` to `SimConfig`, `SimulationSessionDescriptor`, and menu selection pipeline.
- Implemented `AgentSpatialGrid` and integrated O(n) rebuild + localized neighbor retrieval each decision step.
- Added `Agent.select_unified_target` producing scored resource or partner candidates with deterministic tie-breaks:
  - Resource tie-break: (−ΔU, distance, x, y) via upstream candidate ordering
  - Partner tie-break: partner_id within same score bucket
  - Mixed: higher raw ΔU; if equal ΔU then lexical kind ordering
- Introduced conservative bilateral trade delta heuristic (min of directional marginal gains across a feasible one‑unit swap).
- Integrated unified pass `_unified_selection_pass` with reservation sets (resources, partners) and minimal commitment semantics.
- Restored Leontief prospecting fallback inside unified pass (prevents regression when no positive ΔU candidates exist).
- Added live GUI control (Start Menu + Controls panel Decision Params group) for distance scaling factor k.
- Added new test suite file `test_unified_selection.py` (resource, partner, determinism) and `test_distance_scaling_factor.py` (monotonic discount assertion).
- Adjusted partner pairing test to accept immediate trade completion (balanced inventories) as success.
- Updated CHANGELOG (Unreleased) documenting distance scaling factor and Leontief fallback inclusion.

---
## 3. Determinism & Testing Status
- Full test suite: 210 passing.
- Determinism hash tests green (no schema drift; resource iteration order unchanged; added logic only consults config + deterministically sorted neighbor lists).
- New monotonic discount test validates functional impact of k without relying on brittle resource/partner switching assumptions.
- No snapshot/schema changes beyond append-only `SimConfig.distance_scaling_factor` (already present earlier in refactor steps).

---
## 4. GUI Integration
- Start Menu: numeric input (QDoubleSpinBox) for initial k.
- Controls Panel: live-adjustable k (Decision Params group) updating `simulation.config.distance_scaling_factor` in place (read each step by unified selection path).
- Tooltips clarify formula and educational effect.

---
## 5. Outstanding / Immediate Next Steps (Priority Ordered)
1. Performance Validation:
   - Run perf harness (`scripts/perf_stub.py`) with k=0 and a mid value (e.g., k=3) to confirm no FPS regression (> ~2% threshold).
2. Legacy Path Cleanup:
   - Remove (or gate behind flag) any now-dead legacy target selection branches to reduce maintenance surface.
3. Additional k Behavior Tests:
   - Add test demonstrating unchanged choice for k=0 vs k=0.001 (stability under tiny perturbations).
   - Add a scenario where large k flips a choice (engineered ΔU gap + distance contrast) for educational demonstration (optional; keep deterministic).
4. Documentation Sync:
   - Update `.github/copilot-instructions.md` to note GUI k control now implemented.
   - Add brief section to README describing how k influences spatial focus.
5. Trade Heuristic Validation:
   - Add test ensuring partner delta computation excludes non-positive combined gains (guard against regression if heuristic evolves).
6. Metrics / Hash Consideration:
   - Confirm distance_scaling_factor is intentionally NOT part of hash schema (consistent with other config inputs?). Decide if hash should incorporate config fields that alter decision path when changed mid-run.
7. UI UX Polish:
   - Possibly color-code k label when >0 to visually indicate “local bias” active (defer if outside baseline scope).
8. Snapshot / Replay:
   - Verify snapshot serialization (if used) persists k; append field if missing.
9. Educational Overlay (Optional Low Risk):
   - Add overlay showing current k and maybe a per-agent last chosen target type (resource vs partner) for teaching.

---
## 6. Risks / Watchpoints
- Partner vs resource tie-breaking: lexical fallback after equal raw ΔU may surprise users (“partner” beats “resource” due to string order). Consider explicit deterministic priority policy or documentation note.
- Changing k mid-simulation alters future choices but does not retroactively adjust commitments—document this (expected behavior).
- Potential silent perf drift if future additions expand spatial neighbor list filtering cost (currently O(n)).
- Monotonic discount test relies on partner staying chosen; if future scoring adjustments alter raw deltas, may require recalibration.

---
## 7. Validation Checklist (Next Perf + Cleanup PR)
- [ ] Run perf harness (new vs baseline) store JSON artifacts.
- [ ] Confirm median frame time delta < 2%.
- [ ] Run determinism suite with k set to 0 and a non-zero value—ensure identical snapshot when k reverted (no hidden state accumulation).
- [ ] Confirm no additional allocations in hot loop (inspect diff / optionally tracemalloc sample).
- [ ] Document tie-break behavior in developer docs.

---
## 8. Invariants Reconfirmed
- Tie-break key for resource candidates unchanged: (-ΔU, distance, x, y).
- Stable resource iteration preserved via `iter_resources_sorted` fallback.
- Internal RNG separation untouched (no new randomness inserted).
- Metrics hash contract unaffected (no trade/accounting fields added to hash path).
- Complexity remains O(agents + resources) per step (single spatial grid rebuild; localized scans).

---
## 9. Proposed Next PR Slices
A. Perf + Docs PR:
   - Perf validation outputs, README & instructions update, tie-break doc note.
B. Cleanup + Tests PR:
   - Remove legacy selection code, add k stability + partner-delta tests.
C. Optional UX PR:
   - Overlay / color highlight for k, educational explanation panel.

---
## 10. Quick Reference (Current Key Elements)
- Distance scaling factor attribute path: `simulation.config.distance_scaling_factor` (float 0–10).
- Unified selection entry: `Simulation._unified_selection_pass` (invoked during `Simulation.step` when decision mode active and flags permit).
- Partner delta heuristic location: `Agent.select_unified_target` (single pass evaluating nearby agents list).
- Leontief prospecting fallback patch block: inside `_unified_selection_pass` when `choice is None` before deposit/idle fallback.

---
Prepared for next iteration. This document can be extended with perf numbers once gathered.
