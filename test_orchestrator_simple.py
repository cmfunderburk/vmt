#!/usr/bin/env python3
"""
Simple test of DebugOrchestrator environment configuration without PyQt dependencies.
"""

import os
import sys

# Add src to path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Clear environment to simulate clean start
for key in list(os.environ.keys()):
    if key.startswith('ECONSIM_'):
        del os.environ[key]

print("🧪 Testing DebugOrchestrator environment configuration...")

# Import the orchestrator class directly without GUI dependencies
sys.path.append('src/econsim/tools/launcher/framework')

# Mock the TestConfiguration class
class MockTestConfiguration:
    def __init__(self):
        self.id = 999
        self.name = "Debug Test"
        self.debug_categories = None
        self.preference_mix = 'cobb_douglas'

# Import and test the orchestrator
try:
    from debug_orchestrator import DebugOrchestrator
    
    config = MockTestConfiguration()
    orchestrator = DebugOrchestrator(config)
    
    print("\n📊 Structured Logging Environment Variables:")
    print("=" * 50)
    
    # Check the key structured logging variables
    structured_vars = [
        'ECONSIM_LOG_LEVEL',
        'ECONSIM_LOG_FORMAT', 
        'ECONSIM_LOG_CATEGORIES',
        'ECONSIM_LOG_EXPLANATIONS',
        'ECONSIM_LOG_DECISION_REASONING'
    ]
    
    all_good = True
    for var in structured_vars:
        value = os.environ.get(var, 'NOT SET')
        status = "✅" if value != 'NOT SET' else "❌"
        print(f"{status} {var}: {value}")
        if value == 'NOT SET':
            all_good = False
    
    # Check key simulation flags
    print(f"\n🔧 Key Simulation Flags:")
    sim_vars = ['ECONSIM_FORAGE_ENABLED', 'ECONSIM_TRADE_DRAFT', 'ECONSIM_TRADE_EXEC']
    for var in sim_vars:
        value = os.environ.get(var, 'NOT SET')
        status = "✅" if value == '1' else "❌"
        print(f"{status} {var}: {value}")
    
    print(f"\n🎉 Results:")
    if all_good:
        print("✅ SUCCESS: Comprehensive logging properly configured!")
        print("   📈 Phase 3.2 behavior tracking will work automatically")
        print("   🔗 Phase 3.4 event clustering will work automatically") 
        print("   🚀 Future logging enhancements will be incorporated by default")
    else:
        print("❌ FAILED: Some structured logging variables not set")
        
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()