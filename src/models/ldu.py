from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
import hashlib
from .extracted_document import BoundingBox


class ChunkType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    FIGURE = "figure"
    LIST = "list"
    HEADER = "header"
    FOOTER = "footer"


class LDU(BaseModel):
    """Logical Document Unit - semantically coherent chunk"""
    ldu_id: str = Field(..., min_length=1, description="Unique identifier for this LDU")
    content: str = Field(..., min_length=1, description="Extracted text content")
    chunk_type: ChunkType
    page_refs: List[int] = Field(..., min_length=1, description="Pages this LDU spans")
    bounding_boxes: List[BoundingBox] = Field(..., description="Spatial coordinates per page")
    parent_section: Optional[str] = Field(None, description="Parent section ID for hierarchy")
    token_count: int = Field(..., gt=0, description="Approximate token count")
    content_hash: str = Field(..., min_length=16, max_length=16, description="SHA-256 hash (16 chars)")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Relationships
    related_chunks: List[str] = Field(default_factory=list, description="IDs of related LDUs")
    
    @field_validator('page_refs')
    @classmethod
    def validate_page_refs(cls, v):
        """Ensure page refs are positive and sorted"""
        if not all(p >= 0 for p in v):
            raise ValueError("Page references must be non-negative")
        return sorted(set(v))  # Remove duplicates and sort
    
    @field_validator('bounding_boxes')
    @classmethod
    def validate_bboxes(cls, v):
        """Validate bounding box coordinates"""
        for bbox in v:
            if bbox.x1 <= bbox.x0 or bbox.y1 <= bbox.y0:
                raise ValueError("Invalid bounding box coordinates")
        return v
    
    @model_validator(mode='after')
    def validate_bbox_page_consistency(self):
        """Ensure bbox pages match page_refs"""
        bbox_pages = {bbox.page for bbox in self.bounding_boxes}
        if not bbox_pages.issubset(set(self.page_refs)):
            raise ValueError("Bounding box pages must be subset of page_refs")
        return self
    
    @staticmethod
    def generate_content_hash(content: str) -> str:
        """Generate SHA-256 hash of normalized content"""
        normalized = " ".join(content.split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    model_config = {"use_enum_values": True}
