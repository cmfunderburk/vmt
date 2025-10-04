# GUI→Simulation Coupling Map

**Date:** 2025-10-03  
**Purpose:** Document all GUI dependencies on simulation components

## Direct Dependencies

### SimulationController → Simulation
- **File:** `src/econsim/gui/simulation_controller.py`
- **Dependency:** `Simulation` class (line 15: `from econsim.simulation.world import Simulation`)
- **Usage:** Constructor takes `Simulation` instance (line 20: `def __init__(self, simulation: Simulation)`)
- **Impact:** HIGH - Core GUI controller depends on simulation
- **Details:** 
  - Stores reference to simulation (line 21: `self.simulation = simulation`)
  - Accesses simulation config for seed (lines 32-34)
  - Accesses simulation respawn interval (line 44)
  - Provides methods to control simulation execution

### EmbeddedPygameWidget → Simulation
- **File:** `src/econsim/gui/embedded_pygame.py`
- **Dependency:** `_SimulationProto` (protocol interface, lines 29-30)
- **Usage:** Renders simulation state, calls `simulation.step(rng)`
- **Impact:** HIGH - Main rendering widget drives simulation
- **Details:**
  - Takes simulation parameter in constructor (line 43: `simulation: _SimulationProto | None = None`)
  - Stores simulation reference (line 51: `self._simulation: _SimulationProto | None = simulation`)
  - Calls simulation.step() in _on_tick() method (confirmed by protocol definition)
  - Manages RNG for simulation stepping

### SessionFactory → Simulation
- **File:** `src/econsim/gui/session_factory.py`
- **Dependency:** `Simulation.from_config()` factory method (line 16: `from econsim.simulation.world import Simulation`)
- **Usage:** Creates simulation instances for GUI sessions
- **Impact:** MEDIUM - Factory pattern, can be abstracted
- **Details:**
  - Returns SimulationController (line 38: `def build(descriptor) -> "SimulationController"`)
  - Creates Simulation via Simulation.from_config() (line 114: `sim = Simulation.from_config(cfg, pref_factory)`)
  - Creates SimulationController wrapping the simulation (line 116: `controller = SimulationController(sim)`)

## Indirect Dependencies

### All GUI Panels → SimulationController
- **Files:** All files in `src/econsim/gui/panels/`
- **Dependency:** `SimulationController` (which wraps `Simulation`)
- **Usage:** Access simulation state through controller
- **Impact:** MEDIUM - Panels depend on controller, not simulation directly

#### Specific Panel Dependencies:
- **controls_panel.py:** Imports SimulationController (line 20), takes controller in constructor (line 24)
- **metrics_panel.py:** Imports SimulationController (line 11), takes controller in constructor (line 15)
- **agent_inspector_panel.py:** Imports SimulationController (line 11), takes controller in constructor (line 16)
- **trade_inspector_panel.py:** Imports SimulationController (line 14), takes controller in constructor (line 21)
- **event_log_panel.py:** Imports SimulationController (line 16), takes controller in constructor (line 22)
- **status_footer_bar.py:** Imports SimulationController (line 10), takes controller in constructor (line 15)
- **overlays_panel.py:** No direct controller dependency (mutates shared OverlayState)

### MainWindow → SessionFactory → Simulation
- **File:** `src/econsim/gui/main_window.py`
- **Dependency:** Chain: MainWindow → SessionFactory → Simulation
- **Usage:** Creates simulation sessions through factory
- **Impact:** MEDIUM - Goes through factory layer
- **Details:**
  - Imports SessionFactory (line 27: `from .session_factory import SessionFactory`)
  - Imports SimulationController (line 28: `from .simulation_controller import SimulationController`)
  - Imports EmbeddedPygameWidget (line 33: `from .embedded_pygame import EmbeddedPygameWidget`)
  - Creates controller via SessionFactory.build() (line 125: `controller = SessionFactory.build(descriptor)`)
  - Passes simulation to EmbeddedPygameWidget (line 143: `simulation=controller.simulation`)

## Data Flow Analysis

### Simulation State Access
1. **GUI reads simulation state** through `SimulationController`
2. **GUI controls simulation execution** through `SimulationController`
3. **GUI renders simulation state** through `EmbeddedPygameWidget`

### Control Flow
1. **GUI starts/stops simulation** via controller
2. **GUI pauses/resumes simulation** via controller  
3. **GUI adjusts simulation speed** via controller
4. **GUI toggles simulation features** via controller

## Coupling Severity

### HIGH SEVERITY (Must Remove)
- `SimulationController` direct `Simulation` dependency
- `EmbeddedPygameWidget` direct `simulation.step()` calls
- GUI panels accessing simulation state through controller

### MEDIUM SEVERITY (Can Abstract)
- `SessionFactory` simulation creation
- MainWindow simulation session management

### LOW SEVERITY (Already Abstracted)
- Event handling and UI controls
- Configuration and preferences

---

## Simulation→GUI Dependencies

### Direct Dependencies
**RESULT: NONE FOUND** ✅

After comprehensive analysis:
- **Simulation module:** No GUI imports found
- **Preferences module:** No GUI imports found  
- **Observability module:** No GUI imports found
- **No PyQt/pygame imports** in simulation code
- **No SimulationController/EmbeddedPygameWidget imports** in simulation code

### Analysis
- **Expected:** Simulation should have ZERO GUI dependencies ✅
- **Actual:** Simulation is completely independent of GUI ✅
- **Action Required:** None - simulation is already decoupled ✅

### Conclusion
The simulation core is already clean and independent. Only GUI depends on simulation, not vice versa. This makes the decoupling task simpler - we only need to remove GUI dependencies on simulation, not clean up simulation dependencies on GUI.
