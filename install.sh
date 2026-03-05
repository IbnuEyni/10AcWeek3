#!/bin/bash
# Complete installation script for Document Intelligence Refinery
# Installs all dependencies for Stages 1-5

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Document Intelligence Refinery - Installation Script    ║"
echo "║   Enterprise-grade document extraction pipeline           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version detected"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip -q
echo "✓ pip upgraded"
echo ""

echo "════════════════════════════════════════════════════════════"
echo "CORE DEPENDENCIES"
echo "════════════════════════════════════════════════════════════"
echo ""

# Core Python packages
echo "1. Installing core Python packages..."
pip install pydantic pyyaml python-dotenv rich -q
echo "   ✓ pydantic, pyyaml, python-dotenv, rich"

echo "2. Installing PDF processing libraries..."
pip install pdfplumber PyMuPDF -q
echo "   ✓ pdfplumber (text extraction)"
echo "   ✓ PyMuPDF (layout/figures)"

echo "3. Installing table extraction..."
pip install "camelot-py[cv]" opencv-python -q
echo "   ✓ camelot-py (table extraction)"
echo "   ✓ opencv-python (image processing)"

echo "4. Installing testing framework..."
pip install pytest pytest-cov -q
echo "   ✓ pytest, pytest-cov"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "STAGE-SPECIFIC DEPENDENCIES"
echo "════════════════════════════════════════════════════════════"
echo ""

# Stage 1: Triage (already covered by core)
echo "Stage 1 (Triage): ✓ Already installed"

# Stage 2: Extraction
echo ""
echo "Stage 2 (Extraction) - Optional Components:"
echo "-----------------------------------------------------------"

# Docling (optional, heavy)
read -p "Install Docling for advanced layout analysis? [y/N]: " install_docling
if [[ $install_docling =~ ^[Yy]$ ]]; then
    echo "   Installing Docling (this may take 5-10 minutes)..."
    pip install docling -q
    echo "   ✓ Docling installed (Tier 1 native PDF extraction)"
else
    echo "   ⊘ Skipping Docling (will use pdfplumber only)"
fi

# Vision APIs
read -p "Install Gemini API for scanned PDFs? [y/N]: " install_gemini
if [[ $install_gemini =~ ^[Yy]$ ]]; then
    echo "   Installing Google Generative AI..."
    pip install google-generativeai -q
    echo "   ✓ Gemini API client installed (Tier 2 scanned PDFs)"
else
    echo "   ⊘ Skipping Gemini (Tier 2 will be limited)"
fi

# Tesseract (fallback OCR)
read -p "Install Tesseract OCR (fallback)? [y/N]: " install_tesseract
if [[ $install_tesseract =~ ^[Yy]$ ]]; then
    echo "   Installing pytesseract..."
    pip install pytesseract -q
    echo "   ✓ pytesseract installed"
    echo "   ⚠ Note: You also need to install Tesseract system package:"
    echo "     Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "     macOS: brew install tesseract"
else
    echo "   ⊘ Skipping Tesseract"
fi

# Stage 3: Chunking (already covered by core)
echo ""
echo "Stage 3 (Semantic Chunking): ✓ Already installed"

# Stage 4: PageIndex
echo ""
echo "Stage 4 (PageIndex) - Optional Components:"
echo "-----------------------------------------------------------"

read -p "Install vector database (FAISS)? [y/N]: " install_faiss
if [[ $install_faiss =~ ^[Yy]$ ]]; then
    echo "   Installing FAISS..."
    pip install faiss-cpu -q
    echo "   ✓ FAISS installed (CPU version)"
else
    echo "   ⊘ Skipping FAISS (Stage 4 will be limited)"
fi

read -p "Install embedding models (sentence-transformers)? [y/N]: " install_embeddings
if [[ $install_embeddings =~ ^[Yy]$ ]]; then
    echo "   Installing sentence-transformers..."
    pip install sentence-transformers -q
    echo "   ✓ sentence-transformers installed"
else
    echo "   ⊘ Skipping embeddings"
fi

# Stage 5: Query Interface
echo ""
echo "Stage 5 (Query Interface) - Optional Components:"
echo "-----------------------------------------------------------"

read -p "Install LLM integration (OpenAI/Anthropic)? [y/N]: " install_llm
if [[ $install_llm =~ ^[Yy]$ ]]; then
    echo "   Installing LLM clients..."
    pip install openai anthropic -q
    echo "   ✓ OpenAI and Anthropic clients installed"
else
    echo "   ⊘ Skipping LLM clients"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "DEVELOPMENT DEPENDENCIES (Optional)"
echo "════════════════════════════════════════════════════════════"
echo ""

read -p "Install development tools (linting, formatting)? [y/N]: " install_dev
if [[ $install_dev =~ ^[Yy]$ ]]; then
    echo "Installing development tools..."
    pip install black flake8 mypy isort -q
    echo "   ✓ black (code formatter)"
    echo "   ✓ flake8 (linter)"
    echo "   ✓ mypy (type checker)"
    echo "   ✓ isort (import sorter)"
else
    echo "⊘ Skipping development tools"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "INSTALLATION SUMMARY"
echo "════════════════════════════════════════════════════════════"
echo ""

# List installed packages
echo "Installed packages:"
pip list | grep -E "pydantic|pyyaml|pdfplumber|PyMuPDF|camelot|opencv|docling|google-generativeai|pytesseract|faiss|sentence-transformers|openai|anthropic|pytest|black|flake8" || echo "Core packages installed"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "ENVIRONMENT SETUP"
echo "════════════════════════════════════════════════════════════"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    if [ -f ".env.template" ]; then
        cp .env.template .env
        echo "✓ .env file created"
        echo "⚠ Please edit .env and add your API keys:"
        echo "  - GEMINI_API_KEY (for Tier 2 extraction)"
        echo "  - OPENAI_API_KEY (for Stage 5 query interface)"
    else
        echo "⚠ .env.template not found, creating basic .env..."
        cat > .env << EOF
# API Keys
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here

# Paths
DATA_DIR=./data
OUTPUT_DIR=./.refinery

# Configuration
LOG_LEVEL=INFO
MAX_WORKERS=4
EOF
        echo "✓ Basic .env file created"
    fi
else
    echo "✓ .env file already exists"
fi

# Create necessary directories
echo ""
echo "Creating project directories..."
mkdir -p data
mkdir -p .refinery/profiles
mkdir -p .refinery/pageindex
mkdir -p .refinery/ldus
mkdir -p .refinery/docling_cache
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p logs
echo "✓ Project directories created"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "VERIFICATION"
echo "════════════════════════════════════════════════════════════"
echo ""

# Test imports
echo "Testing core imports..."
python3 << EOF
try:
    import pdfplumber
    import fitz  # PyMuPDF
    import camelot
    import pydantic
    import yaml
    print("✓ All core imports successful")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    exit(1)
EOF

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✓ INSTALLATION COMPLETE!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo ""
echo "1. Configure API keys in .env file:"
echo "   nano .env"
echo ""
echo "2. Run tests to verify installation:"
echo "   pytest tests/"
echo ""
echo "3. Try the demos:"
echo "   python3 demo_stage1.py          # Document profiling"
echo "   python3 demo_stage2.py          # Content extraction"
echo "   python3 demo_stage3.py          # Semantic chunking"
echo "   python3 demo_hybrid_pipeline.py # Hybrid extraction"
echo ""
echo "4. Process your documents:"
echo "   python3 -m src.main process data/your_document.pdf"
echo ""
echo "Documentation:"
echo "   - README.md                              # Project overview"
echo "   - docs/HYBRID_PIPELINE_IMPLEMENTATION.md # Extraction details"
echo "   - docs/DOCLING_OPTIMIZATION_STRATEGY.md  # Performance tuning"
echo "   - docs/DOMAIN_NOTES.md                   # Architecture notes"
echo ""
echo "Need help? Check the docs/ folder or run:"
echo "   python3 -m src.main --help"
echo ""
echo "Happy extracting! 🚀"
echo ""
