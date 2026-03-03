"""Base extraction strategy interface with complete type safety"""

from abc import ABC, abstractmethod
from typing import Tuple
from ..models.extracted_document import ExtractedDocument
from ..models.document_profile import DocumentProfile


class BaseExtractor(ABC):
    """Base class for all extraction strategies"""
    
    @abstractmethod
    def extract(self, pdf_path: str, profile: DocumentProfile) -> Tuple[ExtractedDocument, float]:
        """
        Extract content from PDF
        
        Args:
            pdf_path: Path to PDF file
            profile: Document profile from triage
            
        Returns:
            Tuple of (ExtractedDocument, confidence_score)
            
        Raises:
            ExtractionError: If extraction fails
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, profile: DocumentProfile) -> float:
        """
        Estimate cost in USD for extraction
        
        Args:
            profile: Document profile
            
        Returns:
            Estimated cost in USD
        """
        pass
    
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Name of the extraction strategy"""
        pass
