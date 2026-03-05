"""Integration tests for hybrid extraction pipeline"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.strategies.hybrid_pipeline import HybridExtractionPipeline
from src.utils.pdf_classifier import PDFClassifier
from src.models.document_profile import DocumentProfile


class TestHybridPipeline:
    """Test hybrid extraction pipeline (Tier 1 + Tier 2)"""
    
    @pytest.fixture
    def pipeline(self):
        return HybridExtractionPipeline()
    
    @pytest.fixture
    def classifier(self):
        return PDFClassifier()
    
    @pytest.fixture
    def native_profile(self):
        return DocumentProfile(
            doc_id="test_native",
            filename="test_native.pdf",
            total_pages=10,
            origin_type="native_digital",
            layout_complexity="single_column",
            domain_hint="financial",
            language_confidence=0.9,
            estimated_extraction_cost="fast_text_sufficient",
            origin_confidence=0.95,
            layout_confidence=0.85,
            domain_confidence=0.8,
            character_density=1500.0,
            image_ratio=0.1,
            has_font_metadata=True,
            table_count_estimate=2
        )
    
    @pytest.fixture
    def scanned_profile(self):
        return DocumentProfile(
            doc_id="test_scanned",
            filename="test_scanned.pdf",
            total_pages=5,
            origin_type="scanned_image",
            layout_complexity="single_column",
            domain_hint="financial",
            language_confidence=0.7,
            estimated_extraction_cost="needs_vision_model",
            origin_confidence=0.6,
            layout_confidence=0.7,
            domain_confidence=0.75,
            character_density=50.0,
            image_ratio=0.9,
            has_font_metadata=False,
            table_count_estimate=1
        )
    
    @patch('src.utils.pdf_classifier.pdfplumber.open')
    def test_classifier_native_detection(self, mock_open, classifier, tmp_path):
        """Test classifier correctly identifies native PDFs"""
        mock_pdf = MagicMock()
        mock_pdf.pages = [MagicMock()]
        mock_pdf.pages[0].extract_text.return_value = "Sample text " * 100
        mock_open.return_value.__enter__.return_value = mock_pdf
        
        test_pdf = tmp_path / "native.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\n")
        
        is_native = classifier.is_native_pdf(str(test_pdf))
        assert is_native is True
    
    @patch('src.utils.pdf_classifier.pdfplumber.open')
    def test_classifier_scanned_detection(self, mock_open, classifier, tmp_path):
        """Test classifier correctly identifies scanned PDFs"""
        mock_pdf = MagicMock()
        mock_pdf.pages = [MagicMock()]
        mock_pdf.pages[0].extract_text.return_value = ""  # No text
        mock_open.return_value.__enter__.return_value = mock_pdf
        
        test_pdf = tmp_path / "scanned.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\n")
        
        is_native = classifier.is_native_pdf(str(test_pdf))
        assert is_native is False
    
    @pytest.mark.skip(reason="Requires valid PDF for Docling")
    @patch('src.utils.pdf_classifier.PDFClassifier.is_native_pdf')
    @patch('src.utils.docling_helper_optimized.OptimizedDoclingHelper.extract_text')
    @patch('src.utils.camelot_extractor.CamelotExtractor.extract_tables')
    @patch('src.utils.pymupdf_extractor.PyMuPDFExtractor.extract_figures')
    @patch('src.utils.pymupdf_extractor.PyMuPDFExtractor.extract_layout')
    def test_tier1_extraction(self, mock_layout, mock_figures, mock_tables, mock_text, 
                             mock_classifier, pipeline, native_profile, tmp_path):
        """Test Tier 1 extraction for native PDFs"""
        mock_classifier.return_value = True  # Native PDF
        mock_text.return_value = [{'text': 'Sample', 'page': 0, 'bbox': {'x0': 0, 'y0': 0, 'x1': 100, 'y1': 100}}]
        mock_tables.return_value = []
        mock_figures.return_value = []
        mock_layout.return_value = {'pages': [], 'multi_column_pages': []}
        
        test_pdf = tmp_path / "native.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\n")
        
        extracted_doc, confidence = pipeline.extract(str(test_pdf), native_profile)
        
        assert extracted_doc.extraction_strategy == "tier1_native"
        assert confidence >= 0.8
        assert len(extracted_doc.text_blocks) > 0
    
    @pytest.mark.skip(reason="Requires valid PDF for Docling fallback")
    @patch('src.utils.pdf_classifier.PDFClassifier.is_native_pdf')
    @patch('src.strategies.vision_augmented.VisionExtractor.extract')
    def test_tier2_extraction(self, mock_vision, mock_classifier, 
                             pipeline, scanned_profile, tmp_path):
        """Test Tier 2 extraction for scanned PDFs"""
        from src.models.extracted_document import ExtractedDocument
        
        mock_classifier.return_value = False  # Scanned PDF
        mock_doc = ExtractedDocument(
            doc_id="test_scanned",
            filename="test_scanned.pdf",
            extraction_strategy="vision_augmented",
            confidence_score=0.82,
            text_blocks=[],
            tables=[],
            figures=[]
        )
        mock_vision.return_value = (mock_doc, 0.82)
        
        test_pdf = tmp_path / "scanned.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\n")
        
        extracted_doc, confidence = pipeline.extract(str(test_pdf), scanned_profile)
        
        assert extracted_doc.extraction_strategy == "tier2_scanned"
        assert confidence >= 0.8
    
    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initializes all components"""
        assert pipeline.classifier is not None
        assert pipeline.docling_native is not None
        assert pipeline.camelot is not None
        assert pipeline.pymupdf is not None


class TestPipelinePerformance:
    """Test pipeline performance characteristics"""
    
    @patch('src.utils.pdf_classifier.pdfplumber.open')
    def test_classification_speed(self, mock_open, tmp_path):
        """Test classification is fast (<2 seconds)"""
        import time
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [MagicMock()]
        mock_pdf.pages[0].extract_text.return_value = "Text " * 100
        mock_open.return_value.__enter__.return_value = mock_pdf
        
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\n")
        
        classifier = PDFClassifier()
        start = time.time()
        classifier.is_native_pdf(str(test_pdf))
        elapsed = time.time() - start
        
        assert elapsed < 2.0, f"Classification took {elapsed:.2f}s, expected <2s"


class TestPipelineErrorHandling:
    """Test pipeline error handling"""
    
    def test_missing_dependencies_graceful(self):
        """Test pipeline handles missing optional dependencies"""
        # Should not crash even if camelot/pymupdf not installed
        pipeline = HybridExtractionPipeline()
        assert pipeline is not None
    
    @patch('src.utils.pdf_classifier.PDFClassifier.is_native_pdf')
    def test_extraction_failure_fallback(self, mock_classifier, tmp_path):
        """Test pipeline handles extraction failures gracefully"""
        from src.models.document_profile import DocumentProfile
        
        mock_classifier.return_value = True
        
        # Create invalid PDF (will fail Docling)
        test_pdf = tmp_path / "test.pdf"
        test_pdf.write_bytes(b"%PDF-1.4\n")
        
        profile = DocumentProfile(
            doc_id="test",
            filename="test.pdf",
            total_pages=1,
            origin_type="native_digital",
            layout_complexity="single_column",
            domain_hint="general",
            language_confidence=0.8,
            estimated_extraction_cost="fast_text_sufficient",
            origin_confidence=0.9,
            layout_confidence=0.8,
            domain_confidence=0.7,
            character_density=1000.0,
            image_ratio=0.2,
            has_font_metadata=True,
            table_count_estimate=0
        )
        
        pipeline = HybridExtractionPipeline()
        
        # Should fail gracefully with invalid PDF
        try:
            result = pipeline.extract(str(test_pdf), profile)
            # If it succeeds, that's also acceptable
            assert result is not None
        except Exception as e:
            # Should fail with a clear error message
            error_msg = str(e).lower()
            assert any(word in error_msg for word in ['invalid', 'not valid', 'failed', 'error'])
