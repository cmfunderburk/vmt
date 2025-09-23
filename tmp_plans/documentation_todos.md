# Documentation Remediation & Roadmap Alignment Todos (2025-09-23)

Decision Inputs Locked:
1. README split: archive current as `README_aspirational.md`.
2. API guide: manual wiring only now; real factory documented after Gate 6 implementation.
3. Tone: neutral, corrective (no blame; clarify divergence + plan).
4. Gate 6 scope WILL include minimal overlay toggle enablement (not full control panels).
5. Docstrings: multi-line narrative retained (remove outdated scaffold/future phrasing).

## Active Todo List

| ID | Title | Status | Notes |
|----|-------|--------|-------|
| 1 | Align on documentation remediation scope | completed | Decisions captured above |
| 2 | Collect target files for update | in-progress | Inventory paths & confirm existence |
| 3 | Draft updated core README (honest state) | not-started | Move old README -> README_aspirational.md |
| 4 | Add API_GUIDE.md | not-started | Manual wiring examples (decision mode, respawn, metrics) |
| 5 | Update module docstrings | not-started | agent.py, grid.py, metrics.py, respawn.py, world.py |
| 6 | Create Gate 6 planning docs | not-started | Gate_6_todos.md + GATE6_CHECKLIST.md |
| 7 | Add ROADMAP_REVISED.md | not-started | Gates 6–9 realistic scope |
| 8 | Cross-link docs for discoverability | not-started | README links to API guide & roadmap |
| 9 | Quality pass & consistency check | not-started | grep for 'scaffold' obsolete usage |
| 10 | Solicit stakeholder review | not-started | Summarize deltas & pending decisions |

## Acceptance Criteria per Todo
- 2: Confirm each targeted file path; list missing if any.
- 3: New README contains: (a) Implemented vs Pending table, (b) Quick start reflecting decision opt-in, (c) Honest limitations section, (d) Links to API guide & roadmap.
- 4: API_GUIDE.md includes code snippets runnable in isolation, notes upcoming factory; states current manual wiring friction.
- 5: No docstring states "scaffold" for shipping features; each lists Capabilities + Deferred.
- 6: Gate_6_todos.md enumerates concrete tasks (factory, GUI decision default, overlay toggle, tests refactor) with acceptance tests; GATE6_CHECKLIST.md is checkable bullets.
- 7: ROADMAP_REVISED.md clearly shows sequencing & deferrals; aligns with Gate 6 tasks.
- 8: README top-level navigation updated; Copilot instructions only touched if navigation pointer required.
- 9: `grep -R "scaffold" src/econsim/simulation` only returns legitimately future items (documented rationale) or zero results.
-10: Review summary prepared as markdown snippet ready to paste into PR or issue.

## Risks & Mitigations
- Drift between README and roadmap: Mitigated by cross-links & single source-of-truth table reused.
- Over-edit causing merge friction: Keep patches minimal & isolated per file.
- Future factory naming churn: Use neutral placeholder wording in API guide ("forthcoming factory method"), avoid premature naming.

## Next Step
Proceed with Todo 2: inventory target files and confirm presence before drafting new README.
