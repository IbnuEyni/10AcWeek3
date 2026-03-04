from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from .extracted_document import BoundingBox


class SourceCitation(BaseModel):
    """Citation linking extracted content to source location"""
    doc_name: str = Field(..., min_length=1, description="Source document name")
    page: int = Field(..., ge=0, description="Page number (0-indexed)")
    bbox: Dict[str, float] = Field(..., description="Bounding box coordinates")
    content_hash: str = Field(..., min_length=16, max_length=16, description="Content hash for verification")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")
    extraction_strategy: str = Field(..., description="Strategy used: fast_text, layout_aware, vision_augmented")
    
    @field_validator('bbox')
    @classmethod
    def validate_bbox(cls, v):
        """Ensure bbox has required coordinates"""
        required = {'x0', 'y0', 'x1', 'y1'}
        if not required.issubset(v.keys()):
            raise ValueError(f"Bounding box must contain {required}")
        if v['x1'] < v['x0'] or v['y1'] < v['y0']:
            raise ValueError("Invalid bounding box coordinates")
        return v
    
    @field_validator('extraction_strategy')
    @classmethod
    def validate_strategy(cls, v):
        """Ensure valid extraction strategy"""
        valid = {'fast_text', 'layout_aware', 'vision_augmented'}
        if v not in valid:
            raise ValueError(f"Strategy must be one of {valid}")
        return v


class ProvenanceChain(BaseModel):
    """Chain of evidence linking claims to source documents"""
    claim: str = Field(..., min_length=1, description="Extracted claim or fact")
    sources: List[SourceCitation] = Field(..., min_length=1, description="Supporting source citations")
    verification_status: str = Field(..., description="verified, unverifiable, conflicting")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in claim")
    aggregated_bbox: Optional[BoundingBox] = Field(None, description="Aggregated bounding box from all sources")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('verification_status')
    @classmethod
    def validate_status(cls, v):
        """Ensure valid verification status"""
        valid = {'verified', 'unverifiable', 'conflicting'}
        if v not in valid:
            raise ValueError(f"Status must be one of {valid}")
        return v
    
    @model_validator(mode='after')
    def compute_aggregated_bbox(self):
        """Compute aggregated bounding box from sources if not provided"""
        if self.aggregated_bbox is None and self.sources:
            # Aggregate bounding boxes from all sources
            min_x0 = min(s.bbox['x0'] for s in self.sources)
            min_y0 = min(s.bbox['y0'] for s in self.sources)
            max_x1 = max(s.bbox['x1'] for s in self.sources)
            max_y1 = max(s.bbox['y1'] for s in self.sources)
            # Use page from first source
            page = self.sources[0].page
            
            self.aggregated_bbox = BoundingBox(
                x0=min_x0, y0=min_y0, x1=max_x1, y1=max_y1, page=page
            )
        return self
