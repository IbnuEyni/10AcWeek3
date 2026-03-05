# Quick Start Guide - Hybrid Extraction Pipeline

## Installation

### Option 1: Fast Installation with uv (Recommended)

```bash
# Install with uv (10-100× faster than pip)
./install_uv.sh

# Choose installation profile:
# 1. Minimal  - Core only
# 2. Tier 1   - + Native PDF tools (Camelot, Docling)
# 3. Tier 2   - + Scanned PDF tools (Gemini API)
# 4. Full     - All features
# 5. Dev      - Full + development tools
```

### Option 2: Manual Installation with uv

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv .venv
source .venv/bin/activate

# Install dependencies
uv pip install -e .                    # Minimal
uv pip install -e ".[tier1]"           # + Native PDF tools
uv pip install -e ".[tier1,tier2]"     # + Scanned PDF tools
uv pip install -e ".[all]"             # All features
uv pip install -e ".[all,dev]"         # All + dev tools
```

### Option 3: Traditional pip Installation

```bash
# Run the bash installation script
./install.sh

# Or install manually
source .venv/bin/activate
pip install -e ".[all]"
```

## Configuration

Edit `.env` file:
```bash
# Required for Tier 2 (scanned PDFs)
GEMINI_API_KEY=your_key_here

# Optional
OPENAI_API_KEY=your_key_here
```

## Usage

### 1. Basic Extraction

```python
from src.strategies.hybrid_pipeline import HybridExtractionPipeline
from src.agents.triage import TriageAgent

# Initialize
triage = TriageAgent()
pipeline = HybridExtractionPipeline()

# Process document
profile = triage.profile_document("document.pdf")
extracted_doc, confidence = pipeline.extract("document.pdf", profile)

# Access results
print(f"Text blocks: {len(extracted_doc.text_blocks)}")
print(f"Tables: {len(extracted_doc.tables)}")
print(f"Figures: {len(extracted_doc.figures)}")
```

### 2. Run Demos

```bash
# Test hybrid pipeline
python3 demo_hybrid_pipeline.py

# Test individual stages
python3 demo_stage1.py  # Triage
python3 demo_stage2.py  # Extraction
python3 demo_stage3.py  # Chunking
```

### 3. Batch Processing

```python
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

pdf_files = list(Path("data").glob("*.pdf"))

def process_pdf(pdf_path):
    profile = triage.profile_document(str(pdf_path))
    return pipeline.extract(str(pdf_path), profile)

# Process in parallel (4 workers)
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_pdf, pdf_files))
```

## Architecture Decision

### Tier 1: Native PDFs (80% of documents)
- **Classifier:** pdfplumber (1s)
- **Text:** Docling without OCR (10-30s)
- **Tables:** Camelot (3-5s)
- **Figures:** PyMuPDF (1s)
- **Layout:** PyMuPDF (1s)
- **Cost:** $0
- **Time:** ~15s per document

### Tier 2: Scanned PDFs (20% of documents)
- **Page Understanding:** Gemini 2.5 Flash (2-5s)
- **Tables:** Docling with OCR (fallback)
- **Figures:** Gemini Vision (2-5s)
- **Handwriting:** Gemini Vision (2-5s)
- **Fallback:** GCP Vision → Tesseract
- **Cost:** $0.0002 per page
- **Time:** ~5s per document

## Performance Expectations

### 1000-Page Corpus
- **Native (800 pages):** 3.3 hours, $0
- **Scanned (200 pages):** 16 minutes, $0.04
- **Total:** 3.5 hours, $0.04
- **Savings:** 97% vs industry standard ($1.50)

## Optimization Tips

### 1. Enable Docling Caching
```python
# Docling converts once, extracts multiple times
helper = OptimizedDoclingHelper(use_ocr=False)
result = helper.convert_once(pdf_path)  # 10-30s
text = helper.extract_text(pdf_path)    # <1ms (cached)
tables = helper.extract_tables(pdf_path) # <1ms (cached)
```

### 2. Parallel Processing
```python
# Process 4 documents simultaneously
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=4) as executor:
    results = executor.map(process_document, pdf_paths)

# Time: 3.3 hours → 50 minutes (4× speedup)
```

### 3. Disk Caching
```python
import pickle
from pathlib import Path

cache_dir = Path(".refinery/docling_cache")
cache_file = cache_dir / f"{doc_id}.pkl"

if cache_file.exists():
    result = pickle.load(open(cache_file, 'rb'))  # <1s
else:
    result = docling.convert(pdf_path)  # 10-30s
    pickle.dump(result, open(cache_file, 'wb'))
```

## Troubleshooting

### Issue: Docling takes too long
**Solution:** Disable OCR for native PDFs
```python
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False  # Saves 2+ minutes
```

### Issue: Camelot finds no tables
**Solution:** Try both flavors
```python
# Try lattice first (bordered tables)
tables = camelot.read_pdf(pdf, flavor='lattice')

# Fallback to stream (borderless tables)
if len(tables) == 0:
    tables = camelot.read_pdf(pdf, flavor='stream')
```

### Issue: Out of memory
**Solution:** Process in smaller batches
```python
# Instead of processing all at once
for batch in chunks(pdf_files, batch_size=10):
    results = process_batch(batch)
    save_results(results)
    clear_cache()  # Free memory
```

### Issue: Gemini API rate limits
**Solution:** Add retry logic
```python
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def extract_with_gemini(pdf_path):
    return gemini_api.extract(pdf_path)
```

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/unit/test_hybrid_pipeline.py

# Run with coverage
pytest --cov=src tests/
```

## Monitoring

Check extraction logs:
```bash
# View ledger
cat .refinery/extraction_ledger.jsonl | jq

# Count by strategy
cat .refinery/extraction_ledger.jsonl | jq -r '.strategy_used' | sort | uniq -c

# Average confidence
cat .refinery/extraction_ledger.jsonl | jq -r '.confidence_score' | awk '{sum+=$1; count++} END {print sum/count}'

# Total cost
cat .refinery/extraction_ledger.jsonl | jq -r '.cost_estimate' | awk '{sum+=$1} END {print "$"sum}'
```

## Next Steps

1. **Stage 4:** Implement PageIndex for spatial search
2. **Stage 5:** Add Query Interface Agent
3. **Optimization:** Add GPU support for Docling OCR
4. **Scale:** Deploy as API service

## Resources

- **Documentation:** `docs/HYBRID_PIPELINE_IMPLEMENTATION.md`
- **Optimization:** `docs/DOCLING_OPTIMIZATION_STRATEGY.md`
- **Architecture:** `docs/DOMAIN_NOTES.md`
- **README:** `README.md`

## Support

For issues or questions:
1. Check documentation in `docs/`
2. Review test cases in `tests/`
3. Run demos to verify setup
4. Check logs in `logs/` directory

---

**Status:** Production-ready ✅  
**Version:** 1.0.0  
**Last Updated:** 2024
