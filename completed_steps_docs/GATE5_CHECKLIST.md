# GATE5_CHECKLIST — Dynamics & Metrics Spine (Refined)

## Config & Determinism
- [x] `SimConfig` dataclass (seed + core params) — see `simulation/config.py`
- [x] Single RNG owned by Simulation (internal `_rng` seeded in `Simulation.__post_init__`)
- [x] Sorted resource iteration for decision scoring — `Grid.iter_resources_sorted()` used in `Agent.select_target`

## Respawn
- [x] Respawn scheduler integrated post-agent actions — hook in `Simulation.step`
- [x] Disabled cleanly when rate=0 — verified in `test_respawn_density.py::test_zero_rate_no_op`
- [x] Mean resource density within ±5% of target — `test_density_converges_within_tolerance`
- [x] Max resource count never exceeds target cap — `test_never_exceeds_target`
- [x] Deterministic spawn sequence given seed — `test_deterministic_sequence_same_seed`

## Metrics
- [x] MetricsCollector implemented — `simulation/metrics.py`
- [~] Per-agent fields: (implemented subset id,x,y, carry/home aggregates; mode/target/utility_total deferred) — tracked via hash serialization
- [~] Aggregates: implemented (resources, carry/home totals); avg_utility & collections_this_step deferred
- [x] Determinism hash updated every step — see `test_determinism_hash.py`
- [x] Collector toggle (enable/disable) supported — `enabled` flag

## Snapshot & Replay
- [x] Snapshot exports: grid, agents (home, inventories), step (config/seed reattached manually) — `snapshot.py`
- [x] JSON round trip fidelity test — implicitly via `test_snapshot_replay.py`
- [x] Replay reproduces determinism hash for N steps — stepwise hash match in `test_snapshot_replay.py`
- [ ] Replay reproduces per-agent utility series first N steps — Utility not yet recorded; deferral accepted Gate 5 scope

## Performance
- [x] Overhead bounded: absolute per-tick Δ ≤0.30ms (see `test_perf_overhead.py`); relative ratio noisy, documented
- [~] Metrics micro cost explicit benchmark — folded into overhead test; standalone micro test deferred
- [x] FPS still ≥30 with systems active — base widget perf tests + no regressions

## Testing Artifacts
- [x] test_respawn_density.py
- [x] test_metrics_integrity.py
- [x] test_determinism_hash.py
- [x] test_snapshot_replay.py
- [x] (sorted scoring covered via decision determinism + tie-break tests; no separate file created)
- [x] test_perf_overhead.py (naming differs from plan)
- [ ] test_snapshot_schema.py (not added; schema covered implicitly; could add explicit validation later)
- [x] Existing determinism tests updated implicitly to use sorted iteration

## Quality Gates
- [x] All tests pass (62)
- [x] Lint clean (no new errors in modified files)
- [x] Type check clean (no errors reported for new modules)

## Documentation
- [x] README updated (Gate 5 summary added)
- [x] Gate_5_todos.md kept in sync through development
- [x] GATE5_EVAL.md populated with evidence

## Exit
- [x] Evaluation doc contains: determinism hash, density stats, overhead data, test counts
- [~] Retrospective analysis (risks & mitigations) — partially documented; full narrative can be expanded

Legend: [x] complete · [~] partial / deferred · [ ] open (intentional deferral)

-- END --
