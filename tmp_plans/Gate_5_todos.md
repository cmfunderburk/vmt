# Gate 5 Todos — Dynamics & Metrics Spine

Status: Draft Planning (Pre-Implementation)
Date: 2025-09-22

## 1. Scope Statement
Establish deterministic dynamic environment (resource respawn) and metrics/observability layer (per-step, per-agent & aggregate) with snapshot/replay reproducibility and minimal performance overhead (<10% frame time increase).

## 2. Objectives
- Add resource respawn with density cap & deterministic RNG.
- Add metrics collector producing structured per-step records.
- Guarantee determinism via centralized seed and hashing.
- Support snapshot capture and replay equivalence.
- Maintain performance within 10% overhead vs Gate 4 baseline.

## 3. Non-Goals / Explicit Deferrals
- Pathfinding / multi-step planning.
- GUI panels, menus, zoom/pan.
- Scenario library, tutorials, analytics dashboards.
- Energy/budget constraints, trading, multi-agent interaction depth beyond existing competition logic.

## 4. Work Breakdown
### 4.1 Foundations
1. Introduce `simulation/config.py` with dataclass `SimConfig` (grid_size, initial_resources, perception_radius, respawn_target_density, respawn_rate, seed).
2. Introduce central RNG in `world.py` (pass to agents if needed) seeded from config.
3. Add sorted resource iteration in scoring (refactor if currently inline—ensure stable order by (x,y,type)).

### 4.2 Resource Respawn
4. Add respawn scheduler: each tick compute deficit = target_count - current; spawn up to min(deficit, budget) using RNG sampling over empty cells with probability derived from respawn_rate.
5. Track spawned positions for determinism test; ensure no overwrite of existing resource.
6. Config guard: if respawn disabled (rate=0), scheduler is inert.

### 4.3 Metrics Layer
7. Create `metrics.py`: `MetricsCollector` with `record(step, agents, grid, util_fn)`.
8. Fields per agent: id,x,y,mode,target_x,target_y,carrying_good1,carrying_good2,home_good1,home_good2,utility.
9. Aggregate: total_resources, avg_utility, collections_this_step.
10. Maintain internal lists or ring buffer (simple list first) — complexity acceptable.
11. Determinism hash: update incremental SHA256 each `record()` using canonical ordered serialization.

### 4.4 Snapshot & Replay
12. Snapshot function: returns dict {config, initial_resources_list, seed}.
13. Replay harness: build world from snapshot, run N steps, compare determinism hash + per-agent utility series to baseline.
14. JSON serialization test for snapshot schema (round trip).

### 4.5 Performance Guard
15. Add perf test: measure baseline (metrics disabled) vs enabled (collector active) over fixed steps; assert overhead ratio ≤ 1.10.
16. Add micro-benchmark for collector serialization cost (<X ms for 100 steps, choose threshold empirically after initial implementation; placeholder test initially skipped then updated).

### 4.6 Testing & Validation
17. `test_respawn_density.py`: run simulation until warm-up W (e.g., 100 steps), compute mean & max resource counts vs target.
18. `test_metrics_integrity.py`: assert lengths, non-negative utilities, consistent IDs ordering.
19. `test_determinism_hash.py`: two runs same config yield identical hash.
20. `test_snapshot_replay.py`: baseline run vs replay equivalence for first N steps.
21. `test_sorted_scoring.py`: shuffle insertion order of initial resources; ensure target selection sequence identical (hash subset or explicit sequence check).
22. `test_perf_overhead_gate5.py`: overhead ratio test.
23. `test_snapshot_schema.py`: JSON round trip fidelity.
24. Update existing determinism tests if needed to incorporate sorted iteration change.

### 4.7 Documentation & Closure
25. Update README (Gate 5 section stub once near completion) — deferred until implementation near done.
26. Produce `GATE5_EVAL.md` mapping criteria to evidence.
27. Finalize `GATE5_CHECKLIST.md` statuses.

## 5. Acceptance Criteria (Mirrors Checklist)
See `GATE5_CHECKLIST.md` (to be generated) for checkboxes.

## 6. Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Performance regression >10% | Optimize serialization (pre-allocated tuples), skip costly deepcopy |
| Respawn statistical variance flakiness | Use deterministic spawn order candidate list; tolerance windows in tests |
| Hash misses field changes | Centralize serialization; add test mutating one field to detect hash change |
| Metrics memory growth | Provide future knob for down-sampling; Gate 5 tolerates naive list growth |

## 7. Metrics to Record Pre-Implementation
Run baseline script capturing: avg frame time, decision loop microseconds, FPS. Store numbers in `GATE5_EVAL.md` baseline section (initial placeholder now).

## 8. Tooling Impact
- New modules require mypy stubs if necessary; keep types explicit.
- Perf test reuse existing pattern (pytest marker or simple assert threshold).

## 9. Dependencies
- Relies on stable agent & grid APIs from Gate 4; minimal refactor except scoring sort.
- No external package additions anticipated.

## 10. Sequencing Strategy
Critical path: Config + RNG → Sorted scoring → Respawn → Metrics → Hash → Snapshot → Tests → Perf guard → Docs.
Parallelizable: Metrics collector implementation can start while respawn logic stabilized.

## 11. Completion Definition
Gate closes when: checklist all checked, evaluation doc cites: density stats, hash strings, overhead ratio, test counts, lint/type pass.

-- END --
