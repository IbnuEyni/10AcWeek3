"""Hierarchical LDU tree builder"""

from typing import List
from ..models.ldu import LDU

class LDUTreeBuilder:
    """Build hierarchical parent-child relationships between LDUs"""
    
    def build_hierarchy(self, ldus: List[LDU]) -> List[LDU]:
        """Build parent-child relationships"""
        page_groups = {}
        for ldu in ldus:
            for page in ldu.page_refs:
                if page not in page_groups:
                    page_groups[page] = []
                page_groups[page].append(ldu)
        
        for page, page_ldus in page_groups.items():
            sorted_ldus = sorted(page_ldus, key=lambda l: l.bounding_boxes[0].y0 if l.bounding_boxes else 0)
            
            for i in range(len(sorted_ldus) - 1):
                current = sorted_ldus[i]
                next_ldu = sorted_ldus[i + 1]
                
                if next_ldu.ldu_id not in current.related_chunks:
                    current.related_chunks.append(next_ldu.ldu_id)
                if current.ldu_id not in next_ldu.related_chunks:
                    next_ldu.related_chunks.append(current.ldu_id)
        
        for i, ldu in enumerate(ldus):
            if self._is_section_header(ldu):
                for j in range(i + 1, len(ldus)):
                    if self._is_section_header(ldus[j]):
                        break
                    if ldus[j].parent_section is None:
                        ldus[j].parent_section = ldu.ldu_id
        
        return ldus
    
    def _is_section_header(self, ldu: LDU) -> bool:
        content = ldu.content.strip()
        if len(content) > 100:
            return False
        if content.endswith(':') or content.isupper():
            return True
        if content and content[0].isdigit():
            return True
        return False
