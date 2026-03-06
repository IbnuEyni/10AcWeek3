# Demo Files Summary

## Available Demos

### 1. **demo_complete_pipeline.py** ⭐ (RECOMMENDED)
**Complete end-to-end demonstration of Stages 1-3**

**What it does:**
- Stage 1: Document profiling (triage)
- Stage 2: Content extraction (text, tables, figures)
- Stage 3: Semantic chunking (LDU creation)

**Features:**
- ✅ Beautiful Rich console output with tables and panels
- ✅ Performance metrics for each stage
- ✅ Sample LDU display
- ✅ Output file locations
- ✅ Error handling
- ✅ Progress indicators

**Usage:**
```bash
python3 demo_complete_pipeline.py
```

**Output includes:**
- Document profile (origin, layout, domain)
- Extraction results (text blocks, tables, figures)
- LDU distribution by type
- Performance summary
- Sample LDUs with content preview

---

### 2. **demo_hybrid_pipeline.py**
**Hybrid extraction pipeline (Tier 1 + Tier 2)**

**What it does:**
- Tests PDF classification (native vs scanned)
- Routes to appropriate tier
- Shows cost and time estimates

**Usage:**
```bash
python3 demo_hybrid_pipeline.py
```

---

### 3. **demo_stage3.py**
**Stage 3 only: Semantic chunking**

**What it does:**
- Demonstrates chunking rules
- Shows LDU creation
- Displays chunking statistics

**Usage:**
```bash
python3 demo_stage3.py
```

---

## Quick Test Files

### **test_imports.py**
Quick verification that all dependencies are installed
```bash
python3 test_imports.py
```

---

## Removed Files

The following redundant demos were removed:
- ❌ `demo_fast_classification.py` - Functionality merged into complete demo
- ❌ `demo_stage3_fast.py` - Duplicate of demo_stage3.py
- ❌ `test_docling.py` - Unnecessary test file
- ❌ `test_docling_speed.py` - Replaced by demos
- ❌ `test_cbe_report.py` - One-off test
- ❌ `demo_stage3_test.py` - Duplicate
- ❌ `test_automated.py` - Old test

---

## Best Practices Demonstrated

### 1. **Error Handling**
```python
try:
    demo_complete_pipeline(pdf_path)
except KeyboardInterrupt:
    console.print("Demo interrupted by user")
except Exception as e:
    console.print(f"Error: {e}")
```

### 2. **Progress Indicators**
```python
with Progress(SpinnerColumn(), TextColumn(...)) as progress:
    task = progress.add_task("Loading...", total=None)
    # Initialize agents
    progress.update(task, completed=True)
```

### 3. **Rich Output**
- Tables for structured data
- Panels for sample content
- Color-coded status messages
- Performance metrics

### 4. **Validation**
- File existence checks
- Graceful fallbacks
- Clear error messages

### 5. **Documentation**
- Docstrings for all functions
- Inline comments for complex logic
- Clear output descriptions

---

## Running Demos

### Quick Start
```bash
# Complete pipeline (recommended)
python3 demo_complete_pipeline.py

# Test imports first
python3 test_imports.py
```

### With Custom PDF
```bash
# Edit demo_complete_pipeline.py and change:
default_pdf = "data/your_document.pdf"
```

### Batch Processing
```bash
# Process multiple PDFs
for pdf in data/*.pdf; do
    python3 demo_complete_pipeline.py "$pdf"
done
```

---

## Output Locations

All demos save outputs to:
- **Profiles:** `.refinery/profiles/{doc_id}.json`
- **LDUs:** `.refinery/ldus/{doc_id}_ldus.json`
- **Ledger:** `.refinery/extraction_ledger.jsonl`

---

## Performance Expectations

### demo_complete_pipeline.py
- **Native PDF (10 pages):** ~15-30 seconds
- **Scanned PDF (10 pages):** ~50-60 seconds
- **Memory:** ~500MB

### Breakdown:
- Stage 1 (Triage): <1 second
- Stage 2 (Extraction): 5-50 seconds (depends on PDF type)
- Stage 3 (Chunking): <1 second

---

## Troubleshooting

### Demo hangs
- **Cause:** Docling initialization (10-30s)
- **Solution:** Wait or use test_imports.py first

### No PDFs found
- **Cause:** Missing data/ directory
- **Solution:** Create data/ and add PDF files

### Import errors
- **Cause:** Missing dependencies
- **Solution:** Run `./install_uv.sh` or `pip install -e ".[all]"`

---

## Next Steps

After running demos:
1. Check output files in `.refinery/`
2. Review extraction ledger for metrics
3. Process your own documents
4. Implement Stages 4-5 (PageIndex, Query Interface)

---

**Status:** Production-ready demos with best practices ✅  
**Last Updated:** 2024
