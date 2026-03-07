#!/bin/bash
# Quick install script for Document Intelligence Refinery Demo

set -e

echo "🚀 Document Intelligence Refinery - Demo Setup"
echo "=============================================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

echo "✅ uv is installed"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "🔧 Creating virtual environment..."
    uv venv .venv
fi

echo "✅ Virtual environment ready"
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Install demo dependencies
echo "📥 Installing demo dependencies..."
uv pip install -e ".[demo]"

echo ""
echo "✅ Installation complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. Activate the environment: source .venv/bin/activate"
echo "   2. Run the demo: streamlit run streamlit_app.py"
echo "   3. Upload a PDF and explore the 4-stage pipeline!"
echo ""
echo "📚 For more details, see DEMO_GUIDE.md"
