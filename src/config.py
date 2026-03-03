"""Configuration management with environment-based settings"""

import os
from typing import Optional
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

load_dotenv()


class ExtractionConfig(BaseModel):
    """Extraction strategy configuration"""
    fast_text_cost_per_page: float = Field(default=0.001, ge=0)
    layout_aware_cost_per_page: float = Field(default=0.01, ge=0)
    vision_cost_per_page: float = Field(default=0.02, ge=0)
    max_cost_per_document: float = Field(default=1.0, ge=0)
    confidence_threshold: float = Field(default=0.7, ge=0, le=1.0)


class TriageConfig(BaseModel):
    """Triage agent configuration"""
    min_char_density: float = Field(default=0.01, ge=0)
    max_image_ratio: float = Field(default=0.5, ge=0, le=1.0)
    table_heavy_threshold: int = Field(default=10, ge=0)


class APIConfig(BaseModel):
    """API keys and endpoints"""
    gemini_api_key: Optional[str] = Field(default=None)
    openai_api_key: Optional[str] = Field(default=None)
    deepseek_api_key: Optional[str] = Field(default=None)
    groq_api_key: Optional[str] = Field(default=None)
    
    @field_validator('gemini_api_key', 'openai_api_key', 'deepseek_api_key', 'groq_api_key')
    @classmethod
    def validate_api_key(cls, v):
        if v and len(v) < 10:
            raise ValueError("API key too short")
        return v


class PathConfig(BaseModel):
    """File paths configuration"""
    profiles_dir: Path = Field(default=Path(".refinery/profiles"))
    pageindex_dir: Path = Field(default=Path(".refinery/pageindex"))
    ledger_path: Path = Field(default=Path(".refinery/extraction_ledger.jsonl"))
    log_dir: Optional[Path] = Field(default=None)
    
    def ensure_dirs(self):
        """Create directories if they don't exist"""
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.pageindex_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)


class Config(BaseModel):
    """Main configuration"""
    environment: str = Field(default="development")
    extraction: ExtractionConfig = Field(default_factory=ExtractionConfig)
    triage: TriageConfig = Field(default_factory=TriageConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    paths: PathConfig = Field(default_factory=PathConfig)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        return cls(
            environment=os.getenv("ENVIRONMENT", "development"),
            extraction=ExtractionConfig(
                max_cost_per_document=float(os.getenv("MAX_COST_PER_DOCUMENT", "1.0")),
                confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
            ),
            api=APIConfig(
                gemini_api_key=os.getenv("GEMINI_API_KEY"),
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
                groq_api_key=os.getenv("GROQ_API_KEY")
            )
        )
    
    def validate_config(self) -> bool:
        """Validate configuration on startup"""
        self.paths.ensure_dirs()
        return True


# Global config instance
config = Config.from_env()
