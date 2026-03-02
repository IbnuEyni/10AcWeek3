from typing import List, Dict, Any
from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    doc_name: str
    page: int
    bbox: Dict[str, float]
    content_hash: str
    confidence: float = Field(ge=0.0, le=1.0)
    extraction_strategy: str


class ProvenanceChain(BaseModel):
    claim: str
    sources: List[SourceCitation]
    verification_status: str = Field(description="verified, unverifiable, conflicting")
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
