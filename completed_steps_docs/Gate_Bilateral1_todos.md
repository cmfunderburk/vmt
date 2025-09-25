# Gate Bilateral1 Todos – Foundational Trade Draft & Single Execution (Draft)

Objective: Introduce a deterministic, feature‑flagged bilateral exchange prototype without altering existing determinism hashes by default. Deliver intent enumeration, single optional executed trade per tick (flag‑gated), metrics placeholders, and educational inspection hooks while preserving performance (≥60 FPS typical, ≥30 FPS floor) and O(agents+resources) complexity.

## Deliverables
1. Marginal utility helper (pure, deterministic) for existing preference types.
2. `Agent.total_inventory()` convenience (read-only aggregation; no mutation).
3. `TradeIntent` dataclass + draft enumeration (no state mutation) behind `ECONSIM_TRADE_DRAFT=1`.
4. Co‑location index pass (O(n)) reused for intent generation (no extra scans).
5. Metrics placeholders appended: `trade_intents_generated`, `trades_executed` (hash unaffected initially).
6. Debug overlay (flagged) listing first N intents (stable ordering) – no perf regression (>2% budget).
7. Single executed swap (qty=1, carrying-only) behind `ECONSIM_TRADE_EXEC=1` (implies draft); at most one trade per tick.
8. Agent inspector field: Last Trade (optional blank when none).
9. Documentation updates: README Known Gaps note (carrying-only invariant), Copilot instructions trading invariant (already added), API_GUIDE appendix stub.
10. Comprehensive tests: intent determinism, hash parity (draft on/off), execution correctness, invariant enforcement, perf overhead.

## Out of Scope / Deferred
* Multi-trade per tick and reservation set.
* Inequality / diversity analytics (post-trade impact metrics).
* GUI trade configuration panel (beyond placeholders).
* Snapshot/replay inclusion of trade fields (hash change deferred until promotion gate).
* Agent negotiation heuristics or pricing.

## Acceptance Criteria
| # | Criterion | Validation |
|---|-----------|------------|
| 1 | MU helper deterministic per preference | `test_trade_mu_helper_determinism` (compare repeat outputs)
| 2 | Draft intents generated only when flag set | `test_trade_draft_flag_behavior`
| 3 | No hash change with draft flag on (no exec) | Compare baseline & draft run in `test_trade_draft_hash_parity`
| 4 | Intent ordering stable | Sort key test `test_trade_intent_priority_order`
| 5 | Execution swaps only carrying items | `test_trade_execution_carrying_only`
| 6 | Home inventory untouched by trades | Same test + explicit home inventory snapshot
| 7 | Single trade max per tick enforced | `test_trade_single_execution_cap`
| 8 | Perf overhead ≤2% draft mode vs baseline | `test_perf_trade_draft_overhead`
| 9 | Overlay debug path pixel parity off / bounded diff on | Existing overlay pixel test extended; new `test_trade_overlay_opt_in`
|10 | Hash divergence isolated to exec flag scenario | New fixture file; baseline unaffected

## Task List
- [ ] Add `preferences/helpers.py` with marginal utility helper.
- [ ] Add `total_inventory()` method to `Agent` (tests updated).
- [ ] Implement `TradeIntent` dataclass in `simulation/trade.py` (new file).
- [ ] Add co-location indexing inside `Simulation.step` (single pass build map if trade draft flag set).
- [ ] Implement `_compute_trade_intents()` (draft mode) – no side effects.
- [ ] Append metrics fields (do not integrate into hash yet).
- [ ] Implement debug overlay listing N intents (flag check, constant N=3).
- [ ] Add execution path `_execute_first_trade()` gated by `ECONSIM_TRADE_EXEC=1`.
- [ ] Update agent inspector panel with Last Trade field (blank when none).
- [ ] Write determinism & parity tests for draft mode.
- [ ] Write execution correctness + invariant tests.
- [ ] Write perf test comparing baseline vs draft vs exec (collect FPS JSON).
- [ ] Update README (trade roadmap snippet) & API_GUIDE (draft section placeholder).
- [ ] Extend copilot instructions ONLY if new invariants emerge.
- [ ] Prepare `GATE_BILATERAL1_CHECKLIST.md` from acceptance table.

## Risk Mitigation
| Risk | Mitigation |
|------|------------|
| Hash drift from new fields | Keep hash function unchanged; exclude draft metrics until promotion gate |
| Performance regression | Co-location map built only when flag set; single pass O(n) |
| Unintended inventory mutation | Limit trade to carrying dict; assert home inventory unchanged post-step |
| Ordering instability | Deterministic priority tuple; test explicit tie cases |
| Feature creep | Gate strictly ends at single-trade execution; multi-trade deferred |

## Metrics to Capture
* FPS baseline vs draft vs exec (2s widget run).
* Counts: intents generated / executed over 100-step scenario.
* Determinism hash baseline vs draft parity; exec flagged variant stored separately.

## Exit Summary Template (for Evaluation)
Provide: perf table (baseline/draft/exec), representative intents list, before/after carrying state for executed trade, hash parity evidence, overlay pixel diff summary.

-- END --
