#!/usr/bin/env python3
"""
VMT Token Analysis Report Generator
==================================

Simple CLI command to run token analysis and generate a markdown report.

Usage:
    python3 generate_report.py [--output FILENAME]
    
Examples:
    python3 generate_report.py
    python3 generate_report.py --output custom_report.md
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
import json
import subprocess

def run_full_analysis():
    """Run the full token counter with repotokens and capture its output."""
    try:
        # Run token_counter.py with JSON output
        result = subprocess.run([
            sys.executable, 'token_counter.py', '--format', 'json'
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode != 0:
            print(f"Error running token_counter.py: {result.stderr}")
            print("Falling back to demo version...")
            return run_demo_analysis()
            
        # Parse JSON output
        analysis_data = json.loads(result.stdout)
        analysis_data['analysis_method'] = 'full'
        return analysis_data
        
    except Exception as e:
        print(f"Failed to run full analysis: {e}")
        print("Falling back to demo version...")
        return run_demo_analysis()

def run_demo_analysis():
    """Run the demo counter and capture its output as structured data."""
    try:
        # Run demo_counter.py and capture output
        result = subprocess.run([
            sys.executable, 'demo_counter.py', '--json'
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode != 0:
            print(f"Error running demo_counter.py: {result.stderr}")
            return None
            
        # Parse JSON output
        analysis_data = json.loads(result.stdout)
        analysis_data['analysis_method'] = 'demo'
        return analysis_data
        
    except Exception as e:
        print(f"Failed to run analysis: {e}")
        return None

def format_number(num):
    """Format numbers with appropriate suffixes."""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return str(num)

def format_percentage(value, total):
    """Format percentage with one decimal place."""
    if total == 0:
        return "0.0%"
    return f"{(value / total * 100):.1f}%"

def generate_markdown_report(analysis_data):
    """Generate a markdown report from analysis data."""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    analysis_method = analysis_data.get('analysis_method', 'demo')
    
    # Extract data
    summary = analysis_data.get('summary', {})
    by_type = analysis_data.get('by_file_type', {})
    top_files = analysis_data.get('top_files', [])
    
    total_tokens = summary.get('total_tokens', 0)
    total_files = summary.get('total_files', 0)
    total_size = summary.get('total_size_mb', 0)
    avg_tokens = summary.get('average_tokens_per_file', 0)
    
    report = f"""# VMT Repository Token Analysis Report

*Generated on {timestamp}*

## 📊 Executive Summary

| Metric | Value |
|--------|--------|
| **Total Tokens** | {format_number(total_tokens)} tokens |
| **Total Files** | {total_files:,} files |
| **Repository Size** | {total_size:.1f} MB |
| **Average Tokens/File** | {avg_tokens:.0f} tokens |

## 📄 File Type Breakdown

"""

    # Add file type breakdown table
    if by_type:
        report += "| File Type | Token Count | Percentage | Files |\n"
        report += "|-----------|-------------|------------|-------|\n"
        
        # Sort by token count (descending)
        sorted_types = sorted(by_type.items(), key=lambda x: x[1]['tokens'], reverse=True)
        
        for file_type, data in sorted_types:
            tokens = data.get('tokens', 0)
            files = data.get('files', 0)
            percentage = format_percentage(tokens, total_tokens)
            
            report += f"| {file_type} | {format_number(tokens)} | {percentage} | {files} |\n"

    # Add top files section
    if top_files:
        report += f"\n## 🔥 Top {len(top_files)} Largest Files\n\n"
        report += "| File | Tokens | Size |\n"
        report += "|------|--------|------|\n"
        
        for file_info in top_files:
            path = file_info.get('path', 'Unknown')
            tokens = file_info.get('tokens', 0)
            size_mb = file_info.get('size_mb', 0)
            
            # Truncate long paths
            display_path = path
            if len(path) > 60:
                display_path = "..." + path[-57:]
            
            report += f"| `{display_path}` | {format_number(tokens)} | {size_mb:.1f} MB |\n"

    # Add context interpretation
    report += f"""

## 🤖 LLM Context Analysis

### Context Window Compatibility

| Model | Context Window | VMT Coverage |
|-------|---------------|--------------|
| GPT-4 | ~128K tokens | {format_percentage(128_000, total_tokens)} |
| Claude 3 | ~200K tokens | {format_percentage(200_000, total_tokens)} |
| Claude 3.5 Sonnet | ~200K tokens | {format_percentage(200_000, total_tokens)} |

### Recommendations

- **Full Repository**: {format_number(total_tokens)} tokens requires chunking for any LLM
- **Focused Analysis**: Select 25-40% of files for single-context analysis
- **Code Reviews**: Use token counts to prioritize which files to include
- **Documentation**: {format_percentage(by_type.get('Markdown', {}).get('tokens', 0), total_tokens)} of tokens are documentation

## 📈 Analysis Metadata

- **Analysis Tool**: VMT Token Counter ({'full version with repotokens' if analysis_method == 'full' else 'demo version'})
- **Tokenization**: {'Accurate repotokens library' if analysis_method == 'full' else 'Simple estimation (~1.3 tokens/word)'}
- **Files Processed**: {total_files:,} code files
- **Excluded**: Binary files, caches, logs, virtual environments
- **Repository**: VMT EconSim Platform

---

*This report was automatically generated by the VMT Token Counter.*
"""

    return report

def main():
    parser = argparse.ArgumentParser(description="Generate VMT token analysis markdown report")
    parser.add_argument(
        '--output', '-o',
        default='vmt_token_report.md',
        help='Output markdown file name (default: vmt_token_report.md)'
    )
    parser.add_argument(
        '--timestamp', '-t',
        action='store_true',
        help='Add timestamp to output filename'
    )
    parser.add_argument(
        '--full',
        action='store_true',
        default=True,
        help='Use full token counter with repotokens (default: True)'
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Use demo version instead of full counter'
    )
    
    args = parser.parse_args()
    
    # Generate output filename with optional timestamp
    output_filename = args.output
    if args.timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = Path(output_filename).stem
        extension = Path(output_filename).suffix
        output_filename = f"{base_name}_{timestamp}{extension}"
    
    print("🔍 Running VMT token analysis...")
    
    # Run analysis (full or demo)
    if args.demo:
        analysis_data = run_demo_analysis()
    else:
        analysis_data = run_full_analysis()
    
    if not analysis_data:
        print("❌ Failed to run token analysis")
        sys.exit(1)
    
    print("📄 Generating markdown report...")
    
    # Generate report
    report_content = generate_markdown_report(analysis_data)
    
    # Write to file
    output_path = Path(__file__).parent / output_filename
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ Report generated successfully!")
        print(f"📁 Output: {output_path}")
        print(f"📊 Summary: {analysis_data['summary']['total_tokens']:,} tokens across {analysis_data['summary']['total_files']:,} files")
        
    except Exception as e:
        print(f"❌ Failed to write report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()