#!/usr/bin/env python3
"""
Legacy System Audit Script
Analyzes the codebase for deprecated systems and generates migration recommendations.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class LegacyUsage:
    """Represents a single instance of legacy system usage."""
    file_path: str
    line_number: int
    line_content: str
    usage_type: str
    severity: str  # 'low', 'medium', 'high'
    migration_suggestion: str


@dataclass
class LegacyAuditReport:
    """Complete audit report of legacy system usage."""
    total_files_scanned: int
    legacy_usages: List[LegacyUsage]
    summary_by_type: Dict[str, int]
    summary_by_severity: Dict[str, int]
    recommendations: List[str]


class LegacyAuditor:
    """Analyzes codebase for legacy system usage patterns."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.patterns = self._compile_patterns()
        
    def _compile_patterns(self) -> Dict[str, Tuple[re.Pattern, str, str]]:
        """Compile regex patterns for legacy system detection."""
        return {
            'gui_logger_import': (
                re.compile(r'from\s+.*debug_logger\s+import|import\s+.*debug_logger'),
                'high',
                'Replace with observer pattern: from econsim.observability import FileObserver'
            ),
            'gui_logger_usage': (
                re.compile(r'GUILogger\(|\.log_|debug_logger\.'),
                'high', 
                'Replace with observer events and registry.notify()'
            ),
            'legacy_random_flag': (
                re.compile(r'ECONSIM_LEGACY_RANDOM'),
                'medium',
                'Remove entirely - flag is deprecated and ignored'
            ),
            'use_decision_false': (
                re.compile(r'use_decision\s*=\s*False'),
                'medium',
                'Change to use_decision=True - legacy mode is deprecated'
            ),
            'legacy_gui_flag': (
                re.compile(r'ECONSIM_NEW_GUI\s*=\s*["\']?0|should_use_new_gui.*False'),
                'medium',
                'Remove - consolidate to enhanced GUI only'
            ),
            'deprecated_warnings': (
                re.compile(r'warnings\.warn.*deprecated|DEPRECATED'),
                'low',
                'Review for removal after migration period'
            ),
            'legacy_adapter': (
                re.compile(r'LegacyLoggerAdapter|legacy_adapter|create_legacy_adapter'),
                'high',
                'Bridge component - remove after GUILogger migration'
            ),
            'xfail_determinism': (
                re.compile(r'@pytest\.mark\.xfail.*determinism|determinism.*xfail'),
                'low',
                'Update with new baseline hashes after architecture stabilization'
            ),
        }
    
    def scan_file(self, file_path: Path) -> List[LegacyUsage]:
        """Scan a single file for legacy system usage."""
        usages = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    for pattern_name, (pattern, severity, suggestion) in self.patterns.items():
                        if pattern.search(line):
                            usages.append(LegacyUsage(
                                file_path=str(file_path.relative_to(self.workspace_root)),
                                line_number=line_num,
                                line_content=line.strip(),
                                usage_type=pattern_name,
                                severity=severity,
                                migration_suggestion=suggestion
                            ))
        except (UnicodeDecodeError, PermissionError):
            # Skip binary files or files we can't read
            pass
            
        return usages
    
    def scan_workspace(self) -> LegacyAuditReport:
        """Scan entire workspace for legacy system usage."""
        all_usages = []
        files_scanned = 0
        
        # Scan Python files
        for py_file in self.workspace_root.rglob('*.py'):
            if self._should_skip_file(py_file):
                continue
                
            files_scanned += 1
            usages = self.scan_file(py_file)
            all_usages.extend(usages)
        
        # Scan other relevant files (Makefile, README, etc.)
        for pattern in ['Makefile', '*.md', '*.toml']:
            for file_path in self.workspace_root.rglob(pattern):
                if self._should_skip_file(file_path):
                    continue
                    
                files_scanned += 1
                usages = self.scan_file(file_path)
                all_usages.extend(usages)
        
        # Generate summaries
        summary_by_type = defaultdict(int)
        summary_by_severity = defaultdict(int)
        
        for usage in all_usages:
            summary_by_type[usage.usage_type] += 1
            summary_by_severity[usage.severity] += 1
        
        recommendations = self._generate_recommendations(all_usages)
        
        return LegacyAuditReport(
            total_files_scanned=files_scanned,
            legacy_usages=all_usages,
            summary_by_type=dict(summary_by_type),
            summary_by_severity=dict(summary_by_severity),
            recommendations=recommendations
        )
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Determine if a file should be skipped during scanning."""
        skip_patterns = [
            '__pycache__', '.git', '.pytest_cache', 'vmt-dev',
            '.mypy_cache', '.ruff_cache', 'node_modules'
        ]
        
        return any(pattern in str(file_path) for pattern in skip_patterns)
    
    def _generate_recommendations(self, usages: List[LegacyUsage]) -> List[str]:
        """Generate prioritized recommendations based on audit results."""
        recommendations = []
        
        # Count high-severity usages
        high_severity = [u for u in usages if u.severity == 'high']
        medium_severity = [u for u in usages if u.severity == 'medium']
        
        if high_severity:
            gui_logger_count = len([u for u in high_severity if 'gui_logger' in u.usage_type])
            if gui_logger_count > 10:
                recommendations.append(
                    f"CRITICAL: {gui_logger_count} GUILogger usages found. "
                    "Create automated migration script before manual conversion."
                )
            
            adapter_count = len([u for u in high_severity if 'legacy_adapter' in u.usage_type])
            if adapter_count > 0:
                recommendations.append(
                    f"HIGH: {adapter_count} legacy adapter usages found. "
                    "These can be removed after GUILogger migration is complete."
                )
        
        if medium_severity:
            flag_count = len([u for u in medium_severity if 'flag' in u.usage_type])
            if flag_count > 5:
                recommendations.append(
                    f"MEDIUM: {flag_count} deprecated environment flag usages found. "
                    "These can be safely removed immediately."
                )
        
        # Migration prioritization
        recommendations.append(
            "RECOMMENDED MIGRATION ORDER:\n"
            "1. Remove deprecated environment flags (low risk)\n" 
            "2. Update use_decision=False parameters (medium risk)\n"
            "3. Consolidate GUI paths (medium risk)\n"
            "4. Migrate GUILogger usage (high risk)"
        )
        
        return recommendations


def main():
    """Main audit execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Audit legacy system usage in VMT EconSim')
    parser.add_argument('--workspace', type=Path, default=Path('.'),
                       help='Path to workspace root (default: current directory)')
    parser.add_argument('--output', type=Path, 
                       help='Output file for JSON report (default: stdout)')
    parser.add_argument('--format', choices=['json', 'text'], default='text',
                       help='Output format (default: text)')
    
    args = parser.parse_args()
    
    auditor = LegacyAuditor(args.workspace)
    report = auditor.scan_workspace()
    
    if args.format == 'json':
        output_data = asdict(report)
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(output_data, f, indent=2)
        else:
            print(json.dumps(output_data, indent=2))
    else:
        # Text format
        print("🔍 VMT EconSim Legacy System Audit Report")
        print("=" * 50)
        print(f"Files scanned: {report.total_files_scanned}")
        print(f"Legacy usages found: {len(report.legacy_usages)}")
        print()
        
        print("📊 Summary by Type:")
        for usage_type, count in sorted(report.summary_by_type.items()):
            print(f"  {usage_type}: {count}")
        print()
        
        print("⚠️  Summary by Severity:")
        for severity, count in sorted(report.summary_by_severity.items(), 
                                    key=lambda x: {'high': 3, 'medium': 2, 'low': 1}[x[0]], reverse=True):
            print(f"  {severity.upper()}: {count}")
        print()
        
        # Show high-priority items
        high_priority = [u for u in report.legacy_usages if u.severity == 'high']
        if high_priority:
            print("🚨 HIGH PRIORITY ITEMS:")
            for usage in high_priority[:10]:  # Limit output
                print(f"  {usage.file_path}:{usage.line_number} - {usage.usage_type}")
                print(f"    → {usage.migration_suggestion}")
            if len(high_priority) > 10:
                print(f"    ... and {len(high_priority) - 10} more")
            print()
        
        print("💡 RECOMMENDATIONS:")
        for rec in report.recommendations:
            print(f"  {rec}")


if __name__ == '__main__':
    main()