"""Test trade inspector panel functionality."""
import os
import sys
from unittest import mock

# We need to set up QApplication for Qt widgets
import pytest
from PyQt6.QtWidgets import QApplication

from econsim.gui.panels.trade_inspector_panel import TradeInspectorPanel
from econsim.gui.simulation_controller import SimulationController


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    if not QApplication.instance():
        app = QApplication(sys.argv)
        yield app
        app.quit()
    else:
        yield QApplication.instance()


def test_trade_inspector_panel_creation(qapp):
    """Test that TradeInspectorPanel can be created without crashing."""
    # Create mock controller
    mock_controller = mock.MagicMock(spec=SimulationController)
    mock_controller.trade_draft_enabled.return_value = True
    mock_controller.trade_execution_enabled.return_value = False
    mock_controller.active_intents_count.return_value = 0
    mock_controller.get_active_intents.return_value = []
    mock_controller.last_trade_summary.return_value = None
    mock_controller.calculate_total_welfare_change.return_value = 0.0
    mock_controller.count_trading_pairs.return_value = 0
    mock_controller.analyze_preference_diversity.return_value = "Homogeneous (CobbDouglas)"
    
    # Create panel
    panel = TradeInspectorPanel(mock_controller)
    
    # Verify basic structure
    assert panel is not None
    assert hasattr(panel, '_update_display')
    assert hasattr(panel, 'get_visualization_options')
    assert hasattr(panel, 'is_pause_on_trade_enabled')
    
    # Test visualization options
    viz_options = panel.get_visualization_options()
    assert 'show_arrows' in viz_options
    assert 'show_highlights' in viz_options
    assert viz_options['show_arrows'] is True  # Default
    assert viz_options['show_highlights'] is True  # Default
    
    # Test pause on trade (should be False by default)
    assert panel.is_pause_on_trade_enabled() is False
    
    # Clean up
    panel.close()


def test_trade_inspector_with_active_trades(qapp):
    """Test panel with mock active trades."""
    # Create mock controller with active trades
    mock_controller = mock.MagicMock(spec=SimulationController)
    mock_controller.trade_draft_enabled.return_value = True
    mock_controller.trade_execution_enabled.return_value = True
    mock_controller.active_intents_count.return_value = 2
    
    # Mock trade intents
    mock_intent1 = mock.MagicMock()
    mock_intent1.seller_id = 0
    mock_intent1.buyer_id = 1
    mock_intent1.give_type = "good1"
    mock_intent1.take_type = "good2"
    mock_intent1.delta_utility = 1.5
    
    mock_intent2 = mock.MagicMock()
    mock_intent2.seller_id = 2
    mock_intent2.buyer_id = 3
    mock_intent2.give_type = "good2"
    mock_intent2.take_type = "good1"
    mock_intent2.delta_utility = 0.8
    
    mock_controller.get_active_intents.return_value = [mock_intent1, mock_intent2]
    mock_controller.last_trade_summary.return_value = "A0→A1 good1→good2 ΔU=1.200"
    mock_controller.calculate_total_welfare_change.return_value = 2.3
    mock_controller.count_trading_pairs.return_value = 2
    mock_controller.analyze_preference_diversity.return_value = "Mixed (2 types)"
    
    # Create panel and trigger update
    panel = TradeInspectorPanel(mock_controller)
    panel._update_display()
    
    # Verify controller methods were called
    mock_controller.active_intents_count.assert_called()
    mock_controller.get_active_intents.assert_called()
    mock_controller.calculate_total_welfare_change.assert_called()
    mock_controller.count_trading_pairs.assert_called()
    mock_controller.analyze_preference_diversity.assert_called()
    
    # Clean up
    panel.close()


if __name__ == "__main__":
    # Run tests directly for quick verification
    app = QApplication(sys.argv)
    
    try:
        test_trade_inspector_panel_creation(app)
        test_trade_inspector_with_active_trades(app)
        print("Trade inspector panel tests passed!")
    finally:
        app.quit()