# Revised Transitional Roadmap (Gate 5 → Implementation Gate 1 Breakdown)

Date: 2025-09-22
Author: Planning Automation
Status: Draft (for review before promotion to orientation_docs)

## Rationale
Current codebase (post Validation Gate 4) provides a thin vertical slice (preferences + greedy movement + overlays) but lacks: dynamic environment evolution, metrics/analytics foundation, deterministic replay scaffolding, and configuration ingress. The original Implementation Gate 1 scope is broad (UI polish, zoom/pan, performance indexing). To reduce risk and surface measurable value earlier, we introduce a Transitional Gate 5 and decompose Implementation Gate 1 into smaller sub-gates.

## Overview of Incremental Path
```
Validation Gate 4 (Complete)
        ↓
Gate 5: Dynamics & Metrics Spine (NEW)
        ↓
Impl Gate 1A: GUI Shell & Config Panels
        ↓
Impl Gate 1B: Spatial Scaling & Indexing
        ↓
Impl Gate 1C: Interaction & Visual Ergonomics
        ↓
Implementation Gate 2 (Flexible Preferences UI, Optimization Engine)
```

## Gate 5: Dynamics & Metrics Spine
Purpose: Establish reproducible simulation core with evolving environment and measurement needed for future educational & optimization layers.

### In-Scope
- Resource Respawn Scheduler (deterministic, density-capped)
- Metrics Collection Layer
  - Per-step per-agent metrics: position, mode, carrying, home_inventory, instantaneous utility
  - Aggregate metrics: total resources on grid, average utility, collection rate
- Determinism Hardening
  - Single central RNG (seeded input)
  - Sorted resource iteration for target scoring
  - Determinism hash (SHA256 over concatenated ordered state tuple per step)
- Snapshot & Replay
  - Export JSON snapshot (seed, config, initial resource layout)
  - Replay function verifying identical first N-step determinism hash
- Minimal Config Ingress
  - Load config dict / JSON (grid size, initial resources, perception radius, respawn settings)
- Performance Guard
  - Assert decision+metrics overhead keeps FPS degradation <10% vs pre-Gate5 baseline (micro benchmark)

### Out-of-Scope (Explicit deferrals)
- Pathfinding beyond greedy step
- GUI panels / menus / zoom / pan
- Advanced analytics dashboards
- Scenario library / tutorials
- Agent energy/budget constraints

### Acceptance Criteria
1. Respawn density: After warm-up (W steps), mean resource count within ±5% of configured target density; never exceeds cap (test + assertion).
2. Determinism hash identical across two runs with same seed & config for first N steps.
3. Snapshot → replay reproduces identical per-agent utility series for first N steps.
4. Metrics arrays lengths == steps executed; no missing indices.
5. Sorted iteration removes dependency on dict insertion (test: randomized insertion order yields identical target selection sequence).
6. Performance: (AVG_frame_time_with_metrics - baseline_frame_time) / baseline ≤ 0.10 in micro benchmark.
7. Lint & mypy clean; all existing tests pass; +8 new tests (respawn, metrics integrity, determinism hash, replay, density bounds, sorted scoring, performance delta, snapshot schema).

### Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|-----------|
| Over-collection of metrics hurts performance | Medium | Single structured append per step; avoid per-agent dict merges |
| Respawn randomness introduces flakiness | Medium | Deterministic RNG + fixed test seeds + statistical tolerance windows |
| Hash collisions ignored | Low | Use SHA256 and include all relevant fields (id,x,y,mode,carrying,home_inv,utility) |
| Config sprawl early | Low | Constrain to 5–6 keys; validation errors explicit |

### Deliverables
- `simulation/metrics.py` (collector + hash util)
- `simulation/respawn.py` (scheduler) or integrated in `world.py` minimally
- `tests/unit/test_respawn_density.py`
- `tests/unit/test_metrics_integrity.py`
- `tests/unit/test_determinism_hash.py`
- `tests/unit/test_snapshot_replay.py`
- `tests/unit/test_sorted_scoring.py`
- `tests/unit/test_perf_overhead_gate5.py`
- `tests/unit/test_snapshot_schema.py`
- `Gate_5_todos.md`, `GATE5_CHECKLIST.md`, `GATE5_EVAL.md`

---

## Implementation Gate 1A: GUI Shell & Config Panels
Purpose: Introduce professional window scaffolding without deep feature coupling.

### Scope
- Main window class with menu bar (File: Load Config, Save Snapshot; View: Toggle Overlays; Help placeholder)
- Status bar (FPS, average utility)
- Dockable panel placeholder for future parameter controls
- Basic keyboard shortcuts (pause/resume simulation, single-step)
- Resize handling preserving aspect ratio

### Acceptance Criteria
- Menus functional (hooked to stub actions) with tests for triggered signals
- FPS & avg utility update at ≥1 Hz
- Pause/resume & single-step deterministic (hash unchanged during pause)
- Lint/mypy clean, +6 GUI tests (headless) verifying menu actions and status updates

Out-of-Scope: Preference adjustment UI, theme customization, accessibility features.

---

## Implementation Gate 1B: Spatial Scaling & Indexing
Purpose: Scale to ≥50 agents and ~500 resources without frame degradation.

### Scope
- Spatial index (simple bucket grid or uniform hashing) for nearby resource queries
- Benchmark harness extension measuring select_target avg time with 50 agents / 500 resources
- Adaptive perception radius cost analysis (ensure O(k) local)

### Acceptance Criteria
- Throughput test: ≥50 agents step loop ≤ X ms (define threshold from empirical baseline +20%)
- Index correctness test: results match non-indexed fallback for random sample queries
- Memory overhead documented (<15% increase vs baseline)

Out-of-Scope: A* pathfinding, multi-threading.

---

## Implementation Gate 1C: Interaction & Visual Ergonomics
Purpose: Add essential user ergonomics once data & scaling are stable.

### Scope
- Zoom (integer scale factors) + pan (keyboard or mouse drag)
- Overlay toggles (resources, agents, metrics overlay HUD)
- Color-blind palette toggle
- Basic screenshot export

### Acceptance Criteria
- Zoom/pan do not alter determinism hash
- Performance regression <10% vs Gate 1B baseline at default zoom
- Screenshot contents deterministic under fixed seed

Out-of-Scope: Smooth animation easing, accessibility narration, advanced theming.

---

## Revised Roadmap Table (Early Segment)
| Stage | Focus | Key Artifacts | Exit Proof |
|-------|-------|---------------|------------|
| Gate 5 | Dynamics & Metrics Spine | metrics, respawn, snapshot, hash tests | Density + determinism + perf delta tests green |
| Impl 1A | GUI Shell | main window, menus, status panel | GUI tests + deterministic pause/resume |
| Impl 1B | Scaling & Indexing | spatial index, perf benchmarks | 50-agent perf test passes |
| Impl 1C | Interaction Ergonomics | zoom/pan, overlays, screenshots | Determinism + performance preserved |

---

## Metric Baselines to Capture Before Gate 5 Work
- Baseline frame time (current simple loop) at N_agents=10, N_resources=120
- Decision loop micro time (select_target) distribution
- Current average memory footprint (optional, for regression context)

## Promotion Criteria for This Document
Move from `tmp_plans/` to `orientation_docs/` only after stakeholder sign-off on:
1. Gate 5 scope & acceptance criteria
2. Decomposition of Implementation Gate 1 into A/B/C
3. Agreement on performance and determinism metrics to collect pre-change

## Next Immediate Actions (If Approved)
1. Create `Gate_5_todos.md` + `GATE5_CHECKLIST.md`
2. Add baseline metrics capture script (optional) `scripts/baseline_metrics.py`
3. Begin respawn scheduler implementation

-- END DRAFT --
