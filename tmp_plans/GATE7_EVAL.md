# GATE7_EVAL — Agent Interaction & Trading Primitives (Scaffold)

## Purpose
Evaluate introduction of deterministic, minimal trading between agents without regressing performance, determinism, or snapshot compatibility.

## Scope (Restated)
Add optional trading (flagged) enabling single-unit bilateral exchanges when two agents co-locate (or chosen ordering) and each holds at least one unit of a different good. Preserve O(agents + resources) complexity and baseline hashes when disabled.

## Preconditions
- Gate 6 integration stable (factory, overlay, respawn, metrics intact)
- Determinism & perf baselines captured (Gate 6 hashes + perf JSON)
- Copilot instructions updated with invariants (already current)

## Acceptance Criteria Mapping (Fill During Evaluation)
| # | Criterion | Evidence (Link / Snippet) | Status |
|---|-----------|---------------------------|--------|
| 1 | Config flag added | diff snippet / test reference | |
| 2 | Deterministic trade partner ordering | test_trading_basic_exchange | |
| 3 | Single exchange per agent per tick | code snippet + test_trading_no_double | |
| 4 | Goods conservation | test_trading_goods_conservation | |
| 5 | Disabled path hash parity | determinism hash comparison table | |
| 6 | Enabled path deterministic hash | captured hash sample | |
| 7 | Perf overhead <5% | perf JSON diff | |
| 8 | Metrics appended only | snapshot schema diff + metrics test | |
| 9 | No O(n^2) loops | code review excerpt | |
| 10 | Serialization unchanged ordering | snapshot replay test | |

## Hash Samples (Populate)
```
Baseline (disabled): <hash>
Trading Enabled Scenario: <hash>
```

## Performance Table (Populate)
| Scenario | Avg FPS | Delta vs Gate 6 | Pass/Fail |
|----------|---------|-----------------|-----------|
| Disabled |         |                 |           |
| Enabled  |         |                 |           |

## Metrics Extension (If Implemented)
```
trades_executed=..., units_exchanged_good1=..., units_exchanged_good2=...
```
Determinism note: metrics hash changes only when trading enabled (document new hash root cause).

## Risks Encountered & Resolutions
- TBD

## Regression Guard Additions
- New determinism variant test name(s): ...
- Perf harness parameter additions: ...

## Follow-On Recommendations
- Parameterize trade quantity by marginal utility ratio (future gate)
- Introduce multi-agent matching fairness test
- Add GUI panel for trade stats (deferred)

## Exit Decision
(Complete when all criteria satisfied)
- [ ] All checklist items complete
- [ ] Hash parity (disabled) confirmed
- [ ] Perf targets met
- [ ] Documentation updated

## Sign-Off
Reviewer(s): ...  Date: ...

-- END SCAFFOLD --
