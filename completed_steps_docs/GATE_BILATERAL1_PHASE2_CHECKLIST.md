# Gate Bilateral1 – Phase 2 Review Checklist

Goal: Draft enumeration of trade intents (no execution) under feature flag without affecting determinism hash or performance floor.

## 1. Scope Verification
- [x] `TradeIntent` dataclass introduced with deterministic priority tuple.
- [x] Enumeration function `enumerate_intents_for_cell` added (O(k) for cell agents, k<=cell population).
- [x] Integrated enumeration into `Simulation.step` behind `ECONSIM_TRADE_DRAFT=1`.
- [x] Debug overlay helper renders first N intents (N=3) only when flag active and intents exist.
- [x] No mutation of agent inventories or other state during enumeration.

## 2. Determinism Safeguards
- [x] No RNG usage in enumeration logic.
- [x] Ordering enforced by sorting over priority tuple.
- [x] Determinism hash parity test (`test_draft_hash_parity`) passes.
- [x] Added metrics counters excluded from hash (confirmed by unchanged hash string).

## 3. Performance Considerations
- [x] Co-location map built in O(agents).
- [x] No per-frame allocations beyond transient intent list (discarded when flag off).
- [x] Overlay rendering limited to <=3 blits/text lines.

## 4. Testing Coverage
- [x] No-intents scenario (no co-location).
- [x] Co-located generation with ordering assertion.
- [x] Hash parity with/without flag.
- [x] Overlay smoke (flag on) idempotence check.
- [x] Overlay noop (flag off) safety.

## 5. Code Quality / Lint
- [x] Typing clarified in `world.py` (trade_intents None vs list lifecycle).
- [x] Overlay helper protocols refactored; removed unused imports.

## 6. Documentation
- [x] Phase 2 summary document present (`Gate_Bilateral1_phase2_summary.md`).
- [x] Planned future phases enumerated (execution, ΔU integration, metrics promotion).
- [x] Invariant (only carrying goods tradable) already documented in core instructions.

## 7. Risk Review
- [x] Risks & mitigations captured in summary doc.

## 8. Acceptance Criteria
All boxes checked → Phase 2 READY for gate sign-off.

Sign-off:
- Reviewer: __________________ Date: __________

Notes:
- Proceed to Phase 3 only after explicit stakeholder approval.
