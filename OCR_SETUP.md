# OCR Engines Setup Guide

This guide shows how to configure all OCR engines for handwriting recognition.

## Overview

The system supports 4 OCR engines with automatic fallback:
1. **Gemini Vision** (Cloud, recommended)
2. **Azure Computer Vision** (Cloud, enterprise)
3. **Google Cloud Vision** (Cloud, high accuracy)
4. **Tesseract** (Local, offline)

You only need to configure ONE engine for the system to work. More engines = better fallback.

---

## Option 1: Tesseract (Easiest - Local & Free)

### Install Tesseract

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

### Install Python Package

```bash
pip install pytesseract
# or
uv pip install pytesseract
```

### Test It

```python
from src.strategies.handwriting_ocr import HandwritingOCR

ocr = HandwritingOCR()
print(ocr.get_available_engines())  # Should show ['tesseract']
```

**Pros:**
- ✅ Free
- ✅ Works offline
- ✅ No API keys needed
- ✅ Fast

**Cons:**
- ⚠️ Lower accuracy than cloud services
- ⚠️ Struggles with handwriting

---

## Option 2: Gemini Vision (Recommended - Cloud)

### Get API Key

1. Go to: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

### Configure

**Method 1: Environment Variable**
```bash
export GEMINI_API_KEY="your_key_here"
```

**Method 2: .env File**
```bash
# Create .env file in project root
echo "GEMINI_API_KEY=your_key_here" >> .env
```

### Install Package

```bash
pip install google-generativeai pillow
# or
uv pip install google-generativeai pillow
```

### Test It

```python
from src.strategies.handwriting_ocr import HandwritingOCR

ocr = HandwritingOCR()
print(ocr.get_available_engines())  # Should show ['gemini']
```

**Pros:**
- ✅ High accuracy
- ✅ Good with handwriting
- ✅ Easy to setup
- ✅ Free tier available

**Cons:**
- ⚠️ Requires internet
- ⚠️ API costs (after free tier)

**Cost:** ~$0.001 per image (very cheap)

---

## Option 3: Azure Computer Vision (Enterprise)

### Get Credentials

1. Go to: https://portal.azure.com
2. Create "Computer Vision" resource
3. Get:
   - API Key (from "Keys and Endpoint")
   - Endpoint URL

### Configure

```bash
export AZURE_CV_KEY="your_key_here"
export AZURE_CV_ENDPOINT="https://your-resource.cognitiveservices.azure.com/"
```

Or in `.env`:
```
AZURE_CV_KEY=your_key_here
AZURE_CV_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
```

### Install Package

```bash
pip install azure-cognitiveservices-vision-computervision msrest
# or
uv pip install azure-cognitiveservices-vision-computervision msrest
```

### Test It

```python
from src.strategies.handwriting_ocr import HandwritingOCR

ocr = HandwritingOCR()
print(ocr.get_available_engines())  # Should show ['azure']
```

**Pros:**
- ✅ Enterprise-grade
- ✅ High accuracy
- ✅ Good SLA
- ✅ Compliance certifications

**Cons:**
- ⚠️ Requires Azure account
- ⚠️ More expensive than Gemini
- ⚠️ More complex setup

**Cost:** ~$1.50 per 1000 images

---

## Option 4: Google Cloud Vision (High Accuracy)

### Get Credentials

1. Go to: https://console.cloud.google.com
2. Create project
3. Enable "Cloud Vision API"
4. Create service account
5. Download JSON key file

### Configure

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-key.json"
```

Or in `.env`:
```
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-key.json
```

### Install Package

```bash
pip install google-cloud-vision
# or
uv pip install google-cloud-vision
```

### Test It

```python
from src.strategies.handwriting_ocr import HandwritingOCR

ocr = HandwritingOCR()
print(ocr.get_available_engines())  # Should show ['google_vision']
```

**Pros:**
- ✅ Highest accuracy
- ✅ Excellent with handwriting
- ✅ Many language support

**Cons:**
- ⚠️ Most complex setup
- ⚠️ Requires GCP account
- ⚠️ Most expensive

**Cost:** ~$1.50 per 1000 images

---

## Quick Setup (Recommended)

### For Development/Testing: Use Tesseract

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr
pip install pytesseract

# macOS
brew install tesseract
pip install pytesseract
```

### For Production: Use Gemini

```bash
# Get API key from https://makersuite.google.com/app/apikey
export GEMINI_API_KEY="your_key_here"
pip install google-generativeai pillow
```

---

## Verify Setup

Run this script to check which engines are available:

```python
from src.strategies.handwriting_ocr import HandwritingOCR

ocr = HandwritingOCR()
engines = ocr.get_available_engines()

print(f"Available OCR engines: {engines}")
print(f"Total engines: {len(engines)}")

if not engines:
    print("\n⚠️  No OCR engines configured!")
    print("See OCR_SETUP.md for setup instructions")
else:
    print(f"\n✅ OCR is ready with {len(engines)} engine(s)")
```

Save as `check_ocr.py` and run:
```bash
python3 check_ocr.py
```

---

## Troubleshooting

### "No OCR engines available"

**Solution:** Install at least one engine (Tesseract is easiest)

### "Tesseract not found"

**Solution:** 
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Then
pip install pytesseract
```

### "Gemini API error: 404"

**Solution:** Check API key is set correctly
```bash
echo $GEMINI_API_KEY  # Should show your key
```

### "All OCR engines failed"

**Possible causes:**
1. No engines configured
2. API keys invalid
3. No internet (for cloud services)
4. Image format not supported

**Solution:** Check logs for specific error messages

---

## Comparison Table

| Engine | Setup | Cost | Accuracy | Offline | Best For |
|--------|-------|------|----------|---------|----------|
| Tesseract | Easy | Free | Medium | ✅ Yes | Development, testing |
| Gemini | Easy | Low | High | ❌ No | Production, general use |
| Azure | Medium | Medium | High | ❌ No | Enterprise, compliance |
| Google Vision | Hard | High | Highest | ❌ No | Maximum accuracy needed |

---

## Recommended Setup

**Minimum (Development):**
- Tesseract only

**Recommended (Production):**
- Gemini (primary)
- Tesseract (fallback)

**Enterprise:**
- Azure (primary)
- Gemini (fallback)
- Tesseract (offline fallback)

---

## Update pyproject.toml

Add OCR dependencies:

```toml
[project.optional-dependencies]
ocr = [
    "pytesseract>=0.3.10",
    "google-generativeai>=0.3.0",
    "azure-cognitiveservices-vision-computervision>=0.9.0",
    "google-cloud-vision>=3.4.0",
    "msrest>=0.7.1",
    "Pillow>=10.0.0",
]
```

Install with:
```bash
pip install -e ".[ocr]"
# or
uv pip install -e ".[ocr]"
```

---

## Next Steps

1. Choose ONE engine to start (Tesseract recommended for testing)
2. Follow setup instructions above
3. Run `check_ocr.py` to verify
4. Test with real documents
5. Add more engines for better fallback

---

## Support

If you have issues:
1. Check logs: Look for "OCR" messages
2. Verify API keys are set
3. Test each engine individually
4. Check internet connection (for cloud services)
