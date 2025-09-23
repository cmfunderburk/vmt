# GATE 5 CHECKLIST — Dynamics & Metrics Spine

(Complete all items before declaring Gate 5 done.)

## Configuration & Determinism
- [ ] Central `SimConfig` dataclass (grid_size, initial_resources, perception_radius, respawn_target_density, respawn_rate, seed)
- [ ] Single RNG source seeded from `SimConfig`
- [ ] Sorted resource iteration in scoring (stable order by (x,y,type))

## Resource Respawn
- [ ] Respawn scheduler respects target density & cap
- [ ] Respawn disabled when rate=0
- [ ] Density mean within ±5% window after warm-up
- [ ] Density never exceeds cap in test run

## Metrics Layer
- [ ] MetricsCollector records per-agent fields (id,x,y,mode,target,carrying,home,utility)
- [ ] Aggregate metrics (total_resources, avg_utility, collections_this_step) captured
- [ ] Determinism hash updates every step
- [ ] Metrics lengths match number of steps

## Snapshot & Replay
- [ ] Snapshot exports (config, initial_resources_list, seed)
- [ ] JSON round trip preserves snapshot
- [ ] Replay reproduces determinism hash for N steps
- [ ] Replay reproduces per-agent utility series first N steps

## Performance Guard
- [ ] Overhead ratio ≤ 1.10 vs baseline (decision + metrics)
- [ ] Collector micro-benchmark below threshold (placeholder updated with empirical value)

## Testing
- [ ] `test_respawn_density.py`
- [ ] `test_metrics_integrity.py`
- [ ] `test_determinism_hash.py`
- [ ] `test_snapshot_replay.py`
- [ ] `test_sorted_scoring.py`
- [ ] `test_perf_overhead_gate5.py`
- [ ] `test_snapshot_schema.py`
- [ ] Updated existing determinism tests (if required)

## Quality Gates
- [ ] All pre-existing tests pass
- [ ] New tests pass
- [ ] Lint clean (ruff + black)
- [ ] Type check clean (mypy)

## Documentation
- [ ] Gate 5 section added to README (summary of dynamics & metrics)
- [ ] `GATE5_EVAL.md` produced mapping criteria → evidence
- [ ] Todos file updated progressively (this gate)
- [ ] Checklist (this file) fully checked at closure

## Exit
- [ ] Evaluation doc includes: density stats, determinism hash, overhead ratio, test counts, baseline vs post metrics
- [ ] Gate 5 retrospective (risks realized vs mitigated) embedded in evaluation doc

-- END --
