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
        
        Returns:
            Tuple of (ExtractedDocument, confidence_score)
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, profile: DocumentProfile) -> float:
        """Estimate cost in USD for extraction"""
        pass
    
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Name of the extraction strategy"""
        pass
