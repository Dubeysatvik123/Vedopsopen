"""
Resilience patterns and utilities for VedOps
"""

import time
import threading
import logging
from typing import Callable, Any, Dict, Optional
from functools import wraps
from enum import Enum
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open" 
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Circuit breaker pattern implementation for fault tolerance"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, 
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        self.lock = threading.Lock()
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.lock:
                if self.state == CircuitBreakerState.OPEN:
                    if self._should_attempt_reset():
                        self.state = CircuitBreakerState.HALF_OPEN
                        logger.info(f"Circuit breaker for {func.__name__} moved to HALF_OPEN")
                    else:
                        raise Exception(f"Circuit breaker OPEN for {func.__name__}")
                
                try:
                    result = func(*args, **kwargs)
                    self._on_success()
                    return result
                    
                except self.expected_exception as e:
                    self._on_failure()
                    raise
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful execution"""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
        logger.debug("Circuit breaker reset to CLOSED")
    
    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker OPENED after {self.failure_count} failures")

class RetryPolicy:
    """Configurable retry policy with exponential backoff"""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, exponential_base: float = 2.0,
                 jitter: bool = True):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(self.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == self.max_attempts - 1:
                        logger.error(f"Function {func.__name__} failed after {self.max_attempts} attempts")
                        raise
                    
                    delay = self._calculate_delay(attempt)
                    logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}), retrying in {delay:.2f}s: {str(e)}")
                    time.sleep(delay)
            
            raise last_exception
        
        return wrapper
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt"""
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
        
        return delay

class Timeout:
    """Timeout decorator for operations"""
    
    def __init__(self, seconds: int):
        self.seconds = seconds
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {self.seconds} seconds")
            
            # Set the signal handler
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.seconds)
            
            try:
                result = func(*args, **kwargs)
                signal.alarm(0)  # Cancel the alarm
                return result
            finally:
                signal.signal(signal.SIGALRM, old_handler)
        
        return wrapper

class BulkheadIsolation:
    """Bulkhead pattern for resource isolation"""
    
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = threading.Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            acquired = self.semaphore.acquire(blocking=False)
            if not acquired:
                raise ResourceExhaustionError(
                    "thread_pool",
                    f"Maximum concurrent executions ({self.max_concurrent}) reached for {func.__name__}"
                )
            
            try:
                return func(*args, **kwargs)
            finally:
                self.semaphore.release()
        
        return wrapper

class HealthChecker:
    """Health checking utility for services and dependencies"""
    
    def __init__(self):
        self.checks = {}
        self.results = {}
        self.lock = threading.Lock()
    
    def register_check(self, name: str, check_func: Callable[[], bool], 
                      interval: int = 30, timeout: int = 10):
        """Register a health check"""
        with self.lock:
            self.checks[name] = {
                'func': check_func,
                'interval': interval,
                'timeout': timeout,
                'last_check': None,
                'next_check': datetime.now()
            }
    
    def run_check(self, name: str) -> Dict[str, Any]:
        """Run a specific health check"""
        if name not in self.checks:
            return {'status': 'unknown', 'error': f'Check {name} not registered'}
        
        check_info = self.checks[name]
        
        try:
            start_time = time.time()
            
            # Run check with timeout
            @Timeout(check_info['timeout'])
            def timed_check():
                return check_info['func']()
            
            result = timed_check()
            duration = time.time() - start_time
            
            check_result = {
                'status': 'healthy' if result else 'unhealthy',
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'details': result if isinstance(result, dict) else {}
            }
            
        except Exception as e:
            check_result = {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        
        with self.lock:
            self.results[name] = check_result
            self.checks[name]['last_check'] = datetime.now()
            self.checks[name]['next_check'] = datetime.now() + timedelta(seconds=check_info['interval'])
        
        return check_result
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all registered health checks"""
        results = {}
        for name in self.checks.keys():
            results[name] = self.run_check(name)
        
        overall_status = 'healthy' if all(
            result.get('status') == 'healthy' 
            for result in results.values()
        ) else 'unhealthy'
        
        return {
            'overall_status': overall_status,
            'checks': results,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_status(self, name: str = None) -> Dict[str, Any]:
        """Get health check status"""
        with self.lock:
            if name:
                return self.results.get(name, {'status': 'unknown'})
            return dict(self.results)

class ErrorRecovery:
    """Error recovery strategies"""
    
    @staticmethod
    def exponential_backoff_retry(func: Callable, max_attempts: int = 3, 
                                base_delay: float = 1.0) -> Any:
        """Retry with exponential backoff"""
        policy = RetryPolicy(max_attempts, base_delay)
        return policy(func)()
    
    @staticmethod
    def circuit_breaker_protection(func: Callable, failure_threshold: int = 5) -> Any:
        """Protect function with circuit breaker"""
        breaker = CircuitBreaker(failure_threshold)
        return breaker(func)()
    
    @staticmethod
    def graceful_degradation(primary_func: Callable, fallback_func: Callable) -> Any:
        """Try primary function, fall back to secondary on failure"""
        try:
            return primary_func()
        except Exception as e:
            logger.warning(f"Primary function failed, using fallback: {str(e)}")
            return fallback_func()
    
    @staticmethod
    def safe_execution(func: Callable, default_value: Any = None, 
                      log_errors: bool = True) -> Any:
        """Execute function safely with default return value"""
        try:
            return func()
        except Exception as e:
            if log_errors:
                logger.error(f"Safe execution failed: {str(e)}")
            return default_value

# Global health checker instance
health_checker = HealthChecker()

# Decorator shortcuts
def circuit_breaker(failure_threshold: int = 5, recovery_timeout: int = 60):
    """Circuit breaker decorator"""
    return CircuitBreaker(failure_threshold, recovery_timeout)

def retry(max_attempts: int = 3, base_delay: float = 1.0):
    """Retry decorator"""
    return RetryPolicy(max_attempts, base_delay)

def timeout(seconds: int):
    """Timeout decorator"""
    return Timeout(seconds)

def bulkhead(max_concurrent: int = 10):
    """Bulkhead isolation decorator"""
    return BulkheadIsolation(max_concurrent)
