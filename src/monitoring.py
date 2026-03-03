"""Monitoring and metrics collection"""

import time
from typing import Dict, Optional, Callable
from functools import wraps
from dataclasses import dataclass, field
from datetime import datetime
from .logging_config import get_logger

logger = get_logger("monitoring")


@dataclass
class Metrics:
    """Metrics container"""
    total_documents: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    total_cost: float = 0.0
    total_processing_time: float = 0.0
    escalations: int = 0
    strategy_usage: Dict[str, int] = field(default_factory=dict)
    
    def record_extraction(self, strategy: str, cost: float, time_ms: float, 
                         success: bool, escalated: bool = False):
        """Record extraction metrics"""
        self.total_documents += 1
        if success:
            self.successful_extractions += 1
        else:
            self.failed_extractions += 1
        
        self.total_cost += cost
        self.total_processing_time += time_ms
        
        if escalated:
            self.escalations += 1
        
        self.strategy_usage[strategy] = self.strategy_usage.get(strategy, 0) + 1
    
    def get_summary(self) -> Dict:
        """Get metrics summary"""
        return {
            "total_documents": self.total_documents,
            "success_rate": self.successful_extractions / self.total_documents if self.total_documents > 0 else 0,
            "total_cost": round(self.total_cost, 2),
            "avg_cost_per_doc": round(self.total_cost / self.total_documents, 4) if self.total_documents > 0 else 0,
            "avg_processing_time_ms": round(self.total_processing_time / self.total_documents, 2) if self.total_documents > 0 else 0,
            "escalation_rate": self.escalations / self.total_documents if self.total_documents > 0 else 0,
            "strategy_usage": self.strategy_usage
        }


# Global metrics instance
metrics = Metrics()


def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = (time.time() - start) * 1000
            logger.debug(f"{func.__name__} completed in {elapsed:.2f}ms")
            return result
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            logger.error(f"{func.__name__} failed after {elapsed:.2f}ms: {e}")
            raise
    return wrapper


class PerformanceMonitor:
    """Monitor performance metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.checkpoints: Dict[str, float] = {}
    
    def checkpoint(self, name: str):
        """Record a checkpoint"""
        self.checkpoints[name] = time.time() - self.start_time
        logger.debug(f"Checkpoint '{name}': {self.checkpoints[name]:.3f}s")
    
    def get_elapsed(self, checkpoint: Optional[str] = None) -> float:
        """Get elapsed time since start or checkpoint"""
        if checkpoint and checkpoint in self.checkpoints:
            return time.time() - self.start_time - self.checkpoints[checkpoint]
        return time.time() - self.start_time
    
    def summary(self) -> Dict[str, float]:
        """Get timing summary"""
        return {
            "total_time": self.get_elapsed(),
            "checkpoints": self.checkpoints
        }
