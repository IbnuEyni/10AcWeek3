# Setup Guide: Gemini Flash 2.5 Integration

## Why Gemini Flash 2.5?

For this document intelligence pipeline, **Gemini Flash 2.5** is the optimal choice because:

1. **Best for Document Vision**: Specifically optimized for document understanding and OCR tasks
2. **Cost-Effective**: Free tier includes 1,500 requests/day, then very affordable pricing
3. **Fast**: Low latency for real-time document processing
4. **High Accuracy**: Excellent at extracting text from scanned documents, tables, and complex layouts
5. **Native Google Integration**: Direct API, no intermediary services needed

### Comparison with Alternatives

| Feature | Gemini Flash 2.5 | DeepSeek | Groq |
|---------|------------------|----------|------|
| Document Vision | ✅ Excellent | ❌ Text-only | ❌ Text-only |
| OCR Quality | ✅ High | N/A | N/A |
| Table Extraction | ✅ Native | N/A | N/A |
| Cost | ✅ Free tier + low | ✅ Low | ✅ Free |
| Speed | ✅ Fast | ✅ Very fast | ✅ Fastest |
| Use Case | **Document extraction** | Text generation | Fast inference |

**Verdict**: Gemini Flash 2.5 is purpose-built for our document intelligence needs.

---

## Getting Your Gemini API Key

### Step 1: Visit Google AI Studio
Go to: https://makersuite.google.com/app/apikey

### Step 2: Sign in with Google Account
Use your Google account to sign in.

### Step 3: Create API Key
1. Click "Create API Key"
2. Select a Google Cloud project (or create new one)
3. Copy the generated API key

### Step 4: Add to .env File
```bash
# In your project root
echo "GEMINI_API_KEY=your_actual_key_here" > .env
```

---

## Installation

### Install Vision Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install vision extras
uv pip install -e ".[vision]"

# This installs:
# - google-generativeai (Gemini SDK)
# - pdf2image (PDF to image conversion)
# - Pillow (image processing)
```

### System Dependencies (for pdf2image)

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**macOS:**
```bash
brew install poppler
```

**Windows:**
Download poppler from: http://blog.alivate.com.au/poppler-windows/

---

## Testing Gemini Integration

### Quick Test Script

Create `test_gemini.py`:

```python
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# Test with simple prompt
response = model.generate_content("Extract text from this: Hello World")
print(response.text)
```

Run:
```bash
.venv/bin/python3 test_gemini.py
```

---

## Using Gemini in the Pipeline

### Automatic Usage

The pipeline automatically uses Gemini when:
1. Document is classified as `scanned_image`
2. Confidence from fast_text or layout_aware is < 0.7
3. GEMINI_API_KEY is set in .env

### Manual Testing

```python
from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter

# Initialize
triage = TriageAgent()
router = ExtractionRouter()

# Process scanned document
profile = triage.profile_document("data/Audit Report - 2023.pdf")
print(f"Strategy: {profile.estimated_extraction_cost}")

# Extract (will use Gemini if scanned)
extracted = router.extract("data/Audit Report - 2023.pdf", profile)
print(f"Extracted {len(extracted.text_blocks)} blocks")
print(f"Confidence: {extracted.confidence_score}")
```

---

## Cost Management

### Gemini Pricing (as of 2024)

**Free Tier:**
- 1,500 requests per day
- 1 million tokens per month

**Paid Tier:**
- Input: $0.075 per 1M tokens
- Output: $0.30 per 1M tokens
- Images: ~$0.00025 per image

### Our Budget Guards

1. **Per-document cap**: $1.00 maximum
2. **Pre-flight check**: Cost estimated before processing
3. **Page limit**: Large documents flagged for review

### Example Costs

| Document | Pages | Estimated Cost | Status |
|----------|-------|----------------|--------|
| 3-page audit | 3 | $0.06 | ✅ Process |
| 50-page report | 50 | $1.00 | ✅ Process |
| 100-page manual | 100 | $2.00 | ⚠️ Exceeds cap |

---

## Troubleshooting

### Error: "google.generativeai not found"
```bash
uv pip install google-generativeai
```

### Error: "pdf2image not available"
```bash
# Install pdf2image
uv pip install pdf2image

# Install system dependency
sudo apt-get install poppler-utils  # Ubuntu
brew install poppler  # macOS
```

### Error: "API key not valid"
- Check .env file exists in project root
- Verify GEMINI_API_KEY is set correctly
- Test key at: https://makersuite.google.com/

### Error: "Quota exceeded"
- You've hit the free tier limit (1,500 requests/day)
- Wait 24 hours or upgrade to paid tier
- Consider processing in batches

---

## Advanced Configuration

### Custom Model Selection

Edit `src/strategies/vision_augmented.py`:

```python
# Use different Gemini model
self.model = "gemini-1.5-pro"  # More powerful, higher cost
# or
self.model = "gemini-2.0-flash-exp"  # Default, balanced
```

### Adjust DPI for Image Quality

```python
# In _pdf_to_images method
return convert_from_path(pdf_path, dpi=200)  # Higher quality, slower
```

### Domain-Specific Prompts

The system automatically adjusts prompts based on document domain:
- **Financial**: Focus on tables and numerical precision
- **Legal**: Preserve structure and clauses
- **Technical**: Extract specifications and diagrams
- **Medical**: Careful with patient data

---

## Production Deployment

### Environment Variables

```bash
# Production .env
GEMINI_API_KEY=prod_key_here
MAX_COST_PER_DOCUMENT=5.0  # Higher limit for production
CONFIDENCE_ESCALATION_THRESHOLD=0.75
```

### Monitoring

Check extraction ledger:
```bash
cat .refinery/extraction_ledger.jsonl | jq '.strategy_used' | sort | uniq -c
```

### Batch Processing

For large corpora:
```python
# Process in batches to respect rate limits
import time

for doc in documents:
    profile = triage.profile_document(doc)
    extracted = router.extract(doc, profile)
    time.sleep(0.5)  # Rate limiting
```

---

## Next Steps

1. ✅ Get Gemini API key
2. ✅ Install vision dependencies
3. ✅ Test with sample document
4. ✅ Process full corpus
5. ⏭️ Implement Phase 3: Semantic Chunking
6. ⏭️ Implement Phase 4: PageIndex Builder

---

## Support

- Gemini Documentation: https://ai.google.dev/docs
- API Reference: https://ai.google.dev/api/python
- Pricing: https://ai.google.dev/pricing
