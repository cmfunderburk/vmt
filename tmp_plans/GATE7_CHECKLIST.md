# GATE7_CHECKLIST — Agent Interaction & Trading Primitives (Draft)

(Complete / evidence each item before marking Gate 7 done. Keep additions append-only; do not reorder once checked.)

## Configuration & Flags
- [ ] `enable_trading` added to `SimConfig` (default False)
- [ ] Factory passes trading flag through unchanged
- [ ] Trading disabled path leaves hashes & metrics untouched (baseline determinism test unchanged)

## Trading Subsystem
- [ ] `simulation/trading.py` created with `TradePolicy` / `SimpleExchangePolicy`
- [ ] Deterministic partner grouping (single pass build: cell -> agent list)
- [ ] Partner order = ascending agent id
- [ ] Single exchange per agent per tick (participation marker works)
- [ ] Trade rule: swap 1 unit good where each has ≥1 of different good types (exact logic documented)
- [ ] Goods conservation invariant (sum across agents constant) enforced by test

## Integration Point
- [ ] Trading invoked only when `enable_trading` True
- [ ] Invocation occurs after collection & deposit (final chosen ordering documented) before respawn/metrics
- [ ] No side effects when no eligible pairs

## Metrics (Optional If Implemented)
- [ ] Metrics fields appended (`trades_executed`, `units_exchanged_good1`, `units_exchanged_good2`)
- [ ] Metrics hash parity when disabled
- [ ] New metrics tests cover increment logic

## Determinism & Tests
- [ ] New test: `test_trading_basic_exchange`
- [ ] New test: `test_trading_no_exchange_conditions`
- [ ] New test: `test_trading_determinism_seed_parity`
- [ ] New test: `test_trading_goods_conservation`
- [ ] Updated determinism suite includes trading-enabled scenario hash capture

## Performance
- [ ] Perf run (trading disabled) unchanged from Gate 6 baseline (±5%)
- [ ] Perf run (trading enabled) overhead <5% FPS drop (document numbers)
- [ ] Complexity review: no O(n^2) partner loops; code walkthrough evidence

## Serialization / Snapshot
- [ ] Snapshot append-only (no reordering)
- [ ] Replay test passes with trading disabled
- [ ] Replay determinism test with trading enabled (canonical scenario) documented

## Documentation
- [ ] README: Gate 7 section (trading primitive overview)
- [ ] Copilot instructions mention trading fast path constraints
- [ ] Gate_7_todos.md maintained & updated during execution
- [ ] This checklist committed early (pre-implementation)

## Quality Gates
- [ ] Lint clean post-change
- [ ] Type checks clean (new module annotated)
- [ ] Tests all green (include new trading tests)
- [ ] Perf evidence JSON captured & stored (e.g., `tmp_perf_gate7.json`)

## Exit Artifacts
- [ ] GATE7_EVAL.md produced (criteria→evidence mapping)
- [ ] Release notes draft (if pattern continued) summarizing trading addition
- [ ] Hash samples recorded (baseline disabled vs enabled scenario)

-- END --
