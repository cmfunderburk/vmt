#!/usr/bin/env python3
"""
Phase 1.5 Validation: Test Remaining File Migrations

Validates that all remaining manual test files now use the new framework location.
"""
import sys
import os
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "MANUAL_TESTS"))

def test_remaining_files():
    """Test the remaining files that were migrated in Phase 1.5."""
    print("🔬 Testing Phase 1.5 Migrated Files...")
    
    files_to_test = [
        "test_framework_validation",
        "example_custom_phases", 
        "phase_config_editor",
        "test_custom_phases",
        "live_config_editor"
    ]
    
    failures = []
    for file_name in files_to_test:
        try:
            exec(f"import {file_name}")
            print(f"  ✅ {file_name}")
        except Exception as e:
            print(f"  ❌ {file_name}: {e}")
            failures.append(file_name)
    
    return failures

if __name__ == "__main__":
    print("🚀 Phase 1.5 Validation: Remaining File Migrations")
    print(f"Repository: {repo_root}")
    
    failures = test_remaining_files()
    
    # Summary
    print(f"\n📊 Phase 1.5 Validation Summary:")
    if not failures:
        print("✅ All remaining files migrated successfully!")
        sys.exit(0)
    else:
        print(f"❌ {len(failures)} files failed: {', '.join(failures)}")
        sys.exit(1)