# Gate 3 Checklist — Spatial & Agent Foundations

(Complete all items before marking Gate 3 done.)

## Core Structures
- [x] Grid class created with width/height
- [x] Resource add/query/remove methods implemented
- [x] Out-of-bounds access raises ValueError
- [x] Resources stored in set for O(1) membership

## Agent
- [x] Agent class (id, position, inventory, preference)
- [x] move_random() stays within bounds
- [x] collect() removes resource & increments inventory
- [x] Inventory keys restricted to good1/good2

## Simulation
- [x] Simulation/World aggregates grid + agents
- [x] step() moves & collects each agent exactly once
- [x] Deterministic output under fixed seed test passing

## Integration
- [x] Optional widget integration toggle (simulation step invoked when enabled)
- [x] Simulation disabled path leaves existing tests unaffected
- [x] Clean teardown verified (shutdown tests still pass)

## Performance
- [x] Perf test with 10 agents / 50 resources ≥30 FPS
- [x] No significant regression vs baseline (document if any)

## Testing
- [x] test_grid.py covers resource operations & bounds
- [x] test_agent.py covers movement & collection
- [x] test_simulation.py covers deterministic stepping
- [x] test_perf_simulation.py (or extension) covers FPS threshold

## Documentation
- [x] Module docstrings (grid, agent, simulation) explain deferrals
- [x] README updated current phase to Gate 3 in progress
- [x] Gate 3 todos + this checklist committed before implementation start
- [x] Retrospective template prepared for Gate 3 Eval (Gate 3 todos file serves as template)

## Quality Gates
- [x] All existing tests still pass
- [x] New tests pass
- [x] Lint & type check clean (core modified modules; legacy prefs modernization deferred outside Gate 3 scope)

## Exit
- [x] Gate 3 Evaluation document written (GATE3_EVAL.md)
- [x] All checklist items checked
