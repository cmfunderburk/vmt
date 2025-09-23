# GATE DOCS UPDATE CHECKLIST

(Reference: Gate Docs Update – Todos)

| ID | Criterion | Evidence | Done |
|----|-----------|----------|------|
| 1 | README updated with square grid, alternating respawn, agent metrics UI, test count | README diff | [ ] |
| 2 | API guide lists controller accessors (list_agent_ids, agent_carry_bundle, agent_carry_utility) | API_GUIDE.md diff | [ ] |
| 3 | Copilot instructions include Respawn Policy subsection (alternation invariant + complexity guard) | .github/copilot-instructions.md diff | [ ] |
| 4 | Roadmap marks multi-type respawn partial & adds future weighting strategy item | ROADMAP_REVISED.md diff | [ ] |
| 5 | CHANGELOG.md entry dated 2025-09-23 summarizing recent increments | CHANGELOG.md | [ ] |
| 6 | Gate eval addendum (Docs update rationale & risks) exists | GATE_DOCS_UPDATE_EVAL.md | [ ] |
| 7 | Consistency sweep: no lingering single-type respawn claims | Grep log / manual scan note | [ ] |
| 8 | Full test suite passes (>=104 tests) post-doc edits | pytest output snapshot | [ ] |
| 9 | All new sections respect determinism & performance invariants (no conflicting text) | Reviewer note | [ ] |
| 10 | Maintainer sign-off recorded | Sign-off appended to eval | [ ] |

## Sign-Off Section
Maintainer: ____________________  Date: ___________

Notes:
- Evidence column should reference commit hash or attached diff summary.
- If test count increases due to added doc tests, update threshold accordingly.
