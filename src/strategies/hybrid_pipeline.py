"""Hybrid extraction pipeline - Tier 1 (Native) + Tier 2 (Scanned)"""

from typing import Tuple
from pathlib import Path

from ..models.document_profile import DocumentProfile
from ..models.extracted_document import ExtractedDocument, TextBlock, BoundingBox
from ..utils.pdf_classifier import PDFClassifier
from ..utils.docling_helper_optimized import OptimizedDoclingHelper
from ..utils.camelot_extractor import CamelotExtractor
from ..utils.pymupdf_extractor import PyMuPDFExtractor
from ..logging_config import get_logger

logger = get_logger("hybrid_pipeline")


class HybridExtractionPipeline:
    """
    Hybrid extraction pipeline:
    - Tier 1: Native PDFs → Docling (no OCR) + Camelot + PyMuPDF
    - Tier 2: Scanned PDFs → Gemini Vision + Docling fallback
    """
    
    def __init__(self):
        self.classifier = PDFClassifier()
        self.docling_native = OptimizedDoclingHelper(use_ocr=False)  # Tier 1
        self.docling_scanned = OptimizedDoclingHelper(use_ocr=True)  # Tier 2 fallback
        self.camelot = CamelotExtractor()
        self.pymupdf = PyMuPDFExtractor()
        logger.info("HybridExtractionPipeline initialized")
    
    def extract(self, pdf_path: str, profile: DocumentProfile) -> Tuple[ExtractedDocument, float]:
        """
        Main extraction method - routes to appropriate tier
        
        Args:
            pdf_path: Path to PDF file
            profile: Document profile from triage
            
        Returns:
            Tuple of (ExtractedDocument, confidence_score)
        """
        # Classify document
        is_native = self.classifier.is_native_pdf(pdf_path)
        
        if is_native:
            logger.info(f"Routing to Tier 1 (Native PDF extraction)")
            return self.extract_tier1(pdf_path, profile)
        else:
            logger.info(f"Routing to Tier 2 (Scanned PDF extraction)")
            return self.extract_tier2(pdf_path, profile)
    
    def extract_tier1(self, pdf_path: str, profile: DocumentProfile) -> Tuple[ExtractedDocument, float]:
        """
        Tier 1: Native PDF extraction
        - Text: Docling (no OCR)
        - Tables: Camelot
        - Figures: PyMuPDF
        - Layout: PyMuPDF
        """
        logger.info("Starting Tier 1 extraction...")
        
        # Extract text with Docling (cached)
        docling_text = self.docling_native.extract_text(pdf_path)
        text_blocks = [
            TextBlock(
                content=item['text'],
                bbox=BoundingBox(**item['bbox'], page=item['page']) if item.get('bbox') else BoundingBox(x0=0, y0=0, x1=0, y1=0, page=item['page']),
                reading_order=idx
            )
            for idx, item in enumerate(docling_text)
        ]
        
        # Extract tables with Camelot
        tables = self.camelot.extract_tables(pdf_path)
        
        # Extract figures with PyMuPDF
        figures = self.pymupdf.extract_figures(pdf_path)
        
        # Extract layout with PyMuPDF
        layout_info = self.pymupdf.extract_layout(pdf_path)
        
        confidence = 0.85  # High confidence for native PDFs
        
        extracted_doc = ExtractedDocument(
            doc_id=profile.doc_id,
            filename=profile.filename,
            text_blocks=text_blocks,
            tables=tables,
            figures=figures,
            extraction_strategy="tier1_native",
            confidence_score=confidence,
            metadata={
                'layout_info': layout_info,
                'multi_column_pages': layout_info.get('multi_column_pages', [])
            }
        )
        
        logger.info(f"Tier 1 complete: {len(text_blocks)} blocks, {len(tables)} tables, {len(figures)} figures")
        return extracted_doc, confidence
    
    def extract_tier2(self, pdf_path: str, profile: DocumentProfile) -> Tuple[ExtractedDocument, float]:
        """
        Tier 2: Scanned PDF extraction
        - Page Understanding: Gemini 2.5 Flash
        - Tables: Docling (from OCR conversion)
        - Figures: Gemini Vision
        - Handwriting: Gemini Vision
        - Fallback: GCP Vision → Tesseract
        """
        logger.info("Starting Tier 2 extraction...")
        
        try:
            # Primary: Gemini Vision API
            from ..strategies.vision_augmented import VisionExtractor
            vision_extractor = VisionExtractor()
            extracted_doc, confidence = vision_extractor.extract(pdf_path, profile)
            
            # If tables not found by Gemini, use Docling OCR
            if len(extracted_doc.tables) == 0:
                logger.info("No tables from Gemini, trying Docling OCR...")
                docling_tables = self.docling_scanned.extract_tables(pdf_path)
                if docling_tables:
                    # Convert Docling tables to Table objects
                    from ..models.extracted_document import Table
                    extracted_doc.tables = [
                        Table(
                            headers=[],  # Parse from docling_table['data']
                            rows=[],
                            bbox=BoundingBox(**dt['bbox'], page=dt['page']) if dt['bbox'] else None,
                            table_id=f"docling_table_{idx}"
                        )
                        for idx, dt in enumerate(docling_tables)
                    ]
            
            extracted_doc.extraction_strategy = "tier2_scanned"
            logger.info(f"Tier 2 complete: {len(extracted_doc.text_blocks)} blocks, {len(extracted_doc.tables)} tables")
            return extracted_doc, confidence
            
        except Exception as e:
            logger.error(f"Tier 2 extraction failed: {e}")
            # Fallback to Docling OCR only
            return self.extract_tier2_fallback(pdf_path, profile)
    
    def extract_tier2_fallback(self, pdf_path: str, profile: DocumentProfile) -> Tuple[ExtractedDocument, float]:
        """Fallback: Use Docling OCR for everything"""
        logger.info("Using Tier 2 fallback (Docling OCR)")
        
        # Extract everything with Docling OCR
        docling_text = self.docling_scanned.extract_text(pdf_path)
        docling_tables = self.docling_scanned.extract_tables(pdf_path)
        docling_figures = self.docling_scanned.extract_figures(pdf_path)
        
        text_blocks = [
            TextBlock(
                content=item['text'],
                bbox=BoundingBox(**item['bbox'], page=item['page']) if item.get('bbox') else BoundingBox(x0=0, y0=0, x1=0, y1=0, page=item['page']),
                reading_order=idx
            )
            for idx, item in enumerate(docling_text)
        ]
        
        # Convert Docling outputs to model objects
        from ..models.extracted_document import Table, Figure
        tables = []  # TODO: Convert docling_tables
        figures = []  # TODO: Convert docling_figures
        
        confidence = 0.70  # Lower confidence for OCR
        
        extracted_doc = ExtractedDocument(
            doc_id=profile.doc_id,
            filename=profile.filename,
            text_blocks=text_blocks,
            tables=tables,
            figures=figures,
            extraction_strategy="tier2_fallback_ocr",
            confidence_score=confidence
        )
        
        return extracted_doc, confidence
