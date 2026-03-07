"""Decision boundary tuner for VLM vs OCR strategy selection"""

import json
from pathlib import Path
from typing import Dict, List

class DecisionBoundaryTuner:
    """Tune and track VLM vs OCR decision boundaries"""
    
    def __init__(self, config_path: str = ".refinery/decision_boundaries.json"):
        self.config_path = Path(config_path)
        self.boundaries = self._load_boundaries()
    
    def _load_boundaries(self) -> Dict:
        """Load current decision boundaries"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        
        return {
            "char_density_threshold": 0.01,
            "image_ratio_threshold": 0.8,
            "table_count_threshold": 10,
            "confidence_threshold": 0.7,
            "cost_per_page": {
                "fast_text": 0.001,
                "layout_aware": 0.01,
                "vision": 0.02
            }
        }
    
    def save_boundaries(self):
        """Save updated boundaries"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.boundaries, f, indent=2)
    
    def log_decision(self, doc_id: str, profile: Dict, strategy_used: str, 
                    confidence: float, cost: float, success: bool):
        """Log strategy decision for A/B testing"""
        decision_log = self.config_path.parent / "decision_log.jsonl"
        
        log_entry = {
            "doc_id": doc_id,
            "char_density": profile.get("character_density"),
            "image_ratio": profile.get("image_ratio"),
            "table_count": profile.get("table_count", 0),
            "strategy_used": strategy_used,
            "confidence": confidence,
            "cost": cost,
            "success": success
        }
        
        with open(decision_log, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def analyze_decisions(self) -> Dict:
        """Analyze decision quality and suggest boundary adjustments"""
        decision_log = self.config_path.parent / "decision_log.jsonl"
        if not decision_log.exists():
            return {}
        
        decisions = []
        with open(decision_log, 'r') as f:
            for line in f:
                decisions.append(json.loads(line))
        
        if not decisions:
            return {}
        
        # Analyze by strategy
        by_strategy = {}
        for d in decisions:
            strategy = d['strategy_used']
            if strategy not in by_strategy:
                by_strategy[strategy] = []
            by_strategy[strategy].append(d)
        
        analysis = {}
        for strategy, strat_decisions in by_strategy.items():
            avg_confidence = sum(d['confidence'] for d in strat_decisions) / len(strat_decisions)
            avg_cost = sum(d['cost'] for d in strat_decisions) / len(strat_decisions)
            success_rate = sum(1 for d in strat_decisions if d['success']) / len(strat_decisions)
            
            analysis[strategy] = {
                "count": len(strat_decisions),
                "avg_confidence": avg_confidence,
                "avg_cost": avg_cost,
                "success_rate": success_rate,
                "cost_per_success": avg_cost / success_rate if success_rate > 0 else float('inf')
            }
        
        return analysis
    
    def suggest_adjustments(self) -> Dict[str, float]:
        """Suggest boundary adjustments based on logged decisions"""
        analysis = self.analyze_decisions()
        if not analysis:
            return {}
        
        suggestions = {}
        
        # If fast_text has low success rate, lower char_density threshold
        if 'fast_text' in analysis and analysis['fast_text']['success_rate'] < 0.7:
            suggestions['char_density_threshold'] = self.boundaries['char_density_threshold'] * 1.2
        
        # If vision is overused, raise image_ratio threshold
        if 'vision' in analysis and analysis['vision']['count'] > sum(a['count'] for a in analysis.values()) * 0.3:
            suggestions['image_ratio_threshold'] = self.boundaries['image_ratio_threshold'] * 1.1
        
        return suggestions
