#!/usr/bin/env python3
"""Test TestRunner GUI creation without user interaction.

This creates a test window briefly to validate the complete TestRunner
flow including GUI components, then closes automatically.
"""

import sys
from pathlib import Path

# Add src to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(repo_root / "src"))

def test_gui_creation():
    """Test that TestRunner can create GUI without crashing."""
    print("🔧 Testing GUI creation...")
    
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
        print("✅ TestRunner initialized")
        
        # Track test results
        test_results = {"success": False, "error": None}
        
        def run_test():
            """Run the test and close window after brief delay."""
            try:
                print("🚀 Attempting to launch Test 1...")
                
                # Launch test 1
                runner.run_by_id(1, "framework")
                print("✅ Test launch call succeeded")
                
                # Schedule window close after brief delay
                def close_test():
                    print("🔄 Closing test window...")
                    if runner.current_test_window:
                        runner.current_test_window.close()
                        print("✅ Test window closed")
                    
                    test_results["success"] = True
                    app.quit()
                
                # Close after 2 seconds
                QTimer.singleShot(2000, close_test)
                
            except Exception as e:
                print(f"❌ Test launch failed: {e}")
                test_results["error"] = str(e)
                app.quit()
        
        # Start test after brief delay
        QTimer.singleShot(500, run_test)
        
        # Run event loop
        print("🔄 Starting GUI event loop...")
        app.exec()
        
        # Check results
        if test_results["success"]:
            print("✅ GUI test completed successfully")
            return True
        else:
            print(f"❌ GUI test failed: {test_results.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ GUI test setup failed: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    """Run GUI creation test."""
    print("=" * 60)
    print("VMT TestRunner GUI Test")
    print("=" * 60)
    
    if test_gui_creation():
        print("\n🎉 GUI test passed!")
        print("TestRunner is ready for launcher integration.")
        return True
    else:
        print("\n❌ GUI test failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)