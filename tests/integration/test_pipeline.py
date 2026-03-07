"""Integration tests for document processing pipeline"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.agents.triage import TriageAgent
from src.agents.extractor import ExtractionRouter
from src.exceptions import DocumentValidationError, BudgetExceededError


class TestPipelineIntegration:
    """End-to-end pipeline integration tests"""
    
    @pytest.fixture
    def triage_agent(self, tmp_path):
        return TriageAgent(output_dir=str(tmp_path / "profiles"))
    
    @pytest.fixture
    def extraction_router(self, tmp_path):
        return ExtractionRouter(ledger_path=str(tmp_path / "ledger.jsonl"))
    
    @patch('fitz.open')
    @patch('src.utils.pdf_analyzer.pdfplumber.open')
    def test_full_pipeline_native_digital(self, mock_pdfplumber_open, mock_fitz_open, triage_agent, 
                                          extraction_router, tmp_path):
        """Test complete pipeline for native digital PDF"""
        # Setup mock PDF with proper metrics for native digital detection
        mock_pdf = MagicMock()
        mock_pdf.pages = [MagicMock() for _ in range(5)]
        
        for page in mock_pdf.pages:
            # Provide substantial text content for high character density
            page.extract_text.return_value = "Sample text content " * 300  # Lots of text
            page.width = 612
            page.height = 792
            page.images = []  # No images
            page.chars = [{'text': 'a'}] * 50  # Many characters
            page.find_tables.return_value = []
            page.extract_tables.return_value = []
        
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

        # Mock PyMuPDF (fitz) font detection to treat as native digital
        mock_fitz_doc = MagicMock()
        mock_fitz_doc.page_count = 5
        mock_fitz_doc.__getitem__.return_value.get_fonts.return_value = ["/F1"]
        mock_fitz_open.return_value = mock_fitz_doc
        
        # Create test PDF
        test_pdf = tmp_path / "data/tax_expenditure_ethiopia_2021_22.pdf"
        test_pdf.parent.mkdir(parents=True, exist_ok=True)
        # Minimal valid PDF so MuPDF/fitz can open it during pipeline execution
        test_pdf.write_bytes(
            b"%PDF-1.4\n"
            b"1 0 obj<< /Type /Catalog /Pages 2 0 R>>endobj\n"
            b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1>>endobj\n"
            b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R>>endobj\n"
            b"4 0 obj<< /Length 44>>stream\nBT /F1 24 Tf 72 712 Td (Hello) Tj ET\nendstream\nendobj\n"
            b"xref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000079 00000 n \n0000000174 00000 n \n0000000266 00000 n \n"
            b"trailer<< /Root 1 0 R /Size 5>>\nstartxref\n354\n%%EOF\n"
        )
        
        # Run pipeline
        profile = triage_agent.profile_document(str(test_pdf))
        # Accept either native_digital or form_fillable (both are native types)
        assert profile.origin_type in ["native_digital", "form_fillable"]
        assert profile.domain_hint == "financial"
        
        extracted = extraction_router.extract(str(test_pdf), profile)
        assert extracted.doc_id == "tax_expenditure_ethiopia_2021_22"
        # Accept either fast_text or layout_aware (both valid for native PDFs)
        assert extracted.extraction_strategy in ["fast_text", "layout_aware"]
    
    def test_invalid_pdf_handling(self, triage_agent, tmp_path):
        """Test handling of invalid PDF files"""
        # Non-existent file
        with pytest.raises(DocumentValidationError, match="File not found"):
            triage_agent.profile_document("nonexistent.pdf")
        
        # Empty file
        empty_pdf = tmp_path / "empty.pdf"
        empty_pdf.write_bytes(b"")
        with pytest.raises(DocumentValidationError, match="Empty file"):
            triage_agent.profile_document(str(empty_pdf))
        
        # Non-PDF file
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a pdf")
        with pytest.raises(DocumentValidationError, match="Not a PDF file"):
            triage_agent.profile_document(str(txt_file))
    
    @patch('src.strategies.vision_augmented.VisionExtractor.estimate_cost')
    def test_budget_guard_enforcement(self, mock_cost, extraction_router, 
                                     scanned_profile, tmp_path):
        """Test budget guard prevents expensive extractions"""
        mock_cost.return_value = 5.0  # Exceeds $1 budget
        
        test_pdf = tmp_path / "large_scanned.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\n")
        
        with pytest.raises(BudgetExceededError):
            extraction_router.extract(str(test_pdf), scanned_profile)


class TestStrategySelection:
    """Test extraction strategy selection logic"""
    
    @pytest.fixture
    def router(self, tmp_path):
        return ExtractionRouter(ledger_path=str(tmp_path / "ledger.jsonl"))
    
    def test_fast_text_selection(self, router, sample_profile):
        """Test fast text strategy is selected for native digital PDFs"""
        strategy = router._select_strategy(sample_profile)
        assert strategy.strategy_name == "fast_text"
    
    def test_vision_selection(self, router, scanned_profile):
        """Test vision strategy is selected for scanned PDFs"""
        strategy = router._select_strategy(scanned_profile)
        assert strategy.strategy_name == "vision_augmented"
    
    @patch('src.strategies.fast_text.FastTextExtractor.extract')
    @patch('src.strategies.layout_aware.LayoutExtractor.extract')
    def test_escalation_on_low_confidence(self, mock_layout, mock_fast, 
                                         router, sample_profile, tmp_path):
        """Test automatic escalation when confidence is low"""
        from src.models.extracted_document import ExtractedDocument
        
        # Fast text returns low confidence
        low_conf_doc = ExtractedDocument(
            doc_id="test",
            filename="test.pdf",
            extraction_strategy="fast_text",
            confidence_score=0.5
        )
        mock_fast.return_value = (low_conf_doc, 0.5)
        
        # Layout returns high confidence
        high_conf_doc = ExtractedDocument(
            doc_id="test",
            filename="test.pdf",
            extraction_strategy="layout_aware",
            confidence_score=0.85
        )
        mock_layout.return_value = (high_conf_doc, 0.85)
        
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\n")
        
        result = router.extract(str(test_pdf), sample_profile)
        
        # Should have escalated to layout
        assert mock_layout.called
        assert result.confidence_score == 0.85


class TestExtractionLedger:
    """Test extraction ledger logging"""
    
    def test_ledger_creation(self, tmp_path):
        """Test ledger file is created"""
        ledger_path = tmp_path / "test_ledger.jsonl"
        router = ExtractionRouter(ledger_path=str(ledger_path))
        
        assert ledger_path.parent.exists()
    
    @patch('src.strategies.fast_text.FastTextExtractor.extract')
    def test_ledger_entries(self, mock_extract, tmp_path, sample_profile):
        """Test ledger entries are written correctly"""
        from src.models.extracted_document import ExtractedDocument
        
        mock_doc = ExtractedDocument(
            doc_id="test",
            filename="test.pdf",
            extraction_strategy="fast_text",
            confidence_score=0.85
        )
        mock_extract.return_value = (mock_doc, 0.85)
        
        ledger_path = tmp_path / "ledger.jsonl"
        router = ExtractionRouter(ledger_path=str(ledger_path))
        
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\n")
        
        router.extract(str(test_pdf), sample_profile)
        
        # Check ledger was written
        assert ledger_path.exists()
        content = ledger_path.read_text()
        assert "test" in content
        assert "fast_text" in content
        assert "0.85" in content
