# Gate 4 — Preference-Driven Movement & Visual Layer (Planning Draft)

Date: 2025-09-22
Prereqs: Gates 1–3 accepted (render loop, preferences, spatial foundation)

## Goal
Introduce preference-informed agent movement, resource type differentiation, and visual overlays while preserving deterministic behavior and frame performance headroom.

## Objectives
1. Replace random walk with utility-based target selection (local heuristic; no global pathfinding).
2. Add multiple resource types mapped to distinct goods.
3. Render agents and resources distinctly on the existing Pygame surface.
4. Maintain deterministic simulation under fixed seed & tie-breaking rules.
5. Preserve ≥55 FPS (≥30 minimum safeguard) with moderate scale (20 agents, 120 resources).
6. Provide clean documentation and evaluation artifacts per gate workflow.

## Out of Scope (Deferred)
- Multi-step lookahead/pathfinding (A*, BFS) beyond greedy Manhattan move.
- Trade, budgets, prices, or inter-agent exchange.
- Resource respawn / regeneration cycles.
- UI control panels, overlays, or interactive placement.
- Threading or tick decoupling (unless performance forces minimal toggle stub, documented if added).

## Movement & Decision Model
At each step (mode forage):
1. Perceive candidate resources within radius R (initially full grid or capped at 8 Manhattan distance; pick constant R=8 for testability).
2. For each resource of type T at (x,y): compute ΔU = U(bundle + δ_T) - U(bundle), where δ_T adds 1 unit to the mapped good.
3. Score = ΔU / (dist + 1e-9) where dist = Manhattan distance from agent to resource.
4. Filter ΔU > 0. If none → switch to return_home if carrying goods else idle.
5. Choose highest score; tie-break by (descending ΔU, ascending dist, then (x,y) lexicographically).
6. Set target; move one Manhattan step toward it greedily (abs(dx) > abs(dy) → horizontal first else vertical).
7. On arrival at resource: collect → clear target → next tick reselect (no immediate second selection to keep per-tick constant cost).

Return cycle:
- Mode return_home: target=home; move until at home; deposit carrying into home_inventory; decide next mode (forage if desired goods remain else idle).

## Data Structure Changes
Grid: store resources as dict[(x,y)] = resource_type (e.g., 'A','B').
Agent: add home_pos, mode, target, home_inventory; rename existing inventory to carrying or maintain both with clear semantics.

## Acceptance Criteria (See Also Checklist)
(Refined list used for test design & evaluation mapping.)
1. Grid supports typed resources (add, has, take returns type or None). Serialization preserves types.
2. Agent state includes: mode, home_pos, target, carrying, home_inventory; deposit merges carrying → home_inventory.
3. Resource type to good mapping: 'A' → good1, 'B' → good2 (documented constant map).
4. Decision function deterministically selects target using scoring rules & tie-break order.
5. If no positive ΔU resource available and carrying >0 → agent returns home; if carrying ==0 and none available → mode idle.
6. Greedy Manhattan step moves exactly 1 cell unless already at target.
7. Arrival at resource triggers collection; inventory updated correctly; resource removed.
8. Arrival at home triggers deposit & mode transition logic.
9. Determinism test: two seeded runs (same initial grid/resources/agents) produce identical sequence of (mode, pos, target or None, carrying totals) after N steps.
10. Competition test: two agents chasing same high-score resource results in only one collecting; loser retargets next tick deterministically.
11. Cobb-Douglas preference shift test: as good1 quantity grows, agent eventually selects a good2 resource when ΔU ratio reverses (monotonic switch evidence within bounded steps scenario).
12. Rendering: resources of type A and B drawn with distinct colors; agents drawn; at least one test asserts surface pixel variance after enablement (smoke-level, not color-exact).
13. Performance: scenario (20 agents, 120 mixed resources) passes perf test ≥55 FPS (≥30 threshold assertion to prevent flakes); test logs measured average FPS.
14. Per-step decision overhead (micro-benchmark in test) below configured budget (target <0.3 ms/agent averaged across 50 steps; skip if environment noise, mark informational).
15. All prior tests (Gate 3) remain green; new tests cover criteria above.
16. Lint + type checks clean for new/modified modules.
17. README updated: Gate 4 in progress, movement model overview, visualization note.
18. Gate planning docs (`Gate_4_todos.md`, `GATE4_CHECKLIST.md`) committed before starting implementation code.
19. Evaluation doc `GATE4_EVAL.md` produced mapping each criterion to evidence.
20. Checklist exit items all marked before declaring gate complete.

## Risks & Mitigations
Risk | Mitigation
-----|-----------
Performance dip with scoring | Limit perception radius or short-circuit after top-K discovered.
Tie-breaking ambiguity | Deterministic ordered tuple comparison; document order.
Overfitting tests to heuristic | Keep scoring logic simple & documented; future heuristics may replace behind same interface.
Excessive test brittleness | Use state snapshots & pattern assertions instead of pixel-perfect or exact path lengths.

## Phases
Phase | Tasks | Output
------|-------|-------
P1 | Typed resource grid refactor + tests | Updated grid module & serialization tests
P2 | Agent state extensions + deposit logic tests | Extended agent module
P3 | Decision scoring & movement integration | Determinism + selection tests
P4 | Rendering overlays (agents/resources) | Visual smoke test
P5 | Competition & preference shift tests | Behavioral coverage
P6 | Performance & micro-benchmark tests | Perf threshold test artifacts
P7 | Docs & evaluation scaffolding | README + Gate 4 eval draft stub

## Test Plan (New Files / Enhancements)
- `tests/unit/test_grid_typed.py`
- `tests/unit/test_agent_decision.py`
- `tests/unit/test_simulation_determinism_adv.py`
- `tests/unit/test_agent_competition.py`
- `tests/unit/test_preference_shift.py`
- `tests/unit/test_render_agents.py`
- `tests/unit/test_perf_decision.py`

## Metrics & Instrumentation (Optional, Lightweight)
- Helper to snapshot agent state tuple for determinism tests.
- Simple timing utility in test for decision time (avoid adding production dependency).

## Baseline Performance Snapshot (Pre-Gate 4 Changes)
Captured on 2025-09-22 before introducing decision logic & rendering overlays:

Widget FPS (2s run): ~61.0 FPS (Frames=122 / 2.00s)

Micro Benchmark (seeded synthetic scenario):
```
30 agents, 200 resources
200 steps total
Total duration: ~0.00359 s
Per step: ~17.96 µs
Per agent-step: ~0.60 µs
```
Interpretation:
- Enormous headroom: even a 50–100x increase in per-agent decision cost keeps us well below frame budget (~16ms).
- Gate 4 heuristic scoring target (<0.3 ms/agent per decision) is extremely conservative relative to current ~0.0006 ms.

These figures will be referenced in Gate 4 evaluation to quantify overhead introduced by utility-driven targeting & rendering.

## Current Progress (2025-09-22)
Status Snapshot:
- Completed: Phase P1 (typed resource grid refactor) merged; all legacy + new tests green.
- Added: New typed agent collection logic (`Agent.collect`) mapping 'A'→good1, 'B'→good2; new test `test_agent_typed_collect.py` (suite now 38 tests).
- Partial Phase P2: Resource type → good mapping implemented; remaining P2 work (agent modes, home/target state, deposit behavior) not yet started.
- Baseline performance unchanged (logic addition is O(1) branch on collected type; no measurable overhead expected, perf re-check deferred until decision logic added).

Delta vs Plan:
- No scope drift. Implementation order preserved. Minor adjustment: introduced typed collection test earlier than originally listed (beneficial guard for upcoming state refactors).

Upcoming Focus (Next Sequence) [Revised for Epsilon Augmentation]:
1. Decision Logic Correction: Implement epsilon augmentation bootstrap for Cobb-Douglas zero-good states. Approach: lift bundle with ε (const, e.g., 1e-6) added to both goods when computing base & marginal utilities so first acquisitions yield positive ΔU. Retain exact utility function after both goods >0 (no epsilon injection in delta stage if both >0).
2. Target Reselection Optimization: Only re-run `select_target` when (a) target is None, (b) resource collected previous tick, or (c) mode transition (FORAGE↔RETURN_HOME/IDLE). Avoid per-tick full scan to preserve performance headroom.
3. Determinism Test Update: Adjust determinism test to assert non-idle progression and at least one collection event with epsilon bootstrap active.
4. Competition & Preference Shift Tests: After stable ΔU bootstrap, implement race scenario & switch test (ensure agent diversifies once both goods positive—Cobb-Douglas will produce positive marginal utilities natively then).
5. Rendering & Performance Phases remain unchanged sequence-wise (P4–P6) once decision stability confirmed.
6. Documentation: Add short note in README & evaluation doc explaining epsilon augmentation as educational modeling choice (assumes strictly positive baseline endowment approaching zero).

Risk Watch Items:
- Decision loop complexity creep: keep perception radius constant (R=8) and short-circuit if best possible score cannot be exceeded by remaining candidates.
- Test brittleness: use state tuple snapshots rather than asserting exact paths beyond first few steps.
 - Epsilon sensitivity: choose ε small enough (e.g., 1e-6) that post-bootstrap ΔU comparisons remain dominated by real differences; document constant to allow future experimental tuning.

## Exit Condition
All acceptance criteria satisfied, evaluation document completed, and performance/determinism evidence recorded.

-- END DRAFT --
