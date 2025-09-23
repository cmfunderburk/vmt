# Gate 6 Release Notes (Draft)

Date: 2025-09-23

## Highlights
- Added `Simulation.from_config` factory for single-step, declarative simulation construction
- Extended `SimConfig` with `enable_respawn` / `enable_metrics` flags and respawn tuning fields
- Overlay (HUD) toggle via 'O' key in demo/GUI without affecting determinism or performance
- Centralized hook attachment (respawn scheduler, metrics collector) inside factory
- Migrated determinism & competition tests to factory path ensuring future consistency

## Stability & Determinism
- All 72 tests passing (determinism, hash, competition, performance guards included)
- Representative determinism hashes:
  - Demo scenario: `b65a6986d3fb8ba5fc37dbe93e9b938b7d8eb06f469372114d494e22cc575000`
  - Seed 42 (40 steps, respawn enabled): `5ecce2f0c835387d4c21f1f19a00d7aaafcc6560d006ab10b6c2912a5ccf8f7d`

## Performance
- 2s perf sample: ~60.98 FPS (target >=60 typical) with overlay code path present
- No regression vs historical baseline; no new per-frame allocations identified

## Demo Run Reference (Sample Variations)
Executed variations to validate deterministic hashes under different flags:
- Baseline CD (steps=8, seed=1111): `647bc3bbfff4ba2fd9c9e3d54f726813c6711c63f4ce471871692afc4663259f`
- Perfect Substitutes (steps=10, agents=2, seed=2222): `5a681e3e216d7107bd832db43f964ee31f13b2afea52512f26e0f56c289e5943`
- Leontief with density scatter (steps=12, seed=3333, density=0.3): `09b3a9c82ae4be8d0b2a2f8bf9f73314ce7b1b6f2c6a2864948da2d507994087`
- CD with respawn gating (steps=15, seed=4444, respawn-every=3): `ea319602a314e8e5822f588030a30cb47b782922cc4a9df0740c50a62361e0fa`
- Random movement legacy variant: (not exposed; skipped this gate)

### Additional GUI Turn-Mode Set (10 steps each @ ~1 tps)
| Variation | Flags | Final Hash |
|-----------|-------|------------|
| 1. CD baseline | `--steps 10 --pref cd --seed 7001 --turn-mode` | `6f701499e4d3dbcc31d4766f2f9c968ccacbcba957f9c80c99995fdc892edf13` |
| 2. Subs 2 agents | `--steps 10 --pref subs --agents 2 --seed 7002 --turn-mode` | `95b7762d6d294df0330d7aa2ce235501879d1b9f05b76f0f2894d10e9018e96e` |
| 3. Leontief density | `--steps 10 --pref leontief --seed 7003 --turn-mode --density 0.3` | `e12ddd914f1a646d6281b59877818edd4ce98504bf1bbb04ca2f2a33dd17e603` |
| 4. CD respawn/tails/fade | `--steps 10 --pref cd --seed 7004 --turn-mode --respawn-every 3 --tail-length 10 --fade-ms 800` | `6f701499e4d3dbcc31d4766f2f9c968ccacbcba957f9c80c99995fdc892edf13` |
| 5. Subs density+respawn no overlay | `--steps 10 --pref subs --seed 7005 --turn-mode --density 0.5 --respawn-every 4 --no-overlay` | `77217de43aa5a38e023f0ef251f3eec419f2b31f88795e1b1938f1232e6c8fe9` |

## API Changes
- Preferred construction pattern: `Simulation.from_config(SimConfig(...))`
- Manual assembly (direct `Simulation(...)` + manual hook assignment) now discouraged (backwards compatible for this gate)
- Configurable flags: `enable_respawn`, `enable_metrics` provide zero-cost (disabled) path when false
- Demo script UX change: GUI is now default; use `--headless` for previous text-table output (legacy `--gui` accepted but deprecated/no-op).

## Upgrade Guide
1. Replace manual simulation wiring with:
   ```python
   cfg = SimConfig(grid_size=(w,h), initial_resources=resources, seed=SEED, enable_respawn=True, enable_metrics=True, ...)
   sim = Simulation.from_config(cfg, agent_positions=[(0,0)])
   ```
2. Remove direct assignments to `respawn_scheduler` / `metrics_collector` (factory manages them when enabled flags are set)
3. Keep determinism tests: no expected hash changes for unchanged seeds / parameters

## Deferred / Known Gaps
- Automated overlay keypress test (manual verification only this gate)
- Environment variable shortcut for legacy random mode (consider future minor enhancement)

## Risks & Mitigations
- Risk: Hidden dependence on manual wiring in downstream user scripts → Mitigation: Clear API guide, deprecation note
- Risk: Specialized tests still touching `sim._rng` for replay/density scenarios → Scoped; documented as acceptable exceptions

## Next Steps (Gate 7 Prep Candidates)
- Add automated overlay toggle test via Qt key event injection
- Introduce optional environment variable for legacy random movement mode
- Expand metrics granularity (per-agent utility snapshots) behind flag

-- End Draft --
