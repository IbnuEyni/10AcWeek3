from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class OriginType(str, Enum):
    NATIVE_DIGITAL = "native_digital"
    SCANNED_IMAGE = "scanned_image"
    MIXED = "mixed"
    FORM_FILLABLE = "form_fillable"


class LayoutComplexity(str, Enum):
    SINGLE_COLUMN = "single_column"
    MULTI_COLUMN = "multi_column"
    TABLE_HEAVY = "table_heavy"
    FIGURE_HEAVY = "figure_heavy"
    MIXED = "mixed"


class DomainHint(str, Enum):
    FINANCIAL = "financial"
    LEGAL = "legal"
    TECHNICAL = "technical"
    MEDICAL = "medical"
    GENERAL = "general"


class ExtractionCost(str, Enum):
    FAST_TEXT_SUFFICIENT = "fast_text_sufficient"
    NEEDS_LAYOUT_MODEL = "needs_layout_model"
    NEEDS_VISION_MODEL = "needs_vision_model"


class DocumentProfile(BaseModel):
    doc_id: str
    filename: str
    origin_type: OriginType
    layout_complexity: LayoutComplexity
    language: str = Field(default="en")
    language_confidence: float = Field(ge=0.0, le=1.0)
    domain_hint: DomainHint
    estimated_extraction_cost: ExtractionCost
    total_pages: int
    
    # Classification confidence scores
    origin_confidence: float = Field(ge=0.0, le=1.0, description="Confidence in origin type classification")
    layout_confidence: float = Field(ge=0.0, le=1.0, description="Confidence in layout complexity classification")
    domain_confidence: float = Field(ge=0.0, le=1.0, description="Confidence in domain classification")
    
    # Confidence metrics
    character_density: float = Field(description="Average chars per page area")
    image_ratio: float = Field(ge=0.0, le=1.0, description="Image area / total area")
    has_font_metadata: bool
    table_count_estimate: int = Field(ge=0)
    
    # Per-page analysis
    page_profiles: Optional[dict] = Field(default=None, description="Per-page origin type if mixed")
    
    model_config = {"use_enum_values": True}
