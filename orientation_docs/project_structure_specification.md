# Project Structure Specification - VMT EconSim Platform

## Purpose
Transform Implementation Roadmap architectural specifications into concrete file system layout for systematic development progression.

## Root Project Structure

```
vmt/                                    # Root project directory
├── .github/                           # GitHub workflows and project metadata
│   ├── workflows/                     # CI/CD automation
│   │   ├── tests.yml                 # Comprehensive testing pipeline
│   │   ├── visual_validation.yml     # Cross-platform visual consistency
│   │   └── educational_qa.yml        # Educational content validation
│   └── copilot-instructions.md       # GitHub Copilot guidance (existing)
│
├── src/                              # Source code (production)
│   └── econsim/                      # Main application package
│       ├── __init__.py               # Package initialization, version exports
│       ├── main.py                   # Application entry point, GUI bootstrap
│       │
│       ├── gui/                      # PyQt6 GUI components
│       │   ├── __init__.py
│       │   ├── main_window.py        # Primary application window
│       │   ├── control_panel.py     # Parameter adjustment controls
│       │   ├── visualization_widget.py # Pygame integration widget
│       │   └── dialogs/              # Modal dialogs and settings
│       │       ├── __init__.py
│       │       ├── settings.py       # Application preferences
│       │       └── about.py          # About/help dialog
│       │
│       ├── spatial/                  # Spatial simulation foundation
│       │   ├── __init__.py
│       │   ├── grid.py              # NxN grid world implementation
│       │   ├── agents.py            # Spatial agent behavior and movement
│       │   ├── pathfinding.py       # Route optimization algorithms
│       │   └── visualization.py     # Pygame rendering engine
│       │
│       ├── theory/                   # Economic theory implementation
│       │   ├── __init__.py
│       │   ├── base_preferences.py  # Abstract preference interface
│       │   ├── cobb_douglas.py      # Cobb-Douglas utility functions
│       │   ├── perfect_substitutes.py # Perfect substitutes implementation
│       │   ├── leontief.py          # Leontief (fixed proportions) preferences
│       │   └── optimization.py      # Utility maximization algorithms
│       │
│       ├── education/                # Educational framework
│       │   ├── __init__.py
│       │   ├── tutorials.py         # Progressive tutorial system
│       │   ├── scenarios.py         # Pre-built educational scenarios
│       │   ├── assessment.py        # Learning effectiveness measurement
│       │   └── content/             # Educational content data
│       │       ├── tutorial_scripts.json
│       │       ├── scenario_definitions.json
│       │       └── assessment_questions.json
│       │
│       ├── analytics/                # Data analysis and export
│       │   ├── __init__.py
│       │   ├── metrics.py           # Performance and behavior metrics
│       │   ├── export.py            # Research-grade data export
│       │   └── visualization.py     # Publication-quality charts
│       │
│       └── utils/                    # Shared utilities
│           ├── __init__.py
│           ├── config.py            # Configuration management
│           ├── logging.py           # Application logging
│           └── validation.py        # Input validation and sanitization
│
├── tests/                            # Test suite organization
│   ├── __init__.py
│   ├── conftest.py                  # pytest configuration and fixtures
│   │
│   ├── unit/                        # Fast, isolated component tests
│   │   ├── __init__.py
│   │   ├── test_gui/                # GUI component tests
│   │   │   ├── test_main_window.py
│   │   │   ├── test_control_panel.py
│   │   │   └── test_visualization_widget.py
│   │   ├── test_spatial/            # Spatial system tests
│   │   │   ├── test_grid.py
│   │   │   ├── test_agents.py
│   │   │   └── test_pathfinding.py
│   │   ├── test_theory/             # Economic theory tests
│   │   │   ├── test_base_preferences.py
│   │   │   ├── test_cobb_douglas.py
│   │   │   ├── test_perfect_substitutes.py
│   │   │   └── test_leontief.py
│   │   ├── test_education/          # Educational framework tests
│   │   │   ├── test_tutorials.py
│   │   │   ├── test_scenarios.py
│   │   │   └── test_assessment.py
│   │   └── test_utils/              # Utility function tests
│   │       ├── test_config.py
│   │       └── test_validation.py
│   │
│   ├── integration/                 # Cross-module interaction tests
│   │   ├── __init__.py
│   │   ├── test_gui_spatial_integration.py
│   │   ├── test_theory_spatial_integration.py
│   │   └── test_education_workflow.py
│   │
│   ├── visual_regression/           # Visual consistency testing
│   │   ├── __init__.py
│   │   ├── baselines/               # Reference images by platform
│   │   │   ├── linux/
│   │   │   ├── macos/
│   │   │   └── windows/
│   │   ├── test_spatial_visualization.py
│   │   ├── test_gui_rendering.py
│   │   └── utils.py                 # Visual comparison utilities
│   │
│   └── educational_validation/      # Economic theory validation
│       ├── __init__.py
│       ├── test_spatial_collection.py    # Collection behavior validation
│       ├── test_route_optimization.py    # Pathfinding with preferences
│       ├── test_visual_patterns.py       # Visual distinction validation
│       ├── test_analytical_solutions.py  # Mathematical accuracy
│       └── test_pedagogical_effectiveness.py
│
├── docs/                            # Documentation
│   ├── README.md                    # Project overview and getting started
│   ├── DEVELOPMENT.md               # Development setup and workflows
│   ├── EDUCATIONAL_GUIDE.md         # Teaching with the platform
│   ├── ECONOMIC_THEORY.md           # Economic foundations and validation
│   ├── API_REFERENCE.md             # Code documentation
│   └── assets/                      # Documentation images and diagrams
│       ├── screenshots/
│       ├── diagrams/
│       └── educational_examples/
│
├── config/                          # Configuration files
│   ├── development.yaml             # Development environment settings
│   ├── educational.yaml             # Educational mode configuration
│   ├── performance.yaml             # Performance testing parameters
│   └── logging.yaml                 # Logging configuration
│
├── scripts/                         # Build and automation scripts
│   ├── setup_dev_environment.py     # Development environment setup
│   ├── validate_economics.py        # Economic theory validation runner
│   ├── run_visual_tests.py          # Visual regression testing
│   ├── build_documentation.py       # Documentation generation
│   └── package_application.py       # PyInstaller packaging automation
│
├── resources/                       # Application resources
│   ├── icons/                       # Application and UI icons
│   │   ├── app_icon.png
│   │   ├── toolbar/
│   │   └── preferences/
│   ├── images/                      # Educational images and graphics
│   ├── fonts/                       # Custom fonts for GUI
│   └── examples/                    # Example scenarios and demonstrations
│       ├── basic_scenarios/
│       ├── advanced_scenarios/
│       └── research_examples/
│
├── validation_workspace/            # Gate 1-4 validation artifacts
│   ├── gate1_technical/             # PyQt6 + Pygame integration prototypes
│   ├── gate2_economic_theory/       # Economic implementation validation
│   ├── gate3_spatial_integration/   # Spatial choice behavior validation
│   └── gate4_educational_interface/ # Educational workflow validation
│
├── build/                           # Build artifacts (gitignored)
├── dist/                            # Distribution packages (gitignored)
│
├── pyproject.toml                   # Python project configuration
├── Makefile                         # Primary build automation
├── .gitignore                       # Git ignore rules
├── .pre-commit-config.yaml          # Pre-commit hooks configuration
└── README.md                        # Root project documentation
```

## Module Organization Principles

### **Source Code Organization (`src/econsim/`)**

#### **GUI Package (`gui/`)**
- **Purpose**: PyQt6 interface components with clean separation of concerns
- **Dependencies**: PyQt6, embedded Pygame widgets
- **Interface Pattern**: Model-View-Controller with signal/slot communication
- **Testing**: Mock-based unit tests + visual regression validation

#### **Spatial Package (`spatial/`)**
- **Purpose**: Grid-based simulation foundation with agent behavior
- **Dependencies**: NumPy for efficient computation, Pygame for visualization
- **Interface Pattern**: Entity-Component-System for agent management
- **Testing**: Mathematical validation + performance benchmarking

#### **Theory Package (`theory/`)**
- **Purpose**: Economic preference implementations with spatial optimization
- **Dependencies**: SciPy for optimization, NumPy for mathematical operations
- **Interface Pattern**: Abstract base classes with concrete implementations
- **Testing**: Analytical solution validation + comparative static tests

#### **Education Package (`education/`)**
- **Purpose**: Tutorial system and learning assessment framework
- **Dependencies**: JSON for content, integration with spatial and theory packages
- **Interface Pattern**: Progressive disclosure with measurable outcomes
- **Testing**: Educational effectiveness metrics + content validation

### **Test Organization Principles**

#### **Unit Tests (`tests/unit/`)**
- **Scope**: Individual class and function testing in isolation
- **Speed**: <5 minutes for full suite execution
- **Coverage**: 90%+ code coverage requirement
- **Mocking**: External dependencies mocked for isolation

#### **Integration Tests (`tests/integration/`)**
- **Scope**: Cross-module interaction and workflow validation
- **Speed**: <10 minutes for comprehensive integration validation
- **Focus**: GUI-spatial integration, theory-spatial integration, educational workflows
- **Data**: Realistic test scenarios with known expected outcomes

#### **Visual Regression (`tests/visual_regression/`)**
- **Scope**: Cross-platform visual consistency validation
- **Storage**: Platform-specific baseline images for comparison
- **Automation**: Automated baseline generation and comparison
- **Tolerance**: Configurable pixel-difference thresholds

#### **Educational Validation (`tests/educational_validation/`)**
- **Scope**: Economic theory accuracy and pedagogical effectiveness
- **Methods**: Analytical solution comparison + spatial collection behavior validation
- **Metrics**: Route optimization accuracy, visual pattern distinction, learning outcomes
- **Standards**: Academic-grade mathematical validation

## Development Workflow Integration

### **Validation Workspace (`validation_workspace/`)**
- **Gate 1**: Technical integration prototypes and experiments
- **Gate 2**: Economic theory implementation and mathematical validation
- **Gate 3**: Spatial integration and collection behavior validation
- **Gate 4**: Educational interface and tutorial workflow validation

**Transition Process**: Validated artifacts graduate from `validation_workspace/` to `src/` through systematic refactoring and quality enhancement.

### **Configuration Management (`config/`)**
- **Environment-Specific**: Development vs educational vs performance configurations
- **Hot Reload**: Configuration changes without application restart
- **Validation**: Schema-based configuration validation
- **Documentation**: Inline documentation for all configuration options

### **Build Automation (`scripts/` + `Makefile`)**
- **Development Setup**: One-command environment preparation
- **Quality Gates**: Automated linting, type checking, testing
- **Documentation**: Automated API documentation generation
- **Packaging**: Cross-platform desktop application packaging

## Quality and Maintenance Standards

### **Code Quality Requirements**
- **Formatting**: Black code formatter with consistent style
- **Linting**: Ruff linter with comprehensive rule set
- **Type Safety**: MyPy with 100% type coverage requirement
- **Documentation**: Docstrings for all public interfaces

### **Testing Requirements**
- **Unit Coverage**: 90%+ code coverage for all modules
- **Integration**: End-to-end workflow validation
- **Performance**: Benchmarking for spatial simulation performance
- **Visual**: Cross-platform visual consistency validation

### **Educational Standards**
- **Theory Accuracy**: Mathematical validation against analytical solutions
- **Pedagogical Effectiveness**: Measurable learning outcome assessment
- **Accessibility**: Support for diverse educational environments
- **Content Quality**: Progressive complexity with clear learning objectives

This project structure provides the concrete foundation for systematic development while maintaining the quality standards and educational focus that characterize this project's planning excellence.

## Next Steps for Implementation

1. **Create Root Structure**: Establish directory hierarchy with proper `.gitignore`
2. **Initialize Package**: Create `__init__.py` files with proper exports
3. **Configuration Setup**: Implement `pyproject.toml` and `Makefile` based on specifications
4. **Quality Infrastructure**: Set up pre-commit hooks and testing framework
5. **Begin Gate 1 Validation**: Start PyQt6 + Pygame integration validation with proper structure

This structure specification transforms your Implementation Roadmap into actionable development organization, ready for immediate use in validation and production development.