# Gate MoneyMode Planning Snapshot

Date: 2025-09-24
Scope: Consolidated resolutions (R1–R17) prior to implementing Money Mode atop existing bilateral exchange foundation.

## Bilateral Context
Bilateral Phase 3 (single reciprocal marginal utility swap, carrying-only) completed with hash parity. Money Mode will layer market pricing & sale ordering without altering bilateral invariants unless explicitly gated.

## Resolutions Summary
- R1 Zeros allowed in endowment; no minimum guarantee.
- R2 Removed RNG tie fallback; deterministic ordering only.
- R3 Home=0 after withdrawal; sale / marginal logic uses carrying.
- R4 Barter (ratio) market deprecated (historical only).
- R5 Money distribution: Pattern-based (reuse endowment weights; total n*5).
- R6 Price history retained (store list each step) – memory O(steps); revisit if perf issue.
- R7 Snapshot ordering: legacy fields → (optional) bilateral_traded_with bitmask (future) → (optional) economy dict.
- R8 Utility aggregation: if mode uses_total_inventory (bilateral, money) then home+carrying else carrying only.
- R9 Allowed O(n log n): Money-mode sale ordering (M12); no other complexity escalations without gate.
- R10 LOSS_SCALE = 1_000_000_000 (hash-impacting if changed).
- R11 Reserve `simulation/util_math.py` for marginal_utility & utility_loss_if_remove (to migrate from preferences helpers where needed).
- R12 Metrics invariants: anchor price fixed; money conserved; economy segment conditional.
- R13 Sale candidate requires qty>0.
- R14 Spatial constraint: Keep 2x2 central marketplace requirement for money trades.
- R15 Planned tests: money_conservation, sale_ordering_utility_loss, price_anchor_invariant, money_distribution_pattern.
- R16 Canonical name: baseline mode.
- R17 GUI labels: “Bilateral Exchange”, “Money Market Exchange”.

## Implementation Checklist (Pre-Code Gate)
1. Define constants: LOSS_SCALE, central marketplace coordinates helper.
2. Add snapshot append rules (economy dict & optional bitmask placeholder) ensuring append-only ordering.
3. Implement util_math functions (pure) with tests (marginal_utility parity vs existing).
4. Implement pattern-based money distribution (deterministic order) + test.
5. Add price history accumulation (list append each step) + gating for memory disable toggle (optional env flag ECONSIM_PRICE_HISTORY=0?).
6. Implement sale candidate generation (qty>0) and utility-loss calculation using LOSS_SCALE.
7. Sorting & execution of sales (single pass O(n log n)) with invariants tests.
8. Metrics updates (anchor, conservation checks in tests only; not hash enforced yet).
9. GUI labeling & optional mode selector wiring.
10. Update documentation & determinism hash note if new fields added.

## Determinism / Hash Policy
- New counters and price history excluded from hash until stability review.
- Snapshot field order change prohibited; only append at tail as defined.
- LOSS_SCALE alteration requires determinism gate.

## Open Risks / Watch Items
- Price history memory growth: add max length or compression if scenario durations large.
- Spatial constraint could bottleneck trades; consider future flag to relax vs. congestion pedagogy value.
- Interaction between bilateral and money mode: ensure mutual exclusivity or explicit precedence.

## Next Gate Trigger
Proceed to implementation only after this snapshot is acknowledged by stakeholders and a Gate document (Gate_MoneyMode_todos.md) created referencing each checklist item.

Reviewer Sign-off:
- Name: __________________ Date: __________
