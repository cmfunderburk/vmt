# Refactor Checklist (Consolidated)

A curated action list derived from subsystem READMEs to guide upcoming comprehensive code review & modernization. Prioritize items roughly in listed order within each section; maintain determinism & performance invariants throughout.

---
## 1. Determinism & Invariants
- [ ] Add explicit test asserting tie-break key stability (-ΔU, distance, x, y) for target selection.
- [ ] Codify serialization ordering contract in a dedicated test (agent append-only + snapshot field ordering).
- [ ] Introduce invariant test: `trades_executed == trade_ticks == fairness_round` for a controlled single-trade scenario.
- [ ] Add regression test ensuring priority flag (`ECONSIM_TRADE_PRIORITY_DELTA`) only reorders, never mutates multiset of intents.

## 2. Simulation Core Simplification
- [ ] Extract decision-mode targeting & movement into strategy class (pure functions) for isolated unit testing.
- [ ] Normalize buyer vs seller utility deltas (avoid approximating buyer delta as seller delta).
- [ ] Introduce structured result object for `Simulation.step` (e.g., StepOutcome) behind optional flag for diagnostics.
- [ ] Evaluate replacing co-location intent enumeration with incremental cache if profiling shows hotspots (measure first).

## 3. Trade System Evolution
- [ ] Implement marginal utility helper methods in preferences to remove duplication in trade intent enumeration.
- [ ] Support multi-unit or batched trades behind a feature flag with perf tests.
- [ ] Add optional paused-on-trade auto-resume after N steps (educational pacing) controlled via controller.
- [ ] Consolidate trade visualization (retire legacy `_trade_debug_overlay` once new panel stable).

## 4. Metrics & Observability
- [ ] Add timing breakdown (movement / foraging / trade / render) behind `ECONSIM_DEBUG_PROF` flag.
- [ ] Provide API to snapshot metrics deltas over window (for live charts) without exposing internal mutable state.
- [ ] Move event log assembly to a lightweight dataclass rather than raw dicts.
- [ ] Add test ensuring metrics hash unchanged when trade flags toggled OFF (guard against accidental inclusion).

## 5. Rendering & GUI
- [ ] Centralize panel refresh timers (shared dispatcher) to reduce QTimer proliferation.
- [ ] Abstract overlay drawing phases into composable mini-renderers (grid, agents, homes, trade, debug) for selective enabling.
- [ ] Replace manual font.init calls with cached singleton font manager.
- [ ] Add accessibility pass: configurable font scaling & high-contrast palette.
- [ ] Validate surface byte diff overlay test with deterministic synthetic overlay (current variance block OK; evaluate cost).

## 6. Start Menu & Session Lifecycle
- [ ] Integrate bilateral_exchange scenario once feature gating finalized (currently disabled placeholder).
- [ ] Parameterize respawn interval/rate via start menu advanced section (currently fixed defaults on launch).
- [ ] Add validation feedback inline (labels) instead of modal message boxes for common input errors.

## 7. Preferences Layer
- [ ] Implement marginal utilities (MU_x, MU_y) API on base class for trade & future optimization features.
- [ ] Add CES / Quasi-linear preferences behind feature flag; perf test their utility calls.
- [ ] Unify bundle normalization across all preference implementations (helpers already exist—verify consistency in error messages).

## 8. Snapshot & Replay
- [ ] Add explicit replay harness: load snapshot, step N ticks, verify hash path.
- [ ] Version snapshot schema (add `schema_version`) with backward compatibility tests.
- [ ] Provide diff utility between two snapshots (agent positions, inventories, resource layout).

## 9. Respawn System
- [ ] Expose respawn density shortfall metrics (records of placed vs requested count).
- [ ] Add test covering off→on interval change mid-run (determinism of placement order preserved).
- [ ] Modularize scheduling policy for alternative respawn strategies (e.g., cluster-biased) behind flag.

## 10. Testing & Tooling
- [ ] Register custom pytest mark `slow` to silence unknown mark warning.
- [ ] Replace return statements in tests that currently return a value with asserts (`test_sprite_loading`, educational performance tests).
- [ ] Add perf regression guard for trade intent enumeration under high agent colocation.
- [ ] Introduce property-based tests for trade intent symmetry and conservation of goods.

## 11. Performance Hardening
- [ ] Benchmark memory allocations per tick; refactor hotspots (object churn) if above threshold.
- [ ] Consider pooling `TradeIntent` objects if profiling shows GC pressure (only with evidence).
- [ ] Add optional compiled fast path (Cython or Rust extension) for intent scoring (flag controlled) if Python becomes a bottleneck.

## 12. Documentation & Developer Experience
- [ ] Generate Sphinx or MkDocs site (auto-build in CI) using API index below.
- [ ] Add CONTRIBUTING.md with determinism/perf guardrails summary.
- [ ] Embed architectural diagram (GUI loop, simulation step pipeline) in top-level README.
- [ ] Create a “Refactor Playbook” summarizing order-of-operations for large changes (e.g., modify tie-break key → update hash tests → update docs → run perf + determinism gates).

## 13. Safety & Robustness
- [ ] Expand defensive guards around environment flag parsing (centralized flag loader).
- [ ] Add early assertion ensuring only one executed trade per step (currently via code path; formalize test).
- [ ] Guard against surface recreation if viewport_size changes mid-run (decide policy: fixed vs dynamic).

## 14. Future Educational Features (Plan Ahead)
- [ ] Introduce curriculum scenarios (scripted parameter sequences) with reproducible seeds.
- [ ] Add agent annotation layer (teacher notes or prompts) overlayable on grid.
- [ ] Implement interactive “what-if” trade negotiation mock (no inventory mutation) for pedagogy.

---
## Prioritization Heuristic
Focus first on correctness & determinism (Sections 1–3), then observability (4), followed by performance (5, 11), and finally extensibility & UX (6, 12, 14).

---
## Tracking
Copy this file into an issue or project board; mark items incrementally. Each completed item should link corresponding PR + tests.
