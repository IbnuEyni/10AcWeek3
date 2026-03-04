from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum
from .extracted_document import BoundingBox


class ExtractionStrategy(str, Enum):
    FAST_TEXT = "fast_text"
    LAYOUT_AWARE = "layout_aware"
    VISION_AUGMENTED = "vision_augmented"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIABLE = "unverifiable"
    CONFLICTING = "conflicting"


class SourceCitation(BaseModel):
    """Citation linking extracted content to source location"""
    doc_name: str = Field(..., min_length=1, description="Source document name")
    page: int = Field(..., ge=0, description="Page number (0-indexed)")
    bbox: BoundingBox = Field(..., description="Bounding box coordinates")
    content_hash: str = Field(..., min_length=16, max_length=16, description="Content hash for verification")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")
    extraction_strategy: ExtractionStrategy = Field(..., description="Strategy used for extraction")
    
    model_config = {"use_enum_values": True}


class ProvenanceChain(BaseModel):
    """Chain of evidence linking claims to source documents"""
    claim: str = Field(..., min_length=1, description="Extracted claim or fact")
    sources: List[SourceCitation] = Field(..., min_length=1, description="Supporting source citations")
    verification_status: VerificationStatus = Field(..., description="Verification status of the claim")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in claim")
    aggregated_bbox: Optional[BoundingBox] = Field(None, description="Aggregated bounding box from all sources")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    

    
    @model_validator(mode='after')
    def compute_aggregated_bbox(self):
        """Compute aggregated bounding box from sources if not provided"""
        if self.aggregated_bbox is None and self.sources:
            # Aggregate bounding boxes from all sources
            min_x0 = min(s.bbox.x0 for s in self.sources)
            min_y0 = min(s.bbox.y0 for s in self.sources)
            max_x1 = max(s.bbox.x1 for s in self.sources)
            max_y1 = max(s.bbox.y1 for s in self.sources)
            # Use page from first source
            page = self.sources[0].bbox.page
            
            self.aggregated_bbox = BoundingBox(
                x0=min_x0, y0=min_y0, x1=max_x1, y1=max_y1, page=page
            )
        return self
    
    model_config = {"use_enum_values": True}
