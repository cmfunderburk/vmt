# Gate 4 Checklist — Preference-Driven Movement & Visual Layer

(Complete all items before marking Gate 4 done.)

## Grid & Resources
- [ ] Typed resources (dict[(x,y)] -> type)
- [ ] Add/query/remove return resource type or None
- [ ] Serialization preserves resource types

## Agent State & Modes
- [ ] home_pos stored
- [ ] mode field (forage/return_home/idle)
- [ ] target coordinate optional
- [ ] carrying vs home_inventory distinction
- [ ] Deposit merges carrying into home_inventory

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
- [ ] All existing Gate 3 tests still pass
- [ ] New tests added & passing
- [ ] Lint clean (modified/new modules)
- [ ] Type check clean

## Documentation
- [ ] README updated with Gate 4 section (movement model & visuals)
- [ ] Module docstrings updated (grid/agent/simulation) list new deferrals
- [ ] Gate_4_todos + this checklist committed pre-implementation
- [ ] Evaluation doc drafted (skeleton) early

## Exit
- [ ] GATE4_EVAL.md produced mapping criteria→evidence
- [ ] All checklist items checked

-- END --
