#!/usr/bin/env python3
"""
Simple diagnostic script to check if bilateral exchange and GUI panels are working.
This will create a minimal test to verify:
1. Are trades actually happening in the GUI simulation?
2. Is the event log panel properly connected?
3. Is the agent inspector getting data?
"""

import os
import sys
import random
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Set up environment for bilateral exchange
os.environ["ECONSIM_NEW_GUI"] = "1"
os.environ["ECONSIM_TRADE_DRAFT"] = "1"
os.environ["ECONSIM_TRADE_EXEC"] = "1"
os.environ["ECONSIM_TRADE_GUI_INFO"] = "1"

# Import after setting environment variables
from econsim.simulation.world import Simulation
from econsim.simulation.agent import Agent, AgentMode
from econsim.simulation.grid import Grid
from econsim.preferences.cobb_douglas import CobbDouglasPreference
from econsim.simulation.metrics import MetricsCollector
from econsim.gui.simulation_controller import SimulationController
from econsim.gui.panels.event_log_panel import EventLogPanel
from econsim.gui.panels.agent_inspector_panel import AgentInspectorPanel

def test_gui_panels():
    print("=== GUI Panel Diagnostic Test ===")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    try:
        # Create a simple simulation with 2 agents AT THE SAME LOCATION
        a1 = Agent(id=1, x=2, y=2, preference=CobbDouglasPreference(alpha=0.3))
        a2 = Agent(id=2, x=2, y=2, preference=CobbDouglasPreference(alpha=0.7))
        
        # Give them complementary goods with higher quantities to make trade more attractive
        a1.carrying['good1'] = 5
        a2.carrying['good2'] = 5
        
        # Force into bilateral exchange mode
        a1.mode = AgentMode.IDLE
        a2.mode = AgentMode.IDLE
        
        print(f"   Initial positions: A1 at ({a1.x}, {a1.y}), A2 at ({a2.x}, {a2.y})")
        print(f"   Co-located: {a1.x == a2.x and a1.y == a2.y}")
        
        sim = Simulation(grid=Grid(5, 5, []), agents=[a1, a2])
        sim.metrics_collector = MetricsCollector()
        
        controller = SimulationController(simulation=sim)
        
        # CRITICAL FIX: Disable foraging to allow pure bilateral exchange
        controller.set_forage_enabled(False)
        
        print(f"✅ Created simulation with controller")
        print(f"   Bilateral exchange enabled: {controller._bilateral_enabled}")
        print(f"   Foraging enabled: {controller._forage_enabled}")
        print(f"   Environment variables set: DRAFT={os.environ.get('ECONSIM_TRADE_DRAFT')}, EXEC={os.environ.get('ECONSIM_TRADE_EXEC')}")
        
        # Create GUI panels
        event_log = EventLogPanel(controller)
        agent_inspector = AgentInspectorPanel(controller)
        
        print(f"✅ Created GUI panels")
        
        # Test simulation steps to see if trades happen
        rng = random.Random(123)
        
        print(f"\n--- Running Simulation Steps ---")
        for step in range(3):
            print(f"\nStep {step}:")
            print(f"  Before: A1 carrying={dict(a1.carrying)}, mode={a1.mode}, A2 carrying={dict(a2.carrying)}, mode={a2.mode}")
            print(f"  Positions: A1 at ({a1.x}, {a1.y}), A2 at ({a2.x}, {a2.y})")
            
            # Check if trade intents will be generated  
            print(f"  Environment flags: DRAFT={os.environ.get('ECONSIM_TRADE_DRAFT')}, EXEC={os.environ.get('ECONSIM_TRADE_EXEC')}")
            
            # Step the simulation
            sim.step(rng, use_decision=False)
            
            print(f"  After:  A1 carrying={dict(a1.carrying)}, mode={a1.mode}, A2 carrying={dict(a2.carrying)}, mode={a2.mode}")
            print(f"  Positions: A1 at ({a1.x}, {a1.y}), A2 at ({a2.x}, {a2.y})")
            
            # Check trade intents
            trade_intents = getattr(sim, 'trade_intents', [])
            print(f"  Trade intents generated: {len(trade_intents)}")
            if trade_intents:
                for i, intent in enumerate(trade_intents):
                    print(f"    Intent {i}: {intent}")
            
            # Check metrics collector directly
            mc = sim.metrics_collector
            print(f"  Metrics - Last trade: {mc.last_executed_trade}")
            print(f"  Metrics - Agent histories: {dict(mc.agent_trade_histories)}")
            
            # Check controller methods
            current_step = controller.get_current_step()
            recent_trades = controller.get_recent_trades(current_step)
            print(f"  Controller - Current step: {current_step}")
            print(f"  Controller - Recent trades: {recent_trades}")
            
            # Check agent trade history
            for agent_id in [1, 2]:
                history = controller.agent_trade_history(agent_id)
                print(f"  Controller - Agent {agent_id} history: {history}")
            
            # Trigger GUI panel updates manually and check their internal state
            event_log._update_log()
            print(f"  Event Log - Log entries: {event_log._log_entries[-3:] if len(event_log._log_entries) > 3 else event_log._log_entries}")
            
            # Update agent inspector for agent 1
            agent_inspector._update_trade_history(1)
            print(f"  Agent Inspector - Trade labels text: {[label.text() for label in agent_inspector._trade_labels[:2]]}")
            
            if recent_trades:
                print(f"  🎉 TRADE DETECTED!")
                break
        
        print(f"\n--- Final Status ---")
        if not recent_trades:
            print(f"❌ No trades detected through controller")
            print(f"   This suggests either trades aren't happening or detection is broken")
        else:
            print(f"✅ Trades detected and panels should be working")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        app.quit()

if __name__ == "__main__":
    test_gui_panels()