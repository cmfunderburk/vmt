# Market Implementation Planning – Final Pass Review (Consistency & Gaps)

Source Documents Reviewed:
- Market Implementation Planning.md (original / evolving)
- market_implementation_criticism.md
- Locked decision records (Endowment D-*, Money Mode M1–M12, additional D-* sets)

Purpose: Consolidate outstanding concerns, identify inconsistencies, enumerate required final confirmations before implementation.

---

## 1. Endowment Distribution
Conflict: Original text includes “Minimum guarantee” (raise zeros). Decision D-Endow-3 locks allowing zeros.
Resolved (R1 Adopted): Remove guarantee step; explicit: zeros permitted; no redistribution after apportionment.
RNG Fallback: Original mentions RNG for fractional ties; D-Endow-2 removed RNG.
Resolved (R2 Adopted): Delete RNG fallback references; clarify ordering only (-fractional_part, group priority).

Home vs Carry: Immediate withdrawal leaves home=0 post-step0 yet later prose implies potential home inventory nuance.
Resolved (R3 Adopted): Clarify sales/utility-loss logic references carrying only (home=0 early phase).

---

## 2. Market (Legacy Ratio) vs Money Mode
Earlier “Market Exchange” (barter ratio) decisions (D-Market-5/6) superseded by Money Mode M1–M12.
Resolved (R4 Adopted): Barter section marked DEPRECATED (historical only); canonical path = Money Mode (numeraire). Close D-Market-5/6 referencing supersession by M6–M12.

---

## 3. Money Distribution Consistency
M3: uniform initial_agent_money=5.
M4: pattern-based (reuse endowment weights; total = n*5).
Decision (R5 Pattern Chosen): Adopt pattern-based distribution (teaching inequality); document scaling rule and determinism ordering.

---

## 4. Price History Ambiguity
M8 accepted “history=yes” (store price history). M10 (Option 2) only logs current prices (no history).
Decision (R6 Store List): Implement price_history list inside economy (memory O(steps)); will add gating note if memory becomes concern.

---

## 5. Snapshot Schema Alignment
M9: Single appended `economy` dict; earlier docs still list discrete marketplace fields (ratio mode).
Resolved (R7 Confirmed): Replace old snapshot additions with: append `economy` dict (mode, kappa, anchor_good, price_scale, prices, price_history, market_money, agent_money, blocked_sales). Barter fields omitted intentionally. Ordering: existing legacy fields → (if bilateral) bilateral_traded_with bitmask (planned, gated) → (if money) economy.

---

## 6. Utility Aggregation Wording
Unified Statement (R8 Adopted): When uses_total_inventory flag true (bilateral, money), utility aggregates home+carrying; baseline mode uses carrying only unless a deposit action (future) mutates home. Home remains zero post-initial withdrawal in current phases, so bilateral execution draws exclusively from carrying.

---

## 7. Performance Exception Declaration
Performance (R9 Adopted): Explicitly allowed O(n log n) step: Money-mode sale ordering (M12). All other new features must remain O(agents+resources) unless separately gated.

---

## 8. Utility-Loss Ordering Scale
Loss Scaling (R10 Adopted): Define LOSS_SCALE = 1_000_000_000 for deterministic integer sorting of utility-loss. Changing value is hash-impacting and requires determinism gate review.

---

## 9. Marginal Utility / Loss Helpers
Utility Math (R11 Adopted): Path reserved `simulation/util_math.py` (future implementation). Will contain:
- marginal_utility(...)
- utility_loss_if_remove(...)
NOTE: Avoid duplication with existing `preferences/helpers.py`; centralization occurs when money mode implementation begins.

---

## 10. Metrics Invariants
Metrics / Invariants (R12 Adopted):
- Anchor price invariant: price[anchor_good] == price_scale each step.
- Conservation: sum(agent_money) + market_money constant (initial endowment total).
- Conditional segment: economy dict only present when mode == money.
Future tests: test_price_anchor_invariant, test_money_conservation.

---

## 11. Sale Candidate Preconditions
Sale Candidate Precondition (R13 Adopted): Only goods with quantity >0 create sale candidate; zero-quantity goods skipped, preventing artificial blocked counts.

---

## 12. Spatial Marketplace Requirement
Spatial Requirement (R14 Keep): Retain 2x2 central marketplace presence requirement for money-mode trades (movement gating preserved). Rationale: pedagogical emphasis on congestion & spatial friction. Document deterministic identification of central area. (Future flag could relax.)

---

## 13. Additional Test Coverage
Planned Test Additions (R15 Adopted):
- test_money_conservation
- test_sale_ordering_utility_loss
- test_price_anchor_invariant
- test_money_distribution_pattern (pattern-based distribution confirmed)
All to be added prior to enabling money mode execution gate.

---

## 14. Base Mode Naming Consistency
Naming Consistency (R16 Adopted): Canonical label: “baseline mode” (replace any “basic”).

---

## 15. GUI Display Labels
GUI Labels (R17 Adopted): “Bilateral Exchange” and “Money Market Exchange” as user-facing mode names.

---

## Summary Decision Table

| Ref | Topic | Resolution |
|-----|-------|-----------|
| R1 | Remove min guarantee step | Adopted |
| R2 | Remove RNG tie fallback text | Adopted |
| R3 | Clarify home=0 carrying-only | Adopted |
| R4 | Deprecate barter section | Adopted |
| R5 | Money distribution pattern | Adopted (Pattern) |
| R6 | Store price history list | Adopted (Store) |
| R7 | Snapshot ordering | Confirmed |
| R8 | Unified utility aggregation | Adopted |
| R9 | O(n log n) exception | Adopted |
| R10 | LOSS_SCALE constant | Adopted (1e9) |
| R11 | util_math.py path | Adopted |
| R12 | Metrics invariants | Adopted |
| R13 | Qty>0 candidate rule | Adopted |
| R14 | Keep spatial 2x2 | Adopted |
| R15 | Planned tests list | Adopted |
| R16 | Label “baseline” | Adopted |
| R17 | GUI labels set | Adopted |

---

## Recommended Defaults (If You Prefer One-Shot Acceptance)
R1 Yes, R2 Yes, R3 Yes, R4 Yes, R5 Pattern (if teaching inequality with money), R6 A, R7 Confirm, R8 Yes, R9 Yes, R10 Yes (1_000_000_000), R11 Confirm, R12 Yes, R13 Yes, R14 Drop, R15 Yes, R16 baseline, R17 (“Bilateral Exchange”, “Money Market Exchange”)

Provide your selections and we will patch the planning docs accordingly before coding.
