"""Confidence metrics tracking for extraction strategies"""

import json
from pathlib import Path
from typing import Dict
from datetime import datetime

class ConfidenceTracker:
    """Track confidence metrics for extraction quality analysis"""
    
    def __init__(self, metrics_dir: str = ".refinery/metrics"):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.metrics_dir / "confidence_metrics.jsonl"
    
    def log_extraction(self, doc_id: str, strategy: str, confidence: float, 
                      signals: Dict[str, float], escalated: bool = False):
        """Log extraction confidence metrics"""
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "doc_id": doc_id,
            "strategy": strategy,
            "confidence": confidence,
            "signals": signals,
            "escalated": escalated
        }
        
        with open(self.metrics_file, 'a') as f:
            f.write(json.dumps(metric) + '\n')
    
    def get_strategy_stats(self, strategy: str = None) -> Dict:
        """Get confidence statistics by strategy"""
        if not self.metrics_file.exists():
            return {}
        
        metrics = []
        with open(self.metrics_file, 'r') as f:
            for line in f:
                m = json.loads(line)
                if strategy is None or m['strategy'] == strategy:
                    metrics.append(m)
        
        if not metrics:
            return {}
        
        confidences = [m['confidence'] for m in metrics]
        escalations = sum(1 for m in metrics if m['escalated'])
        
        return {
            "count": len(metrics),
            "avg_confidence": sum(confidences) / len(confidences),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "escalation_rate": escalations / len(metrics)
        }
