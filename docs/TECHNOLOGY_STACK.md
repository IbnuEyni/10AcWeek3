# Document Intelligence Refinery - Technology Stack by Stage

## Complete Pipeline Flow

```
Stage 1 (Triage) → Stage 2 (Extraction) → Stage 3 (Chunking) → 
Stage 4 (PageIndex) → Stage 5 (Query) → ProvenanceChain
```

---

## Stage 1: Triage Agent (Short-Circuit Waterfall)

**Purpose**: Document classification with cost-optimized sequential checks

### Short-Circuit Waterfall Algorithm

Stage 1 uses a **sequential waterfall** that short-circuits as soon as a definitive classification is made:

| Pass | Tool | Time | Check | Action | Short-Circuit? |
|------|------|------|-------|--------|----------------|
| **1. Microsecond** | **PyMuPDF** | <1ms | `page.get_fonts()` | If no fonts → `scanned_image` → Route to Strategy C | ✓ HALT |
| **2. Millisecond** | **pdfplumber** | ~10ms | Image-to-page ratio | If >80% image → `hybrid` → Route to Strategy C | ✓ HALT |
| **3. Second** | **Docling (Fast)** | ~100ms | Layout complexity | Detect `multi_column` or `table_heavy` → Route A vs B | Continue |

### Sequential Logic

```python
# Pass 1: Microsecond Check (PyMuPDF)
fonts = page.get_fonts()
if not fonts:
    return origin_type="scanned_image", route_to=Strategy_C
    # HALT - Skip pdfplumber and Docling

# Pass 2: Millisecond Check (pdfplumber)  
image_ratio = calculate_image_ratio(page)
if image_ratio > 0.8:
    return origin_type="hybrid", route_to=Strategy_C
    # HALT - Skip Docling

# Pass 3: Second Check (Docling Fast Mode)
# Only runs if document is confirmed native digital
layout = docling_fast_mode.detect_layout()
if layout in ["multi_column", "table_heavy"]:
    return layout_complexity=layout, route_to=Strategy_B
else:
    return layout_complexity="single_column", route_to=Strategy_A
```

### Performance Impact

| Document Type | Tools Run | Time | Cost Savings |
|---------------|-----------|------|--------------|
| Scanned Image | PyMuPDF only | <1ms | 99% faster (skip pdfplumber + Docling) |
| Hybrid (80% image) | PyMuPDF + pdfplumber | ~10ms | 90% faster (skip Docling) |
| Native Digital | All three | ~110ms | Baseline |

### Tool Details

#### Pass 1: PyMuPDF (Microsecond Check)
- **Purpose**: Instant scanned image detection
- **Method**: `page.get_fonts()` - checks font metadata
- **Decision**: No fonts = scanned image
- **Time**: <1ms per page
- **Short-circuit**: Routes directly to Strategy C

#### Pass 2: pdfplumber (Millisecond Check)
- **Purpose**: Hybrid document detection
- **Method**: Calculate `image_area / page_area`
- **Decision**: >80% image = hybrid/scanned
- **Time**: ~10ms per page
- **Short-circuit**: Routes directly to Strategy C

#### Pass 3: Docling Fast Mode (Second Check)
- **Purpose**: Layout complexity detection (native digital only)
- **Method**: Fast pipeline with `do_ocr=False`, `do_table_structure=False`
- **Decision**: Detect multi-column or table-heavy layouts
- **Time**: ~100ms per page
- **No short-circuit**: Final classification for Strategy A vs B

**Output**: `DocumentProfile` (origin_type, layout_complexity, extraction_strategy)

---

## Stage 2: Extraction Router

**Purpose**: Multi-strategy content extraction

### Strategy A: Fast Text (Native Digital PDFs)

| Component | Library/Tool | Use Case |
|-----------|-------------|----------|
| Text Extraction | **pdfplumber** | Native digital, single-column |
| Table Detection | **pdfplumber.find_tables()** | Simple tables |
| Confidence Scoring | **Custom heuristics** | Character density analysis |

**Triggers**: `origin_type=native_digital` AND `layout_complexity=single_column`

---

### Strategy B: Layout-Aware (Multi-column/Table-heavy)

| Component | Library/Tool | Use Case |
|-----------|-------------|----------|
| Document Parsing | **Docling** | Complex layouts, multi-column |
| Alternative | **MinerU** | Advanced table extraction |
| Table Structure | **Docling TableStructure** | Header-row relationships |
| Reading Order | **Docling reading_order** | Correct text flow |

**Triggers**: `layout_complexity IN [multi_column, table_heavy, mixed]`

---

### Strategy C: Vision-Augmented (Bounding-Box Micro-Cropping)

| Component | Library/Tool | Use Case |
|-----------|-------------|----------|
| Bbox Extraction | **Strategy A/B confidence metadata** | Extract failed element coordinates |
| Micro-Cropping | **PIL/Pillow** | Crop specific bbox from page |
| Page Rendering | **PyMuPDF** | Render page to image |
| Vision Model | **Google Gemini Flash 2.5** | OCR on cropped snippet only |
| API | **google.generativeai** | Multimodal understanding |

**Triggers**: 
- `origin_type=scanned_image` (full page)
- Escalation Guard: Low-confidence table/chart from Strategy A/B (micro-crop only)

**Cost Optimization**: 
- Full page: $0.02/page (scanned documents)
- Micro-crop: $0.002/element (10x cheaper - only failed elements)

### Micro-Cropping Workflow

```python
# Extract bbox from low-confidence element
bbox = failed_table.bbox  # {x0, y0, x1, y1, page}

# Render page and crop
page_image = render_page(pdf_path, bbox.page)
cropped = page_image.crop((bbox.x0, bbox.y0, bbox.x1, bbox.y1))

# Send only cropped snippet to Gemini
response = gemini.generate_content([cropped, "Extract table as JSON"])
```

**Key Advantage**: 90% cost reduction by sending only failed elements, not full pages

---

## Stage 3: Semantic Chunking

**Purpose**: Create Logical Document Units (LDUs)

### Tools/Libraries Used (All Document Types)

| Component | Library/Tool | Purpose |
|-----------|-------------|---------|
| Token Counting | **tiktoken** | GPT tokenizer for chunk sizing |
| Content Hashing | **hashlib (SHA-256)** | Provenance verification |
| Chunking Logic | **Custom rules** | Table integrity, figure-caption binding |
| Validation | **Pydantic** | LDU schema validation |

**Output**: List of `LDU` objects with content, metadata, and provenance

---

## Stage 4: PageIndex Builder (AI-Native DOM Parsing)

**Purpose**: Hierarchical navigation using Docling's native Document Object Model

### Tools/Libraries Used (All Document Types)

| Component | Library/Tool | Purpose |
|-----------|-------------|---------|
| DOM Extraction | **Docling Document Object Model** | Native hierarchical tags (heading_1, heading_2, paragraph) |
| Section Tree | **Docling iterate_items()** | Automatic hierarchy from DOM structure |
| Summary Generation | **Gemini Flash 2.5 (optional)** | LLM-generated section summaries |
| Serialization | **JSON** | PageIndex storage |

### AI-Native Approach

```python
# Docling provides native DOM with hierarchical tags
result = converter.convert(pdf_path)

for item in result.document.iterate_items():
    if item.type == 'heading_1':
        section = Section(title=item.text, level=1)
    elif item.type == 'heading_2':
        subsection = Section(title=item.text, level=2)
```

**Key Advantage**: No regex - Docling's AI models understand document structure

**Output**: `PageIndex` with hierarchical sections from Docling DOM

---

## Stage 4.5: Fact Extraction (LLM Structured Outputs)

**Purpose**: Extract structured facts using LLM with Pydantic schemas

### Tools/Libraries Used (All Document Types)

| Component | Library/Tool | Purpose |
|-----------|-------------|---------|
| Fact Extraction | **Gemini Flash 2.5** | LLM with structured output |
| Schema Enforcement | **Pydantic** | Strictly enforced JSON schemas |
| Database | **SQLite3** | Fact storage |
| Validation | **Pydantic validators** | Type checking and validation |

### AI-Native Approach

```python
class ExtractedFact(BaseModel):
    key: str
    value: str
    unit: Optional[str]
    page: int

# Pass chunk to LLM with schema
response = gemini.generate_content(
    f"Extract facts from: {chunk}",
    generation_config={"response_mime_type": "application/json",
                      "response_schema": ExtractedFact}
)

facts = ExtractedFact.model_validate_json(response.text)
```

**Key Advantage**: No regex - LLM understands context and extracts facts accurately

**Output**: SQLite database with LLM-extracted facts

---

## Stage 5: Query Interface Agent

**Purpose**: Natural language querying with provenance

### Tool 1: PageIndex Navigate

| Component | Library/Tool | Purpose |
|-----------|-------------|---------|
| Tree Traversal | **Custom algorithm** | Section search |
| Keyword Matching | **String operations** | Query-to-section matching |

---

### Tool 2: Semantic Search

| Component | Library/Tool | Purpose |
|-----------|-------------|---------|
| Vector Store (Optional) | **ChromaDB** | Semantic similarity |
| Embeddings (Optional) | **Sentence Transformers** | Text embeddings |
| Fallback | **Keyword search** | Simple string matching |

---

### Tool 3: Structured Query

| Component | Library/Tool | Purpose |
|-----------|-------------|---------|
| Database | **SQLite3** | SQL queries over facts |
| Query Builder | **Custom templates** | NL to SQL conversion |

---

### Provenance Chain

| Component | Library/Tool | Purpose |
|-----------|-------------|---------|
| Citation Model | **Pydantic** | SourceCitation schema |
| Content Verification | **SHA-256 hashes** | Audit trail |
| Serialization | **JSON** | ProvenanceChain storage |

---

## Summary by Document Type

### Native Digital PDF

```
Stage 1: PyMuPDF (fonts exist) → pdfplumber (low image ratio) → Docling (layout)
Stage 2: pdfplumber (Strategy A)
Stage 3: tiktoken + custom chunking
Stage 4: Docling DOM → Section tree
Stage 5: SQLite + keyword search
```

### Scanned Image PDF

```
Stage 1: PyMuPDF (no fonts) → SHORT-CIRCUIT → Strategy C
Stage 2: Gemini Flash 2.5 (Strategy C)
Stage 3: tiktoken + custom chunking
Stage 4: Docling DOM → Section tree
Stage 5: SQLite + keyword search
```

### Mixed/Multi-column PDF

```
Stage 1: PyMuPDF (fonts exist) → pdfplumber (low image ratio) → Docling (complex layout)
Stage 2: Docling/MinerU (Strategy B)
Stage 3: tiktoken + custom chunking
Stage 4: Docling DOM → Section tree
Stage 5: SQLite + keyword search
```

---

## Core Dependencies

```python
# PDF Processing
pdfplumber>=0.10.0
PyMuPDF>=1.23.0
docling>=1.0.0  # Optional, for layout-aware

# Vision Models
google-generativeai>=0.3.0  # For scanned PDFs
Pillow>=10.0.0

# Data Processing
pydantic>=2.0.0
tiktoken>=0.5.0
python-dotenv>=1.0.0

# Storage
chromadb>=0.4.0  # Optional, for vector search

# Utilities
PyYAML>=6.0
rich>=13.0.0  # For demo UI
```

---

## Configuration-Driven Strategy Selection

All thresholds and routing logic are in `rubric/extraction_rules.yaml`:

```yaml
strategies:
  fast_text:
    triggers:
      - origin_type: native_digital
      - layout_complexity: single_column
    tool: pdfplumber
    
  layout_aware:
    triggers:
      - layout_complexity: [multi_column, table_heavy]
    tool: docling
    
  vision_augmented:
    triggers:
      - origin_type: scanned_image
    tool: gemini_flash_2_5
```

---

## Cost & Performance by Strategy

| Strategy | Tool | Cost/Page | Speed | Use Case |
|----------|------|-----------|-------|----------|
| Fast Text | pdfplumber | $0.001 | <0.1s | Native digital |
| Layout-Aware | Docling | $0.01 | 0.5-1s | Complex layouts |
| Vision-Augmented | Gemini | $0.02 | 1-2s | Scanned images |

---

## Key Insight

The pipeline uses **different tools at Stage 2** based on document type, but **the same tools at all other stages**. This allows:

- Consistent LDU format regardless of extraction method
- Unified query interface across document types
- Graceful degradation (fallbacks at each stage)
- Cost optimization (cheapest viable strategy)
