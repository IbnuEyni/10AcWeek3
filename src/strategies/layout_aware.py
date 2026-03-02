from typing import Tuple, List
from .base import BaseExtractor
from ..models.extracted_document import (
    ExtractedDocument, TextBlock, Table, Figure, BoundingBox
)
from ..models.document_profile import DocumentProfile


class LayoutExtractor(BaseExtractor):
    """Layout-aware extraction using Docling or MinerU"""
    
    def __init__(self):
        self.use_docling = True
        try:
            from docling.document_converter import DocumentConverter
            self.converter = DocumentConverter()
        except ImportError:
            self.use_docling = False
            print("Warning: Docling not available, falling back to pdfplumber")
    
    def extract(self, pdf_path: str, profile: DocumentProfile) -> Tuple[ExtractedDocument, float]:
        """Extract with layout awareness"""
        if self.use_docling:
            return self._extract_with_docling(pdf_path, profile)
        else:
            return self._extract_fallback(pdf_path, profile)
    
    def _extract_with_docling(self, pdf_path: str, profile: DocumentProfile) -> Tuple[ExtractedDocument, float]:
        """Extract using Docling"""
        result = self.converter.convert(pdf_path)
        doc = result.document
        
        text_blocks = []
        tables = []
        figures = []
        
        # Parse Docling output
        for item in doc.iterate_items():
            if item.type == "text":
                bbox = BoundingBox(
                    x0=item.bbox.x0 if hasattr(item, 'bbox') else 0,
                    y0=item.bbox.y0 if hasattr(item, 'bbox') else 0,
                    x1=item.bbox.x1 if hasattr(item, 'bbox') else 0,
                    y1=item.bbox.y1 if hasattr(item, 'bbox') else 0,
                    page=item.page if hasattr(item, 'page') else 0
                )
                text_blocks.append(TextBlock(
                    content=item.text,
                    bbox=bbox,
                    reading_order=len(text_blocks)
                ))
            elif item.type == "table":
                # Extract table structure
                pass  # Implement table parsing
        
        confidence = 0.85  # Higher confidence for layout-aware
        
        extracted_doc = ExtractedDocument(
            doc_id=profile.doc_id,
            filename=profile.filename,
            text_blocks=text_blocks,
            tables=tables,
            figures=figures,
            extraction_strategy=self.strategy_name,
            confidence_score=confidence
        )
        
        return extracted_doc, confidence
    
    def _extract_fallback(self, pdf_path: str, profile: DocumentProfile) -> Tuple[ExtractedDocument, float]:
        """Fallback to pdfplumber with enhanced processing"""
        import pdfplumber
        
        text_blocks = []
        tables = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract with layout preservation
                text = page.extract_text(layout=True)
                if text:
                    bbox = BoundingBox(x0=0, y0=0, x1=page.width, y1=page.height, page=page_num)
                    text_blocks.append(TextBlock(
                        content=text,
                        bbox=bbox,
                        reading_order=len(text_blocks)
                    ))
                
                # Extract tables with settings
                page_tables = page.extract_tables()
                for table_data in page_tables:
                    if table_data and len(table_data) > 1:
                        headers = [str(h) if h is not None else "" for h in (table_data[0] or [])]
                        rows = [[str(cell) if cell is not None else "" for cell in row] for row in table_data[1:]]
                        tables.append(Table(
                            headers=headers,
                            rows=rows,
                            bbox=BoundingBox(x0=0, y0=0, x1=page.width, y1=page.height, page=page_num),
                            table_id=f"table_{page_num}_{len(tables)}"
                        ))
        
        confidence = 0.75
        
        extracted_doc = ExtractedDocument(
            doc_id=profile.doc_id,
            filename=profile.filename,
            text_blocks=text_blocks,
            tables=tables,
            extraction_strategy=self.strategy_name,
            confidence_score=confidence
        )
        
        return extracted_doc, confidence
    
    def estimate_cost(self, profile: DocumentProfile) -> float:
        """Medium cost for layout-aware extraction"""
        return 0.01 * profile.total_pages  # $0.01 per page
    
    @property
    def strategy_name(self) -> str:
        return "layout_aware"
