#!/usr/bin/env python3
"""
VMT Repository Token Counter
===========================

A CLI tool for analyzing token counts in the VMT codebase using repotokens.
Provides detailed breakdowns by file type, directory, and overall statistics
to help understand the scope and complexity of the repository for LLM context.

Usage:
    python token_counter.py [--format json|table|summary] [--output file.txt]
    python token_counter.py --by-directory
    python token_counter.py --by-filetype
    python token_counter.py --top-files 10

Examples:
    python token_counter.py                           # Basic summary
    python token_counter.py --format table           # Detailed table
    python token_counter.py --by-directory           # Group by directory
    python token_counter.py --top-files 20           # Show top 20 largest files
    python token_counter.py --output analysis.json   # Save to file
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
from collections import defaultdict
from contextlib import redirect_stderr
import io

try:
    import click
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.tree import Tree
    from rich.panel import Panel
    import repotokens
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install -r requirements.txt")
    sys.exit(1)


@dataclass
class FileTokenInfo:
    """Information about tokens in a single file."""
    path: str
    tokens: int
    size_bytes: int
    file_type: str


@dataclass
class AnalysisResult:
    """Complete token analysis results."""
    total_tokens: int
    total_files: int
    total_size_bytes: int
    files: List[FileTokenInfo]
    by_directory: Dict[str, int]
    by_filetype: Dict[str, int]
    largest_files: List[FileTokenInfo]


class VMTTokenCounter:
    """Token counter for VMT repository analysis."""
    
    def __init__(self, repo_root: Optional[Path] = None):
        """Initialize counter with repository root."""
        self.repo_root = repo_root or Path(__file__).parent.parent
        self.console = Console()
        
        # File patterns to include/exclude
        self.include_patterns = [
            "*.py", "*.md", "*.txt", "*.json", "*.toml", "*.yml", "*.yaml",
            "*.js", "*.ts", "*.html", "*.css", "*.sh", "*.bat", "*.Makefile",
            "Makefile", "*.cfg", "*.ini", "*.log"
        ]
        
        self.exclude_patterns = [
            "__pycache__", ".git", ".pytest_cache", "node_modules",
            "*.pyc", "*.pyo", "vmt-dev", "launcher_logs", "gui_logs",
            ".mypy_cache"
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
        
        # Include if matches include patterns or is a text file
        for pattern in self.include_patterns:
            if pattern.startswith('*.') and file_path.suffix == pattern[1:]:
                return True
            elif pattern == file_path.name:  # Exact match (like Makefile)
                return True
        
        # Try to detect if it's a text file
        try:
            if file_path.is_file() and file_path.stat().st_size < 1024 * 1024:  # < 1MB
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.read(100)  # Try to read first 100 chars
                return True
        except (UnicodeDecodeError, PermissionError, OSError):
            pass
        
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
    
    def count_tokens_in_file(self, file_path: Path, quiet: bool = False) -> int:
        """Count tokens in a single file."""
        try:
            # Use repotokens to count tokens (pass file path, not content)
            if quiet:
                # Suppress stdout/stderr from repotokens for clean JSON output
                with redirect_stderr(io.StringIO()):
                    old_stdout = sys.stdout
                    sys.stdout = io.StringIO()
                    try:
                        token_count = repotokens.count_tokens(str(file_path))
                    finally:
                        sys.stdout = old_stdout
                return token_count
            else:
                token_count = repotokens.count_tokens(str(file_path))
                return token_count
            
        except Exception as e:
            # If repotokens fails, fall back to simple estimation
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                # Rough estimation: ~4 characters per token
                return len(content) // 4
            except:
                return 0
    
    def analyze_repository(self, quiet: bool = False) -> AnalysisResult:
        """Perform complete token analysis of the repository."""
        files_info = []
        by_directory = defaultdict(int)
        by_filetype = defaultdict(int)
        total_tokens = 0
        total_size = 0
        
        # Find all files to analyze
        all_files = []
        for root, dirs, files in os.walk(self.repo_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(
                pattern.strip('*') in d for pattern in self.exclude_patterns 
                if not pattern.startswith('*.')
            )]
            
            for file in files:
                file_path = Path(root) / file
                if self.should_include_file(file_path):
                    all_files.append(file_path)
        
        # Analyze files with progress bar (if not quiet)
        if not quiet:
            progress_ctx = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            )
        else:
            # Dummy context manager for quiet mode
            from contextlib import nullcontext
            progress_ctx = nullcontext()
        
        with progress_ctx as progress:
            if not quiet:
                task = progress.add_task(f"Analyzing {len(all_files)} files...", total=len(all_files))
            
            for file_path in all_files:
                try:
                    tokens = self.count_tokens_in_file(file_path, quiet=quiet)
                    size = file_path.stat().st_size
                    file_type = self.get_file_type(file_path)
                    
                    # Get relative path for display
                    try:
                        rel_path = str(file_path.relative_to(self.repo_root))
                    except ValueError:
                        rel_path = str(file_path)
                    
                    file_info = FileTokenInfo(
                        path=rel_path,
                        tokens=tokens,
                        size_bytes=size,
                        file_type=file_type
                    )
                    
                    files_info.append(file_info)
                    
                    # Update counters
                    total_tokens += tokens
                    total_size += size
                    by_directory[str(Path(rel_path).parent)] += tokens
                    by_filetype[file_type] += tokens
                    
                except Exception as e:
                    # Skip files that cause errors
                    pass
                
                if not quiet:
                    progress.advance(task)
        
        # Sort files by token count
        files_info.sort(key=lambda x: x.tokens, reverse=True)
        
        return AnalysisResult(
            total_tokens=total_tokens,
            total_files=len(files_info),
            total_size_bytes=total_size,
            files=files_info,
            by_directory=dict(by_directory),
            by_filetype=dict(by_filetype),
            largest_files=files_info[:20]
        )


def format_number(num: int) -> str:
    """Format number with thousands separators."""
    return f"{num:,}"


def format_bytes(bytes_count: int) -> str:
    """Format byte count in human-readable form."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_count < 1024:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024
    return f"{bytes_count:.1f} TB"


@click.command()
@click.option('--format', 'output_format', type=click.Choice(['json', 'table', 'summary']), 
              default='summary', help='Output format')
@click.option('--by-directory', is_flag=True, help='Group results by directory')
@click.option('--by-filetype', is_flag=True, help='Group results by file type')
@click.option('--top-files', type=int, help='Show top N files by token count')
@click.option('--output', type=click.Path(), help='Save output to file')
@click.option('--repo-root', type=click.Path(exists=True), help='Repository root path')
def main(output_format: str, by_directory: bool, by_filetype: bool, 
         top_files: Optional[int], output: Optional[str], repo_root: Optional[str]):
    """Analyze token counts in the VMT repository."""
    
    # For JSON output, suppress all console messages to ensure clean JSON to stdout
    console = Console(quiet=(output_format == 'json' and not output), file=sys.stderr if output_format == 'json' else None)
    
    # Initialize counter
    root_path = Path(repo_root) if repo_root else None
    counter = VMTTokenCounter(root_path)
    
    if output_format != 'json' or output:
        console.print("🔍 VMT Repository Token Analysis", style="bold blue")
        console.print(f"Repository: {counter.repo_root}", style="dim")
    
    # Perform analysis
    if output_format != 'json' or output:
        with console.status("Analyzing repository..."):
            results = counter.analyze_repository()
    else:
        # Silent analysis for JSON stdout
        results = counter.analyze_repository(quiet=True)
    
    # Generate output
    output_content = None
    
    if output_format == 'json':
        # JSON output - compatible with generate_report.py format
        # Count files per type
        type_file_counts = defaultdict(int)
        for f in results.files:
            type_file_counts[f.file_type] += 1
        
        json_data = {
            'summary': {
                'total_tokens': results.total_tokens,
                'total_files': results.total_files,
                'total_size_mb': results.total_size_bytes / (1024 * 1024),
                'average_tokens_per_file': results.total_tokens / results.total_files if results.total_files > 0 else 0
            },
            'by_file_type': {
                file_type: {
                    'tokens': tokens,
                    'files': type_file_counts[file_type]
                }
                for file_type, tokens in results.by_filetype.items()
            },
            'top_files': [
                {
                    'path': f.path,
                    'tokens': f.tokens,
                    'size_mb': f.size_bytes / (1024 * 1024)
                }
                for f in sorted(results.files, key=lambda x: x.tokens, reverse=True)[:20]
            ],
            'by_directory': results.by_directory
        }
        output_content = json.dumps(json_data, indent=2)
        if not output:
            print(output_content)  # Use print for clean JSON output to stdout
    
    elif output_format == 'table':
        # Detailed table output
        table = Table(title="VMT Repository Token Analysis")
        table.add_column("File", style="cyan", no_wrap=False)
        table.add_column("Tokens", justify="right", style="magenta")
        table.add_column("Size", justify="right", style="green")
        table.add_column("Type", style="yellow")
        
        display_files = results.files[:50]  # Limit to top 50
        for file_info in display_files:
            table.add_row(
                file_info.path,
                format_number(file_info.tokens),
                format_bytes(file_info.size_bytes),
                file_info.file_type
            )
        
        console.print(table)
        
        # Summary panel
        summary_panel = Panel(
            f"Total: {format_number(results.total_tokens)} tokens in {results.total_files} files "
            f"({format_bytes(results.total_size_bytes)})",
            title="Summary",
            style="bold blue"
        )
        console.print(summary_panel)
    
    else:
        # Summary output (default)
        console.print("\n📊 Analysis Results", style="bold green")
        
        # Main statistics
        stats_table = Table(show_header=False, box=None)
        stats_table.add_row("Total Tokens:", f"[bold]{format_number(results.total_tokens)}[/bold]")
        stats_table.add_row("Total Files:", f"{results.total_files}")
        stats_table.add_row("Total Size:", f"{format_bytes(results.total_size_bytes)}")
        stats_table.add_row("Average Tokens/File:", f"{results.total_tokens // results.total_files if results.total_files else 0}")
        
        console.print(stats_table)
    
    # Additional breakdowns if requested
    if by_directory or (output_format == 'summary' and not by_filetype and not top_files):
        console.print("\n📁 By Directory", style="bold yellow")
        dir_table = Table()
        dir_table.add_column("Directory", style="cyan")
        dir_table.add_column("Tokens", justify="right", style="magenta")
        dir_table.add_column("% of Total", justify="right", style="green")
        
        sorted_dirs = sorted(results.by_directory.items(), key=lambda x: x[1], reverse=True)
        for directory, tokens in sorted_dirs[:15]:  # Top 15 directories
            percentage = (tokens / results.total_tokens) * 100 if results.total_tokens else 0
            dir_table.add_row(directory, format_number(tokens), f"{percentage:.1f}%")
        
        console.print(dir_table)
    
    if by_filetype or (output_format == 'summary' and not by_directory and not top_files):
        console.print("\n📄 By File Type", style="bold yellow")
        type_table = Table()
        type_table.add_column("File Type", style="cyan")
        type_table.add_column("Files", justify="right", style="blue")
        type_table.add_column("Tokens", justify="right", style="magenta")
        type_table.add_column("% of Total", justify="right", style="green")
        
        # Count files by type
        files_by_type = defaultdict(int)
        for file_info in results.files:
            files_by_type[file_info.file_type] += 1
        
        sorted_types = sorted(results.by_filetype.items(), key=lambda x: x[1], reverse=True)
        for file_type, tokens in sorted_types:
            file_count = files_by_type[file_type]
            percentage = (tokens / results.total_tokens) * 100 if results.total_tokens else 0
            type_table.add_row(
                file_type, 
                str(file_count),
                format_number(tokens), 
                f"{percentage:.1f}%"
            )
        
        console.print(type_table)
    
    if top_files or (output_format == 'summary' and not by_directory and not by_filetype):
        count = top_files or 10
        console.print(f"\n🔥 Top {count} Largest Files", style="bold yellow")
        top_table = Table()
        top_table.add_column("File", style="cyan", no_wrap=False)
        top_table.add_column("Tokens", justify="right", style="magenta")
        top_table.add_column("Type", style="yellow")
        
        for file_info in results.largest_files[:count]:
            top_table.add_row(
                file_info.path,
                format_number(file_info.tokens),
                file_info.file_type
            )
        
        console.print(top_table)
    
    # Save to file if requested
    if output and output_content:
        with open(output, 'w') as f:
            f.write(output_content)
        console.print(f"\n💾 Results saved to: {output}", style="green")


if __name__ == '__main__':
    main()