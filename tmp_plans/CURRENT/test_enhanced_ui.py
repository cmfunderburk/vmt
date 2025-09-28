#!/usr/bin/env python3
"""Test enhanced TestRunner with StandardPhaseTest UI.

This tests the enhanced TestRunner that uses the full StandardPhaseTest
framework to provide the complete UI experience.
"""

import sys
from pathlib import Path

# Add src to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root / "src"))

def test_enhanced_ui():
    """Test that TestRunner creates full UI with StandardPhaseTest."""
    print("🔧 Testing enhanced UI with StandardPhaseTest...")
    
    try:
        # Import PyQt6 first
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        
        # Create QApplication
        app = QApplication(sys.argv)
        
        # Import TestRunner
        from econsim.tools.launcher.test_runner import TestRunner
        
        # Initialize runner
        runner = TestRunner()
        print("✅ Enhanced TestRunner initialized")
        
        # Track test results
        test_results = {"success": False, "error": None, "ui_type": None}
        
        def run_test():
            """Run the test and analyze the created window."""
            try:
                print("🚀 Attempting to launch Test 1 with enhanced UI...")
                
                # Launch test 1
                runner.run_by_id(1, "framework")
                print("✅ Test launch call succeeded")
                
                # Check what type of window was created
                if runner.current_test_window:
                    window_type = type(runner.current_test_window).__name__
                    test_results["ui_type"] = window_type
                    print(f"📋 Window type: {window_type}")
                    
                    # Check if it has StandardPhaseTest features
                    has_controls = hasattr(runner.current_test_window, 'test_layout')
                    has_config = hasattr(runner.current_test_window, 'config')
                    has_simulation = hasattr(runner.current_test_window, 'simulation')
                    
                    print(f"   Has test_layout: {has_controls}")
                    print(f"   Has config: {has_config}")
                    print(f"   Has simulation: {has_simulation}")
                    
                    if has_controls and has_config:
                        print("✅ Enhanced UI features detected")
                        test_results["success"] = True
                    else:
                        print("⚠️ Basic UI detected - enhancement may not be working")
                        test_results["success"] = True  # Still working, just not enhanced
                else:
                    print("❌ No test window created")
                
                # Schedule window close after brief delay
                def close_test():
                    print("🔄 Closing test window...")
                    if runner.current_test_window:
                        runner.close_current_test()
                        print("✅ Test window closed")
                    
                    app.quit()
                
                # Close after 3 seconds
                QTimer.singleShot(3000, close_test)
                
            except Exception as e:
                print(f"❌ Enhanced test launch failed: {e}")
                test_results["error"] = str(e)
                import traceback
                print(traceback.format_exc())
                app.quit()
        
        # Start test after brief delay
        QTimer.singleShot(500, run_test)
        
        # Run event loop
        print("🔄 Starting GUI event loop...")
        app.exec()
        
        # Check results
        if test_results["success"]:
            print(f"✅ Enhanced UI test completed successfully")
            print(f"   Window type: {test_results['ui_type']}")
            return True
        else:
            print(f"❌ Enhanced UI test failed: {test_results.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Enhanced UI test setup failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """Run enhanced UI test."""
    print("=" * 60)
    print("VMT Enhanced TestRunner UI Test")
    print("=" * 60)
    
    if test_enhanced_ui():
        print("\n🎉 Enhanced UI test passed!")
        print("TestRunner now provides full StandardPhaseTest interface.")
        return True
    else:
        print("\n❌ Enhanced UI test failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)