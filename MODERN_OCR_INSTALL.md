# Modern OCR Installation Guide

## Quick Install with uv

### Option 1: Tier 2 Only (Scanned PDFs + Modern OCR)
```bash
uv pip install -e ".[tier2]"
```

Installs:
- Gemini Vision API
- RapidOCR (fastest)
- PaddleOCR (accurate)
- Surya OCR (highest quality)

### Option 2: All Features
```bash
uv pip install -e ".[all]"
```

Installs everything including modern OCR engines.

### Option 3: Minimal + Modern OCR
```bash
# Core only
uv pip install -e .

# Add modern OCR
uv pip install rapidocr-onnxruntime paddleocr surya-ocr
```

## Individual Engine Installation

### RapidOCR (Recommended - Fastest)
```bash
uv pip install rapidocr-onnxruntime
```
- Size: ~50MB
- Speed: 100ms/page
- Accuracy: 95%+
- CPU-only

### PaddleOCR (Balanced)
```bash
uv pip install paddleocr
```
- Size: ~200MB
- Speed: 200ms/page
- Accuracy: 97%+
- Optional GPU support

### Surya OCR (Highest Quality)
```bash
uv pip install surya-ocr
```
- Size: ~500MB
- Speed: 500ms/page
- Accuracy: 99%+
- Best bounding boxes

## Verification

```bash
python3 -c "from src.strategies.handwriting_ocr import ModernOCR; ocr = ModernOCR(); print(f'Available engines: {ocr.get_available_engines()}')"
```

Expected output:
```
Available engines: ['rapidocr', 'paddleocr', 'surya', 'gemini', 'google_vision']
```

## Dependencies Removed

- ❌ `pytesseract` - No longer needed
- ❌ Tesseract system installation - Not required
- ❌ `azure-cognitiveservices-vision-computervision` - Replaced by better local options

## System Requirements

- Python 3.10+
- 4GB RAM minimum
- 8GB RAM recommended for Surya OCR
- No GPU required (but optional for PaddleOCR/Surya)

## Troubleshooting

### Issue: "No OCR engines available"
**Solution**: Install at least one engine:
```bash
uv pip install rapidocr-onnxruntime
```

### Issue: PaddleOCR slow
**Solution**: Use RapidOCR for speed or enable GPU:
```bash
uv pip install paddlepaddle-gpu
```

### Issue: Surya out of memory
**Solution**: Use RapidOCR or PaddleOCR instead, or increase RAM.
