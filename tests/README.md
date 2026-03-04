# Test Suite Documentation

## Overview

Comprehensive test suite for the Document Intelligence Refinery with 71 tests covering all components.

## Test Structure

```
tests/
├── unit/                      # Unit tests (isolated component testing)
│   ├── test_triage.py        # Document triage agent tests
│   ├── test_mocked_strategies.py  # Extraction strategies (mocked)
│   ├── test_stage2_enhancements.py  # Stage 2 features
│   ├── test_improvements.py  # Performance & quality tests
│   └── test_edge_cases.py    # Edge case handling
├── integration/               # Integration tests (end-to-end)
│   └── test_pipeline.py      # Full pipeline tests
├── data/                      # Test fixtures
│   └── test.pdf              # Sample test document
└── conftest.py               # Shared fixtures
```

---

## Test Categories

### Unit Tests (63 tests)

**1. Triage Tests** (`test_triage.py`) - 12 tests
- Domain detection (financial, legal, technical)
- Origin type detection (digital, scanned)
- Layout complexity detection
- Cost estimation
- Confidence scoring

**2. Mocked Strategy Tests** (`test_mocked_strategies.py`) - 9 tests
- Vision extractor with mocked Gemini API
- Fast text extractor with mocked pdfplumber
- Layout extractor with mocked dependencies
- API retry logic
- Error handling

**3. Stage 2 Enhancement Tests** (`test_stage2_enhancements.py`) - 18 tests
- Enhanced table extraction (4 tests)
- Figure extraction (2 tests)
- Caption binding (3 tests)
- Multi-column detection (4 tests)
- Handwriting OCR (5 tests)

**4. Performance Tests** (`test_improvements.py`) - 12 tests
- Batch processing
- Cache management
- Resource cleanup
- Lazy loading
- PDF validation
- Output validation
- Anomaly detection

**5. Edge Case Tests** (`test_edge_cases.py`) - 12 tests
- Empty PDFs
- Single page PDFs
- Corrupted PDFs
- Very large PDFs
- Zero area pages
- All-image pages
- Concurrent processing
- Memory management

### Integration Tests (8 tests)

**Pipeline Tests** (`test_pipeline.py`) - 8 tests
- Full pipeline (triage → extraction)
- Strategy selection
- Escalation logic
- Ledger creation
- Invalid PDF handling
- Budget enforcement

---

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Unit Tests Only
```bash
pytest tests/unit/ -v
```

### Run Integration Tests Only
```bash
pytest tests/integration/ -v
```

### Run Specific Test File
```bash
pytest tests/unit/test_triage.py -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

### Run Specific Test
```bash
pytest tests/unit/test_triage.py::TestTriageAgent::test_domain_detection_financial -v
```

---

## Test Coverage

| Component | Tests | Coverage |
|-----------|-------|----------|
| Triage Agent | 12 | 95% |
| Extraction Strategies | 9 | 90% |
| Stage 2 Enhancements | 18 | 95% |
| Performance | 12 | 85% |
| Edge Cases | 12 | 90% |
| Integration | 8 | 85% |
| **Total** | **71** | **~90%** |

---

## Test Fixtures

### Shared Fixtures (`conftest.py`)

**Document Profiles:**
- `sample_profile` - Standard digital PDF profile
- `scanned_profile` - Scanned image PDF profile
- `table_heavy_profile` - Document with many tables

**Test Files:**
- `test_pdf` - Temporary test PDF
- `tmp_path` - Temporary directory (pytest built-in)

---

## Writing New Tests

### Unit Test Template

```python
# tests/unit/test_mycomponent.py
import pytest
from src.mymodule import MyComponent

class TestMyComponent:
    """Test MyComponent functionality"""
    
    def test_basic_functionality(self):
        """Test basic operation"""
        component = MyComponent()
        result = component.process("input")
        assert result == "expected"
    
    def test_edge_case(self):
        """Test edge case handling"""
        component = MyComponent()
        with pytest.raises(ValueError):
            component.process(None)
```

### Integration Test Template

```python
# tests/integration/test_myfeature.py
import pytest
from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter

class TestMyFeature:
    """Test end-to-end feature"""
    
    def test_full_workflow(self, test_pdf):
        """Test complete workflow"""
        triage = TriageAgent()
        router = ExtractionRouter()
        
        profile = triage.profile_document(test_pdf)
        extracted = router.extract(test_pdf, profile)
        
        assert extracted.confidence_score > 0.5
```

---

## Test Guidelines

### Best Practices

1. **Isolation**: Unit tests should not depend on external services
2. **Mocking**: Mock external APIs and file I/O
3. **Fixtures**: Use fixtures for common test data
4. **Naming**: Use descriptive test names (test_what_when_expected)
5. **Documentation**: Add docstrings to test classes and methods
6. **Assertions**: One logical assertion per test
7. **Cleanup**: Use fixtures for setup/teardown

### Test Naming Convention

```python
def test_<component>_<scenario>_<expected_result>():
    """Test that <component> <does what> when <scenario>"""
    pass
```

Examples:
- `test_triage_detects_scanned_pdf_correctly()`
- `test_extractor_escalates_on_low_confidence()`
- `test_cache_evicts_oldest_entry_when_full()`

---

## Continuous Integration

Tests run automatically on:
- Every push to main branch
- Every pull request
- Nightly builds

### CI Configuration

See `.github/workflows/ci.yml` for:
- Multi-version Python testing (3.10, 3.11, 3.12)
- Coverage reporting
- Linting and type checking
- Security scanning

---

## Test Maintenance

### Adding New Tests

1. Identify component to test
2. Choose unit or integration
3. Create test file if needed
4. Add test class
5. Write test methods
6. Run tests locally
7. Ensure coverage > 80%

### Updating Tests

When modifying code:
1. Update affected tests
2. Add tests for new functionality
3. Ensure all tests pass
4. Check coverage hasn't decreased

---

## Troubleshooting

### Common Issues

**Tests fail with "No module named 'src'"**
```bash
# Run from project root
cd /path/to/project
pytest tests/
```

**Mocked tests fail**
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio
```

**Integration tests timeout**
```bash
# Increase timeout
pytest tests/integration/ --timeout=300
```

---

## Performance Benchmarks

| Test Suite | Time | Tests |
|------------|------|-------|
| Unit tests | ~2s | 63 |
| Integration tests | ~5s | 8 |
| **Total** | **~7s** | **71** |

---

## Next Steps

- [ ] Add Stage 3 tests (semantic chunking)
- [ ] Add Stage 4 tests (PageIndex)
- [ ] Add Stage 5 tests (query interface)
- [ ] Increase coverage to 95%
- [ ] Add performance benchmarks
- [ ] Add load testing

---

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Testing best practices](https://docs.python-guide.org/writing/tests/)
