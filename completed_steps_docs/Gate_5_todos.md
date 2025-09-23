# Gate 5 Todos – Dynamics & Metrics Spine (Refined Planning)

Status: PLANNING (Pre-Implementation)
Date: 2025-09-22

## 1. Mission Summary
Introduce deterministic dynamic world evolution (resource respawn) plus an internal metrics & replay spine without degrading core rendering / decision performance (>30 FPS & ≤10% decision loop overhead). This gate turns the static environment into a controlled, instrumentable system suitable for pedagogical demonstrations and future scenario authoring.

## 2. Scope
In-Scope:
- Deterministic respawn scheduler (target density & cap; seed-driven RNG)
- Metrics collection (per-step per-agent + aggregated snapshot)
- Determinism hash + snapshot / replay harness
- Performance and density guard tests
- Sorted, stable resource iteration (ordering neutrality)

Out-of-Scope (Deferred):
- Pathfinding or multi-step planning heuristics
- Trading / interaction mechanics beyond existing competition resolution
- GUI overlays / panels for metrics visualization
- Persistence or multi-scenario packaging
- Advanced statistical smoothing / down-sampling

## 3. Success Criteria (Condensed)
- Respawn keeps mean resource count within ±5% of configured target after warm-up
- No frame rate floor violation (FPS ≥30) and decision+metrics overhead ratio ≤1.10
- Determinism: identical determinism hash + per-agent utility series for same seed snapshot
- Metrics collector captures required fields (id, pos, mode, target, carrying, home, utility) + aggregates (total_resources, avg_utility, collections_this_step)
- All new tests + legacy tests pass lint & type gates cleanly

## 4. Key Design Constraints & Principles
- Single RNG source (seed in `SimConfig`) – forbid ad-hoc `random` usage outside controlled injection
- Respawn algorithm must be O(R + S) where R = resources, S = spawns per tick (avoid scanning entire grid each tick for large future grids; initial naive approach acceptable but document improvement path)
- Metrics overhead minimized: avoid deep copies; operate on primitive tuples and direct dict field reads
- Hash stability: canonical ordering (agent id ascending) + minimal float formatting (repr of ints / exact floats); use SHA256 updated per step
- Avoid memory bloat: gate requirement allows naive list accumulation; note future ring-buffer optimization hook

## 5. Proposed Modules / Files
- `src/econsim/simulation/config.py` → `SimConfig` dataclass
- `src/econsim/simulation/respawn.py` → `RespawnScheduler` (pure logic; no rendering)
- `src/econsim/simulation/metrics.py` → `MetricsCollector`
- `tests/unit/test_respawn_density.py`
- `tests/unit/test_metrics_integrity.py`
- `tests/unit/test_determinism_hash.py`
- `tests/unit/test_snapshot_replay.py`
- `tests/unit/test_sorted_scoring.py`
- `tests/unit/test_perf_overhead_gate5.py`
- `tests/unit/test_snapshot_schema.py`

## 6. Phased Work Breakdown
Phase A – Foundations:
1. Add `SimConfig` + central RNG plumbing (world owns `rng: Random`).
2. Refactor resource iteration use in scoring to sorted sequence (stable by (x,y,rtype)).

Phase B – Respawn:
3. Implement `RespawnScheduler`: compute deficit = target - current; cap spawn count per tick (config field). 
4. Spawn selection: biased random sampling without replacement among empty cells (document current complexity).
5. Deterministic ordering: keep list of candidate empty cells sorted before RNG selection.

Phase C – Metrics Spine:
6. Implement `MetricsCollector.record(step, sim)` returning lightweight struct (append to internal list).
7. Compute per-agent utility using existing preference objects (reuse bundle from carrying+home? decision uses carrying; metrics uses stored+carrying for *total owned*). Document rationale.
8. Track aggregate counts & step-level collections delta.
9. Determinism hash update each record (after respawn + agent steps).

Phase D – Snapshot & Replay:
10. Implement `create_snapshot(sim, config)` capturing initial resources & seed.
11. Implement `replay(snapshot, steps) -> hash, utility_series` harness.
12. Write deterministic equivalence test.

Phase E – Performance & Validation:
13. Overhead perf test (with & without metrics enabled for same steps count) asserting ≤10%.
14. Density stability test (warm-up W steps, compute mean, max). 
15. Micro-benchmark collector overhead (avg µs per record). Empirically set threshold post-initial run then lock test.

Phase F – Documentation & Closure:
16. Update README (Gate 5 summary stub) near end.
17. Populate `GATE5_EVAL.md` evidence table.
18. Close checklist & retrospective section.

## 7. Detailed Task List (Execution Items)
- [ ] Add `SimConfig` dataclass
- [ ] Integrate config + RNG into `Simulation`
- [ ] Stable sorted resource iteration path for decision scoring
- [ ] Implement `RespawnScheduler`
- [ ] Add respawn hook in simulation step (post-agent collection phase)
- [ ] MetricsCollector implementation
- [ ] Determinism hash integration
- [ ] Snapshot creation function
- [ ] Replay harness
- [ ] All enumerated tests (see Section 5)
- [ ] Perf overhead guard test
- [ ] Micro-benchmark threshold test
- [ ] README Gate 5 section update
- [ ] Evaluation doc evidence population
- [ ] Checklist completion pass

## 8. Open Questions (Document Before Coding)
- Should respawn avoid spawning adjacent to agents (pedagogical clarity)? (Default: NO for Gate 5)
- Utility for metrics: carrying only vs carrying+home? (Proposed: carrying+home to reflect accumulated welfare.)
- Cap on spawn per tick relative to grid size? (Introduce `max_spawn_per_tick` config field.)

## 9. Risk Register (Incremental)
| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Respawn causes burst allocations | Perf regression | Medium | Preallocate candidate list; reuse RNG | 
| Hash misses subtle state (e.g., mode change) | Replay false positive | Low | Include mode & inventory in hash serialization |
| Metrics overhead >10% | Perf gate fail | Medium | Early measurement & optimize field access |
| Test flakiness (density variance) | CI noise | Medium | Use warm-up & tolerance band; deterministic spawn ordering |

## 10. Exit Definition
Gate passes when: All success criteria satisfied, checklist complete, evaluation doc includes baseline vs post metrics, determinism artifacts (hash string), no perf regressions, and no unresolved P1 risks.

-- END --
