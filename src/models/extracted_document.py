from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class BoundingBox(BaseModel):
    x0: float
    y0: float
    x1: float
    y1: float
    page: int


class ExtractionStrategy(str, Enum):
    FAST_TEXT = "fast_text"
    LAYOUT_AWARE = "layout_aware"
    VISION_AUGMENTED = "vision_augmented"


class EscalationReason(str, Enum):
    LOW_CONFIDENCE = "low_confidence"
    BUDGET_EXCEEDED = "budget_exceeded"
    STRATEGY_FAILED = "strategy_failed"
    MANUAL_OVERRIDE = "manual_override"


class ProcessingStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    ESCALATED = "escalated"


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


class EscalationAttempt(BaseModel):
    """Record of a single escalation attempt"""
    strategy: ExtractionStrategy
    confidence: float = Field(ge=0.0, le=1.0)
    reason: EscalationReason
    timestamp: str
    cost_estimate: float = Field(ge=0.0)
    status: ProcessingStatus


class EscalationHistory(BaseModel):
    """Complete escalation history for a document"""
    attempts: List[EscalationAttempt] = Field(default_factory=list)
    final_strategy: ExtractionStrategy
    total_attempts: int = Field(ge=0)
    escalation_triggered: bool = Field(default=False)
    final_status: ProcessingStatus = Field(default=ProcessingStatus.SUCCESS)
    

class RoutingSummary(BaseModel):
    """Structured summary of routing decisions and outcomes"""
    selected_strategy: ExtractionStrategy
    strategies_attempted: List[ExtractionStrategy]
    total_attempts: int = Field(ge=1)
    final_confidence: float = Field(ge=0.0, le=1.0)
    escalation_triggered: bool
    total_cost: float = Field(ge=0.0)
    processing_time_ms: int = Field(ge=0)
    status: ProcessingStatus
    
    model_config = {"use_enum_values": True}


class ExtractedDocument(BaseModel):
    doc_id: str
    filename: str
    text_blocks: List[TextBlock] = Field(default_factory=list)
    tables: List[Table] = Field(default_factory=list)
    figures: List[Figure] = Field(default_factory=list)
    reading_order: List[int] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extraction_strategy: ExtractionStrategy
    confidence_score: float = Field(ge=0.0, le=1.0)
    escalation_history: Optional[EscalationHistory] = Field(None, description="Complete escalation audit trail")
    routing_summary: Optional[RoutingSummary] = Field(None, description="Structured routing summary")
    
    model_config = {"use_enum_values": True}
