import json
from pathlib import Path
from typing import Tuple
from datetime import datetime
from ..models.document_profile import DocumentProfile, ExtractionCost
from ..models.extracted_document import ExtractedDocument
from ..strategies import FastTextExtractor, LayoutExtractor, VisionExtractor


class ExtractionRouter:
    """Routes documents to appropriate extraction strategy with escalation"""
    
    CONFIDENCE_THRESHOLD = 0.7
    
    def __init__(self, ledger_path: str = ".refinery/extraction_ledger.jsonl"):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.fast_extractor = FastTextExtractor()
        self.layout_extractor = LayoutExtractor()
        self.vision_extractor = VisionExtractor()
    
    def extract(self, pdf_path: str, profile: DocumentProfile) -> ExtractedDocument:
        """Route to appropriate strategy with automatic escalation"""
        start_time = datetime.now()
        
        # Select initial strategy based on profile
        strategy = self._select_strategy(profile)
        
        # Attempt extraction
        extracted_doc, confidence = strategy.extract(pdf_path, profile)
        
        # Escalation guard
        if confidence < self.CONFIDENCE_THRESHOLD:
            print(f"Low confidence ({confidence:.2f}), escalating...")
            extracted_doc, confidence = self._escalate(pdf_path, profile, strategy)
        
        # Calculate metrics
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        cost_estimate = strategy.estimate_cost(profile)
        
        # Log to ledger
        self._log_extraction(
            profile=profile,
            strategy_used=strategy.strategy_name,
            confidence_score=confidence,
            cost_estimate=cost_estimate,
            processing_time_ms=processing_time,
            escalation_triggered=confidence < self.CONFIDENCE_THRESHOLD
        )
        
        return extracted_doc
    
    def _select_strategy(self, profile: DocumentProfile):
        """Select extraction strategy based on profile"""
        if profile.estimated_extraction_cost == ExtractionCost.FAST_TEXT_SUFFICIENT:
            return self.fast_extractor
        elif profile.estimated_extraction_cost == ExtractionCost.NEEDS_LAYOUT_MODEL:
            return self.layout_extractor
        else:  # NEEDS_VISION_MODEL
            return self.vision_extractor
    
    def _escalate(self, pdf_path: str, profile: DocumentProfile, current_strategy) -> Tuple[ExtractedDocument, float]:
        """Escalate to more powerful strategy"""
        if current_strategy.strategy_name == "fast_text":
            print("Escalating to layout-aware extraction...")
            return self.layout_extractor.extract(pdf_path, profile)
        elif current_strategy.strategy_name == "layout_aware":
            print("Escalating to vision-augmented extraction...")
            return self.vision_extractor.extract(pdf_path, profile)
        else:
            # Already at highest level
            return current_strategy.extract(pdf_path, profile)
    
    def _log_extraction(
        self, profile: DocumentProfile, strategy_used: str,
        confidence_score: float, cost_estimate: float,
        processing_time_ms: float, escalation_triggered: bool
    ):
        """Log extraction to ledger"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "doc_id": profile.doc_id,
            "filename": profile.filename,
            "strategy_used": strategy_used,
            "confidence_score": round(confidence_score, 3),
            "cost_estimate": round(cost_estimate, 4),
            "processing_time_ms": round(processing_time_ms, 2),
            "escalation_triggered": escalation_triggered,
            "origin_type": profile.origin_type,
            "layout_complexity": profile.layout_complexity
        }
        
        with open(self.ledger_path, 'a') as f:
            f.write(json.dumps(entry) + '\n')
