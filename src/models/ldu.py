from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import hashlib


class ChunkType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    FIGURE = "figure"
    LIST = "list"
    HEADER = "header"
    FOOTER = "footer"


class LDU(BaseModel):
    """Logical Document Unit - semantically coherent chunk"""
    ldu_id: str
    content: str
    chunk_type: ChunkType
    page_refs: List[int]
    bounding_boxes: List[Dict[str, float]]
    parent_section: Optional[str] = None
    token_count: int
    content_hash: str
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Relationships
    related_chunks: List[str] = Field(default_factory=list, description="IDs of related LDUs")
    
    @staticmethod
    def generate_content_hash(content: str) -> str:
        """Generate SHA-256 hash of normalized content"""
        normalized = " ".join(content.split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    model_config = {"use_enum_values": True}
