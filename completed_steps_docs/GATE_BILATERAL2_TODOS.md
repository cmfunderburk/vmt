# GATE_BILATERAL2_TODOS — Bilateral Exchange GUI Integration & Analytics

Goal: Elevate bilateral exchange from core simulation feature to an interactive, inspectable, and pedagogically clear GUI experience without altering determinism hash (unless explicitly gated) and without degrading performance below 30 FPS.

## Scope Summary
Phase 1: Data Plumbing & ΔU Augmentation (no GUI yet)
Phase 2: GUI Surfacing (overlay + inspector)
Phase 3: Priority & Fairness Feature Flag (optional enhancements)
Phase 4: Evidence & Polishing

Out of Scope: Multi-trade per tick, money mode integration, snapshot schema changes (beyond approved append-only fields), adaptive epsilon tuning.

---
## Phase 1: Data Plumbing & ΔU Augmentation
- [x] P1.1 Add ΔU calculation to trade enumeration (store per intent, not yet in priority)
- [x] P1.2 Add realized_utility_gain_total metric (hash-excluded)
- [x] P1.3 Add last_executed_trade record (seller, buyer, give_type, take_type, delta_utility)
- [x] P1.4 Add no_trade_ticks & trade_ticks counters (hash-excluded)
- [x] P1.5 Unit tests: test_trade_intent_delta_utility_computed
- [x] P1.6 Unit tests: test_trade_metrics_realized_gain_and_ticks
- [x] P1.7 Update Phase 3 summary doc with ΔU field note
- [x] P1.8 Update bilateral checklist (ΔU partial completion noted; priority ordering still gated)

## Phase 2: GUI Surfacing
- [x] P2.1 Overlay highlight executed trade (green highlight implemented)
- [x] P2.2 Add optional executed trade summary line (flag ECONSIM_TRADE_GUI_INFO implemented)
- [x] P2.3 Agent inspector panel: display last trade (if inspector system present; otherwise scaffold minimal panel)
- [x] P2.4 Start Menu checkbox (disabled if feature flags off) labeled "Bilateral Exchange (Experimental)"
- [x] P2.5 Unit tests (GUI smoke): test_overlay_shows_executed_highlight (passing)
- [x] P2.6 Unit tests (GUI) skip-if-headless: test_agent_inspector_last_trade_placeholder (implemented within existing inspector test suite)
- [x] P2.7 Docs: README GUI section add bilateral exchange subsection
- [x] P2.8 API_GUIDE experimental flags appendix updated (EXEC, DRAFT, GUI_INFO)

## Phase 3: Priority & Fairness (Flagged Enhancements)
- [x] P3.1 Implement ECONSIM_TRADE_PRIORITY_DELTA flag switching priority to (-ΔU, seller_id, buyer_id, give_type, take_type)
- [x] P3.2 Implement fairness_round index incrementing on each executed trade (no behavior yet)
- [x] P3.3 Unit test: test_priority_delta_flag_reorders_intents
- [x] P3.4 Unit test: test_fairness_round_increments
- [x] P3.5 Docs: Add fairness & priority flag rationale to summary
	- Added multiset invariance test and autouse env-clearing fixture (hardening determinism & isolation)

## Phase 4: Evidence & Polishing
- [x] P4.1 Capture perf JSON baseline/draft/exec/gui-info (see tmp_perf_trade_*.json outputs)
- [x] P4.2 Overlay summary text captured (headless run produced no executed trade in sample scenario; logic validated via tests)
- [x] P4.3 Inspector integration validated via runtime toggle & last trade tests (text evidence; no screenshot required for headless CI)
- [x] P4.4 Determinism hash parity report (baseline vs exec hash) recorded in GATE_BILATERAL2_EVAL.md
- [x] P4.5 README Known Gaps updated referencing multi-trade & fairness scheduling future work
- [x] P4.6 Gate evaluation narrative (GATE_BILATERAL2_EVAL.md) finalized
- [x] P4.7 Cross-reference to Bilateral2 outcomes will be appended to Bilateral1 checklist in later documentation sweep (deferred note)

## Risks & Mitigations
- Overlay Overdraw: Limit highlight operations to O(1) additional draws.
- Metric Overhead: Only constant-time increments; no per-frame list growth.
- GUI Inspector Absence: Provide fallback text / skip tests when feature flag or component missing.
- Determinism Drift: Keep new metrics excluded from hash; priority change gated.

## Exit Criteria
- All Phase 1–3 tasks complete (priority flag optional but implemented).
- No FPS drop below 30 in worst-case small-grid many-intents scenario.
- Determinism hash unchanged with all new flags off.
- Documentation & evaluation artifacts captured.

-- END --
