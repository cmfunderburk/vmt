# Changelog

All notable changes for the simulation & GUI (documentation alignment gate onwards). This file follows a simple reverse‑chronological order. Dates in ISO (YYYY-MM-DD).

## [Unreleased]
- Placeholder for upcoming trading gate entries.

## 2025-09-23 – Documentation Alignment & Baseline Enhancements
### Added
- Square grid rendering (uniform cell size) – visual clarity, no logic change.
- Agent metrics panel: dropdown to select agent + live carry bundle & utility display.
- Controller accessors: `list_agent_ids`, `agent_carry_bundle`, `agent_carry_utility` (read-only, deterministic).
- Random multi-type respawn baseline (A/B) with diversity test ensuring both types present under sustained consumption.
- Deterministic randomized non-overlapping agent home placement (seed+offset secondary RNG) replacing clustered spawn pattern.
- Home label overlay: `H{id}` text rendered in each agent's home cell (cached font, negligible frame cost).
- Diversity & UI tests expanding suite to 104 tests.
- Respawn policy documentation (copilot instructions) establishing random assignment as baseline and gating future adaptive strategies.

### Changed
- README and API Guide updated to reflect new UI components and respawn behavior.
- Roadmap Gate 6 description expanded to include visual & introspection improvements.

### Performance / Determinism
- Verified no metrics hash drift relative to pre-change baseline for identical seeds (hash parity tests unchanged).
- FPS remains within target (no added per-frame allocations in main loop; metrics panel timer isolated from render path).

### Notes
- Weighted or adaptive respawn ratios explicitly deferred and must be gated.
- Next planned gate (Trading) will evaluate hash extension risk before merging trade metrics.
