#!/bin/bash
# Quick setup script for VMT Token Counter

echo "🔧 Setting up VMT Token Counter..."

# Check if we're in the right directory
if [[ ! -f "token_counter.py" ]]; then
    echo "❌ Please run this from the llm_counter/ directory"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

if [[ $? -eq 0 ]]; then
    echo "✅ Setup complete!"
    echo ""
    echo "🚀 Try running:"
    echo "  python token_counter.py"
    echo ""
    echo "📚 For more options:"
    echo "  python token_counter.py --help"
else
    echo "❌ Installation failed. You may need to:"
    echo "   1. Activate a virtual environment"
    echo "   2. Use pip3 instead of pip"
    echo "   3. Install with --user flag: pip install --user -r requirements.txt"
fi