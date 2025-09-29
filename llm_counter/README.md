# VMT Repository Token Counter

A standalone CLI tool for analyzing token counts in the VMT repository using the `repotokens` library. This helps understand the scope and complexity of the codebase for LLM context analysis.

## Setup

1. Install dependencies:
```bash
cd llm_counter
pip install -r requirements.txt
```

2. Run analysis:
```bash
python token_counter.py
```

## Usage Examples

### Basic Analysis
```bash
python token_counter.py
```
Shows a summary with total tokens, files, and breakdowns by directory and file type.

### Detailed Table View
```bash
python token_counter.py --format table
```
Shows detailed table of all files with token counts.

### JSON Output
```bash
python token_counter.py --format json --output analysis.json
```
Exports complete analysis to JSON file.

### Top Files Analysis
```bash
python token_counter.py --top-files 20
```
Shows the 20 largest files by token count.

### Directory Breakdown
```bash
python token_counter.py --by-directory
```
Groups results by directory.

### File Type Breakdown
```bash
python token_counter.py --by-filetype
```
Groups results by file type (Python, Markdown, etc.).

### Custom Repository Root
```bash
python token_counter.py --repo-root /path/to/other/repo
```
Analyze a different repository.

## Features

- **Accurate Token Counting**: Uses `repotokens` library for precise token estimation
- **File Type Detection**: Automatically categorizes files (Python, Markdown, JSON, etc.)
- **Smart Filtering**: Excludes binary files, caches, logs, and virtual environments
- **Multiple Output Formats**: Summary, table, and JSON formats
- **Rich CLI Interface**: Beautiful terminal output with progress bars and tables
- **Flexible Analysis**: Group by directory, file type, or show top files

## File Inclusion Rules

The tool includes:
- Source code files (`.py`, `.js`, `.ts`, `.html`, `.css`)
- Documentation (`.md`, `.txt`, `.rst`)
- Configuration files (`.json`, `.toml`, `.yml`, `.cfg`, `.ini`)
- Build files (`Makefile`, shell scripts)
- Text-based files under 1MB

The tool excludes:
- Binary files and large files (>1MB)
- Cache directories (`__pycache__`, `.pytest_cache`, `.mypy_cache`)
- Virtual environments (`vmt-dev`, `node_modules`)
- Log files in `launcher_logs/` and `gui_logs/`
- Git metadata (`.git/`)

## Sample Output

```
🔍 VMT Repository Token Analysis
Repository: /home/user/PROJECTS/vmt

📊 Analysis Results
Total Tokens:     125,437
Total Files:      245  
Total Size:       2.1 MB
Average Tokens/File: 512

📁 By Directory
src/                     67,234 tokens  (53.6%)
docs/                    23,156 tokens  (18.5%)
tests/                   18,923 tokens  (15.1%)
MANUAL_TESTS/           12,445 tokens  (9.9%)
...

📄 By File Type  
Python                   89,234 tokens  (71.2%)
Markdown                 21,456 tokens  (17.1%)
JSON                     8,923 tokens   (7.1%)
...

🔥 Top 10 Largest Files
src/econsim/tools/launcher/app_window.py    3,245 tokens
src/econsim/simulation/world.py             2,891 tokens
docs/launcher_architecture.md               2,456 tokens
...
```

## Integration with VMT

This tool is completely standalone and doesn't interfere with the VMT codebase. It can be run independently to analyze token counts for:

- **LLM Context Planning**: Understanding how much of the codebase fits in context
- **Code Review**: Identifying large files that might need refactoring
- **Documentation**: Measuring documentation coverage vs code ratio
- **CI/CD**: Tracking codebase growth over time

## Dependencies

- `repotokens`: Accurate token counting for various LLM tokenizers
- `click`: CLI interface framework
- `rich`: Beautiful terminal output with tables and progress bars