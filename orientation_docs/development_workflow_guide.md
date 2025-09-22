# Development Workflow Guide

## Purpose
Integrate validation and implementation workflows with systematic Git branching strategy, build automation, quality gates, and CI/CD pipeline for desktop application development.

## Development Lifecycle Overview

### **Workflow Philosophy**
**Gate-Based Development**: Each development phase builds on validated achievements with systematic quality gates and clear progression criteria.

**Quality-First Approach**: Maintain professional code standards throughout validation and implementation phases with automated quality enforcement.

**Educational Focus Preservation**: Every workflow decision supports the educational mission while maintaining technical excellence.

## Git Branching Strategy

### **Branch Structure**

```
main                                    # Production-ready releases
├── develop                            # Integration branch for all development
│   ├── validation/                    # Validation phase branches
│   │   ├── validation/gate-1         # Gate 1: Technical validation
│   │   ├── validation/gate-2         # Gate 2: Economic theory validation  
│   │   ├── validation/gate-3         # Gate 3: Spatial integration validation
│   │   └── validation/gate-4         # Gate 4: Educational interface validation
│   │
│   ├── implementation/                # Implementation phase branches  
│   │   ├── implementation/phase-1    # Phase 1: Spatial foundation
│   │   ├── implementation/phase-2    # Phase 2: Flexible preferences
│   │   ├── implementation/phase-3    # Phase 3: Three preference types
│   │   └── implementation/phase-4    # Phase 4: Educational polish
│   │
│   ├── feature/                       # Individual feature development
│   │   ├── feature/cobb-douglas-ui   # Specific feature branches
│   │   ├── feature/spatial-optimization
│   │   └── feature/tutorial-system
│   │
│   └── hotfix/                        # Critical bug fixes
│       └── hotfix/performance-issue
```

### **Branch Lifecycle Management**

#### **Validation Branches**
```bash
# Create validation branch
git checkout develop
git checkout -b validation/gate-1

# Work on validation
# ... validation development ...

# Complete validation (requires all validation criteria met)
git checkout develop  
git merge validation/gate-1 --no-ff
git tag "gate-1-complete"
git branch -d validation/gate-1

# Transition to implementation
git checkout -b implementation/phase-1
```

#### **Implementation Branches**
```bash
# Create implementation branch (requires completed validation gate)
git checkout develop
git checkout -b implementation/phase-1

# Implementation development with quality gates
# ... implementation development ...

# Complete implementation phase (requires all phase criteria met)
git checkout develop
git merge implementation/phase-1 --no-ff  
git tag "phase-1-complete"
git branch -d implementation/phase-1
```

#### **Feature Development**
```bash
# Create feature branch
git checkout develop
git checkout -b feature/spatial-optimization

# Feature development with continuous integration
# ... feature development ...

# Feature completion (requires quality gates passed)
git checkout develop
git merge feature/spatial-optimization --no-ff
git branch -d feature/spatial-optimization
```

### **Branch Protection Rules**

#### **Main Branch Protection**
- **No direct commits** - all changes via pull request
- **Requires review** - at least 1 approval (self-review for solo development)
- **Status checks must pass** - all CI/CD pipeline stages successful
- **Up-to-date requirement** - must be current with develop branch
- **Delete head branches** - automatic cleanup after merge

#### **Develop Branch Protection**  
- **Requires status checks** - automated testing and quality gates
- **Linear history preferred** - rebase and merge strategy
- **Branch deletion after merge** - keep branch structure clean
- **Tag integration points** - mark validation and implementation completions

## Build Automation System

### **Makefile Structure**

```makefile
# VMT EconSim Platform - Development Automation
# Usage: make [target] - see 'make help' for available targets

.PHONY: help install dev test lint format type-check clean build package

# Default target
.DEFAULT_GOAL := help

# Development Environment Setup
install: ## Install all dependencies for development
	python -m pip install --upgrade pip
	pip install -e .[dev,educational,packaging]
	pre-commit install

install-minimal: ## Install minimal dependencies for validation work  
	python -m pip install --upgrade pip
	pip install -e .[validation]

# Development Workflow
dev: ## Start development environment with hot reload
	python src/econsim/main.py --dev-mode --hot-reload

dev-validation: ## Start validation workspace environment
	cd validation_workspace && python -m pytest --validation-mode

# Code Quality Gates  
lint: ## Run comprehensive linting (must pass before commit)
	ruff check src/ tests/ scripts/ --fix
	ruff format src/ tests/ scripts/

type-check: ## Run type checking (must pass before commit)
	mypy src/ --strict
	mypy tests/ --strict --disable-error-code=import

format: ## Apply code formatting (auto-fix)
	black src/ tests/ scripts/
	isort src/ tests/ scripts/

# Testing Workflow
test: ## Run complete test suite
	$(MAKE) test-unit
	$(MAKE) test-integration  
	$(MAKE) test-visual
	$(MAKE) test-educational

test-unit: ## Run fast unit tests only
	pytest tests/unit/ -v --cov=src/ --cov-report=term-missing

test-integration: ## Run integration tests
	pytest tests/integration/ -v --slow

test-visual: ## Run visual regression tests  
	python scripts/run_visual_tests.py --platform=current

test-educational: ## Run educational effectiveness validation
	pytest tests/educational_validation/ -v --educational-metrics

test-performance: ## Run performance benchmarking
	python scripts/performance_benchmark.py --report

# Quality Gates (CI/CD Integration)
quality-gate-validation: ## Validation phase quality gate
	$(MAKE) lint
	$(MAKE) type-check  
	$(MAKE) test-unit
	$(MAKE) test-performance
	python scripts/validate_gate_completion.py --gate=validation

quality-gate-implementation: ## Implementation phase quality gate  
	$(MAKE) lint
	$(MAKE) type-check
	$(MAKE) test
	$(MAKE) test-educational
	python scripts/validate_phase_completion.py --phase=implementation

# Documentation and Analysis
docs: ## Generate complete documentation
	python scripts/build_documentation.py --all
	sphinx-build -b html docs/ docs/_build/

docs-api: ## Generate API documentation only
	sphinx-apidoc -o docs/api/ src/
	sphinx-build -b html docs/ docs/_build/

analyze: ## Run code analysis and metrics
	python scripts/code_analysis.py --complexity --coverage --performance

# Build and Packaging
clean: ## Clean build artifacts and caches
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name __pycache__ -delete

build: ## Build source and wheel distributions
	python -m build --wheel --sdist

package: ## Create desktop application packages  
	$(MAKE) clean
	$(MAKE) quality-gate-implementation
	python scripts/package_application.py --platform=current

package-all: ## Create packages for all supported platforms
	python scripts/package_application.py --platform=all

# Utility Targets
requirements: ## Generate requirements files
	pip-compile pyproject.toml --output-file requirements/base.txt
	pip-compile pyproject.toml --extra=dev --output-file requirements/dev.txt
	pip-compile pyproject.toml --extra=educational --output-file requirements/educational.txt

security: ## Run security analysis
	bandit -r src/
	safety check requirements/base.txt

help: ## Display this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
```

### **Development Scripts**

#### **Environment Setup (`scripts/setup_dev_environment.py`)**
```python
#!/usr/bin/env python3
"""Development environment setup automation."""

import subprocess
import sys
from pathlib import Path

def setup_python_environment():
    """Set up Python virtual environment and dependencies."""
    print("Setting up Python development environment...")
    
    # Create virtual environment if it doesn't exist
    if not Path("venv").exists():
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    
    # Install dependencies
    pip_cmd = "venv/bin/pip" if sys.platform != "win32" else "venv\\Scripts\\pip"
    subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True)
    subprocess.run([pip_cmd, "install", "-e", ".[dev,educational]"], check=True)
    
    # Setup pre-commit hooks
    subprocess.run(["venv/bin/pre-commit", "install"], check=True)
    
    print("✅ Development environment ready!")

def validate_setup():
    """Validate that setup completed successfully."""
    print("Validating development environment...")
    
    # Test imports
    subprocess.run([sys.executable, "-c", "import PyQt6, pygame, numpy"], check=True)
    
    # Test basic functionality
    subprocess.run([sys.executable, "-m", "pytest", "tests/unit/", "-x"], check=True)
    
    print("✅ Environment validation successful!")

if __name__ == "__main__":
    setup_python_environment()
    validate_setup()
```

#### **Quality Gate Validation (`scripts/validate_gate_completion.py`)**
```python
#!/usr/bin/env python3
"""Validate completion of validation gates."""

import argparse
import subprocess
import sys
from pathlib import Path

def validate_gate_1():
    """Validate Gate 1: Technical Integration."""
    print("Validating Gate 1: Technical Integration...")
    
    # Check PyQt6 + Pygame integration
    result = subprocess.run([
        sys.executable, "-c",
        "from src.econsim.gui.visualization_widget import PygameWidget; print('✅ PyQt6+Pygame integration')"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ PyQt6+Pygame integration failed")
        return False
    
    # Check basic GUI functionality
    # Check performance benchmarks
    # ... additional gate-specific validations
    
    print("✅ Gate 1 validation complete")
    return True

def validate_gate_completion(gate_number):
    """Validate specific gate completion."""
    validators = {
        1: validate_gate_1,
        2: validate_gate_2,  
        3: validate_gate_3,
        4: validate_gate_4
    }
    
    if gate_number not in validators:
        print(f"❌ Unknown gate number: {gate_number}")
        return False
    
    return validators[gate_number]()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", type=int, required=True, choices=[1,2,3,4])
    args = parser.parse_args()
    
    success = validate_gate_completion(args.gate)
    sys.exit(0 if success else 1)
```

## CI/CD Pipeline Configuration

### **GitHub Actions Workflow (`.github/workflows/comprehensive-testing.yml`)**
```yaml
name: Comprehensive Testing Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

env:
  PYTHON_VERSION: '3.11'

jobs:
  code-quality:
    runs-on: ubuntu-latest
    name: Code Quality Gates
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev]
    
    - name: Linting and formatting
      run: |
        ruff check src/ tests/ --output-format=github
        ruff format src/ tests/ --check
    
    - name: Type checking  
      run: mypy src/ --strict
    
    - name: Security analysis
      run: |
        bandit -r src/ -f json -o bandit-report.json
        safety check --json --output safety-report.json
    
    - name: Upload security reports
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: |
          bandit-report.json
          safety-report.json

  unit-tests:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ['3.11', '3.12']
    
    name: Unit Tests (${{ matrix.os }}, Python ${{ matrix.python-version }})
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install system dependencies (Linux)
      if: runner.os == 'Linux'
      run: |
        sudo apt-get update
        sudo apt-get install -y xvfb
    
    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev,educational]
    
    - name: Run unit tests with coverage
      run: |
        pytest tests/unit/ -v --cov=src/ --cov-report=xml --cov-report=term-missing
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  integration-tests:
    runs-on: ubuntu-latest
    needs: [code-quality, unit-tests]
    name: Integration Tests
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install dependencies
      run: |
        sudo apt-get update && sudo apt-get install -y xvfb
        python -m pip install --upgrade pip
        pip install -e .[dev,educational]
    
    - name: Run integration tests
      run: |
        xvfb-run -a pytest tests/integration/ -v --slow

  visual-regression:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
    
    needs: [integration-tests]
    name: Visual Regression (${{ matrix.os }})
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4  
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev,educational]
    
    - name: Download baseline images
      uses: actions/download-artifact@v3
      with:
        name: visual-baselines-${{ matrix.os }}
        path: tests/visual_regression/baselines/
    
    - name: Run visual regression tests
      run: |
        python scripts/run_visual_tests.py --platform=${{ matrix.os }} --generate-report
    
    - name: Upload visual test results
      uses: actions/upload-artifact@v3
      with:
        name: visual-results-${{ matrix.os }}
        path: tests/visual_regression/results/

  educational-validation:
    runs-on: ubuntu-latest
    needs: [integration-tests]
    name: Educational Effectiveness Validation
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install dependencies
      run: |
        sudo apt-get update && sudo apt-get install -y xvfb
        python -m pip install --upgrade pip
        pip install -e .[dev,educational]
    
    - name: Run educational validation
      run: |
        xvfb-run -a pytest tests/educational_validation/ -v --educational-metrics
    
    - name: Generate educational report
      run: |
        python scripts/generate_educational_report.py --output=educational-effectiveness-report.html
    
    - name: Upload educational report
      uses: actions/upload-artifact@v3
      with:
        name: educational-effectiveness-report
        path: educational-effectiveness-report.html

  build-and-package:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
    
    needs: [visual-regression, educational-validation]
    name: Build and Package (${{ matrix.os }})
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ env.PYTHON_VERSION }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev,educational,packaging]
    
    - name: Build application package
      run: |
        python scripts/package_application.py --platform=${{ matrix.os }}
    
    - name: Upload application package
      uses: actions/upload-artifact@v3
      with:
        name: application-${{ matrix.os }}
        path: dist/
```

## Quality Gate Integration

### **Pre-Commit Hooks (`.pre-commit-config.yaml`)**
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-added-large-files

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [ --fix, --exit-non-zero-on-fix ]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict]

  - repo: local
    hooks:
      - id: pytest-unit-fast
        name: Fast unit tests
        entry: pytest tests/unit/ -x --ff
        language: system
        pass_filenames: false
        stages: [commit]
```

### **Development Workflow Validation**

#### **Validation Phase Quality Gates**
1. **Code Quality**: Linting, formatting, type checking must pass
2. **Unit Testing**: 90%+ coverage, all tests passing
3. **Performance**: Baseline performance benchmarks met
4. **Gate-Specific Validation**: Custom validation for each gate milestone

#### **Implementation Phase Quality Gates**  
1. **All Validation Gates**: Must pass validation quality gates
2. **Integration Testing**: Cross-module functionality validated
3. **Visual Regression**: No unintended visual changes
4. **Educational Validation**: Pedagogical effectiveness maintained
5. **Documentation**: Complete API documentation and user guides
6. **Packaging**: Successfully builds desktop applications

### **Release Management**

#### **Version Tagging Strategy**
- **Gate Completions**: `gate-1-complete`, `gate-2-complete`, etc.
- **Phase Completions**: `phase-1-complete`, `phase-2-complete`, etc.  
- **Releases**: `v0.1.0-alpha`, `v0.2.0-beta`, `v1.0.0`
- **Hotfixes**: `v1.0.1`, `v1.0.2`

#### **Release Process**
```bash
# Prepare release
git checkout main
git merge develop --no-ff
git tag v1.0.0
make package-all

# Deploy release
git push origin main --tags
# Upload packages to distribution channels
```

This development workflow guide provides comprehensive integration of validation, implementation, quality gates, and automation systems to support systematic development while maintaining the educational focus and technical excellence that characterize this project.