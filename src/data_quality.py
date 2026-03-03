"""Data quality and validation utilities"""

import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from .models.extracted_document import ExtractedDocument
from .exceptions import DocumentValidationError
from .logging_config import get_logger

logger = get_logger("data_quality")


class PDFValidator:
    """Validate PDF files before processing"""
    
    MAX_FILE_SIZE_MB = 100
    VALID_SIGNATURES = [b'%PDF-1.', b'%PDF-2.']
    
    @staticmethod
    def validate_file(pdf_path: str) -> bool:
        """
        Comprehensive PDF validation
        
        Raises:
            DocumentValidationError: If validation fails
        """
        path = Path(pdf_path)
        
        # Existence check
        if not path.exists():
            raise DocumentValidationError(f"File not found: {pdf_path}")
        
        # Size check
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > PDFValidator.MAX_FILE_SIZE_MB:
            raise DocumentValidationError(
                f"File too large: {size_mb:.1f}MB (max {PDFValidator.MAX_FILE_SIZE_MB}MB)"
            )
        
        # Format verification
        with open(path, 'rb') as f:
            header = f.read(8)
            if not any(header.startswith(sig) for sig in PDFValidator.VALID_SIGNATURES):
                raise DocumentValidationError("Invalid PDF signature")
        
        # Corruption check
        try:
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                if len(pdf.pages) == 0:
                    raise DocumentValidationError("PDF has no pages")
        except Exception as e:
            raise DocumentValidationError(f"Corrupted PDF: {e}")
        
        logger.info(f"PDF validation passed: {pdf_path}")
        return True
    
    @staticmethod
    def compute_hash(pdf_path: str) -> str:
        """Compute SHA256 hash for file integrity"""
        sha256 = hashlib.sha256()
        with open(pdf_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()


class OutputValidator:
    """Validate extraction output quality"""
    
    MIN_CONFIDENCE = 0.5
    MIN_CONTENT_LENGTH = 10
    
    @staticmethod
    def validate_extraction(doc: ExtractedDocument) -> Dict[str, any]:
        """
        Validate extracted document quality
        
        Returns:
            Quality metrics dictionary
        """
        issues = []
        
        # Confidence check
        if doc.confidence_score < OutputValidator.MIN_CONFIDENCE:
            issues.append(f"Low confidence: {doc.confidence_score:.2f}")
        
        # Content check
        total_content = sum(len(block.content) for block in doc.text_blocks)
        if total_content < OutputValidator.MIN_CONTENT_LENGTH:
            issues.append(f"Insufficient content: {total_content} chars")
        
        # Empty blocks check
        empty_blocks = sum(1 for b in doc.text_blocks if not b.content.strip())
        if empty_blocks > len(doc.text_blocks) * 0.5:
            issues.append(f"Too many empty blocks: {empty_blocks}/{len(doc.text_blocks)}")
        
        # Provenance check
        missing_provenance = sum(1 for b in doc.text_blocks if not b.bbox)
        if missing_provenance > 0:
            issues.append(f"Missing provenance: {missing_provenance} blocks")
        
        quality_score = 1.0 - (len(issues) * 0.2)
        
        result = {
            "valid": len(issues) == 0,
            "quality_score": max(0.0, quality_score),
            "issues": issues,
            "metrics": {
                "total_blocks": len(doc.text_blocks),
                "total_tables": len(doc.tables),
                "total_chars": total_content,
                "confidence": doc.confidence_score
            }
        }
        
        if issues:
            logger.warning(f"Quality issues in {doc.doc_id}: {issues}")
        else:
            logger.info(f"Quality validation passed: {doc.doc_id}")
        
        return result


class AnomalyDetector:
    """Detect anomalies in extraction results"""
    
    def __init__(self):
        self.baseline_metrics = {
            "avg_blocks_per_page": 5.0,
            "avg_chars_per_block": 200.0,
            "avg_confidence": 0.8
        }
    
    def detect_anomalies(self, doc: ExtractedDocument, profile) -> List[str]:
        """Detect statistical anomalies"""
        anomalies = []
        
        # Blocks per page anomaly
        blocks_per_page = len(doc.text_blocks) / max(profile.total_pages, 1)
        if blocks_per_page < self.baseline_metrics["avg_blocks_per_page"] * 0.3:
            anomalies.append(f"Unusually low blocks/page: {blocks_per_page:.1f}")
        
        # Character density anomaly
        if doc.text_blocks:
            avg_chars = sum(len(b.content) for b in doc.text_blocks) / len(doc.text_blocks)
            if avg_chars < self.baseline_metrics["avg_chars_per_block"] * 0.2:
                anomalies.append(f"Unusually short blocks: {avg_chars:.0f} chars")
        
        # Confidence anomaly
        if doc.confidence_score < self.baseline_metrics["avg_confidence"] * 0.6:
            anomalies.append(f"Low confidence: {doc.confidence_score:.2f}")
        
        if anomalies:
            logger.warning(f"Anomalies detected in {doc.doc_id}: {anomalies}")
        
        return anomalies
    
    def update_baseline(self, docs: List[ExtractedDocument], profiles: List):
        """Update baseline metrics from processed documents"""
        if not docs:
            return
        
        total_blocks = sum(len(d.text_blocks) for d in docs)
        total_pages = sum(p.total_pages for p in profiles)
        total_chars = sum(sum(len(b.content) for b in d.text_blocks) for d in docs)
        
        self.baseline_metrics["avg_blocks_per_page"] = total_blocks / max(total_pages, 1)
        self.baseline_metrics["avg_chars_per_block"] = total_chars / max(total_blocks, 1)
        self.baseline_metrics["avg_confidence"] = sum(d.confidence_score for d in docs) / len(docs)
        
        logger.info(f"Baseline updated: {self.baseline_metrics}")
