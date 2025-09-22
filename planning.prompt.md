---
name: Scaffold: Project Skeleton Planner (Solo + AI)
description: Generate and lint a complete project skeleton specification for a solo developer + AI pairing—including directory tree, stubs, contracts, tooling, and quality gates—before any real code is written.
---

# Scaffold: Project Skeleton Planner (Solo + AI)

## Intent
Create a **practical project skeleton** for **${input:projectName:your project}** through iterative discovery. Focus on rapid validation and implementation readiness rather than comprehensive documentation. Generate scaffolding that enables immediate development start while maintaining quality engineering principles.

## Three-Phase Approach
**Phase 1: Core Understanding (30 min)** - Problem clarity + key scenarios + risk radar  
**Phase 2: Design Contracts (45 min)** - Data model + core interfaces + testing strategy  
**Phase 3: Implementation Readiness (30 min)** - Detailed scaffolding + quality gates + roadmap

## Inputs
- Project name: ${input:projectName}
- Problem statement: ${input:problem}
- Hard constraints: ${input:constraints}
- Context artifact (optional): ${input:contextPath}
- Project type: ${input:projectType:web-app} (web-app, cli-tool, library, service, data-pipeline)

## Global Rules
- No functional code. Only: directory trees, file purpose comments, interface signatures, invariants, pseudocode ≤ limits.
- Stable IDs: requirements `R-##`, modules `M-##`, interfaces `F-##`, assumptions `A-##`, decisions `D-##`, tests `T-##`, scaffolds `S-##` (filesystem assets), workflows `W-##` (automation/CI), quality gates `Q-##`.
- All omissions explicit: state “Not in scope now; becomes relevant when <trigger>.”
- Proposals beyond provided context must be labeled “(Proposal)”.
- Gaps: insert `❗Needs-Decision[D-new]` and add ADR-lite stub in Section 15 (Decision Log).
- Every run ends with **Patch Notes**: changed/added/removed IDs + one‑line reason.
- Avoid hidden coupling: note any cross-module dependency explicitly.

## Output Structure

### Phase 1: Core Understanding (30 min)
1. **Problem & Success Definition**
2. **Key User Scenarios (3-5 flows)**
3. **System Sketch (components + data flow)**
4. **Risk Radar (top 5 risks with impact)**
5. **Assumptions & Validation Experiments**

### Phase 2: Design Contracts (45 min)
6. **Domain Model (core entities + relationships)**
7. **Core Interfaces (3-5 key APIs with intent)**
8. **Error Handling Strategy**
9. **Testing Strategy Outline**
10. **Integration Points & Dependencies**

### Phase 3: Implementation Readiness (30 min)
11. **Directory Structure & File Plan**
12. **Tooling & Quality Setup**
13. **CI/CD Pipeline Sketch**
14. **Implementation Roadmap (MVP focus)**
15. **Decision Log & Next Steps**

## Extended Skeleton Artifacts (Must Appear in Section 15)
- Directory tree (with comments) covering: src/, tests/, docs/, scripts/, ci/, config/, tools/, .github/ (if CI), plus optional examples/.
- Placeholder file specs: filename, purpose, initial content sketch (comment-only template).
- Tooling baseline: lint (e.g., ruff/flake8), formatter (black), type checking (mypy), test runner (pytest), task runner (make/nox/just) — mark chosen ones with decision reference (D-ID).
- CI placeholders: W-IDs for lint, test, type, build, security scan.

## Simplified Templates

### User Scenario Format
```
S-##: <Actor> wants to <Goal>
Flow: <step 1> → <step 2> → <outcome>
Success: <measurable result>
Failure modes: <what could go wrong>
```

### Interface Intent
```
API-##: <name>
Purpose: <why it exists in 1 sentence>
Happy path: <input> → <output>
Error cases: <condition> → <error type>
Key constraint: <business rule or invariant>
```

### Risk Assessment
```
R-##: <risk description>
Impact: High/Med/Low
Likelihood: High/Med/Low  
Validation: <how to test this assumption>
Mitigation: <what we'll do about it>
```

### Directory Structure Template
```
project-name/
├── src/
│   └── <main-module>/     # Core business logic
├── tests/
│   ├── unit/              # Fast, isolated tests
│   └── integration/       # Service interaction tests
├── docs/
│   └── README.md          # Getting started guide
├── scripts/               # Build/deployment automation
└── ci/                    # Continuous integration configs
```

### Decision Record (ADR-Lite)
```
#### D-##: <title>
- Context & Forces:
- Options (≥3) + Trade-offs:
- Criteria & Scoring (table if useful):
- Decision & Rationale:
- Consequences (+ / −):
- Revisit Conditions:
- Review Date:
```

### Traceability Row Pattern
`| R-## | <requirement> | M-## | F-## | T-## | Q-## | A-## | D-## |`

### Quality Gate Definition
| Q-ID | Name | Enforced Stage | Tool/Mechanism | Blocking? | Failure Signal | Auto-fix Strategy |
|------|------|----------------|----------------|-----------|----------------|-------------------|
| Q-01 | Lint Clean | pre-commit | ruff/flake8    | Yes | non-zero exit | autofix + diff    |

## AI Prompt Contracts (Per Section)
- **1 (Scope)**: ≤120 words, list 3–6 falsifiable skeleton success metrics (e.g., “Repo generation script reproduces tree deterministically”).
- **2 (Assumptions)**: Each A-ID gets a counterpoint + validation experiment referencing a concrete artifact or metric.
- **Testing Approach**: What types of tests for which parts
- **Dependencies**: External services, libraries, data sources

### Phase 3: Implementation Readiness (30 min)
- **Directory Structure**: Logical organization for the team size
- **Tooling**: Linting, testing, CI - keep it simple initially
- **Pipeline**: Basic build/test/deploy - complexity comes later
- **Roadmap**: MVP first, then growth features
- **Decisions**: Document key choices and why❗ rationale.
- **11 (Evolution)**: Define semantic version policy; breaking-change protocol; deprecation timeline template.
- **12 (Risks)**: Top ≥8 risks ranked; Risk ≥12 must have pre-build experiment with pass/fail threshold.
- **13 (Traceability)**: No orphan R/M/F/T/Q; list gaps explicitly if found.
- **14 (Decisions)**: Score options against criteria; unresolved = ❗Needs-Decision.
- **15 (Roadmap)**: MVP subset delivering ≥1 success metric; color-code (MVP / Post-MVP / Deferred) textually.
- **16 (Glossary)**: Normalize synonyms; choose canonical term; refer back to sections using them.

## Additional Skeleton-Specific Requirements
- Provide a deterministic **Scaffold Generation Checklist** (step‑by‑step) referencing S-IDs.
- Provide a **Makefile (Stub Layout)** spec (commented tasks only, no logic beyond echo or placeholders).
- Provide initial **pyproject.toml section plan** (tool groups + rationale) without full configs.
- Provide **README seed outline** (headings only + placeholders referencing sections).
- Provide **.gitignore essentials list** with justification.

## Guardrails
- Pseudocode: ≤15 lines per interface (max 3 interfaces with pseudocode). No imports, I/O, network, DB, or algorithmic micro-optimizations.
- Every invariant (I-##) must appear in: a) Postcondition OR b) Property-based test spec.
- No module with >5 responsibilities (else flagged & remediated in roadmap).
- All risks Risk ≥12 mapped to experiment before Gate 0 passes.
- All success metrics must be testable via listed artifacts.
## Quality Gates
- **Phase 1 Gate**: Problem clarity achieved, key scenarios defined, top risks identified
- **Phase 2 Gate**: Core interfaces specified, error handling defined, testing approach outlined  
- **Phase 3 Gate**: Directory structure complete, tooling selected, MVP roadmap ready

## Execution Flow
1. **Phase 1 (30 min)**: Complete sections 1-5, pass Phase 1 Gate
## Execution Flow
1. **Phase 1 (30 min)**: Complete sections 1-5, pass Phase 1 Gate
2. **Phase 2 (45 min)**: Complete sections 6-10, pass Phase 2 Gate  
3. **Phase 3 (30 min)**: Complete sections 11-15, pass Phase 3 Gate
4. **Final output**: Single markdown document with all sections + decision log

## Output Format
Return a single Markdown document with all 15 sections organized by phase. Focus on practical implementation readiness rather than comprehensive documentation.
Provide only delta since prior run: Added/Changed/Removed IDs with a terse justification.

# End of Prompt Specification
