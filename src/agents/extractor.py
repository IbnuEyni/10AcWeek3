import json
import yaml
from pathlib import Path
from typing import Tuple
from datetime import datetime
from ..models.document_profile import DocumentProfile, ExtractionCost
from ..models.extracted_document import ExtractedDocument, EscalationHistory, EscalationAttempt
from ..strategies import FastTextExtractor, LayoutExtractor, VisionExtractor
from ..logging_config import get_logger
from ..monitoring import metrics, PerformanceMonitor
from ..config import config

logger = get_logger("extractor")


class ExtractionRouter:
    """Routes documents to appropriate extraction strategy with escalation"""
    
    def __init__(self, ledger_path: str = None, config_path: str = None):
        self.ledger_path = Path(ledger_path or config.paths.ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load escalation config
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "rubric" / "extraction_rules.yaml"
        
        with open(config_path) as f:
            self.escalation_config = yaml.safe_load(f)['escalation']
        
        self.CONFIDENCE_THRESHOLD = self.escalation_config['confidence_threshold']
        self.MAX_ATTEMPTS = self.escalation_config['max_attempts']
        self.ESCALATION_ENABLED = self.escalation_config['enabled']
        
        self.fast_extractor = FastTextExtractor()
        self.layout_extractor = LayoutExtractor()
        self.vision_extractor = VisionExtractor()
        
        logger.info(f"ExtractionRouter initialized with threshold={self.CONFIDENCE_THRESHOLD}")
    
    def extract(self, pdf_path: str, profile: DocumentProfile) -> ExtractedDocument:
        """Route to appropriate strategy with automatic escalation"""
        monitor = PerformanceMonitor()
        logger.info(f"Starting extraction for {profile.doc_id}")
        
        # Initialize escalation tracking
        escalation_history = EscalationHistory(
            attempts=[],
            final_strategy="",
            total_attempts=0,
            escalation_triggered=False
        )
        
        # Select initial strategy
        strategy = self._select_strategy(profile)
        monitor.checkpoint("strategy_selected")
        logger.debug(f"Selected strategy: {strategy.strategy_name}")
        
        # Attempt extraction
        try:
            extracted_doc, confidence = strategy.extract(pdf_path, profile)
            monitor.checkpoint("extraction_complete")
            
            # Record initial attempt
            escalation_history.attempts.append(EscalationAttempt(
                strategy=strategy.strategy_name,
                confidence=confidence,
                reason="initial_strategy",
                timestamp=datetime.now().isoformat(),
                cost_estimate=strategy.estimate_cost(profile)
            ))
            escalation_history.total_attempts = 1
            
            # Escalation guard
            if confidence < self.CONFIDENCE_THRESHOLD:
                logger.warning(f"Low confidence ({confidence:.2f}), escalating...")
                extracted_doc, confidence, escalation_history = self._escalate_with_history(
                    pdf_path, profile, strategy, escalation_history
                )
                monitor.checkpoint("escalation_complete")
            
            escalation_history.final_strategy = strategy.strategy_name
            extracted_doc.escalation_history = escalation_history
            
            # Calculate metrics
            processing_time = monitor.get_elapsed() * 1000
            cost_estimate = strategy.estimate_cost(profile)
            
            # Record metrics
            metrics.record_extraction(
                strategy=strategy.strategy_name,
                cost=cost_estimate,
                time_ms=processing_time,
                success=True,
                escalated=escalation_history.escalation_triggered
            )
            
            # Log to ledger
            self._log_extraction(
                profile=profile,
                strategy_used=strategy.strategy_name,
                confidence_score=confidence,
                cost_estimate=cost_estimate,
                processing_time_ms=processing_time,
                escalation_triggered=escalation_history.escalation_triggered
            )
            
            logger.info(f"Extraction complete: {profile.doc_id} | {strategy.strategy_name} | "
                       f"confidence={confidence:.2f} | time={processing_time:.0f}ms")
            
            return extracted_doc
            
        except Exception as e:
            processing_time = monitor.get_elapsed() * 1000
            metrics.record_extraction(
                strategy=strategy.strategy_name,
                cost=0,
                time_ms=processing_time,
                success=False
            )
            logger.error(f"Extraction failed for {profile.doc_id}: {e}")
            raise
    
    def _select_strategy(self, profile: DocumentProfile):
        """Select extraction strategy based on profile"""
        if profile.estimated_extraction_cost == ExtractionCost.FAST_TEXT_SUFFICIENT:
            return self.fast_extractor
        elif profile.estimated_extraction_cost == ExtractionCost.NEEDS_LAYOUT_MODEL:
            return self.layout_extractor
        else:  # NEEDS_VISION_MODEL
            return self.vision_extractor
    
    def _escalate_with_history(self, pdf_path: str, profile: DocumentProfile, 
                              current_strategy, history: EscalationHistory) -> tuple:
        """Escalate with complete history tracking"""
        if not self.ESCALATION_ENABLED:
            logger.warning("Escalation disabled in config")
            return current_strategy.extract(pdf_path, profile) + (history,)
        
        history.escalation_triggered = True
        
        # Get escalation path from config
        strategy_order = self.escalation_config['strategy_order']
        current_idx = strategy_order.index(current_strategy.strategy_name)
        
        # Check if we can escalate further
        if current_idx >= len(strategy_order) - 1:
            logger.warning(f"Already at highest strategy: {current_strategy.strategy_name}")
            return current_strategy.extract(pdf_path, profile) + (history,)
        
        # Escalate to next strategy
        next_strategy_name = strategy_order[current_idx + 1]
        logger.info(f"Escalating from {current_strategy.strategy_name} to {next_strategy_name}")
        
        if next_strategy_name == "layout_aware":
            next_strategy = self.layout_extractor
        elif next_strategy_name == "vision_augmented":
            next_strategy = self.vision_extractor
        else:
            next_strategy = self.fast_extractor
        
        extracted_doc, confidence = next_strategy.extract(pdf_path, profile)
        
        # Record escalation attempt
        history.attempts.append(EscalationAttempt(
            strategy=next_strategy_name,
            confidence=confidence,
            reason=f"escalated_from_{current_strategy.strategy_name}_low_confidence",
            timestamp=datetime.now().isoformat(),
            cost_estimate=next_strategy.estimate_cost(profile)
        ))
        history.total_attempts += 1
        history.final_strategy = next_strategy_name
        
        return extracted_doc, confidence, history
    
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
