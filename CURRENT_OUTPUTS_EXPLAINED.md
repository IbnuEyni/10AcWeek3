# What You Get From Current Implementation

## Overview

We've implemented **Stages 1-2** (54% of the project). Here's exactly what outputs you get when you process a document.

---

## How It Works

### Simple Usage

```python
from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter

# Initialize
triage = TriageAgent()
router = ExtractionRouter()

# Process any PDF
profile = triage.profile_document("your_document.pdf")
extracted = router.extract("your_document.pdf", profile)

# Access results
print(f"Text blocks: {len(extracted.text_blocks)}")
print(f"Tables: {len(extracted.tables)}")
print(f"Figures: {len(extracted.figures)}")
```

---

## Output 1: Document Profile

**Location:** `.refinery/profiles/{doc_id}.json`

**What it contains:**
```json
{
    "doc_id": "test",
    "filename": "test.pdf",
    "origin_type": "scanned_image",           // digital or scanned
    "layout_complexity": "single_column",      // layout type
    "language": "en",
    "language_confidence": 0.95,
    "domain_hint": "general",                  // financial, legal, etc.
    "estimated_extraction_cost": "needs_vision_model",  // strategy recommendation
    "total_pages": 1,
    "character_density": 0.00015,              // text density metric
    "image_ratio": 0.0,                        // image coverage
    "has_font_metadata": true,
    "table_count_estimate": 0
}
```

**What this tells you:**
- Is the PDF digital or scanned?
- How complex is the layout?
- What domain is it (financial, legal, technical)?
- Which extraction strategy should be used?
- How much will it cost to process?

---

## Output 2: Extracted Content

**Returned as:** `ExtractedDocument` object

**What it contains:**

### Text Blocks
```python
extracted.text_blocks = [
    TextBlock(
        content="The company reported strong growth...",
        bbox=BoundingBox(x0=100, y0=200, x1=400, y1=250, page=1),
        reading_order=0
    ),
    ...
]
```

**Each text block has:**
- `content`: The actual text
- `bbox`: Exact location on page (x0, y0, x1, y1, page)
- `reading_order`: Sequence number

### Tables
```python
extracted.tables = [
    Table(
        table_id="table_1_0",
        headers=["Quarter", "Revenue", "Profit"],
        rows=[
            ["Q1 2023", "$1.2M", "$200K"],
            ["Q2 2023", "$1.5M", "$300K"]
        ],
        bbox=BoundingBox(x0=100, y0=300, x1=500, y1=400, page=1)
    ),
    ...
]
```

**Each table has:**
- `table_id`: Unique identifier
- `headers`: Column headers
- `rows`: All data rows
- `bbox`: Location on page

### Figures
```python
extracted.figures = [
    Figure(
        figure_id="fig_page2_0",
        page=2,
        bbox=BoundingBox(x0=100, y0=200, x1=400, y1=500, page=2),
        caption="Figure 1: Revenue Growth 2020-2023",
        image_path=".refinery/figures/doc_id/fig_page2_0.png",
        metadata={
            "width": 300,
            "height": 300,
            "format": "PNG",
            "md5_hash": "a3f5b2..."
        }
    ),
    ...
]
```

**Each figure has:**
- `figure_id`: Unique identifier
- `page`: Page number
- `bbox`: Location on page
- `caption`: Extracted caption (if found)
- `image_path`: Where the image is saved
- `metadata`: Dimensions, format, hash

---

## Output 3: Extraction Ledger

**Location:** `.refinery/extraction_ledger.jsonl`

**What it contains:**
```json
{
    "timestamp": "2024-03-04T12:28:45",
    "doc_id": "test",
    "filename": "test.pdf",
    "strategy_used": "vision_augmented",      // Which strategy was used
    "confidence_score": 0.8,                  // How confident the extraction is
    "cost_estimate": 0.02,                    // Estimated cost in dollars
    "processing_time_ms": 2529.75,            // How long it took
    "escalation_triggered": false,            // Did it escalate to better strategy?
    "origin_type": "scanned_image",
    "layout_complexity": "single_column"
}
```

**What this tells you:**
- Complete audit trail of every extraction
- Which strategy was used and why
- How confident the system is in the results
- How much it cost
- How long it took
- Whether escalation happened

---

## Output 4: Extracted Figures

**Location:** `.refinery/figures/{doc_id}/`

**What you get:**
- All images extracted from the PDF
- Saved as PNG files
- Named with figure IDs
- Organized by document

**Example:**
```
.refinery/figures/
└── annual_report_2023/
    ├── fig_page2_0.png
    ├── fig_page5_0.png
    ├── fig_page5_1.png
    └── fig_page12_0.png
```

**Features:**
- MD5 deduplication (same image not saved twice)
- Metadata preserved (dimensions, format, DPI)
- Captions bound to figures

---

## What You Can Do With These Outputs

### 1. Verify Extraction Quality
```python
# Check confidence
if extracted.confidence_score < 0.7:
    print("Low confidence - review manually")

# Check what was extracted
print(f"Found {len(extracted.tables)} tables")
print(f"Found {len(extracted.figures)} figures")
```

### 2. Access Structured Data
```python
# Get all tables
for table in extracted.tables:
    print(f"Table: {table.table_id}")
    print(f"Headers: {table.headers}")
    for row in table.rows:
        print(f"  {row}")
```

### 3. Find Specific Content
```python
# Find text on specific page
page_2_text = [
    block.content 
    for block in extracted.text_blocks 
    if block.bbox.page == 2
]

# Find all figures with captions
captioned_figures = [
    fig for fig in extracted.figures 
    if fig.caption
]
```

### 4. Track Costs
```python
# Read ledger
import json
with open('.refinery/extraction_ledger.jsonl') as f:
    entries = [json.loads(line) for line in f]

# Calculate total cost
total_cost = sum(e['cost_estimate'] for e in entries)
print(f"Total spent: ${total_cost:.2f}")
```

### 5. Audit Processing
```python
# Check which strategy was used
for entry in entries:
    print(f"{entry['doc_id']}: {entry['strategy_used']} "
          f"(confidence: {entry['confidence_score']:.2f})")
```

---

## Real-World Example

### Input
```
data/annual_report_2023.pdf (120 pages)
```

### Stage 1 Output (Profile)
```json
{
    "doc_id": "annual_report_2023",
    "origin_type": "native_digital",
    "layout_complexity": "table_heavy",
    "domain_hint": "financial",
    "total_pages": 120,
    "estimated_extraction_cost": "needs_layout_model"
}
```

### Stage 2 Output (Extracted)
```python
ExtractedDocument(
    doc_id="annual_report_2023",
    text_blocks=[...],  # 450 text blocks
    tables=[...],       # 23 tables with structure
    figures=[...],      # 15 figures with captions
    extraction_strategy="layout_aware",
    confidence_score=0.85
)
```

### Artifacts Created
```
.refinery/
├── profiles/
│   └── annual_report_2023.json
├── figures/
│   └── annual_report_2023/
│       ├── fig_page5_0.png
│       ├── fig_page12_0.png
│       └── ... (15 images)
└── extraction_ledger.jsonl (new entry added)
```

---

## Enhanced Features (Automatically Applied)

### 1. Enhanced Table Extraction
- Tables preserve merged cells
- Headers detected automatically
- Structure classified (simple/nested/complex)
- Can export to markdown

### 2. Figure-Caption Binding
- Figures automatically matched to captions
- Pattern matching ("Figure 1:", "Fig. 2:", etc.)
- Spatial proximity search
- Confidence scoring

### 3. Multi-Column Layout
- Detects multi-column layouts
- Corrects reading order
- Prevents text jumbling

### 4. Handwriting OCR
- Tries 4 different OCR engines
- Automatic fallback chain
- Works offline (Tesseract) or online (Gemini, Azure, Google)

### 5. Cost Tracking
- Every extraction logged with cost
- Budget guards prevent overspending
- Detailed cost breakdown

### 6. Confidence-Based Escalation
- Low confidence triggers automatic retry
- Escalates to better (more expensive) strategy
- Prevents bad data from going through

---

## What's NOT Yet Implemented

### Stage 3: Semantic Chunking
- Breaking content into RAG-ready chunks
- Preserving logical relationships
- Adding metadata and context

### Stage 4: PageIndex
- Navigation tree
- Section summaries
- Entity extraction

### Stage 5: Query Interface
- Question answering
- Provenance tracking
- Claim verification

---

## Summary

**What you get NOW (Stages 1-2):**
✅ Document classification and profiling
✅ Multi-strategy extraction (fast/layout/vision)
✅ Structured text, tables, and figures
✅ Enhanced table extraction
✅ Figure-caption binding
✅ Multi-column layout correction
✅ Handwriting OCR support
✅ Complete audit trail
✅ Cost tracking
✅ Confidence scoring

**What you DON'T get yet (Stages 3-5):**
⏳ RAG-ready chunks
⏳ Navigation tree
⏳ Question answering
⏳ Provenance verification

**Current Status:** 54% Complete, Production-Ready Foundation

---

## Try It Yourself

```bash
# Run the demo
python3 simple_demo.py

# Check the outputs
cat .refinery/profiles/test.json
cat .refinery/extraction_ledger.jsonl
ls .refinery/figures/
```

**Next:** Implement Stages 3-5 to complete the system!
