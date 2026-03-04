# Git Commit Plan

## Commit Strategy: Small, Focused Commits

### Commit 1: Fix Gemini API model name
**Files:**
- src/strategies/vision_augmented.py
- src/strategies/handwriting_ocr.py

**Message:** `fix: update Gemini model to stable version (gemini-1.5-flash)`

---

### Commit 2: Add Stage 2 enhancements - Enhanced tables
**Files:**
- src/strategies/enhanced_table.py
- tests/unit/test_stage2_enhancements.py (table tests only)

**Message:** `feat: add enhanced table extraction with structure preservation`

---

### Commit 3: Add Stage 2 enhancements - Figure extraction
**Files:**
- src/strategies/figure_extractor.py
- src/models/extracted_document.py (Figure model updates)

**Message:** `feat: add figure extraction with metadata and disk saving`

---

### Commit 4: Add Stage 2 enhancements - Caption binding
**Files:**
- src/strategies/caption_binder.py

**Message:** `feat: add figure-caption binding with spatial proximity`

---

### Commit 5: Add Stage 2 enhancements - Multi-column detection
**Files:**
- src/strategies/column_detector.py

**Message:** `feat: add multi-column layout detection and reading order correction`

---

### Commit 6: Add Stage 2 enhancements - Handwriting OCR
**Files:**
- src/strategies/handwriting_ocr.py

**Message:** `feat: add handwriting OCR with multi-engine fallback`

---

### Commit 7: Integrate Stage 2 enhancements into extractors
**Files:**
- src/strategies/layout_aware.py
- src/strategies/vision_augmented.py

**Message:** `feat: integrate Stage 2 enhancements into extraction pipeline`

---

### Commit 8: Add OCR configuration and setup
**Files:**
- .env.template
- pyproject.toml
- OCR_SETUP.md
- check_ocr.py

**Message:** `docs: add OCR setup guide and configuration`

---

### Commit 9: Add test infrastructure
**Files:**
- tests/README.md
- run_tests.py
- Makefile
- TEST_SUITE_COMPLETE.md

**Message:** `test: add professional test suite infrastructure`

---

### Commit 10: Add demo and test scripts
**Files:**
- test_complete.py
- simple_demo.py
- demo_current_implementation.py

**Message:** `test: add end-to-end demo and test scripts`

---

### Commit 11: Add comprehensive documentation
**Files:**
- COMPREHENSIVE_PROJECT_EXPLANATION.md
- CURRENT_OUTPUTS_EXPLAINED.md
- STAGE2_FINAL_100_PERCENT.md
- FIXES_SUMMARY.md

**Message:** `docs: add comprehensive project documentation`

---

### Commit 12: Clean up old documentation
**Files:**
- FINAL_SUMMARY.md (deleted)
- INTERIM_CHECKLIST.md (deleted)
- INTERIM_SUMMARY.md (deleted)
- PHASE_4_5_6_SUMMARY.md (deleted)

**Message:** `docs: remove outdated documentation files`

---

### Commit 13: Add TODO and maintenance files
**Files:**
- TODO.md

**Message:** `docs: add TODO list for future improvements`

---

## Execution Commands

```bash
# Commit 1
git add src/strategies/vision_augmented.py src/strategies/handwriting_ocr.py
git commit -m "fix: update Gemini model to stable version (gemini-1.5-flash)"

# Commit 2
git add src/strategies/enhanced_table.py
git commit -m "feat: add enhanced table extraction with structure preservation"

# Commit 3
git add src/strategies/figure_extractor.py src/models/extracted_document.py
git commit -m "feat: add figure extraction with metadata and disk saving"

# Commit 4
git add src/strategies/caption_binder.py
git commit -m "feat: add figure-caption binding with spatial proximity"

# Commit 5
git add src/strategies/column_detector.py
git commit -m "feat: add multi-column layout detection and reading order correction"

# Commit 6 (already added in commit 1, skip)

# Commit 7
git add src/strategies/layout_aware.py src/strategies/vision_augmented.py
git commit -m "feat: integrate Stage 2 enhancements into extraction pipeline"

# Commit 8
git add .env.template pyproject.toml OCR_SETUP.md check_ocr.py
git commit -m "docs: add OCR setup guide and configuration"

# Commit 9
git add tests/README.md run_tests.py Makefile TEST_SUITE_COMPLETE.md
git commit -m "test: add professional test suite infrastructure"

# Commit 10
git add test_complete.py simple_demo.py demo_current_implementation.py test_automated.py test_stage_1_2.py quick_test.py manual_test.py
git commit -m "test: add end-to-end demo and test scripts"

# Commit 11
git add COMPREHENSIVE_PROJECT_EXPLANATION.md CURRENT_OUTPUTS_EXPLAINED.md STAGE2_FINAL_100_PERCENT.md STAGE2_100_PERCENT_COMPLETE.md FIXES_SUMMARY.md
git commit -m "docs: add comprehensive project documentation"

# Commit 12
git rm FINAL_SUMMARY.md INTERIM_CHECKLIST.md INTERIM_SUMMARY.md PHASE_4_5_6_SUMMARY.md
git commit -m "docs: remove outdated documentation files"

# Commit 13
git add TODO.md
git commit -m "docs: add TODO list for future improvements"
```
