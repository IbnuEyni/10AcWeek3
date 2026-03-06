"""
PageIndex Builder Agent - Stage 4
Builds hierarchical navigation structure from extracted document
"""

import re
from typing import List, Dict, Optional
from pathlib import Path
import json
from ..models.pageindex import PageIndex, Section
from ..models.extracted_document import ExtractedDocument
from ..models.ldu import LDU
from ..logging_config import get_logger

logger = get_logger("pageindex_builder")


class PageIndexBuilder:
    """Builds hierarchical PageIndex from extracted document and LDUs"""
    
    def __init__(self):
        # Heading patterns for section detection
        self.heading_patterns = [
            r'^#+\s+(.+)$',  # Markdown headings
            r'^(\d+\.)+\s+(.+)$',  # Numbered sections (1.1, 1.2.3)
            r'^[A-Z][A-Z\s]+$',  # ALL CAPS headings
            r'^(Chapter|Section|Part)\s+\d+',  # Explicit chapter/section
        ]
        
        # Common section keywords
        self.section_keywords = [
            'introduction', 'background', 'methodology', 'results',
            'discussion', 'conclusion', 'references', 'appendix',
            'abstract', 'summary', 'overview', 'executive summary'
        ]
    
    def build_index(
        self, 
        extracted_doc: ExtractedDocument, 
        ldus: List[LDU],
        output_path: Optional[str] = None
    ) -> PageIndex:
        """
        Build PageIndex from extracted document and LDUs
        
        Args:
            extracted_doc: Extracted document with text blocks
            ldus: List of Logical Document Units
            output_path: Optional path to save PageIndex JSON
            
        Returns:
            PageIndex with hierarchical structure
        """
        logger.info(f"Building PageIndex for {extracted_doc.doc_id}")
        
        # Step 1: Detect sections from text blocks
        sections = self._detect_sections(extracted_doc)
        
        # Step 2: Build hierarchy
        root_sections = self._build_hierarchy(sections)
        
        # Step 3: Link LDUs to sections
        self._link_ldus_to_sections(root_sections, ldus)
        
        # Step 4: Generate summaries
        self._generate_section_summaries(root_sections, ldus)
        
        # Create PageIndex
        page_index = PageIndex(
            doc_id=extracted_doc.doc_id,
            filename=extracted_doc.filename,
            root_sections=root_sections,
            total_pages=self._get_total_pages(extracted_doc)
        )
        
        # Save to file
        if output_path:
            self._save_index(page_index, output_path)
        
        logger.info(f"PageIndex built with {len(root_sections)} root sections")
        return page_index
    
    def _detect_sections(self, extracted_doc: ExtractedDocument) -> List[Dict]:
        """Detect sections from text blocks"""
        sections = []
        section_counter = 0
        
        for block in extracted_doc.text_blocks:
            # Check if block is a heading
            is_heading, level, title = self._is_heading(block.content)
            
            if is_heading:
                section_counter += 1
                sections.append({
                    'section_id': f"sec_{section_counter}",
                    'title': title,
                    'page_start': block.bbox.page,
                    'page_end': block.bbox.page,  # Will be updated
                    'level': level,
                    'parent_id': None,  # Will be set in hierarchy building
                    'child_sections': [],
                    'ldu_ids': [],
                    'key_entities': [],
                    'data_types_present': []
                })
        
        # Update page_end for each section
        for i, section in enumerate(sections):
            if i < len(sections) - 1:
                section['page_end'] = sections[i + 1]['page_start'] - 1
            else:
                section['page_end'] = self._get_total_pages(extracted_doc) - 1
        
        # If no sections detected, create default section
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
    
    def _is_heading(self, text: str) -> tuple[bool, int, str]:
        """
        Check if text is a heading
        
        Returns:
            (is_heading, level, cleaned_title)
        """
        text = text.strip()
        
        # Check markdown headings
        if text.startswith('#'):
            level = len(text) - len(text.lstrip('#'))
            title = text.lstrip('#').strip()
            return True, level, title
        
        # Check numbered sections (1.1, 1.2.3)
        numbered_match = re.match(r'^((\d+\.)+)\s+(.+)$', text)
        if numbered_match:
            dots = numbered_match.group(1).count('.')
            title = numbered_match.group(3)
            return True, dots, title
        
        # Check ALL CAPS (short lines only)
        if text.isupper() and len(text) < 100 and len(text.split()) < 10:
            return True, 0, text
        
        # Check explicit keywords
        for keyword in self.section_keywords:
            if text.lower().startswith(keyword):
                return True, 0, text
        
        return False, 0, text
    
    def _build_hierarchy(self, sections: List[Dict]) -> List[Section]:
        """Build hierarchical structure from flat section list"""
        if not sections:
            return []
        
        # Convert to Section objects
        section_objects = []
        for sec_dict in sections:
            section = Section(**sec_dict)
            section_objects.append(section)
        
        # Build parent-child relationships
        root_sections = []
        stack = []  # Stack to track current hierarchy
        
        for section in section_objects:
            # Pop stack until we find appropriate parent
            while stack and stack[-1].level >= section.level:
                stack.pop()
            
            if stack:
                # Add as child to parent
                parent = stack[-1]
                section.parent_id = parent.section_id
                parent.child_sections.append(section)
            else:
                # Root level section
                root_sections.append(section)
            
            stack.append(section)
        
        return root_sections
    
    def _link_ldus_to_sections(self, sections: List[Section], ldus: List[LDU]):
        """Link LDUs to their containing sections"""
        
        def link_recursive(section: Section):
            for ldu in ldus:
                # Check if LDU is in this section's page range
                ldu_pages = ldu.page_refs if hasattr(ldu, 'page_refs') else []
                
                if ldu_pages:
                    ldu_page = ldu_pages[0] if isinstance(ldu_pages, list) else ldu_pages
                    
                    if section.page_start <= ldu_page <= section.page_end:
                        section.ldu_ids.append(ldu.ldu_id)
                        
                        # Track data types
                        if ldu.chunk_type == 'table' and 'table' not in section.data_types_present:
                            section.data_types_present.append('table')
                        elif ldu.chunk_type == 'figure' and 'figure' not in section.data_types_present:
                            section.data_types_present.append('figure')
            
            # Recurse to children
            for child in section.child_sections:
                link_recursive(child)
        
        for section in sections:
            link_recursive(section)
    
    def _generate_section_summaries(self, sections: List[Section], ldus: List[LDU]):
        """Generate summaries for sections"""
        
        def summarize_recursive(section: Section):
            # Get LDUs in this section
            section_ldus = [ldu for ldu in ldus if ldu.ldu_id in section.ldu_ids]
            
            if section_ldus:
                # Simple summary: first 200 chars of first text LDU
                text_ldus = [ldu for ldu in section_ldus if ldu.chunk_type == 'text']
                if text_ldus:
                    section.summary = text_ldus[0].content[:200] + "..."
            
            # Recurse to children
            for child in section.child_sections:
                summarize_recursive(child)
        
        for section in sections:
            summarize_recursive(section)
    
    def _get_total_pages(self, extracted_doc: ExtractedDocument) -> int:
        """Get total page count from extracted document"""
        max_page = 0
        
        for block in extracted_doc.text_blocks:
            max_page = max(max_page, block.bbox.page)
        
        for table in extracted_doc.tables:
            max_page = max(max_page, table.bbox.page)
        
        for figure in extracted_doc.figures:
            max_page = max(max_page, figure.bbox.page)
        
        return max_page + 1  # Pages are 0-indexed
    
    def _save_index(self, page_index: PageIndex, output_path: str):
        """Save PageIndex to JSON file"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(page_index.model_dump(), f, indent=2)
        
        logger.info(f"PageIndex saved to {output_path}")
