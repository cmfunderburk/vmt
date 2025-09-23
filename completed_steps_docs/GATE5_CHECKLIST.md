# GATE5_CHECKLIST — Dynamics & Metrics Spine (Refined)

## Config & Determinism
- [ ] `SimConfig` dataclass (grid_size, initial_resources, perception_radius, respawn_target_density, respawn_rate, max_spawn_per_tick, seed)
- [ ] Single RNG owned by Simulation (no stray random usage)
- [ ] Sorted resource iteration for decision scoring (stable (x,y,rtype))

## Respawn
- [ ] Respawn scheduler integrated post-agent actions
- [ ] Disabled cleanly when rate=0
- [ ] Mean resource density within ±5% of target after warm-up
- [ ] Max resource count never exceeds target cap in test run
- [ ] Deterministic spawn sequence given seed

## Metrics
- [ ] MetricsCollector implemented
- [ ] Per-agent fields: id,x,y,mode,target,carry_good1,carry_good2,home_good1,home_good2,utility_total
- [ ] Aggregates: total_resources, avg_utility, collections_this_step
- [ ] Determinism hash updated every step
- [ ] Collector toggle (enable/disable) supported

## Snapshot & Replay
- [ ] Snapshot exports: config + initial resources + seed
- [ ] JSON round trip fidelity test
- [ ] Replay reproduces determinism hash for N steps
- [ ] Replay reproduces per-agent utility series first N steps

## Performance
- [ ] Decision+metrics overhead ratio ≤1.10 vs baseline
- [ ] Metrics micro cost ≤ threshold (µs/record) (threshold documented)
- [ ] FPS still ≥30 with metrics+respawn active

## Testing Artifacts
- [ ] test_respawn_density.py
- [ ] test_metrics_integrity.py
- [ ] test_determinism_hash.py
- [ ] test_snapshot_replay.py
- [ ] test_sorted_scoring.py
- [ ] test_perf_overhead_gate5.py
- [ ] test_snapshot_schema.py
- [ ] Updated existing determinism tests (if required)

## Quality Gates
- [ ] All tests pass
- [ ] Lint clean
- [ ] Type check clean

## Documentation
- [ ] README updated (Gate 5 summary)
- [ ] Gate_5_todos.md kept in sync (progress marks)
- [ ] GATE5_EVAL.md populated with evidence table

## Exit
- [ ] Evaluation doc contains: determinism hash, density stats, overhead ratio, micro cost, test counts
- [ ] Retrospective analysis (risks & mitigations) completed

-- END --
