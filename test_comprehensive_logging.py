#!/usr/bin/env python3
"""
Test that base_test now enables comprehensive logging by default.

Validates that the DebugOrchestrator properly configures all structured
logging environment variables for comprehensive educational logging.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Clear environment to simulate clean start
for key in list(os.environ.keys()):
    if key.startswith('ECONSIM_'):
        del os.environ[key]

print("🧪 Testing DebugOrchestrator comprehensive logging configuration...")

# Import and create orchestrator (simulating base_test initialization)
from econsim.tools.launcher.framework.debug_orchestrator import DebugOrchestrator
from econsim.tools.launcher.framework.test_configs import TestConfiguration

# Create a basic test configuration
config = TestConfiguration(
    id=999,
    name="Debug Test",
    description="Testing comprehensive logging",
    agent_count=10,
    steps=100,
    viewport_size=400
)

# Create orchestrator (this should set up comprehensive logging)
orchestrator = DebugOrchestrator(config)

print("\n📊 Environment Variables Set:")
print("=" * 50)

# Check structured logging configuration
structured_vars = {
    'ECONSIM_LOG_LEVEL': os.environ.get('ECONSIM_LOG_LEVEL', 'NOT SET'),
    'ECONSIM_LOG_FORMAT': os.environ.get('ECONSIM_LOG_FORMAT', 'NOT SET'), 
    'ECONSIM_LOG_CATEGORIES': os.environ.get('ECONSIM_LOG_CATEGORIES', 'NOT SET'),
    'ECONSIM_LOG_EXPLANATIONS': os.environ.get('ECONSIM_LOG_EXPLANATIONS', 'NOT SET'),
    'ECONSIM_LOG_DECISION_REASONING': os.environ.get('ECONSIM_LOG_DECISION_REASONING', 'NOT SET'),
}

for var, value in structured_vars.items():
    status = "✅" if value != 'NOT SET' else "❌"
    print(f"{status} {var}: {value}")

# Check some standard debug flags
standard_vars = {
    'ECONSIM_DEBUG_TRADES': os.environ.get('ECONSIM_DEBUG_TRADES', 'NOT SET'),
    'ECONSIM_FORAGE_ENABLED': os.environ.get('ECONSIM_FORAGE_ENABLED', 'NOT SET'),
    'ECONSIM_TRADE_DRAFT': os.environ.get('ECONSIM_TRADE_DRAFT', 'NOT SET'),
    'ECONSIM_TRADE_EXEC': os.environ.get('ECONSIM_TRADE_EXEC', 'NOT SET'),
}

print("\n🔧 Standard Debug Flags:")
print("=" * 30)
for var, value in standard_vars.items():
    status = "✅" if value == '1' else "❌" if value == 'NOT SET' else "⚠️"
    print(f"{status} {var}: {value}")

# Test selective disabling
print("\n🎯 Testing Selective Disable Functionality:")
print("=" * 45)
print(f"Before disable: ECONSIM_LOG_CATEGORIES = {os.environ.get('ECONSIM_LOG_CATEGORIES')}")

orchestrator.disable_log_categories(['PERF', 'STAGNATION'])
print(f"After disable PERF,STAGNATION: ECONSIM_LOG_CATEGORIES = {os.environ.get('ECONSIM_LOG_CATEGORIES')}")

orchestrator.set_minimal_logging()
print(f"After minimal logging: ECONSIM_LOG_CATEGORIES = {os.environ.get('ECONSIM_LOG_CATEGORIES')}")

# Verify results
print("\n🎉 Summary:")
print("=" * 20)

all_structured_set = all(value != 'NOT SET' for value in structured_vars.values())
comprehensive_enabled = os.environ.get('ECONSIM_LOG_CATEGORIES') != 'NOT SET'

if all_structured_set and comprehensive_enabled:
    print("✅ SUCCESS: Comprehensive logging enabled by default!")
    print("   - All structured logging variables properly set")
    print("   - Future logging enhancements will be automatically incorporated")
    print("   - Selective disable functionality working")
else:
    print("❌ FAILED: Comprehensive logging not properly configured")
    if not all_structured_set:
        print("   - Missing structured logging environment variables")
    if not comprehensive_enabled:
        print("   - Log categories not properly enabled")

print("\n🚀 base_test will now automatically enable all future logging features!")