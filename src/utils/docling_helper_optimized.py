"""Optimized Docling helper with caching and OCR control"""

from typing import List, Dict, Optional, Any
from pathlib import Path
from ..logging_config import get_logger

logger = get_logger("docling_helper_optimized")


class OptimizedDoclingHelper:
    """Docling helper with caching and configurable OCR"""
    
    def __init__(self, use_ocr: bool = False):
        self.use_ocr = use_ocr
        self.converter = None
        self._cache = {}  # In-memory cache
        self._initialized = False
        logger.info(f"OptimizedDoclingHelper initialized (OCR={'enabled' if use_ocr else 'disabled'})")
    
    def _ensure_initialized(self):
        """Lazy initialization of Docling converter"""
        if self._initialized:
            return
        
        try:
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            
            # Configure pipeline
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = self.use_ocr
            pipeline_options.do_table_structure = True
            
            self.converter = DocumentConverter(
                format_options={
                    "pdf": PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
            self._initialized = True
            logger.info(f"Docling converter initialized (OCR={'on' if self.use_ocr else 'off'})")
        except Exception as e:
            logger.error(f"Failed to initialize Docling: {e}")
            raise
    
    def convert_once(self, pdf_path: str):
        """Convert PDF once and cache result"""
        if pdf_path in self._cache:
            logger.debug(f"Using cached result for {pdf_path}")
            return self._cache[pdf_path]
        
        self._ensure_initialized()
        
        logger.info(f"Converting {pdf_path} with Docling...")
        result = self.converter.convert(pdf_path)
        self._cache[pdf_path] = result
        logger.info(f"Conversion complete, cached for future use")
        
        return result
    
    def extract_text(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract text blocks from cached conversion"""
        result = self.convert_once(pdf_path)
        text_blocks = []
        
        for item in result.document.iterate_items():
            if hasattr(item, 'type') and item.type == 'text':
                text_blocks.append({
                    'text': item.text if hasattr(item, 'text') else '',
                    'page': getattr(item, 'page', 0),
                    'bbox': self._extract_bbox(item)
                })
        
        logger.info(f"Extracted {len(text_blocks)} text blocks")
        return text_blocks
    
    def extract_tables(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract tables from cached conversion"""
        result = self.convert_once(pdf_path)
        tables = []
        
        for item in result.document.iterate_items():
            if hasattr(item, 'type') and item.type == 'table':
                tables.append({
                    'page': getattr(item, 'page', 0),
                    'bbox': self._extract_bbox(item),
                    'data': self._extract_table_data(item)
                })
        
        logger.info(f"Extracted {len(tables)} tables")
        return tables
    
    def extract_figures(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract figures from cached conversion"""
        result = self.convert_once(pdf_path)
        figures = []
        
        for item in result.document.iterate_items():
            if hasattr(item, 'type') and item.type == 'figure':
                figures.append({
                    'page': getattr(item, 'page', 0),
                    'bbox': self._extract_bbox(item),
                    'caption': getattr(item, 'caption', None)
                })
        
        logger.info(f"Extracted {len(figures)} figures")
        return figures
    
    def extract_layout(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract document structure/hierarchy"""
        result = self.convert_once(pdf_path)
        headings = []
        
        for item in result.document.iterate_items():
            if hasattr(item, 'type') and item.type in ['heading', 'title']:
                headings.append({
                    'level': getattr(item, 'level', 1),
                    'text': item.text if hasattr(item, 'text') else '',
                    'page': getattr(item, 'page', 0)
                })
        
        logger.info(f"Extracted {len(headings)} headings")
        return headings
    
    def _extract_bbox(self, item) -> Optional[Dict[str, float]]:
        """Extract bounding box from Docling item"""
        if hasattr(item, 'bbox'):
            bbox = item.bbox
            return {
                'x0': getattr(bbox, 'x0', 0),
                'y0': getattr(bbox, 'y0', 0),
                'x1': getattr(bbox, 'x1', 0),
                'y1': getattr(bbox, 'y1', 0)
            }
        return None
    
    def _extract_table_data(self, item) -> List[List[str]]:
        """Extract table data from Docling table item"""
        # Placeholder - implement based on Docling's table structure
        return []
    
    def clear_cache(self):
        """Clear conversion cache"""
        self._cache.clear()
        logger.info("Cache cleared")
