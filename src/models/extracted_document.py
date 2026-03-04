from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float
    page: int


class TextBlock(BaseModel):
    content: str
    bbox: BoundingBox
    font_info: Optional[Dict[str, Any]] = None
    reading_order: int


class Table(BaseModel):
    headers: List[str]
    rows: List[List[str]]
    bbox: BoundingBox
    caption: Optional[str] = None
    table_id: Optional[str] = None


class Figure(BaseModel):
    figure_id: str
    bbox: BoundingBox
    caption: Optional[str] = None
    image_path: Optional[str] = None
    page: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractedDocument(BaseModel):
    doc_id: str
    filename: str
    text_blocks: List[TextBlock] = Field(default_factory=list)
    tables: List[Table] = Field(default_factory=list)
    figures: List[Figure] = Field(default_factory=list)
    reading_order: List[int] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extraction_strategy: str
    confidence_score: float = Field(ge=0.0, le=1.0)
