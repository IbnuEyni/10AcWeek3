# Docling FAST Mode Integration

## Summary

Integrated Docling in **FAST mode** (no OCR, no AI table structure) for optimal native PDF extraction.

## Where It's Used

### 1. Layout-Aware Strategy (`src/strategies/layout_aware.py`)
- **Line 27**: `if self.use_docling:` - Checks if Docling is available
- **Line 28**: `return self._extract_with_docling(pdf_path, profile)` - Uses Docling FAST mode
- **Line 32-50**: Docling extraction with preserved reading order, table structure, and figure-caption bindings

### 2. Docling Helper (`src/utils/docling_helper.py`)
- **Lines 13-37**: Initialization with FAST mode configuration
```python
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False           # No OCR for native PDFs
pipeline_options.do_table_structure = False  # Fast table extraction

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
```

### 3. Configuration (`rubric/extraction_rules.yaml`)
- **Lines 213-227**: New extraction strategy configuration section
```yaml
extraction_strategies:
  layout_aware:
    use_docling_fast_mode: true
    docling_fallback: true
```

## Benefits

1. **Performance**: No OCR overhead for native digital PDFs
2. **Structure Preservation**: 
   - Reading order maintained
   - Table headers and cells preserved
   - Multi-column layouts correctly detected
   - Figure-caption bindings automatic
3. **Fallback**: Gracefully falls back to pdfplumber if Docling unavailable

## Guarantees (Documented in Code)

### Docling Mode:
- Reading order preserved from layout analysis
- Table structure maintained with headers
- Multi-column layouts correctly ordered
- Figure-caption bindings preserved

### Fallback Mode (pdfplumber):
- Reading order: Left-to-right, top-to-bottom
- Table fidelity: Headers preserved
- Multi-column: Detected and reordered
- Figure-caption: Bound using spatial proximity

## Usage Flow

```
Native Digital PDF → Layout-Aware Strategy
                           ↓
                    Docling Available?
                    ↙              ↘
                  YES              NO
                   ↓                ↓
            Docling FAST      pdfplumber
            (no OCR/AI)       (fallback)
                   ↓                ↓
            ExtractedDocument with routing_summary
```
