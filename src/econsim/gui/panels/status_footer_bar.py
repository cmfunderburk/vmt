"""Status Footer Bar for simulation window.

Shows current overlay states, decision mode, and pause status in bottom footer.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import QTimer

from ..simulation_controller import SimulationController
from ..overlay_state import OverlayState


class StatusFooterBar(QWidget):  # pragma: no cover (GUI)
    def __init__(self, controller: SimulationController, overlay_state: OverlayState):
        super().__init__()
        self._controller = controller
        self._overlay_state = overlay_state
        
        layout = QHBoxLayout(self)
        
        # Status labels
        self._grid_status = QLabel("Grid: ON")
        self._overlay_status = QLabel("Overlay: ON")  
        self._mode_status = QLabel("Mode: Decision")
        self._paused_status = QLabel("Paused: No")
        
        # Add labels with separators
        layout.addWidget(self._grid_status)
        layout.addWidget(QLabel(" | "))
        layout.addWidget(self._overlay_status)
        layout.addWidget(QLabel(" | "))
        layout.addWidget(self._mode_status)
        layout.addWidget(QLabel(" | "))
        layout.addWidget(self._paused_status)
        layout.addStretch()
        
        # Auto-update timer
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_status)  # type: ignore[arg-type]
        self._update_timer.start(500)  # 2 Hz update rate
        
        # Initial update
        self._update_status()
    
    def _update_status(self) -> None:
        """Update all status displays."""
        try:
            # Grid overlay status
            grid_on = self._overlay_state.show_grid
            self._grid_status.setText(f"Grid: {'ON' if grid_on else 'OFF'}")
            
            # General overlay status (any overlay enabled)
            any_overlay = (self._overlay_state.show_grid or 
                         self._overlay_state.show_agent_ids or
                         self._overlay_state.show_target_arrow or 
                         self._overlay_state.show_home_labels)
            self._overlay_status.setText(f"Overlay: {'ON' if any_overlay else 'OFF'}")
            
            # Decision mode status
            try:
                decision_mode = getattr(self._controller, '_use_decision_mode', True)
                mode_text = "Decision" if decision_mode else "Legacy"
            except Exception:
                mode_text = "Decision"  # Default assumption
            self._mode_status.setText(f"Mode: {mode_text}")
            
            # Paused status
            is_paused = self._controller.is_paused()
            self._paused_status.setText(f"Paused: {'Yes' if is_paused else 'No'}")
            
        except Exception:
            # Graceful fallback if any status check fails
            pass


__all__ = ["StatusFooterBar"]