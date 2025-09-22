# Economic Simulation Platform: Project Skeleton Plan

**Project Name**: EconSim Platform  
**Project Type**: Python Library with Educational Focus  
**Development Philosophy**: Visualization-First Agent-Based Economic Modeling

---

## Phase 1: Core Understanding (30 min)

### 1. Problem & Success Definition

**Problem**: Build a comprehensive educational and research platform that implements the full breadth of modern microeconomic theory, starting with the foundational dual framework of preference relations and choice functions, then progressing through the complete spectrum of economic models. Use visualization-first development with spatial NxN grid simulations to demonstrate why these concepts are powerful and flexible analytical tools, combining interactive visual simulations with statistical dashboards for deep economic understanding and novel research investigation.

**Core Educational and Research Mission**: Establish the fundamental relationship between preference relations, choice functions, and utility functions through immediate spatial visualization, then build systematically through consumer theory, market equilibrium, game theory, information economics, and beyond. The platform serves as both an educational tool for building intuition about abstract economic concepts through concrete spatial interactions, and as a research instrument enabling investigation of advanced microeconomic phenomena, mechanism design, and spatial economic behavior for graduate students and researchers.

**Success Metrics** (≤120 words):
- **R-01**: Students demonstrate improved comprehension of preference-choice-utility relationships through spatial visualization exercises and assessments
- **R-02**: Interactive parameter adjustments (preferences, constraints, spatial costs) produce immediate visual feedback and statistical updates within 1 second
- **R-03**: Platform generates exportable economic insights, statistical dashboards, and publication-quality visualizations for classroom and research use
- **R-04**: Spatial grid simulations work seamlessly across educational computing environments with consistent visual behavior
- **R-05**: Foundational spatial architecture scales from simple utility maximization to complex multi-agent economic models and game theory
- **R-06**: Economic simulations reproduce theoretical predictions with mathematical accuracy while maintaining visual clarity and educational intuition

### 2. Key User Scenarios (3-5 flows)

**S-01**: Economics Instructor wants to teach consumer choice fundamentals
Flow: Launch preference tutorial → Show students spatial agent making choices → Adjust preference parameters → Watch agent behavior change → Export results for homework
Success: Students understand preference-choice-utility relationships through visual spatial demonstration
Failure modes: Spatial visualization confuses rather than clarifies, parameter changes don't produce clear behavioral differences

**S-02**: Economics Student wants to explore utility maximization
Flow: Open spatial grid simulation → Place agent and valued items on grid → Set budget/movement constraints → Watch agent optimize spatially → Analyze statistical dashboard
Success: Student gains intuitive understanding of constrained optimization through spatial agent behavior
Failure modes: Agent behavior appears random, constraints unclear, statistical feedback inadequate

**S-03**: Educator wants to build custom economic scenarios
Flow: Use scenario builder → Define agent preferences and spatial constraints → Test educational effectiveness → Share with colleagues → Export for classroom use
Success: Custom scenarios effectively teach targeted economic concepts with measurable learning outcomes
Failure modes: Scenario builder too complex, scenarios don't align with educational objectives, sharing mechanisms fail

**S-04**: Researcher wants to implement new economic theory
Flow: Extend platform with new economic model → See immediate spatial visualization → Validate against theoretical predictions → Generate statistical analysis → Publish results
Success: New theory implementation matches analytical solutions and provides novel educational insights
Failure modes: Visualization doesn't illuminate theory, implementation contains theoretical errors, performance inadequate

**S-05**: Student wants to understand complex economic interactions
Flow: Progress through curriculum → Start with simple spatial choice → Build to multi-agent interactions → Explore game theory scenarios → Export analysis for projects
Success: Student builds understanding from concrete spatial interactions to abstract economic theory
Failure modes: Progression too steep, spatial metaphors break down for complex theory, analysis tools inadequate

**S-06**: Graduate Student/Researcher wants to investigate spatial economic phenomena
Flow: Design custom spatial scenario → Implement novel agent behaviors → Run large-scale simulations → Analyze emergent patterns → Export research-grade data and visualizations
Success: Novel insights about spatial economic behavior, publication-quality results, reproducible research methodology
Failure modes: Platform lacks flexibility for novel research questions, performance insufficient for research-scale simulations, data export inadequate for statistical analysis

### 3. System Sketch (components + data flow)

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Spatial Foundation│◄──►│ Consumer Theory  │◄──►│ Educational UI  │
│      (M-01)      │    │     (M-02)       │    │     (M-03)      │
│ • NxN Grid       │    │ • Preferences    │    │ • Tutorials     │
│ • Agent Movement │    │ • Choice Functions│    │ • Explanations  │
│ • Constraints    │    │ • Utility Max    │    │ • Assessments   │
│ • Extensibility  │    │ • Custom Behaviors│    │ • Research UI   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────────┐
                    │  Analytics Engine   │
                    │      (M-04)         │
                    │ • Statistical Dash  │
                    │ • Research Export   │
                    │ • Theory Validation │
                    │ • Reproducibility   │
                    └─────────────────────┘
```

**Data Flow**: Spatial Agent State → Economic Choice Calculation → Visual Rendering → Statistical Analysis → Research Data Export → Parameter Feedback → Spatial Update Loop

### 4. Risk Radar (top 5 risks with impact)

**R-07**: Visual complexity overwhelms educational value
Impact: High | Likelihood: Med
Validation: A/B test with economics students measuring comprehension before/after interaction
Mitigation: Progressive complexity reveal, simple defaults, extensive user testing with educators

**R-08**: Performance degrades below educational threshold (< 10 FPS) or research scale requirements
Impact: High | Likelihood: Med
Validation: Stress test with 1000+ agents for education, 10,000+ agents for research scale, profile rendering bottlenecks
Mitigation: Spatial partitioning, level-of-detail rendering, performance budgets per visual component, research-mode optimizations

**R-09**: Economic algorithms contain theoretical errors
Impact: High | Likelihood: Low
Validation: Compare simulation results against published analytical solutions for standard economic models
Mitigation: Theoretical validation test suite, economics expert code review, mathematical cross-reference system

**R-10**: Platform-specific rendering inconsistencies break cross-platform use
Impact: Med | Likelihood: Med
Validation: Automated visual regression testing across macOS/Linux/Windows with identical scenarios
Mitigation: Standardized rendering pipeline, consistent font/graphics handling, automated cross-platform CI

**R-11**: Development complexity prevents rapid iteration and feature addition
Impact: Med | Likelihood: High
Validation: Track feature development velocity, measure time from concept to working visualization
Mitigation: Modular architecture with clear interfaces, comprehensive visual testing, hot-reload development environment

**R-12**: Research results lack reproducibility undermining scientific credibility
Impact: High | Likelihood: Low
Validation: Test scenario reproduction across different platforms and time periods with identical results
Mitigation: Comprehensive metadata tracking, deterministic random seeding, version control for all research parameters

### 5. Assumptions & Validation Experiments

**A-01**: Pygame provides sufficient performance for educational scenarios (≥30 FPS with 50+ agents)
Counterpoint: Modern web technologies (WebGL, Canvas) might be more accessible and performant
Validation: Benchmark rendering performance with target agent counts across platforms
Experiment: Build minimal grid renderer with 100 agents, measure frame rates and memory usage

**A-02**: Visual-first development improves code quality and reduces bugs
Counterpoint: Visual validation overhead might slow development without corresponding quality gains
Validation: Track bug rates, development velocity, and code review feedback compared to traditional TDD
Experiment: Develop same feature using visual-first vs traditional approaches, compare outcomes

**A-03**: Economic theory can be made visually intuitive without sacrificing mathematical rigor
Counterpoint: Visual simplification might lead to theoretical inaccuracies or oversimplification
Validation: Test economic concept comprehension with students using visual vs traditional methods
Experiment: Create utility function visualizer, validate mathematical accuracy against analytical solutions

**A-04**: Real-time parameter adjustment enhances learning effectiveness
Counterpoint: Too much interactivity might distract from core economic concepts
Validation: Measure learning outcomes with interactive vs static educational materials
Experiment: Build movement cost slider, measure student engagement and concept retention

**A-05**: Cross-platform Python/Pygame deployment is feasible for educational distribution
Counterpoint: Installation complexity might prevent adoption by educators
Validation: Test installation process with educators across different platforms and technical skill levels
Experiment: Create installation packages for each platform, measure setup success rates

---

## Phase 2: Design Contracts (45 min)

### 6. Domain Model (core entities + relationships)

**SpatialAgent (E-01)**
```python
@dataclass
class SpatialAgent:
    id: AgentID
    position: Coordinate  # (x, y) grid position
    preference_relation: PreferenceFunction  # Complete, transitive preference ordering
    choice_function: ChoiceFunction  # Rational choice from available options
    utility_function: UtilityFunction  # Numerical representation of preferences
    constraints: SpatialConstraints  # Movement costs, budget, time limits
    behavior_model: BehaviorModel  # Customizable agent behavior for research
    learning_parameters: LearningState  # For bounded rationality, adaptation research
    visual_state: RenderingData  # Color, size, animation state, choice visualization
```

**SpatialChoice (E-02)**
```python
@dataclass  
class SpatialChoice:
    agent: SpatialAgent
    available_options: List[SpatialOption]  # Items/locations available to agent
    chosen_option: SpatialOption  # Agent's optimal choice
    choice_path: List[Coordinate]  # Spatial path to chosen option
    utility_achieved: float  # Utility level from choice
    choice_rationale: EducationalExplanation  # Why this choice was optimal
```

**SpatialGrid (E-03)**
```python
@dataclass
class SpatialGrid:
    dimensions: Tuple[int, int]  # (width, height)
    agents: List[SpatialAgent]  # Agents making spatial choices
    items: List[ValuedItem]  # Goods/resources distributed on grid  
    constraints: GridConstraints  # Movement costs, barriers, time limits
    choice_history: List[SpatialChoice]  # Record of all agent choices
    render_cache: VisualCache
```

**EconomicScenario (E-04)**
```python
@dataclass
class EconomicScenario:
    grid: SpatialGrid
    theory_focus: EconomicConcept  # Which economic theory is being demonstrated
    learning_objectives: List[LearningGoal]  # What students should understand
    assessment_criteria: List[AssessmentMetric]  # How to measure understanding
    research_parameters: ResearchConfig  # For customizable research investigations
    statistical_dashboard: AnalyticsDashboard  # Real-time economic metrics
    data_export_config: ExportConfiguration  # Research-grade data output settings
    reproducibility_metadata: ReproducibilityData  # For research reproducibility
    educational_context: LearningState
```

**Key Relationships**:
- SpatialAgent ↔ SpatialGrid: Agent positioned on grid making spatial economic choices (1:1 position, many:many choice interactions)
- SpatialAgent ↔ SpatialChoice: Agent generates choices based on preferences, constraints, and customizable behaviors (1:many choice history)
- SpatialChoice ↔ EconomicScenario: Choices demonstrate economic theory and enable novel research investigation (many:1 theory/research demonstration)
- All entities → AnalyticsDashboard: Real-time statistical analysis, educational insights, and research-grade data export
- EconomicScenario → ReproducibilitySystem: Research scenarios maintain full reproducibility metadata for scientific validation

### 7. Core Interfaces (3-5 key APIs with intent)

**F-01**: VisualSimulation
```python
class VisualSimulation:
    def initialize(config: SimConfig) -> SimulationState
    def step() -> VisualUpdate
    def render() -> FrameBuffer
    def get_metrics() -> EducationalMetrics
```
Purpose: Primary orchestration interface for educational economic simulation
Happy path: initialize() → step() → render() → adjust_parameters() → step()
Error cases: Invalid config → ValidationError, Render failure → RenderError, Performance timeout → PerformanceError
Key constraint: Every simulation state must be visually representable within 33ms (30 FPS)

**F-02**: EconomicEngine
```python
class EconomicEngine:
    def calculate_equilibrium(agents: List[Agent]) -> EquilibriumResult
    def execute_trades(orders: List[Order]) -> TradeResults
    def validate_theory(result: Any) -> TheoreticalValidation
```
Purpose: Core economic computation with mathematical validation against theory
Happy path: calculate_equilibrium() → convergence with theoretical accuracy
Error cases: No equilibrium exists → NoEquilibriumError, Convergence timeout → ConvergenceError
Key constraint: All computations must match economic theory within 0.01% tolerance

**F-03**: VisualRenderer
```python
class VisualRenderer:
    def render_frame(state: SimulationState) -> VisualFrame
    def create_animation(states: List[State]) -> Animation
    def export_visualization(animation: Animation) -> ExportFormat
```
Purpose: Transform economic state into educational visualizations with performance guarantees
Happy path: render_frame() → visual_frame within performance budget
Error cases: Invalid state → RenderError, Performance timeout → PerformanceError
Key constraint: Rendering must complete within 33ms for 30 FPS educational experience

**F-04**: EducationalInterface
```python
class EducationalInterface:
    def explain_concept(state: State, concept: EconConcept) -> Explanation
    def generate_quiz(topic: Topic) -> InteractiveQuiz
    def track_learning(interactions: List[Interaction]) -> LearningAnalytics
```
Purpose: Provide interactive learning features with theoretical accuracy
Happy path: explain_concept() → clear, accurate educational content
Error cases: Unknown concept → ConceptError, Context mismatch → ContextError
Key constraint: All explanations must be theoretically accurate and age-appropriate

**F-05**: ParameterController
```python
class ParameterController:
    def set_parameter(name: str, value: float) -> ImmediateUpdate
    def get_parameter_bounds(name: str) -> Bounds
    def validate_parameter_set(params: Dict) -> ValidationResult
```
Purpose: Real-time parameter adjustment with immediate visual feedback and constraint validation
Happy path: set_parameter() → immediate visual update within 100ms
Error cases: Invalid parameter → ParameterError, Value out of bounds → BoundsError
Key constraint: Parameter changes must propagate to visualization within 100ms

### 8. Error Handling Strategy

**Educational Error Philosophy**: Transform computational errors into learning opportunities

**Error Categories**:

**Economic Errors (EC-01)**: Theoretical violations, convergence failures
- Strategy: Visual explanation of economic problem (e.g., "No equilibrium exists because...")
- Recovery: Suggest theoretically valid parameter adjustments with visual guidance
- Example: Market fails to clear → Show excess demand/supply visually, suggest price adjustments

**Performance Errors (PE-01)**: Frame rate drops, computation timeouts
- Strategy: Graceful degradation maintaining educational value (reduce visual complexity, not accuracy)
- Recovery: Automatic performance scaling with user notification and educational context
- Example: Too many agents → Reduce animation detail while maintaining economic accuracy

**Visual Errors (VE-01)**: Rendering failures, display inconsistencies
- Strategy: Fallback to simplified but accurate visualizations
- Recovery: Maintain simulation state integrity, attempt progressive render recovery
- Example: Complex visualization fails → Fall back to simple grid view with data overlay

**Educational Errors (ED-01)**: Confusing visualizations, theoretical inaccuracies
- Strategy: Immediate user feedback collection with alternative explanation generation
- Recovery: Revert to validated educational content, log for improvement
- Example: Student indicates confusion → Offer alternative explanation methods, simpler visualizations

**Error Logging Strategy**: All errors include educational context, student interaction history, and theoretical validation state for debugging learning effectiveness

### 9. Testing Strategy Outline

**Visual Test-Driven Development Philosophy**: Build tests that validate both computational correctness and educational effectiveness

**T-01**: Visual Regression Tests
Purpose: Ensure visual consistency and educational clarity across code changes
Method: Screenshot comparison with perceptual hashing and tolerance thresholds
Coverage: All major visual components, educational scenarios, cross-platform rendering
Test Example: `test_utility_curve_visualization()` captures and validates Cobb-Douglas curve shape

**T-02**: Economic Validation Tests
Purpose: Verify mathematical correctness against established economic theory
Method: Compare simulation results to analytical solutions from economics literature
Coverage: Utility maximization, equilibrium computation, welfare analysis, spatial economics
Test Example: `test_walrasian_equilibrium()` validates price discovery against analytical solution

**T-03**: Educational Effectiveness Tests
Purpose: Validate learning value through user comprehension measurement
Method: A/B testing with pre/post assessments, eye-tracking studies, concept mapping
Coverage: Interactive tutorials, parameter adjustment exercises, visual explanations
Test Example: `test_deadweight_loss_comprehension()` measures understanding before/after visualization

**T-04**: Performance Benchmark Tests
Purpose: Maintain educational performance standards (≥30 FPS, ≤100ms response)
Method: Automated performance profiling with acceptable threshold enforcement
Coverage: Rendering pipeline, economic computation, parameter responsiveness, memory usage
Test Example: `test_50_agent_performance()` ensures smooth interaction with target agent count

**T-05**: Cross-Platform Integration Tests
Purpose: Ensure consistent educational experience across operating systems
Method: Automated test suite execution on macOS/Linux/Windows with result comparison
Coverage: Visual rendering, file I/O, font rendering, performance characteristics
Test Example: `test_cross_platform_visual_consistency()` validates identical screenshots across platforms

### 10. Integration Points & Dependencies

**Core Dependencies**:
- **Python 3.11+**: Type hints, dataclasses, performance improvements for educational responsiveness
- **Pygame 2.5+**: Cross-platform real-time visualization, educational graphics capabilities
- **NumPy 1.24+**: Efficient numerical computation for economic calculations
- **SciPy 1.10+**: Optimization algorithms for equilibrium solving, statistical analysis
- **Matplotlib 3.7+**: Static analysis plots, publication-quality educational diagrams

**Development Dependencies**:
- **pytest 7.4+**: Testing framework with visual testing extensions
- **Black 23.0+**: Code formatting for educational code clarity
- **mypy 1.5+**: Type checking for educational code reliability
- **Jupyter**: Interactive development notebooks for educational content creation

**Educational Dependencies** (Optional):
- **Pillow**: Image processing for visual regression testing
- **imageio**: Animation export for educational presentations
- **pandas**: Data analysis for educational metrics

**Integration Strategy**:
- **Zero External Services**: Fully self-contained educational tool, no network dependencies
- **Minimal Dependencies**: Reduce complexity for educational deployment
- **Version Pinning**: Ensure reproducible educational environments
- **Graceful Degradation**: Optional dependencies enhance but don't break core functionality

**No Integration Points**:
- No databases (educational scenarios use generated data)
- No web APIs (standalone educational tool)
- No cloud services (privacy and accessibility for education)
- No real-time data feeds (focus on theoretical economic models)

---

## Phase 3: Implementation Readiness (30 min)

### 11. Directory Structure & File Plan

```
econsim-platform/
├── src/
│   └── econsim/                      # Main package
│       ├── __init__.py              # S-01: Package exports and version
│       ├── main.py                  # S-02: Application entry point
│       ├── spatial/                 # M-01: Spatial Foundation Module
│       │   ├── __init__.py         # Spatial foundation exports
│       │   ├── grid.py             # S-03: NxN grid world with spatial indexing
│       │   ├── agents.py           # S-04: Spatial agents with movement and constraints
│       │   ├── choices.py          # S-05: Spatial choice modeling and visualization  
│       │   ├── renderer.py         # S-06: Spatial visualization and animation
│       │   └── constraints.py      # S-07: Movement costs, barriers, time limits
│       ├── theory/                  # M-02: Consumer Theory Module
│       │   ├── __init__.py         # Consumer theory exports
│       │   ├── preferences.py      # S-08: Preference relations and orderings
│       │   ├── choice_functions.py # S-09: Rational choice functions and revealed preference
│       │   ├── utility.py          # S-10: Utility functions and optimization
│       │   ├── demand.py           # S-11: Demand theory and consumer surplus
│       │   └── validation.py       # S-12: Economic theory validation framework
│       ├── analytics/               # M-04: Analytics Engine Module
│       │   ├── __init__.py         # Analytics module exports
│       │   ├── dashboard.py        # S-13: Interactive statistical dashboards
│       │   ├── metrics.py          # S-14: Economic metrics and KPI calculation
│       │   ├── export.py           # S-15: Research-grade data export and visualization export
│       │   ├── validation.py       # S-16: Statistical validation of economic theory
│       │   ├── visualization.py    # S-17: Publication-quality plots and charts
│       │   └── reproducibility.py  # S-24: Research reproducibility and metadata management
│       ├── education/               # M-03: Educational Framework Module
│       │   ├── __init__.py         # Educational module exports
│       │   ├── tutorials.py        # S-18: Progressive economic concept tutorials
│       │   ├── explanations.py     # S-19: Dynamic concept explanations and context
│       │   ├── scenarios.py        # S-20: Pre-built educational economic scenarios
│       │   ├── assessment.py       # S-21: Learning effectiveness measurement tools
│       │   └── curriculum.py       # S-22: Curriculum sequencing and progression
│       └── config/                  # Configuration management
│           ├── __init__.py         # Config module exports
│           ├── settings.py         # S-21: Application configuration
│           └── educational.py      # S-22: Educational mode settings
├── tests/
│   ├── unit/                       # Fast, isolated component tests
│   │   ├── test_visual.py         # Visual component unit tests
│   │   ├── test_spatial.py        # Spatial logic unit tests
│   │   ├── test_economics.py      # Economic computation unit tests
│   │   └── test_education.py      # Educational feature unit tests
│   ├── integration/                # Cross-module interaction tests
│   │   ├── test_simulation.py     # End-to-end simulation workflows
│   │   ├── test_educational.py    # Complete educational user journeys
│   │   └── test_performance.py    # Performance integration testing
│   ├── visual_regression/          # Visual consistency testing
│   │   ├── baselines/             # Reference screenshots and animations
│   │   ├── test_configs/          # Visual test configuration files
│   │   └── comparison_tools.py    # Visual diff and analysis tools
│   └── economic_validation/        # Economic theory validation
│       ├── analytical_solutions/  # Reference solutions from literature
│       ├── test_scenarios/        # Standard economic test cases
│       └── validation_framework.py # Theory validation automation
├── docs/
│   ├── README.md                   # S-23: Getting started guide
│   ├── DEVELOPMENT.md             # Development workflows and setup
│   ├── EDUCATIONAL_GUIDE.md       # Teaching with the platform
│   ├── ECONOMIC_THEORY.md         # Economic foundations and validation
│   └── API_REFERENCE.md           # Complete API documentation
├── config/
│   ├── development.yaml           # Development environment settings
│   ├── educational.yaml           # Educational mode configuration
│   ├── performance.yaml           # Performance testing parameters
│   └── visual_testing.yaml        # Visual regression test settings
├── scripts/
│   ├── setup_dev_environment.py   # Development setup automation
│   ├── run_visual_tests.py        # Visual regression test runner
│   ├── generate_scenarios.py      # Educational scenario generator
│   ├── validate_economics.py      # Economic theory validation runner
│   └── build_documentation.py     # Documentation generation
├── examples/
│   ├── basic_simulation/          # Simple grid world example
│   ├── market_clearing/           # Market equilibrium demonstration
│   ├── spatial_economics/         # Deadweight loss visualization
│   └── educational_tutorial/      # Complete learning module example
├── assets/                        # Static resources
│   ├── fonts/                     # Educational typography
│   ├── icons/                     # UI elements and symbols
│   └── templates/                 # Visualization templates
└── .github/                       # CI/CD automation (if using GitHub)
    └── workflows/
        ├── tests.yml              # W-01: Comprehensive test automation
        ├── visual_validation.yml  # W-02: Visual regression testing
        └── educational_qa.yml     # W-03: Educational content validation
```

### 12. Tooling & Quality Setup

**Development Toolchain** (D-01: Educational-focused development environment):

| Tool | Purpose | Educational Rationale | Quality Gate |
|------|---------|----------------------|--------------|
| **Black** | Code formatting | Clear, readable code for educational use | Q-01: Pre-commit autoformat |
| **Ruff** | Linting | Fast, comprehensive error detection | Q-02: Zero lint errors allowed |
| **mypy** | Type checking | Reliable educational software | Q-03: 100% type coverage |
| **pytest** | Test runner | Comprehensive testing with visual extensions | Q-04: 90% test coverage minimum |
| **pytest-visual** | Visual testing | Automated educational content validation | Q-05: All visual components tested |

**Educational Tools**:
- **jupyter**: Interactive development and educational content creation
- **matplotlib**: Publication-quality educational diagrams
- **pillow**: Visual regression testing and image processing
- **imageio**: Animation export for educational presentations

**Build and Task Management** (D-02: Simple educational deployment):
```makefile
# Makefile stub layout
.PHONY: install test visual-test dev clean docs

install:
	# Install all dependencies for educational use
	@echo "Installing EconSim educational platform..."

test:
	# Run comprehensive test suite
	@echo "Running all tests including visual validation..."

visual-test:
	# Run visual regression tests
	@echo "Validating visual educational components..."

dev:
	# Start development environment with hot reload
	@echo "Starting visual development environment..."

clean:
	# Clean build artifacts
	@echo "Cleaning development environment..."

docs:
	# Generate educational documentation
	@echo "Building educational documentation..."
```

**pyproject.toml Structure Plan**:
```toml
[project]
name = "econsim-platform"
description = "Educational agent-based economic simulation with visualization-first development"
requires-python = ">=3.11"
dependencies = [
    "pygame>=2.5.0",    # Real-time educational visualization
    "numpy>=1.24.0",    # Efficient economic computation
    "scipy>=1.10.0",    # Optimization for equilibrium solving
    "matplotlib>=3.7.0" # Educational plotting and analysis
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",     # Testing framework
    "black>=23.0.0",     # Code formatting
    "ruff>=0.0.280",     # Fast linting
    "mypy>=1.5.0"        # Type checking
]
educational = [
    "jupyter>=1.0.0",    # Interactive educational content
    "pillow>=10.0.0",    # Visual testing support
    "imageio>=2.31.0"    # Animation export
]

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
select = ["E", "F", "W", "C90", "I", "N", "UP", "ANN", "B", "A", "COM", "C4", "DTZ", "T10", "EM", "EXE", "ISC", "ICN", "G", "INP", "PIE", "T20", "PYI", "PT", "Q", "RSE", "RET", "SLF", "SIM", "TID", "TCH", "ARG", "PTH", "PD", "PGH", "PL", "TRY", "NPY", "RUF"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
```

### 13. CI/CD Pipeline Sketch

**W-01**: Comprehensive Testing Pipeline
```yaml
name: Educational Platform Tests
on: [push, pull_request]
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: [3.11, 3.12]
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: pip install -e .[dev,educational]
      - name: Run linting
        run: ruff check src/ tests/
      - name: Run type checking
        run: mypy src/
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=src/
      - name: Run integration tests
        run: pytest tests/integration/ -v
```

**W-02**: Visual Regression Testing
```yaml
name: Visual Educational Validation
on: [push, pull_request]
jobs:
  visual-tests:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python and dependencies
        # ... setup steps
      - name: Run visual regression tests
        run: python scripts/run_visual_tests.py --generate-baselines
      - name: Upload visual test results
        uses: actions/upload-artifact@v3
        with:
          name: visual-test-results-${{ matrix.os }}
          path: tests/visual_regression/results/
      - name: Compare cross-platform consistency
        run: python scripts/compare_platform_visuals.py
```

**W-03**: Educational Content Validation
```yaml
name: Educational Quality Assurance
on: [push, pull_request]
jobs:
  educational-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate economic theory
        run: python scripts/validate_economics.py --all-scenarios
      - name: Test educational scenarios
        run: pytest tests/educational/ --educational-metrics
      - name: Generate educational coverage report
        run: python scripts/educational_coverage.py
      - name: Validate accessibility
        run: python scripts/check_educational_accessibility.py
```

### 14. Implementation Roadmap (MVP focus)

**MVP Milestone 1: Spatial Foundation** (Week 1-2)
- **MVP Components**: S-03, S-04, S-06, S-02 - NxN grid, spatial agents, visualization, application entry
- **Success Criteria**: Grid renders with agents at 30+ FPS, agents move smoothly with spatial constraints
- **Educational Validation**: Manual verification that spatial agent movement is clear and intuitive
- **Risk Mitigation**: Focus on rock-solid spatial foundation that scales to complex economic behavior

**MVP Milestone 2: Preference-Choice-Utility Foundation** (Week 3-4)
- **MVP Components**: S-08, S-09, S-10, S-05 - Preference relations, choice functions, utility optimization, spatial choice visualization
- **Success Criteria**: Agent demonstrates rational spatial choice based on preferences, utility maximization visible on grid
- **Educational Validation**: Students can observe and understand preference-driven spatial behavior
- **Risk Mitigation**: Validate against consumer theory fundamentals, ensure theoretical accuracy

**MVP Milestone 3: Educational Interface and Analytics** (Week 5-6)
- **MVP Components**: S-18, S-19, S-13, S-14 - Tutorials, explanations, statistical dashboard, economic metrics
- **Success Criteria**: Students complete preference-choice tutorial, parameter changes show immediate spatial effects with statistical feedback
- **Educational Validation**: User testing shows improved understanding of consumer choice fundamentals
- **Risk Mitigation**: A/B testing of spatial vs traditional teaching approaches

**Post-MVP Phase 1: Consumer Theory Extension** (Week 7-10)
- **Post-MVP Components**: S-11, S-15, S-17 - Demand theory, export capabilities, advanced visualizations
- **Success Criteria**: Full consumer theory curriculum with demand curves, consumer surplus, comparative statics
- **Educational Validation**: Advanced consumer theory concepts accessible through spatial demonstration
- **Extensions**: Multi-good choices, budget constraints, income effects, substitution effects

**Post-MVP Phase 2: Multi-Agent and Market Theory** (Week 11-16)
- **Post-MVP Components**: S-20, S-21, S-22 - Multi-agent scenarios, assessment tools, curriculum sequencing
- **Success Criteria**: Multiple agents interacting spatially, early market formation, equilibrium concepts
- **Educational Validation**: Progression from individual choice to market interactions maintains clarity
- **Extensions**: Simple trading, price formation, welfare analysis, market efficiency

**Post-MVP Phase 3: Advanced Theory Integration** (Week 17+)  
- **Deferred Components**: Game theory, information economics, mechanism design, behavioral economics
- **Success Criteria**: Full microeconomic theory curriculum with spatial intuition maintained throughout
- **Educational Validation**: Platform adopted by economics educators for comprehensive theory instruction
- **Extensions**: Research-grade simulations, publication-quality analysis, community content creation

**Deferred Features**:
- Web-based deployment (maintain desktop focus initially)
- 3D visualization options (2D sufficient for core concepts)
- Multi-threaded performance optimization (educational scale sufficient)
- Advanced econometric analysis (focus on core microeconomic theory)
- Real-time collaborative features (single-user educational tool initially)

### 15. Decision Log & Next Steps

#### D-01: Visualization Technology Choice
- **Context & Forces**: Need cross-platform, high-performance educational visualization with Python integration
- **Options**: (1) Pygame + Python, (2) Web technologies (Three.js, Canvas), (3) Native GUI (tkinter, PyQt)
- **Criteria**: Educational deployment ease, performance, cross-platform consistency, development velocity
- **Decision**: Pygame + Python for desktop-first educational platform
- **Rationale**: Best balance of performance, educational accessibility, and Python ecosystem integration
- **Consequences**: (+) Excellent performance and educational control, (-) Desktop-only deployment initially
- **Revisit Conditions**: If web deployment becomes critical or performance insufficient
- **Review Date**: After MVP completion and educator feedback

#### D-02: Economic Theory Validation Strategy  
- **Context & Forces**: Must ensure mathematical correctness for educational integrity while maintaining development velocity
- **Options**: (1) Manual expert review, (2) Automated testing against analytical solutions, (3) Academic collaboration
- **Criteria**: Correctness guarantee, scalability, development integration, credibility with educators
- **Decision**: Automated validation against established economic solutions + expert review for new features
- **Rationale**: Scalable correctness validation with expert oversight for novel implementations
- **Consequences**: (+) High confidence in educational accuracy, (-) Requires building validation framework
- **Revisit Conditions**: If validation framework becomes maintenance burden or expert review unavailable
- **Review Date**: After economic engine implementation

#### D-03: Educational Content Development Approach
- **Context & Forces**: Balance between comprehensive economic coverage and development resources
- **Options**: (1) Build comprehensive content library, (2) Minimal examples with extension points, (3) Community-driven content
- **Criteria**: Educational completeness, development time, maintainability, community adoption potential
- **Decision**: Minimal high-quality examples with clear extension framework for educator customization
- **Rationale**: Enables rapid MVP delivery while supporting diverse educational needs
- **Consequences**: (+) Faster time to market, educator flexibility, (-) Initial content limited
- **Revisit Conditions**: If educators need more comprehensive out-of-box content
- **Review Date**: After initial educator testing

#### ❗Needs-Decision[D-04]: Performance vs. Educational Fidelity Trade-offs
- **Context**: May need to balance visual complexity with performance for different educational contexts
- **Options**: (1) Fixed performance profile, (2) Adaptive complexity, (3) Multiple performance modes
- **Required Decision**: How to handle performance degradation while maintaining educational value
- **Timeline**: Before performance optimization phase

#### ❗Needs-Decision[D-05]: Assessment and Learning Analytics Strategy
- **Context**: Educational effectiveness measurement approaches vary significantly
- **Options**: (1) Built-in assessment tools, (2) External analytics integration, (3) Simple interaction logging
- **Required Decision**: Level of learning analytics integration for educational validation
- **Timeline**: Before educational interface implementation

**Extended Skeleton Artifacts**:

**Scaffold Generation Checklist**:
1. [ ] S-01: Initialize Python package structure with proper `__init__.py` files
2. [ ] S-02: Create main application entry point with GUI and command-line interface
3. [ ] S-03: Implement NxN grid world with spatial indexing for performance
4. [ ] S-04: Build spatial agents with movement and constraint systems
5. [ ] S-05: Create spatial choice modeling and optimization visualization
6. [ ] S-06: Develop spatial rendering engine with Pygame and animation support
7. [ ] S-07: Implement movement costs, barriers, and spatial constraints
8. [ ] S-08: Build preference relations and ordering systems
9. [ ] S-09: Create rational choice functions and revealed preference framework
10. [ ] S-10: Implement utility functions and constrained optimization
11. [ ] S-11: Build demand theory and consumer surplus analysis
12. [ ] S-12: Create economic theory validation and testing framework
13. [ ] S-13: Develop interactive statistical dashboards with real-time updates
14. [ ] S-14: Build economic metrics and KPI calculation systems
15. [ ] S-15: Implement data export and visualization export capabilities
16. [ ] S-16: Create statistical validation of economic theory predictions
17. [ ] S-17: Build publication-quality plots and charts generation
18. [ ] S-18: Develop progressive economic concept tutorials
19. [ ] S-19: Create dynamic concept explanations with contextual help
20. [ ] S-20: Build pre-configured educational economic scenarios
21. [ ] S-21: Implement learning effectiveness measurement and assessment tools
22. [ ] S-22: Create curriculum sequencing and progression management
23. [ ] S-23: Write comprehensive getting started and educator guides
24. [ ] S-24: Implement research reproducibility and metadata management system

**README Seed Outline**:
```markdown
# EconSim Platform: Visual Economic Simulation for Education

## Quick Start
<!-- Reference to S-02, S-23 -->

## Educational Philosophy  
<!-- Reference to educational approach, Section 1 -->

## Installation
<!-- Reference to development setup, S-01 -->

## Basic Usage
<!-- Reference to tutorials, S-16 -->

## Economic Concepts Covered
<!-- Reference to scenarios, S-18 -->

## For Educators
<!-- Reference to educational guide -->

## For Developers
<!-- Reference to development documentation -->

## Contributing
<!-- Reference to development workflows -->
```

**.gitignore Essentials**:
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/

# Educational artifacts
*.egg-info/
dist/
build/

# Visual testing
tests/visual_regression/results/
tests/visual_regression/temp/
*.png
*.gif
*.mp4

# Development
.pytest_cache/
.coverage
.mypy_cache/
.ruff_cache/

# Platform-specific
.DS_Store
Thumbs.db

# Educational content
examples/output/
scenarios/generated/
educational_data/
```

**Quality Gates Summary**:

| Q-ID | Name | Stage | Tool | Blocking? | Signal | Auto-fix |
|------|------|-------|------|-----------|--------|----------|
| Q-01 | Code Format | pre-commit | Black | Yes | Non-standard format | black --fix |
| Q-02 | Lint Clean | pre-commit | Ruff | Yes | Lint errors | ruff --fix |
| Q-03 | Type Safety | CI | mypy | Yes | Type errors | Manual fix required |
| Q-04 | Test Coverage | CI | pytest | Yes | <90% coverage | Write additional tests |
| Q-05 | Visual Consistency | CI | pytest-visual | Yes | Visual regression | Manual review required |
| Q-06 | Economic Accuracy | CI | validation framework | Yes | Theory mismatch | Expert review required |
| Q-07 | Educational Effectiveness | Release | User testing | No | Low comprehension | Content revision |

**Next Immediate Steps**:
1. **Environment Setup**: Execute scaffold generation checklist items S-01 through S-06
2. **Visual Foundation**: Implement core rendering system with basic educational examples
3. **Economic Validation**: Build validation framework against known economic solutions
4. **Educational Testing**: Begin user testing protocols with simple economic scenarios
5. **Performance Baseline**: Establish and document educational performance targets

---

## Patch Notes

**Added IDs**:
- R-01 through R-11: Requirements and risks with educational focus
- S-01 through S-23: Scaffold components prioritizing visual-first development
- M-01 through M-04: Core modules organized around educational effectiveness
- F-01 through F-05: Interfaces designed for educational use and validation
- E-01 through E-04: Domain entities with visualization integration
- T-01 through T-05: Testing strategy emphasizing visual and educational validation
- W-01 through W-03: CI/CD workflows for educational platform quality
- Q-01 through Q-07: Quality gates ensuring educational effectiveness
- A-01 through A-05: Assumptions with educational validation experiments
- D-01 through D-05: Decisions prioritizing educational value and correctness

**Rationale**: Comprehensive project skeleton following scaffold planning methodology, emphasizing visualization-first development for economic education while maintaining research-grade mathematical rigor.