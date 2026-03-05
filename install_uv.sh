#!/bin/bash
# Fast installation using uv package manager
# uv is 10-100× faster than pip

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Document Intelligence Refinery - UV Installation        ║"
echo "║   Fast dependency management with uv                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "⚠ uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo "✓ uv installed"
else
    echo "✓ uv already installed ($(uv --version))"
fi
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version detected"
echo ""

# Create/sync virtual environment with uv
echo "Creating virtual environment with uv..."
uv venv .venv
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
source .venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

echo "════════════════════════════════════════════════════════════"
echo "INSTALLATION OPTIONS"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Choose installation profile:"
echo ""
echo "1. Minimal      - Core only (pdfplumber, PyMuPDF)"
echo "2. Tier 1       - + Camelot, Docling (native PDFs)"
echo "3. Tier 2       - + Gemini API (scanned PDFs)"
echo "4. Full         - All features (Tier 1 + Tier 2 + PageIndex + Query)"
echo "5. Development  - Full + dev tools"
echo ""
read -p "Select profile [1-5] (default: 4): " profile
profile=${profile:-4}

echo ""
echo "════════════════════════════════════════════════════════════"
echo "INSTALLING DEPENDENCIES"
echo "════════════════════════════════════════════════════════════"
echo ""

case $profile in
    1)
        echo "Installing minimal dependencies..."
        uv pip install -e .
        ;;
    2)
        echo "Installing Tier 1 dependencies..."
        uv pip install -e ".[tier1]"
        ;;
    3)
        echo "Installing Tier 2 dependencies..."
        uv pip install -e ".[tier1,tier2]"
        ;;
    4)
        echo "Installing full dependencies..."
        uv pip install -e ".[all]"
        ;;
    5)
        echo "Installing development dependencies..."
        uv pip install -e ".[all,dev]"
        ;;
    *)
        echo "Invalid selection. Installing full dependencies..."
        uv pip install -e ".[all]"
        ;;
esac

echo ""
echo "✓ Dependencies installed"
echo ""

# Create necessary directories
echo "Creating project directories..."
mkdir -p data
mkdir -p .refinery/{profiles,pageindex,ldus,docling_cache}
mkdir -p tests/{unit,integration}
mkdir -p logs
echo "✓ Directories created"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
# API Keys
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Paths
DATA_DIR=./data
OUTPUT_DIR=./.refinery

# Configuration
LOG_LEVEL=INFO
MAX_WORKERS=4

# Extraction Settings
CONFIDENCE_THRESHOLD=0.7
MAX_COST_PER_DOCUMENT=1.0
EOF
    echo "✓ .env file created"
    echo "⚠ Please edit .env and add your API keys"
else
    echo "✓ .env file already exists"
fi
echo ""

# Verify installation
echo "════════════════════════════════════════════════════════════"
echo "VERIFICATION"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "Testing imports..."
python3 << 'EOF'
import sys
errors = []

# Core imports
try:
    import pdfplumber
    import fitz  # PyMuPDF
    import pydantic
    import yaml
    print("✓ Core dependencies")
except ImportError as e:
    errors.append(f"Core: {e}")

# Tier 1 imports (optional)
try:
    import camelot
    print("✓ Tier 1 dependencies (Camelot)")
except ImportError:
    print("⊘ Tier 1 dependencies not installed")

try:
    import docling
    print("✓ Tier 1 dependencies (Docling)")
except ImportError:
    print("⊘ Docling not installed (optional)")

# Tier 2 imports (optional)
try:
    import google.generativeai
    print("✓ Tier 2 dependencies (Gemini)")
except ImportError:
    print("⊘ Tier 2 dependencies not installed")

if errors:
    print("\n✗ Some imports failed:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
else:
    print("\n✓ All required imports successful")
EOF

echo ""
echo "Installed packages:"
uv pip list | grep -E "pdfplumber|PyMuPDF|camelot|docling|google-generativeai|faiss|sentence-transformers" || echo "Core packages installed"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✓ INSTALLATION COMPLETE!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Installation profile: $(case $profile in 1) echo 'Minimal';; 2) echo 'Tier 1';; 3) echo 'Tier 2';; 4) echo 'Full';; 5) echo 'Development';; esac)"
echo ""
echo "Next steps:"
echo ""
echo "1. Configure API keys:"
echo "   nano .env"
echo ""
echo "2. Run tests:"
echo "   pytest tests/"
echo ""
echo "3. Try demos:"
echo "   python3 demo_hybrid_pipeline.py"
echo "   python3 demo_stage1.py"
echo "   python3 demo_stage2.py"
echo "   python3 demo_stage3.py"
echo ""
echo "4. Process documents:"
echo "   python3 -m src.main process data/your_document.pdf"
echo ""
echo "Documentation:"
echo "   - QUICKSTART.md                          # Quick start guide"
echo "   - README.md                              # Project overview"
echo "   - docs/HYBRID_PIPELINE_IMPLEMENTATION.md # Architecture"
echo ""
echo "Useful commands:"
echo "   uv pip list                    # List installed packages"
echo "   uv pip install -e '.[dev]'     # Add dev dependencies"
echo "   uv pip sync                    # Sync dependencies"
echo ""
echo "Happy extracting! 🚀"
echo ""
