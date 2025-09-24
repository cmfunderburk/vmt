"""Agent Inspector panel for detailed agent state viewing.

Displays selected agent's current carrying bundle, utility, and other inspector details.
Updates via timer to show live state without affecting simulation determinism.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import QTimer

from ..simulation_controller import SimulationController


class AgentInspectorPanel(QWidget):  # pragma: no cover (GUI)
    def __init__(self, controller: SimulationController):
        super().__init__()
        self._controller = controller
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Agent selection
        agent_row = QHBoxLayout()
        agent_row.addWidget(QLabel("Agent:"))
        self._agent_box = QComboBox()
        self._agent_box.setToolTip("Select an agent to inspect its current state")
        agent_row.addWidget(self._agent_box)
        agent_row.addStretch()
        
        # Agent details
        self._carry_label = QLabel("Carry: —")
        self._utility_label = QLabel("Utility: —")
        
        # Populate agent list (deterministic order by agent ID)
        self._populate_agent_list()
        
        # Wire signals
        self._agent_box.currentIndexChanged.connect(self._on_agent_changed)  # type: ignore[arg-type]
        
        # Layout assembly
        layout.addLayout(agent_row)
        layout.addWidget(self._carry_label)
        layout.addWidget(self._utility_label)
        layout.addStretch()
        
        # Auto-refresh timer (4 Hz max per requirements)
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._update_display)  # type: ignore[arg-type]
        self._update_timer.start(250)  # 4 Hz
        
        # Initial update
        self._update_display()
    
    def _populate_agent_list(self) -> None:
        """Populate agent dropdown with available agents in deterministic order."""
        try:
            agent_ids = self._controller.list_agent_ids()
            for aid in sorted(agent_ids):  # Ensure deterministic order
                self._agent_box.addItem(f"Agent {aid}", userData=aid)
        except Exception:
            # Fallback if controller doesn't have agent listing method
            self._agent_box.addItem("No agents available", userData=None)
    
    def _on_agent_changed(self) -> None:
        """Handle agent selection change."""
        self._update_display()
    
    def _update_display(self) -> None:
        """Update the agent details display."""
        current_data = self._agent_box.currentData()
        if current_data is None:
            self._carry_label.setText("Carry: —")
            self._utility_label.setText("Utility: —")
            return
        
        try:
            # Get agent carry bundle (returns tuple of good1, good2)
            carry_bundle = self._controller.agent_carry_bundle(current_data)
            carry_text = f"Carry: (g1={carry_bundle[0]}, g2={carry_bundle[1]})"
            self._carry_label.setText(carry_text)
            
            # Get agent utility
            utility = self._controller.agent_carry_utility(current_data)
            utility_text = f"Utility: {utility:.3f}" if utility is not None else "Utility: —"
            self._utility_label.setText(utility_text)
            
        except Exception:
            # Graceful fallback if controller methods not available
            self._carry_label.setText("Carry: (unavailable)")
            self._utility_label.setText("Utility: (unavailable)")


__all__ = ["AgentInspectorPanel"]