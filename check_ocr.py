#!/usr/bin/env python3
"""Check which OCR engines are available"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from src.strategies.handwriting_ocr import HandwritingOCR


def main():
    print("=" * 60)
    print("OCR ENGINES CHECK")
    print("=" * 60)
    
    ocr = HandwritingOCR()
    engines = ocr.get_available_engines()
    
    print(f"\n✅ Available engines: {len(engines)}")
    
    if engines:
        for engine in engines:
            print(f"   • {engine}")
    else:
        print("   ⚠️  No engines configured")
    
    print("\n" + "=" * 60)
    print("ENGINE STATUS")
    print("=" * 60)
    
    # Check each engine
    import os
    
    # Gemini
    if os.getenv("GEMINI_API_KEY"):
        print("✅ Gemini Vision: Configured")
    else:
        print("❌ Gemini Vision: Not configured (set GEMINI_API_KEY)")
    
    # Azure
    if os.getenv("AZURE_CV_KEY") and os.getenv("AZURE_CV_ENDPOINT"):
        print("✅ Azure Computer Vision: Configured")
    else:
        print("❌ Azure Computer Vision: Not configured (set AZURE_CV_KEY and AZURE_CV_ENDPOINT)")
    
    # Google Cloud Vision
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("✅ Google Cloud Vision: Configured")
    else:
        print("❌ Google Cloud Vision: Not configured (set GOOGLE_APPLICATION_CREDENTIALS)")
    
    # Tesseract
    try:
        import pytesseract
        print("✅ Tesseract: Installed")
    except ImportError:
        print("❌ Tesseract: Not installed (pip install pytesseract)")
    
    print("\n" + "=" * 60)
    print("RECOMMENDATION")
    print("=" * 60)
    
    if len(engines) == 0:
        print("""
⚠️  No OCR engines available!

Quick fix (easiest):
  1. Install Tesseract:
     Ubuntu/Debian: sudo apt-get install tesseract-ocr
     macOS: brew install tesseract
  
  2. Install Python package:
     pip install pytesseract

See OCR_SETUP.md for detailed instructions.
""")
    elif len(engines) == 1:
        print(f"""
✅ OCR is working with {engines[0]}

Consider adding a fallback engine for reliability.
See OCR_SETUP.md for more options.
""")
    else:
        print(f"""
✅ OCR is well configured with {len(engines)} engines!

Fallback chain: {' → '.join(engines)}
""")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
