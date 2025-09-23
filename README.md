# VMT EconSim Platform

**An Educational Economic Simulation Platform for Microeconomics Learning**

## Project Status: GATE 5 COMPLETE — DYNAMICS, METRICS & DETERMINISM ✅

**Gate 1 Technical Validation**: ✅ COMPLETE – PyQt6 + Pygame integration working at ~62 FPS (headless-capable)
**Gate 2 Preference Architecture**: ✅ COMPLETE – Cobb-Douglas, Perfect Substitutes, Leontief fully implemented with validation & serialization
**Gate 3 Spatial / Agent Foundations**: ✅ COMPLETE – Grid, Agent core, Simulation coordinator, deterministic harness
**Gate 4 Decision & Visualization**: ✅ COMPLETE – Utility-driven target selection, typed resources, epsilon bootstrap, competition & preference-shift behavior, rendering overlays, performance guards
**Gate 5 Dynamics & Metrics Spine**: ✅ COMPLETE – Respawn scheduler (target density), MetricsCollector (per-step aggregates + determinism hash), snapshot & replay, performance overhead guard (<0.30ms/tick), reproducible hash replay

**Current Phase**: Preparing for next gate (post-Gate 5 refinement / upcoming feature planning)

**Confidence Level**: Maximum - Working implementation validates all technical assumptions and educational approach.

## Project Overview

VMT is a **Desktop GUI Application** designed to teach microeconomic theory through spatial agent-based visualizations. The platform addresses the common student criticism of "people don't behave like that" by demonstrating multiple preference types (Cobb-Douglas, Perfect Substitutes, Leontief) through observable spatial agent behavior.

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

### **🚀 Current Capabilities (Post Gate 5)**
```bash
# Working demonstration (Gate 5)
source vmt-dev/bin/activate
make dev                               # Launch GUI with overlay-capable widget
make test                              # 62 tests pass (preferences + grid + agents + decision + respawn + metrics + snapshot + perf)
make lint                              # Code quality enforced
python3 scripts/perf_stub.py --mode widget --duration 2  # Quick FPS validation
```

### **📊 Performance Metrics (Gate 5 Snapshot)**
- **Frame Rate (widget)**: ~62 FPS baseline retained after overlays & decision logic
- **Decision Throughput**: >6000 decision ticks/sec (20 agents / 120 resources scenario; guard ≥2000)
- **Target Selection Micro-Overhead**: <3,000 µs guard, currently well below threshold
- **Respawn + Metrics Overhead**: ~200µs per tick (absolute guard 300µs; relative noisy due to micro baseline) via `test_perf_overhead.py`
- **Density Convergence**: Respawn reaches target density within ±5% (no overshoot)
- **Determinism Hash**: Stable across identical seeds; diverges on state perturbation; snapshot replay reproduces stepwise hash
- **Tests**: 62 unit tests (adds respawn density, metrics integrity, determinism hash, snapshot replay, perf overhead)
- **Code Quality**: Zero linting errors, formatted codebase
- **CI Pipeline**: Fully functional with headless execution

#### Gate 1 Performance Validation Details
Authoritative 5s run (2025-09-22):
```json
{"frames": 310.0, "duration_s": 5.000980996999715, "avg_fps": 61.98783802337605}
```
Interpretation:
- Sustained ~62 FPS (stretch goal met; ≥30 requirement exceeded with large margin)
- Headless path stable (CI uses SDL_VIDEODRIVER=dummy + QT_QPA_PLATFORM=offscreen)
- Current automated perf test uses a conservative ≥25 FPS threshold to avoid flakiness; may be tightened after observing CI stability.

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
- `--pref {cd,subs,leontief,all}` choose preference(s)
- `--steps N` number of decision steps (default 25)
- `--agents N` number of agents (default 1; small recommended for clarity)
- `--seed SEED` deterministic base seed
- `--replay` run snapshot+restore parity check (hash must MATCH)

Use this script in teaching contexts to highlight differing resource acquisition paths driven purely by utility structure.

### **Turn Mode Visualization (Bundle 3 Additions)**
Enhanced pedagogical visualization is available via GUI turn mode with discrete step control and richer overlays.

Launch example:
```bash
python scripts/demo_single_agent.py --gui --turn-mode --steps 40 --agents 1 --seed 1234 \
	--density 0.18 --grid-lines --tail-length 6 --fade-ms 600 --respawn-every 5
```

Interactive controls (turn mode):
- SPACE: advance 1 step
- ENTER: advance 5 steps
- A: toggle auto-run (interval controlled by --auto-interval)
- Q: quit

Key flags:
- `--turn-mode` enable discrete stepping (otherwise continuous)
- `--density FLOAT` deterministic random initial resource layout (overrides checkerboard)
- `--grid-lines` show grid cell boundaries (auto-enabled in turn mode if omitted)
- `--tail-length N` breadcrumb tail length per agent (0 disables)
- `--no-tails` force-disable tails
- `--fade-ms MS` fade-out duration for recently collected resources (0 disables)
- `--respawn-every N` gated respawn every N turns (0 disables); uses target density = density or default 0.18
- `--no-overlay` hide HUD (turn count, resources, inventories, utility)
- `--pause-start` (planned) start with zero pending steps (manual first step)

HUD Contents:
- Turn number (decision steps executed)
- Remaining resources
- Per-agent: position, carrying inventory, home inventory, combined utility

Determinism Notes:
- Visual effects (fade, tails, overlay) do not influence the determinism hash
- Initial resource scatter deterministic given `--density` and `--seed`

Performance Impact:
- Gridlines, overlay text, and tails add negligible overhead for small grids
- Fading resources use a short list pruned each turn; safe under existing perf guards

Future Enhancements (not yet implemented): path previews, utility change deltas, interactive placement.

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

## Next Steps: Gate 4 Completion → Gate 5 Preview

Immediate (Gate 4 wrap-up):
1. Draft `GATE4_EVAL.md` mapping acceptance criteria to implemented evidence
2. Finalize checklist & retrospective evaluation
3. Expand README educational example (optional) with decision trace excerpt

Upcoming (Gate 5 preview – NOT yet implemented):
1. Resource regeneration / respawn mechanics
2. Agent interaction (trading or sharing) primitives
3. Enhanced visualization (paths, utility heat overlays)
4. Configurable simulation pacing (decoupled tick rate)
5. Extended preference diagnostics (marginal utility logging)

---

**Project Status**: Gate 4 In Progress — Decision Logic & Visualization  
**Technical Validation**: ✅ Gate 1 (Integration) | ✅ Gate 2 (Preferences) | ✅ Gate 3 (Spatial Core)  
**Last Updated**: September 22, 2025  
**Repository**: [github.com/cmfunderburk/vmt](https://github.com/cmfunderburk/vmt)