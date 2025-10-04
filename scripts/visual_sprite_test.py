#!/usr/bin/env python3
"""Visual verification script for sprite rendering."""

import os

from econsim.simulation.config import SimConfig
from econsim.simulation.world import Simulation
from econsim.gui.embedded_pygame import EmbeddedPygameWidget
from PyQt6.QtWidgets import QApplication, QMainWindow
import sys
import random

def main():
    app = QApplication(sys.argv)
    
    # Create a simple simulation with a few agents and resources
    config = SimConfig(
        grid_size=(8, 8),
        initial_resources=[
            (1, 1, "A"),  # Food resource
            (3, 2, "B"),  # Stone resource
            (5, 4, "A"),  # Food resource
            (2, 6, "B"),  # Stone resource
        ],

        perception_radius=3,
        respawn_target_density=0.1,
        respawn_rate=0.5,
        enable_respawn=True,
        enable_metrics=False,
        seed=42
    )
    
    sim = Simulation.from_config(config, agent_positions=[(0, 0), (7, 7), (3, 3)])
    
    # Create widget without simulation dependency (Phase 1B decoupling)
    widget = EmbeddedPygameWidget()
    # TODO: Phase 2 - widget will receive simulation state via observers
    widget.setWindowTitle("VMT Sprite Test - Agents (Blue) & Resources (Food/Stone)")
    widget.resize(400, 400)
    widget.show()
    
    print("Visual test launched!")
    print("- Agents should appear as blue sprites")
    print("- Type A resources should appear as food sprites")
    print("- Type B resources should appear as stone sprites")
    print("- Press Ctrl+C or close window to exit")
    
    return app.exec()

if __name__ == "__main__":
    main()