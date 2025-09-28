# GATE_BILATERAL2_CHECKLIST — GUI Integration & Analytics for Bilateral Exchange

## Phase 1: Data Plumbing & ΔU
- [ ] ΔU stored per TradeIntent (not yet in priority by default)
- [ ] realized_utility_gain_total metric increments on each executed trade
- [ ] last_executed_trade record updated (seller,buyer,give,take,deltaU)
- [ ] trade_ticks and no_trade_ticks counters maintained
- [ ] Tests green: intent ΔU, realized gain accumulation, tick counters
- [ ] Phase 3 summary doc updated with ΔU note

## Phase 2: GUI Surfacing
- [ ] Overlay highlights executed trade (distinct style)
- [ ] ECONSIM_TRADE_GUI_INFO flag renders executed trade summary text
- [ ] Agent inspector (or fallback) displays last executed trade
- [ ] Start Menu checkbox for Bilateral Exchange appears (disabled unless flags active)
- [ ] Tests: overlay highlight smoke; inspector fallback smoke
- [ ] README GUI section updated; API_GUIDE experimental flags updated

## Phase 3: Priority & Fairness (Flagged)
- [ ] ECONSIM_TRADE_PRIORITY_DELTA flag switches ordering to (-ΔU, seller_id, buyer_id, give_type, take_type)
- [ ] fairness_round index increments on execution (tracked metric)
- [ ] Tests: priority reorder under flag; fairness_round increments
- [ ] Docs: Rationale added (why default stays stable / determinism considerations)

## Performance & Determinism
- [ ] FPS ≥30 with GUI info flag on (short perf capture)
- [ ] No additional per-frame allocations beyond O(intents)
- [ ] Hash parity with all new flags off
- [ ] Priority flag off: ordering unchanged vs Gate Bilateral1 baseline

## Evidence Artifacts
- [ ] Perf JSON (baseline vs GUI_INFO)
- [ ] Screenshot executed trade highlight
- [ ] Inspector view snapshot or textual dump
- [ ] Determinism hash comparison (flags off vs on)
- [ ] Sample log of ΔU annotated intents

## Documentation & Cross-Links
- [ ] Gate_Bilateral1_summary updated: points to Bilateral2 features
- [ ] Bilateral2 evaluation document completed (GATE_BILATERAL2_EVAL.md)
- [ ] Known Gaps updated (multi-trade, fairness scheduling activation)

## Exit Conditions
All checklist items above marked complete and evaluation document accepted.

-- END --
