"""Tests with mocked external dependencies"""

import os
import pytest
from unittest.mock import patch, MagicMock, Mock
from src.strategies.vision_augmented import VisionExtractor
from src.strategies.fast_text import FastTextExtractor
from src.strategies.layout_aware import LayoutExtractor
from src.exceptions import BudgetExceededError, APIError


class TestVisionExtractorMocked:
    """Test vision extractor with mocked Gemini API"""
    
    def test_gemini_api_success(self, sample_profile, tmp_path):
        """Test successful Gemini API call"""
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Extracted document content"
        mock_model.generate_content.return_value = mock_response
        
        extractor = VisionExtractor(api_key="test_key")
        extractor.use_gemini = True
        extractor.client = mock_model
        
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\n")
        
        with patch.object(extractor, '_pdf_to_images', return_value=[Mock()]):
            doc, confidence = extractor.extract(str(test_pdf), sample_profile)
            
            assert doc.extraction_strategy == "vision_augmented"
            assert confidence == 0.8
            assert len(doc.text_blocks) > 0
    
    def test_gemini_api_failure(self, sample_profile, tmp_path):
        """Test Gemini API failure handling"""
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        
        extractor = VisionExtractor(api_key="test_key")
        extractor.use_gemini = True
        extractor.client = mock_model
        
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\n")
        
        with patch.object(extractor, '_pdf_to_images', return_value=[Mock()]):
            doc, confidence = extractor.extract(str(test_pdf), sample_profile)
            
            # Should handle error gracefully
            assert doc.extraction_strategy == "vision_augmented"
    
    def test_budget_guard(self, scanned_profile):
        """Test budget guard prevents expensive extractions"""
        extractor = VisionExtractor()
        
        # Create profile with many pages
        scanned_profile.total_pages = 100
        
        with pytest.raises(BudgetExceededError):
            extractor.extract("dummy.pdf", scanned_profile)
    
    def test_no_api_key_fallback(self, sample_profile, tmp_path):
        """Test fallback when no API key is provided"""
        with patch.dict(os.environ, {}, clear=True):  # Clear environment
            extractor = VisionExtractor(api_key=None)
            
            test_pdf = tmp_path / "test.pdf"
            test_pdf.write_bytes(b"%PDF-1.4\n")
            
            doc, confidence = extractor.extract(str(test_pdf), sample_profile)
            
            assert confidence == 0.5  # Lower confidence for placeholder
            assert doc.extraction_strategy == "vision_augmented"
            assert not extractor.use_gemini


class TestFastTextExtractorMocked:
    """Test fast text extractor with mocked pdfplumber"""
    
    @patch('src.strategies.fast_text.pdfplumber')
    def test_successful_extraction(self, mock_pdfplumber, sample_profile, tmp_path):
        """Test successful text extraction"""
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample text content"
        mock_page.width = 612
        mock_page.height = 792
        mock_page.extract_tables.return_value = [[["Header"], ["Data"]]]
        
        mock_pdf.pages = [mock_page] * 5
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        extractor = FastTextExtractor()
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\n")
        
        doc, confidence = extractor.extract(str(test_pdf), sample_profile)
        
        assert doc.extraction_strategy == "fast_text"
        assert len(doc.text_blocks) == 5
        assert confidence > 0.7
    
    @patch('src.strategies.fast_text.pdfplumber')
    def test_empty_content_handling(self, mock_pdfplumber, sample_profile, tmp_path):
        """Test handling of empty content"""
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_page.width = 612
        mock_page.height = 792
        mock_page.extract_tables.return_value = []
        
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        extractor = FastTextExtractor()
        test_pdf = tmp_path / "empty.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\n")
        
        doc, confidence = extractor.extract(str(test_pdf), sample_profile)
        
        assert len(doc.text_blocks) == 0
        assert confidence < 0.75  # Low confidence for empty content


class TestLayoutExtractorMocked:
    """Test layout extractor with mocked dependencies"""
    
    def test_fallback_extraction(self, sample_profile, tmp_path):
        """Test fallback to pdfplumber when Docling unavailable"""
        with patch('pdfplumber.open') as mock_open:
            mock_pdf = MagicMock()
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Layout preserved text"
            mock_page.width = 612
            mock_page.height = 792
            mock_page.extract_tables.return_value = [[["Col1", "Col2"], ["Val1", "Val2"]]]
            
            mock_pdf.pages = [mock_page]
            mock_open.return_value.__enter__.return_value = mock_pdf
            
            extractor = LayoutExtractor()
            test_pdf = tmp_path / "test.pdf"
            test_pdf.write_bytes(b"%PDF-1.4\n")
            
            doc, confidence = extractor.extract(str(test_pdf), sample_profile)
            
            assert doc.extraction_strategy == "layout_aware"
            assert len(doc.tables) > 0
            assert confidence == 0.75


class TestAPIRetryLogic:
    """Test API retry and error handling"""
    
    def test_retry_on_transient_error(self, sample_profile, tmp_path):
        """Test retry logic for transient API errors"""
        mock_model = MagicMock()
        
        # Fail first time, succeed second time
        mock_model.generate_content.side_effect = [
            Exception("Transient error"),
            MagicMock(text="Success")
        ]
        
        extractor = VisionExtractor(api_key="test_key")
        extractor.use_gemini = True
        extractor.client = mock_model
        
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\n")
        
        with patch.object(extractor, '_pdf_to_images', return_value=[Mock(), Mock()]):
            doc, confidence = extractor.extract(str(test_pdf), sample_profile)
            
            # Should have at least one successful extraction
            assert len(doc.text_blocks) >= 1
