"""
Test to prevent reintroduction of legacy symbols after refactor completion.

This test ensures that removed legacy components don't accidentally get
reintroduced during future development.
"""
from pathlib import Path

import pytest


class TestNoLegacySymbols:
    """Prevent reintroduction of removed legacy symbols."""
    
    def test_no_legacy_enhanced_test_launcher_class(self):
        """Ensure EnhancedTestLauncher class is not present in active code."""
        repo_root = Path(__file__).parent.parent.parent.parent
        
        # Search for the legacy class name in Python files
        # Exclude backup files and archived directories
        search_paths = [
            "src/",
            "MANUAL_TESTS/enhanced_test_launcher_v2.py",
        ]
        
        banned_symbol = "class EnhancedTestLauncher"
        
        for search_path in search_paths:
            full_path = repo_root / search_path
            if not full_path.exists():
                continue
                
            if full_path.is_file():
                # Search single file
                content = full_path.read_text()
                assert banned_symbol not in content, (
                    f"Legacy symbol '{banned_symbol}' found in {search_path}. "
                    "This symbol should have been removed during Phase 4 cleanup."
                )
            else:
                # Search directory recursively
                for py_file in full_path.rglob("*.py"):
                    # Skip backup/archived files
                    if any(skip in str(py_file) for skip in ["backup", "archived", "__pycache__"]):
                        continue
                        
                    content = py_file.read_text()
                    assert banned_symbol not in content, (
                        f"Legacy symbol '{banned_symbol}' found in {py_file}. "
                        "This symbol should have been removed during Phase 4 cleanup."
                    )
    
    def test_no_legacy_fallback_imports(self):
        """Ensure launcher module fallback patterns are removed."""
        repo_root = Path(__file__).parent.parent.parent.parent
        launcher_file = repo_root / "MANUAL_TESTS/enhanced_test_launcher_v2.py"
        
        if not launcher_file.exists():
            pytest.skip("Launcher file not found")
            
        content = launcher_file.read_text()
        
        # Check for specific legacy launcher fallback patterns that should be removed
        legacy_patterns = [
            "_launcher_modules_available",
            "if _launcher_modules_available:",
            "# Fallback to legacy EnhancedTestLauncher",
        ]
        
        for pattern in legacy_patterns:
            assert pattern not in content, (
                f"Legacy fallback pattern '{pattern}' found in launcher. "
                "Fallback logic should have been removed during Phase 4 cleanup."
            )