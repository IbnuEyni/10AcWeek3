"""Docling integration utilities for enhanced document processing"""

from typing import List, Dict, Optional, Any
from pathlib import Path
from ..logging_config import get_logger

logger = get_logger("docling_helper")


class DoclingHelper:
    """Helper class for Docling document processing with FAST mode (no OCR/AI)"""
    
    def __init__(self, use_fast_mode: bool = True):
        self.use_docling = False
        self.converter = None
        self.use_fast_mode = use_fast_mode
        
        try:
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            
            # Configure FAST mode (no OCR, no AI table structure)
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = False
            pipeline_options.do_table_structure = False
            
            self.converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
            self.use_docling = True
            logger.info("Docling initialized in FAST mode (no OCR/AI)")
        except ImportError:
            logger.warning("Docling not available, falling back to pdfplumber")
        except Exception as e:
            logger.error(f"Failed to initialize Docling: {e}")
    
    def extract_document_structure(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract document hierarchy (sections, headings)"""
        if not self.use_docling:
            return []
        
        try:
            result = self.converter.convert(pdf_path)
            sections = []
            
            for item in result.document.iterate_items():
                if hasattr(item, 'type') and item.type in ['heading', 'title']:
                    sections.append({
                        'level': getattr(item, 'level', 1),
                        'title': item.text,
                        'page': getattr(item, 'page', 0),
                        'bbox': self._extract_bbox(item)
                    })
            
            logger.info(f"Extracted {len(sections)} sections from {pdf_path}")
            return sections
        except Exception as e:
            logger.error(f"Failed to extract structure: {e}")
            return []
    
    def get_reading_order(self, pdf_path: str, page_num: int) -> List[Dict[str, Any]]:
        """Get correct reading order for a page"""
        if not self.use_docling:
            return []
        
        try:
            result = self.converter.convert(pdf_path)
            items = []
            
            for item in result.document.iterate_items():
                if hasattr(item, 'page') and item.page == page_num:
                    items.append({
                        'text': item.text if hasattr(item, 'text') else '',
                        'type': getattr(item, 'type', 'text'),
                        'reading_order': getattr(item, 'reading_order', 0),
                        'bbox': self._extract_bbox(item)
                    })
            
            # Sort by reading order
            items.sort(key=lambda x: x['reading_order'])
            return items
        except Exception as e:
            logger.error(f"Failed to get reading order: {e}")
            return []
    
    def extract_figures_with_captions(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract figures with associated captions"""
        if not self.use_docling:
            return []
        
        try:
            result = self.converter.convert(pdf_path)
            figures = []
            
            for item in result.document.iterate_items():
                if hasattr(item, 'type') and item.type == 'figure':
                    figures.append({
                        'page': getattr(item, 'page', 0),
                        'bbox': self._extract_bbox(item),
                        'caption': getattr(item, 'caption', None),
                        'figure_id': getattr(item, 'id', None)
                    })
            
            logger.info(f"Extracted {len(figures)} figures with captions")
            return figures
        except Exception as e:
            logger.error(f"Failed to extract figures: {e}")
            return []
    
    def extract_lists(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract lists as coherent units"""
        if not self.use_docling:
            return []
        
        try:
            result = self.converter.convert(pdf_path)
            lists = []
            current_list = None
            
            for item in result.document.iterate_items():
                if hasattr(item, 'type'):
                    if item.type == 'list':
                        current_list = {
                            'page': getattr(item, 'page', 0),
                            'items': [],
                            'bbox': self._extract_bbox(item)
                        }
                        lists.append(current_list)
                    elif item.type == 'list_item' and current_list:
                        current_list['items'].append(item.text if hasattr(item, 'text') else '')
            
            logger.info(f"Extracted {len(lists)} lists")
            return lists
        except Exception as e:
            logger.error(f"Failed to extract lists: {e}")
            return []
    
    def classify_page_layout(self, pdf_path: str, page_num: int) -> Dict[str, Any]:
        """Classify layout type for a specific page"""
        if not self.use_docling:
            return {'multi_column': False, 'table_heavy': False, 'layout_type': 'simple'}
        
        try:
            result = self.converter.convert(pdf_path)
            page_items = [item for item in result.document.iterate_items() 
                         if hasattr(item, 'page') and item.page == page_num]
            
            # Analyze layout
            columns = set()
            table_count = 0
            
            for item in page_items:
                if hasattr(item, 'column'):
                    columns.add(item.column)
                if hasattr(item, 'type') and item.type == 'table':
                    table_count += 1
            
            has_columns = len(columns) > 1
            is_table_heavy = table_count > 3
            
            return {
                'multi_column': has_columns,
                'table_heavy': is_table_heavy,
                'table_count': table_count,
                'column_count': len(columns),
                'layout_type': 'complex' if has_columns or is_table_heavy else 'simple'
            }
        except Exception as e:
            logger.error(f"Failed to classify layout: {e}")
            return {'multi_column': False, 'table_heavy': False, 'layout_type': 'simple'}
    
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
