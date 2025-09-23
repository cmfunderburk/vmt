# Gate 6 Documentation Reconciliation & Readiness Summary (2025-09-23)

Purpose: Provide stakeholders with a concise record of what changed in the documentation alignment pass and confirm scope boundaries before starting Gate 6 implementation.

## 1. Scope Addressed in This Pass
- Replaced aspirational README with an accurate state snapshot; archived old version as `README_aspirational.md`.
- Added `API_GUIDE.md` (manual wiring patterns; pre-factory).
- Added `ROADMAP_REVISED.md` with realistic Gate 6–9 sequencing (integration → interaction → GUI controls → production/consumption).
- Reauthored Gate 6 execution artifacts: `Gate_6_todos.md` and `GATE6_CHECKLIST.md` (integration-focused; trading deferred).
- Cleaned simulation module docstrings (removed "scaffold" terminology; each now lists Capabilities + Deferred features).
- Added cross-links & quick navigation section to `README.md`; referenced roadmap in `.github/copilot-instructions.md`.

## 2. Key Decisions (Locked)
1. Gate 6 is strictly an integration gate (factory + default decision mode + minimal overlay toggle).
2. Trading / interaction features begin in Gate 7 only.
3. Overlay scope for Gate 6 = single HUD on/off toggle (no panels or data-heavy overlays).
4. `Simulation.from_config(SimConfig)` will conditionally attach respawn & metrics based on config flags.
5. Tests will migrate to factory usage; private hook mutation removed.

## 3. Current Gaps (Intentionally Deferred)
| Area | Deferred To | Rationale |
|------|-------------|-----------|
| Trading / bilateral exchange | Gate 7 | Preserve focused integration diff |
| GUI parameter panels | Gate 8 | Avoid UI surface churn before stable core |
| Utility contours / heatmaps | Later visualization gate | Performance & scope control |
| Production & consumption loops | Gate 9 | Requires stable interaction layer |
| Extended economic metrics (inequality, welfare indices) | Post Gate 6/7 | Depends on interaction & production dynamics |

## 4. Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|-----------|
| Factory alters ordering → hash drift | Breaks determinism tests | Attach hooks pre-step; keep agent iteration identical |
| Overlay reduces FPS | Perf regression (<60 FPS typical) | Minimal draw ops; perf stub overlay on/off delta (<5%) |
| Test migration brittleness | Flaky CI during transition | Incremental migration; add factory fixture; keep legacy tests until parity |
| Scope creep (trading sneaks into Gate 6) | Delays integration close | Checklist enforcement + evaluation gating |
| Config sprawl | Hard-to-track flags | Centralize in `SimConfig`; version if new fields accrue |

## 5. Acceptance Criteria Snapshot (Gate 6)
- Factory: constructs sim w/ deterministic RNG + respawn + metrics when enabled.
- GUI: decision mode default (legacy random behind env `ECONSIM_LEGACY_RANDOM=1`).
- Overlay: key `O` toggles, off by default, <5% perf delta.
- No direct test mutation of internal hooks or `_rng` access.
- Determinism & hash tests unchanged and passing.
- Perf: ≥60 FPS typical, floor ≥30 FPS.
- Docs updated to show factory usage (manual wiring section reduced/removed).

## 6. Open Questions for Final Confirmation
| Question | Proposed Default | Need Stakeholder Input? |
|----------|------------------|-------------------------|
| Overlay toggle key binding | `O` | Optional (change if conflict) |
| Env var name for legacy random | `ECONSIM_LEGACY_RANDOM` | Only if naming policy differs |
| Expose perception radius in `SimConfig` now? | Defer to Gate 8 (UI) | Yes (confirm deferral) |
| Include minimal logging on factory use? | Quiet by default | Optional |

## 7. Next Implementation Steps (Upon Approval)
1. Extend `SimConfig` (fields: enable_respawn, enable_metrics, respawn params, maybe seed default).
2. Implement `Simulation.from_config` (attach hooks, seed RNG, return instance).
3. Flip GUI default path to decision mode (env flag fallback).
4. Implement overlay toggle logic in widget; integrate into paint path.
5. Add / refactor tests: factory integration, overlay toggle, no private wiring.
6. Update docs (README + API_GUIDE) replacing manual wiring emphasis with factory example.
7. Perf & determinism re-validation; capture before/after JSON & hash for `GATE6_EVAL.md`.

## 8. Evidence of Documentation Alignment
| Artifact | Status |
|----------|--------|
| README (accurate vs pending) | Updated |
| API Guide (manual wiring) | Added |
| Roadmap (revised) | Added |
| Gate 6 Todos & Checklist | Added / Revised |
| Module Docstrings cleaned | Yes |
| Copilot Instructions reference roadmap | Yes |
| Residual 'scaffold' terminology | Removed |

## 9. Recommendation
Proceed with Gate 6 coding after confirming open questions (overlay key, env var, perception radius deferral). Keep initial PR narrow: `SimConfig` extension + factory + minimal test; follow with GUI default + overlay in a second PR to isolate risk.

## 10. Approval Sign-Off (Fill During Review)
| Reviewer | Decision | Notes |
|----------|----------|-------|
| Stakeholder | ✅ / ❌ | |
| Technical Lead | ✅ / ❌ | |

-- END --
