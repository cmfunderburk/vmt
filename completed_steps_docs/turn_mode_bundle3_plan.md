# Turn Mode Bundle 3 Implementation Plan

Bundle 3 Goal: Transform current GUI demo into a clear, pedagogical, turn-based visualization with:
1. Gridlines and cell clarity
2. Resource glyph improvements (visibility when agent overlaps + optional fade-out)
3. Turn overlay (turn number, remaining resources, per-agent carrying/home, utility snapshot)
4. Movement highlight (recently moved agents) and breadcrumb tail (last N positions)
5. Slower / controllable auto-run pacing & explicit paused start
6. Randomized sparse resource layout option + density flag (with deterministic seeding)
7. Optional respawn every K turns (configurable) to keep board populated
8. Background animation suppression in turn mode (static neutral background)
9. Performance safety: maintain ~60 FPS idle; turn step cost remains below existing perf guards
10. Clean configuration flags & README update

---
## Assumptions / Constraints
- Do NOT alter core simulation logic ordering or agent decision semantics.
- Keep `EmbeddedPygameWidget` backward compatible; enhancements layered via subclass/composition (avoid breaking existing tests).
- Determinism preserved: all random placement and respawn must use seeded RNG from config or wrapper.
- Minimal new dependencies (pure pygame drawing additions only).

---
## Proposed Flags / CLI Additions
Add to `demo_single_agent.py`:
- `--grid-lines` (bool; default auto-on in turn mode)
- `--density FLOAT` (0<d<=1; default 0.18) activates random placement overriding checkerboard
- `--respawn-every N` (int; 0 disables) apply respawn scheduler every N turns (reuse existing RespawnScheduler with target density & rate defaults)
- `--tail N` breadcrumb length (default 4)
- `--fade-ms MS` resource fade duration after collection (0 disables; default 500)
- `--pause-start` start with zero pending steps (default True when turn mode)
- `--overlay` enable turn overlay (on by default in turn mode)
- `--auto-interval` already exists (used when auto mode toggled)

---
## Architectural Additions
1. Rendering Enhancements Layer
   - Introduce a lightweight `TurnRenderState` dataclass to track:
     - `recent_moves: dict[agent_id, int]` (frames since move) for highlight
     - `tails: dict[agent_id, deque[tuple[int,int]]]`
     - `fading_resources: list[(x,y,type,start_time)]` for fade-out
   - Manage state inside TurnWidget (not in simulation core).

2. Resource Collection Hook
   - After each step, compare pre/post resource sets OR intercept `grid.take_resource_type` via monkey-patch/wrapper.
   - Simpler: before step, snapshot keys; after step, diff sets to identify removed coordinates & start fade timers.

3. Breadcrumb Update
   - On each actual turn advance, append agent position to tail (only when changed). Trim to length N.

4. Overlay Drawing
   - Use pygame.font (ensure it initializes safely); fallback to basic text skip if font fails.
   - Display: Turn, Remaining Resources, Agent lines: `A0 pos=(x,y) carry=(g1,g2) home=(h1,h2)`
   - Utility snapshot (compute using `preference.utility` on carrying or combined home+carrying?) => pick carrying for marginal view.

5. Gridlines
   - Draw once per frame after clearing background: vertical & horizontal lines; light gray.
   - Adjust cell size calculation unchanged; overlay lines only if flag active.

6. Highlight / Fade Drawing Order
   - Draw resources (base color or faded alpha) BEFORE agents.
   - Then draw tail (small semi-transparent squares or thin outline).
   - Then agents (solid) + highlight outline (white) if moved this turn (recent_moves[agent_id]==0).

7. Fade Logic
   - On fade-enabled: maintain timestamp (perf_counter) and compute alpha = max(0,1 - dt/fade_duration).
   - Draw fading resource as tinted rectangle with alpha (use convert_alpha surface or temporary surface blit).

8. Respawn Every K Turns
   - If `--respawn-every > 0` and (turn_count % K == 0 and turn_count>0): call `respawn_scheduler.step(...)` manually BEFORE metrics record (or reuse simulation hook by attaching scheduler and letting normal step do it—BUT gating frequency would require wrapper).
   - Simpler: use existing scheduler each turn but set rate low; or implement custom gating: keep scheduler but skip call except on required turns by toggling `enabled` flag or wrapping `step`.

---
## Step-by-Step Implementation Plan

1. Planning & Flag Wiring
   - Add new CLI flags to `demo_single_agent.py` (density, respawn-every, tail, fade-ms, grid-lines, pause-start, overlay).
   - Adjust `build_grid()` to support deterministic random scatter when `--density` present: iterate all cells; if rng.random() < density add resource with type chosen by parity or rng choice.

2. TurnWidget Enhancements
   - Extend existing TurnWidget to include `TurnRenderState`.
   - Add methods: `_before_step_capture()`, `_after_step_update()` invoked around wrapper step (Modify DecisionWrapper.step to call optional callbacks when a step actually occurs).

3. Recent Move & Tail Tracking
   - On each successful step: for each agent, if position changed from previous stored pos, push to tail and set recent_moves[agent_id]=0 else increment all existing counters each frame.

4. Fade-Out Tracking
   - `_before_step_capture`: store set of resources = set(grid._resources.keys()) (direct attribute access acceptable inside demo).
   - After step: compute removed = before - after; for each coordinate in removed store (x,y,type,start_time).
   - During draw: filter out expired fades (dt > fade_ms).

5. Rendering Order Update in TurnWidget
   - Override a new hook or monkey-patch: Instead of relying solely on EmbeddedPygameWidget._update_scene, subclass overrides and calls super partially or re-implements with conditions:
     - If turn-mode: static neutral background (e.g., dark slate), optional skip legacy moving rectangle.
     - Draw gridlines if enabled.
     - Draw resources & fading resources.
     - Draw tails.
     - Draw agents + highlight outline.
     - Draw overlay text if enabled.

6. DecisionWrapper Integration
   - Add callbacks passed to wrapper: `on_pre_step`, `on_post_step` invoked only when a step occurs (not each frame).
   - Connect these to TurnWidget so state updates near-synchronously with simulation changes.

7. Respawn Gating (optional but in scope)
   - If `--respawn-every` > 0 attach scheduler normally but inside wrapper, maintain a local turn counter and only call `respawn_scheduler.step(...)` on matching turns (manually) and set `sim.respawn_scheduler=None` to prevent double invocation.

8. Determinism Guard
   - Ensure any new random resource placement uses seeded RNG: `rng = random.Random(args.seed + 1001)`.
   - Fade animations must not influence determinism hash (they won’t if we keep hash logic unchanged and fade state purely visual).

9. Performance Check
   - Run existing perf tests (should be unaffected because they use non-turn path).
   - Possibly add a lightweight self-check: measure ms per step for 200 steps in headless mode if needed (optional).

10. README Update
   - New subsection: Turn Mode Demo Controls & Visualization Features.

11. (Optional) Tests
   - Minimal: a unit or smoke test verifying grid generation with density stub (headless) and deterministic resource count.
   - Tail & fade purely visual (skip automated test for now to keep scope light).

---
## Data Structures
```python
@dataclass
class TurnRenderState:
    prev_positions: dict[int, tuple[int,int]]
    tails: dict[int, collections.deque[tuple[int,int]]]
    recent_moves: dict[int, int]  # frames since last move (0 = just moved)
    fading: list[tuple[int,int,str,float]]  # x,y,type,start_time
```

---
## Open Decisions / Clarifications Needed
- Tail representation: outline vs filled semi-transparent squares? (Default: small filled semi-transparent.)
- Utility overlay: carry-only vs carry+home? (Recommend carry-only for marginal behavior.)
- Fade alpha function: linear vs ease-out? (Linear for simplicity.)
- Respawn target density default when using `--respawn-every`: reuse 0.18? (Yes.)

---
## Rollout Sequence (Coding Chunks)
1. Flags + randomized grid (with deterministic seed)
2. Wrapper callbacks + state capture (before/after step)
3. TurnRenderState + tail & move tracking
4. Fade collection detection
5. Rendering override (gridlines, resources, tails, agents, overlay)
6. Respawn gating (optional flag) + integrity check
7. README update + smoke test (grid density determinism)

---
## Acceptance Criteria
- Launch with `--gui --turn-mode --grid-lines --density 0.15 --tail 5 --fade-ms 600 --respawn-every 5` shows:
  - Visible gridlines
  - Sparse random resources gradually consumed with fade-out effect
  - Agents highlight immediately after each step (outline) and breadcrumb tail persists (max length)
  - Overlay text updates turn count & remaining resources
  - Deterministic resource initial placement reproducible by repeating command with same seed
  - Exiting after N steps still reports final determinism hash (hash unchanged by visual features)

---
## Deferred (Not in Bundle 3 unless requested)
- Path preview lines
- Per-agent utility sparkline
- Mouse interaction (click to enqueue steps)
- Save/load visual configuration

---
END OF PLAN
