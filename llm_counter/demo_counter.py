#!/usr/bin/env python3
"""
Simple Token Counter Demo
========================

A basic version that works without external dependencies to demonstrate
core functionality. Uses simple character-based token estimation.

Usage:
    python3 demo_counter.py [--top-files 10]
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
import json
import argparse


class SimpleTokenCounter:
    """Simplified token counter without external dependencies."""
    
    def __init__(self, repo_root=None):
        self.repo_root = Path(repo_root) if repo_root else Path(__file__).parent.parent
        
        # File patterns to include/exclude
        self.include_extensions = {
            '.py', '.md', '.txt', '.json', '.toml', '.yml', '.yaml',
            '.js', '.ts', '.html', '.css', '.sh', '.cfg', '.ini'
        }
        
        self.exclude_dirs = {
            '__pycache__', '.git', '.pytest_cache', 'node_modules',
            'vmt-dev', 'launcher_logs', 'gui_logs', '.vscode', '.mypy_cache'
        }
    
    def should_include_file(self, file_path):
        """Check if file should be included."""
        # Skip excluded directories
        for part in file_path.parts:
            if part in self.exclude_dirs:
                return False
        
        # Include if extension matches or special files
        if file_path.suffix.lower() in self.include_extensions:
            return True
        if file_path.name.lower() in ['makefile', 'license', 'notice']:
            return True
        
        return False
    
    def estimate_tokens(self, content):
        """Simple token estimation: ~4 characters per token."""
        # More sophisticated estimation considering whitespace and punctuation
        words = content.split()
        # Average ~1.3 tokens per word (accounting for subword tokenization)
        return int(len(words) * 1.3)
    
    def get_file_type(self, file_path):
        """Get file type category."""
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()
        
        type_map = {
            '.py': 'Python', '.md': 'Markdown', '.txt': 'Text',
            '.json': 'JSON', '.toml': 'TOML', '.yml': 'YAML', '.yaml': 'YAML',
            '.js': 'JavaScript', '.ts': 'TypeScript', '.html': 'HTML',
            '.css': 'CSS', '.sh': 'Shell', '.cfg': 'Config', '.ini': 'Config'
        }
        
        if suffix in type_map:
            return type_map[suffix]
        elif name in ['makefile', 'license', 'notice']:
            return 'Build/Meta'
        else:
            return 'Other'
    
    def analyze_repository(self, quiet=False):
        """Analyze the repository."""
        if not quiet:
            print(f"🔍 Analyzing repository: {self.repo_root}")
        
        files_data = []
        by_type = defaultdict(int)
        by_dir = defaultdict(int)
        total_tokens = 0
        total_files = 0
        total_size = 0
        
        # Walk through all files
        for root, dirs, files in os.walk(self.repo_root):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                file_path = Path(root) / file
                
                if not self.should_include_file(file_path):
                    continue
                
                try:
                    # Read and analyze file
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    tokens = self.estimate_tokens(content)
                    size = len(content.encode('utf-8'))
                    file_type = self.get_file_type(file_path)
                    
                    # Get relative path
                    try:
                        rel_path = str(file_path.relative_to(self.repo_root))
                    except ValueError:
                        rel_path = str(file_path)
                    
                    files_data.append({
                        'path': rel_path,
                        'tokens': tokens,
                        'size': size,
                        'type': file_type
                    })
                    
                    # Update counters
                    total_tokens += tokens
                    total_files += 1
                    total_size += size
                    by_type[file_type] += tokens
                    by_dir[str(Path(rel_path).parent)] += tokens
                    
                except (UnicodeDecodeError, PermissionError, FileNotFoundError):
                    # Skip files that can't be read
                    continue
        
        # Sort files by token count
        files_data.sort(key=lambda x: x['tokens'], reverse=True)
        
        return {
            'total_tokens': total_tokens,
            'total_files': total_files,
            'total_size': total_size,
            'files': files_data,
            'by_type': dict(by_type),
            'by_directory': dict(by_dir)
        }


def format_number(num):
    """Format number with commas."""
    return f"{num:,}"


def format_bytes(bytes_count):
    """Format bytes in human readable form."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_count < 1024:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024
    return f"{bytes_count:.1f} TB"


def print_analysis(results, top_files=10):
    """Print analysis results."""
    print("\n" + "="*60)
    print("📊 VMT Repository Token Analysis (Demo Version)")
    print("="*60)
    
    # Summary statistics
    print(f"\n📈 Summary:")
    print(f"  Total Tokens:       {format_number(results['total_tokens'])}")
    print(f"  Total Files:        {results['total_files']}")
    print(f"  Total Size:         {format_bytes(results['total_size'])}")
    avg_tokens = results['total_tokens'] // results['total_files'] if results['total_files'] else 0
    print(f"  Average Tokens/File: {avg_tokens}")
    
    # By file type
    print(f"\n📄 By File Type:")
    sorted_types = sorted(results['by_type'].items(), key=lambda x: x[1], reverse=True)
    for file_type, tokens in sorted_types:
        percentage = (tokens / results['total_tokens']) * 100 if results['total_tokens'] else 0
        print(f"  {file_type:<12} {format_number(tokens):>10} tokens ({percentage:4.1f}%)")
    
    # Top directories
    print(f"\n📁 Top Directories:")
    sorted_dirs = sorted(results['by_directory'].items(), key=lambda x: x[1], reverse=True)
    for i, (directory, tokens) in enumerate(sorted_dirs[:10]):
        percentage = (tokens / results['total_tokens']) * 100 if results['total_tokens'] else 0
        dir_name = directory if directory != '.' else '(root)'
        print(f"  {dir_name:<25} {format_number(tokens):>10} tokens ({percentage:4.1f}%)")
    
    # Top files
    print(f"\n🔥 Top {top_files} Largest Files:")
    for i, file_info in enumerate(results['files'][:top_files]):
        print(f"  {i+1:2d}. {file_info['path']:<40} {format_number(file_info['tokens']):>6} tokens ({file_info['type']})")
    
    print("\n" + "="*60)
    print("💡 This is a demo version using simple token estimation.")
    print("   For accurate results, install repotokens and use token_counter.py")
    print("="*60)


def format_for_report(results, top_files=10):
    """Format results for report generation."""
    # Calculate file type stats
    by_file_type = {}
    type_file_counts = defaultdict(int)
    
    for file_info in results['files']:
        file_type = file_info['type']
        type_file_counts[file_type] += 1
    
    for file_type, tokens in results['by_type'].items():
        by_file_type[file_type] = {
            'tokens': tokens,
            'files': type_file_counts[file_type]
        }
    
    # Top files with size in MB
    top_files_list = []
    for file_info in results['files'][:top_files]:
        top_files_list.append({
            'path': file_info['path'],
            'tokens': file_info['tokens'],
            'size_mb': file_info['size'] / (1024 * 1024)
        })
    
    return {
        'summary': {
            'total_tokens': results['total_tokens'],
            'total_files': results['total_files'],
            'total_size_mb': results['total_size'] / (1024 * 1024),
            'average_tokens_per_file': results['total_tokens'] // results['total_files'] if results['total_files'] else 0
        },
        'by_file_type': by_file_type,
        'top_files': top_files_list
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Simple VMT token counter demo')
    parser.add_argument('--top-files', type=int, default=10, 
                       help='Number of top files to show (default: 10)')
    parser.add_argument('--repo-root', type=str, 
                       help='Repository root path (default: parent directory)')
    parser.add_argument('--json', action='store_true',
                       help='Output results as JSON (formatted for report generation)')
    
    args = parser.parse_args()
    
    # Create counter and analyze
    counter = SimpleTokenCounter(args.repo_root)
    results = counter.analyze_repository(quiet=args.json)
    
    if args.json:
        formatted_results = format_for_report(results, args.top_files)
        print(json.dumps(formatted_results, indent=2))
    else:
        print_analysis(results, args.top_files)


if __name__ == '__main__':
    main()