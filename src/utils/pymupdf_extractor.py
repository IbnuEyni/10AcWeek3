"""PyMuPDF-based extractors for figures and layout"""

from typing import List, Dict, Any
from ..logging_config import get_logger
from ..models.extracted_document import Figure, BoundingBox

logger = get_logger("pymupdf_extractor")

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF not installed. Figure/layout extraction will be limited.")


class PyMuPDFExtractor:
    """Fast extraction using PyMuPDF"""
    
    def extract_figures(self, pdf_path: str) -> List[Figure]:
        """Extract figures with bounding boxes"""
        if not PYMUPDF_AVAILABLE:
            logger.warning("PyMuPDF not available, skipping figure extraction")
            return []
        
        figures = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num, page in enumerate(doc):
                # Get all images on page
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    
                    # Get image bounding box
                    rects = page.get_image_rects(xref)
                    
                    for rect in rects:
                        bbox = BoundingBox(
                            x0=rect.x0,
                            y0=rect.y0,
                            x1=rect.x1,
                            y1=rect.y1,
                            page=page_num
                        )
                        
                        figure = Figure(
                            figure_id=f"fig_{page_num}_{img_index}",
                            bbox=bbox,
                            page=page_num,
                            caption=None,  # Will be bound later
                            metadata={'source': 'pymupdf', 'xref': xref}
                        )
                        figures.append(figure)
            
            doc.close()
            logger.info(f"Extracted {len(figures)} figures using PyMuPDF")
            
        except Exception as e:
            logger.error(f"PyMuPDF figure extraction failed: {e}")
        
        return figures
    
    def extract_layout(self, pdf_path: str) -> Dict[str, Any]:
        """Extract layout information (blocks, columns, reading order)"""
        if not PYMUPDF_AVAILABLE:
            logger.warning("PyMuPDF not available, skipping layout extraction")
            return {'pages': [], 'multi_column_pages': [], 'reading_order': []}
        
        layout_info = {
            'pages': [],
            'multi_column_pages': [],
            'reading_order': []
        }
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num, page in enumerate(doc):
                # Get text blocks with positions
                blocks = page.get_text("dict")["blocks"]
                
                text_blocks = []
                for block in blocks:
                    if block.get("type") == 0:  # Text block
                        text_blocks.append({
                            'bbox': block["bbox"],
                            'text': self._extract_block_text(block),
                            'page': page_num
                        })
                
                # Detect columns
                is_multi_column = self._detect_columns(text_blocks, page.rect.width)
                
                layout_info['pages'].append({
                    'page_num': page_num,
                    'blocks': text_blocks,
                    'multi_column': is_multi_column,
                    'width': page.rect.width,
                    'height': page.rect.height
                })
                
                if is_multi_column:
                    layout_info['multi_column_pages'].append(page_num)
            
            doc.close()
            logger.info(f"Extracted layout for {len(layout_info['pages'])} pages")
            
        except Exception as e:
            logger.error(f"PyMuPDF layout extraction failed: {e}")
        
        return layout_info
    
    def _extract_block_text(self, block: Dict) -> str:
        """Extract text from block"""
        text_parts = []
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text_parts.append(span.get("text", ""))
        return " ".join(text_parts)
    
    def _detect_columns(self, blocks: List[Dict], page_width: float) -> bool:
        """Detect if page has multiple columns"""
        if len(blocks) < 3:
            return False
        
        # Group blocks by horizontal position
        left_blocks = [b for b in blocks if b['bbox'][0] < page_width * 0.4]
        right_blocks = [b for b in blocks if b['bbox'][0] > page_width * 0.5]
        
        # If significant blocks on both sides, likely multi-column
        return len(left_blocks) > 2 and len(right_blocks) > 2
