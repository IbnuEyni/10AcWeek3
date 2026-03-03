"""Input validation utilities"""

from pathlib import Path
from typing import Optional
import os
from .exceptions import DocumentValidationError, ConfigurationError


def validate_pdf_file(pdf_path: str) -> Path:
    """
    Validate PDF file exists and is readable
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Validated Path object
        
    Raises:
        DocumentValidationError: If file is invalid
    """
    path = Path(pdf_path)
    
    if not path.exists():
        raise DocumentValidationError(f"File not found: {pdf_path}")
    
    if not path.is_file():
        raise DocumentValidationError(f"Not a file: {pdf_path}")
    
    if path.suffix.lower() != '.pdf':
        raise DocumentValidationError(f"Not a PDF file: {pdf_path}")
    
    if path.stat().st_size == 0:
        raise DocumentValidationError(f"Empty file: {pdf_path}")
    
    if path.stat().st_size > 100 * 1024 * 1024:  # 100MB limit
        raise DocumentValidationError(f"File too large (>100MB): {pdf_path}")
    
    return path


def validate_api_key(key_name: str, required: bool = False) -> Optional[str]:
    """
    Validate API key from environment
    
    Args:
        key_name: Environment variable name
        required: Whether key is required
        
    Returns:
        API key or None
        
    Raises:
        ConfigurationError: If required key is missing
    """
    key = os.getenv(key_name)
    
    if required and not key:
        raise ConfigurationError(f"Required API key not found: {key_name}")
    
    if key and len(key) < 10:
        raise ConfigurationError(f"Invalid API key format: {key_name}")
    
    return key


def validate_confidence_score(score: float) -> float:
    """Validate confidence score is in valid range"""
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"Confidence score must be 0-1, got {score}")
    return score


def validate_cost(cost: float, max_cost: float) -> float:
    """Validate cost is within budget"""
    if cost < 0:
        raise ValueError(f"Cost cannot be negative: {cost}")
    if cost > max_cost:
        from .exceptions import BudgetExceededError
        raise BudgetExceededError(cost, max_cost)
    return cost
