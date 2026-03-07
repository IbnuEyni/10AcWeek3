"""Provenance models for source citation and audit trail"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    """Single source citation with spatial provenance"""
    document_name: str = Field(..., description="Source document filename")
    doc_id: str = Field(..., description="Document identifier")
    page_number: int = Field(..., ge=0, description="Page number (0-indexed)")
    bbox: Optional[dict] = Field(None, description="Bounding box coordinates {x0, y0, x1, y1}")
    content_hash: str = Field(..., description="Content hash for verification")
    excerpt: str = Field(..., description="Relevant text excerpt from source")
    ldu_id: Optional[str] = Field(None, description="Source LDU identifier")


class ProvenanceChain(BaseModel):
    """Complete provenance chain for an answer"""
    query: str = Field(..., description="Original user query")
    answer: str = Field(..., description="Generated answer")
    citations: List[SourceCitation] = Field(..., description="Source citations")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Answer confidence")
    retrieval_method: str = Field(..., description="pageindex | semantic_search | structured_query")
    verified: bool = Field(default=False, description="Whether sources were verified")
