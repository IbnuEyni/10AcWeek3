# Phase 5: Query Interface Agent

## Overview

The Query Interface Agent is the final stage of the Document Intelligence Refinery pipeline. It provides a natural language interface for querying processed documents with full provenance tracking.

## Architecture

```
User Query → Method Selection → Tool Execution → Answer + Provenance
                ↓
    [PageIndex Navigate]
    [Semantic Search]
    [Structured Query]
```

## Three Query Tools

### 1. PageIndex Navigate
- **Purpose**: Navigate document hierarchy to find relevant sections
- **Use Case**: "What are the main sections?", "Where is the financial data?"
- **Method**: Tree traversal over PageIndex structure
- **Advantage**: No vector search needed, fast section-level navigation

### 2. Semantic Search
- **Purpose**: Find relevant content chunks using semantic similarity
- **Use Case**: "Explain the methodology", "What are the key findings?"
- **Method**: Vector search over LDUs (with keyword fallback)
- **Advantage**: Finds semantically related content

### 3. Structured Query
- **Purpose**: Precise queries over extracted facts
- **Use Case**: "What is the total revenue?", "Show all expenditures"
- **Method**: SQL queries over FactTable database
- **Advantage**: Exact numerical queries, no hallucination

## Provenance Chain

Every answer includes a `ProvenanceChain` with:
- **Query**: Original user question
- **Answer**: Generated response
- **Citations**: List of source citations with:
  - Document name
  - Page number
  - Bounding box coordinates
  - Content hash (for verification)
  - Text excerpt
  - LDU identifier
- **Confidence**: Answer confidence score
- **Retrieval Method**: Which tool was used

## Audit Mode

The `verify_claim()` method enables claim verification:

```python
result = agent.verify_claim(
    "The report states revenue was $4.2B in Q3",
    doc_id="annual_report_2023"
)

if result['verified']:
    print(f"✓ VERIFIED - Source: Page {result['citation']['page_number']}")
else:
    print(f"✗ UNVERIFIABLE - {result['reason']}")
```

## FactTable Extraction

The `FactExtractor` extracts structured facts from:
- **Tables**: Header-value pairs from table cells
- **Text**: Numerical facts using pattern matching
  - "Revenue: $4.2B"
  - "Total expenditure was $1.5M"
  - "Growth rate of 15%"

Facts are stored in SQLite with:
- Key-value pairs
- Units (USD, %, million, etc.)
- Page references
- Bounding boxes
- Content hashes

## Usage

### Basic Query

```python
from src.agents.query_agent import QueryAgent

agent = QueryAgent()

# Auto-select method
result = agent.query("What is the total revenue?", doc_id="annual_report")

print(result.answer)
for citation in result.citations:
    print(f"Source: {citation.document_name}, Page {citation.page_number}")
```

### Specific Method

```python
# Force PageIndex navigation
result = agent.query(
    "What are the main sections?",
    doc_id="annual_report",
    method="pageindex"
)

# Force semantic search
result = agent.query(
    "Explain the methodology",
    method="semantic"
)

# Force structured query
result = agent.query(
    "Show all revenue figures",
    method="structured"
)
```

### Claim Verification

```python
verification = agent.verify_claim(
    "The report states revenue was $4.2B",
    doc_id="annual_report"
)

if verification['verified']:
    citation = verification['citation']
    print(f"✓ Verified on page {citation['page_number']}")
    print(f"Excerpt: {citation['excerpt']}")
else:
    print(f"✗ Unverifiable: {verification['reason']}")
```

## Demo

Run the complete 5-stage pipeline:

```bash
# Process document through all stages
python demo_full_pipeline.py data/sample.pdf

# Query the processed document
python demo_query_interface.py sample
```

## Output Artifacts

- **Facts Database**: `.refinery/facts.db` - SQLite database with extracted facts
- **Query Results**: Returned as `ProvenanceChain` objects with full citations

## Key Features

✓ **Three query methods** - PageIndex, semantic, structured
✓ **Automatic method selection** - Based on query type
✓ **Full provenance** - Every answer cites sources with page + bbox
✓ **Audit mode** - Verify claims against source documents
✓ **Fact extraction** - Structured data for SQL queries
✓ **Graceful degradation** - Keyword fallback if vector store unavailable

## Performance

| Query Type | Method | Avg Time | Accuracy |
|------------|--------|----------|----------|
| Section navigation | PageIndex | <0.1s | High |
| Semantic questions | Vector search | 0.5-1s | Medium-High |
| Numerical queries | SQL | <0.1s | Very High |

## Integration with Previous Stages

1. **Stage 1 (Triage)**: Profile determines document type
2. **Stage 2 (Extraction)**: Provides raw content
3. **Stage 3 (Chunking)**: Creates queryable LDUs
4. **Stage 4 (PageIndex)**: Enables hierarchical navigation
5. **Stage 5 (Query)**: Combines all artifacts for intelligent retrieval

## Future Enhancements

- [ ] LLM-powered answer generation (currently uses simple extraction)
- [ ] Natural language to SQL conversion (currently uses templates)
- [ ] Multi-document reasoning
- [ ] Query result caching
- [ ] Advanced fact extraction with entity recognition
- [ ] Vector store optimization with FAISS/Qdrant
