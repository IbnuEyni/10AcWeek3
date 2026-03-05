"""Document structure analysis using Docling for semantic chunking"""

from typing import List, Dict, Optional, Any
from pathlib import Path
from ..logging_config import get_logger
from ..utils.docling_helper import DoclingHelper

logger = get_logger("structure_analyzer")


class DocumentStructureAnalyzer:
    """Analyze document structure for semantic chunking"""
    
    def __init__(self):
        self.docling_helper = DoclingHelper()
    
    def analyze_structure(self, pdf_path: str) -> Dict[str, Any]:
        """
        Analyze complete document structure
        
        Returns:
            Dictionary with sections, lists, reading_order, layout_info
        """
        if not self.docling_helper.use_docling:
            logger.warning("Docling not available, returning basic structure")
            return self._basic_structure()
        
        try:
            sections = self.docling_helper.extract_document_structure(pdf_path)
            lists = self.docling_helper.extract_lists(pdf_path)
            
            # Build hierarchy
            hierarchy = self._build_hierarchy(sections)
            
            result = {
                'sections': sections,
                'lists': lists,
                'hierarchy': hierarchy,
                'has_structure': len(sections) > 0
            }
            
            logger.info(f"Analyzed structure: {len(sections)} sections, {len(lists)} lists")
            return result
            
        except Exception as e:
            logger.error(f"Structure analysis failed: {e}")
            return self._basic_structure()
    
    def get_page_layout_info(self, pdf_path: str, page_num: int) -> Dict[str, Any]:
        """Get detailed layout information for a specific page"""
        if not self.docling_helper.use_docling:
            return {'layout_type': 'simple', 'multi_column': False}
        
        try:
            layout_info = self.docling_helper.classify_page_layout(pdf_path, page_num)
            reading_order = self.docling_helper.get_reading_order(pdf_path, page_num)
            
            return {
                **layout_info,
                'reading_order_items': len(reading_order),
                'has_reading_order': len(reading_order) > 0
            }
        except Exception as e:
            logger.error(f"Page layout analysis failed: {e}")
            return {'layout_type': 'simple', 'multi_column': False}
    
    def _build_hierarchy(self, sections: List[Dict]) -> List[Dict]:
        """Build hierarchical structure from flat section list"""
        if not sections:
            return []
        
        hierarchy = []
        stack = []
        
        for section in sections:
            level = section['level']
            
            # Pop stack until we find parent level
            while stack and stack[-1]['level'] >= level:
                stack.pop()
            
            # Add to parent's children or root
            node = {
                **section,
                'children': []
            }
            
            if stack:
                stack[-1]['children'].append(node)
            else:
                hierarchy.append(node)
            
            stack.append(node)
        
        return hierarchy
    
    def _basic_structure(self) -> Dict[str, Any]:
        """Return basic structure when Docling unavailable"""
        return {
            'sections': [],
            'lists': [],
            'hierarchy': [],
            'has_structure': False
        }
    
    def get_section_for_page(self, structure: Dict[str, Any], page_num: int) -> Optional[Dict]:
        """Find which section a page belongs to"""
        sections = structure.get('sections', [])
        
        # Find the section that contains this page
        current_section = None
        for section in sections:
            if section['page'] <= page_num:
                current_section = section
            else:
                break
        
        return current_section
