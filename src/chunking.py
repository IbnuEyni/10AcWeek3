"""Semantic chunking engine for document segmentation"""

from typing import List, Dict
from .models.extracted_document import ExtractedDocument, TextBlock, Table
from .models.ldu import LogicalDocumentUnit
from .logging_config import get_logger

logger = get_logger("chunking")


class SemanticChunker:
    """Chunk documents into logical units preserving semantic boundaries"""
    
    def __init__(self, max_tokens: int = 512):
        self.max_tokens = max_tokens
    
    def chunk_document(self, doc: ExtractedDocument) -> List[LogicalDocumentUnit]:
        """
        Chunk document into semantic units
        
        Args:
            doc: Extracted document
            
        Returns:
            List of logical document units
        """
        logger.info(f"Chunking document {doc.doc_id} with {len(doc.text_blocks)} blocks")
        
        ldus = []
        current_chunk = []
        current_tokens = 0
        chunk_id = 0
        
        # Sort blocks by reading order
        sorted_blocks = sorted(doc.text_blocks, key=lambda b: b.reading_order)
        
        for block in sorted_blocks:
            block_tokens = self._estimate_tokens(block.content)
            
            # Check if adding block exceeds limit
            if current_tokens + block_tokens > self.max_tokens and current_chunk:
                # Create LDU from current chunk
                ldus.append(self._create_ldu(doc, current_chunk, chunk_id))
                chunk_id += 1
                current_chunk = []
                current_tokens = 0
            
            current_chunk.append(block)
            current_tokens += block_tokens
        
        # Add remaining chunk
        if current_chunk:
            ldus.append(self._create_ldu(doc, current_chunk, chunk_id))
        
        # Add tables as separate LDUs
        for idx, table in enumerate(doc.tables):
            ldus.append(LogicalDocumentUnit(
                ldu_id=f"{doc.doc_id}_table_{idx}",
                doc_id=doc.doc_id,
                content=self._table_to_text(table),
                content_type="table",
                page_numbers=[table.bbox.page],
                bboxes=[table.bbox],
                metadata={"table_index": idx, "rows": len(table.rows)}
            ))
        
        logger.info(f"Created {len(ldus)} logical document units")
        return ldus
    
    def _create_ldu(self, doc: ExtractedDocument, blocks: List[TextBlock], chunk_id: int) -> LogicalDocumentUnit:
        """Create LDU from text blocks"""
        content = "\n\n".join(b.content for b in blocks)
        pages = sorted(set(b.bbox.page for b in blocks))
        bboxes = [b.bbox for b in blocks]
        
        return LogicalDocumentUnit(
            ldu_id=f"{doc.doc_id}_chunk_{chunk_id}",
            doc_id=doc.doc_id,
            content=content,
            content_type="text",
            page_numbers=pages,
            bboxes=bboxes,
            metadata={"block_count": len(blocks), "chunk_index": chunk_id}
        )
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        return len(text.split()) // 0.75  # ~0.75 words per token
    
    def _table_to_text(self, table: Table) -> str:
        """Convert table to text representation"""
        lines = []
        for row in table.rows:
            lines.append(" | ".join(str(cell) for cell in row))
        return "\n".join(lines)
