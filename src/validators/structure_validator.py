"""Structure validation for extraction quality assurance"""

from typing import List, Dict
from ..models.extracted_document import ExtractedDocument, TextBlock, Table
from ..models.ldu import LDU

class StructureValidator:
    """Validate structure preservation in extraction"""
    
    def validate_extraction(self, doc: ExtractedDocument) -> Dict[str, bool]:
        """Validate extraction quality"""
        if not (doc.text_blocks or doc.tables or doc.figures):
            # Extraction produced nothing; treat as invalid so the router can escalate
            return {
                'has_content': False,
                'reading_order_valid': False,
                'tables_have_headers': False,
                'bboxes_valid': False,
                'no_overlapping_blocks': False,
            }

        return {
            'has_content': True,
            'reading_order_valid': self._check_reading_order(doc.text_blocks),
            'tables_have_headers': self._check_table_headers(doc.tables),
            'bboxes_valid': self._check_bboxes(doc.text_blocks, doc.tables),
            'no_overlapping_blocks': self._check_no_overlap(doc.text_blocks),
        }
    
    def validate_chunking(self, ldus: List[LDU], doc: ExtractedDocument) -> Dict[str, bool]:
        """Validate chunking quality"""
        return {
            'tables_not_split': self._check_tables_intact(ldus, doc.tables),
            'all_content_preserved': self._check_content_coverage(ldus, doc),
            'hashes_unique': self._check_unique_hashes(ldus),
            'page_refs_valid': self._check_page_refs(ldus),
        }
    
    def _check_reading_order(self, blocks: List[TextBlock]) -> bool:
        if not blocks:
            return True
        orders = [b.reading_order for b in blocks]
        return orders == sorted(orders)
    
    def _check_table_headers(self, tables: List[Table]) -> bool:
        if not tables:
            return True
        return all(len(t.headers) > 0 for t in tables)
    
    def _check_bboxes(self, blocks: List[TextBlock], tables: List[Table]) -> bool:
        for block in blocks:
            if block.bbox.x1 <= block.bbox.x0 or block.bbox.y1 <= block.bbox.y0:
                return False
        for table in tables:
            if table.bbox.x1 <= table.bbox.x0 or table.bbox.y1 <= table.bbox.y0:
                return False
        return True
    
    def _check_no_overlap(self, blocks: List[TextBlock]) -> bool:
        pages = {}
        for block in blocks:
            page = block.bbox.page
            if page not in pages:
                pages[page] = []
            pages[page].append(block)
        
        for page_blocks in pages.values():
            for i, b1 in enumerate(page_blocks):
                for b2 in page_blocks[i+1:]:
                    if self._boxes_overlap(b1.bbox, b2.bbox):
                        return False
        return True
    
    def _boxes_overlap(self, bbox1, bbox2) -> bool:
        x_overlap = max(0, min(bbox1.x1, bbox2.x1) - max(bbox1.x0, bbox2.x0))
        y_overlap = max(0, min(bbox1.y1, bbox2.y1) - max(bbox1.y0, bbox2.y0))
        overlap_area = x_overlap * y_overlap
        
        area1 = (bbox1.x1 - bbox1.x0) * (bbox1.y1 - bbox1.y0)
        area2 = (bbox2.x1 - bbox2.x0) * (bbox2.y1 - bbox2.y0)
        
        min_area = min(area1, area2)
        return overlap_area > 0.3 * min_area if min_area > 0 else False
    
    def _check_tables_intact(self, ldus: List[LDU], tables: List[Table]) -> bool:
        table_ldus = [ldu for ldu in ldus if ldu.chunk_type == 'table']
        return len(table_ldus) == len(tables)
    
    def _check_content_coverage(self, ldus: List[LDU], doc: ExtractedDocument) -> bool:
        total_ldu_chars = sum(len(ldu.content) for ldu in ldus)
        total_doc_chars = sum(len(b.content) for b in doc.text_blocks)
        total_doc_chars += sum(len(str(t.headers) + str(t.rows)) for t in doc.tables)
        
        return 0.9 <= total_ldu_chars / max(total_doc_chars, 1) <= 1.1
    
    def _check_unique_hashes(self, ldus: List[LDU]) -> bool:
        hashes = [ldu.content_hash for ldu in ldus]
        return len(hashes) == len(set(hashes))
    
    def _check_page_refs(self, ldus: List[LDU]) -> bool:
        for ldu in ldus:
            bbox_pages = {bbox.page for bbox in ldu.bounding_boxes}
            if not bbox_pages.issubset(set(ldu.page_refs)):
                return False
        return True
    
    def get_validation_score(self, validation_results: Dict[str, bool]) -> float:
        if not validation_results:
            return 0.0
        passed = sum(1 for v in validation_results.values() if v)
        return passed / len(validation_results)
