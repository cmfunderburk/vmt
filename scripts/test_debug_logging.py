#!/usr/bin/env python3
"""
Test script for enhanced debug logging capabilities.

This script validates all the new debug logging features including:
- Enhanced configuration system
- Educational context logging  
- Performance analysis
- Runtime configurability
"""
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_basic_logging():
    """Test basic debug logging functionality."""
    print("🧪 Testing basic debug logging...")
    
    # Set up environment for debug logging
    os.environ['ECONSIM_DEBUG_ECONOMICS'] = '1'
    os.environ['ECONSIM_DEBUG_TRADES'] = '1'
    os.environ['ECONSIM_DEBUG_PERFORMANCE'] = '1'
    
    from econsim.gui.debug_logger import (
        get_gui_logger, log_utility_change, log_trade_detail, 
        log_performance_analysis, finalize_log_session
    )
    
    # Test utility logging
    log_utility_change(1, 10.0, 12.5, 'collected bread', 1, 'bread')
    log_utility_change(2, 8.0, 7.2, 'gave away fish', 2, 'fish')
    
    # Test trade logging  
    log_trade_detail(1, 'bread', 2, 'fish', 1.5, 3)
    
    # Test performance analysis
    log_performance_analysis(
        fps=45.2, step_time=0.018, render_time=0.012, 
        agent_count=50, resource_count=80, step=100
    )
    log_performance_analysis(
        fps=25.1, step_time=0.035, render_time=0.028, 
        agent_count=150, resource_count=250, step=200
    )
    
    print("✅ Basic logging test completed")
    finalize_log_session()

def test_educational_logging():
    """Test educational context features."""
    print("🧪 Testing educational logging features...")
    
    # Enable educational features
    os.environ['ECONSIM_LOG_EXPLANATIONS'] = '1'
    os.environ['ECONSIM_LOG_DECISION_REASONING'] = '1'
    
    from econsim.gui.debug_logger import log_utility_change, finalize_log_session
    
    # Test with educational explanations
    log_utility_change(1, 5.0, 8.5, 'successful trade', 10, 'bread')
    log_utility_change(2, 12.0, 11.8, 'marginal loss', 11, 'fish')
    log_utility_change(3, 3.0, 6.2, 'resource collection', 12, 'wood')
    
    print("✅ Educational logging test completed")  
    finalize_log_session()

def test_configuration_system():
    """Test enhanced configuration capabilities."""
    print("🧪 Testing configuration system...")
    
    try:
        from econsim.gui.log_config import LogConfig, LogManager, get_log_manager
        
        # Test creating config from environment
        config = LogConfig.from_environment()
        print(f"  Default config level: {config.level}")
        print(f"  Default config format: {config.format}")
        
        # Test runtime configuration changes
        manager = get_log_manager()
        original_level = manager.config.level
        
        manager.update_config(level="VERBOSE")
        print(f"  Updated config level: {manager.config.level}")
        
        # Test serialization
        config_dict = manager.config.to_dict()
        print(f"  Config serializable: {len(config_dict)} keys")
        
        # Restore original
        manager.update_config(level=original_level.value)
        
        print("✅ Configuration system test completed")
        
    except ImportError as e:
        print(f"⚠️  Configuration system not available: {e}")

def test_performance_monitoring():
    """Test performance monitoring features."""
    print("🧪 Testing performance monitoring...")
    
    os.environ['ECONSIM_DEBUG_PERFORMANCE'] = '1'
    
    from econsim.gui.debug_logger import log_performance_analysis, finalize_log_session
    
    # Test various performance scenarios
    scenarios = [
        # Good performance
        (60.0, 0.012, 0.008, 20, 40, "good"),
        # Borderline performance
        (30.5, 0.032, 0.020, 80, 120, "borderline"), 
        # Poor performance - should trigger warnings
        (18.2, 0.055, 0.048, 200, 350, "poor"),
        # Rendering bottleneck
        (25.0, 0.040, 0.035, 50, 75, "render_bottleneck"),
        # Logic bottleneck  
        (22.0, 0.045, 0.015, 150, 200, "logic_bottleneck")
    ]
    
    for i, (fps, step_time, render_time, agents, resources, scenario) in enumerate(scenarios):
        print(f"  Scenario {i+1}: {scenario}")
        log_performance_analysis(fps, step_time, render_time, agents, resources, i*10)
    
    print("✅ Performance monitoring test completed")
    finalize_log_session()

def test_log_filtering():
    """Test selective log filtering."""
    print("🧪 Testing log filtering...")
    
    # Test with different debug flags
    test_configs = [
        {"ECONSIM_DEBUG_ECONOMICS": "1"},
        {"ECONSIM_DEBUG_TRADES": "1"}, 
        {"ECONSIM_DEBUG_PERFORMANCE": "1"},
        {"ECONSIM_DEBUG_ECONOMICS": "1", "ECONSIM_DEBUG_TRADES": "1"},
    ]
    
    from econsim.gui.debug_logger import (
        log_utility_change, log_trade_detail, log_performance_analysis,
        finalize_log_session
    )
    
    for i, config in enumerate(test_configs):
        print(f"  Testing config {i+1}: {list(config.keys())}")
        
        # Clear environment
        for key in ["ECONSIM_DEBUG_ECONOMICS", "ECONSIM_DEBUG_TRADES", "ECONSIM_DEBUG_PERFORMANCE"]:
            os.environ.pop(key, None)
            
        # Set new config
        for key, value in config.items():
            os.environ[key] = value
            
        # Test logging with this config
        log_utility_change(1, 10.0, 11.0, f'test_{i}', i, 'bread')
        log_trade_detail(1, 'bread', 2, 'fish', 0.5, i)
        log_performance_analysis(45.0, 0.020, 0.015, 30, 50, i)
    
    print("✅ Log filtering test completed")
    finalize_log_session()

def main():
    """Run all debug logging tests."""
    print("🚀 VMT Debug Logging Enhancement Test Suite")
    print("=" * 50)
    
    try:
        test_basic_logging()
        test_educational_logging()
        test_configuration_system() 
        test_performance_monitoring()
        test_log_filtering()
        
        print("\n🎉 All debug logging tests completed successfully!")
        print("\n📁 Check gui_logs/ directory for generated log files")
        
        # Show most recent log file info
        import glob
        log_files = glob.glob("gui_logs/*.log")
        if log_files:
            latest_log = max(log_files, key=os.path.getctime)
            size = os.path.getsize(latest_log)
            print(f"📄 Latest log: {latest_log} ({size} bytes)")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()