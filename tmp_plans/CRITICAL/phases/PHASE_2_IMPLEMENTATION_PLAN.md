# Phase 2: Output Architecture - REBUILD GUI

## Overview

Phase 2 rebuilds the GUI as a playback consumer rather than a simulation driver. With Phase 1 complete (GUI-Simulation decoupling achieved), we now build a robust output/playback system that allows:

- **Headless simulation execution** with complete state recording
- **GUI as playback consumer** - loads and displays saved simulation runs
- **VCR-style controls** - play, pause, seek, speed adjustment
- **Performance optimization** - efficient recording and playback

## Success Criteria

✅ **Working Playback System**: Can run simulation headless, save output, load in GUI, playback with full control
✅ **Performance Benchmarks**: Recording and playback meet performance targets
✅ **GUI Functional Again**: GUI works as playback consumer (not simulation driver)
✅ **VCR Controls**: Play, pause, seek, speed controls functional

---

## Phase 2A: Prototype & Benchmark (Days 1-3)

### Step 2A.1: Performance Prototype

**Goal**: Validate performance before building full system

**Tasks**:
1. **Create minimal recording prototype**
   ```bash
   # Create prototype files
   mkdir -p src/econsim/output/prototype
   touch src/econsim/output/prototype/recorder_prototype.py
   touch src/econsim/output/prototype/playback_prototype.py
   ```

2. **Benchmark current FileObserver performance**
   ```bash
   # Run performance tests
   python scripts/performance_test.py --headless --steps 1000 --agents 50
   python scripts/performance_test.py --headless --steps 10000 --agents 100
   ```

3. **Measure memory usage patterns**
   ```bash
   # Test memory usage
   python scripts/perf_baseline_scenario.py --memory-profile
   ```

**Deliverables**:
- [ ] Performance baseline measurements
- [ ] Memory usage analysis
- [ ] Prototype recording/playback code
- [ ] Performance targets defined

### Step 2A.2: Output Format Design

**Goal**: Design efficient output schema without versioning complexity

**Tasks**:
1. **Analyze existing FileObserver events**
   - Review `FILEOBSERVER_AUDIT.md` findings
   - Identify essential vs. optional data
   - Design compact binary format

2. **Design output schema**
   ```python
   # Schema design in prototype
   class SimulationOutputSchema:
       header: SimulationMetadata
       events: List[SimulationEvent]
       snapshots: List[StateSnapshot]  # Periodic full state
   ```

3. **Validate schema efficiency**
   - Test serialization performance
   - Measure storage requirements
   - Compare with JSON/text formats

**Deliverables**:
- [ ] Output schema specification
- [ ] Serialization performance benchmarks
- [ ] Storage size estimates
- [ ] Schema validation tests

### Step 2A.3: Git Checkpoint

```bash
git tag phase2a-prototype-complete -m "Phase 2A: Prototype & benchmark complete"
```

---

## Phase 2B: SimulationRecorder Implementation (Days 4-10)

### Step 2B.1: Core Recorder Architecture

**Goal**: Build robust simulation state recording system

**Tasks**:
1. **Create SimulationRecorder class**
   ```bash
   # Create recorder module
   mkdir -p src/econsim/output
   touch src/econsim/output/recorder.py
   touch src/econsim/output/schema.py
   touch src/econsim/output/events.py
   ```

2. **Implement event recording**
   ```python
   class SimulationRecorder:
       def __init__(self, output_path: str, snapshot_interval: int = 100):
           self.output_path = output_path
           self.snapshot_interval = snapshot_interval
           self.events: List[SimulationEvent] = []
           self.snapshots: List[StateSnapshot] = []
       
       def record_step_start(self, step: int, simulation: Simulation):
           # Record step start event
       
       def record_step_end(self, step: int, simulation: Simulation):
           # Record step end event
           # Take snapshot if needed
       
       def record_trade(self, trade_event: TradeEvent):
           # Record trade execution
       
       def record_agent_action(self, action_event: AgentActionEvent):
           # Record agent actions
   ```

3. **Integrate with existing FileObserver system**
   - Extend current observers to write to recorder
   - Maintain backward compatibility
   - Ensure zero performance impact when not recording

**Deliverables**:
- [ ] SimulationRecorder class implementation
- [ ] Event recording system
- [ ] Integration with FileObserver
- [ ] Unit tests for recorder

### Step 2B.2: Output Serialization

**Goal**: Efficient serialization and storage of simulation data

**Tasks**:
1. **Implement binary serialization**
   ```python
   class OutputSerializer:
       def serialize_header(self, metadata: SimulationMetadata) -> bytes:
           # Binary header serialization
       
       def serialize_event(self, event: SimulationEvent) -> bytes:
           # Binary event serialization
       
       def serialize_snapshot(self, snapshot: StateSnapshot) -> bytes:
           # Binary snapshot serialization
   ```

2. **Create output file format**
   ```python
   class SimulationOutputFile:
       def __init__(self, path: str):
           self.path = path
           self.header: SimulationMetadata
           self.events: List[SimulationEvent]
           self.snapshots: List[StateSnapshot]
       
       def save(self):
           # Write binary file with header + events + snapshots
       
       def load(self):
           # Read and parse binary file
   ```

3. **Add compression support**
   - Implement gzip compression for output files
   - Configurable compression level
   - Streaming compression for large files

**Deliverables**:
- [ ] Binary serialization system
- [ ] Output file format specification
- [ ] Compression support
- [ ] File I/O performance tests

### Step 2B.3: Integration Testing

**Goal**: Validate recorder works with headless simulation

**Tasks**:
1. **Create headless runner with recording**
   ```python
   class HeadlessSimulationRunner:
       def __init__(self, config: SimulationConfig, output_path: str = None):
           self.config = config
           self.recorder = SimulationRecorder(output_path) if output_path else None
       
       def run(self, steps: int) -> SimulationOutput:
           # Run simulation with optional recording
   ```

2. **Test recording performance**
   ```bash
   # Performance tests with recording
   python scripts/performance_test.py --headless --record --steps 1000
   python scripts/performance_test.py --headless --record --steps 10000
   ```

3. **Validate output file integrity**
   - Test file loading and parsing
   - Verify event completeness
   - Check snapshot accuracy

**Deliverables**:
- [ ] Headless runner with recording
- [ ] Performance benchmarks with recording
- [ ] Output file validation tests
- [ ] Integration test suite

### Step 2B.4: Git Checkpoint

```bash
git tag phase2b-recorder-complete -m "Phase 2B: SimulationRecorder complete"
```

---

## Phase 2C: PlaybackEngine Implementation (Days 11-15)

### Step 2C.1: Core Playback Engine

**Goal**: Build system to reconstruct simulation state from recorded data

**Tasks**:
1. **Create PlaybackEngine class**
   ```bash
   # Create playback module
   touch src/econsim/output/playback.py
   touch src/econsim/output/state_reconstructor.py
   ```

2. **Implement state reconstruction**
   ```python
   class PlaybackEngine:
       def __init__(self, output_file: SimulationOutputFile):
           self.output_file = output_file
           self.current_step = 0
           self.current_state: SimulationState = None
           self.snapshot_cache: Dict[int, StateSnapshot] = {}
       
       def load_snapshot(self, step: int) -> SimulationState:
           # Load nearest snapshot and replay events to target step
       
       def get_state_at_step(self, step: int) -> SimulationState:
           # Get complete simulation state at specific step
       
       def get_events_for_step(self, step: int) -> List[SimulationEvent]:
           # Get all events for a specific step
   ```

3. **Implement efficient seeking**
   - Find nearest snapshot for target step
   - Replay events from snapshot to target
   - Cache reconstructed states
   - Handle forward/backward seeking

**Deliverables**:
- [ ] PlaybackEngine class implementation
- [ ] State reconstruction system
- [ ] Seeking functionality
- [ ] Performance optimization

### Step 2C.2: VCR Controls

**Goal**: Implement playback controls (play, pause, seek, speed)

**Tasks**:
1. **Create playback controller**
   ```python
   class PlaybackController:
       def __init__(self, playback_engine: PlaybackEngine):
           self.engine = playback_engine
           self.is_playing = False
           self.playback_speed = 1.0
           self.current_step = 0
           self.target_step = None
       
       def play(self):
           # Start playback
       
       def pause(self):
           # Pause playback
       
       def seek_to_step(self, step: int):
           # Seek to specific step
       
       def set_speed(self, speed: float):
           # Set playback speed multiplier
   ```

2. **Implement timing system**
   - Frame-rate independent playback
   - Configurable playback speeds
   - Smooth seeking between steps
   - Pause/resume functionality

3. **Add playback callbacks**
   ```python
   class PlaybackController:
       def __init__(self, on_step_change: Callable[[int], None] = None,
                    on_state_change: Callable[[SimulationState], None] = None):
           self.on_step_change = on_step_change
           self.on_state_change = on_state_change
   ```

**Deliverables**:
- [ ] PlaybackController implementation
- [ ] VCR-style controls
- [ ] Timing and speed control
- [ ] Callback system for GUI integration

### Step 2C.3: Performance Optimization

**Goal**: Ensure playback performance meets targets

**Tasks**:
1. **Optimize state reconstruction**
   - Efficient snapshot loading
   - Minimal event replay
   - Smart caching strategies
   - Memory usage optimization

2. **Benchmark playback performance**
   ```bash
   # Playback performance tests
   python scripts/playback_performance_test.py --steps 10000 --agents 100
   python scripts/playback_performance_test.py --seek-test --steps 10000
   ```

3. **Profile and optimize bottlenecks**
   - Identify performance bottlenecks
   - Optimize critical paths
   - Add performance monitoring
   - Memory usage profiling

**Deliverables**:
- [ ] Performance optimization
- [ ] Playback benchmarks
- [ ] Memory usage optimization
- [ ] Performance monitoring tools

### Step 2C.4: Git Checkpoint

```bash
git tag phase2c-playback-complete -m "Phase 2C: PlaybackEngine complete"
```

---

## Phase 2D: Launcher GUI Rebuild (Days 16-22)

### Step 2D.1: Launcher Architecture Redesign

**Goal**: Rebuild existing `make launcher` system to work as playback consumer

**Current System Understanding**:
- `make launcher` → `VMTLauncherWindow` (main launcher window)
- Test Gallery → `TestGalleryWidget` with `TestCardWidget` cards
- Launch Test → `BaseManualTest` window with `EmbeddedPygameWidget`
- Test execution → Direct simulation running in GUI (BROKEN after Phase 1)

**New Architecture**:
- `make launcher` → Same `VMTLauncherWindow` (preserve existing UX)
- Test Gallery → Same `TestGalleryWidget` (preserve existing UX)
- Launch Test → `BasePlaybackTest` window (similar to current `BaseManualTest`)
- Test execution → **NEW**: Headless simulation → Output file → GUI playback
- GUI behavior → **NEW**: Shows "Start Test" → Runs headless → Loads output → VCR controls

**Tasks**:
1. **Modify test launch flow**
   ```bash
   # Update launcher components
   # src/econsim/tools/launcher/app_window.py - modify _launch_test()
   # src/econsim/tools/launcher/widgets.py - modify TestGalleryWidget
   # src/econsim/tools/launcher/cards.py - modify TestCard launch behavior
   ```

2. **Create playback-based test execution**
   ```python
   class BasePlaybackTest(QWidget):  # Inherits from BaseManualTest
       def __init__(self, config: TestConfiguration):
           super().__init__(config)
           self.playback_controller: PlaybackController = None
           self.current_output_file: SimulationOutputFile = None
           self.output_file_path: str = None
           
           # Initially shows "Start Test" button (like current BaseManualTest)
           # After simulation completes, loads output file for playback
           self.setup_playback_ui()
   ```

3. **Integrate with existing launcher system**
   - Preserve existing `make launcher` UX
   - Replace `BaseManualTest` with `BasePlaybackTest` (single mode)
   - Update `TestExecutor` to launch `BasePlaybackTest`
   - Maintain same user workflow: Launch → Start Test → Playback

**Deliverables**:
- [ ] Modified launcher architecture design
- [ ] BasePlaybackTest implementation
- [ ] Integration with existing launcher system
- [ ] Preserved user experience

### Step 2D.2: Update BaseManualTest Framework

**Goal**: Transform existing test framework to work with playback instead of live simulation

**Tasks**:
1. **Create BasePlaybackTest class**
   ```python
   class BasePlaybackTest(BaseManualTest):
       def __init__(self, config: TestConfiguration, playback_file: str):
           super().__init__(config)
           self.playback_file = playback_file
           self.playback_controller: PlaybackController = None
           self.current_output_file: SimulationOutputFile = None
           
           # Load playback file instead of creating simulation
           self.load_playback_file()
           
           # Override UI setup for playback controls
           self.setup_playback_ui()
   ```

2. **Modify test layout for playback**
   ```python
   class PlaybackTestLayout(TestLayout):
       def __init__(self, config: TestConfiguration, playback_controller: PlaybackController):
           super().__init__(config)
           self.playback_controller = playback_controller
           
           # Replace simulation controls with playback controls
           self.setup_playback_controls()
       
       def setup_playback_controls(self):
           # VCR-style controls: Play, Pause, Seek, Speed
           # Replace start_button with play_button
           # Add seek slider
           # Add speed control
   ```

3. **Update test execution flow**
   ```python
   def start_test(self):
       """Run headless simulation, then load output for playback."""
       try:
           # Phase 1: Run headless simulation with recording
           self.log_status("🚀 Starting headless simulation...")
           self.run_headless_simulation()
           
           # Phase 2: Load output file for playback
           self.log_status("📁 Loading simulation output...")
           self.load_playback_file()
           
           # Phase 3: Setup playback controls
           self.log_status("🎮 Setting up playback controls...")
           self.setup_playback_controls()
   
   def run_headless_simulation(self):
       """Run simulation headless with recording enabled."""
       # Create headless runner with recording
       runner = HeadlessSimulationRunner(self.config, output_path=self.get_output_path())
       runner.run(steps=self.config.steps)
       self.output_file_path = runner.output_file_path
   
   def load_playback_file(self):
       """Load completed simulation output for playback."""
       self.current_output_file = SimulationOutputFile.load(self.output_file_path)
       self.playback_controller = PlaybackController(self.current_output_file)
       
       # Create pygame widget for playback rendering
       from econsim.gui.embedded_pygame import EmbeddedPygameWidget
       self.pygame_widget = EmbeddedPygameWidget(
           playback_controller=self.playback_controller
       )
       
       # Connect playback controller to widget
       self.playback_controller.on_step_change.connect(self.pygame_widget.update_from_playback)
   ```

**Deliverables**:
- [ ] BasePlaybackTest implementation
- [ ] PlaybackTestLayout with VCR controls
- [ ] Updated EmbeddedPygameWidget integration
- [ ] Playback-based test execution

### Step 2D.3: Update Launcher Integration

**Goal**: Modify launcher system to support playback mode while preserving UX

**Tasks**:
1. **Update TestExecutor for single mode**
   ```python
   class TestExecutor:
       def launch_framework(self, test_name: str):
           """Launch test in playback mode (headless sim → playback)."""
           config = self.get_test_config(test_name)
           
           # Always launch BasePlaybackTest (replaces BaseManualTest)
           from .framework.playback_test import BasePlaybackTest
           test_window = BasePlaybackTest(config)
           
           test_window.show()
   ```

2. **Keep test cards simple (single mode)**
   ```python
   class TestCardWidget(QWidget):
       def __init__(self, config: TestConfiguration):
           super().__init__()
           self.config = config
           self.setup_ui()
       
       def setup_ui(self):
           # Single launch button (same as current)
           self.launch_button = QPushButton("Launch Test")
           
           # Button launches BasePlaybackTest which handles:
           # 1. Headless simulation execution
           # 2. Output file generation  
           # 3. Playback controls
   ```

3. **Add automatic file management**
   - Create directory structure for recorded simulations
   - Generate playback files automatically during headless execution
   - Clean up temporary files after playback session
   - Organize output files by test configuration and timestamp

**Deliverables**:
- [ ] Updated TestExecutor for single mode
- [ ] Simplified test cards (single launch button)
- [ ] Automatic file management system
- [ ] Clean output file organization

### Step 2D.4: Integration and Testing

**Goal**: Test complete launcher system with playback functionality

**Tasks**:
1. **Test launcher with single mode**
   ```bash
   # Test make launcher with new functionality
   make launcher
   # Click on test card → "Launch Test" → opens BasePlaybackTest window
   ```

2. **Test single-mode functionality**
   ```bash
   # Test single mode: Click "Launch Test"
   # 1. Opens BasePlaybackTest window
   # 2. Click "Start Test" → runs headless simulation
   # 3. After completion → shows playback with VCR controls
   ```

3. **Validate playback controls in test windows**
   - Test VCR-style controls (play/pause/seek/speed)
   - Test step-by-step navigation
   - Test speed control
   - Test file loading and error handling

4. **Test automatic file management**
   - Test automatic playback file generation during headless execution
   - Test file cleanup after playback session
   - Test file validation and error handling
   - Test organized output file structure

**Deliverables**:
- [ ] Integrated launcher with single mode
- [ ] Single-mode functionality testing (Launch → Start Test → Playback)
- [ ] Playback control validation
- [ ] Automatic file management testing

### Step 2D.5: Git Checkpoint

```bash
git tag phase2d-gui-rebuild-complete -m "Phase 2D: GUI rebuild complete"
```

---

## Phase 2E: Integration Testing (Days 23-25)

### Step 2E.1: End-to-End Testing

**Goal**: Validate complete workflow from simulation to playback

**Tasks**:
1. **Test complete workflow**
   ```bash
   # Record simulation
   python scripts/demo_single_agent.py --headless --record --steps 1000 --output test_run.bin
   
   # Playback in GUI
   python scripts/playback_gui.py --file test_run.bin
   ```

2. **Performance validation**
   ```bash
   # Performance benchmarks
   python scripts/performance_test.py --record --steps 10000 --agents 100
   python scripts/playback_performance_test.py --file large_simulation.bin
   ```

3. **Memory usage validation**
   - Test large simulation recording
   - Test long playback sessions
   - Validate memory cleanup
   - Check for memory leaks

**Deliverables**:
- [ ] End-to-end workflow tests
- [ ] Performance validation
- [ ] Memory usage validation
- [ ] Test automation scripts

### Step 2E.2: User Experience Testing

**Goal**: Ensure GUI provides good user experience

**Tasks**:
1. **Test user workflows**
   - Load simulation file
   - Navigate through playback
   - Use all controls
   - Test edge cases

2. **Validate GUI responsiveness**
   - Test with large simulation files
   - Test seeking performance
   - Test UI responsiveness during playback
   - Test error handling

3. **Documentation and help**
   - Create user guide for playback GUI
   - Add tooltips and help text
   - Create example simulation files
   - Document file format

**Deliverables**:
- [ ] User workflow tests
- [ ] GUI responsiveness validation
- [ ] User documentation
- [ ] Example files

### Step 2E.3: Final Validation

**Goal**: Ensure all success criteria are met

**Tasks**:
1. **Validate success criteria**
   - ✅ Working Playback System
   - ✅ Performance Benchmarks
   - ✅ GUI Functional Again
   - ✅ VCR Controls

2. **Update project status**
   - Update REFACTOR_STATUS.md
   - Mark Phase 2 as complete
   - Document known issues
   - Plan Phase 3 activities

3. **Create final git checkpoint**
   ```bash
   git tag phase2-complete -m "Phase 2: Output Architecture Complete"
   ```

**Deliverables**:
- [ ] Success criteria validation
- [ ] Updated project status
- [ ] Final git checkpoint
- [ ] Phase 2 completion summary

---

## Phase 2 Completion Summary

### Expected Deliverables

**Core System**:
- [ ] `SimulationRecorder` - Records complete simulation runs
- [ ] `PlaybackEngine` - Reconstructs state from recorded data
- [ ] `PlaybackController` - VCR-style playback controls
- [ ] Binary output format - Efficient simulation data storage

**Launcher System**:
- [ ] `VMTLauncherWindow` - Updated main launcher window (preserve UX)
- [ ] `TestGalleryWidget` - Updated with playback launch options
- [ ] `BasePlaybackTest` - New playback-based test window
- [ ] `EmbeddedPygameWidget` - Updated for playback rendering
- [ ] VCR-style controls - Play, pause, seek, speed controls
- [ ] File loading interface - Load recorded simulations

**Testing & Validation**:
- [ ] End-to-end workflow tests
- [ ] Performance benchmarks
- [ ] Memory usage validation
- [ ] User experience testing

### Success Metrics

**Performance Targets**:
- Recording overhead: < 10% of simulation time
- Playback performance: Real-time or better
- Memory usage: < 2x simulation memory
- File size: < 50MB for 10,000 steps with 100 agents

**Functionality Targets**:
- `make launcher` works with single mode (Launch → Start Test → Playback)
- Test gallery shows single "Launch Test" option (same as current)
- Headless simulation execution works seamlessly
- VCR controls work smoothly in test windows after simulation completion
- Seeking to any step < 1 second
- Playback speed control 0.1x to 10x
- Automatic file management (generate, load, cleanup)

### Git Checkpoints

```bash
# Before Phase 2
git tag phase2-start -m "Before Phase 2: Output Architecture"

# Phase 2A: Prototype complete
git tag phase2a-prototype-complete -m "Phase 2A: Prototype & benchmark complete"

# Phase 2B: Recorder complete
git tag phase2b-recorder-complete -m "Phase 2B: SimulationRecorder complete"

# Phase 2C: Playback complete
git tag phase2c-playback-complete -m "Phase 2C: PlaybackEngine complete"

# Phase 2D: GUI rebuild complete
git tag phase2d-gui-rebuild-complete -m "Phase 2D: GUI rebuild complete"

# Phase 2 Complete
git tag phase2-complete -m "Phase 2: Output Architecture Complete"
```

### Timeline Summary

- **Days 1-3**: Phase 2A - Prototype & Benchmark
- **Days 4-10**: Phase 2B - SimulationRecorder Implementation
- **Days 11-15**: Phase 2C - PlaybackEngine Implementation
- **Days 16-22**: Phase 2D - GUI Rebuild
- **Days 23-25**: Phase 2E - Integration Testing

**Total**: 25 working days = 5 weeks

### Risk Mitigation

**Technical Risks**:
- Performance bottlenecks → Prototype early, benchmark continuously
- Memory usage issues → Profile memory usage, implement streaming
- File format complexity → Start simple, iterate based on needs

**Schedule Risks**:
- GUI complexity → Build incrementally, test frequently
- Integration issues → Test integration points early
- Performance requirements → Validate performance targets early

### Next Steps After Phase 2

Phase 2 completion enables:
- **Phase 3**: Clean up test suite (can overlap with Phase 2)
- **Phase 4**: Consolidate MANUAL_TESTS
- **Phase 5**: Improve preference extension workflow
- **Phase 6**: Document extension patterns

---

## Implementation Notes

### Development Approach

1. **Incremental Development**: Build and test each component incrementally
2. **Performance First**: Validate performance at each step
3. **Integration Testing**: Test integration points frequently
4. **User Experience**: Keep user experience in mind throughout

### Key Design Decisions

1. **Binary Format**: Use binary serialization for performance
2. **Snapshot Strategy**: Periodic snapshots with event replay
3. **Launcher as Consumer**: Existing launcher becomes playback consumer, no simulation coupling
4. **Single Mode**: Replace BaseManualTest with BasePlaybackTest (headless sim → playback)
5. **VCR Controls**: Standard playback controls for familiarity
6. **Preserve UX**: Maintain existing `make launcher` user experience

### Dependencies

- **Phase 1 Complete**: GUI-Simulation decoupling must be complete
- **FileObserver System**: Leverage existing observability infrastructure
- **PyQt6**: GUI framework (already available)
- **Pygame**: Rendering engine (already available)

This implementation plan provides a clear, step-by-step approach to rebuilding the existing `make launcher` system as a playback consumer while maintaining the clean separation achieved in Phase 1 and preserving the existing user experience.

## Summary of Changes Made

The Phase 2 plan has been updated to specifically address the existing `make launcher` system:

### **Current System (Broken after Phase 1)**:
- `make launcher` → `VMTLauncherWindow` 
- Test Gallery → `TestGalleryWidget` with test cards
- Launch Test → `BaseManualTest` window with **BROKEN** live simulation

### **New System (Single Mode)**:
- `make launcher` → Same `VMTLauncherWindow` (preserve UX)
- Test Gallery → Same `TestGalleryWidget` with **single launch option**
- Launch Test → **NEW**: `BasePlaybackTest` window with headless sim → playback
- **Single Mode**: Launch → Start Test → Headless Execution → Playback

### **Key Benefits**:
✅ **Preserves existing UX** - `make launcher` works exactly the same
✅ **Fixes broken GUI** - Replaces broken BaseManualTest with working BasePlaybackTest
✅ **Clean architecture** - No GUI-simulation coupling, pure playback consumer
✅ **Seamless workflow** - User clicks "Start Test" → headless execution → VCR controls
✅ **Familiar controls** - VCR-style playback controls in test windows

This approach ensures that users can continue using the familiar `make launcher` interface while gaining the benefits of the new playback architecture.
