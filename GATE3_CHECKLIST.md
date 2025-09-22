# Gate 3 Checklist — Spatial & Agent Foundations

(Complete all items before marking Gate 3 done.)

## Core Structures
- [ ] Grid class created with width/height
- [ ] Resource add/query/remove methods implemented
- [ ] Out-of-bounds access raises ValueError
- [ ] Resources stored in set for O(1) membership

## Agent
- [ ] Agent class (id, position, inventory, preference)
- [ ] move_random() stays within bounds
- [ ] collect() removes resource & increments inventory
- [ ] Inventory keys restricted to good1/good2

## Simulation
- [ ] Simulation/World aggregates grid + agents
- [ ] step() moves & collects each agent exactly once
- [ ] Deterministic output under fixed seed test passing

## Integration
- [ ] Optional widget integration toggle (simulation step invoked when enabled)
- [ ] Simulation disabled path leaves existing tests unaffected
- [ ] Clean teardown verified (shutdown tests still pass)

## Performance
- [ ] Perf test with 10 agents / 50 resources ≥30 FPS
- [ ] No significant regression vs baseline (document if any)

## Testing
- [ ] test_grid.py covers resource operations & bounds
- [ ] test_agent.py covers movement & collection
- [ ] test_simulation.py covers deterministic stepping
- [ ] test_perf_simulation.py (or extension) covers FPS threshold

## Documentation
- [ ] Module docstrings (grid, agent, simulation) explain deferrals
- [ ] README updated current phase to Gate 3 in progress
- [ ] Gate 3 todos + this checklist committed before implementation start
- [ ] Retrospective template prepared for Gate 3 Eval

## Quality Gates
- [ ] All existing tests still pass
- [ ] New tests pass
- [ ] Lint & type check clean

## Exit
- [ ] Gate 3 Evaluation document written (GATE3_EVAL.md)
- [ ] All checklist items checked
