"""Shared test fixtures and configuration"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from src.models.document_profile import (
    DocumentProfile, OriginType, LayoutComplexity, DomainHint, ExtractionCost
)


@pytest.fixture
def sample_profile():
    """Sample document profile for testing"""
    return DocumentProfile(
        doc_id="test_doc",
        filename="test.pdf",
        origin_type=OriginType.NATIVE_DIGITAL,
        layout_complexity=LayoutComplexity.SINGLE_COLUMN,
        language="en",
        language_confidence=0.95,
        domain_hint=DomainHint.FINANCIAL,
        estimated_extraction_cost=ExtractionCost.FAST_TEXT_SUFFICIENT,
        total_pages=10,
        origin_confidence=0.9,
        layout_confidence=0.8,
        domain_confidence=0.85,
        character_density=0.05,
        image_ratio=0.1,
        has_font_metadata=True,
        table_count_estimate=2
    )


@pytest.fixture
def scanned_profile():
    """Scanned document profile for testing"""
    return DocumentProfile(
        doc_id="scanned_doc",
        filename="scanned.pdf",
        origin_type=OriginType.SCANNED_IMAGE,
        layout_complexity=LayoutComplexity.MIXED,
        language="en",
        language_confidence=0.95,
        domain_hint=DomainHint.LEGAL,
        estimated_extraction_cost=ExtractionCost.NEEDS_VISION_MODEL,
        total_pages=5,
        origin_confidence=0.85,
        layout_confidence=0.75,
        domain_confidence=0.8,
        character_density=0.001,
        image_ratio=0.9,
        has_font_metadata=False,
        table_count_estimate=0
    )


@pytest.fixture
def mock_pdf_metrics():
    """Mock PDF analysis metrics"""
    return {
        "total_pages": 10,
        "character_density": 0.05,
        "image_ratio": 0.2,
        "has_font_metadata": True,
        "table_count_estimate": 5,
        "page_char_densities": [0.05] * 10,
        "page_image_ratios": [0.2] * 10
    }


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini API client"""
    mock = MagicMock()
    mock.generate_content.return_value.text = "Extracted text content"
    return mock


@pytest.fixture
def temp_pdf_dir(tmp_path):
    """Temporary directory for test PDFs"""
    pdf_dir = tmp_path / "test_pdfs"
    pdf_dir.mkdir()
    return pdf_dir
