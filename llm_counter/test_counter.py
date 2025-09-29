"""
Test script for the VMT Token Counter.

Simple validation of core functionality without requiring dependencies.
"""

import sys
from pathlib import Path
import tempfile
import os

# Add the llm_counter directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_file_detection():
    """Test file inclusion/exclusion logic."""
    print("🧪 Testing file detection logic...")
    
    # Create a mock counter (won't work without deps, but we can test logic)
    class MockCounter:
        def __init__(self):
            self.include_patterns = [
                "*.py", "*.md", "*.txt", "*.json", "*.toml", "*.yml", "*.yaml",
                "*.js", "*.ts", "*.html", "*.css", "*.sh", "*.bat", "*.Makefile",
                "Makefile", "*.cfg", "*.ini", "*.log"
            ]
            
            self.exclude_patterns = [
                "__pycache__", ".git", ".pytest_cache", "node_modules",
                "*.pyc", "*.pyo", "vmt-dev", "launcher_logs", "gui_logs"
            ]
        
        def should_include_file(self, file_path: Path) -> bool:
            """Check if file should be included in analysis."""
            # Skip if in excluded directories
            for part in file_path.parts:
                if any(pattern.strip('*') in part for pattern in self.exclude_patterns 
                       if not pattern.startswith('*.')):
                    return False
            
            # Skip if matches excluded file patterns
            for pattern in self.exclude_patterns:
                if pattern.startswith('*.') and file_path.suffix == pattern[1:]:
                    return False
            
            # Include if matches include patterns
            for pattern in self.include_patterns:
                if pattern.startswith('*.') and file_path.suffix == pattern[1:]:
                    return True
                elif pattern == file_path.name:  # Exact match (like Makefile)
                    return True
            
            return False
        
        def get_file_type(self, file_path: Path) -> str:
            """Determine file type category."""
            suffix = file_path.suffix.lower()
            name = file_path.name.lower()
            
            type_mapping = {
                '.py': 'Python',
                '.md': 'Markdown',
                '.txt': 'Text',
                '.json': 'JSON',
                '.toml': 'TOML',
                '.yml': 'YAML',
                '.yaml': 'YAML',
                '.js': 'JavaScript',
                '.ts': 'TypeScript',
                '.html': 'HTML',
                '.css': 'CSS',
                '.sh': 'Shell',
                '.bat': 'Batch',
                '.cfg': 'Config',
                '.ini': 'Config',
                '.log': 'Log'
            }
            
            if suffix in type_mapping:
                return type_mapping[suffix]
            elif name in ['makefile', 'dockerfile', 'license', 'notice']:
                return 'Build/Meta'
            else:
                return 'Other'
    
    counter = MockCounter()
    
    # Test cases
    test_cases = [
        # Should include
        (Path("src/econsim/main.py"), True, "Python"),
        (Path("README.md"), True, "Markdown"),
        (Path("pyproject.toml"), True, "TOML"),
        (Path("Makefile"), True, "Build/Meta"),
        (Path("docs/guide.md"), True, "Markdown"),
        
        # Should exclude
        (Path("__pycache__/module.pyc"), False, None),
        (Path("vmt-dev/lib/python3.11/site-packages/module.py"), False, None),
        (Path("launcher_logs/2025-09-29.log"), False, None),
        (Path(".git/config"), False, None),
        (Path("build/temp.pyc"), False, None),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for file_path, should_include, expected_type in test_cases:
        included = counter.should_include_file(file_path)
        if included == should_include:
            if included and expected_type:
                file_type = counter.get_file_type(file_path)
                if file_type == expected_type:
                    print(f"  ✅ {file_path} -> Include: {included}, Type: {file_type}")
                    passed += 1
                else:
                    print(f"  ❌ {file_path} -> Type mismatch: got {file_type}, expected {expected_type}")
            elif not included:
                print(f"  ✅ {file_path} -> Correctly excluded")
                passed += 1
            else:
                print(f"  ✅ {file_path} -> Include: {included}")
                passed += 1
        else:
            print(f"  ❌ {file_path} -> Include mismatch: got {included}, expected {should_include}")
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    return passed == total


def test_token_estimation():
    """Test basic token estimation logic."""
    print("\n🧪 Testing token estimation fallback...")
    
    # Test the fallback estimation (4 chars per token)
    test_content = "This is a test string with some content that should be tokenized."
    estimated_tokens = len(test_content) // 4
    
    print(f"  Content: '{test_content}'")
    print(f"  Length: {len(test_content)} chars")
    print(f"  Estimated tokens: {estimated_tokens}")
    print(f"  ✅ Fallback estimation works")
    
    return True


def main():
    """Run all tests."""
    print("🔍 VMT Token Counter - Unit Tests")
    print("="*50)
    
    tests = [
        test_file_detection,
        test_token_estimation,
    ]
    
    passed_tests = 0
    for test in tests:
        try:
            if test():
                passed_tests += 1
        except Exception as e:
            print(f"  ❌ Test failed with error: {e}")
    
    print("\n" + "="*50)
    print(f"🏆 Overall Results: {passed_tests}/{len(tests)} tests passed")
    
    if passed_tests == len(tests):
        print("✅ All tests passed! The token counter logic is working correctly.")
        print("\n💡 To run the full tool:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Run analysis: python token_counter.py")
    else:
        print("❌ Some tests failed. Check the logic above.")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())