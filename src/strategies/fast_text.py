import pdfplumber
from typing import Tuple, List
from .base import BaseExtractor
from ..models.extracted_document import (
    ExtractedDocument, TextBlock, Table, BoundingBox
)
from ..models.document_profile import DocumentProfile


class FastTextExtractor(BaseExtractor):
    """Fast text extraction using pdfplumber for native digital PDFs"""
    
    CONFIDENCE_THRESHOLD = 0.7
    MIN_CHAR_DENSITY = 0.01
    
    def extract(self, pdf_path: str, profile: DocumentProfile) -> Tuple[ExtractedDocument, float]:
        """Extract text and tables from native digital PDF"""
        text_blocks = []
        tables = []
        reading_order = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # Extract text blocks
                text = page.extract_text()
                if text:
                    bbox = BoundingBox(
                        x0=0, y0=0, 
                        x1=page.width, y1=page.height,
                        page=page_num
                    )
                    text_blocks.append(TextBlock(
                        content=text,
                        bbox=bbox,
                        reading_order=len(text_blocks)
                    ))
                    reading_order.append(len(text_blocks) - 1)
                
                # Extract tables
                page_tables = page.extract_tables()
                for table_data in page_tables:
                    if table_data and len(table_data) > 1:
                        headers = [str(h) if h is not None else "" for h in (table_data[0] if table_data[0] else [])]
                        rows = [[str(cell) if cell is not None else "" for cell in row] for row in table_data[1:]] if len(table_data) > 1 else []
                        
                        # Get table bbox (approximate)
                        table_bbox = BoundingBox(
                            x0=0, y0=0,
                            x1=page.width, y1=page.height,
                            page=page_num
                        )
                        
                        tables.append(Table(
                            headers=headers,
                            rows=rows,
                            bbox=table_bbox,
                            table_id=f"table_{page_num}_{len(tables)}"
                        ))
        
        # Calculate confidence
        confidence = self._calculate_confidence(profile, text_blocks, tables)
        
        extracted_doc = ExtractedDocument(
            doc_id=profile.doc_id,
            filename=profile.filename,
            text_blocks=text_blocks,
            tables=tables,
            reading_order=reading_order,
            extraction_strategy=self.strategy_name,
            confidence_score=confidence
        )
        
        return extracted_doc, confidence
    
    def _calculate_confidence(
        self, profile: DocumentProfile, 
        text_blocks: List[TextBlock], 
        tables: List[Table]
    ) -> float:
        """Calculate extraction confidence based on multiple signals"""
        signals = []
        
        # Signal 1: Character density
        if profile.character_density > self.MIN_CHAR_DENSITY:
            signals.append(0.9)
        else:
            signals.append(0.3)
        
        # Signal 2: Font metadata presence
        if profile.has_font_metadata:
            signals.append(0.95)
        else:
            signals.append(0.4)
        
        # Signal 3: Image ratio (lower is better for text extraction)
        if profile.image_ratio < 0.3:
            signals.append(0.9)
        elif profile.image_ratio < 0.6:
            signals.append(0.6)
        else:
            signals.append(0.3)
        
        # Signal 4: Content extracted
        if len(text_blocks) > 0:
            signals.append(0.8)
        else:
            signals.append(0.1)
        
        return sum(signals) / len(signals)
    
    def estimate_cost(self, profile: DocumentProfile) -> float:
        """Estimate cost - very low for fast text extraction"""
        return 0.001 * profile.total_pages  # $0.001 per page
    
    @property
    def strategy_name(self) -> str:
        return "fast_text"
