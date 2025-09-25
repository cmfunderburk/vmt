# GATE_BILATERAL1_CHECKLIST — Foundational Bilateral Trade (Draft + Single Execution) (Updated 2025-09-24)

## Configuration & Helpers
- [x] Marginal utility helper implemented (`preferences/helpers.py`) deterministic across runs (epsilon-lift added Phase 3)
- [x] `Agent.total_inventory()` added (no mutation of originals)
- [x] Helper & accessor covered by tests (determinism & aggregation)

## Draft Intent Mode (No State Mutation)
- [x] `TradeIntent` dataclass created (`simulation/trade.py`)
- [x] Draft flag `ECONSIM_TRADE_DRAFT=1` enumerates intents only
- [x] Co-location index built once per step when draft flag active
- [x] Enumeration produces deterministic ordered list (stable sort & tie-break contract)
- [x] Hash parity: baseline vs draft identical (tests green)
- [x] Perf overhead draft vs baseline ≤2% (spot measurement; formal perf gate pending)

## Metrics & Overlay
- [x] Metrics fields appended: `trade_intents_generated`, `trades_executed` (excluded from hash)
- [x] Overlay debug listing first N intents (N≤3) behind draft flag
- [x] Overlay path pixel baseline unaffected when draft off

## Execution Mode (Single Trade)
- [x] Execution flag `ECONSIM_TRADE_EXEC=1` implies draft enumeration
- [x] Single trade per tick executed if at least one valid intent
- [x] Trade limited to carrying inventory; home inventory unchanged
- [ ] Priority ordering enhanced with real (-ΔU_combined, seller_id, buyer_id, give_type, take_type)  (CURRENT: placeholder 0.0; ΔU calculation not yet integrated)
- [x] Single trade per tick enforced (tests)
- [x] Hash parity vs draft retained (execution counters excluded from hash)
- [ ] Perf overhead exec vs baseline ≤2.5% (formal measurement planned; early runs within target)

## UI / Educational Hooks
- [ ] Agent inspector displays Last Trade (blank when none) (NOT IMPLEMENTED)
- [ ] Start Menu checkbox placeholder / gating hint (NOT IMPLEMENTED)
- [x] README Known Gaps updated with carrying-only invariant (verified)

## Determinism & Tests
- [x] Intent determinism test (stable ordering) 
- [x] Draft parity hash test
- [x] Execution correctness test (inventory delta ±1 of exchanged goods)
- [x] Carrying-only invariant test
- [ ] Tie priority ordering test (ΔU equality scenario) (DEFERRED until ΔU integrated)
- [ ] Perf draft overhead test (Pending perf harness extension)
- [ ] Perf exec overhead test (Pending perf harness extension)
- [x] Overlay debug opt-in smoke test

## Documentation
- [x] README trade draft subsection / roadmap entry (present)
- [ ] API_GUIDE appendix noting experimental flags (NOT YET ADDED)
- [x] Copilot instructions include trading invariant
- [x] Gate Phase 3 summary document created

## Quality Gates
- [x] Lint clean (no new warnings) 
- [x] Type check clean (no new ignores; ΔU deferred)
- [x] Determinism baseline tests green
- [x] Performance floor maintained (≥30 FPS observed)
- [x] No additional allocations in hot loop beyond bounded intent list

## Evidence to Capture for Evaluation
- [ ] Perf JSON: baseline, draft, exec (avg_fps, frames)
- [ ] Sample intents list (canonical scenario)
- [ ] Before/after inventory snapshot for executed trade
- [ ] Determinism hash parity output (baseline vs draft)
- [ ] Exec hash record (hash parity currently retained; note counters excluded)
- [ ] Overlay debug screenshot or pixel diff summary

## Post-Gate Quick Win Targets
- Integrate actual ΔU into intent & optional priority flag.
- Add last executed trade record for inspector / overlay highlight.
- Add no-trade tick metrics.
- Perf harness extension for draft/exec overhead assertions.

-- END --
