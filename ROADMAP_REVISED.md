# Revised Roadmap (Post Documentation Reconciliation – 2025-09-23)

This roadmap resets expectations to align with implemented reality. It sequences integration first, then new economic depth, then user experience enhancements.

## Guiding Principles
- Preserve determinism first; all added features must maintain existing hash & trajectory tests (unless a deliberate gate explicitly evolves invariants).
- Integration before expansion: wire existing components (decision mode, respawn, metrics, config) before adding new mechanics.
- Minimize surface area change per gate; defer speculative abstractions.
- Explicit deferrals documented at each gate boundary.

## Gate 6 – Integration & Minimal Overlay Toggle
Focus: Make the *current* components discoverable and default; consolidate baseline visual & introspection improvements without expanding core economics.
- Factory: `Simulation.from_config(SimConfig)` attaches RNG, respawn, metrics.
- Default decision mode in GUI; legacy random behind env flag.
- Minimal overlay toggle (HUD on/off) – no advanced visuals.
- Square grid rendering (uniform cell geometry) for clearer spatial reasoning (no logic impact).
- Agent metrics panel (dropdown selection → carry bundle + utility) via new controller accessors (`list_agent_ids`, `agent_carry_bundle`, `agent_carry_utility`).
- Alternating multi‑type respawn baseline (A ↔ B) eliminating single‑type drift while remaining O(1) toggle; documented policy + diversity test.
- Tests moved off private internals; adopt factory; new UI + respawn diversity tests (suite size now 104).
- Docs updated (README, API_GUIDE, copilot instructions, this roadmap) reflecting new baseline capabilities.
- Performance parity (overlay + metrics panel overhead negligible; FPS guard maintained).

Deferrals: trading, parameter panels, advanced overlays, economic indicators, weighted/adaptive respawn strategies (future gate will evaluate ratios & adaptive policies under determinism + perf constraints).

## Gate 7 – Trading / Agent Interaction
Prerequisite: Gate 6 integration done.
- Deterministic bilateral trade primitive improving both agents' utilities.
- Interaction scheduling with ordering invariant (position, id) for contest resolution.
- Metrics: trade count, utility deltas (optional hash inclusion after evaluation of stability risk).
- Config flags to enable/disable trading.

Deferrals: multi-good negotiation, multi-step bargaining, pricing, specialization.

## Gate 8 – Basic GUI Controls & Visualization
Prerequisite: Stable trade layer.
- UI controls: start/pause, decision/trade toggles, overlay toggle surfaced in UI, basic parameter sliders (respawn density, perception radius if exposed safely).
- Visual aids: optional agent utility labels, resource density heat shading (performance-tested).
- Persistence: scenario save/load (serialize grid + agents + config subset).

Deferrals: multi-tab analytics, comparative scenario dashboards, heatmap animations.

## Gate 9 – Production & Consumption Dynamics
Prerequisite: Interactive agents & basic UI controls.
- Production: agents generate goods at home or scheduled output based on preference bias.
- Consumption: periodic reduction of home inventory modeling utility decay / need renewal.
- Metrics: per-agent net production, consumption rate, total system output.
- Extended determinism hash fields (after controlled evaluation to avoid instability).

Deferrals: market equilibrium visualization, adaptive preference transitions, multi-sector production chains.

## Future (Beyond Gate 9) – Exploratory Themes
(Not yet scheduled; listed for strategic visibility.)
- Adaptive preferences (learning or fatigue).
- Endogenous price formation (simple Walrasian tâtonnement or trade-clearing auction).
- Multi-good expansion (N-dimensional utility functions with generalized bundle structures).
- Graph-based spatial layouts (non-grid topology).
- Classroom assessment tooling (built-in quizzes / scenario scoring).

## Risk Register (Forward-Looking)
| Risk | Description | Mitigation Gate |
|------|-------------|-----------------|
| Feature creep in Gate 6 | Trading slips back into integration gate | Strict checklist & evaluation sign-off |
| Hash churn in trading | Trade ordering alters existing determinism | Prototype on branch + hash diff analysis before merge |
| UI complexity balloon | Panels added before model stable | Defer UI expansion to Gate 8, enforce scope line |
| Performance regression | Overlays or trade loop add >30% overhead | Micro-bench tests + absolute per-tick budget |
| Config fragmentation | Ad-hoc flags proliferate | Centralize in `SimConfig`; version fields if needed |

## Cross-Document References
- `.github/copilot-instructions.md` – invariants & guardrails
- `API_GUIDE.md` – current public usage patterns
- `completed_steps_docs/Gate_6_todos.md` & `GATE6_CHECKLIST.md` – active execution artifacts
- `completed_steps_docs/GATE5_EVAL.md` – last gate evidence baseline

## Change Control
Any scope additions must be:
1. Proposed as a minimal diff.
2. Mapped to explicit learning or determinism value.
3. Logged in the next gate's todos before implementation.

-- END --
