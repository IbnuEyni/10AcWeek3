#!/bin/bash
# Install dependencies for hybrid extraction pipeline

echo "Installing Hybrid Pipeline Dependencies..."
echo "=========================================="

# Activate virtual environment
source .venv/bin/activate

# Core dependencies
echo ""
echo "1. Installing pdfplumber (PDF classification)..."
pip install pdfplumber -q

echo "2. Installing PyMuPDF (figure/layout extraction)..."
pip install PyMuPDF -q

echo "3. Installing Camelot (table extraction)..."
pip install "camelot-py[cv]" -q

echo "4. Installing OpenCV (Camelot dependency)..."
pip install opencv-python -q

# Optional: Docling (heavy, takes time)
echo ""
read -p "Install Docling? (heavy dependencies, ~2GB) [y/N]: " install_docling
if [[ $install_docling =~ ^[Yy]$ ]]; then
    echo "5. Installing Docling (this may take 5-10 minutes)..."
    pip install docling -q
    echo "✓ Docling installed"
else
    echo "⊘ Skipping Docling (Tier 1 will be limited)"
fi

# Optional: Gemini API
echo ""
read -p "Install Gemini API client? (for Tier 2) [y/N]: " install_gemini
if [[ $install_gemini =~ ^[Yy]$ ]]; then
    echo "6. Installing Google Generative AI..."
    pip install google-generativeai -q
    echo "✓ Gemini API client installed"
else
    echo "⊘ Skipping Gemini (Tier 2 will use fallbacks)"
fi

echo ""
echo "=========================================="
echo "✓ Installation complete!"
echo ""
echo "Installed components:"
pip list | grep -E "pdfplumber|PyMuPDF|camelot|opencv|docling|google-generativeai"

echo ""
echo "Next steps:"
echo "1. Run demo: python3 demo_hybrid_pipeline.py"
echo "2. Check docs: docs/HYBRID_PIPELINE_IMPLEMENTATION.md"
