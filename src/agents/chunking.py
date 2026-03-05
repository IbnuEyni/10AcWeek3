"""Chunking agent for Stage 3: Semantic Chunking Engine"""

import json
from pathlib import Path
from typing import List

from rich.console import Console
from ..models.extracted_document import ExtractedDocument
from ..models.ldu import LDU
from ..chunking import SemanticChunker
from ..logging_config import get_logger

logger = get_logger("chunking_agent")
console = Console()

class ChunkingAgent:
    """Agent for semantic chunking of extracted documents"""
    
    def __init__(self, output_dir: str = ".refinery/ldus", config_path: str = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.chunker = SemanticChunker(config_path=config_path)
        logger.info(f"ChunkingAgent initialized with output_dir={output_dir}")
    
    def process_document(self, extracted_doc: ExtractedDocument, pdf_path: str) -> List[LDU]:
        """
        Process extracted document into LDUs
        
        Args:
            extracted_doc: Extracted document from Stage 2
            pdf_path: Path to original PDF for structure analysis
            
        Returns:
            List of LDUs
        """
        logger.info(f"Processing document: {extracted_doc.doc_id}")
        console.log(f"Creating LDUs for document: {extracted_doc.doc_id}", style="bold cyan")
        try:
            # Chunk document
            ldus = self.chunker.chunk_document(extracted_doc, pdf_path)
            
            # Save LDUs
            self._save_ldus(ldus, extracted_doc.doc_id)
            
            logger.info(f"Successfully created {len(ldus)} LDUs for {extracted_doc.doc_id}")
            return ldus
            
        except Exception as e:
            logger.error(f"Failed to process document {extracted_doc.doc_id}: {e}")
            raise
    
    def _save_ldus(self, ldus: List[LDU], doc_id: str):
        """Save LDUs to JSON file"""
        output_path = self.output_dir / f"{doc_id}_ldus.json"
        
        try:
            ldu_dicts = [ldu.model_dump() for ldu in ldus]
            with open(output_path, 'w') as f:
                json.dump(ldu_dicts, f, indent=2)
            logger.debug(f"Saved {len(ldus)} LDUs to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save LDUs: {e}")
            raise
    
    def load_ldus(self, doc_id: str) -> List[LDU]:
        """Load LDUs from JSON file"""
        input_path = self.output_dir / f"{doc_id}_ldus.json"
        
        if not input_path.exists():
            raise FileNotFoundError(f"LDUs not found for {doc_id}")
        
        try:
            with open(input_path, 'r') as f:
                ldu_dicts = json.load(f)
            ldus = [LDU(**ldu_dict) for ldu_dict in ldu_dicts]
            logger.info(f"Loaded {len(ldus)} LDUs for {doc_id}")
            return ldus
        except Exception as e:
            logger.error(f"Failed to load LDUs: {e}")
            raise
