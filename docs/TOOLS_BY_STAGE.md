# Quick Reference: Tools by Stage & Document Type

## Native Digital PDF

| Stage | Tool/Library | What It Does |
|-------|-------------|--------------|
| **1. Triage** | pdfplumber + Docling (fast) | Analyze character density, detect layout |
| **2. Extraction** | **pdfplumber** | Extract text, tables (Strategy A) |
| **3. Chunking** | tiktoken + hashlib | Create LDUs, hash content |
| **4. PageIndex** | Regex + custom | Build section hierarchy |
| **4.5 Facts** | Regex + SQLite3 | Extract & store facts |
| **5. Query** | SQLite3 + keyword search | Answer queries with provenance |

**Cost**: ~$0.001/page | **Speed**: Fast

---

## Scanned Image PDF

| Stage | Tool/Library | What It Does |
|-------|-------------|--------------|
| **1. Triage** | pdfplumber + Docling (fast) | Detect scanned image (low char density) |
| **2. Extraction** | **Gemini Flash 2.5** | Vision model OCR (Strategy C) |
| **3. Chunking** | tiktoken + hashlib | Create LDUs, hash content |
| **4. PageIndex** | Regex + custom | Build section hierarchy |
| **4.5 Facts** | Regex + SQLite3 | Extract & store facts |
| **5. Query** | SQLite3 + keyword search | Answer queries with provenance |

**Cost**: ~$0.02/page | **Speed**: Slower (API calls)

---

## Mixed/Multi-column/Table-heavy PDF

| Stage | Tool/Library | What It Does |
|-------|-------------|--------------|
| **1. Triage** | pdfplumber + Docling (fast) | Detect multi-column, count tables |
| **2. Extraction** | **Docling** (or MinerU) | Layout-aware extraction (Strategy B) |
| **3. Chunking** | tiktoken + hashlib | Create LDUs, hash content |
| **4. PageIndex** | Regex + custom | Build section hierarchy |
| **4.5 Facts** | Regex + SQLite3 | Extract & store facts |
| **5. Query** | SQLite3 + keyword search | Answer queries with provenance |

**Cost**: ~$0.01/page | **Speed**: Medium

---

## Key Insight

**Only Stage 2 changes based on document type!**

All other stages use the same tools regardless of whether the document is:
- Native digital
- Scanned image  
- Mixed/complex layout

This is because Stage 2 normalizes everything into a common `ExtractedDocument` format.

---

## Stage 2 Strategy Selection

```python
if origin_type == "native_digital" and layout_complexity == "single_column":
    → Use pdfplumber (Strategy A) - CHEAPEST
    
elif layout_complexity in ["multi_column", "table_heavy"]:
    → Use Docling (Strategy B) - MEDIUM COST
    
elif origin_type == "scanned_image":
    → Use Gemini Flash (Strategy C) - MOST EXPENSIVE
```

---

## Core Dependencies

```bash
# Stage 1 & 2A
pip install pdfplumber PyMuPDF

# Stage 2B (optional)
pip install docling

# Stage 2C (optional)
pip install google-generativeai Pillow

# Stage 3-5
pip install tiktoken pydantic PyYAML

# Stage 5 (optional)
pip install chromadb  # For vector search
```

---

## Configuration File

All thresholds in `rubric/extraction_rules.yaml`:

```yaml
strategies:
  fast_text:
    tool: pdfplumber
    cost_per_page: 0.001
    
  layout_aware:
    tool: docling
    cost_per_page: 0.01
    
  vision_augmented:
    tool: gemini_flash_2_5
    cost_per_page: 0.02
```

---

## Performance Comparison

| Document Type | Stage 2 Tool | Time/Page | Cost/Page | Accuracy |
|---------------|-------------|-----------|-----------|----------|
| Native Digital | pdfplumber | 0.01s | $0.001 | High |
| Multi-column | Docling | 0.1s | $0.01 | Very High |
| Scanned Image | Gemini | 1-2s | $0.02 | High |

---

## Escalation Flow

```
Start with cheapest strategy
    ↓
Measure confidence
    ↓
If low → Escalate to next strategy
    ↓
Repeat until confidence threshold met
```

This ensures cost optimization while maintaining quality!
