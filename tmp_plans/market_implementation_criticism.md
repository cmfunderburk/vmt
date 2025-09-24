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
| D-Endow-1 | Group sizing rule | Algorithm | LOCKED: Option A (largest remainder apportionment) + expressive priority ordering + contiguous ID block mapping |
| D-Endow-2 | Fractional tie RNG removal | Yes (remove RNG fallback) | LOCKED: Ties resolved deterministically by (-fractional_part, priority_rank, group ordering); no randomness introduced |
| D-Endow-3 | Zero allocations allowed | Yes (permit zeros; no minimum guarantee) | LOCKED: Preserve heavy-tail realism; rely on epsilon bootstrap for utility; future flag `ensure_minimum_endowment` possible |
| D-Endow-4 | Separate total units T | Yes/No | LOCKED: No separate field (Option A). T stays = n * E (appendable override deferred) |
| D-Endow-5 | Same pattern all goods | Yes (modified A) | LOCKED: Apply one pattern to both goods now; add explicit TODO scaffold for future per-good differentiation |
| D-Util-1 | Aggregation flag location | Flag vs inline | LOCKED: Simulation-level boolean `uses_total_inventory` set at construction based on mode |
| D-Util-2 | Caching now | Yes/No | LOCKED: Defer caching (Option A) – compute on demand; add backlog item for micro-opt if profiling justifies |
| D-Util-3 | Marginal utility helper | Spec | LOCKED: Implement pure function `marginal_utility(preference, g1, g2, good, epsilon=True)` + agent wrapper `agent_marginal_utility(good, use_total)` (no Preference API change) |
| D-Bilat-1 | Swap prevention | Rule | LOCKED: Lower-id precedence; if head-on swap detected only lower id moves, higher id stays |
| D-Bilat-2 | Max attempts | Yes/No | LOCKED: No max counter; immediate mark-if-no-mutual-gain (Option A) |
| D-Bilat-3 | 1 unit per trade | Yes/No | LOCKED: Yes (exactly 1 unit per successful trade per frame) |
| D-Bilat-4 | Pathfinding upgrade trigger | Threshold | LOCKED: Stay greedy (Option A); reconsider if n > 30 or obstacles are introduced |
| D-Market-1 | Price representation | Rational/Float | LOCKED: Scaled int ratio (Option B) price_num = round(((ΣMU_A+1)/(ΣMU_B+1))*SCALE), price_den = SCALE (SCALE=10000) |
| D-Market-2 | Initial inventory rule | Spec | LOCKED: Option D – seed 1 each good; if n >= 8 add +1 each (one-time at creation, no reseed) |
| D-Market-3 | Idle reset on trade | Yes/No | LOCKED: Yes (reset idle_consec=0 on trade); K=2 consecutive idle steps after min_stay=5 triggers exit |
| D-Market-4 | Dual-direction tie | Priority rule | LOCKED: Option A – choose direction with larger ΔU; if equal use lower current quantity; final tie lexicographic 'A' acquisition |
| D-Market-5 | Trades per step | 1 / many | TBD |
| D-Market-6 | Depletion fairness | Sequential/Batch | TBD |
| D-Snap-1 | Field append order | Approve | TBD |
| D-Snap-2 | Include distribution now | Yes/No | TBD |
| D-Snap-3 | Price storage | Format | TBD |
| D-Snap-4 | Bitmask ordering | Confirm | TBD |
| D-Perf-1 | Accept O(n^2) | Yes/No | LOCKED: Option B – Disallow O(n^2) per-step in core logic; only O(n) (and necessary O(n log n) for explicit, justified sorts like M12 trade ordering) accepted. Feature additions requiring higher complexity need gating + perf test. |
| D-Perf-2 | Spatial index threshold | n=? | LOCKED: Option B – Declare placeholder SPATIAL_INDEX_THRESHOLD=300 (doc only). No index built until agent count >= threshold; implementation deferred. |
| D-GUI-1 | Dropdown location | Start only / runtime | LOCKED: Option A – Start screen only; immutable after launch to preserve determinism and avoid mid-run re-init complexity. |
| D-GUI-2 | Price overlay format | Spec | LOCKED: Option B – Two-line overlay: line1 Prices (g1=..., g2=...); line2 Money (market=..., blocked=...). Compact; avoids table complexity. |
| D-GUI-3 | Marketplace marking | Spec | LOCKED: Option B – Single small "$" badge rendered once (overlay layer), no per-cell artifacts, constant-time. |
| D-GUI-4 | Mode mutability | Yes/No | LOCKED: Option A – Immutable post-start; mode changes require new simulation instance (explicit reset). |
| D-Test-1 | Inequality metric now | Yes/No | LOCKED: Option A – Defer inequality metrics (Gini/variance) until base money dynamics stabilized. |
| D-Test-2 | Rounding tolerance | Spec | LOCKED: Option A – Exact integer equality (no tolerance) for prices/money; scaled ints remove float drift risk. |
| D-Edge-1 | Partial trade handling | Skip/Partial | LOCKED: Option A – No partial trades; insufficient market money => blocked sale increment only. |
| D-Edge-2 | Flat utility handling | Halt rule | LOCKED: Option A – Agents remain IDLE when no positive marginal utility; no random exploration injected. |
| D-Metrics-1 | Inequality metrics | Now/Defer | LOCKED: Option A – Defer; future addition inside economy metrics namespace (append-only). |
| D-Metrics-2 | Price stats metrics | Now/Defer | LOCKED: Option A – Defer; external scripts can compute from recorded per-step prices. |
| D-Config-1 | Field names | Approve | LOCKED: Option A – Accept names: mode, quasi_linear_kappa, initial_agent_money, initial_market_money (append-only). |
| D-Config-2 | Enum vs string | Choice | LOCKED: Option A – Use plain string literals for mode ("basic"/"money"); potential Enum later without breaking existing configs. |

---
### Money Mode Decisions (In Progress)
| Code | Topic | Need | Status |
|------|-------|------|--------|
| M1 | Utility model (money) | Select integration pattern | LOCKED: Quasi-linear U=U_goods + kappa*money (kappa=1.0 config); future expansion path toward adaptive dynamic (spec D) noted |
| M2 | Price formation method | Anchor vs proportional | LOCKED: Anchor (good1 fixed SCALE=10000, good2 relative); min clamp=1; recompute each step |
| M3 | Money config fields | Field selection & validation | LOCKED: Add to SimConfig: mode, quasi_linear_kappa (float>0, default 1.0), initial_agent_money (int>=0, default 5), initial_market_money (int>=0 or None=>n); drop enable_money flag (mode implies); validation raises on invalid; None maps to n deterministically |
| M4 | Agent initial money distribution | Pattern selection | LOCKED: Pattern B – reuse goods endowment weight vector to allocate money, then scale to total = n * default(5); future distinct money patterns documented |
| M5 | Market initial money rule | Initialization & validation | LOCKED: Derive from n when None (Option A); allow explicit zero; negative => error; tracking in metrics deferred |
| M6 | Trade lot size (money mode) | Quantity per trade | LOCKED: Fixed 1 unit per trade (Option A); add placeholder field `desired_lot_size` (unused now); one trade per agent per step |
| M7 | Sell liquidity condition | Market money constraint | LOCKED: Strict conservation (S1); require market_money >= price; sale priority by ascending agent id; track blocked_sales_count (counter) yes; no retry same step |
| M8 | Price recompute cadence | Frequency & history | LOCKED: Every step pre-trade (anchor update); empty-agent fallback prices = (SCALE,SCALE); record price history in metrics (history=yes) |
| M9 | Snapshot integration & ordering | Append-only snapshot plan | LOCKED: Add single new top-level key `economy` (namespaced). Internal ordered keys: mode, kappa, anchor_good, price_scale, prices (sorted list of (good, price_int) incl anchor), market_money, agent_money (sorted (id, money)), blocked_sales. Legacy snapshots omit `economy`. Deterministic ordering via sorted goods & ids; no per-agent money field added to avoid altering existing agent dict order. |
| M10 | Metrics scope (money mode) | What to record & hash | LOCKED: Option 2. Per-step record append (order): money_agents (total_agent_money), money_market (market_money), price_g1 (anchor), price_g2, blocked_sales. Determinism hash appends segment `M=ta,mm,pg1,pg2,bs` only when economy.mode=='money'. No per-agent distribution hashing; legacy mode unchanged; prices present allow detection of price algorithm regressions. |
| M11 | Termination / stop criteria | Internal auto-stop policy | LOCKED: Option A (none). Core `Simulation` adds no stop fields or logic; controller/demos decide when to halt. Preserves legacy step semantics; avoids hash fixture churn and additional config. Future addition (max_steps or convergence) can append config later. |
| M12 | Trade ordering tie-break | Deterministic sale priority | LOCKED: Option D (utility-loss minimization). Candidate sale good per agent selected by lowest marginal utility loss (compute base_bundle = (home+carrying) goods; test removing 1 unit of each good with positive quantity; utility_loss = U(base) - U(after)). Choose good with smaller loss; tie-break: higher price_int first, then good name lexicographic, then agent_id. Build candidate list (≤ n entries) and sort by key (loss_scaled=int(round(loss*1e9)), -price, good, agent_id) then process until each agent sells at most one unit or market money exhausted. Selling draws from home_inventory first else carrying for that good (deterministic). Complexity introduces O(n log n) sort; justified for small educational n; future optimization note: can bucket losses if n growth pressures performance. Floating comparison stabilized via scaled int key. |

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
