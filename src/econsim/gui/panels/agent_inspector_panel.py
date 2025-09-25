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
        self._home_label = QLabel("Home: —") 
        self._utility_label = QLabel("Utility: —")
        self._preference_label = QLabel("Preference: —")
        self._total_trades_label = QLabel("Total Trades: —")
        # Last 5 trades display (only populated when bilateral feature enabled)
        self._trade_labels = [QLabel("—") for _ in range(5)]
        
        # Populate agent list (deterministic order by agent ID)
        self._populate_agent_list()
        
        # Wire signals
        self._agent_box.currentIndexChanged.connect(self._on_agent_changed)  # type: ignore[arg-type]
        
        # Layout assembly
        layout.addLayout(agent_row)
        layout.addWidget(self._carry_label)
        layout.addWidget(self._home_label)
        layout.addWidget(self._utility_label)
        layout.addWidget(self._preference_label)
        layout.addWidget(self._total_trades_label)
        # Add section header and trade history
        layout.addWidget(QLabel("Recent Trades:"))
        for label in self._trade_labels:
            layout.addWidget(label)
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

    def get_selected_agent_id(self) -> int | None:
        """Get the currently selected agent ID, or None if no agent selected."""
        return self._agent_box.currentData()
    
    def _update_display(self) -> None:
        """Update the agent details display."""
        current_data = self._agent_box.currentData()
        if current_data is None:
            self._carry_label.setText("Carry: —")
            self._home_label.setText("Home: —")
            self._utility_label.setText("Utility: —")
            self._preference_label.setText("Preference: —")
            self._total_trades_label.setText("Total Trades: —")
            return
        
        try:
            # Get agent carry bundle (returns tuple of good1, good2)
            carry_bundle = self._controller.agent_carry_bundle(current_data)
            carry_text = f"Carry: (g1={carry_bundle[0]}, g2={carry_bundle[1]})"
            self._carry_label.setText(carry_text)
            
            # Get agent home bundle  
            home_bundle = self._controller.agent_home_bundle(current_data)
            home_text = f"Home: (g1={home_bundle[0]}, g2={home_bundle[1]})"
            self._home_label.setText(home_text)
            
            # Get agent utility (now includes total wealth: carrying + home)
            utility = self._controller.agent_carry_utility(current_data)
            utility_text = f"Utility: {utility:.3f}" if utility is not None else "Utility: —"
            self._utility_label.setText(utility_text)
            
            # Get agent preference type
            preference_type = self._controller.agent_preference_type(current_data)
            preference_text = f"Preference: {preference_type}" if preference_type else "Preference: —"
            self._preference_label.setText(preference_text)
            
            # Get total trades count
            total_trades = self._get_total_trades_count(current_data)
            self._total_trades_label.setText(f"Total Trades: {total_trades}")
            
            # Update trade history display
            self._update_trade_history_display(current_data)
            
        except Exception:
            # Graceful fallback if controller methods not available
            self._carry_label.setText("Carry: (unavailable)")
            self._home_label.setText("Home: (unavailable)")
            self._utility_label.setText("Utility: (unavailable)")
            self._preference_label.setText("Preference: (unavailable)")
            self._total_trades_label.setText("Total Trades: (unavailable)")
            # Clear trade history on error
            for label in self._trade_labels:
                label.setText("—")

    def _update_trade_history_display(self, agent_id: int) -> None:
        """Update the trade history display for the selected agent."""
        try:
            # Get trade history from controller
            if hasattr(self._controller, "agent_trade_history"):
                trade_history = self._controller.agent_trade_history(agent_id)
            else:
                trade_history = None
            
            # Clear all labels first
            for label in self._trade_labels:
                label.setText("—")
            
            if trade_history:
                # Display most recent trades first (reverse order)
                recent_trades = list(reversed(trade_history[-5:]))  # Last 5, most recent first
                
                for i, trade in enumerate(recent_trades):
                    if i < len(self._trade_labels):
                        try:
                            step = trade.get('step', '?')
                            partner = trade.get('partner_id', '?')
                            gave = trade.get('gave', '?')
                            received = trade.get('received', '?')
                            delta_u = trade.get('delta_utility', 0)
                            
                            trade_text = f"Step {step}: gave {gave} → got {received} from A{partner} (ΔU={delta_u:.3f})"
                            self._trade_labels[i].setText(trade_text)
                        except Exception:
                            self._trade_labels[i].setText("Trade info unavailable")
        except Exception:
            # Graceful fallback
            for label in self._trade_labels:
                label.setText("—")

    def _get_total_trades_count(self, agent_id: int) -> int:
        """Get the total number of completed trades for an agent."""
        try:
            # Get trade history from controller (same source as the display)
            if hasattr(self._controller, "agent_trade_history"):
                trade_history = self._controller.agent_trade_history(agent_id)
                if trade_history:
                    return len(trade_history)
            return 0
        except Exception:
            return 0


__all__ = ["AgentInspectorPanel"]