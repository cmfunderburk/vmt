# Copilot Instructions for VMT (EconSim Platform)

## Repository Overview

**VMT** is an educational **Economic Simulation Platform** (EconSim) designed to teach microeconomic theory through spatial agent-based visualizations. This is a **Desktop GUI Application** built with PyQt6 that uses visualization-first development to help students understand abstract economic concepts through concrete spatial interactions.

### Key Repository Information
- **Project Type**: Desktop GUI Application with Educational Focus
- **Primary Language**: Python 3.11+
- **GUI Framework**: PyQt6 with embedded Pygame visualization
- **Architecture**: Self-contained desktop app with agent-based economic simulation on spatial NxN grid
- **Repository Status**: **Planning Complete - Ready for Week 0 Validation Implementation**
- **Current Phase**: Gate 1 Technical Validation (PyQt6 + Pygame integration)
- **Target Platforms**: macOS/Linux initially (Windows expandable later)
- **Distribution Model**: Self-contained executable files for easy educational deployment

### Educational Mission
The platform addresses the common student criticism of "people don't behave like that" by demonstrating multiple preference types (Cobb-Douglas, Perfect Substitutes, Leontief) through spatial agent behavior, showing that economic theory provides a flexible framework rather than rigid assumptions.

## Build and Development Instructions

### Prerequisites
- **Python 3.11+** (required)
- **pip** for package management
- **Make** for task automation

### Environment Setup
**Current Status: Ready for Week 0 Validation Implementation**

**Immediate Setup for Week 0 Validation:**
```bash
# Create virtual environment for validation work
python3 -m venv vmt-dev
source vmt-dev/bin/activate  # On Windows: vmt-dev\Scripts\activate

# Install core dependencies for Week 0 validation
pip install PyQt6>=6.5.0 pygame>=2.5.0 numpy>=1.24.0
pip install pytest>=7.4.0 black>=23.0.0 ruff>=0.0.280

# Follow detailed setup: orientation_docs/Week0/Week 0 Development Setup.md
```

**Full Project Setup (Post-Validation):**
```bash
# When project structure is created from specifications
make install  # Uses project_structure_specification.md
pip install -e .[dev,educational]  # When pyproject.toml is implemented
```

### Core Dependencies
- **PyQt6**: Professional desktop GUI framework with OpenGL integration
- **pygame>=2.5.0**: Real-time visualization engine (embedded in PyQt6 widgets)
- **numpy>=1.24.0**: Efficient economic computation  
- **scipy>=1.10.0**: Optimization for equilibrium solving

### Desktop Application Dependencies
- **PyInstaller 6.0+**: Cross-platform application packaging for self-contained distribution
- **Pillow**: Image processing for icons, splash screens, and visual assets

### Development Dependencies
- **pytest>=7.4.0**: Testing framework with GUI and visual testing extensions
- **black>=23.0.0**: Code formatting for educational code clarity
- **ruff>=0.0.280**: Fast, comprehensive linting
- **mypy>=1.5.0**: Type checking for desktop application reliability

### Build Commands

**Week 0 Validation Commands:**
```bash
# Run Week 0 validation tests
python validation_workspace/gate1_technical/test_pyqt6_basic.py
python validation_workspace/gate1_technical/test_pygame_integration.py

# Validate development setup
python -c "import PyQt6, pygame, numpy; print('Week 0 dependencies ready')"
```

**Future Build Commands (Post-Structure Creation):**
```bash
# Create project structure from specifications
python scripts/create_project_structure.py  # Uses project_structure_specification.md

# Full development workflow (when implemented)
make install      # Install all dependencies
make test         # Run comprehensive test suite
make dev          # Start development environment
make clean        # Clean build artifacts
make docs         # Generate documentation
```

**Current State**: Project structure specifications ready for implementation. Use orientation_docs/ planning documents to guide development.

### Testing Strategy

**When implemented, run tests in this specific order:**

1. **Linting** (must pass before proceeding):
   ```bash
   ruff check src/ tests/
   ```

2. **Type checking** (must pass before proceeding):
   ```bash
   mypy src/
   ```

3. **Unit tests** (fast, isolated):
   ```bash
   pytest tests/unit/ -v --cov=src/
   ```

4. **Integration tests** (cross-module):
   ```bash
   pytest tests/integration/ -v
   ```

5. **Visual regression tests** (platform-specific):
   ```bash
   python scripts/run_visual_tests.py --generate-baselines
   ```

6. **Educational validation tests** (theory accuracy):
   ```bash
   pytest tests/educational/ --educational-metrics
   ```

**Current State**: No source code or tests exist yet - these are the planned testing approaches.

### Quality Gates (All Must Pass)
- **Q-01**: Code formatting via Black (auto-fix: `black --fix`)
- **Q-02**: Zero lint errors via Ruff (auto-fix: `ruff --fix`)  
- **Q-03**: 100% type coverage via mypy (manual fix required)
- **Q-04**: 90% test coverage minimum via pytest
- **Q-05**: Visual consistency via pytest-visual (manual review)
- **Q-06**: Economic theory accuracy (expert review required)

### Performance Requirements
- **Educational threshold**: ≥10 FPS for smooth interaction
- **Response time**: ≤100ms for parameter adjustments
- **Agent scale**: 50+ agents for educational scenarios
- **Research scale**: 1000+ agents for advanced simulations

## Project Layout and Architecture

### **Current Repository Status: Complete Planning + Ready for Implementation**

**Planning Documents** (`orientation_docs/`)
- `README.md` - Complete documentation index and navigation
- `current_assessment.md` - 99% project readiness assessment  
- `Implementation Roadmap.md` - Phase-based development plan with supporting specifications
- `project_structure_specification.md` - **Complete directory hierarchy ready for creation**
- `validation_to_production_transition_plan.md` - Systematic prototype→production evolution
- `educational_scenarios_specification.md` - Concrete tutorial scenarios with JSON parameters
- `development_workflow_guide.md` - Git branching, CI/CD pipeline, quality gates
- `implementation_phase_gates.md` - Rigorous implementation progression system

**Week 0 Validation** (`orientation_docs/Week0/`)
- `Week 0 Development Setup.md` - **Start here for environment setup**
- `Week 0 Economic Theory Validation.md` - Mathematical validation with spatial collection framework  
- `Week 0 GUI Approach.md` - PyQt6 + Pygame integration approach
- `Week 0 Success Metrics.md` - Measurable validation criteria

**Validation Workspace** (Ready to Create)
- `validation_workspace/gate1_technical/` - PyQt6 + Pygame integration prototypes
- `validation_workspace/gate2_economic_theory/` - Economic implementation validation
- `validation_workspace/gate3_spatial_integration/` - Spatial choice behavior validation  
- `validation_workspace/gate4_educational_interface/` - Educational workflow validation

### Core Architecture Modules (Specified, Ready to Implement)

**`src/econsim/`** - Main application package (structure defined)
- `gui/` - PyQt6 interface components with embedded Pygame widgets
- `spatial/` - Grid-based simulation foundation with agent behavior  
- `theory/` - Economic preference implementations (Cobb-Douglas, Perfect Substitutes, Leontief)
- `education/` - Tutorial system and learning assessment framework
- `analytics/` - Data analysis and research-grade export capabilities
- `utils/` - Configuration, logging, validation utilities

**`tests/`** - Comprehensive test organization (structure defined)
- `unit/` - Fast, isolated component tests with 90%+ coverage target
- `integration/` - Cross-module interaction tests
- `visual_regression/` - Cross-platform visual consistency validation  
- `educational_validation/` - Economic theory accuracy and pedagogical effectiveness

**Supporting Infrastructure** (Specifications Ready)
- `config/` - Environment-specific configuration files
- `scripts/` - Build automation and development tools
- `resources/` - Icons, images, fonts, example scenarios
- `docs/` - User guides, API documentation, educational materials

### Testing Structure (Planned Architecture)
```
tests/                      # Not yet implemented
├── unit/                    # Fast, isolated component tests
├── integration/             # Cross-module interaction tests
├── visual_regression/       # Visual consistency testing
└── economic_validation/     # Economic theory validation
```

### Documentation Structure (Current and Planned)
```
# Current comprehensive planning documents:
initial_planning.md         # Complete project specification (50k+ words)
planning.prompt.md          # Project planning framework and templates  
Current_Assessment.md       # Project readiness assessment
Theory_Progression_Considerations.md  # Economic theory decisions

# Planned documentation structure:
docs/                       # Not yet implemented
├── README.md               # Getting started guide
├── DEVELOPMENT.md          # Development workflows and setup
├── EDUCATIONAL_GUIDE.md    # Teaching with the platform
└── ECONOMIC_THEORY.md      # Economic foundations and validation
```

## CI/CD and Validation Pipeline

### GitHub Actions Workflows (.github/workflows/)

**W-01: Comprehensive Testing Pipeline** (`tests.yml`)
- Multi-platform testing (Ubuntu, macOS, Windows)
- Python 3.11 and 3.12 support
- Full lint → type → unit → integration test sequence

**W-02: Visual Regression Testing** (`visual_validation.yml`)  
- Cross-platform visual consistency validation
- Baseline generation and comparison
- Educational content visual validation

**W-03: Educational Quality Assurance** (`educational_qa.yml`)
- Economic theory validation against analytical solutions
- Educational scenario effectiveness testing
- Accessibility validation for educational use

### Validation Steps for Changes

**Before committing any code changes:**

1. Run linting and auto-fix issues:
   ```bash
   ruff check src/ tests/ --fix
   black src/ tests/
   ```

2. Verify type safety:
   ```bash
   mypy src/
   ```

3. Run relevant test suites:
   ```bash
   pytest tests/unit/ -v        # For unit changes
   pytest tests/integration/ -v # For integration changes
   ```

4. For visual changes, run visual regression tests:
   ```bash
   python scripts/run_visual_tests.py
   ```

5. For economic model changes, validate theory:
   ```bash
   python scripts/validate_economics.py --all-scenarios
   ```

## Working with Current Repository State

### Current Phase: Planning and Design (September 2025)
The repository is actively in **planning refinement phase** with recent major decisions:

**Recent Updates**:
- ✅ **Interface Decision**: Chose Desktop GUI Application (PyQt6 + embedded Pygame) over library approach
- ✅ **Success Metrics**: Updated to be solo-developer measurable and testable
- ✅ **Week 0 Validation**: Added technology validation phase for PyQt6-Pygame integration
- ✅ **Target Platforms**: Focused on macOS/Linux for initial MVP (Windows later)

### What You Can Do Now
Since the repository is in active planning phase, focus on:

1. **Review recent planning updates** - `initial_planning.md` contains desktop GUI architecture decisions
2. **Understand desktop GUI approach** - `Week 0 GUI Approach.md` has PyQt6 development roadmap  
3. **Address planning gaps** - `Planning Document Review.md` identifies specific improvement areas
4. **Refine educational content** - Help define specific tutorial scenarios for each preference type
5. **Prepare for Week 0** - Assist with technology validation planning and GUI architecture design

### Creating Initial Implementation
When starting implementation:

1. **Create pyproject.toml** first based on specification in `initial_planning.md` lines 518-556
2. **Create Makefile** based on specification in `initial_planning.md` lines 489-516  
3. **Set up project structure** following layout in `initial_planning.md` lines 378-468
4. **Implement build automation** before writing core logic

### Expected Implementation Timeline
According to current planning documents:
- **Week 0**: Technology validation (PyQt6 + Pygame integration, 3 preference types proof-of-concept)
- **Week 1-2**: Spatial foundation (grid, agents, basic PyQt6 GUI with embedded Pygame)
- **Week 3-4**: Flexible preference architecture and parameter controls
- **Week 5-6**: Three core preference types (Cobb-Douglas, Perfect Substitutes, Leontief)
- **Week 7**: Spatial choice integration and comprehensive testing
- **Week 8**: Educational interface, tutorials, and application packaging

### Build Command Timing Expectations
When implemented, expect these timing requirements:
- **Linting** (ruff): <30 seconds for full codebase
- **Type checking** (mypy): <60 seconds for full codebase  
- **Unit tests**: <5 minutes for comprehensive suite
- **Visual regression tests**: <10 minutes across platforms
- **Educational validation**: <15 minutes for all economic scenarios

### Desktop Application Packaging
When ready for distribution:
- **PyInstaller packaging**: 2-5 minutes per platform
- **Application size**: ~50-100MB self-contained executable
- **Startup time**: <3 seconds from click to functional GUI
- **Cross-platform testing**: Manual testing required on macOS/Linux

### When Making Changes to Economic Models
- **Always validate against analytical solutions** using `scripts/validate_economics.py`
- **Test all three preference types** (Cobb-Douglas, Perfect Substitutes, Leontief)
- **Check visual behavior** - different preference types should produce visually distinct agent behaviors
- **Maintain educational clarity** - ensure changes don't overwhelm educational value

### When Adding Educational Content
- **Follow progressive complexity reveal** - start simple, build complexity gradually
- **Test cross-platform visual consistency** - educational content must work on all platforms
- **Validate learning effectiveness** using assessment tools in `education/assessment.py`
- **Ensure accessibility** for diverse educational environments

### When Modifying Spatial/Visual Components
- **Maintain performance thresholds** (≥10 FPS, ≤100ms response)
- **Test with realistic agent counts** (50+ for education, 1000+ for research)
- **Run visual regression tests** to prevent unintended visual changes
- **Verify pygame compatibility** across platforms

### When Working on Desktop GUI Components
- **PyQt6 Layout Management**: Use proper layout managers (QVBoxLayout, QHBoxLayout) for responsive design
- **Signal-Slot Connections**: Connect GUI controls to simulation updates using PyQt6 signal/slot mechanism
- **Threading Considerations**: Keep simulation updates on main thread or use QTimer for smooth integration
- **Resource Management**: Use Qt resource system for icons, images, and UI assets
- **Cross-Platform GUI**: Test layout and appearance on both macOS and Linux

### Performance Considerations
- **Spatial partitioning** is used for efficient agent management
- **Level-of-detail rendering** maintains performance with many agents
- **Educational mode** prioritizes clarity over raw performance
- **Research mode** optimizes for larger-scale simulations

### Common Gotchas and Workarounds

**Pygame Platform Differences:**
- Visual rendering may vary slightly across operating systems
- Always test cross-platform for educational consistency
- Use visual regression baselines for each platform

**Economic Theory Validation:**
- Mathematical optimization can be complex for spatial constraints
- Leontief constraints may require different algorithms than Cobb-Douglas
- Perfect Substitutes corner solutions need special spatial handling

**Educational Content:**
- Students often struggle with "unrealistic" assumptions - emphasize framework flexibility
- Visual complexity can overwhelm - use progressive disclosure
- Parameter adjustment UI becomes complex with three preference types

**Desktop Application Packaging:**
- PyInstaller platform differences can cause runtime issues
- Always test packaged applications on clean systems without Python installed
- File path handling differs between development and packaged environments
- Icon and resource loading requires special attention in packaged apps

## Repository State and Dependencies

### Current Implementation State
This repository is in the **planning and architecture phase**. The comprehensive planning documents (`initial_planning.md`, `planning.prompt.md`, etc.) contain detailed specifications for:

- Complete system architecture and module design
- Detailed build and testing strategies  
- Educational philosophy and user scenarios
- Risk assessment and mitigation strategies

### No External Service Dependencies
- **Zero external services required** - fully self-contained educational tool
- **No network dependencies** for core functionality
- **Minimal dependencies** to reduce educational deployment complexity

### Git Workflow
- Main development branch: Follow standard GitHub workflow
- Always run quality gates before pushing changes
- Use descriptive commit messages focusing on educational impact

**Planned .gitignore (Not Yet Created):**
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

## Trust These Instructions

**These instructions are based on comprehensive analysis of the planning documents and intended system architecture.** Only search beyond these instructions if:

1. You encounter specific build/test failures not covered here
2. The planned architecture differs significantly from actual implementation
3. You need details about specific economic theory implementations
4. You're implementing net-new features not covered in the planning documents

The planning documents contain extensive detail about intended implementation, so refer to `initial_planning.md` for deep architectural guidance and `Current_Assessment.md` for the latest status and strategic decisions.

## Quick Reference for Common Tasks

### Understanding the Economic Theory
- **Three preference types**: Cobb-Douglas (balanced), Perfect Substitutes (interchangeable), Leontief (fixed proportions)
- **Spatial optimization**: Agents move on NxN grid to maximize utility under budget constraints
- **Educational goal**: Show that economic theory is flexible framework, not rigid assumptions

### Key Planning Document Sections
- **Architecture overview**: `initial_planning.md` lines 378-468
- **Build specifications**: `initial_planning.md` lines 470-556  
- **CI/CD workflows**: `initial_planning.md` lines 558-630
- **Quality gates**: `initial_planning.md` lines 848-857
- **Strategic decisions**: `Current_Assessment.md` lines 49-191

### Implementation Priorities
1. **Spatial foundation** before economic theory
2. **Visual feedback** for all parameter changes
3. **Cross-platform consistency** for educational use
4. **Performance optimization** to maintain educational thresholds
