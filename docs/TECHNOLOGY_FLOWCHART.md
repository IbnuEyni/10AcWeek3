# Technology Stack Flowchart

## Complete Pipeline with Tools/Libraries

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INPUT: PDF DOCUMENT                          │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 1: TRIAGE AGENT                                              │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Tools: pdfplumber + Docling (fast mode) + PyMuPDF            │  │
│  │ Purpose: Classify document type and complexity                │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  Output: DocumentProfile                                            │
│    - origin_type: native_digital | scanned_image | mixed           │
│    - layout_complexity: single_column | multi_column | table_heavy │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 2: EXTRACTION ROUTER (Multi-Strategy)                        │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  STRATEGY A      │  │  STRATEGY B      │  │  STRATEGY C      │  │
│  │  Fast Text       │  │  Layout-Aware    │  │  Vision Model    │  │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────────┤  │
│  │ Tool:            │  │ Tool:            │  │ Tool:            │  │
│  │ • pdfplumber     │  │ • Docling        │  │ • Gemini Flash   │  │
│  │                  │  │ • MinerU (alt)   │  │ • PIL/Pillow     │  │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────────┤  │
│  │ Triggers:        │  │ Triggers:        │  │ Triggers:        │  │
│  │ • Native digital │  │ • Multi-column   │  │ • Scanned image  │  │
│  │ • Single column  │  │ • Table-heavy    │  │ • Low confidence │  │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────────┤  │
│  │ Cost: $0.001/pg  │  │ Cost: $0.01/pg   │  │ Cost: $0.02/pg   │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                      │
│  Output: ExtractedDocument (text_blocks, tables, figures)           │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 3: SEMANTIC CHUNKING ENGINE                                  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Tools: tiktoken + hashlib + custom rules                      │  │
│  │ Purpose: Create Logical Document Units (LDUs)                 │  │
│  │                                                                │  │
│  │ Rules:                                                         │  │
│  │ • Table integrity (headers + rows together)                   │  │
│  │ • Figure-caption binding                                       │  │
│  │ • List coherence                                               │  │
│  │ • Section context preservation                                 │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  Output: List[LDU] with content, metadata, provenance               │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 4: PAGEINDEX BUILDER                                         │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Tools: Regex + Custom tree builder + JSON                     │  │
│  │ Purpose: Build hierarchical navigation structure              │  │
│  │                                                                │  │
│  │ Features:                                                      │  │
│  │ • Section detection (headings, numbering)                     │  │
│  │ • Parent-child hierarchy                                       │  │
│  │ • LDU-to-section mapping                                       │  │
│  │ • Section summaries                                            │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  Output: PageIndex (hierarchical section tree)                      │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 4.5: FACT EXTRACTION                                         │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Tools: Regex + SQLite3                                         │  │
│  │ Purpose: Extract structured facts for SQL queries             │  │
│  │                                                                │  │
│  │ Extracts:                                                      │  │
│  │ • Table cells (header-value pairs)                            │  │
│  │ • Text patterns ("Revenue: $4.2B")                            │  │
│  │ • Numerical facts with units                                  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  Output: SQLite database (.refinery/facts.db)                       │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STAGE 5: QUERY INTERFACE AGENT                                     │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  TOOL 1          │  │  TOOL 2          │  │  TOOL 3          │  │
│  │  PageIndex       │  │  Semantic        │  │  Structured      │  │
│  │  Navigate        │  │  Search          │  │  Query           │  │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────────┤  │
│  │ Tools:           │  │ Tools:           │  │ Tools:           │  │
│  │ • Tree traversal │  │ • ChromaDB (opt) │  │ • SQLite3        │  │
│  │ • Keyword match  │  │ • Keyword search │  │ • SQL templates  │  │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────────┤  │
│  │ Use Case:        │  │ Use Case:        │  │ Use Case:        │  │
│  │ • Section nav    │  │ • Content search │  │ • Numerical data │  │
│  │ • "Where is X?"  │  │ • "Explain Y"    │  │ • "What is Z?"   │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                      │
│  Auto-selects best tool based on query type                         │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  OUTPUT: PROVENANCE CHAIN                                           │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Tools: Pydantic + SHA-256 + JSON                               │  │
│  │                                                                │  │
│  │ Contains:                                                      │  │
│  │ • Query + Answer                                               │  │
│  │ • Citations (document, page, bbox, hash)                      │  │
│  │ • Confidence score                                             │  │
│  │ • Retrieval method used                                        │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Audit Mode: verify_claim() for claim verification                  │
└─────────────────────────────────────────────────────────────────────┘
```

## Document Type Routing

```
┌──────────────────┐
│  Native Digital  │
│      PDF         │
└────────┬─────────┘
         │
         ├─ Stage 1: pdfplumber + Docling
         ├─ Stage 2: pdfplumber (Strategy A) ← FAST & CHEAP
         ├─ Stage 3: tiktoken + custom
         ├─ Stage 4: Regex + tree
         └─ Stage 5: SQLite + keyword

┌──────────────────┐
│  Scanned Image   │
│      PDF         │
└────────┬─────────┘
         │
         ├─ Stage 1: pdfplumber + Docling
         ├─ Stage 2: Gemini Flash (Strategy C) ← EXPENSIVE BUT ACCURATE
         ├─ Stage 3: tiktoken + custom
         ├─ Stage 4: Regex + tree
         └─ Stage 5: SQLite + keyword

┌──────────────────┐
│  Multi-column/   │
│  Table-heavy     │
└────────┬─────────┘
         │
         ├─ Stage 1: pdfplumber + Docling
         ├─ Stage 2: Docling/MinerU (Strategy B) ← LAYOUT-AWARE
         ├─ Stage 3: tiktoken + custom
         ├─ Stage 4: Regex + tree
         └─ Stage 5: SQLite + keyword
```

## Key Libraries Summary

| Stage | Library | Purpose | All Types? |
|-------|---------|---------|------------|
| 1 | pdfplumber | PDF analysis | ✓ |
| 1 | Docling (fast) | Layout detection | ✓ |
| 2 | pdfplumber | Fast text extraction | Native only |
| 2 | Docling | Layout-aware extraction | Complex only |
| 2 | Gemini Flash | Vision extraction | Scanned only |
| 3 | tiktoken | Token counting | ✓ |
| 3 | hashlib | Content hashing | ✓ |
| 4 | Regex | Section detection | ✓ |
| 4.5 | SQLite3 | Fact storage | ✓ |
| 5 | ChromaDB | Vector search (optional) | ✓ |
| 5 | SQLite3 | Structured queries | ✓ |
| All | Pydantic | Schema validation | ✓ |

## Cost Optimization Strategy

```
Try Strategy A (pdfplumber) first
    ↓
Measure confidence
    ↓
If confidence < 0.7 → Escalate to Strategy B (Docling)
    ↓
If still low → Escalate to Strategy C (Gemini)
```

This ensures you only pay for expensive models when necessary!
