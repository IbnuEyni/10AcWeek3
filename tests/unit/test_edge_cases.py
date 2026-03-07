"""Edge case and negative tests"""

import pytest
from unittest.mock import patch, MagicMock
from src.utils.pdf_analyzer import PDFAnalyzer
from src.agents.triage import TriageAgent
from src.exceptions import DocumentValidationError, TriageError
from src.validation_utils import validate_pdf_file, validate_confidence_score, validate_cost


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_pdf_pages(self, tmp_path):
        """Test handling of PDF with empty pages (short-circuit Pass 1)"""
        analyzer = PDFAnalyzer()
        
        # Simulate Pass 1 short-circuit (no fonts)
        metrics = {
            "short_circuit": "pass1_no_fonts",
            "character_density": 0.0,
            "has_font_metadata": False,
            "image_ratio": 1.0,
            "total_pages": 3,
            "table_count_estimate": 0,
            "page_char_densities": [],
            "page_image_ratios": [],
            "has_form_fields": False,
            "is_mixed_mode": False
        }
        
        origin, confidence = analyzer.detect_origin_type(metrics)
        assert origin == "scanned_image"
        assert confidence == 0.95
    
    def test_single_page_pdf(self, tmp_path):
        """Test handling of single-page PDF"""
        analyzer = PDFAnalyzer()
        
        # Simulate Pass 3 (native digital)
        metrics = {
            "short_circuit": None,
            "total_pages": 1,
            "character_density": 0.02,
            "has_font_metadata": True,
            "image_ratio": 0.1,
            "table_count_estimate": 0,
            "page_char_densities": [0.02],
            "page_image_ratios": [0.1],
            "has_form_fields": False,
            "is_mixed_mode": False
        }
        
        origin, confidence = analyzer.detect_origin_type(metrics)
        assert origin == "native_digital"
        assert confidence == 0.9
    
    def test_corrupted_pdf_handling(self, tmp_path):
        """Test handling of corrupted PDF"""
        with patch('src.utils.pdf_analyzer.pdfplumber.open') as mock_open:
            mock_open.side_effect = Exception("PDF syntax error")
            
            test_pdf = tmp_path / "corrupted.pdf"
            test_pdf.write_bytes(b"%PDF-1.4\n")
            
            with pytest.raises(TriageError, match="Failed to analyze"):
                PDFAnalyzer.analyze_document(str(test_pdf))
    
    def test_very_large_pdf(self, tmp_path):
        """Test handling of very large PDF (>100MB)"""
        large_pdf = tmp_path / "large.pdf"
        large_pdf.write_bytes(b"x" * (101 * 1024 * 1024))  # 101MB
        
        with pytest.raises(DocumentValidationError, match="File too large"):
            validate_pdf_file(str(large_pdf))
    
    def test_zero_area_page(self):
        """Test handling of page with zero area"""
        analyzer = PDFAnalyzer()
        metrics = {
            "short_circuit": "pass1_no_fonts",
            "character_density": 0.0,
            "has_font_metadata": False,
            "image_ratio": 0.0
        }
        
        origin, confidence = analyzer.detect_origin_type(metrics)
        assert origin == "scanned_image"
    
    def test_all_images_page(self):
        """Test page that is 100% images"""
        analyzer = PDFAnalyzer()
        metrics = {
            "short_circuit": "pass1_no_fonts",
            "character_density": 0.0,
            "has_font_metadata": False,
            "image_ratio": 1.0
        }
        
        origin, confidence = analyzer.detect_origin_type(metrics)
        assert origin == "scanned_image"
        assert confidence > 0.7


class TestValidationEdgeCases:
    """Test validation edge cases"""
    
    def test_confidence_score_boundaries(self):
        """Test confidence score validation at boundaries"""
        assert validate_confidence_score(0.0) == 0.0
        assert validate_confidence_score(1.0) == 1.0
        assert validate_confidence_score(0.5) == 0.5
        
        with pytest.raises(ValueError):
            validate_confidence_score(-0.1)
        
        with pytest.raises(ValueError):
            validate_confidence_score(1.1)
    
    def test_cost_validation(self):
        """Test cost validation"""
        assert validate_cost(0.0, 1.0) == 0.0
        assert validate_cost(0.5, 1.0) == 0.5
        
        with pytest.raises(ValueError, match="cannot be negative"):
            validate_cost(-1.0, 1.0)
        
        from src.exceptions import BudgetExceededError
        with pytest.raises(BudgetExceededError):
            validate_cost(2.0, 1.0)
    
    def test_special_characters_in_filename(self, tmp_path):
        """Test handling of special characters in filename"""
        special_pdf = tmp_path / "test@#$%.pdf"
        special_pdf.write_bytes(b"%PDF-1.4\n")
        
        path = validate_pdf_file(str(special_pdf))
        assert path.exists()


class TestConcurrentProcessing:
    """Test concurrent document processing scenarios"""
    
    @pytest.mark.parametrize("num_docs", [1, 5, 10])
    def test_multiple_documents(self, num_docs, tmp_path):
        """Test processing multiple documents (unit test with mocked analyzer)"""
        triage = TriageAgent(output_dir=str(tmp_path / "profiles"))
        
        # Mock the analyzer to avoid actual PDF processing
        with patch.object(triage.analyzer, 'analyze_document') as mock_analyze, \
             patch.object(triage.analyzer, 'detect_origin_type') as mock_origin, \
             patch.object(triage.analyzer, 'detect_layout_complexity') as mock_layout:
            
            mock_analyze.return_value = {
                "total_pages": 1,
                "character_density": 0.02,
                "image_ratio": 0.1,
                "has_font_metadata": True,
                "table_count_estimate": 0,
                "page_char_densities": [0.02],
                "page_image_ratios": [0.1],
                "has_form_fields": False,
                "is_mixed_mode": False,
                "short_circuit": None
            }
            mock_origin.return_value = ("native_digital", 0.9)
            mock_layout.return_value = ("single_column", 0.8)
            
            profiles = []
            for i in range(num_docs):
                test_pdf = tmp_path / f"doc_{i}.pdf"
                test_pdf.write_bytes(b"%PDF-1.4\n")
                profile = triage.profile_document(str(test_pdf))
                profiles.append(profile)
            
            assert len(profiles) == num_docs
            assert all(p.doc_id.startswith("doc_") for p in profiles)


class TestMemoryAndPerformance:
    """Test memory usage and performance"""
    
    def test_large_page_count(self, tmp_path):
        """Test handling of PDF with many pages"""
        analyzer = PDFAnalyzer()
        
        # Simulate large document metrics
        metrics = {
            "short_circuit": None,
            "total_pages": 500,
            "character_density": 0.02,
            "has_font_metadata": True,
            "image_ratio": 0.1,
            "table_count_estimate": 50,
            "page_char_densities": [0.02] * 500,
            "page_image_ratios": [0.1] * 500,
            "has_form_fields": False,
            "is_mixed_mode": False
        }
        
        assert metrics["total_pages"] == 500
        assert len(metrics["page_char_densities"]) == 500
        
        origin, confidence = analyzer.detect_origin_type(metrics)
        assert origin == "native_digital"
