# Market Implementation Planning – Constructive Criticism & Decision Checklist

Date: 2025-09-23
Source Plan: `tmp_plans/Market Implementation Planning.md`
Scope: Focused on gaps, ambiguities, and pre‑implementation decision points for Phases A–C (endowments, bilateral exchange, marketplace).

---
## A. Endowment Distribution (Section 3)
**Gaps / Clarifications Needed**
- Middle_class & hollowed_out_middle: Need explicit algorithm for group sizing across arbitrary n (rounding order, no overlap). Provide pseudo-code.
- Minimum guarantee (raise zeros to 1) can distort intended heavy-tail (oligarchic) proportions. Confirm acceptability or add `allow_zero` config.
- Total units per good fixed at T = n * E. Consider separate `endowment_total_units_per_good` override for pedagogy (varying average wealth).
- RNG fallback for fractional ties mentioned—decide if strictly deterministic ordering by (fractional_part desc, agent_id asc) is sufficient (probably yes) and remove RNG branch.
- Multi-good future: Currently identical distribution applied to each good; note whether we’ll later allow per-good pattern (e.g., capital vs consumption).
- Immediate withdrawal ordering: Must occur after agent creation but before first `Simulation.step` to keep hash semantics stable—explicitly document call site.

**Decisions Needed**
- D-Endow-1: Group sizing / rounding rule (proposed: compute target counts via round; if Σ ≠ n adjust by trimming/adding at group boundaries with deterministic priority: Middle -> Top -> Bottom or defined order).
- D-Endow-2: Remove RNG fallback for fractional ties? (Yes/No)
- D-Endow-3: Permit zero allocations? (Yes enables poverty scenarios; No keeps all agents active initially.)
- D-Endow-4: Introduce configurable total units T independent of E? (Yes/No)
- D-Endow-5: Keep single pattern for both goods in Phase A? (Yes/No)

---
## B. Utility Aggregation (Section 4)
**Gaps**
- Call sites not enumerated: list all current invocations of preference utility (for replacement or wrapping).
- Need to define signature & immutability of `total_inventory_counts()` (tuple vs object).
- ΔU calculation for marginal utilities: specify exact helper (avoid repeated full utility recalculation if expensive).
- Determinism hash impact: baseline unaffected; new modes must ensure aggregation change doesn’t leak into baseline path.

**Decisions**
- D-Util-1: Add boolean flag (e.g., `simulation.uses_total_inventory`) vs inline mode check.
- D-Util-2: Implement caching of last total counts + utility now or defer.
- D-Util-3: Marginal utility method name & contract (e.g., `preference.marginal_utility(bundle, good_id)`?).

---
## C. Bilateral Exchange Mechanics (Section 5)
**Gaps**
- Partner selection O(n) per agent → worst case O(n^2). Acceptable for expected small n? Need threshold for future optimization.
- Greedy axis movement may cause swapping or oscillation; need anti-swap rule (e.g., only lower id moves if both would swap positions).
- Trade termination condition if no mutual gains: confirm immediate mark `traded_with[target]=True`.
- Marginal utility definition & step granularity (one unit). Edge case: both agents lacking required goods → skip & mark? Retries?

**Decisions**
- D-Bilat-1: Collision / swap prevention rule.
- D-Bilat-2: Max attempts per partner (guard) or rely on immediate mark-if-no-trade.
- D-Bilat-3: Strictly 1 unit per successful trade per frame? (Yes/No)
- D-Bilat-4: Pathfinding complexity upgrade trigger (e.g., n > threshold).

---
## D. Market Exchange Mechanics (Section 6)
**Gaps**
- Price formula uses sum of marginal utilities: need explicit function; ensure consistent ordering of goods.
- Price representation unresolved: float with fixed rounding vs rational pair (num, denom).
- Initial market inventory seeding unspecified (quantities, goods, deterministic seed usage).
- Exit rule: confirm idle_consec resets after any successful trade.
- Sequential resolution: late agents may face depleted inventory—pedagogical intent? Possibly highlight first-mover advantage; if not, consider virtual batch.
- Trade direction tie: if both A/B ratios suggest action simultaneously, define priority.

**Decisions**
- D-Market-1: Price storage (rational pair vs fixed-scale int vs rounded float).
- D-Market-2: Initial inventory seeding rule (e.g., 1 unit each good + maybe seed-weighted extras).
- D-Market-3: Idle counter reset on trade? (Yes/No)
- D-Market-4: Tie-breaking for dual-direction signals.
- D-Market-5: One trade per agent per step? (Yes/No)
- D-Market-6: Depletion fairness strategy (sequential as-is vs batch compute then apply).

---
## E. Snapshot / Serialization (Section 7)
**Gaps**
- Append order not locked (critical for hash stability). Suggest order now.
- Bitmask spec lacking: confirm LSB = agent id 0.
- Whether to include `endowment_distribution` immediately or defer until GUI implemented.
- Price persistence redundancy: store only rational form or rational + derived float.
- Backward compatibility default values for newly added fields (mode=baseline, no marketplace, zero bitmask).

**Decisions**
- D-Snap-1: Field append order (proposed list below).
- D-Snap-2: Include distribution pattern field now? (Yes/No)
- D-Snap-3: Price storage format.
- D-Snap-4: Bitmask packing order confirmation.

*Proposed Append Order* (after existing baseline fields):
1. mode
2. endowment_distribution (if immediate)
3. bilateral_traded_with_bitmask[] (array or per-agent int)
4. marketplace_inventory (sorted keys)
5. marketplace_price_num
6. marketplace_price_den
7. agent_market_phase_counters (if needed)

---
## F. Performance & Determinism (Sections 8–9)
**Gaps**
- Complexity summary table missing (allocation O(n log n), bilateral worst O(n^2), market price O(n)).
- Explicit statement that no additional RNG calls are made per step (except potential future features) should be codified.
- Need test ensuring two identical seeds produce identical endowment vector across all four patterns.

**Decisions**
- D-Perf-1: Accept O(n^2) bilateral for current scale? Provide cutoff.
- D-Perf-2: Allocate micro-optimization backlog item (defer spatial index until n > threshold).

---
## G. GUI Additions (Section 11)
**Gaps**
- Location of distribution dropdown (Start Menu only vs runtime). Mid-run changes would violate determinism unless disallowed.
- Marketplace visual marking scheme (color overlay? cell border?).
- Price overlay formatting (ratio vs decimal vs both).
- Tooltips / explanatory text for educational framing.

**Decisions**
- D-GUI-1: Dropdown scope (Start Menu only?).
- D-GUI-2: Overlay format (e.g., “Price A:B = 5:4 (1.25)” ).
- D-GUI-3: Marketplace visual style.
- D-GUI-4: Allow changing mode mid-simulation? (Probably No.)

---
## H. Testing Plan (Section 10)
**Gaps**
- Add tests for each distribution shape verifying share proportions within integer rounding tolerance.
- Add inequality metric test (optional) comparing Gini ordering: uniform < middle_class < hollowed_out_middle < oligarchic.
- Test immediate withdrawal: post-initialization home inventory == 0.
- Test bilateral oscillation prevention (agents do not swap infinitely).
- Test deterministic price sequence across two runs.

**Decisions**
- D-Test-1: Adopt inequality metric now or later.
- D-Test-2: Rounding tolerance (suggest ±1 unit from ideal per agent, aggregated exact total).

---
## I. Edge & Failure Handling
**Gaps**
- Very small n causing overlapping group definitions: need deterministic merge rule (e.g., compute sets, union collisions, then renormalize weights uniformly within surviving groups).
- Oligarchic with E=1: top share compression; ensure min guarantee logic doesn’t inflate bottom beyond intended share proportions (document expected distortion).
- Market trade partial feasibility: If market lacks one side, trade skipped or partial? Clarify (current spec implies skip).
- Flat preference (equal marginal utilities) — agents should not churn; need rule to skip trade attempts when ΔU ≤ 0 for both goods.

**Decisions**
- D-Edge-1: Skip vs partial trade when inventory insufficient.
- D-Edge-2: Behavior when all marginal utilities equal (halt trading vs continue scanning).

---
## J. Metrics / Analytics (Not Yet Covered)
**Opportunities**
- Track inequality (Gini or Theil) over time per mode for educational dashboards.
- Track trade count per agent, average price, wealth distribution snapshot after phase.
- Could add optional metrics collector hook (O(n)).

**Decisions**
- D-Metrics-1: Implement inequality metrics in Phase A or defer.
- D-Metrics-2: Include price stats in metrics (min/max/avg) now or defer.

---
## K. Naming / Configuration
**Gaps**
- Final naming consistency: `mode`, `endowment_distribution`, `market_size`, `endowment_max_units`.
- Enum vs string literal: Enum improves clarity; string literal simpler snapshot diff (but both workable).

**Decisions**
- D-Config-1: Approve field names.
- D-Config-2: Enum vs str literal for mode & distribution.

---
## Consolidated Decision Matrix (Quick Reference)
| Code | Topic | Need | Your Choice |
|------|-------|------|-------------|
| D-Endow-1 | Group sizing rule | Algorithm | TBD |
| D-Endow-2 | Fractional tie RNG removal | Yes/No | TBD |
| D-Endow-3 | Zero allocations allowed | Yes/No | TBD |
| D-Endow-4 | Separate total units T | Yes/No | TBD |
| D-Endow-5 | Same pattern all goods | Yes/No | TBD |
| D-Util-1 | Aggregation flag location | Flag vs inline | TBD |
| D-Util-2 | Caching now | Yes/No | TBD |
| D-Util-3 | Marginal utility helper | Spec | TBD |
| D-Bilat-1 | Swap prevention | Rule | TBD |
| D-Bilat-2 | Max attempts | Yes/No | TBD |
| D-Bilat-3 | 1 unit per trade | Yes/No | TBD |
| D-Bilat-4 | Pathfinding upgrade trigger | Threshold | TBD |
| D-Market-1 | Price representation | Rational/Float | TBD |
| D-Market-2 | Initial inventory rule | Spec | TBD |
| D-Market-3 | Idle reset on trade | Yes/No | TBD |
| D-Market-4 | Dual-direction tie | Priority rule | TBD |
| D-Market-5 | Trades per step | 1 / many | TBD |
| D-Market-6 | Depletion fairness | Sequential/Batch | TBD |
| D-Snap-1 | Field append order | Approve | TBD |
| D-Snap-2 | Include distribution now | Yes/No | TBD |
| D-Snap-3 | Price storage | Format | TBD |
| D-Snap-4 | Bitmask ordering | Confirm | TBD |
| D-Perf-1 | Accept O(n^2) | Yes/No | TBD |
| D-Perf-2 | Spatial index threshold | n=? | TBD |
| D-GUI-1 | Dropdown location | Start only / runtime | TBD |
| D-GUI-2 | Price overlay format | Spec | TBD |
| D-GUI-3 | Marketplace marking | Spec | TBD |
| D-GUI-4 | Mode mutability | Yes/No | TBD |
| D-Test-1 | Inequality metric now | Yes/No | TBD |
| D-Test-2 | Rounding tolerance | Spec | TBD |
| D-Edge-1 | Partial trade handling | Skip/Partial | TBD |
| D-Edge-2 | Flat utility handling | Halt rule | TBD |
| D-Metrics-1 | Inequality metrics | Now/Defer | TBD |
| D-Metrics-2 | Price stats metrics | Now/Defer | TBD |
| D-Config-1 | Field names | Approve | TBD |
| D-Config-2 | Enum vs string | Choice | TBD |

---
## Suggested Implementation Order (Post-Decision)
1. Lock decisions (especially endowment & price representation).
2. Add config fields + enums (or literals) + append snapshot placeholders.
3. Implement deterministic endowment allocator (all four patterns) + tests.
4. Immediate withdrawal hook + test verifying home empty after step 0.
5. Utility aggregation gating + tests.
6. Bilateral skeleton: partner selection, movement, swap prevention; add trade rule.
7. Marketplace skeleton: inventory init, price calc, single-trade loop; overlay.
8. Snapshot field population; determinism/hash tests.
9. GUI Start Menu updates + endowment distribution dropdown.
10. Expanded metrics (optional) + docs & README update.

---
## Open Questions for You
Please fill in or respond inline for each decision code. Once resolved, we proceed with skeleton code generation while preserving determinism and minimal diff.

---
## Notes
- Keep initial diff small: introduce structures & flags before behavior loops.
- Avoid premature optimization; document thresholds.
- Determinism: no dynamic floating rounding—choose rational early if likely needed.
- Educational clarity > micro performance for Phase A.

End of document.
