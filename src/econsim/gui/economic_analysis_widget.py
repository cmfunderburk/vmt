"""
Economic Analysis Widget

Displays economic data from comprehensive simulation deltas in a user-friendly format.
Provides real-time analysis of trades, utility changes, and economic decisions.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QTabWidget, QTableWidget, QTableWidgetItem, QGroupBox,
    QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from ..delta.playback_controller import ComprehensivePlaybackController


class EconomicAnalysisWidget(QWidget):
    """Widget for displaying economic analysis data from comprehensive deltas."""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.delta_controller: Optional[ComprehensivePlaybackController] = None
        self.setup_ui()
        
        # Auto-update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # Update every second
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Economic Analysis")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Create tabbed interface
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Economic Overview Tab
        self.overview_tab = self.create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "Overview")
        
        # Trade Analysis Tab
        self.trades_tab = self.create_trades_tab()
        self.tab_widget.addTab(self.trades_tab, "Trades")
        
        # Agent Analysis Tab
        self.agents_tab = self.create_agents_tab()
        self.tab_widget.addTab(self.agents_tab, "Agents")
        
        # Performance Tab
        self.performance_tab = self.create_performance_tab()
        self.tab_widget.addTab(self.performance_tab, "Performance")
    
    def create_overview_tab(self) -> QWidget:
        """Create the economic overview tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Current step info
        self.step_info = QLabel("Step: --")
        self.step_info.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(self.step_info)
        
        # Economic summary
        self.economic_summary = QTextEdit()
        self.economic_summary.setMaximumHeight(200)
        self.economic_summary.setReadOnly(True)
        layout.addWidget(QLabel("Economic Summary:"))
        layout.addWidget(self.economic_summary)
        
        # Recent decisions
        self.recent_decisions = QTextEdit()
        self.recent_decisions.setReadOnly(True)
        layout.addWidget(QLabel("Recent Economic Decisions:"))
        layout.addWidget(self.recent_decisions)
        
        return widget
    
    def create_trades_tab(self) -> QWidget:
        """Create the trade analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Trade events table
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(6)
        self.trades_table.setHorizontalHeaderLabels([
            "Step", "Seller", "Buyer", "Give", "Take", "Utility Δ"
        ])
        layout.addWidget(QLabel("Trade Events:"))
        layout.addWidget(self.trades_table)
        
        # Trade intents
        self.trade_intents = QTextEdit()
        self.trade_intents.setReadOnly(True)
        layout.addWidget(QLabel("Trade Intents:"))
        layout.addWidget(self.trade_intents)
        
        return widget
    
    def create_agents_tab(self) -> QWidget:
        """Create the agent analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Agent selector
        agent_layout = QHBoxLayout()
        agent_layout.addWidget(QLabel("Agent ID:"))
        self.agent_selector = QLabel("--")
        agent_layout.addWidget(self.agent_selector)
        agent_layout.addStretch()
        layout.addLayout(agent_layout)
        
        # Agent details
        self.agent_details = QTextEdit()
        self.agent_details.setReadOnly(True)
        layout.addWidget(QLabel("Agent Details:"))
        layout.addWidget(self.agent_details)
        
        return widget
    
    def create_performance_tab(self) -> QWidget:
        """Create the performance analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Performance metrics
        self.performance_metrics = QTextEdit()
        self.performance_metrics.setReadOnly(True)
        layout.addWidget(QLabel("Performance Metrics:"))
        layout.addWidget(self.performance_metrics)
        
        return widget
    
    def set_delta_controller(self, controller: ComprehensivePlaybackController):
        """Set the comprehensive delta controller."""
        self.delta_controller = controller
    
    def update_display(self):
        """Update the display with current data."""
        if not self.delta_controller:
            return
        
        current_step = self.delta_controller.get_current_step()
        self.step_info.setText(f"Step: {current_step}")
        
        # Update overview
        self.update_overview(current_step)
        
        # Update trades
        self.update_trades(current_step)
        
        # Update agents
        self.update_agents(current_step)
        
        # Update performance
        self.update_performance(current_step)
    
    def update_overview(self, step: int):
        """Update the economic overview."""
        economic_data = self.delta_controller.get_economic_data(step)
        
        # Economic summary
        summary_text = f"Step {step} Economic Summary:\n\n"
        
        trade_events = economic_data.get('trade_events', [])
        trade_intents = economic_data.get('trade_intents', [])
        economic_decisions = economic_data.get('economic_decisions', [])
        utility_changes = economic_data.get('agent_utility_changes', [])
        
        summary_text += f"Trade Events: {len(trade_events)}\n"
        summary_text += f"Trade Intents: {len(trade_intents)}\n"
        summary_text += f"Economic Decisions: {len(economic_decisions)}\n"
        summary_text += f"Utility Changes: {len(utility_changes)}\n"
        
        self.economic_summary.setText(summary_text)
        
        # Recent decisions
        decisions_text = f"Recent Economic Decisions (Step {step}):\n\n"
        for decision in economic_decisions[:5]:  # Show last 5 decisions
            decisions_text += f"Agent {decision.get('agent_id', '?')}: {decision.get('decision_type', '?')}\n"
            decisions_text += f"  Context: {decision.get('decision_context', 'N/A')}\n"
            decisions_text += f"  Utility Δ: {decision.get('utility_after', 0) - decision.get('utility_before', 0):.2f}\n\n"
        
        self.recent_decisions.setText(decisions_text)
    
    def update_trades(self, step: int):
        """Update the trade analysis."""
        economic_data = self.delta_controller.get_economic_data(step)
        trade_events = economic_data.get('trade_events', [])
        
        # Update trades table
        self.trades_table.setRowCount(len(trade_events))
        for row, trade in enumerate(trade_events):
            self.trades_table.setItem(row, 0, QTableWidgetItem(str(trade.get('step', step))))
            self.trades_table.setItem(row, 1, QTableWidgetItem(str(trade.get('seller_id', '?'))))
            self.trades_table.setItem(row, 2, QTableWidgetItem(str(trade.get('buyer_id', '?'))))
            self.trades_table.setItem(row, 3, QTableWidgetItem(str(trade.get('give_type', '?'))))
            self.trades_table.setItem(row, 4, QTableWidgetItem(str(trade.get('take_type', '?'))))
            utility_delta = trade.get('seller_utility_after', 0) - trade.get('seller_utility_before', 0)
            self.trades_table.setItem(row, 5, QTableWidgetItem(f"{utility_delta:.2f}"))
        
        # Update trade intents
        trade_intents = economic_data.get('trade_intents', [])
        intents_text = f"Trade Intents (Step {step}):\n\n"
        for intent in trade_intents:
            intents_text += f"Agent {intent.get('agent_id', '?')} → Agent {intent.get('partner_id', '?')}\n"
            intents_text += f"  Give: {intent.get('proposed_give', {})}\n"
            intents_text += f"  Take: {intent.get('proposed_take', {})}\n"
            intents_text += f"  Type: {intent.get('intent_type', '?')}\n\n"
        
        self.trade_intents.setText(intents_text)
    
    def update_agents(self, step: int):
        """Update the agent analysis."""
        # For now, show data for agent 1 (could be made configurable)
        agent_data = self.delta_controller.get_agent_state(1, step)
        
        self.agent_selector.setText("1")
        
        details_text = f"Agent 1 Analysis (Step {step}):\n\n"
        
        moves = agent_data.get('moves', [])
        mode_changes = agent_data.get('mode_changes', [])
        inventory_changes = agent_data.get('inventory_changes', [])
        utility_changes = agent_data.get('utility_changes', [])
        
        details_text += f"Moves: {len(moves)}\n"
        details_text += f"Mode Changes: {len(mode_changes)}\n"
        details_text += f"Inventory Changes: {len(inventory_changes)}\n"
        details_text += f"Utility Changes: {len(utility_changes)}\n\n"
        
        # Show recent moves
        if moves:
            details_text += "Recent Moves:\n"
            for move in moves[-3:]:  # Last 3 moves
                details_text += f"  From ({move.get('old_x', '?')}, {move.get('old_y', '?')}) to ({move.get('new_x', '?')}, {move.get('new_y', '?')})\n"
            details_text += "\n"
        
        # Show utility changes
        if utility_changes:
            details_text += "Utility Changes:\n"
            for change in utility_changes[-3:]:  # Last 3 changes
                details_text += f"  {change.get('old_utility', 0):.2f} → {change.get('new_utility', 0):.2f} (Δ{change.get('utility_delta', 0):.2f})\n"
        
        self.agent_details.setText(details_text)
    
    def update_performance(self, step: int):
        """Update the performance analysis."""
        economic_data = self.delta_controller.get_economic_data(step)
        performance_metrics = economic_data.get('performance_metrics')
        
        if performance_metrics:
            metrics_text = f"Performance Metrics (Step {step}):\n\n"
            metrics_text += f"Step Duration: {performance_metrics.get('step_duration_ms', 0):.2f} ms\n"
            metrics_text += f"Agents Processed: {performance_metrics.get('agents_processed', 0)}\n"
            metrics_text += f"Resources Processed: {performance_metrics.get('resources_processed', 0)}\n"
            metrics_text += f"Trades Attempted: {performance_metrics.get('trades_attempted', 0)}\n"
            metrics_text += f"Trades Executed: {performance_metrics.get('trades_executed', 0)}\n"
            metrics_text += f"Memory Usage: {performance_metrics.get('memory_usage_mb', 0):.2f} MB\n"
        else:
            metrics_text = f"No performance metrics available for step {step}"
        
        self.performance_metrics.setText(metrics_text)
