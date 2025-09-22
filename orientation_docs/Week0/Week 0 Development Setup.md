# Week 0 Development Setup Guide

## Purpose
Detailed environment setup and first code execution guide for PyQt6 + Pygame validation.

## Prerequisites Validation

### Python Environment
```bash
# Verify Python 3.11+ installation
python3 --version
# Should show: Python 3.11.x or higher

# Check pip availability
pip3 --version
```

### System Dependencies (Linux)
```bash
# Install Qt6 system libraries
sudo apt update
sudo apt install qt6-base-dev python3-dev python3-pip python3-venv

# Install additional multimedia libraries for Pygame
sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
```

## Step-by-Step Environment Setup

### 1. Virtual Environment Creation
```bash
# Create dedicated environment for VMT project
python3 -m venv vmt-dev
source vmt-dev/bin/activate

# Verify environment activation
which python
# Should show: /path/to/vmt-dev/bin/python
```

### 2. Core Dependencies Installation
```bash
# Install PyQt6 (GUI framework)
pip install PyQt6>=6.5.0

# Install Pygame (embedded visualization)
pip install pygame>=2.5.0

# Install numpy for economic calculations
pip install numpy>=1.24.0

# Verify installations
python -c "import PyQt6; print('PyQt6:', PyQt6.QtCore.qVersion())"
python -c "import pygame; print('Pygame:', pygame.version.ver)"
python -c "import numpy; print('NumPy:', numpy.__version__)"
```

### 3. Development Tools
```bash
# Code quality tools
pip install black>=23.0.0 ruff>=0.0.280 mypy>=1.5.0

# Testing framework
pip install pytest>=7.4.0

# Optional: Jupyter for experimentation
pip install jupyter>=1.0.0
```

## Week 0 Validation Tests

### Test 1: PyQt6 Window Creation
Create `test_pyqt6.py`:
```python
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtCore import Qt

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Week 0 PyQt6 Test")
        self.setGeometry(100, 100, 400, 300)
        
        label = QLabel("PyQt6 Working!", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(label)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())
```

### Test 2: Pygame Surface Creation
Create `test_pygame.py`:
```python
import pygame
import sys

def test_pygame():
    pygame.init()
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("Week 0 Pygame Test")
    
    # Fill with blue background
    screen.fill((50, 50, 200))
    pygame.display.flip()
    
    # Keep window open for 3 seconds
    pygame.time.wait(3000)
    pygame.quit()

if __name__ == "__main__":
    test_pygame()
    print("Pygame test completed successfully!")
```

### Test 3: PyQt6 + Pygame Integration
Create `test_integration.py`:
```python
import sys
import pygame
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer

class PygameWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(400, 300)
        
    def paintEvent(self, event):
        # This will be where we embed Pygame surface
        pass

class IntegrationTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Week 0 Integration Test")
        
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        self.pygame_widget = PygameWidget()
        layout.addWidget(self.pygame_widget)
        
        self.setCentralWidget(central_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = IntegrationTest()
    window.show()
    sys.exit(app.exec())
```

## Success Criteria

### Environment Validation Checklist
- [ ] Python 3.11+ confirmed working
- [ ] Virtual environment created and activated
- [ ] PyQt6 imports without errors
- [ ] Pygame imports and initializes properly
- [ ] PyQt6 window displays correctly on Linux
- [ ] Pygame surface renders correctly
- [ ] No conflicts between PyQt6 and Pygame

### Development Workflow Validation
- [ ] Code formatting with `black` works
- [ ] Linting with `ruff` produces clean results  
- [ ] Type checking with `mypy` runs (warnings acceptable)
- [ ] Pytest can discover and run simple tests

## Common Issues and Solutions

### PyQt6 Installation Problems
```bash
# If PyQt6 fails to install
pip install --upgrade pip setuptools wheel
pip install PyQt6 --no-cache-dir
```

### Pygame Audio Issues (Linux)
```bash
# If pygame audio initialization fails
export SDL_AUDIODRIVER=pulse
# Or disable audio in pygame.init()
```

### Display Issues with Virtual Machines
```bash
# If running in VM, ensure hardware acceleration
export QT_X11_NO_MITSHM=1
```

## Next Steps After Validation
1. Review `Week 0 GUI Approach.md` for detailed daily objectives
2. Begin economic agent proof-of-concept as outlined in Day 1-2 plan
3. Establish git workflow for tracking validation progress
4. Document any platform-specific setup issues encountered

## Environment Maintenance
```bash
# Save current environment state
pip freeze > week0-requirements.txt

# Deactivate environment when done
deactivate

# Reactivate for next session
source vmt-dev/bin/activate
```

This setup guide ensures the foundation is solid before attempting PyQt6-Pygame integration experiments.