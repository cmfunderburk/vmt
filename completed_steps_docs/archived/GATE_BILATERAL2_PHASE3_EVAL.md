# Gate Bilateral2 Phase 3 Evaluation (Bilateral Exchange Movement & Priority Flag)

Date: 2025-09-25
Status: COMPLETE (feature‑gated, deterministic, performance-neutral within tolerances)

## Scope Delivered
- Deterministic bilateral exchange movement path when foraging disabled (partner search → meeting point → trade session → cooldown cleanup)
- Single executed trade intent per step (if any) with feature flags:
  - `ECONSIM_TRADE_DRAFT=1` (enumeration only)
  - `ECONSIM_TRADE_EXEC=1` (execution + enumeration)
  - `ECONSIM_TRADE_PRIORITY_DELTA=1` (optional reordering)
  - `ECONSIM_TRADE_GUI_INFO=1`, `ECONSIM_TRADE_DEBUG_OVERLAY=1` (visual & debug aids)
- Priority tuple (flag enabled): `(-delta_utility, seller_id, buyer_id, give_type, take_type)`
- Advisory metrics (hash-excluded): `trade_intents_generated`, `trades_executed`, `trade_ticks`, `no_trade_ticks`, `realized_utility_gain_total`, `last_executed_trade`, `fairness_round`
- Executed trade visual highlight (pulsing orange/yellow 12 steps) + cyan partner lines
- Selected agent highlight integration (Inspector → green outline)
- Hash neutral debug option: `ECONSIM_TRADE_HASH_NEUTRAL=1` restores carrying inventories post metrics hash for parity experimentation

## Invariants & Determinism
- Intent multiset invariant under priority flag toggling (ordering only) – validated by multiset test
- Trade metrics excluded from determinism hash; enabling/disabling trade features does not disturb base hash when execution off
- Movement system confined to forage-disabled branch; foraging path remains byte-for-byte identical vs pre-phase build
- RNG usage segregated: external RNG for legacy/random walk; internal `Simulation._rng` unaffected by trade path

## Complexity & Performance
- Partner search limited to local perception radius; per-step complexity O(agents + resources)
- No global all-pairs loops introduced; cell co-location map reused for intent generation
- Perf spot check (widget, 2s) shows FPS within historical band (~61–62) and overlay overhead unchanged (<2%)

## Tests (Representative)
- Multiset invariance (priority flag on/off)
- Single-intent execution constraint (at most one per step)
- Fairness round increment per executed trade
- Hash neutrality mode restores inventories (debug scenario) without altering normal run behavior
- Pair availability rules (cooldowns, mutual partner-specific cooldowns) – edge case coverage

## Deferred / Future Gates
- Multi-intent execution policies (e.g., utility threshold, fairness scheduling)
- Advanced analytics / trade network overlays
- Hash redesign separating carrying vs banked wealth for stricter parity between draft & exec modes
- Extended economic metrics (inequality, turnover, trade partner diversity)

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Hidden nondeterminism via partner scan order | Deterministic sorting / original agent list order preserves tie-breaks |
| Priority flag accidentally altering multiset | Explicit multiset invariance test |
| Performance regression from cooldown bookkeeping | O(1) updates; no additional allocations in tight loop |
| Visual debug artifacts altering state | Rendering read-only; highlight & lines derive from immutable snapshot |

## Acceptance Criteria (Met)
- Deterministic with features off (hash parity) ✔
- Single executed trade per step ✔
- No all-pairs global scan ✔
- Feature flags isolate behavior ✔
- Metrics excluded from determinism hash ✔
- Movement algorithm documented (README pseudocode) ✔

---
Prepared as evidence artifact for Gate Bilateral2 Phase 3 completion.
