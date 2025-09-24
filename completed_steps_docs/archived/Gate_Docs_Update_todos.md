# Gate Docs Update – Todos

Scope: Bring all public & contributor-facing documentation current with recent incremental changes (square grid cells, alternating multi-type respawn, agent metrics UI, controller accessors, test suite expansion) while reinforcing invariants (determinism, O(agents+resources) step cost).

## Acceptance Criteria (See separate checklist file)
1. README reflects: square grid cells, alternating respawn (A/B), agent metrics UI, updated test counts.
2. API_GUIDE documents new controller accessors and clarifies they are pure / read-only.
3. .github/copilot-instructions.md gains a Respawn Policy subsection (alternation invariant, complexity guard, future extension note).
4. ROADMAP_REVISED.md marks basic multi-type respawn as PARTIAL and adds future item for strategy/weighted distribution.
5. CHANGELOG.md created (or updated) with dated entry summarizing latest increments + associated tests.
6. Gate evaluation addendum written explaining rationale & risk assessment for early multi-type respawn inclusion.
7. All new/changed docs contain no stale claims about single-type respawn or missing features.
8. Full test suite passes (≥104 tests) after doc edits (no code regressions introduced).

## Ordered Todo List
- [ ] T1: README audit & diff plan (list stale phrases / sections to update)
- [ ] T2: Apply README updates (features, determinism, performance, usage snippet for agent metrics)
- [ ] T3: Update API_GUIDE with controller accessor entries (signatures + usage examples)
- [ ] T4: Append Respawn Policy subsection to copilot instructions (alternation, invariants, future gate boundary)
- [ ] T5: Roadmap revision (mark partial completion; future enhancement tasks)
- [ ] T6: Introduce CHANGELOG.md with 2025-09-23 entry
- [ ] T7: Gate eval addendum (Docs alignment) file creation
- [ ] T8: Consistency sweep (grep for phrases: "all type 'A'", "single-type respawn") ensure removed/qualified
- [ ] T9: Run full test suite; capture count in checklist
- [ ] T10: Final checklist verification & sign-off prep

## Constraints / Non-Goals
* No algorithmic changes (docs-only gate except clarifying invariants).
* Avoid expanding scope into future planned features (e.g., weighted respawn ratios) beyond roadmap notes.
* Preserve determinism explanation; do not reword tie-break key or constants.

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Over-documentation creates future churn | Keep new sections concise, reference existing invariants |
| Missed stale claim persists | Explicit T8 grep-based consistency sweep |
| Confusion about alternation vs future balancing | Roadmap clearly labels current approach as minimal baseline |

## Sign-Off Requirements
Project maintainer acknowledges checklist completion; CHANGELOG entry merged; no failing tests.
