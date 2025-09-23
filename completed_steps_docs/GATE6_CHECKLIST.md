# GATE6_CHECKLIST — Integration & Minimal Overlay Toggle

## Factory & Configuration
- [ ] `SimConfig` extended with enable flags & respawn params
- [ ] `Simulation.from_config` implemented
- [ ] Factory attaches respawn when enabled
- [ ] Factory attaches metrics when enabled
- [ ] Internal RNG seeded from config

## GUI Default Behavior
- [ ] Decision mode active by default
- [ ] Env `ECONSIM_LEGACY_RANDOM=1` reverts to legacy path
- [ ] Legacy path still functional (smoke test)

## Overlay Toggle
- [ ] Key `O` toggles overlay state
- [ ] Overlay off by default (doc consistent)
- [ ] Toggle does not alter determinism hash
- [ ] FPS impact <5% over 2s sample

## Tests & Public Surface
- [ ] New `test_factory_integration.py`
- [ ] New overlay toggle test
- [ ] No test references `sim._rng`
- [ ] No direct assignment of `respawn_scheduler` / `metrics_collector` except factory-specific tests

## Determinism & Performance
- [ ] Existing determinism trajectory tests pass unchanged
- [ ] Hash tests unchanged & green
- [ ] Widget perf ≥60 FPS typical, ≥30 FPS floor (overlay on/off)
- [ ] Respawn density convergence unchanged

## Documentation
- [ ] README updated with factory example
- [ ] API_GUIDE updated to include factory section (manual wiring note removed)
- [ ] `ROADMAP_REVISED.md` added & linked
- [ ] Copilot instructions remain accurate or minimally updated if needed
- [ ] Gate_6_todos.md reflects final executed scope

## Quality Gates
- [ ] Lint clean (ruff)
- [ ] Type checks clean (mypy)
- [ ] Format applied (black)

## Evidence for GATE6_EVAL.md
- [ ] Factory code snippet + test reference
- [ ] Before/after perf JSON excerpt
- [ ] Determinism hash sample unchanged
- [ ] Grep results: no private wiring
- [ ] Overlay toggle screenshot / log evidence

-- END --
