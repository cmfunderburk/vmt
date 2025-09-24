---
applyTo: '**'
phase: planning
---

# Planning Guidance (Lightweight)

Purpose: Encourage a brief shared understanding before code changes that add new behavior, state, or user-visible options.

Use When:
- Adding a feature / mode / config field
- Changing logic that might affect determinism, performance, or saved state
- Introducing new UI controls or overlays

Skip When:
- Trivial doc / comment edit
- Simple constant tweak explicitly requested
- Pure Q&A

Recommended Planning Reply (Adapt As Needed):
1. Summary: Rephrase the ask in ≤2 sentences.
2. Assumptions: 3–6 bullets (mark unclear items with “(?))”.
3. What Will Change: probable files or systems (names only).
4. Key Questions: list unresolved decisions (optional codes if helpful).
5. Risks (if any): short list (performance, determinism, snapshot, UX).
6. Minimal Plan: ordered steps (each 1 line).
7. Tests (if needed): 2–3 bullets (happy / edge / determinism).
8. Ask User: confirm, adjust, or greenlight.

Principles:
- Keep it short; prefer clarity over exhaustiveness.
- Don’t promise implementation details you can’t justify yet.
- Avoid silent scope creep—call out “Out of scope” if tempting extras appear.

Avoid During Planning:
- Editing code
- Large design essays
- Introducing new randomness or background threads

If Ambiguous:
- Offer 2–3 directional options instead of guessing.

Tone:
- Collaborative, neutral, concise.

Exit Planning:
- User replies with approval or provides decisions → then discuss next steps with user.