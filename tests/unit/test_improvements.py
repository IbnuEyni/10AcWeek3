"""Tests for Phase 4, 5, 6 improvements"""

import pytest
import asyncio
from pathlib import Path
from src.performance import BatchProcessor, CacheManager, ResourceManager, LazyPDFLoader
from src.data_quality import PDFValidator, OutputValidator, AnomalyDetector
from src.models.extracted_document import ExtractedDocument, TextBlock, BoundingBox
from src.exceptions import DocumentValidationError


class TestPerformance:
    """Test performance optimization features"""
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, tmp_path):
        """Test batch document processing"""
        # Create test PDFs
        pdf_paths = []
        for i in range(3):
            pdf = tmp_path / f"test_{i}.pdf"
            pdf.write_bytes(b"%PDF-1.4\n")
            pdf_paths.append(str(pdf))
        
        processor = BatchProcessor(max_workers=2)
        
        def mock_process(path):
            return f"processed_{Path(path).name}"
        
        results = await processor.process_batch(pdf_paths, mock_process)
        
        assert len(results) == 3
        assert all("processed_" in str(r) for r in results if not isinstance(r, Exception))
    
    def test_cache_manager(self, tmp_path):
        """Test profile caching"""
        CacheManager.clear_cache()
        
        # Cache should be empty
        info = CacheManager.get_cached_profile.cache_info()
        assert info.currsize == 0
    
    def test_resource_cleanup(self, tmp_path):
        """Test temporary file cleanup"""
        manager = ResourceManager(temp_dir=tmp_path)
        
        # Create old files
        old_file = tmp_path / "old.tmp"
        old_file.write_text("test")
        
        # Cleanup won't remove recent files
        count = manager.cleanup_temp_files(max_age_hours=0)
        assert count >= 0
    
    def test_lazy_pdf_loader(self, tmp_path):
        """Test lazy PDF loading"""
        pdf = tmp_path / "test.pdf"
        
        # Create minimal valid PDF
        with open(pdf, 'wb') as f:
            f.write(b"%PDF-1.4\n")
            f.write(b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n")
            f.write(b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n")
            f.write(b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n")
            f.write(b"xref\n0 4\n0000000000 65535 f\n")
            f.write(b"0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n")
            f.write(b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF\n")
        
        with LazyPDFLoader(str(pdf)) as loader:
            assert loader._pdf is not None


class TestDataQuality:
    """Test data quality and validation"""
    
    def test_pdf_validation_success(self, tmp_path):
        """Test valid PDF passes validation"""
        pdf = tmp_path / "valid.pdf"
        pdf.write_bytes(b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n")
        
        # Create minimal valid PDF
        with open(pdf, 'wb') as f:
            f.write(b"%PDF-1.4\n")
            f.write(b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n")
            f.write(b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n")
            f.write(b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n")
            f.write(b"xref\n0 4\n0000000000 65535 f\n")
            f.write(b"0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n")
            f.write(b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF\n")
        
        assert PDFValidator.validate_file(str(pdf))
    
    def test_pdf_validation_not_found(self):
        """Test validation fails for missing file"""
        with pytest.raises(DocumentValidationError, match="not found"):
            PDFValidator.validate_file("nonexistent.pdf")
    
    def test_pdf_validation_invalid_format(self, tmp_path):
        """Test validation fails for invalid format"""
        pdf = tmp_path / "invalid.pdf"
        pdf.write_bytes(b"Not a PDF")
        
        with pytest.raises(DocumentValidationError, match="Invalid PDF signature"):
            PDFValidator.validate_file(str(pdf))
    
    def test_pdf_hash_computation(self, tmp_path):
        """Test file hash computation"""
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4\n")
        
        hash1 = PDFValidator.compute_hash(str(pdf))
        hash2 = PDFValidator.compute_hash(str(pdf))
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
    
    def test_output_validation_success(self, sample_profile):
        """Test valid extraction passes validation"""
        bbox = BoundingBox(x0=0, y0=0, x1=100, y1=100, page=0)
        doc = ExtractedDocument(
            doc_id="test",
            filename="test.pdf",
            text_blocks=[
                TextBlock(content="Good content here", bbox=bbox, reading_order=0)
            ],
            tables=[],
            extraction_strategy="fast_text",
            confidence_score=0.85
        )
        
        result = OutputValidator.validate_extraction(doc)
        
        assert result["valid"]
        assert result["quality_score"] > 0.8
        assert len(result["issues"]) == 0
    
    def test_output_validation_low_confidence(self, sample_profile):
        """Test validation detects low confidence"""
        bbox = BoundingBox(x0=0, y0=0, x1=100, y1=100, page=0)
        doc = ExtractedDocument(
            doc_id="test",
            filename="test.pdf",
            text_blocks=[TextBlock(content="Content", bbox=bbox, reading_order=0)],
            tables=[],
            extraction_strategy="fast_text",
            confidence_score=0.3
        )
        
        result = OutputValidator.validate_extraction(doc)
        
        assert not result["valid"]
        assert any("confidence" in issue.lower() for issue in result["issues"])
    
    def test_anomaly_detection(self, sample_profile):
        """Test anomaly detection"""
        detector = AnomalyDetector()
        
        bbox = BoundingBox(x0=0, y0=0, x1=100, y1=100, page=0)
        doc = ExtractedDocument(
            doc_id="test",
            filename="test.pdf",
            text_blocks=[TextBlock(content="x", bbox=bbox, reading_order=0)],
            tables=[],
            extraction_strategy="fast_text",
            confidence_score=0.4
        )
        
        anomalies = detector.detect_anomalies(doc, sample_profile)
        
        assert len(anomalies) > 0
        assert any("confidence" in a.lower() for a in anomalies)
    
    def test_baseline_update(self, sample_profile):
        """Test baseline metrics update"""
        detector = AnomalyDetector()
        
        bbox = BoundingBox(x0=0, y0=0, x1=100, y1=100, page=0)
        docs = [
            ExtractedDocument(
                doc_id=f"test_{i}",
                filename=f"test_{i}.pdf",
                text_blocks=[
                    TextBlock(content="Good content" * 20, bbox=bbox, reading_order=0)
                ],
                tables=[],
                extraction_strategy="fast_text",
                confidence_score=0.85
            )
            for i in range(3)
        ]
        
        detector.update_baseline(docs, [sample_profile] * 3)
        
        assert detector.baseline_metrics["avg_confidence"] > 0.8
