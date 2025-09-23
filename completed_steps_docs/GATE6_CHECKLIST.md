# GATE6_CHECKLIST — Interaction & Visualization Enhancements (Draft)

## Interaction Mechanics
- [ ] InteractionScheduler implemented & integrated
- [ ] Deterministic ordering of interaction evaluation (documented tie-break)
- [ ] Bilateral trade rule (1 unit swap) only executes if both utilities strictly increase
- [ ] No duplicate trades (each agent max one trade per tick)
- [ ] Trade disabled cleanly via config flag

## Visualization Overlays
- [ ] Agent utility label overlay (toggle)
- [ ] Overlay toggle does not affect determinism
- [ ] Heatmap / density overlay (stretch)
- [ ] Marginal rate visualization (stretch)

## Metrics Extension
- [ ] Per-agent utility recorded each step
- [ ] Interaction count per step recorded
- [ ] Successful trade count per step recorded
- [ ] Determinism hash includes new metrics fields

## Snapshot / Replay
- [ ] Snapshot includes utility & interaction metrics state
- [ ] Replay reproduces per-agent utility trajectory for N steps

## Performance
- [ ] Interaction layer per-tick overhead ≤0.40ms (absolute) on reference scenario
- [ ] FPS ≥30 with interaction & overlays active

## Testing Artifacts
- [ ] test_interaction_trade_success.py
- [ ] test_interaction_no_trade_when_not_mutual.py
- [ ] test_interaction_ordering_determinism.py
- [ ] test_metrics_interactions_extension.py
- [ ] test_perf_interaction_overhead.py
- [ ] test_overlay_utilities_smoke.py
- [ ] Updated determinism hash tests (utility + interactions)

## Quality Gates
- [ ] All tests pass
- [ ] Lint clean
- [ ] Type check clean

## Documentation
- [ ] Gate 6 README section / changelog added
- [ ] Gate_6_todos.md kept updated
- [ ] GATE6_EVAL.md with evidence mapping

## Exit
- [ ] Evaluation doc includes interaction counts, utility trajectory sample, perf deltas
- [ ] Retrospective added

-- END DRAFT --
