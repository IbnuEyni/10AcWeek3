"""Resilience patterns: circuit breaker, retry logic, rate limiting"""

import time
from typing import Callable, Optional, Any
from functools import wraps
from enum import Enum
from .logging_config import get_logger
from .exceptions import APIError

logger = get_logger("resilience")


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker pattern for API calls"""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker"""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker: transitioning to HALF_OPEN")
            else:
                raise APIError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info("Circuit breaker: transitioning to CLOSED")
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker: transitioning to OPEN after {self.failure_count} failures")


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, 
                       max_delay: float = 10.0, exponential: bool = True):
    """Retry decorator with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"{func.__name__} failed after {max_retries} retries")
                        raise
                    
                    if exponential:
                        delay = min(base_delay * (2 ** (retries - 1)), max_delay)
                    else:
                        delay = base_delay
                    
                    logger.warning(f"{func.__name__} failed (attempt {retries}/{max_retries}), "
                                 f"retrying in {delay:.1f}s: {e}")
                    time.sleep(delay)
            
            return None
        return wrapper
    return decorator


class RateLimiter:
    """Simple rate limiter"""
    
    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls: list = []
    
    def acquire(self) -> bool:
        """Try to acquire a slot"""
        now = time.time()
        
        # Remove old calls outside time window
        self.calls = [t for t in self.calls if now - t < self.time_window]
        
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False
    
    def wait_if_needed(self):
        """Wait if rate limit is exceeded"""
        while not self.acquire():
            sleep_time = 0.1
            logger.debug(f"Rate limit reached, waiting {sleep_time}s")
            time.sleep(sleep_time)


class TimeoutManager:
    """Manage operation timeouts"""
    
    def __init__(self, timeout: float):
        self.timeout = timeout
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def check_timeout(self):
        """Check if timeout exceeded"""
        if self.start_time and time.time() - self.start_time > self.timeout:
            raise TimeoutError(f"Operation exceeded timeout of {self.timeout}s")
    
    def remaining(self) -> float:
        """Get remaining time"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            return max(0, self.timeout - elapsed)
        return self.timeout
