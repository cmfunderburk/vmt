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
- [x] Perception radius implemented (config constant R=8)
- [x] ΔU computation using preference utility
- [x] Score = ΔU / (dist + 1e-9)
- [x] Tie-break rules: (-ΔU, dist, x, y) deterministic
- [x] No positive ΔU => mode transition logic correct
- [x] Greedy Manhattan step (one cell) toward target
- [x] Arrival at resource triggers collection & target clear
- [x] Arrival at home triggers deposit & mode update

## Behavior Tests
- [x] Deterministic trajectory test (seeded runs identical)
- [x] Competition test (single resource contention)
- [x] Preference shift test (agent switches good type)
- [x] Idle state reached after environment exhaustion (implicit via mode transition tests)

## Rendering
- [x] Resource type A color distinct
- [x] Resource type B color distinct
- [x] Agents rendered (shape or color distinct from resources)
- [x] Rendering smoke test passes (surface changes)

## Performance & Timing
- [x] Perf test 20 agents / 120 resources ≥55 FPS (≥30 assert floor) (throughput surrogate >6000 steps/sec)
- [x] Decision micro-benchmark captured (<0.3 ms/agent avg) or documented

## Quality Gates
- [x] All existing Gate 3 tests still pass
- [x] New tests added & passing
- [x] Lint clean (ruff 0 findings; black clean)
- [x] Type check clean (mypy 0 errors)

## Documentation
- [x] README updated with Gate 4 section (movement model & visuals)
- [x] Module docstrings updated (grid/agent/simulation) list new deferrals
- [x] Gate_4_todos + this checklist committed pre-implementation
- [x] Evaluation doc drafted (skeleton) early

## Exit
- [x] GATE4_EVAL.md produced mapping criteria→evidence (final)
- [x] All checklist items checked (Gate 4 complete)

-- END --
