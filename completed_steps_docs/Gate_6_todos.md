# Gate 6 Todos (Draft) — Interaction & Visualization Enhancements

Objective: Introduce agent interaction mechanics (e.g., simple trade or exchange trigger), richer utility & state visualization overlays, and extend metrics to capture interaction outcomes while preserving determinism & performance.

## Core Themes
- Interaction Primitive: Minimal bilateral exchange rule (e.g., if two agents adjacent with complementary inventories, execute swap improving both utilities).
- Enhanced Visualization: Overlay for agent utility values / marginal rates (optional toggle), resource density heatmap.
- Metrics Extension: Track interaction count, per-agent utility trajectory, and trade-improved utility deltas.
- Determinism Preservation: Interactions ordered deterministically (position, id) with tie-break alignment.
- Performance Guard: Ensure interaction layer adds <0.40ms per tick (absolute) on reference scenario.

## Assumptions
- Keep goods limited to two types (good1/good2) this gate.
- No negotiation or pricing; deterministic greedy mutual-improvement trade.
- Use existing preference utilities for evaluating post-trade improvement.

## Tasks
1. Draft interaction design doc (rules, preconditions, tie-break ordering, complexity analysis).
2. Add InteractionScheduler (similar style to RespawnScheduler) invoked post-collection.
3. Implement deterministic agent pairing pass (sorted by (y,x,id)).
4. Implement trade rule: if both agents improve (strictly higher utility) after exchanging 1 unit (good1 ↔ good2) then execute simultaneously.
5. Add visualization overlays:
   - Utility value label (compact integer or 1-decimal) above each agent (toggle)
   - Optional marginal rate indicator (arrow / color shift) (stretch)
   - Resource heatmap (aggregate counts per cell neighborhood) (stretch)
6. Extend MetricsCollector: per-agent utility each step, interaction count, successful trade count.
7. Snapshot update: include interaction stats so replay hash still captures them.
8. Tests:
   - Utility improvement after trade (single scenario)
   - No trade when improvement not bilateral
   - Deterministic ordering when >2 agents cluster
   - Metrics interaction count increments
   - Performance overhead (absolute per-tick <0.40ms added vs Gate 5 baseline)
   - Visualization smoke test (overlay render does not crash)
9. Update perf tests to incorporate interaction scenario (agents seeded to trigger trades).
10. Update evaluation & README sections.

## Stretch / Deferred (If time permits)
- Multi-step negotiation logic
- Variable trade ratios
- Agent specialization types influencing trade propensity

-- END DRAFT --
