"""Document classification and profiling agent with enterprise-level quality"""

import json
import yaml
from pathlib import Path
from typing import Dict, Optional, List
from ..models.document_profile import (
    DocumentProfile, OriginType, LayoutComplexity, 
    DomainHint, ExtractionCost
)
from ..utils.pdf_analyzer import PDFAnalyzer
from ..logging_config import get_logger
from ..exceptions import TriageError, DocumentValidationError
from ..validators import validate_pdf_file

logger = get_logger("triage")


class TriageAgent:
    """Document classification and profiling agent"""
    
    def __init__(self, output_dir: str = ".refinery/profiles", config_path: str = None):
        """
        Initialize triage agent
        
        Args:
            output_dir: Directory to save document profiles
            config_path: Path to extraction_rules.yaml config file
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load config
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "rubric" / "extraction_rules.yaml"
        
        with open(config_path) as f:
            config_data = yaml.safe_load(f)
            self.domain_keywords = config_data['domain_keywords']
            self.origin_config = config_data['origin_detection']
            self.layout_config = config_data['layout']
        
        self.analyzer = PDFAnalyzer(self.origin_config, self.layout_config)
        
        logger.info(f"Triage agent initialized with output_dir={output_dir}")
        logger.debug(f"Loaded domain keywords for {len(self.domain_keywords)} domains")
    
    def profile_document(self, pdf_path: str) -> DocumentProfile:
        """
        Generate complete document profile
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            DocumentProfile with classification results
            
        Raises:
            DocumentValidationError: If PDF is invalid
            TriageError: If profiling fails
        """
        logger.info(f"Profiling document: {pdf_path}")
        
        try:
            # Validate input
            path = validate_pdf_file(pdf_path)
            doc_id = path.stem
            
            # Analyze PDF
            metrics = self.analyzer.analyze_document(str(path))
            
            # Classify origin type
            origin_type, origin_confidence = self.analyzer.detect_origin_type(metrics)
            logger.debug(f"Origin type: {origin_type} (confidence: {origin_confidence:.2f})")
            
            # Classify layout complexity
            layout_complexity, layout_confidence = self.analyzer.detect_layout_complexity(metrics, str(path))
            logger.debug(f"Layout complexity: {layout_complexity} (confidence: {layout_confidence:.2f})")
            
            # Detect domain
            domain_hint, domain_confidence = self._detect_domain(str(path))
            logger.debug(f"Domain hint: {domain_hint} (confidence: {domain_confidence:.2f})")
            
            # Estimate extraction cost
            extraction_cost = self._estimate_extraction_cost(
                origin_type, layout_complexity, metrics
            )
            logger.debug(f"Extraction cost estimate: {extraction_cost}")
            
            # Create profile
            profile = DocumentProfile(
                doc_id=doc_id,
                filename=path.name,
                origin_type=OriginType(origin_type),
                layout_complexity=LayoutComplexity(layout_complexity),
                language="en",
                language_confidence=0.95,
                domain_hint=domain_hint,
                estimated_extraction_cost=extraction_cost,
                total_pages=metrics["total_pages"],
                origin_confidence=origin_confidence,
                layout_confidence=layout_confidence,
                domain_confidence=domain_confidence,
                character_density=metrics["character_density"],
                image_ratio=metrics["image_ratio"],
                has_font_metadata=metrics["has_font_metadata"],
                table_count_estimate=metrics["table_count_estimate"]
            )
            
            # Save profile
            self._save_profile(profile)
            
            logger.info(f"Profile complete: {doc_id} | {origin_type} | {layout_complexity} | {domain_hint}")
            
            return profile
            
        except (DocumentValidationError, TriageError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error profiling document: {e}", exc_info=True)
            raise TriageError(f"Failed to profile document: {e}")
    
    def _detect_domain(self, pdf_path: str) -> tuple[DomainHint, float]:
        """
        Keyword-based domain detection using config
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (domain classification, confidence)
        """
        filename_lower = Path(pdf_path).name.lower()
        
        # Check each domain's keywords from config
        for domain, keywords in self.domain_keywords.items():
            matches = sum(1 for kw in keywords if kw.lower() in filename_lower)
            if matches > 0:
                # Map config domain names to DomainHint enum
                domain_map = {
                    'financial': DomainHint.FINANCIAL,
                    'legal': DomainHint.LEGAL,
                    'technical': DomainHint.TECHNICAL,
                    'medical': DomainHint.MEDICAL,
                    'general': DomainHint.GENERAL
                }
                confidence = min(0.9, 0.5 + (matches * 0.1))  # 0.6-0.9 based on matches
                return domain_map.get(domain, DomainHint.GENERAL), confidence
        
        return DomainHint.GENERAL, 0.5
    
    def _estimate_extraction_cost(
        self, origin_type: str, layout_complexity: str, metrics: Dict
    ) -> ExtractionCost:
        """
        Estimate which extraction strategy is needed
        
        Args:
            origin_type: Document origin classification
            layout_complexity: Layout complexity classification
            metrics: Analysis metrics
            
        Returns:
            Extraction cost estimate
        """
        if origin_type == "scanned_image":
            return ExtractionCost.NEEDS_VISION_MODEL
        elif layout_complexity in ["table_heavy", "multi_column"]:
            return ExtractionCost.NEEDS_LAYOUT_MODEL
        elif origin_type == "native_digital" and layout_complexity == "single_column":
            return ExtractionCost.FAST_TEXT_SUFFICIENT
        else:
            return ExtractionCost.NEEDS_LAYOUT_MODEL
    
    def _save_profile(self, profile: DocumentProfile) -> None:
        """
        Save profile to JSON
        
        Args:
            profile: Document profile to save
        """
        output_path = self.output_dir / f"{profile.doc_id}.json"
        try:
            with open(output_path, 'w') as f:
                json.dump(profile.model_dump(), f, indent=2)
            logger.debug(f"Profile saved: {output_path}")
        except Exception as e:
            logger.error(f"Failed to save profile: {e}")
            raise TriageError(f"Failed to save profile: {e}")
