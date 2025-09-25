# VMT EconSim Platform

An educational microeconomic simulation prototype combining a PyQt6 desktop shell with a deterministic spatial agent model (preferences, resource collection, decision logic).

> This README reflects the **current state after Gate 6 integration (factory, decision default, overlay toggle, perf safeguards)**. The previous aspirational narrative lives in `README_aspirational.md`.

## 1. Snapshot: Implemented vs Pending

| Area | Implemented (Usable) | Pending / Not Yet Integrated |
|------|----------------------|-------------------------------|
| Rendering Core | PyQt6 window + embedded Pygame surface (~62 FPS, configurable 320×320 to 800×800) | GUI controls / menus / scenario panels |
| Preferences | Cobb-Douglas, Perfect Substitutes, Leontief + factory | N-good generalization, adaptive forms |
| Grid & Resources | Typed resources (A,B) with deterministic iteration | Quantities >1 per cell, spatial clustering |
| Agents | Carrying vs home inventories with wealth accumulation, modes, greedy decision, tie-break determinism, randomized non-overlapping home placement + on-grid home labels (H{id}), utility reflects total wealth (carrying + home) | Trading, production/consumption, richer behaviors |
| Decision Mode | Greedy ΔU selection (epsilon bootstrap) + tests; GUI default ON; env / param override | Multi-step planning |
| Respawn | Dual GUI controls: **Interval** (Off/1/5/10/20 steps, default 20) + **Rate** (10%/25%/50%/75%/100% deficit replenishment, default 100%). Random A/B type assignment, uniform seeded placement. | Weighted / adaptive multi-type distribution, richer policies |
| Metrics | Factory-attached collector + determinism hash | Additional economic metrics suite |
| Snapshot / Replay | Serialize + restore + hash parity tests | Scenario library management |
| Configuration | `SimConfig` + `Simulation.from_config` factory | Extended scenario descriptors |
| Overlays / HUD | Toggleable overlay + grid lines (key 'O'); regression + perf neutrality tests | Utility contours, advanced UI panels |
| Tests | Determinism, decision precedence, respawn, metrics, snapshot, perf (FPS + throughput), overlay regression | Extended educational UI interaction tests |

## 2. Current Reality (Post Gate 6)
Gate 6 delivered: factory construction, GUI default decision mode (env override `ECONSIM_LEGACY_RANDOM=1` or widget param), overlay toggle, conditional respawn/metrics wiring, overlay regression test, decision step throughput safeguard. Subsequent increment: uniform seeded respawn distribution (removed top-left bias) + GUI respawn interval dropdown.

## 3. Quick Start (Current Behavior)
```bash
python3 -m venv vmt-dev
source vmt-dev/bin/activate
pip install -e .[dev]

# Launch new GUI (Start Menu → choose scenario, configure viewport size). Decision mode ON by default; press 'O' in simulation to toggle overlay.
make dev

# (Optional) Run legacy minimal bootstrap window (no Start Menu) instead of new GUI
ECONSIM_NEW_GUI=0 make dev

# Run full test suite (decision, determinism, respawn, metrics, snapshot, perf)
pytest -q

# Performance sample (widget)
python scripts/perf_stub.py --mode widget --duration 2 --json

# Force legacy random walk (regression / comparison)
ECONSIM_LEGACY_RANDOM=1 make dev
```

## 4. Factory Construction (Preferred)
Use the factory for deterministic, hook-aware simulation setup:
```python
from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation  # (typo fixed)
import random

cfg = SimConfig(
	grid_size=(12,12),
	initial_resources=[(2,2,'A'), (4,5,'B')],
	perception_radius=8,
	respawn_target_density=0.25,
	respawn_rate=0.4,
	max_spawn_per_tick=3,
	seed=123,
	enable_respawn=True,
	enable_metrics=True,
	viewport_size=640,  # configurable 320-800
)
sim = Simulation.from_config(cfg, agent_positions=[(0,0)])
ext_rng = random.Random(999)
for _ in range(40):
	sim.step(ext_rng, use_decision=True)
print("hash=", sim.metrics_collector.determinism_hash())
```
Legacy manual wiring is supported but deprecated.

## 5. Known Gaps / Explicit Limitations
1. Trading, production, consumption, and economic metrics (e.g., inequality) not implemented.
	- Planned invariant (pre-implementation): only items currently being carried will ever be eligible for bilateral exchange; home (banked) inventory is non-circulating during trade resolution.
2. Advanced overlays (utility contours, analytics) not implemented.
3. Multi-scenario educational progression system not yet built.

### 5.1 Bilateral Exchange (Experimental – Gate Bilateral2 Phase 3)
Status: Single-unit reciprocal trade prototype behind UI + environment flags. Phase 3 adds optional priority reordering (flag-gated) and a fairness_round advisory metric. Determinism hash unchanged when features disabled.

Activation Paths:
* Start Menu (Advanced): enable trade draft / execution toggles (if exposed) or master checkbox.
* Runtime: Controls panel Trade Controls group:
	* Master (Draft+Exec) – enables both draft enumeration and execution.
	* Draft Intents – enumerate intents only.
	* Execute Trades – execute highest-priority intent (implies draft).
	* Debug Overlay – shows first few intents + last executed summary (requires draft).

Feature Flags (auto-managed by GUI when toggled):
* `ECONSIM_TRADE_DRAFT=1` – enumerate draft intents (no execution).
* `ECONSIM_TRADE_EXEC=1` – execute at most one intent per step (implies draft enumeration).
* `ECONSIM_TRADE_GUI_INFO=1` – show executed trade summary overlay line.
* `ECONSIM_TRADE_DEBUG_OVERLAY=1` – (internal helper; currently tied to Debug Overlay toggle).

Current Mechanics:
* Rule: single reciprocal marginal utility improvement (approx) triggers one unit swap of (good1 ↔ good2).
* Intent Fields: seller, buyer, give_type, take_type, delta_utility (approx combined marginal lift), priority tuple.
* Metrics (hash-excluded): `trade_intents_generated`, `trades_executed`, `trade_ticks`, `no_trade_ticks`, `realized_utility_gain_total`, `last_executed_trade`, `fairness_round` (increments per executed trade; advisory only).
* Inspector: shows last trade summary when enabled; cleared immediately upon disable.

Determinism Safeguards:
* Feature off (default) → simulation identical to pre-trade build.
* All trade metrics excluded from determinism hash; delta_utility informational only.
* Priority reordering gated (`ECONSIM_TRADE_PRIORITY_DELTA`) leaving baseline ordering intact when off.

Phase 3 Delivered:
* Priority flag `ECONSIM_TRADE_PRIORITY_DELTA=1` sets intent priority to `(-delta_utility, seller_id, buyer_id, give_type, take_type)`.
* `fairness_round` metric increments per executed trade (advisory, hash-excluded).
* Multiset invariance test ensures flag only changes ordering (not which intents exist).
* Autouse test fixture clears `ECONSIM_TRADE_*` flags preventing cross-test leakage.

Future: multi-intent policies, fairness-driven scheduling, analytics overlays.

### 5.2 Foraging Enable Flag

The baseline resource collection ("foraging") can now be disabled at runtime for instructional contrast with pure trading scenarios.

Environment Flag:
* `ECONSIM_FORAGE_ENABLED=1` (default if unset) – agents move, target, and collect resources.
* `ECONSIM_FORAGE_ENABLED=0` – disables collection logic; when trading disabled agents deterministically return home & idle; when trading enabled they may participate in trades without gathering new goods.

GUI Controls:
* Controls Panel → "Foraging Enabled" checkbox reflects and mutates the flag (sets explicit `0` rather than deleting to preserve disabled state deterministically).

#### 5.2.1 Idle Path Semantics (Updated)
When both foraging and trading features are disabled (`ECONSIM_FORAGE_ENABLED=0`, `ECONSIM_TRADE_DRAFT` unset/`0`, `ECONSIM_TRADE_EXEC` unset/`0`), agents now immediately enter an idle state without marching home and depositing carried goods. This change:
* Preserves any pre-existing carrying inventory for invariance across feature toggles during demonstrations.
* Avoids silent inventory mutation that could confuse students when toggling systems on/off mid-session.
* Keeps per-step complexity O(agents) with no extra movement calculations.

Educational Rationale: The previous behavior (deterministic return-home + deposit) obscured the contrast between active collection vs. inactive economic systems. The new idle semantics make the “nothing is happening because both systems are off” state visually and analytically transparent.

No changes to determinism hash were required; the path is purely a no-op w.r.t. inventories and positions.

### 5.3 Behavior Gating Matrix

Decision mode per-step behavior depends on combinations of Foraging and Trade settings:

| Forage | Trade Draft | Trade Exec | Resulting Behavior |
|--------|-------------|------------|--------------------|
| Off | Off | Off | Agents move toward home then idle; no intents |
| Off | On | Off | Intents enumerated (may be empty); no execution |
| Off | On | On | Intents enumerated; at most one trade executed per step |
| On | Off | Off | Normal collection only |
| On | On | Off | Collect first; non-foraging agents (if any) can draft intents |
| On | On | On | Collect first; non-foraging agents can trade (one execution) |

Note: When both foraging and trading are enabled, any agent that successfully collected a resource this step is excluded from that step's trade enumeration ("forage first then trade" educational sequencing).

### 5.4 Executed Trade Visual Feedback

Recent executed trade cell is outlined with a pulsing highlight (deterministic timing) for a short fixed window (currently 12 steps) when overlays are visible, aiding classroom narration without altering simulation state.

### 5.5 Determinism Hash Parity (Temporary Deferral)

The determinism hash currently includes agents' carrying inventories. Since execution mutates carrying bundles, draft-only vs draft+execution runs diverge. A previously strict parity test (`test_hash_parity_execution_flag`) has been marked `xfail` with an explicit reason while a future hash design revision (likely separating carrying vs banked wealth or introducing a controlled canonical post-trade normalization) is scoped. All other determinism guarantees remain intact.

## 6. Gate 6 (Integration Summary)
Delivered:
* `Simulation.from_config` (seeded RNG + optional respawn & metrics)
* GUI defaults to decision mode (env override `ECONSIM_LEGACY_RANDOM=1` or widget param `decision_mode=False`)
* Overlay/grid toggle (key 'O') + overlay regression (byte-diff) test
* Decision step throughput safeguard test (raw stepping floor)
* Test migration reducing private attribute reliance (only specialized replay/density cases remain)
* Documentation synchronization (README, copilot instructions, Gate 6 eval)
Deferred: advanced GUI panels, utility contours, economic interactions.

## 7. Roadmap (High-Level Forward View)
| Gate | Theme | Core Scope | Deferrals |
|------|-------|-----------|-----------|
| 6 | Integration & Surface | Factory, default decision mode, overlay toggle, test API cleanup | Advanced GUI panels |
| 7 | Agent Interaction | Trading primitives, exchange rules, utility effect tests | UI trade inspector |
| 8 | Basic GUI Controls | Parameter sliders, run/pause, scenario load/save | Multi-tab analytics |
| 9 | Production / Consumption | Resource generation & consumption cycles | Market equilibrium visualization |

Detailed sequencing lives in [`ROADMAP_REVISED.md`](ROADMAP_REVISED.md) and the Gate 6 execution list in [`completed_steps_docs/Gate_6_todos.md`](completed_steps_docs/Gate_6_todos.md).

## 8. Contributing
Follow gate workflow (see `.github/copilot-instructions.md`). For post-Gate 6 work keep PRs narrowly scoped (integration polish vs. new mechanics) unless entering a new gate.

## 9. Testing & Determinism Notes
Determinism enforced via: sorted resource iteration, tie-break key (−ΔU, dist, x, y), agent list ordering, epsilon bootstrap for zero bundles, canonical metrics hash. Adjust any of these only with explicit gate-scoped justification.

## 10. Reference Documents
| Document | Purpose |
|----------|---------|
| `README_aspirational.md` | Archived earlier goals / narrative (superseded) |
| `completed_steps_docs/GATE6_EVAL.md` | Gate 6 evidence mapping |
| `completed_steps_docs/GATE5_EVAL.md` | Gate 5 evidence (historical) |
| `orientation_docs/Implementation Roadmap.md` | Original long-form plan (pre-reconciliation) |
| `.github/copilot-instructions.md` | High-signal constraints & invariants |
| `scripts/perf_stub.py` | Performance validation harness |

See also: `API_GUIDE.md` (usage) and `ROADMAP_REVISED.md` (forward plan).

### Quick Navigation
| Resource | Link |
|----------|------|
| API Guide | [`API_GUIDE.md`](API_GUIDE.md) |
| Revised Roadmap | [`ROADMAP_REVISED.md`](ROADMAP_REVISED.md) |
| Gate 6 Todos | [`completed_steps_docs/Gate_6_todos.md`](completed_steps_docs/Gate_6_todos.md) |
| Gate 6 Checklist | [`completed_steps_docs/GATE6_CHECKLIST.md`](completed_steps_docs/GATE6_CHECKLIST.md) |
| Copilot Instructions | [`.github/copilot-instructions.md`](.github/copilot-instructions.md) |

---
Last updated: 2025-09-24 (Bilateral Phase 3: priority flag + fairness_round; GUI enhancements – configurable viewport, agent wealth accumulation, complete GUI controls).

### Recent Increment (Configurable Viewport, Agent Wealth Accumulation, Complete GUI)
Added:
* **Configurable Viewport**: Pygame surface size selectable from 320×320 to 800×800 (square constraint) in Start Menu Advanced panel. Maintains determinism and performance across all sizes.
* **Agent Wealth Accumulation**: Agents now accumulate goods at home base. Utility calculation includes total wealth (carrying + home inventory). GUI shows both "Carry:" and "Home:" inventories separately in Agent Inspector panel.
* **Complete GUI Controls**: Full-featured Start Menu with scenario selection, parameter configuration, and Advanced panel (grid size, density, perception radius, viewport size). Simulation page includes grouped panels: Controls, Overlays, Metrics, Agent Inspector.
* **Enhanced Agent Inspector**: Individual agent state tracking with dropdown selection, separate display of carrying vs home inventories, and total utility calculation reflecting accumulated wealth.
* **Multi-type respawn baseline**: scheduler assigns random resource types A/B deterministically ensuring diversity without added per-step complexity.
* **Randomized non-overlapping agent home placement** (deterministic secondary RNG seeded by `seed+9973`) with `H{id}` labels rendered in cells.

Performance: Configurable viewport maintains ~62 FPS across all sizes. Agent wealth tracking adds negligible overhead. All GUI components preserve determinism.
Determinism: Viewport size doesn't affect simulation state. Wealth accumulation preserves all hash parity. GUI interactions remain read-only for simulation state.


## Project Overview

VMT is a **Desktop GUI Application** designed to teach microeconomic theory through spatial agent-based visualizations.

### **Key Features**
- **Spatial Collection Visualization**: Agents collect goods on NxN grid demonstrating preference-driven choice
- **Three Preference Types**: Observable differences between Cobb-Douglas, Perfect Substitutes, and Leontief preferences
- **Educational Progression**: Tutorial system with assessment and learning outcome measurement
- **Desktop Application**: Self-contained PyQt6 + embedded Pygame application for easy educational deployment

### **Educational Mission**
Transform abstract utility maximization into concrete, observable spatial behavior that students can watch, understand, and test. Show that economic theory provides a flexible framework rather than rigid assumptions.

## Implementation Status

### **✅ Gate 1 Achievements (Week 0)**
- **PyQt6 Integration**: Professional desktop window with embedded Pygame surface
- **High Performance**: Sustained 62.5 FPS rendering with moving primitives and color cycling
- **Cross-Platform**: Full headless compatibility for CI/CD environments
- **Quality Systems**: Automated linting, formatting, type checking, and testing pipeline
- **Development Environment**: Complete vmt-dev virtual environment with all dependencies

### **🚀 Current Capabilities (Post Uniform Respawn + Interval Control Increment)**
```bash
# Working demonstration
source vmt-dev/bin/activate
make dev                               # Launch GUI (configurable viewport + agent wealth tracking + full controls panel)
make test                              # 104 tests pass (determinism, decision, respawn diversity, metrics, snapshot, perf, GUI pacing, overlays)
make lint                              # Code quality enforced
python scripts/perf_stub.py --mode widget --duration 2  # Quick FPS validation
```

### **📊 Performance & Determinism (Current Snapshot)**
- **Frame Rate (widget)**: ~61–62 FPS typical (floor safeguard ≥25 CI / ≥30 target)
- **Decision Throughput Test**: 4000 steps <1.0s (floor ≥4000 steps/sec; typical much higher)
- **Overlay Regression Test**: Byte-diff ≥2% when enabled, <15% after disabling (ensures draw path active, inert to state)
- **Respawn & Metrics Overhead**: Negligible; hooks no-op when disabled
- **Determinism Hash**: Stable across alternating respawn introduction (hash parity for identical seeds preserved; see tests + `GATE6_EVAL.md` for prior baseline)
- **Private Access**: General tests avoid internals; controlled replay/density exceptions documented
- **Suite Coverage**: Determinism, competition, hash, respawn density, metrics, snapshot, overlay regression, widget & raw perf

## Documentation Organization

### **📁 Complete Planning Documentation** (`orientation_docs/`)
All strategic and implementation planning systematically completed:

- **📋 Project Overview**: `README.md` - Complete documentation index and navigation
- **📊 Current Status**: `current_assessment.md` - 99% readiness assessment with completion summary
- **🛤️ Implementation Strategy**: `Implementation Roadmap.md` - Phase-based development plan with supporting specifications
- **✅ Validation Approach**: `Progressive Validation Roadmap.md` - Gate-based validation methodology

### **🔧 Detailed Implementation Specifications** (All Complete ✅)
- **📁 Project Structure**: `project_structure_specification.md` - Complete directory hierarchy with module organization
- **🔄 Development Process**: `validation_to_production_transition_plan.md` - Systematic prototype→production evolution
- **🎓 Educational Content**: `educational_scenarios_specification.md` - Concrete tutorial scenarios with assessments  
- **⚙️ Development Workflow**: `development_workflow_guide.md` - Git branching, CI/CD, quality gates
- **🚪 Implementation Gates**: `implementation_phase_gates.md` - Rigorous progression with measurable criteria

### **🔬 Validation Planning** (`orientation_docs/Week0/`)
Gate-based technical validation approach:
- Environment setup and PyQt6 + Pygame integration validation
- Economic theory implementation with spatial collection framework
- Success metrics and educational effectiveness measurement

## Technology Stack

### **✅ Implemented & Validated**
- **PyQt6 6.9.1**: Professional desktop GUI - **WORKING** with 640x480 main window
- **Pygame 2.6.1**: Real-time visualization - **WORKING** at 62.5 FPS with off-screen surface
- **Python 3.11+**: Core implementation - **VALIDATED** with full type checking and linting
- **Development Tools**: pytest, black, ruff, mypy - **INTEGRATED** in automated workflow

### **🔧 Development Infrastructure**  
- **Virtual Environment**: vmt-dev with pinned dependencies
- **CI/CD Pipeline**: GitHub Actions with headless testing (QT_QPA_PLATFORM=offscreen)
- **Quality Gates**: Automated linting, formatting, type checking, unit testing
- **Performance Monitoring**: Widget-based FPS measurement and synthetic benchmarking

### **🔄 Gate 4 Additions (Beyond Gate 3)**
- **Typed Resources**: Grid upgraded from boolean presence to typed (A,B) mapping to goods (good1, good2)
- **Agent State Expansion**: Distinct carrying vs home inventory, modes (FORAGE, RETURN_HOME, IDLE), target tracking
- **Utility-Driven Decision Logic**: ΔU scoring with tie-break (−ΔU, distance, x, y) and greedy 1-step movement
- **Epsilon Bootstrap**: Addresses Cobb-Douglas zero-product stall by lifting zero bundles with ε=1e-6 for initial marginal utility
- **Deterministic Behavior**: Advanced determinism test ensures identical (mode,pos,target,inventory) trajectories across runs
- **Competition Resolution**: Contested resource test validates single-winner & loser retargeting without deadlock
- **Preference Shift Behavior**: After unbalanced collection, agent switches to complementary good to raise utility
- **Rendering Overlays**: Resources colored (A=yellow, B=cyan); agents color-blended by inventory composition
- **Performance Guards**: Decision throughput + micro benchmark preventing latent regression
- **Testing Surface Access**: Added `get_surface_bytes()` for safe render assertions

### **🎯 Upcoming Focus**
-- Weighted / adaptive multi-type respawn strategies (beyond current random assignment)
-- Trade interactions & richer economic behaviors
-- Utility contour & marginal rate visualization overlays
-- Parameterized scenario loading & persistence

### Controls & Metrics Panel (Usage)
Controls panel includes:
* Agent dropdown: deterministic list of agent IDs (sorted)
* Carry label: current in-hand goods (good1, good2)
* Home label: accumulated wealth at home base (good1, good2)
* Utility label: utility of total wealth (carrying + home inventory)
* Turn Rate dropdown: pacing (Unlimited or X tps)
* Respawn Interval dropdown: Off / Every 1 / 5 / 10 / 20 steps (default 20; when respawn occurs)
* Respawn Rate dropdown: 10% / 25% / 50% / 75% / 100% (default 100%; percentage of deficit replenished each time)

### Start Menu Configuration
Preferences section (main area) includes:
* Num Agents: agent count (default 4)
* Pref Mix: preference type (Cobb-Douglas, Perfect Substitutes, Leontief)
* Grid Size: NxN simulation grid dimensions (default 20×20)
* Resource Density: target percentage of cells with resources (default 0.25 = 25%)
* Perception Radius: agent decision-making scan radius (default 8)
* Viewport Size: configurable Pygame surface size (default 800×800, square)
* Metrics Enabled: toggle metrics collection and hash computation

Advanced panel (experimental features only, collapsed by default):
* Bilateral Exchange: enable experimental trading features

Agent metrics update cadence is 4 Hz (lightweight timer). Respawn interval changes are deterministic given identical user interaction order and do not reseed RNG.

## Preferences Architecture (Gate 2 Foundation)

Gate 2 establishes a lightweight but extensible preference system enabling multiple utility formulations without committing yet to full agent/grid complexity.

### Implemented Preference Types
- **Cobb-Douglas**: U(x, y) = x^α * y^(1-α)
- **Perfect Substitutes**: U(x, y) = a·x + b·y
- **Leontief (Perfect Complements)**: U(x, y) = min(x/a, y/b)

All concrete preferences share the abstract `Preference` contract:
- `utility(bundle: tuple[float, float]) -> float`
- `describe_parameters() -> dict[str, float]`
- `update_params(**kwargs)` with validation
- `serialize() / @classmethod deserialize(data)`

### Usage Example
```python
from econsim.preferences import (
	PreferenceFactory,
	CobbDouglasPreference,
	PerfectSubstitutesPreference,
	LeontiefPreference,
)

# Direct instantiation
cd = CobbDouglasPreference(alpha=0.4)
u_cd = cd.utility((4.0, 9.0))

# Factory creation (string driven)
ps = PreferenceFactory.create("perfect_substitutes", a=2.0, b=1.0)
u_ps = ps.utility((3.0, 5.0))  # 2*3 + 1*5 = 11

leo = PreferenceFactory.create("leontief", a=2.0, b=4.0)
u_leo = leo.utility((6.0, 20.0))  # min(6/2, 20/4) = 3

# Safe parameter update
cd.update_params(alpha=0.6)

# Serialization round trip
payload = cd.serialize()
cd_clone = PreferenceFactory.from_serialized(payload)
assert abs(cd_clone.utility((2.0, 5.0)) - cd.utility((2.0, 5.0))) < 1e-12
```

### Design Notes
- Two-good bundle fixed for now (`tuple[float, float]`) for simplicity & performance
- Negative quantities raise `PreferenceError`
- Additional forms can be added by subclassing and registering (≈50 lines including tests)
- Visualization preview hooks intentionally deferred until agents/grid give contextual meaning

### Performance & Testing
- 25 unit tests cover utility correctness, parameter validation, and serialization symmetry
- No measurable FPS regression (still ~62 FPS vs ≥30 requirement)
- See `completed_steps_docs/GATE2_EVAL.md` and `completed_steps_docs/Gate_2_acceptance_note.md` for evidence mapping

### Future Extension (Later Gates)
- Generalize to N-good bundles
- Introduce stochastic or adaptive preference variants for advanced educational scenarios
- Integrate with agent decision loop + spatial resource acquisition

---

## Quick Start

### **Prerequisites**
- Python 3.11+ with virtual environment support
- Git for version control and workflow management
- Make for build automation (Linux/macOS)

### **Development Setup**
```bash
# Clone repository and enter project directory
git clone https://github.com/cmfunderburk/vmt.git
cd vmt

# Create virtual environment and install dependencies
python3 -m venv vmt-dev
source vmt-dev/bin/activate
pip install -e .[dev]

# Run the application (62.5 FPS GUI)
make dev

# Run tests and quality checks
make test                    # Unit tests
make lint                    # Code quality
make format                  # Code formatting
```

### **Deterministic Preference Demo (New)**
Run a lightweight, headless-friendly demonstration comparing agent trajectories under different preference types. Produces per-step positions, inventories, and a determinism hash (stable for identical seeds).

```bash
source vmt-dev/bin/activate
python scripts/demo_single_agent.py --pref all --steps 20 --agents 1 --seed 1234 --replay
```

Sample (truncated) output:
```
=== Preference: CobbDouglas ===
step,id,x,y,carry_g1,carry_g2,home_g1,home_g2
0,0,0,0,0,0,0,0
1,0,2,0,1,0,0,0
...
Final hash: 0d9f4c5b... (example)
Replay hash: 0d9f4c5b... (MATCH)

=== Preference: PerfectSubstitutes ===
step,id,x,y,carry_g1,carry_g2,home_g1,home_g2
...
Final hash: 6ab1c2e3...

=== Preference: Leontief ===
...
```

Flags:
- `--pref {cd, subs, leontief, all}` choose preference(s)
- `--steps N` number of decision steps (default 25)
- `--agents N` number of agents (default 1; small recommended for clarity)
- `--seed SEED` deterministic base seed
- `--replay` run snapshot+restore parity check (hash must MATCH)

Use this script in teaching contexts to highlight differing resource acquisition paths driven purely by utility structure.

### **Interactive Visual Demo & Paused Launch**
The GUI now offers a unified baseline visualization with an optional **Start Paused** checkbox (Start Menu). This replaces the old separate "Turn Mode" scenario:

* Start Paused ON → simulation loads in a paused state; you can single-step or resume.
* Start Paused OFF → simulation begins advancing every frame (Unlimited) unless you throttle via the Turn Rate dropdown.

Visual affordances (overlay text, grid, IDs, target arrows, home labels) are controlled by the Overlays panel; all are enabled by default and can be toggled live without affecting determinism.

#### Quick Start (Paused Launch)
```bash
make dev  # launch GUI; check 'Start Paused' in the Start Menu, then press Launch
```

#### Controls (Unified)
- Pause / Resume button
- Step 1 / Step 5 buttons (work while paused)
- Turn Rate dropdown: Unlimited (per-frame) or throttled rates (e.g., 1.0 tps)
- Overlays panel: toggle Grid, Agent IDs, Target Arrows, Home Labels
- Respawn interval dropdown (baseline mode only)

#### Determinism Notes
- Paused start only affects when the first step occurs; state sequence (hash) is identical if you resume at the same wall-clock tick count.
- Overlays are purely render-time; no mutation of simulation state.

#### Flag Reference (script `demo_single_agent.py`)
Legacy CLI flags referencing `--turn-mode` remain accepted for backward compatibility but are internally mapped to the unified GUI path. Deprecated flags tied solely to old turn mode (tails, fade, queued autoplay) are subject to removal in a future cleanup pass.

| Flag | Type / Values | Default | Description |
|------|---------------|---------|-------------|
| `--steps` | int ≥1 | 25 | Total decision steps to execute (headless) or target before auto-exit. |
| `--agents` | int ≥1 | 1 | Number of agents instantiated. |
| `--pref` | {cd, subs, leontief, all} | all | Preference type(s) to run (headless cycles when all). |
| `--seed` | int | 1234 | Base seed controlling resource placement & positions. |
| `--replay` | flag | off | Run snapshot replay parity hash check after forward run. |
| `--gui` | flag | off | Launch GUI instead of headless log. |
| `--density` | float (0<d≤1) | None | Probabilistic resource placement (deterministic w/ seed). |
| `--respawn-every` | int ≥0 | 0 | Respawn attempt every N steps (0 disables). |
| `--grid-lines` | flag | off | Force grid lines in legacy script view (GUI overlays panel supersedes). |
| `--pause-start` | flag | off | Start paused (mirrors Start Menu checkbox). |

Deprecated (legacy compatibility; may be removed): `--turn-mode`, `--fade-ms`, `--tail-length/--tail`, `--no-tails`, `--no-overlay`, `--auto-interval`.

#### Performance
- Baseline rendering aims for ~60 FPS; Unlimited stepping executes one decision step per frame.
- Throttled rates (e.g., 1.0 tps) use a controller timestamp gate; no secondary timers or sleeps.

#### Planned Enhancements
- Optional inequality / market overlays (pending market mode implementation)
- Replay timeline scrubber
- Export current frame as PNG / animated snippet helper

### **Performance Testing**
```bash
# Activate environment
source vmt-dev/bin/activate

# Test widget performance (real rendering)
python3 scripts/perf_stub.py --mode widget --duration 5

# Test synthetic performance (baseline)  
python3 scripts/perf_stub.py --mode synthetic --duration 2
```

### **Development Workflow**
```bash
# Daily development commands
make dev       # Launch application
make test      # Run all tests  
make lint      # Check code quality
make format    # Auto-format code
make clean     # Clean cache files
```

## Development Approach

### **Gate-Based Implementation Success**
**Week 0 Validation**: Technical validation completed successfully with PyQt6 + Pygame integration exceeding all performance requirements.

**Professional Standards**: Implemented automated quality gates (linting, formatting, type checking, testing) ensuring maintainable codebase.

**Educational Focus**: All technical decisions validated against pedagogical objectives for maximum learning impact.

### **Technical Achievements**
- **✅ GUI Framework Validated**: PyQt6 desktop application with professional window management
- **✅ Rendering Engine Working**: Pygame embedded surface with 62.5 FPS sustained performance  
- **✅ Development Environment**: Complete toolchain with automated quality enforcement
- **✅ CI/CD Pipeline**: Headless testing and validation in GitHub Actions
- **✅ Performance Instrumentation**: Real-time FPS monitoring and benchmarking capabilities

## Educational Impact

### **Pedagogical Innovation**
- **Observable Economic Theory**: Transform abstract mathematics into concrete spatial behavior
- **Visual-First Learning**: Students see preference differences through agent movement patterns
- **Interactive Discovery**: Exploration and experimentation with immediate feedback
- **Assessment Integration**: Measurable learning outcomes with pattern recognition

### **Research Applications**  
- **Agent-Based Economic Modeling**: Spatial constraints on traditional economic optimization
- **Educational Effectiveness**: Measurement and validation of visual learning approaches
- **Cross-Platform Educational Software**: Desktop application deployment in educational environments

## Project Status: Validated Technical Foundation

### **Risk Mitigation: Proven Success**
All major technical risks eliminated through working implementation:

- **✅ Technical Feasibility**: PyQt6 + Pygame integration proven working at 62.5 FPS
- **✅ Performance Requirements**: Exceeds minimum 30 FPS by 208% with room for complexity
- **✅ Cross-Platform Compatibility**: Headless execution validated for CI/CD environments
- **✅ Development Quality**: Professional toolchain with automated enforcement working
- **✅ Educational Viability**: Technical foundation supports all planned pedagogical features

### **Success Factors: Implemented**
- **🎯 Working Application**: Desktop GUI with real-time visualization capabilities demonstrated
- **📏 Scalable Architecture**: Modular design ready for spatial grid and agent implementation
- **🔬 Measured Performance**: Quantified FPS metrics with automated regression detection
- **⭐ Professional Standards**: Code quality, testing, and CI/CD exceeding industry practices
- **🎓 Educational Ready**: Technical platform validated for microeconomics learning objectives

## Current Status
**Completed Gates**: 1–6 (Integration, Preferences, Spatial Core, Decision Logic, Dynamics/Respawn/Metrics, Integration & Overlay)  
**Active Planning**: Gate 7 (interaction + GUI enrichment)  
**Repository**: [github.com/cmfunderburk/vmt](https://github.com/cmfunderburk/vmt)  
**Last Updated**: 2025-09-23

## 11. Experimental GUI (Feature-Flagged Phase A)

The next-generation GUI shell is available behind an environment flag while legacy behavior remains the default for stability.

### Activate
```bash
ECONSIM_NEW_GUI=1 make dev
```

### Components (Phase A)
- Start Menu (scenario + parameters + Randomize Seed + Advanced configuration panel)
- Simulation Page:
  - Embedded Pygame viewport (configurable 320×320 to 800×800)
  - Controls Panel (Pause/Resume, Step 1, Step 5, Hash Refresh, Turn Rate)
  - Metrics Panel (ticks, remaining resources, steps/sec, hash via refresh) + optional auto-refresh
  - Agent Inspector Panel (individual agent state: Carry, Home, Utility)
  - Overlays Panel (Grid, Agent IDs, Target Arrows, Home Labels)
  - Back to Menu (safe teardown & new session launch)

### Overlay Toggles
Tied to a shared `OverlayState` dataclass; rendering path is read-only and deterministic.

### Metrics Auto-Refresh (Optional)
Environment flags:
- `ECONSIM_METRICS_AUTO=1` enables periodic refresh
- `ECONSIM_METRICS_AUTO_INTERVAL_MS=500` custom interval (clamped to minimum 250ms to keep ≤4 Hz)

### Other Environment Flags
- `ECONSIM_LEGACY_RANDOM=1` – forces legacy random walk (disables decision logic per step)
- `ECONSIM_LEGACY_ANIM_BG=1` – restores legacy animated background (static neutral background is the default for focus)

### Determinism & Performance Safeguards
- Pause aware stepping (controller gate) – no hidden loops introduced
- Hash caching avoids redundant recomputation between manual refreshes
- Steps/sec estimator uses a rolling 64 timestamp window (O(1) append)
- Overlay off baseline stability validated; overlay on path pixel-diff tested

### Playback Speed (Educational Pacing)
By default the experimental GUI throttles automatic stepping to 1 turn per second to emphasize discrete decision outcomes for teaching. A speed dropdown in the Controls Panel allows selecting: 0.5, 1, 1.5, 2, 3, 4, or 5 turns/sec. Changing the value updates a deterministic scheduler that:

* Emits at most one step per tick
* Advances an internal time anchor by whole intervals to avoid cumulative drift
* Resets after manual stepping to preserve precise pacing

Set to 0.5 tps for slower narration (one step every 2 seconds) or up to 5 tps for quicker walkthroughs. (Planned optional "Unlimited" mode would revert to per-frame stepping.)

### Visual Pause Indicator
When paused a centered translucent "PAUSED" watermark overlays the viewport, providing immediate state clarity without affecting underlying simulation state or determinism.

### Example: Launch New GUI + Auto Metrics
```bash
ECONSIM_NEW_GUI=1 ECONSIM_METRICS_AUTO=1 ECONSIM_METRICS_AUTO_INTERVAL_MS=750 make dev
```
