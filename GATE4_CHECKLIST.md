# Gate 4 Checklist — Preference-Driven Movement & Visual Layer

(Complete all items before marking Gate 4 done.)

## Grid & Resources
- [x] Typed resources (dict[(x,y)] -> type)
- [x] Add/query/remove return resource type or None
- [x] Serialization preserves resource types

## Agent State & Modes
- [x] home_pos stored
- [x] mode field (forage/return_home/idle)
- [x] target coordinate optional
- [x] carrying vs home_inventory distinction
- [x] Deposit merges carrying into home_inventory

## Decision Logic
- [ ] Perception radius implemented (config constant R=8)
- [ ] ΔU computation using preference utility
- [ ] Score = ΔU / (dist + 1e-9)
- [ ] Tie-break rules: (-ΔU, dist, x, y) deterministic
- [ ] No positive ΔU => mode transition logic correct
- [ ] Greedy Manhattan step (one cell) toward target
- [ ] Arrival at resource triggers collection & target clear
- [ ] Arrival at home triggers deposit & mode update

## Behavior Tests
- [ ] Deterministic trajectory test (seeded runs identical)
- [ ] Competition test (single resource contention)
- [ ] Preference shift test (agent switches good type)
- [ ] Idle state reached after environment exhaustion

## Rendering
- [ ] Resource type A color distinct
- [ ] Resource type B color distinct
- [ ] Agents rendered (shape or color distinct from resources)
- [ ] Rendering smoke test passes (surface changes)

## Performance & Timing
- [ ] Perf test 20 agents / 120 resources ≥55 FPS (≥30 assert floor)
- [ ] Decision micro-benchmark captured (<0.3 ms/agent avg) or documented

## Quality Gates
- [x] All existing Gate 3 tests still pass
- [x] New tests added & passing
- [ ] Lint clean (modified/new modules)  <!-- TODO: run lint & mark -->
- [ ] Type check clean  <!-- TODO: run mypy & mark -->

## Documentation
- [ ] README updated with Gate 4 section (movement model & visuals)
- [x] Module docstrings updated (grid/agent/simulation) list new deferrals
- [x] Gate_4_todos + this checklist committed pre-implementation
- [ ] Evaluation doc drafted (skeleton) early

## Exit
- [ ] GATE4_EVAL.md produced mapping criteria→evidence
- [ ] All checklist items checked

-- END --
