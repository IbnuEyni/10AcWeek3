# Document Intelligence Refinery

Enterprise-grade agentic pipeline for unstructured document extraction at scale.

## Overview

The Document Intelligence Refinery is a production-ready system that transforms heterogeneous document corpora (PDFs, scanned images, reports) into structured, queryable, spatially-indexed knowledge.

### Key Features

- **Multi-Strategy Extraction**: Automatic routing between fast text, layout-aware, and vision-augmented extraction
- **Confidence-Gated Escalation**: Low-confidence extractions automatically escalate to more powerful strategies
- **Spatial Provenance**: Every extracted fact includes page number and bounding box coordinates
- **Cost-Aware Processing**: Budget guards and cost tracking per document
- **Enterprise Architecture**: Fully typed, testable, configuration-driven design

## Architecture

```
Input Documents → Triage → Extraction → Chunking → PageIndex → Query Interface
                    ↓          ↓           ↓           ↓            ↓
              DocumentProfile  ExtractedDoc  LDUs    PageIndex  ProvenanceChain
                    ↓
            [Fast Text]
            [Layout Aware]
            [Vision Augmented]
```

## Installation

### Quick Start (Recommended)

```bash
# Fast installation with uv (10-100× faster than pip)
./install_uv.sh

# Choose your profile:
# 1. Minimal  - Core only (pdfplumber, PyMuPDF)
# 2. Tier 1   - + Native PDF tools (Camelot, Docling)
# 3. Tier 2   - + Scanned PDF tools (Gemini API)
# 4. Full     - All features (recommended)
# 5. Dev      - Full + development tools
```

### Manual Installation

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create environment and install
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[all]"  # Install all features
```

### Traditional pip

```bash
./install.sh  # Interactive bash script
# or
pip install -e ".[all]"
```

### Environment Variables

Create a `.env` file:

```
GEMINI_API_KEY=your_key_here  # For vision extraction
# Get your key from: https://makersuite.google.com/app/apikey
```

## Quick Start

### Basic Pipeline (Stages 1-3)

```python
from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter
from src.agents.chunking import ChunkingAgent

# Initialize agents
triage = TriageAgent()
router = ExtractionRouter()
chunker = ChunkingAgent()

# Process document
profile = triage.profile_document("path/to/document.pdf")
extracted_doc = router.extract("path/to/document.pdf", profile)
ldus = chunker.process_document(extracted_doc, "path/to/document.pdf")

print(f"Extracted {len(extracted_doc.text_blocks)} text blocks")
print(f"Created {len(ldus)} LDUs")
```

### Full Pipeline with Query Interface (Stages 1-5)

```python
from src.agents import (
    TriageAgent, ExtractionRouter, ChunkingAgent,
    PageIndexBuilder, QueryAgent
)

# Run full pipeline
triage = TriageAgent()
router = ExtractionRouter()
chunker = ChunkingAgent()
indexer = PageIndexBuilder()
query_agent = QueryAgent()

# Process
profile = triage.profile_document("document.pdf")
extracted_doc = router.extract("document.pdf", profile)
ldus = chunker.process_document(extracted_doc, "document.pdf")
page_index = indexer.build_index(extracted_doc, ldus)

# Query with provenance
result = query_agent.query("What is the total revenue?", doc_id=profile.doc_id)
print(result.answer)
for citation in result.citations:
    print(f"Source: {citation.document_name}, Page {citation.page_number}")
```

## Project Structure

```
document-intelligence-refinery/
├── src/
│   ├── models/              # Pydantic schemas
│   │   ├── document_profile.py
│   │   ├── extracted_document.py
│   │   ├── ldu.py
│   │   ├── pageindex.py
│   │   └── provenance.py
│   ├── agents/              # Core agents
│   │   ├── triage.py        # Document classifier
│   │   ├── extractor.py     # Extraction router
│   │   ├── chunking.py      # Semantic chunking
│   │   ├── pageindex_builder.py  # PageIndex builder
│   │   └── query_agent.py   # Query interface
│   ├── strategies/          # Extraction strategies
│   │   ├── base.py
│   │   ├── fast_text.py
│   │   ├── layout_aware.py
│   │   └── vision_augmented.py
│   └── utils/
│       ├── pdf_analyzer.py
│       ├── docling_helper.py
│       └── fact_extractor.py
├── rubric/
│   └── extraction_rules.yaml
├── .refinery/
│   ├── profiles/            # Document profiles (JSON)
│   ├── ldus/                # Logical Document Units
│   ├── pageindex/           # Page indices
│   ├── facts.db             # Fact database (SQLite)
│   └── extraction_ledger.jsonl
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
│   └── DOMAIN_NOTES.md
└── data/                    # Corpus documents
```

## Pipeline Stages

### Stage 1: Triage Agent
Classifies documents by origin type, layout complexity, and domain to select optimal extraction strategy.

### Stage 2: Extraction Router
Multi-strategy extraction with confidence-gated escalation:
- **Fast Text**: pdfplumber for native digital PDFs
- **Layout-Aware**: Docling for complex layouts
- **Vision-Augmented**: Gemini for scanned documents

### Stage 3: Semantic Chunking
Creates Logical Document Units (LDUs) that preserve:
- Table integrity (headers + rows)
- Figure-caption binding
- List coherence
- Section context

### Stage 4: PageIndex Builder
Builds hierarchical navigation structure:
- Section detection and hierarchy
- LDU-to-section mapping
- Section summaries
- Data type tracking

### Stage 5: Query Interface Agent
Natural language query interface with three tools:
- **PageIndex Navigate**: Section-based navigation
- **Semantic Search**: Vector/keyword search over LDUs
- **Structured Query**: SQL over extracted facts

Every answer includes full provenance: document name, page number, bounding box, and content hash.

## Extraction Strategies

### Strategy A: Fast Text
- **Tool**: pdfplumber
- **Cost**: $0.001/page
- **Use Case**: Native digital PDFs, single-column layouts
- **Confidence Threshold**: 0.7

### Strategy B: Layout-Aware
- **Tool**: Docling/MinerU
- **Cost**: $0.01/page
- **Use Case**: Multi-column, table-heavy documents
- **Confidence Threshold**: 0.75

### Strategy C: Vision-Augmented
- **Tool**: Gemini Flash 2.5 (Google AI)
- **Cost**: $0.02/page
- **Use Case**: Scanned images, handwritten content
- **Confidence Threshold**: 0.8

## Configuration

All extraction rules, thresholds, and costs are externalized in `rubric/extraction_rules.yaml`:

```yaml
confidence:
  escalation_threshold: 0.7

cost:
  max_per_document: 1.0

chunking:
  max_tokens: 512
  rules:
    - table_integrity
    - figure_caption_binding
    - list_coherence
```

## Demo Scripts

```bash
# Run complete 5-stage pipeline
python demo_full_pipeline.py data/sample.pdf

# Query processed document
python demo_query_interface.py sample

# Run stages 1-3 only
python demo_complete_pipeline.py data/sample.pdf
```

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src tests/

# Run specific test
poetry run pytest tests/unit/test_triage.py
```

## Artifacts

### Document Profiles
Located in `.refinery/profiles/`, one JSON per document:

```json
{
  "doc_id": "annual_report_2023",
  "origin_type": "native_digital",
  "layout_complexity": "table_heavy",
  "estimated_extraction_cost": "needs_layout_model",
  "confidence_score": 0.87
}
```

### Extraction Ledger
Located at `.refinery/extraction_ledger.jsonl`:

```json
{
  "doc_id": "annual_report_2023",
  "strategy_used": "layout_aware",
  "confidence_score": 0.85,
  "cost_estimate": 0.23,
  "processing_time_ms": 1240,
  "escalation_triggered": false
}
```

## Performance Benchmarks

| Document Class | Pages | Strategy | Time (s) | Cost ($) | Confidence |
|----------------|-------|----------|----------|----------|------------|
| Financial Report | 120 | Layout | 8.2 | 1.20 | 0.87 |
| Scanned Legal | 45 | Vision | 12.5 | 0.90 | 0.82 |
| Technical Spec | 80 | Fast Text | 2.1 | 0.08 | 0.91 |

## Roadmap

- [x] Phase 1: Triage Agent
- [x] Phase 2: Multi-Strategy Extraction
- [x] Phase 3: Semantic Chunking Engine
- [x] Phase 4: PageIndex Builder
- [x] Phase 5: Query Interface Agent
- [ ] Multi-document reasoning
- [ ] Incremental processing & caching
- [ ] Vector store optimization (FAISS/Qdrant)
- [ ] LLM-powered answer generation

## License

MIT

## Contact

For questions or support, contact the FDE team.
