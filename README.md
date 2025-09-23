# VMT EconSim Platform

An educational microeconomic simulation prototype combining a PyQt6 desktop shell with a deterministic spatial agent model (preferences, resource collection, decision logic).

> This README reflects the **current state after Gate 6 integration (factory, decision default, overlay toggle, perf safeguards)**. The previous aspirational narrative lives in `README_aspirational.md`.

## 1. Snapshot: Implemented vs Pending

| Area | Implemented (Usable) | Pending / Not Yet Integrated |
|------|----------------------|-------------------------------|
| Rendering Core | PyQt6 window + embedded 320x240 Pygame surface (~62 FPS) | GUI controls / menus / scenario panels |
| Preferences | Cobb-Douglas, Perfect Substitutes, Leontief + factory | N-good generalization, adaptive forms |
| Grid & Resources | Typed resources (A,B) with deterministic iteration | Quantities >1 per cell, spatial clustering |
| Agents | Carrying vs home inventories, modes, greedy decision, tie-break determinism | Trading, production/consumption, richer behaviors |
| Decision Mode | Greedy ΔU selection (epsilon bootstrap) + tests; GUI default ON; env / param override | Multi-step planning |
| Respawn | Density-based scheduler (factory flag) | Multi-type spawning, richer policies |
| Metrics | Factory-attached collector + determinism hash | Additional economic metrics suite |
| Snapshot / Replay | Serialize + restore + hash parity tests | Scenario library management |
| Configuration | `SimConfig` + `Simulation.from_config` factory | Extended scenario descriptors |
| Overlays / HUD | Toggleable overlay + grid lines (key 'O'); regression + perf neutrality tests | Utility contours, advanced UI panels |
| Tests | Determinism, decision precedence, respawn, metrics, snapshot, perf (FPS + throughput), overlay regression | Extended educational UI interaction tests |

## 2. Current Reality (Post Gate 6)
Gate 6 delivered: factory construction, GUI default decision mode (env override `ECONSIM_LEGACY_RANDOM=1` or widget param), overlay toggle, conditional respawn/metrics wiring, overlay regression test, decision step throughput safeguard.

## 3. Quick Start (Current Behavior)
```bash
python3 -m venv vmt-dev
source vmt-dev/bin/activate
pip install -e .[dev]

# Launch demo GUI (decision mode ON by default; press 'O' to toggle overlay)
make dev

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
from econsim.simulation.world import Simulation
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
2. No menus / control panels / scenario loader.
3. Advanced overlays (utility contours, analytics) not implemented.

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
Last updated: 2025-09-23 (Documentation remediation – foundation for Gate 6).

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

### **🚀 Current Capabilities (Post Gate 6)**
```bash
# Working demonstration (Gate 5)
source vmt-dev/bin/activate
make dev                               # Launch GUI with overlay-capable widget
make test                              # 62 tests pass (preferences + grid + agents + decision + respawn + metrics + snapshot + perf)
make lint                              # Code quality enforced
python3 scripts/perf_stub.py --mode widget --duration 2  # Quick FPS validation
```

### **📊 Performance & Determinism (Gate 6 Snapshot)**
- **Frame Rate (widget)**: ~61–62 FPS typical (floor safeguard ≥25 CI / ≥30 target)
- **Decision Throughput Test**: 4000 steps <1.0s (floor ≥4000 steps/sec; typical much higher)
- **Overlay Regression Test**: Byte-diff ≥2% when enabled, <15% after disabling (ensures draw path active, inert to state)
- **Respawn & Metrics Overhead**: Negligible; hooks no-op when disabled
- **Determinism Hash**: Unchanged across Gate 6 integration (see `completed_steps_docs/GATE6_EVAL.md`)
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

### **🎯 Post Gate 5 Next Focus**
- Gate 5 retrospective narrative polish (risks/mitigations – partially in GATE5_EVAL)
- Plan Gate 6 scope (e.g., trade interactions, richer utility adaptation, UI scenario configuration)
- Expand educational overlays (utility contours, marginal rate visualization)

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

### **Turn Mode & Interactive Visual Demo (Unified)**
Turn Mode provides a pedagogical, discrete visualization of agent decision steps with optional automatic pacing. It layers educational affordances (HUD, tails, fading resources) onto the deterministic simulation without altering core state transitions or hashes.

#### Quick Start (Autoplay at 1 turn/sec)
```bash
python scripts/demo_single_agent.py --gui --turn-mode --steps 25 --seed 1234 --density 0.20 --fade-ms 500
```

#### Visual Preview (5 Turns)
![Turn Mode 5-Turn Demo](https://i.imgur.com/CwKVgxd.gif)

_Animated excerpt: static background, 1 Hz autoplay, resource fade-outs, tails, HUD overlay._

Generation steps documented in `docs/assets/GENERATE_GIF.md` (regenerate if visuals change).

What You See:
1. Static background (animation suppressed for focus)
2. Grid lines (auto-on unless suppressed in future flags)
3. Resources (A=yellow, B=cyan)
4. Agents (color blend by inventory composition)
5. HUD (Turn, Remaining resources, per-agent position, carrying, home inventory, utility)
6. Breadcrumb tails + most recent move highlight
7. Fading markers where resources were just collected

#### Controls
- Play/Pause button: toggles 1 Hz step enqueue
- SPACE: enqueue 1 step immediately
- ENTER: enqueue 5 steps
- A: toggle legacy faster auto-run (interval from `--auto-interval` ms)
- Q: quit

#### Determinism
- Autoplay adds steps only when no pending steps remain → stable ordering.
- Visual layers (tails/fade/HUD) do not mutate simulation objects.
- Resource placement with `--density` is seeded by `--seed` ensuring reproducible initial layouts.

#### Flag Reference
| Flag | Type / Values | Default | Applies | Description |
|------|---------------|---------|---------|-------------|
| `--steps` | int ≥1 | 25 | All modes | Total decision steps to execute (GUI exits after reaching or on quit). |
| `--agents` | int ≥1 | 1 | All | Number of agents instantiated (higher counts increase decision workload). |
| `--pref` | {cd, subs, leontief, all} | all | All | Preference type(s) to run (non-GUI prints table for each). |
| `--seed` | int | 1234 | All | Base seed controlling resource placement (density), agent start, RNG-driven tie contexts. |
| `--replay` | flag | off | Headless/GUI | After forward run, performs snapshot replay parity hash check. |
| `--gui` | flag | off | N/A | Launch GUI instead of CSV-like stdout log. |
| `--turn-mode` | flag | off | GUI | Enables discrete stepping UI & educational overlays. |
| `--auto-interval` | int ms ≥50* | 500 | Turn mode | Interval for legacy auto-run (A key). *Values <50 may waste CPU. |
| `--density` | float (0<d≤1) | None | All | Probabilistic resource placement at density d (None => patterned baseline). Deterministic with seed. |
| `--respawn-every` | int ≥0 | 0 | All | Respawn attempt every N turns (0 disables). Deterministic gating via step counter. |
| `--grid-lines` | flag | off* | GUI | Draw grid boundaries (*auto-on implicitly in turn mode even if flag omitted). |
| `--fade-ms` | int ≥0 | 600 | Turn mode | Milliseconds resources linger with alpha fade (0 disables fade). |
| `--tail-length`/`--tail` | int ≥0 | 8 | Turn mode | Per-agent tail length (0 disables tails). Ignored if `--no-tails`. |
| `--no-tails` | flag | off | Turn mode | Force-disable tails regardless of tail-length. |
| `--no-overlay` | flag | off | Turn mode | Hide HUD text overlay. |
| `--pause-start` | flag | off | Turn mode | Start with zero pending steps (autoplay play button still available). |

#### Common Scenarios
```bash
# Minimal autoplay (no tails, instantaneous resource removal)
python scripts/demo_single_agent.py --gui --turn-mode --steps 30 --seed 1 --no-tails --fade-ms 0

# Paused start (press Play when ready)
python scripts/demo_single_agent.py --gui --turn-mode --steps 40 --seed 42 --pause-start --tail-length 4

# Density + respawn dynamics exploration
python scripts/demo_single_agent.py --gui --turn-mode --steps 80 --seed 77 --density 0.25 --respawn-every 6 --fade-ms 700
```

#### Performance Notes
- Base render loop still ~60–62 FPS; 1 Hz autoplay is negligible overhead.
- Fading uses bounded list rebuild; tails store at most tail-length * agents entries.
- Disable overlays (`--no-overlay`) or tails (`--no-tails`) for profiling micro-changes.

#### Planned (Not Yet Implemented)
- Speed selector (0.25× / 1× / 2× / 5×)
- Pause overlay dimmer & step badge
- Interactive resource placement / scenario editor
- Per-turn utility delta and marginal rate annotations

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
- Start Menu (scenario + parameters + Randomize Seed)
- Simulation Page:
  - Embedded 320x240 Pygame viewport
  - Controls Panel (Pause/Resume, Step 1, Step 5, Hash Refresh)
  - Metrics Panel (ticks, remaining resources, steps/sec, hash via refresh) + optional auto-refresh
  - Overlays Panel (Grid, Agent IDs, Target Arrows)
  - Back to Menu (safe teardown & new session launch)

### Overlay Toggles
Tied to a shared `OverlayState` dataclass; rendering path is read-only and deterministic.

### Metrics Auto-Refresh (Optional)
Environment flags:
- `ECONSIM_METRICS_AUTO=1` enables periodic refresh
- `ECONSIM_METRICS_AUTO_INTERVAL_MS=500` custom interval (clamped to minimum 250ms to keep ≤4 Hz)

### Other Environment Flags
- `ECONSIM_LEGACY_RANDOM=1` – forces legacy random walk (disables decision logic per step)

### Determinism & Performance Safeguards
- Pause aware stepping (controller gate) – no hidden loops introduced
- Hash caching avoids redundant recomputation between manual refreshes
- Steps/sec estimator uses a rolling 64 timestamp window (O(1) append)
- Overlay off baseline stability validated; overlay on path pixel-diff tested

### Example: Launch New GUI + Auto Metrics
```bash
ECONSIM_NEW_GUI=1 ECONSIM_METRICS_AUTO=1 ECONSIM_METRICS_AUTO_INTERVAL_MS=750 make dev
```
