import json
from pathlib import Path
from typing import Dict
from ..models.document_profile import (
    DocumentProfile, OriginType, LayoutComplexity, 
    DomainHint, ExtractionCost
)
from ..utils.pdf_analyzer import PDFAnalyzer


class TriageAgent:
    """Document classification and profiling agent"""
    
    FINANCIAL_KEYWORDS = ["revenue", "financial", "balance sheet", "income", "audit", "fiscal", "annual", "report", "cbe", "bank"]
    LEGAL_KEYWORDS = ["contract", "agreement", "legal", "court", "law", "regulation"]
    TECHNICAL_KEYWORDS = ["technical", "specification", "engineering", "system", "architecture"]
    MEDICAL_KEYWORDS = ["medical", "patient", "clinical", "diagnosis", "pharmaceutical"]
    
    def __init__(self, output_dir: str = ".refinery/profiles"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.analyzer = PDFAnalyzer()
    
    def profile_document(self, pdf_path: str) -> DocumentProfile:
        """Generate complete document profile"""
        pdf_path = Path(pdf_path)
        doc_id = pdf_path.stem
        
        # Analyze PDF
        metrics = self.analyzer.analyze_document(str(pdf_path))
        
        # Classify origin type
        origin_type, origin_confidence = self.analyzer.detect_origin_type(metrics)
        
        # Classify layout complexity
        layout_complexity = self.analyzer.detect_layout_complexity(metrics)
        
        # Detect domain
        domain_hint = self._detect_domain(str(pdf_path))
        
        # Estimate extraction cost
        extraction_cost = self._estimate_extraction_cost(
            origin_type, layout_complexity, metrics
        )
        
        profile = DocumentProfile(
            doc_id=doc_id,
            filename=pdf_path.name,
            origin_type=OriginType(origin_type),
            layout_complexity=LayoutComplexity(layout_complexity),
            language="en",
            language_confidence=0.95,
            domain_hint=domain_hint,
            estimated_extraction_cost=extraction_cost,
            total_pages=metrics["total_pages"],
            character_density=metrics["character_density"],
            image_ratio=metrics["image_ratio"],
            has_font_metadata=metrics["has_font_metadata"],
            table_count_estimate=metrics["table_count_estimate"]
        )
        
        # Save profile
        self._save_profile(profile)
        
        return profile
    
    def _detect_domain(self, pdf_path: str) -> DomainHint:
        """Simple keyword-based domain detection"""
        filename_lower = Path(pdf_path).name.lower()
        
        if any(kw in filename_lower for kw in self.FINANCIAL_KEYWORDS):
            return DomainHint.FINANCIAL
        elif any(kw in filename_lower for kw in self.LEGAL_KEYWORDS):
            return DomainHint.LEGAL
        elif any(kw in filename_lower for kw in self.TECHNICAL_KEYWORDS):
            return DomainHint.TECHNICAL
        elif any(kw in filename_lower for kw in self.MEDICAL_KEYWORDS):
            return DomainHint.MEDICAL
        else:
            return DomainHint.GENERAL
    
    def _estimate_extraction_cost(
        self, origin_type: str, layout_complexity: str, metrics: Dict
    ) -> ExtractionCost:
        """Estimate which extraction strategy is needed"""
        if origin_type == "scanned_image":
            return ExtractionCost.NEEDS_VISION_MODEL
        elif layout_complexity in ["table_heavy", "multi_column"]:
            return ExtractionCost.NEEDS_LAYOUT_MODEL
        elif origin_type == "native_digital" and layout_complexity == "single_column":
            return ExtractionCost.FAST_TEXT_SUFFICIENT
        else:
            return ExtractionCost.NEEDS_LAYOUT_MODEL
    
    def _save_profile(self, profile: DocumentProfile):
        """Save profile to JSON"""
        output_path = self.output_dir / f"{profile.doc_id}.json"
        with open(output_path, 'w') as f:
            json.dump(profile.model_dump(), f, indent=2)
