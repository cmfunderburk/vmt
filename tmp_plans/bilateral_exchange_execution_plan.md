# Bilateral Exchange Execution Plan (Saved 2025-09-24)

This document preserves the reviewed plan so work can resume without re-deriving decisions.

## Summary of Completed Planning
- Scope & assumptions finalized (single-trade-per-agent-per-step, deterministic partner ordering).
- Data structures: always-appended `trade_partner_mask` (int), ephemeral per-step flags, partner ordering cache (precomputed once O(n^2 log n)).
- Algorithms: partner scan with radius & max cap; deterministic movement (one Manhattan step); trade uses first positive joint marginal utility resource pair.
- Config evolution: `trading_mode` ("off"|"simple"|"bilateral"), plus `exchange_search_radius`, `max_partner_scan`, `exchange_adjacent_allowed`, `collect_trade_metrics` (deferred hashing); legacy `enable_trading` maps to "simple".
- Snapshot: append `trade_partner_mask`; backward load injects 0; hash excludes mask.
- Metrics: optional counters (trades, candidate scans, skipped no gain) gated by flag, excluded from hash initially.
- Testing matrix: unit (utility, pair selection), integration (mode parity), determinism (hash, replay), perf (overhead thresholds), property (conservation), edge (large agent count), validation (invalid config).
- GUI: pure render overlays (targets, traded halo, metrics HUD) — no state mutation.
- Risks: performance, determinism drift, snapshot compatibility, overlay overhead, metric overhead; mitigations enumerated.
- Execution phases: 0–10 with rollback points A–I.

## Immediate Coding Target (Phases 1–3)
1. Append new config fields & resolver.
2. Add `trade_partner_mask` to Agent + snapshot adjustments + hash exclusion.
3. Introduce `BilateralExchangePolicy` skeleton (ordering + mask reset only).

## Rollback Points
- A: Baseline capture (hash + perf) before any code changes.
- B: After config wiring (simple mode parity tested).
- C: After snapshot & mask integration (hash parity confirmed).
- D: After policy skeleton (no movement/trade yet; perf neutral).

## Determinism Safeguards
- Precompute partner ordering using initial positions only.
- Exclude mask & trade metrics from hash.
- Append-only field additions (config, agent snapshot, metrics).

## Perf Guardrails
- Overhead target bilateral vs simple <=10% dense scenario; <=2% when no trades.
- `max_partner_scan` default 8; adjustable.

## Open (Deferred) Items
- Home return behavior (post-MVP).
- Trade pair distribution metrics.
- Extended hash version for trade metrics inclusion.
- Adaptive search radius.

## Next Step Once Resuming
Execute Phases 1–3 and land associated tests before implementing movement & trade logic.

---
Saved automatically by assistant for continuity.
