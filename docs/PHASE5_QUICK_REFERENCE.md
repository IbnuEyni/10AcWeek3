# Phase 5 Quick Reference

## Running the Pipeline

### Full 5-Stage Pipeline
```bash
python demo_full_pipeline.py data/your_document.pdf
```

### Query Interface Only
```bash
python demo_query_interface.py your_document_id
```

## Query Methods

### 1. Auto (Recommended)
```python
result = agent.query("Your question here", doc_id="doc_id")
```

### 2. PageIndex Navigation
```python
result = agent.query(
    "What are the main sections?",
    doc_id="doc_id",
    method="pageindex"
)
```

### 3. Semantic Search
```python
result = agent.query(
    "Explain the methodology",
    doc_id="doc_id",
    method="semantic"
)
```

### 4. Structured Query
```python
result = agent.query(
    "What is the total revenue?",
    doc_id="doc_id",
    method="structured"
)
```

## Accessing Results

```python
# Get answer
print(result.answer)

# Get citations
for citation in result.citations:
    print(f"Document: {citation.document_name}")
    print(f"Page: {citation.page_number}")
    print(f"Excerpt: {citation.excerpt}")
    print(f"Hash: {citation.content_hash}")

# Check confidence
print(f"Confidence: {result.confidence:.2%}")

# Check method used
print(f"Method: {result.retrieval_method}")
```

## Claim Verification (Audit Mode)

```python
verification = agent.verify_claim(
    "The report states revenue was $4.2B",
    doc_id="annual_report"
)

if verification['verified']:
    print("✓ VERIFIED")
    citation = verification['citation']
    print(f"Source: Page {citation['page_number']}")
else:
    print("✗ UNVERIFIABLE")
    print(f"Reason: {verification['reason']}")
```

## Direct Tool Access

### PageIndex Navigate
```python
sections = agent.pageindex_navigate(
    doc_id="annual_report",
    section_query="financial data"
)

for section in sections:
    print(f"{section.title} (Pages {section.page_start}-{section.page_end})")
```

### Semantic Search
```python
ldus = agent.semantic_search(
    query_text="revenue projections",
    doc_id="annual_report",
    top_k=5
)

for ldu in ldus:
    print(f"LDU {ldu.ldu_id}: {ldu.content[:100]}...")
```

### Structured Query
```python
results = agent.structured_query(
    "SELECT * FROM facts WHERE key LIKE '%revenue%' LIMIT 10"
)

for row in results:
    print(f"{row['key']}: {row['value']}")
```

## Fact Extraction

```python
from src.utils.fact_extractor import FactExtractor

extractor = FactExtractor()

# Extract facts from document
fact_count = extractor.extract_facts(extracted_doc, ldus)
print(f"Extracted {fact_count} facts")

# Query facts
facts = extractor.query_facts(
    doc_id="annual_report",
    key_pattern="revenue"
)

for fact in facts:
    print(f"{fact['key']}: {fact['value']} ({fact['unit']})")
```

## Output Artifacts

After running the pipeline, check:

```
.refinery/
├── profiles/           # Document profiles
│   └── doc_id.json
├── ldus/              # Logical Document Units
│   └── doc_id_ldus.json
├── pageindex/         # Page indices
│   └── doc_id_pageindex.json
├── facts.db           # SQLite fact database
└── extraction_ledger.jsonl  # Processing log
```

## Common Query Patterns

### Section-Based Queries
- "What are the main sections?"
- "Which section discusses methodology?"
- "Where is the financial data?"

### Content Queries
- "Explain the key findings"
- "Summarize the methodology"
- "What are the main conclusions?"

### Numerical Queries
- "What is the total revenue?"
- "Show all expenditures"
- "What was the growth rate?"

## Troubleshooting

### No results found
- Check if document was processed: `ls .refinery/ldus/`
- Verify PageIndex exists: `ls .refinery/pageindex/`
- Try different query method

### Low confidence
- Results with confidence < 0.5 may be unreliable
- Try rephrasing query
- Check if document contains relevant information

### Unverifiable claims
- Claim may not exist in document
- Try semantic search to find related content
- Check exact wording in source document

## Performance Tips

1. **Use PageIndex first** for section-based queries (fastest)
2. **Use structured queries** for numerical data (most accurate)
3. **Use semantic search** for general content discovery
4. **Let auto-select** choose the best method

## Integration Example

```python
from src.agents import (
    TriageAgent, ExtractionRouter, ChunkingAgent,
    PageIndexBuilder, QueryAgent
)
from src.utils.fact_extractor import FactExtractor

# Initialize all agents
triage = TriageAgent()
router = ExtractionRouter()
chunker = ChunkingAgent()
indexer = PageIndexBuilder()
query_agent = QueryAgent()
fact_extractor = FactExtractor()

# Process document
profile = triage.profile_document("document.pdf")
extracted_doc = router.extract("document.pdf", profile)
ldus = chunker.process_document(extracted_doc, "document.pdf")
page_index = indexer.build_index(extracted_doc, ldus)
fact_extractor.extract_facts(extracted_doc, ldus)

# Query
result = query_agent.query("Your question", doc_id=profile.doc_id)
print(result.answer)
```

## Next Steps

1. Process your documents through the full pipeline
2. Experiment with different query methods
3. Use audit mode to verify critical claims
4. Build custom queries for your use case
5. Integrate with your application

For detailed documentation, see:
- `docs/PHASE5_QUERY_INTERFACE.md`
- `docs/PHASE5_IMPLEMENTATION_SUMMARY.md`
