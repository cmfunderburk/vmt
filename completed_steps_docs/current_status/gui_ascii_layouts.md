# GUI ASCII Layouts

Date: 2025-09-24
Scope: High-level spatial sketches (not pixel‑accurate) of current / planned GUI surfaces.

Legend:
- `[]` Checkbox  | `( )` Radio / exclusive option | `[#####]` Progress / filled area (illustrative)
- Uppercase labels = section headers; monospace alignment approximates proportional layout
- Viewport is fixed 320x320 embedded Pygame surface; surrounding panels are PyQt widgets.

---
## 1. Start Menu (Initial Screen)

```
+----------------------------------------------------------------------------------+
| VMT EconSim (Start Menu)                                                         |
|----------------------------------------------------------------------------------|
| Scenario: [ baseline            v ]                                              |
|            (Other future: bilateral_exchange, money_market)                     |
|                                                                                  |
| Preferences (initial agents)                                                     |
|   Count:          [   4 ]                                                        |
|   Pref Mix:       [ Cobb-Douglas  v ]                                            |
|                                                                                  |
| Endowment Pattern: [ uniform         v ] (inactive in baseline)                  |
|                                                                                  |
| Seed:             [  1234 ]   [Randomize]    Start Paused [x]                    |
|                                                                                  |
| Respawn Interval: [ Off  v ]   (Off / 1 / 2 / 5 / 10)                            |
| Decision Mode:    (o) Enabled    ( ) Disabled                                    |
|                                                                                  |
| Advanced (collapsed) ▸                                                          |
|   When expanded:                                                                |
|     Grid Size:         [ 12 ] × [ 12 ]                                          |
|     Resource Density:  [ 0.25 ]                                                 |
|     Perception Radius: [ 8 ]                                                    |
|     Viewport Size:     [ 320 ] × same (square)                                  |
|     Metrics Enabled:   [x]                                                      |
|                                                                                  |
|----------------------------------------------------------------------------------|
| [ Launch Simulation ]   [ Quit ]                                                |
+----------------------------------------------------------------------------------+
```

Notes:
- Only baseline scenario currently active. Future scenarios (bilateral_exchange, money_market) appear in dropdown but may be disabled.
- Start Paused checkbox sets controller paused state before first step.
- Randomize button reseeds both internal and external RNG seeding plan.
- Advanced panel remains collapsed by default for classroom simplicity.
- Viewport Size controls the square Pygame surface dimensions (320x320 to 800x800).

---
## 2. Baseline Simulation Screen (Post-Launch)

High-level layout: Viewport left; stacked control / overlay / metrics panels on right.

```
+----------------------------------------------------------------------------------+
| VMT EconSim (Simulation)                                                         |
|----------------------------------------------------------------------------------|
| +-----------------------------+  +--------------------------------------------+  |
| | PYGAME VIEWPORT (configurable) | CONTROLS                                    |  |
| |                             |  |--------------------------------------------|  |
| |  [Grid of cells]            |  |  [Pause/Resume]  [Step 1]  [Step 5]        |  |
| |  Agents: A0 A1 ...          |  |  Turn Rate: [ Unlimited  v ]               |  |
| |  Resources (if respawn)     |  |  Hash:  f3b9...   [Refresh]                |  |
| |  Overlay legends            |  |                                            |  |
| +-----------------------------+  | OVERLAYS                                   |  |
|                                  |  [x] Grid      [x] Agent IDs               |  |
|                                  |  [x] Home Labels [x] Targets               |  |
|                                  |                                            |  |
|                                  | METRICS                                    |  |
|                                  |  Step:  128                                 |  |
|                                  |  Agents: 4   Resources: 17                  |  |
|                                  |  Carry g1: 11  Carry g2: 6                  |  |
|                                  |  Home g1: 3   Home g2: 9                    |  |
|                                  |  Steps/sec: 61.8 (est)                      |  |
|                                  |                                            |  |
|                                  | AGENT INSPECTOR                            |  |
|                                  |  Agent: [ 0  v ]                            |  |
|                                  |  Carry: (g1=2, g2=1)                        |  |
|                                  |  Utility: 4.732                             |  |
|                                  |                                            |  |
|                                  | [ Back to Menu ]                            |  |
| +-----------------------------+  +--------------------------------------------+  |
| | Status / Overlay Footer: Grid On | Overlay: ON | Mode: Decision | Paused: No | |
| +-------------------------------------------------------------------------+----+ |
+----------------------------------------------------------------------------------+
```

Notes:
- Steps/sec estimator uses rolling window; not hashed.
- Hash refresh is manual to avoid redundant CPU when paused.
- Agent Inspector updates at ~4 Hz timer independent of frame draw.
- All overlay toggles are state->render only (no mutation of simulation state).

Future Additions (Placeholder Regions):
- Money Mode: price & market money line inserted below METRICS.
- Bilateral Mode: partner / trades completed counters under METRICS.
- Replay Controls: potential bottom footer bar (play/pause/seek) reserved space.

---
## 3. Change Impact & Determinism Safeguards

| Component            | Determinism Impact | Notes |
|----------------------|--------------------|-------|
| Overlay toggles      | None (render only) | Excluded from hash path. |
| Agent Inspector timer| None               | Read-only snapshot of agent state. |
| Hash Refresh button  | Triggers recompute | Payload strictly canonical & idempotent. |
| Turn Rate gate       | Affects WHEN steps happen, not ordering logic; hash parity holds if sequence identical. |
| Back to Menu         | Full teardown (timer stop, pygame quit) then start menu bootstrap. |

---
## 4. Minimal Implementation Checklist (GUI Layout)

1. Start Menu widget factory (scenario dropdown, seed line edit, Start Paused checkbox, Randomize button, advanced panel).
2. Simulation shell: left viewport container + right vertical panel.
3. Controls group box: pause/resume, step buttons, turn rate combo, hash label & refresh.
4. Overlays group: checkboxes bound to overlay state dataclass.
5. Metrics group: labels updated each frame (or small throttle) but hashed state comes only from simulation internals.
6. Agent Inspector group: combo box (sorted agent IDs), dynamic labels.
7. Footer status bar summarizing toggles & mode.
8. Determinism test: identical hash for N steps with overlays toggled different ways.

---
## 5. Risks / Open Questions

| Risk / Question | Mitigation | Status |
|-----------------|-----------|--------|
| Panel width creep causing viewport shrink | Fixed width constraint | Plan |
| Excess repaint from rapidly toggling overlays | Coalesce state changes (single update()) | Plan |
| Hash recompute overhead if user spams refresh | Debounce (optional) | Defer |
| Future modes adding vertical clutter | Collapsible group boxes | Plan |

---
*End of document.*
