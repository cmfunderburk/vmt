# Gate GUI Evaluation (Pre-Implementation Skeleton)

Status: Framework prepared; to be populated incrementally as fast-path tasks complete.

## 1. Scope Definition
Feature-flagged GUI Phase A providing start menu, basic session lifecycle, overlays, control panel, and metrics mini panel without modifying simulation core invariants.

## 2. Evidence Log (To Fill)
| Item | Target | Evidence | Status |
|------|--------|----------|--------|
| Full suite legacy | 78 pass | test run log | Pending (baseline already known) |
| Full suite flag-on | 78 pass | test run log | Pending |
| Perf baseline (flag off) | ~60 FPS | perf JSON | Pending |
| Perf flag overlays off | ~60 FPS (<=2% delta) | perf JSON | Pending |
| Perf flag overlays on | <=2% slower | perf JSON comparison | Pending |
| Overlay pixel diff | diff_ratio > threshold | test log | Pending |
| Turn mode no autostep | steps constant over N ticks | test log | Pending |
| Steps/sec estimator | reasonable value after warmup | test log | Pending |
| Hash cache integrity | unchanged without refresh | test log | Pending |
| Teardown reuse | second session stable | test log | Pending |

## 3. Determinism Assurance
Planned verification: identical descriptors (hash1 == hash2) in GUI path with overlays toggled between runs.

## 4. Performance Notes
To record: three 2-second perf samples (baseline, flag-off; flag-on overlays off; flag-on overlays on) with frames, duration, avg FPS metrics.

## 5. Risk Review
No new concurrency introduced; only additional UI event handling. Overlay logic bounded by constant operations relative to agents count used in modest pedagogical scenarios (<=64 agents cap in validation).

## 6. Deviation From Gate Checklist
None yet—any deferrals will be itemized here with rationale and follow-up gate mapping.

## 7. Next Actions
Proceed with Batch 1 tasks (Start Menu refactor + validation test). Update evidence log upon first passing test under flag.

-- END EVAL (INITIAL SKELETON) --
