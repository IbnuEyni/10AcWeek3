"""
PageIndex Builder Agent - AI-Native (Docling DOM)
Uses Docling's native Document Object Model instead of regex
"""

from typing import List, Optional
from pathlib import Path
import json
from ..models.pageindex import PageIndex, Section
from ..models.extracted_document import ExtractedDocument
from ..models.ldu import LDU
from ..logging_config import get_logger

logger = get_logger("pageindex_builder_ai")


class PageIndexBuilderAI:
    """Builds PageIndex using Docling's native DOM (no regex)"""
    
    def __init__(self):
        self.docling_available = False
        try:
            from docling.document_converter import DocumentConverter
            self.converter = DocumentConverter()
            self.docling_available = True
            logger.info("Docling DOM available for PageIndex building")
        except ImportError:
            logger.warning("Docling not available, falling back to basic indexing")
    
    def build_index(
        self, 
        extracted_doc: ExtractedDocument, 
        ldus: List[LDU],
        pdf_path: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> PageIndex:
        """
        Build PageIndex using Docling DOM
        
        Args:
            extracted_doc: Extracted document
            ldus: List of LDUs
            pdf_path: Path to original PDF (for Docling DOM extraction)
            output_path: Optional path to save PageIndex
            
        Returns:
            PageIndex with hierarchical structure
        """
        logger.info(f"Building PageIndex for {extracted_doc.doc_id}")
        
        # Try Docling DOM first
        if self.docling_available and pdf_path:
            sections = self._extract_from_docling_dom(pdf_path)
        else:
            # Fallback: extract from text blocks
            sections = self._extract_from_text_blocks(extracted_doc)
        
        # Build hierarchy
        root_sections = self._build_hierarchy(sections)
        
        # Ensure at least one section exists
        if not root_sections:
            root_sections = [Section(
                section_id="sec_1",
                title="Document Content",
                page_start=0,
                page_end=self._get_total_pages(extracted_doc) - 1,
                level=0,
                parent_id=None,
                child_sections=[],
                ldu_ids=[],
                key_entities=[],
                data_types_present=[]
            )]
        
        # Link LDUs to sections
        self._link_ldus_to_sections(root_sections, ldus)
        
        # Create PageIndex
        page_index = PageIndex(
            doc_id=extracted_doc.doc_id,
            filename=extracted_doc.filename,
            root_sections=root_sections,
            total_pages=self._get_total_pages(extracted_doc)
        )
        
        # Save
        if output_path:
            self._save_index(page_index, output_path)
        
        logger.info(f"PageIndex built with {len(root_sections)} root sections")
        return page_index
    
    def _extract_from_docling_dom(self, pdf_path: str) -> List[dict]:
        """Extract sections from Docling's native DOM"""
        sections = []
        section_counter = 0
        
        try:
            result = self.converter.convert(pdf_path)
            
            for item in result.document.iterate_items():
                # Check for heading types
                if hasattr(item, 'type') and 'heading' in str(item.type).lower():
                    section_counter += 1
                    
                    # Extract level from type (heading_1, heading_2, etc.)
                    level = self._extract_level_from_type(str(item.type))
                    
                    sections.append({
                        'section_id': f"sec_{section_counter}",
                        'title': item.text if hasattr(item, 'text') else f"Section {section_counter}",
                        'page_start': getattr(item, 'page', 0),
                        'page_end': getattr(item, 'page', 0),
                        'level': level,
                        'parent_id': None,
                        'child_sections': [],
                        'ldu_ids': [],
                        'key_entities': [],
                        'data_types_present': []
                    })
            
            logger.info(f"Extracted {len(sections)} sections from Docling DOM")
            
        except Exception as e:
            logger.error(f"Docling DOM extraction failed: {e}")
            return []
        
        return sections
    
    def _extract_level_from_type(self, type_str: str) -> int:
        """Extract hierarchy level from Docling type (heading_1 -> 1)"""
        import re
        match = re.search(r'heading[_\s]?(\d+)', type_str.lower())
        if match:
            return int(match.group(1))
        return 0
    
    def _extract_from_text_blocks(self, extracted_doc: ExtractedDocument) -> List[dict]:
        """Fallback: extract sections from text blocks"""
        sections = []
        section_counter = 0
        
        for block in extracted_doc.text_blocks:
            # Simple heuristic: short lines in ALL CAPS or starting with numbers
            text = block.content.strip()
            
            if len(text) < 100 and (text.isupper() or text[0].isdigit()):
                section_counter += 1
                sections.append({
                    'section_id': f"sec_{section_counter}",
                    'title': text,
                    'page_start': block.bbox.page,
                    'page_end': block.bbox.page,
                    'level': 0,
                    'parent_id': None,
                    'child_sections': [],
                    'ldu_ids': [],
                    'key_entities': [],
                    'data_types_present': []
                })
        
        # Default section if none found
        if not sections:
            sections.append({
                'section_id': 'sec_1',
                'title': 'Document Content',
                'page_start': 0,
                'page_end': self._get_total_pages(extracted_doc) - 1,
                'level': 0,
                'parent_id': None,
                'child_sections': [],
                'ldu_ids': [],
                'key_entities': [],
                'data_types_present': []
            })
        
        return sections
    
    def _build_hierarchy(self, sections: List[dict]) -> List[Section]:
        """Build hierarchical structure"""
        if not sections:
            return []
        
        section_objects = [Section(**sec) for sec in sections]
        
        root_sections = []
        stack = []
        
        for section in section_objects:
            while stack and stack[-1].level >= section.level:
                stack.pop()
            
            if stack:
                parent = stack[-1]
                section.parent_id = parent.section_id
                parent.child_sections.append(section)
            else:
                root_sections.append(section)
            
            stack.append(section)
        
        return root_sections
    
    def _link_ldus_to_sections(self, sections: List[Section], ldus: List[LDU]):
        """Link LDUs to sections"""
        def link_recursive(section: Section):
            for ldu in ldus:
                ldu_pages = ldu.page_refs if hasattr(ldu, 'page_refs') else []
                
                if ldu_pages:
                    ldu_page = ldu_pages[0] if isinstance(ldu_pages, list) else ldu_pages
                    
                    if section.page_start <= ldu_page <= section.page_end:
                        section.ldu_ids.append(ldu.ldu_id)
                        
                        if ldu.chunk_type == 'table' and 'table' not in section.data_types_present:
                            section.data_types_present.append('table')
                        elif ldu.chunk_type == 'figure' and 'figure' not in section.data_types_present:
                            section.data_types_present.append('figure')
            
            for child in section.child_sections:
                link_recursive(child)
        
        for section in sections:
            link_recursive(section)
    
    def _get_total_pages(self, extracted_doc: ExtractedDocument) -> int:
        """Get total page count"""
        max_page = 0
        
        for block in extracted_doc.text_blocks:
            max_page = max(max_page, block.bbox.page)
        
        for table in extracted_doc.tables:
            max_page = max(max_page, table.bbox.page)
        
        for figure in extracted_doc.figures:
            max_page = max(max_page, figure.bbox.page)
        
        return max_page + 1
    
    def _save_index(self, page_index: PageIndex, output_path: str):
        """Save PageIndex to JSON"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(page_index.model_dump(), f, indent=2)
        
        logger.info(f"PageIndex saved to {output_path}")
