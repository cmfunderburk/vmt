# VMT Repository Token Counter

## Quick Start (Demo Version)

For a quick analysis without installing dependencies:

```bash
cd llm_counter
python3 demo_counter.py
```

### Generate Markdown Report

Create a formatted markdown report with analysis results:

```bash
# Generate report with default filename (vmt_token_report.md)
python3 generate_report.py

# Generate report with custom filename
python3 generate_report.py --output my_analysis.md
```

The report includes:
- Executive summary with key metrics
- File type breakdown with percentages
- Top largest files
- LLM context compatibility analysis
- Development recommendations

## Full Version Setup

1. **Install dependencies**:
```bash
cd llm_counter
pip install -r requirements.txt
# OR run the setup script
./setup.sh
```

### Adding to VMT Makefile (maybe later)

You could add token analysis to the main VMT Makefile:

```makefile
token-analysis:
	@echo "🔍 Running token analysis..."
	cd llm_counter && python3 demo_counter.py

token-analysis-full:
	@echo "🔍 Running detailed token analysis..."
	cd llm_counter && python3 token_counter.py --format table

token-report:
	@echo "📄 Generating token analysis report..."
	cd llm_counter && python3 generate_report.py
	@echo "Report saved to llm_counter/vmt_token_report.md"
```

## Files Overview

- `token_counter.py` - Full-featured CLI tool (requires dependencies)
- `demo_counter.py` - Standalone demo version (no dependencies)
- `generate_report.py` - CLI tool to generate markdown reports
- `test_counter.py` - Unit tests for core logic
- `requirements.txt` - Python dependencies
- `setup.sh` - Quick setup script
- `README.md` - Detailed documentation
- `vmt_token_report.md` - Generated analysis report (created by generate_report.py)

## Key Features

✅ **Accurate Token Counting** - Uses repotokens library for precise estimation  
✅ **Smart File Filtering** - Excludes caches, logs, binaries automatically  
✅ **Multiple Output Formats** - Summary, table, JSON export  
✅ **Rich CLI Interface** - Beautiful terminal output with progress bars  
✅ **Zero Dependencies Demo** - Works immediately without installation  
✅ **Comprehensive Analysis** - File types, directories, top files  
✅ **VMT-Aware Filtering** - Knows about vmt-dev, launcher_logs, etc.  

## Token Count Interpretation

For LLM context planning:

- **GPT-4**: ~128K tokens context window
- **Claude 3**: ~200K tokens context window  
- **Current VMT**: ~483K total tokens

This means:
- You can fit ~25-40% of VMT in a single context window
- Focus on specific modules/components for detailed analysis  
- Use token counts to prioritize which files to include
- Great for targeted code reviews and feature development

The token counter helps optimize AI-assisted development by showing exactly what fits in context and what needs to be broken down into smaller chunks.