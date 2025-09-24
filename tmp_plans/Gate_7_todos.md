# Gate 7 Todos — Agent Interaction & Trading Primitives (Draft)

Objective: Introduce minimal agent-to-agent interaction (trading primitive) that leverages existing deterministic movement & preference system without breaking performance or hash invariants. Establish extensible contract for future richer exchange / price discovery while keeping O(agents + resources) per-step complexity.

## Context Snapshot (Prior Gates Accomplished)
- Gate 4: Deterministic preference-based target selection, tie-break (-ΔU, dist, x, y), typed resources.
- Gate 5: (Assumed) Stabilization & performance guards (decision throughput baseline retained).
- Gate 6: Factory construction (`Simulation.from_config`), decision-mode default, overlay toggle, respawn integration, metrics hash stability.
- Current invariants: single QTimer loop, no added threads/timers, append-only serialization, RNG separation (external vs internal), performance ≥60 FPS typical.

## High-Level Goals
1. Add a minimal trade interaction enabling voluntary exchange when two agents occupy the same cell or a designated adjacency rule.
2. Preserve determinism (trade matching ordering deterministic & testable) and metrics hash unless extended intentionally.
3. Provide extensible interface (e.g., `TradeRule` or `ExchangePolicy`) with pure deterministic decision given state.
4. Record baseline interaction metrics (count of trades, goods transferred) OPTIONAL (append metrics fields only if tests added).
5. Maintain O(agents + resources) step: no all-pairs scanning; restrict trade partner discovery to local cell or constant-size neighborhood.

## Deliverables
- Trade policy interface (pure, stateless) + default simple rule: if two agents meet and each holds ≥1 unit of a different good, exchange one unit toward balancing marginal utilities.
- Deterministic partner selection (ordered by agent id ascending) & execution order (single pass; no oscillation within a tick).
- New tests: trade execution correctness, determinism with trading enabled, no trade when insufficient goods, hash unchanged when trading disabled.
- Optional metrics extension (if included): fields appended (e.g., `trades_executed`, `units_exchanged_good1`, `units_exchanged_good2`).
- Update factory/config to allow enabling trading (flag `enable_trading` default False to keep baseline hash unchanged).
- Documentation: README trading preview section; Copilot instructions unchanged except new allowed fast path note.

## Non-Goals / Deferred
- Price formation, bids/asks, multi-party markets, inventories > simple goods counts normalization.
- Utility re-optimization mid-tick beyond existing movement + trade.
- GUI panels for trading statistics (future gate).
- Network or asynchronous events.

## Acceptance Criteria (Initial Draft)
| # | Criterion | Validation |
|---|-----------|------------|
| 1 | Config flag `enable_trading` added, default False | `SimConfig` test + factory path leaves trading inert |
| 2 | Trading enabled yields deterministic trades given seed | Re-run determinism test variant with trading on |
| 3 | Partner matching deterministic (id order) | Targeted test with 3 agents same cell ensures order |
| 4 | Trade rule conserves total goods | Invariant test sum(goods) pre == post |
| 5 | No performance regression (>5% FPS drop) | Perf test variant w/ trading flag on |
| 6 | Metrics fields appended only (if used) | Hash parity test trading disabled; new metrics test enabled |
| 7 | Serialization schema unchanged ordering | Snapshot test append-only diff |
| 8 | Complexity O(agents + resources) maintained | Code review + neighborhood iteration test (no nested N^2) |

## Task Breakdown
- [ ] Extend `SimConfig` with `enable_trading` (default False) and validate (bool).
- [ ] Add trading subsystem file `simulation/trading.py` with `TradePolicy` protocol & `SimpleExchangePolicy`.
- [ ] Integrate into `Simulation.step` (conditional block after collection / deposit, before respawn/metrics).
- [ ] Implement partner discovery: group agents by (x,y) (single dict bucket walk) no global all-pairs.
- [ ] Execute at most one exchange per agent per tick (mark participants to prevent double trade).
- [ ] Append metrics fields (optional) + update metrics collector (guard with flag).
- [ ] New unit tests: trade_basic, trade_no_goods, trade_determinism, trade_conservation.
- [ ] Perf test variant enabling trading (reuse existing harness with flag).
- [ ] Snapshot test ensuring enabling trading does not alter baseline snapshot without exchanges.
- [ ] README section + brief rationale.
- [ ] Update Copilot instructions if needed (list trading fast path allowed with constraints).

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|-----------|
| Hidden N^2 from naive partner search | Perf regression | Use per-cell grouping dict built in one pass |
| Hash drift when trading disabled | Breaks regression tests | Guard all new logic behind flag; no side effects when False |
| Floating point utility differences | Determinism variance | Use integer unit transfers; no floating calculations beyond existing preferences |
| Metrics append breaks ordering | Replay failure | Append only at end; update tests accordingly |

## Open Questions (To Align Before Implementation)
1. Should trade trigger before or after deposit? (Proposed: after collection, before deposit/home check might complicate; choose after deposit to avoid mid-transfer of carrying vs home mix.)
2. Allow multi-good swap or single-unit bilateral exchange only? (Start single-unit.)
3. Include partial fairness logic (e.g., utility delta improvement) or unconditional exchange heuristic? (Start unconditional when each has ≥1 of distinct goods.)

## Test Plan Details
- Determinism: run existing trajectory test with trading disabled (baseline) and with enabled + controlled scenario (expected hash captured).
- Conservation: custom fixture sets two agents with asymmetric holdings, steps once, asserts total goods invariant and expected redistribution.
- Performance: 50 agents / moderate resource density; compare avg FPS diff <5% vs disabled flag.
- Snapshot: create snapshot pre-trade; restore; ensure enabling trading but no meeting yields identical hash.

## Exit Summary Template
Provide: performance table (disabled vs enabled), determinism hash parity (disabled), new hash sample (enabled), conservation invariant proof, code snippet of partner matching O(n).

-- END DRAFT --
