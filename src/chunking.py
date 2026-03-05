"""Semantic chunking engine for document segmentation"""

import yaml
from typing import List, Dict, Optional, Any
from pathlib import Path
from .models.extracted_document import ExtractedDocument, TextBlock, Table, Figure, BoundingBox
from .models.ldu import LDU, ChunkType
from .logging_config import get_logger

logger = get_logger("chunking")


class SemanticChunker:
    """Chunk documents into logical units preserving semantic boundaries"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "rubric" / "extraction_rules.yaml"
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
            self.chunking_config = config['chunking']
        
        self.max_tokens = self.chunking_config['max_tokens']
        self.overlap_tokens = self.chunking_config['overlap_tokens']
        self.rules = {rule['name']: rule for rule in self.chunking_config['rules']}
        
        logger.info(f"SemanticChunker initialized: max_tokens={self.max_tokens}")
    
    def chunk_document(self, doc: ExtractedDocument, pdf_path: str = None) -> List[LDU]:
        """
        Chunk document into semantic units with 5 rules (without Docling)
        
        Args:
            doc: Extracted document
            pdf_path: Path to PDF (unused, kept for API compatibility)
            
        Returns:
            List of logical document units
        """
        logger.info(f"Chunking document {doc.doc_id} with {len(doc.text_blocks)} blocks")
        
        ldus = []
        
        # Rule 1: Table Integrity - tables never split
        for idx, table in enumerate(doc.tables):
            ldu = self._create_table_ldu(table, doc.doc_id, idx)
            ldus.append(ldu)
        
        # Rule 2: Figure-Caption Binding - figures with captions
        for idx, figure in enumerate(doc.figures):
            ldu = self._create_figure_ldu(figure, doc.doc_id, idx)
            ldus.append(ldu)
        
        # Rule 3, 4 & 5: Text blocks with smart chunking
        text_ldus = self._chunk_text_blocks(doc.text_blocks, doc.doc_id)
        ldus.extend(text_ldus)
        
        logger.info(f"Created {len(ldus)} logical document units")
        return ldus
    
    def _create_table_ldu(self, table: Table, doc_id: str, idx: int) -> LDU:
        """Rule 1: Table integrity - never split tables"""
        content = self._table_to_text(table)
        
        return LDU(
            ldu_id=f"{doc_id}_table_{idx}",
            content=content,
            chunk_type=ChunkType.TABLE,
            page_refs=[table.bbox.page],
            bounding_boxes=[table.bbox],
            parent_section=None,
            token_count=self._estimate_tokens(content),
            content_hash=LDU.generate_content_hash(content),
            metadata={'table_id': table.table_id, 'rows': len(table.rows), 'caption': table.caption}
        )
    
    def _create_figure_ldu(self, figure: Figure, doc_id: str, idx: int) -> LDU:
        """Rule 2: Figure-caption binding"""
        content = f"Figure {figure.figure_id}"
        if figure.caption:
            content += f": {figure.caption}"
        
        return LDU(
            ldu_id=f"{doc_id}_figure_{idx}",
            content=content,
            chunk_type=ChunkType.FIGURE,
            page_refs=[figure.page],
            bounding_boxes=[figure.bbox],
            parent_section=None,
            token_count=self._estimate_tokens(content),
            content_hash=LDU.generate_content_hash(content),
            metadata={'figure_id': figure.figure_id, 'image_path': str(figure.image_path) if figure.image_path else None}
        )
    

    def _chunk_text_blocks(self, blocks: List[TextBlock], doc_id: str) -> List[LDU]:
        """Rule 3, 4 & 5: Smart text chunking with overlap"""
        ldus = []
        sorted_blocks = sorted(blocks, key=lambda b: b.reading_order)
        
        current_chunk = []
        current_tokens = 0
        chunk_id = 0
        
        for block in sorted_blocks:
            block_tokens = self._estimate_tokens(block.content)
            
            if current_tokens + block_tokens > self.max_tokens and current_chunk:
                ldu = self._create_text_ldu(current_chunk, doc_id, chunk_id)
                ldus.append(ldu)
                chunk_id += 1
                
                # Add overlap
                if self.overlap_tokens > 0 and current_chunk:
                    overlap_content = current_chunk[-1].content[-self.overlap_tokens:]
                    current_chunk = [current_chunk[-1]]
                    current_tokens = self._estimate_tokens(overlap_content)
                else:
                    current_chunk = []
                    current_tokens = 0
            
            current_chunk.append(block)
            current_tokens += block_tokens
        
        if current_chunk:
            ldu = self._create_text_ldu(current_chunk, doc_id, chunk_id)
            ldus.append(ldu)
        
        return ldus
    
    def _create_text_ldu(self, blocks: List[TextBlock], doc_id: str, chunk_id: int) -> LDU:
        """Create text LDU"""
        content = "\n\n".join(b.content for b in blocks)
        pages = sorted(set(b.bbox.page for b in blocks))
        bboxes = [b.bbox for b in blocks]
        
        return LDU(
            ldu_id=f"{doc_id}_text_{chunk_id}",
            content=content,
            chunk_type=ChunkType.TEXT,
            page_refs=pages,
            bounding_boxes=bboxes,
            parent_section=None,
            token_count=self._estimate_tokens(content),
            content_hash=LDU.generate_content_hash(content),
            metadata={'block_count': len(blocks), 'chunk_index': chunk_id}
        )
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        return int(len(text.split()) / 0.75)  # ~0.75 words per token
    
    def _table_to_text(self, table: Table) -> str:
        """Convert table to text representation"""
        lines = []
        if table.headers:
            lines.append(" | ".join(str(h) for h in table.headers))
            lines.append("-" * 50)
        for row in table.rows:
            lines.append(" | ".join(str(cell) for cell in row))
        return "\n".join(lines)
