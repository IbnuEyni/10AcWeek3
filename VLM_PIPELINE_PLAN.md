# Docling VLM Pipeline Integration Plan

## Overview
Integrate Docling's VLM Pipeline to offload heavy layout/table detection to remote Vision-Language Models (GPT-4o, Claude 3.5 Sonnet, Pixtral) instead of running PyTorch models locally.

## Benefits
1. **Performance**: 10-100x faster than local PyTorch models
2. **Accuracy**: State-of-the-art layout understanding from frontier VLMs
3. **Scalability**: No local GPU/memory constraints
4. **Cost-Effective**: Pay-per-use vs. maintaining local infrastructure

## Architecture Changes

```
Current Flow:
PDF → Docling (local PyTorch) → Extraction → Chunking

New VLM Flow:
PDF → Docling VLM Pipeline → Remote VLM API → Extraction → Chunking
```

## Implementation Steps

### Step 1: Add VLM Strategy Class
**File**: `src/strategies/vlm_docling.py`

```python
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import VlmPipelineOptions
from docling.datamodel.base_models import InputFormat

class VLMDoclingExtractor(BaseExtractor):
    """
    Docling VLM Pipeline - offloads to remote VLM APIs
    Supports: GPT-4o, Claude 3.5 Sonnet, Pixtral, Granite Vision
    """
    
    def __init__(self, vlm_model: str = "gpt-4o"):
        # Configure VLM pipeline
        vlm_options = VlmPipelineOptions()
        vlm_options.model = vlm_model  # gpt-4o, claude-3.5-sonnet, pixtral
        vlm_options.api_key = os.getenv(f"{vlm_model.upper()}_API_KEY")
        
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=vlm_options
                )
            }
        )
    
    def extract(self, pdf_path: str, profile: DocumentProfile):
        # Docling sends page images to VLM API
        result = self.converter.convert(pdf_path)
        
        # Extract structured content
        text_blocks = []
        tables = []
        
        for item in result.document.iterate_items():
            if item.type == 'text':
                text_blocks.append(...)
            elif item.type == 'table':
                tables.append(...)
        
        return ExtractedDocument(...)
```

### Step 2: Update Strategy Selection Logic
**File**: `src/agents/extractor.py`

```python
def _select_strategy(self, profile: DocumentProfile):
    """
    Strategy Selection with VLM option:
    
    1. Native Digital + Simple → Layout-Aware (Docling FAST)
    2. Native Digital + Complex → VLM Docling (GPT-4o)
    3. Scanned + Table-Heavy → VLM Docling (Claude 3.5)
    4. Scanned + Simple → Vision-Augmented (Gemini + GCP)
    """
    
    # Use VLM for complex layouts
    if profile.layout_complexity in ["table_heavy", "multi_column"]:
        return self.vlm_docling_extractor
    
    # Use VLM for high-value documents
    if profile.total_pages > 50 and profile.domain_hint == "financial":
        return self.vlm_docling_extractor
    
    # Existing logic for other cases
    ...
```

### Step 3: Configuration
**File**: `rubric/extraction_rules.yaml`

```yaml
extraction_strategies:
  vlm_docling:
    enabled: true
    default_model: "gpt-4o"  # or claude-3.5-sonnet, pixtral
    fallback_model: "gpt-4o-mini"  # cheaper fallback
    max_cost_per_page: 0.05  # $0.05/page for VLM
    use_for_complex_layouts: true
    use_for_table_heavy: true
    
  # Model-specific configs
  models:
    gpt-4o:
      cost_per_page: 0.03
      max_pages: 100
      timeout: 30
    claude-3.5-sonnet:
      cost_per_page: 0.04
      max_pages: 100
      timeout: 30
    pixtral:
      cost_per_page: 0.02
      max_pages: 200
      timeout: 20
```

### Step 4: Environment Variables
**File**: `.env`

```bash
# VLM API Keys
OPENAI_API_KEY=sk-...           # For GPT-4o
ANTHROPIC_API_KEY=sk-ant-...    # For Claude 3.5 Sonnet
MISTRAL_API_KEY=...             # For Pixtral

# VLM Pipeline Config
VLM_DEFAULT_MODEL=gpt-4o
VLM_FALLBACK_MODEL=gpt-4o-mini
VLM_MAX_COST_PER_DOC=5.0
```

### Step 5: Cost Tracking
**File**: `src/monitoring.py`

```python
class VLMCostTracker:
    """Track VLM API costs per document"""
    
    def __init__(self):
        self.costs = {
            "gpt-4o": 0.03,      # per page
            "claude-3.5": 0.04,
            "pixtral": 0.02
        }
    
    def estimate_cost(self, model: str, pages: int) -> float:
        return self.costs.get(model, 0.03) * pages
    
    def check_budget(self, estimated_cost: float, max_budget: float):
        if estimated_cost > max_budget:
            raise BudgetExceededError(...)
```

## Usage Examples

### Example 1: Process with GPT-4o
```python
from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter

triage = TriageAgent()
router = ExtractionRouter(vlm_model="gpt-4o")

profile = triage.profile_document("complex_financial_report.pdf")
extracted_doc = router.extract("complex_financial_report.pdf", profile)

# VLM automatically used for complex layouts
print(f"Strategy: {extracted_doc.extraction_strategy}")  # vlm_docling
print(f"Tables: {len(extracted_doc.tables)}")  # High accuracy
```

### Example 2: CLI Usage
```bash
# Use Docling VLM Pipeline directly
docling --pipeline vlm --vlm-model gpt-4o document.pdf

# Or through our pipeline
python3 -m src.cli extract \
  --pdf document.pdf \
  --strategy vlm_docling \
  --vlm-model claude-3.5-sonnet
```

### Example 3: Batch Processing
```python
from src.strategies.vlm_docling import VLMDoclingExtractor

extractor = VLMDoclingExtractor(vlm_model="pixtral")

for pdf_file in pdf_files:
    profile = triage.profile_document(pdf_file)
    
    # Only use VLM for complex documents
    if profile.layout_complexity == "table_heavy":
        extracted_doc = extractor.extract(pdf_file, profile)
    else:
        # Use cheaper strategy
        extracted_doc = fast_extractor.extract(pdf_file, profile)
```

## Decision Matrix: When to Use VLM Pipeline

| Document Type | Pages | Layout | Recommended Strategy | Cost/Page |
|--------------|-------|--------|---------------------|-----------|
| Native Digital | <20 | Simple | Docling FAST | $0.001 |
| Native Digital | <20 | Complex | VLM (GPT-4o) | $0.03 |
| Native Digital | >50 | Table-Heavy | VLM (Claude 3.5) | $0.04 |
| Scanned | Any | Simple | Gemini + GCP | $0.02 |
| Scanned | Any | Complex | VLM (GPT-4o) | $0.03 |

## Performance Comparison

| Strategy | Speed | Accuracy | Cost | Use Case |
|----------|-------|----------|------|----------|
| Docling FAST | ⚡⚡⚡ | ⭐⭐⭐ | $ | Simple native PDFs |
| Docling VLM | ⚡⚡ | ⭐⭐⭐⭐⭐ | $$$ | Complex layouts |
| Gemini Vision | ⚡⚡ | ⭐⭐⭐⭐ | $$ | Scanned docs |
| pdfplumber | ⚡⚡⚡ | ⭐⭐ | $ | Basic text |

## Implementation Priority

### Phase 1: Core Integration (Week 1)
- [ ] Create `VLMDoclingExtractor` class
- [ ] Add VLM model configuration
- [ ] Implement cost tracking
- [ ] Add to strategy selection logic

### Phase 2: Multi-Model Support (Week 2)
- [ ] Support GPT-4o
- [ ] Support Claude 3.5 Sonnet
- [ ] Support Pixtral
- [ ] Implement automatic fallback

### Phase 3: Optimization (Week 3)
- [ ] Batch processing optimization
- [ ] Caching for repeated documents
- [ ] Cost optimization strategies
- [ ] Performance benchmarking

## Testing Plan

```python
# Test VLM extraction
def test_vlm_extraction():
    extractor = VLMDoclingExtractor(vlm_model="gpt-4o")
    
    # Test with complex table document
    result = extractor.extract("complex_tables.pdf", profile)
    
    assert len(result.tables) > 0
    assert result.confidence_score > 0.9
    assert result.extraction_strategy == "vlm_docling"
```

## Monitoring & Logging

```python
# Log VLM usage
logger.info(f"VLM Pipeline: {vlm_model}")
logger.info(f"Pages processed: {pages}")
logger.info(f"Cost: ${cost:.4f}")
logger.info(f"Processing time: {time_ms}ms")

# Track in ledger
{
  "strategy": "vlm_docling",
  "vlm_model": "gpt-4o",
  "pages": 45,
  "cost": 1.35,
  "time_ms": 12500,
  "confidence": 0.95
}
```

## Next Steps

1. **Install Docling VLM support**: `pip install docling[vlm]`
2. **Get API keys**: OpenAI, Anthropic, or Mistral
3. **Implement `VLMDoclingExtractor`** class
4. **Update strategy selection** logic
5. **Test with complex documents**
6. **Monitor costs and performance**

## Expected Outcomes

- **10-50x faster** than local PyTorch models
- **95%+ accuracy** on complex tables
- **Zero local compute** requirements
- **Scalable** to thousands of documents
- **Cost-effective** for high-value documents
