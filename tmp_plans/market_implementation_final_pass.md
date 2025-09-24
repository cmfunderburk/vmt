# Market Implementation Planning – Final Pass Review (Consistency & Gaps)

Source Documents Reviewed:
- Market Implementation Planning.md (original / evolving)
- market_implementation_criticism.md
- Locked decision records (Endowment D-*, Money Mode M1–M12, additional D-* sets)

Purpose: Consolidate outstanding concerns, identify inconsistencies, enumerate required final confirmations before implementation.

---

## 1. Endowment Distribution
Conflict: Original text includes “Minimum guarantee” (raise zeros). Decision D-Endow-3 locks allowing zeros.
Action Needed (R1): Remove guarantee step; replace with explicit “zeros permitted; no redistribution after apportionment.”
RNG Fallback: Original mentions RNG for fractional ties; D-Endow-2 removed RNG.
Action Needed (R2): Delete RNG fallback references; clarify ordering only (-fractional_part, group priority).

Home vs Carry: Immediate withdrawal leaves home=0 post-step0 yet later prose implies potential home inventory nuance.
Action Needed (R3): Clarify sales/utility-loss logic references carrying only (home=0 early phase).

---

## 2. Market (Legacy Ratio) vs Money Mode
Earlier “Market Exchange” (barter ratio) decisions (D-Market-5/6) superseded by Money Mode M1–M12.
Action Needed (R4): Mark barter section DEPRECATED (historical only); canonical path = Money Mode (numeraire).
Close D-Market-5/6 referencing supersession by M6–M12.

---

## 3. Money Distribution Consistency
M3: uniform initial_agent_money=5.
M4: pattern-based (reuse endowment weights; total = n*5).
Need Choice (R5): Keep pattern-based (document scaling rule) OR revert to uniform.

---

## 4. Price History Ambiguity
M8 accepted “history=yes” (store price history). M10 (Option 2) only logs current prices (no history).
Need Choice (R6):
A) Adjust M8 → history=no (simplify).
B) Implement price_history list inside economy (memory O(steps)).

---

## 5. Snapshot Schema Alignment
M9: Single appended `economy` dict; earlier docs still list discrete marketplace fields (ratio mode).
Action Needed (R5 already used; continue numbering): (R7) Replace old snapshot additions with: append `economy` dict (mode, kappa, anchor_good, price_scale, prices, market_money, agent_money, blocked_sales). Note barter fields omitted intentionally.
Bilateral bitmask ordering: Plan to append `bilateral_traded_with` (if bilateral mode) BEFORE `economy`.
Need Confirmation (R7): Order = existing legacy fields → (if bilateral) bilateral_traded_with → (if money) economy.

---

## 6. Utility Aggregation Wording
Need unified statement: “When uses_total_inventory flag true (bilateral, money), utility uses home+carrying; baseline uses carrying unless deposit changes home.”
Action Needed (R8): Replace fragmented descriptions with single invariant.

---

## 7. Performance Exception Declaration
M12 introduces O(n log n) (sorting by utility-loss) while D-Perf-1=B disallows uncontrolled O(n^2) but silent on sorts.
Action Needed (R9): Explicitly list allowed O(n log n): “Money-mode sale ordering (M12).”

---

## 8. Utility-Loss Ordering Scale
M12: Must freeze scaling constant for converting float loss to int for deterministic sort.
Action Needed (R10): Define LOSS_SCALE = 1_000_000_000; document changing it is hash-impacting.

---

## 9. Marginal Utility / Loss Helpers
Decision: pure function + agent wrapper (D-Util-3).
Action Needed (R11): Assign path `simulation/util_math.py` with:
- marginal_utility(...)
- utility_loss_if_remove(...)

---

## 10. Metrics Invariants
Need explicit invariants to aid regression:
- price_g1 == price_scale (anchor).
- total_agent_money + market_money constant each step.
- M segment absent if mode != money.
Action Needed (R12): Add these invariants.

---

## 11. Sale Candidate Preconditions
Clarify: Only goods with quantity >0 create sale candidate (prevents spurious blocked counts).
Action Needed (R13): Document explicitly.

---

## 12. Spatial Marketplace Requirement
Original barter design referenced 2x2 central area; Money Mode decisions ignore spatial constraint.
Need Choice (R14):
A) Drop spatial requirement (trade anywhere).
B) Retain 2x2 presence requirement (adds movement gating).

---

## 13. Additional Test Coverage
Pending additions if not already listed:
- test_money_conservation
- test_sale_ordering_utility_loss
- test_price_anchor_invariant
- test_money_distribution_pattern (only if pattern-based retained)
Action Needed (R15): Confirm inclusion.

---

## 14. Base Mode Naming Consistency
Docs alternate “baseline” vs “basic.”
Need Choice (R16): Select canonical label (recommend “baseline” for existing references) and update all mentions.

---

## 15. GUI Display Labels
Need final user-facing names:
- Bilateral Exchange
- Money Market Exchange (suggested)
Action Needed (R17): Confirm or adjust labels.

---

## Summary Decision Table

| Ref | Topic | Pending Decision |
|-----|-------|------------------|
| R1 | Remove min guarantee step | Yes/No |
| R2 | Remove RNG tie fallback text | Yes/No |
| R3 | Clarify home=0 post-withdrawal sale logic | Yes/No |
| R4 | Deprecate barter market section | Yes/No |
| R5 | Money distribution approach | Pattern / Uniform |
| R6 | Price history storage | A=no history / B=store |
| R7 | Snapshot append ordering final | Confirm/Adjust |
| R8 | Unified utility aggregation statement | Yes/No |
| R9 | Declare O(n log n) exception (M12) | Yes/No |
| R10 | LOSS_SCALE constant inclusion | Yes/No (value?) |
| R11 | Helper file path util_math.py | Confirm/Adjust |
| R12 | Metrics invariants doc | Yes/No |
| R13 | Candidate requires qty>0 doc | Yes/No |
| R14 | Spatial marketplace requirement | Drop / Keep |
| R15 | Add test cases list | Yes/No |
| R16 | Canonical base mode label | baseline / basic |
| R17 | GUI labels | Confirm/Adjust |

---

## Recommended Defaults (If You Prefer One-Shot Acceptance)
R1 Yes, R2 Yes, R3 Yes, R4 Yes, R5 Pattern (if teaching inequality with money), R6 A, R7 Confirm, R8 Yes, R9 Yes, R10 Yes (1_000_000_000), R11 Confirm, R12 Yes, R13 Yes, R14 Drop, R15 Yes, R16 baseline, R17 (“Bilateral Exchange”, “Money Market Exchange”)

Provide your selections and we will patch the planning docs accordingly before coding.
