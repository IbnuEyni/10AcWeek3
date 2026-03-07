# Document Intelligence Refinery - Demo Guide

## Quick Start

### 1. Install Demo Dependencies

```bash
# Install with uv (recommended)
uv pip install -e ".[demo]"

# Or install all features including demo
uv pip install -e ".[all]"

# Or with pip
pip install streamlit pillow
```

### 2. Run the Demo

```bash
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## Demo Walkthrough

### Stage 1: Document Triage 🔍

**What it shows:**
- Document profiling (origin type, layout complexity, character density)
- Strategy selection rationale
- Automatic routing to optimal extraction strategy

**Key insights:**
- Native PDFs → Layout-Aware (Docling FAST)
- Scanned PDFs → Vision-Augmented (Gemini + OCR)
- Table detection and complexity analysis

### Stage 2: Multi-Strategy Extraction ⚙️

**What it shows:**
- Side-by-side view: Original PDF vs Extracted Content
- Extraction ledger with confidence scores, processing time, and cost
- Structured table extraction (JSON with headers and values)
- Text blocks with bounding boxes

**Key features:**
- Click to view extraction ledger entry
- Inspect table structure as JSON
- View text blocks with reading order

### Stage 3: PageIndex Navigation 🗂️

**What it shows:**
- Hierarchical section tree
- Section statistics (pages, LDUs, data types)
- Interactive page navigation
- Section summaries

**Try this:**
- Enter a page number to find its section
- Explore the section hierarchy
- View data types present in each section

### Stage 4: Query with Provenance 💬

**What it shows:**
- Natural language query interface
- Answers with full provenance chain
- Citation details (page number, bounding box, content hash)
- Side-by-side: Answer + Source PDF page

**Sample queries:**
- "What is the total revenue?"
- "List all tables in the document"
- "Summarize the key findings"

**Provenance includes:**
- Document name and ID
- Page number
- Bounding box coordinates (x0, y0, x1, y1)
- Content hash for verification
- Excerpt from source

## Demo Features

### ✅ Progressive Pipeline
Each stage builds on the previous one. You can see the pipeline progress step-by-step.

### ✅ Interactive Visualizations
- PDF page rendering
- Section tree navigation
- Expandable details

### ✅ Full Provenance
Every answer includes citations with exact page and bounding box coordinates.

### ✅ Cost Tracking
View extraction costs and processing times in the ledger.

## Tips for Best Results

### Document Selection
- **Native PDFs**: Financial reports, technical specs, research papers
- **Scanned PDFs**: Legal documents, historical records, forms
- **Table-heavy**: Annual reports, data sheets, invoices

### Query Tips
- Be specific: "What is the revenue in Q4 2023?" vs "Tell me about revenue"
- Ask about structure: "How many tables are in section 3?"
- Request summaries: "Summarize the executive summary section"

## Troubleshooting

### PDF Rendering Issues
If PDF pages don't render, ensure PyMuPDF is installed:
```bash
uv pip install pymupdf
```

### Extraction Errors
- Check `.env` file for API keys (GEMINI_API_KEY for scanned docs)
- Verify document is not password-protected
- Check `.refinery/extraction_ledger.jsonl` for error details

### Query Failures
- Ensure PageIndex was built successfully
- Check that LDUs were created in Stage 3
- Verify document ID matches across stages

## Architecture Highlights

### Stage Flow
```
Upload PDF → Triage → Extraction → Chunking → PageIndex → Query
              ↓          ↓            ↓          ↓          ↓
           Profile   ExtractedDoc   LDUs    PageIndex  Provenance
```

### Artifacts Created
- `.refinery/profiles/{doc_id}_profile.json` - Document profile
- `.refinery/extraction_ledger.jsonl` - Extraction metadata
- `.refinery/ldus/{doc_id}_ldus.json` - Logical Document Units
- `.refinery/pageindex/{doc_id}_pageindex.json` - Navigation index

## Advanced Usage

### Custom Extraction Rules
Edit `rubric/extraction_rules.yaml` to customize:
- Confidence thresholds
- Cost limits
- Chunking parameters
- Strategy selection logic

### Batch Processing
For multiple documents, use the CLI:
```bash
python -m src.main process data/*.pdf
```

### API Integration
Import agents directly in your code:
```python
from src.agents import TriageAgent, ExtractionRouter, QueryAgent

triage = TriageAgent()
profile = triage.profile_document("document.pdf")
```

## Performance Benchmarks

| Document Type | Pages | Strategy | Time | Cost | Confidence |
|--------------|-------|----------|------|------|------------|
| Financial Report | 120 | Layout | 8.2s | $1.20 | 0.87 |
| Scanned Legal | 45 | Vision | 12.5s | $0.90 | 0.82 |
| Technical Spec | 80 | Fast Text | 2.1s | $0.08 | 0.91 |

## Next Steps

1. **Try different document types** - Compare extraction quality
2. **Explore PageIndex navigation** - Find information without search
3. **Test provenance accuracy** - Verify citations against source PDF
4. **Customize extraction rules** - Tune for your use case

## Support

For issues or questions:
- Check `.refinery/extraction_ledger.jsonl` for errors
- Review `docs/DOMAIN_NOTES.md` for architecture details
- See `README.md` for full documentation
