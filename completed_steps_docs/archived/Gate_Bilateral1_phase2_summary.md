# Gate Bilateral1 – Phase 2 Draft Enumeration Summary

Date: 2025-09-24

## Goal
Introduce a deterministic, feature‑flagged (ECONSIM_TRADE_DRAFT=1) draft layer that enumerates potential bilateral trade intents among co‑located agents without mutating simulation state or impacting the determinism hash.

## Scope Implemented
- Added `TradeIntent` dataclass + `enumerate_intents_for_cell` in `simulation/trade.py`.
- Integrated enumeration into `Simulation.step` under feature flag only.
- Added debug overlay helper `gui/_trade_debug_overlay.py` to visualize up to 3 intents (non‑intrusive, optional, order‑stable).
- Metrics placeholder increment (`trade_intents_generated`) appended (excluded from hash—preserves external contract).

## Determinism & Performance Safeguards
- Enumeration executes only when `ECONSIM_TRADE_DRAFT=1`; otherwise `trade_intents` list is cleared/empty.
- Co‑location index is O(agents); per-cell enumeration limited to pairwise checks over goods {good1, good2}.
- No RNG usage; ordering enforced by sorting on `priority` tuple `( -ΔU_placeholder , seller_id, buyer_id, give_type, take_type )` (ΔU currently 0.0 placeholder).
- Determinism hash parity test confirms no change versus baseline run without flag.

## Tests Added
| Test | Purpose | Result |
|------|---------|--------|
| `test_trade_draft_intents::test_no_intents_without_colocation` | Ensures no false positives | PASS |
| `test_trade_draft_intents::test_intents_generated_when_colocated` | Validates generation + sorted priority | PASS |
| `test_trade_draft_intents::test_draft_hash_parity` | Confirms determinism hash unaffected | PASS |
| `test_trade_overlay_debug_smoke::test_overlay_renders_with_intents` | Overlay draw smoke (flag ON) | PASS |
| `test_trade_overlay_debug_smoke::test_overlay_noop_without_flag` | Overlay no-op (flag OFF) | PASS |

## Non-Hash Fields
- Metrics counters (`trade_intents_generated`, `trades_executed`) remain excluded from hash until execution phase graduates gate.

## Open Items (Next Phases)
1. Phase 3 – Execute a single highest‑priority intent per tick (new flag `ECONSIM_TRADE_EXEC=1`, layered atop draft flag or replacing it).
2. Extend `TradeIntent` priority to incorporate actual marginal utility deltas (requires pure evaluation helper; keep ΔU sign handling stable: tie key begins with -ΔU).
3. Snapshot serialization append: include executed trade log or counters only after gate acceptance; update determinism tests accordingly.
4. Metrics promotion: integrate trade counters into hash once execution semantics frozen.
5. UI enhancement: optional inspector panel for “last executed trade” (read‑only, deterministic ordering, no extra timers).
6. Conflict handling: ensure at most one execution per agent per tick (reservation set) before multi-trade expansion.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Enumeration creep into O(n^2) hotspots with larger good sets | Hard-coded limited good pairs; future expansion must include perf test (`make perf`). |
| Accidental state mutation in overlay | Overlay restricted to read-only attributes; try/except guards. |
| Silent hash drift when adding ΔU | Mandate hash parity test before promotion; ΔU only influences ordering, not contents, at first. |

## Validation Evidence
- All new tests pass (see table).
- Baseline determinism hash unchanged under flag vs. unflagged run (see `test_draft_hash_parity`).
- Overlay smoke tests show idempotent rendering (no list mutation, stable IDs).

## Decision Log
- Chose minimal heuristic (mutual complement) to keep enumeration simple and deterministic prior to utility integration.
- Isolated overlay in helper to avoid polluting main rendering pipeline and to simplify removal/revision post-gate.

## Ready for Gate Review?
Yes. Phase 2 objectives (enumeration + visibility + determinism neutrality) satisfied. Recommend initiating Gate Bilateral1 Phase 3 planning focusing on execution semantics and marginal utility integration.
