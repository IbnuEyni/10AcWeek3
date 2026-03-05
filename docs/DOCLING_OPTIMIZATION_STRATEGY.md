# Docling Optimization Strategy: Free-First, API-Fallback

## Problem Statement

**Challenge**: Docling is free but slow (10-30 seconds per document). Vision APIs (Gemini/GCP Vision) are fast but costly ($0.0002-$0.02 per page).

**Goal**: Use Docling as primary extraction tool, escalate to paid APIs only when necessary.

---

## Recommended Architecture: Hybrid Extraction Pipeline

```
Document → Docling (Free, Slow) → Confidence Check → Vision API (Paid, Fast)
              ↓                           ↓                    ↓
         High Quality              Low Confidence        Final Result
         (90% cases)               (10% cases)          (100% accuracy)
```

---

## Strategy 1: Lazy Docling Initialization (IMPLEMENTED ✓)

### Problem
- `DocumentConverter()` initialization takes 10-30 seconds
- Was being called even when not needed

### Solution
```python
class DoclingHelper:
    def __init__(self):
        self.converter = None  # Don't initialize upfront
        self._initialized = False
    
    def _ensure_initialized(self):
        """Initialize only when first needed"""
        if not self._initialized:
            from docling.document_converter import DocumentConverter
            self.converter = DocumentConverter()
            self._initialized = True
```

**Benefit**: Save 10-30s when Docling isn't needed

---

## Strategy 2: Document-Level Caching (RECOMMENDED)

### Problem
- Docling converts entire PDF each time you call it
- Multiple calls = multiple 10-30s delays

### Solution: Convert Once, Use Many Times
```python
class DoclingCache:
    def __init__(self):
        self._cache = {}  # {pdf_path: docling_result}
    
    def get_or_convert(self, pdf_path: str):
        """Convert once, cache result"""
        if pdf_path not in self._cache:
            result = self.converter.convert(pdf_path)
            self._cache[pdf_path] = result
        return self._cache[pdf_path]
```

**Implementation Location**: `src/utils/docling_helper.py`

**Benefit**: 
- First call: 10-30s (unavoidable)
- Subsequent calls: <1ms (instant)
- Extract text, tables, figures, structure from same conversion

---

## Strategy 3: Confidence-Based Escalation (RECOMMENDED)

### Use Docling First, API as Fallback

```python
def extract_with_escalation(pdf_path: str, profile: DocumentProfile):
    # Step 1: Try Docling (free)
    docling_result = docling_helper.get_or_convert(pdf_path)
    confidence = calculate_confidence(docling_result)
    
    # Step 2: Check confidence
    if confidence >= 0.75:
        return docling_result, "docling", 0.0  # Free!
    
    # Step 3: Escalate to Vision API (paid)
    vision_result = vision_api.extract(pdf_path)
    cost = 0.0002 * profile.total_pages
    return vision_result, "vision_api", cost
```

**Confidence Indicators for Docling**:
- ✓ Text extraction completeness (>80% of expected content)
- ✓ Table structure integrity (headers detected, rows aligned)
- ✓ Figure bounding boxes present
- ✗ Blurry/low-quality scans
- ✗ Handwritten content
- ✗ Complex multi-column layouts

---

## Strategy 4: Selective Feature Extraction (RECOMMENDED)

### Don't Extract Everything Every Time

```python
class SelectiveDoclingExtractor:
    def extract_only_what_you_need(self, pdf_path: str, needs: dict):
        """Extract only requested features"""
        result = self.cache.get_or_convert(pdf_path)  # One conversion
        
        output = {}
        if needs.get('text'):
            output['text'] = self._extract_text(result)
        
        if needs.get('tables'):
            output['tables'] = self._extract_tables(result)
        
        if needs.get('figures'):
            # Docling for layout detection (free)
            figures = self._extract_figures(result)
            
            # Vision API only for low-confidence figures
            for fig in figures:
                if fig.confidence < 0.7:  # Blurry or complex
                    fig.description = vision_api.describe_image(fig)
                    fig.cost += 0.0002
        
        return output
```

**Use Cases**:
- Financial reports → Extract tables only (skip figures)
- Technical specs → Extract text + structure (skip images)
- Scanned forms → Extract figures with API fallback

---

## Strategy 5: Figure-Specific Hybrid Approach (YOUR USE CASE)

### Problem: 5 Figures on One Page

```python
def extract_figures_hybrid(pdf_path: str, page_num: int):
    # Step 1: Docling detects all 5 figures (free, 10-30s once)
    result = docling_cache.get_or_convert(pdf_path)
    figures = [fig for fig in result.figures if fig.page == page_num]
    
    # Step 2: Extract metadata from Docling (free)
    for fig in figures:
        fig.bbox = docling_bbox(fig)
        fig.caption = docling_caption(fig)
        fig.figure_id = fig.id
    
    # Step 3: Vision API only for unidentified figures
    for fig in figures:
        if not fig.caption or fig.confidence < 0.6:
            # Use Vision API for this specific figure
            fig.description = vision_api.describe_region(
                pdf_path, page_num, fig.bbox
            )
            fig.cost = 0.0002  # Only pay for unclear figures
    
    return figures
```

**Cost Analysis**:
- Docling: $0 (detects all 5 figures)
- Vision API: $0.0002 × 2 unclear figures = $0.0004
- **Total**: $0.0004 vs $0.001 (5 × $0.0002) if using API for all

---

## Strategy 6: Parallel Processing (ADVANCED)

### Problem: Processing 100 Documents Takes 100 × 30s = 50 Minutes

```python
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

def process_corpus_parallel(pdf_paths: List[str], max_workers: int = 4):
    """Process multiple documents in parallel"""
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(extract_with_docling, pdf_paths)
    return list(results)
```

**Benefit**: 
- Sequential: 100 docs × 30s = 50 minutes
- Parallel (4 cores): 100 docs × 30s ÷ 4 = 12.5 minutes
- **4× speedup**

**Limitation**: Requires sufficient RAM (Docling is memory-intensive)

---

## Strategy 7: Incremental Processing with Checkpoints

### Save Docling Results to Disk

```python
def extract_with_checkpoints(pdf_path: str):
    cache_path = f".refinery/docling_cache/{doc_id}.pkl"
    
    # Check if already processed
    if Path(cache_path).exists():
        return pickle.load(open(cache_path, 'rb'))  # Instant!
    
    # Process with Docling (slow, but only once)
    result = docling_helper.convert(pdf_path)
    
    # Save for future use
    pickle.dump(result, open(cache_path, 'wb'))
    return result
```

**Benefit**: 
- First run: 30s
- All future runs: <1s (load from disk)
- Survives application restarts

---

## Recommended Implementation Plan

### Phase 1: Immediate Wins (1-2 hours)
1. ✓ **Lazy initialization** (already done)
2. **Add document-level caching** in `DoclingHelper`
3. **Add checkpoint system** for processed documents

### Phase 2: Hybrid Extraction (2-3 hours)
4. **Implement confidence scoring** for Docling results
5. **Add escalation logic** to `ExtractionRouter`
6. **Create figure-specific hybrid extractor**

### Phase 3: Production Optimization (3-4 hours)
7. **Add parallel processing** for batch jobs
8. **Implement selective extraction** based on document type
9. **Add cost tracking** and budget guards

---

## Configuration Example

### `rubric/extraction_rules.yaml`

```yaml
docling:
  enabled: true
  cache_results: true
  cache_dir: ".refinery/docling_cache"
  timeout_seconds: 60
  
  confidence_thresholds:
    text: 0.75
    tables: 0.80
    figures: 0.70
  
  escalation:
    enabled: true
    trigger_confidence: 0.70
    fallback_strategy: "vision_api"

vision_api:
  enabled: true
  use_cases:
    - "low_confidence_figures"
    - "handwritten_content"
    - "complex_diagrams"
  
  cost_limits:
    per_document: 0.50
    per_batch: 10.00
    per_month: 100.00

extraction_strategy:
  priority:
    1: "docling"        # Free, try first
    2: "vision_api"     # Paid, use if needed
    3: "fast_text"      # Fallback for simple docs
```

---

## Cost Comparison: 1000-Page Corpus

| Strategy | Docling Time | API Calls | Total Cost | Total Time |
|----------|--------------|-----------|------------|------------|
| **API-Only** | 0s | 1000 pages | $0.20-$20 | 5 min |
| **Docling-Only** | 5000s | 0 | $0 | 83 min |
| **Hybrid (90% Docling)** | 4500s | 100 pages | $0.02-$2 | 77 min |
| **Hybrid + Cache** | 4500s (once) | 100 pages | $0.02-$2 | 5 min (rerun) |
| **Hybrid + Parallel (4×)** | 1125s | 100 pages | $0.02-$2 | 20 min |

**Recommended**: Hybrid + Cache + Parallel = **$0.02-$2 cost, 20 min first run, 5 min reruns**

---

## Code Template: Efficient Docling Usage

```python
class EfficientDoclingExtractor:
    def __init__(self):
        self.cache = {}
        self.checkpoint_dir = Path(".refinery/docling_cache")
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def extract(self, pdf_path: str, needs: dict) -> dict:
        # 1. Check disk cache
        doc_id = Path(pdf_path).stem
        cache_file = self.checkpoint_dir / f"{doc_id}.pkl"
        
        if cache_file.exists():
            result = pickle.load(open(cache_file, 'rb'))
        else:
            # 2. Convert with Docling (slow, but only once)
            result = self._convert_with_docling(pdf_path)
            pickle.dump(result, open(cache_file, 'wb'))
        
        # 3. Extract only what's needed
        output = self._selective_extract(result, needs)
        
        # 4. Escalate low-confidence items to Vision API
        output = self._escalate_if_needed(output, pdf_path)
        
        return output
```

---

## Key Takeaways

1. **Cache Docling conversions** - Convert once, use forever
2. **Escalate selectively** - Use Vision API only for low-confidence items
3. **Extract selectively** - Don't process features you don't need
4. **Parallelize when possible** - 4× speedup with multi-core
5. **Save checkpoints** - Survive crashes, enable reruns
6. **Monitor costs** - Track API usage, set budget limits

**Bottom Line**: With proper caching and selective escalation, you can achieve **95% cost savings** while maintaining **high accuracy** and **reasonable speed**.
