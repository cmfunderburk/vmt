# Gate Bilateral1 – Phase 3 Execution Summary

Date: 2025-09-24

## Goal
Introduce minimal, deterministic trade execution of at most one bilateral swap per tick based on reciprocal marginal utility preferences, without changing the determinism hash.

## Feature Flags
- `ECONSIM_TRADE_DRAFT=1`: Enumerate candidate trade intents (Phase 2 behavior).
- `ECONSIM_TRADE_EXEC=1`: Implies enumeration (even if draft flag unset) and executes the first viable intent.

## Execution Rule (Current Minimal Policy)
For each co-located unordered agent pair (i,j):
1. Compute marginal utilities MU_i and MU_j over (carrying + home) with epsilon lift for zero components.
2. Generate an intent (i gives good1, j gives good2) iff MU_i(good2) > MU_i(good1) AND MU_j(good1) > MU_j(good2) and each has ≥1 carrying unit of the good they would give.
3. Also test the opposite direction (i gives good2, j gives good1) with roles reversed.
4. Sort intents by priority tuple (currently placeholder `(0.0, seller_id, buyer_id, give_type, take_type)`).
5. If `ECONSIM_TRADE_EXEC=1`, execute the first viable intent: transfer 1 unit of the offered goods between carrying inventories.
6. Increment `trades_executed` (hash-excluded) and stop (single swap per tick).

Carrying-only Invariant: Only goods in `carrying` are tradable; home inventory is immutable during trade.

## Implementation Changes
- Added epsilon-lift capability to `marginal_utility` helper (`epsilon_lift=True`) reusing `EPSILON_UTILITY` constant.
- Enumeration now pre-computes marginal utility dicts for agents in the cell with `epsilon_lift`.
- New execution helper `execute_single_intent` unchanged; viability now determined by enumeration stage.
- `Simulation.step` updated: execution flag implies enumeration path; builds id map once; increments `trade_intents_generated` and conditionally `trades_executed`.

## Tests Added / Updated (All PASS)
| Test | Purpose |
|------|---------|
| `test_single_execution_swap` | Verifies example bundles (8,1) & (1,6) swap → (7,2) & (2,5) |
| `test_no_double_execution` | Ensures only one swap per tick even with surplus inventory |
| `test_hash_parity_execution_flag` | Confirms determinism hash unchanged draft vs draft+exec |
| `test_flag_gating` | EXEC flag alone triggers enumeration + execution (no draft flag) |
| `test_execution_requires_inventory` | No swap if one side lacks required offered good |
| `test_no_trade_when_marginals_not_reciprocal` | Balanced (5,5)/(5,5) yields no trade |

## Determinism & Hash
- Hash parity maintained (trade counters excluded from hash feed).
- All logic purely deterministic (no RNG) with stable sorting; epsilon lift constant reused from decision logic to avoid new randomness.

## Performance Notes
- Added O(a_cell) marginal utility computations per co-located cell (two goods fixed) → still O(N_agents) per frame.
- Single execution only; reservation set unnecessary at this stage.
- Overlay unchanged; still displays top intents (pre-execution list retained for now).

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Future inclusion of ΔU in priority could reorder intents | Keep priority tuple stable; append ΔU only after explicit gate & hash review |
| Epsilon-lift semantics drift from decision logic | Reused existing `EPSILON_UTILITY`; documented coupling |
| Multi-trade expansion may create fairness concerns | Limit to single trade now; future gate to add reservation + fairness metrics |
| Potential starvation of later intents | Future scheduling policy (round-robin, rotating priority) earmarked for Phase 4 |

## Follow-Up (Phase 4 Candidates)
1. Embed actual utility delta in priority: `(-ΔU_total, seller_id, buyer_id, give_type, take_type)` ensuring tie-break contract preserved.
2. Allow multiple trades per tick with reservation set to avoid agent reuse.
3. Promote `trades_executed` & aggregated trade volume stats into determinism hash (after stability soak).
4. Add optional metrics: per-agent trade count, realized utility gain delta (tracked but hash-excluded initially).
5. GUI: inspector / log for last executed trade (read-only overlay or side panel) maybe behind `ECONSIM_TRADE_INSPECT=1` flag.
6. Consider probabilistic acceptance (if utility gains marginal) – would require strict determinism design (e.g., deterministic tie-break fallback) or rejection.

## Acceptance Snapshot
- Core gate objectives (single reciprocal marginal utility trade, determinism neutral, tests passing) achieved.
- Ready for stakeholder review before expanding scope.

Reviewer Sign-off:
- Name: __________________ Date: __________
