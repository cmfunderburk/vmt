# Gate 7 Critical Issues & Alignment Gaps (Trading Primitives vs Market Planning)

Date: 2025-09-24
Purpose: Identify blocking or high-risk misalignments between the lightweight Gate 7 trading scope (`Gate_7_todos.md`) and the broader Market / Money Mode planning documents (`Market Implementation Planning.md`, `market_implementation_criticism.md`, `market_implementation_final_pass.md`). These must be resolved or explicitly deferred before implementation to prevent architectural churn or determinism regressions.

## 1. Scope Creep Risk
- Gate 7 Todos define a minimal bilateral trade (single-cell co-location, 1-unit swap) while market planning documents introduce extensive concepts (endowment distributions, marketplace pricing, money mode, quasi-linear utility, M1–M12 decisions).
- Risk: Blending money mode primitives early would explode surface area (snapshot, metrics, config) and destabilize hash baselines.
- Action: CONFIRM Gate 7 remains strictly “flagged bilateral exchange only” (no endowments/money/prices) OR explicitly retitle Gate 7 to include foundations (endowment allocator + aggregation) if those are prerequisites for teaching outcomes.

## 2. Inconsistent Trading Interaction Model
- Gate 7 plan: trade only when same cell; Market doc Phase B bilateral design expects path-to-adjacency, partner scanning, and per-partner completion tracking (bitmask).
- Divergence: adjacency vs co-location; partner memory absent in minimal Gate 7 spec.
- Consequence: Later migration to adjacency + partner bitmask will alter step semantics & potentially hashes.
- Decision Needed: Adopt adjacency + partner set now (with simplified rule) OR declare co-location a deliberately simpler educational mode (distinct scenario name) to avoid rework.

## 3. Endowment & Utility Aggregation Timing
- Market plans assume deterministic initial endowments + immediate withdrawal + utility computed over total ownership for new modes.
- Gate 7 minimal spec ignores endowment distributions entirely.
- Risk: Adding trading now without the endowment mechanism could require rewriting tests for endowment-influenced marginal utilities later.
- Decision: Introduce endowment allocator behind a disabled config (future gate) or postpone any trading that depends on initial inequality signals.

## 4. Snapshot Evolution Order
- Market decisions (R7 / M9) propose adding namespaced `economy` dict and optional bilateral bitmask fields.
- Gate 7 spec currently does not reserve append order nor mention future field placement.
- Risk: Implementing trading now and appending fields later could force reorder or dual-phase snapshot adjustments (hash churn).
- Action: Pre-reserve append order even if fields left empty (e.g., append placeholder `trading` key with minimal schema when flag enabled). Decide before implementing serialization changes.

## 5. Determinism & Complexity Guarantees
- Gate 7 commits to O(agents + resources); Market plan bilateral partner search may degrade to O(n^2) if naive.
- Current Gate 7 tasks rely on per-cell grouping → O(n). Market document expects nearest partner selection (requires broader search) → potential escalation.
- Decision: Lock Gate 7 bilateral algorithm to local co-location OR implement nearest-partner with documented complexity and perf test guard.

## 6. Metrics Hash Stability vs Extensions
- Gate 7 optional metrics fields (trades_executed, units_exchanged_*) may become obsolete or need renaming once money mode metrics (M10) arrive.
- Risk: Early metrics naming may require compatibility shims later.
- Action: Either (A) skip adding trade metrics in Gate 7 or (B) namespace metrics fields (prefix trade_) so future economy metrics remain cleanly separated.

## 7. Utility Function Consistency
- Market plans define aggregated inventory utility in special modes; Gate 7 currently silent (implies carry-only). Changing to aggregated later changes ΔU and may retroactively alter expected trade test outcomes.
- Decision: Explicitly state Gate 7 uses carrying-only utility AND that future modes may override via `uses_total_inventory` flag to avoid back-compat confusion.

## 8. RNG Partitioning Discipline
- Market decisions introduce additional derived seeds (e.g., +5001 / +5003). Gate 7 adds none.
- Risk: Introducing new derived seeds later without prior reservation may appear as “new randomness” in determinism audits.
- Action: Reserve a documented seed offset namespace table now (even if unused in Gate 7) in planning docs.

## 9. Testing Coverage Gaps
Missing (relative to market doc expectations):
- inequality / endowment determinism tests (if deferred)
- partner non-oscillation test (swap-prevention rule) — needed if adjacency added
- snapshot parity with trading flag disabled (explicit baseline test)
- performance regression test with synthetic dense trade scenario to bound overhead

Recommendation: Add at least (a) snapshot-disabled parity test, (b) determinism on/off comparison, (c) conservation invariant, (d) perf micro-benchmark.

## 10. Naming & Mode Explosion Risk
- Proposed future modes: bilateral_exchange, market_exchange, money. Gate 7 adds generic trading; risk of later renaming causing config diff churn.
- Action: Name Gate 7 mode precisely (e.g., `bilateral_simple`) to avoid semantic collision with richer future `bilateral_exchange` spec.

## 11. Deferred Decision Tracking Drift
- Market criticism & final pass documents enumerate many locked decision codes; Gate 7 docs ignore them, risking forgotten commitments (e.g., LOSS_SCALE, price representation) when later gates implemented.
- Action: Add a “Deferred External Decisions Table” section in Gate 7 eval scaffolding referencing which D-/M- codes are explicitly out-of-scope but acknowledged.

## 12. Documentation Synchronization Risk
- Copilot instructions currently list allowed fast paths; trading addition must clarify that partner search remains O(n) and is flag-gated.
- Action: Plan an update to `.github/copilot-instructions.md` concurrently with trading merge to add a single bullet and avoid drift.

## 13. Serialization Backward Compatibility Test Strategy
- No plan yet for cross-version snapshot replay when trading fields are introduced.
- Action: Pre-create a legacy snapshot fixture (Gate 6 baseline) to ensure loading under Gate 7 (trading disabled) still works.

## 14. Metrics Collector Coupling
- Adding trade metrics directly to existing collector risks coupling; Market plan suggests separate economy metrics namespace.
- Action: Introduce minimal adapter pattern (e.g., `record_trading(step, sim)` returning dict) aggregated into metrics only if flag enabled; reduces internal collector churn later.

## 15. GUI Increment Minimization
- Gate 7 tasks currently do not specify UI elements; market planning contemplates scenario selection expansions.
- Risk: Adding scenario selection plumbing now might preempt later unified scenario picker refactor.
- Action: Implement headless/flag path first; postpone GUI addition until after logic + tests stable.

## 16. Partner Data Structure Future-Proofing
- Market plan references bitmask for `traded_with`; Gate 7 minimal approach may skip storing history entirely.
- Risk: Later adding bitmask changes per-step memory & possibly hash if serialized.
- Action: Optionally store a zeroed bitmask from the start (even if not functionally used) when trading enabled to establish stable schema early.

## 17. Performance Budget Transparency
- No explicit target set for trading overhead (just <5%). Need concrete acceptance number & agent/resource test scale (e.g., 50 agents / 150 resources, overhead <3%).
- Action: Define numeric target now to prevent ambiguous perf regressions.

## 18. Consistency with Decision Tie-Break Ordering
- Trading partner or exchange ordering must not introduce a new tie-break variant (ensure reuse of existing (-ΔU, distance, x, y) logic where applicable or clearly segregate a new ordering spec).
- Action: Document explicit ordering key for trade candidate resolution (e.g., (agent_id, target_agent_id)).

## 19. Hash Stability Communication
- Need explicit statement: enabling trading flag changes hash only when an exchange actually occurs; inert if no eligible partners.
- Action: Include in Gate 7 eval doc under Hash Samples section.

## 20. Risk of Mixing “Money Mode” Concepts Prematurely
- Money mode decisions (M1–M12) introduce price, money, anchors—none should leak into Gate 7 code comments or placeholders to avoid early coupling.
- Action: Ensure Gate 7 code references only trading primitives; create a separate `economy/` package later for money logic.

---
## Recommended Resolution Actions (Prioritized)
1. LOCK minimal scope (Issue 1) & rename mode to `bilateral_simple` (Issue 10).
2. Reserve snapshot field ordering & optional bitmask placeholder (Issues 4 & 16).
3. Add seed offset reservation table (Issue 8) in planning doc.
4. Update Gate 7 eval scaffold with deferred decision table (Issue 11) & hash impact statement (Issue 19).
5. Define perf test scale + numeric threshold (Issue 17) (e.g., 50 agents / 120 resources; overhead ≤3%).
6. Decide co-location vs adjacency now (Issue 2) and document chosen ordering key (Issue 18).
7. Add baseline legacy snapshot replay test plan (Issue 13).
8. Namespace future metrics or defer (Issues 6 & 14).
9. Document explicit layering: trading code isolated from money/economy (Issue 20).

Lower priority (after above resolved): finalize utility aggregation stance (Issue 7), partner data structure placeholder (Issue 16 if still desired), determinism statement for no-exchange scenario (Issue 19 already overlaps), and GUI defer rationale (Issue 15).

---
## Open Decisions (Need Confirmation)
| ID | Decision Needed | Proposed Default | Accept? (Y/N) |
|----|-----------------|------------------|---------------|
| D-G7-1 | Gate 7 scope excludes endowments & money mode | Yes (exclude) | |
| D-G7-2 | Mode name `bilateral_simple` | Yes | |
| D-G7-3 | Trade trigger condition (co-location vs adjacency) | Co-location (simpler) | |
| D-G7-4 | Introduce bitmask placeholder now | Yes (zeroed) | |
| D-G7-5 | Snapshot append reserved key order | agents/... existing → trading_bitmask[] (if) | |
| D-G7-6 | Perf benchmark scale & threshold | 50 agents / 120 resources / ≤3% FPS drop | |
| D-G7-7 | Metrics for trading in Gate 7 | Defer metrics (no new fields) | |
| D-G7-8 | Utility aggregation in Gate 7 | Carry-only (no aggregation) | |
| D-G7-9 | Seed offset reservation table | Add section (reserve +6001 for trading) | |
| D-G7-10 | GUI scenario exposure | Defer (flag only) | |
| D-G7-11 | Ordering key for trades | (agent_id, partner_id) ascending | |
| D-G7-12 | Hash behavior statement | Hash unchanged unless a trade executed | |

---
## Next Steps After Confirmation
1. Patch Gate 7 docs to integrate accepted decisions & remove ambiguous language.
2. Add reserved snapshot & seed sections.
3. Update Copilot instructions (single bullet) for trading flag constraints.
4. Begin skeleton implementation branch (no logic yet) with placeholder modules.

-- END --
