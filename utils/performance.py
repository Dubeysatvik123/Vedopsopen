"""
Performance optimization utilities for VedOps
"""

import time
import threading
import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List, Union
from functools import wraps, lru_cache
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing
import psutil
import hashlib
import pickle
import json
from datetime import datetime, timedelta
import weakref
import gc

logger = logging.getLogger(__name__)

class PerformanceProfiler:
    """Performance profiling and monitoring utility"""
    
    def __init__(self):
        self.profiles = {}
        self.lock = threading.Lock()
    
    def profile(self, name: str = None):
        """Decorator for profiling function execution"""
        def decorator(func: Callable) -> Callable:
            profile_name = name or f"{func.__module__}.{func.__name__}"
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                start_memory = psutil.Process().memory_info().rss
                
                try:
                    result = func(*args, **kwargs)
                    success = True
                    error = None
                except Exception as e:
                    result = None
                    success = False
                    error = str(e)
                    raise
                finally:
                    end_time = time.perf_counter()
                    end_memory = psutil.Process().memory_info().rss
                    
                    duration = end_time - start_time
                    memory_delta = end_memory - start_memory
                    
                    self._record_profile(profile_name, duration, memory_delta, success, error)
                
                return result
            
            return wrapper
        return decorator
    
    def _record_profile(self, name: str, duration: float, memory_delta: int, 
                       success: bool, error: Optional[str]):
        """Record profiling data"""
        with self.lock:
            if name not in self.profiles:
                self.profiles[name] = {
                    'call_count': 0,
                    'total_duration': 0.0,
                    'min_duration': float('inf'),
                    'max_duration': 0.0,
                    'total_memory_delta': 0,
                    'success_count': 0,
                    'error_count': 0,
                    'recent_calls': []
                }
            
            profile = self.profiles[name]
            profile['call_count'] += 1
            profile['total_duration'] += duration
            profile['min_duration'] = min(profile['min_duration'], duration)
            profile['max_duration'] = max(profile['max_duration'], duration)
            profile['total_memory_delta'] += memory_delta
            
            if success:
                profile['success_count'] += 1
            else:
                profile['error_count'] += 1
            
            # Keep last 10 calls for analysis
            profile['recent_calls'].append({
                'timestamp': datetime.now().isoformat(),
                'duration': duration,
                'memory_delta': memory_delta,
                'success': success,
                'error': error
            })
            
            if len(profile['recent_calls']) > 10:
                profile['recent_calls'].pop(0)
    
    def get_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """Get profile data for a specific function"""
        with self.lock:
            if name not in self.profiles:
                return None
            
            profile = self.profiles[name].copy()
            
            if profile['call_count'] > 0:
                profile['avg_duration'] = profile['total_duration'] / profile['call_count']
                profile['avg_memory_delta'] = profile['total_memory_delta'] / profile['call_count']
                profile['success_rate'] = profile['success_count'] / profile['call_count']
            
            return profile
    
    def get_all_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Get all profile data"""
        with self.lock:
            return {name: self.get_profile(name) for name in self.profiles.keys()}
    
    def reset_profiles(self):
        """Reset all profile data"""
        with self.lock:
            self.profiles.clear()

class CacheManager:
    """Advanced caching system with TTL and memory management"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = {}
        self.access_times = {}
        self.expiry_times = {}
        self.lock = threading.Lock()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired, daemon=True)
        self.cleanup_thread.start()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key not in self.cache:
                return None
            
            # Check if expired
            if key in self.expiry_times and datetime.now() > self.expiry_times[key]:
                self._remove_key(key)
                return None
            
            # Update access time
            self.access_times[key] = datetime.now()
            return self.cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        with self.lock:
            # Check if we need to evict
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()
            
            self.cache[key] = value
            self.access_times[key] = datetime.now()
            
            if ttl is not None:
                self.expiry_times[key] = datetime.now() + timedelta(seconds=ttl)
            elif self.default_ttl > 0:
                self.expiry_times[key] = datetime.now() + timedelta(seconds=self.default_ttl)
            
            return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self.lock:
            if key in self.cache:
                self._remove_key(key)
                return True
            return False
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.expiry_times.clear()
    
    def _remove_key(self, key: str):
        """Remove key and associated metadata"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
        self.expiry_times.pop(key, None)
    
    def _evict_lru(self):
        """Evict least recently used item"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        self._remove_key(lru_key)
    
    def _cleanup_expired(self):
        """Background thread to cleanup expired entries"""
        while True:
            try:
                time.sleep(60)  # Check every minute
                
                with self.lock:
                    now = datetime.now()
                    expired_keys = [
                        key for key, expiry in self.expiry_times.items()
                        if now > expiry
                    ]
                    
                    for key in expired_keys:
                        self._remove_key(key)
                
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hit_rate': getattr(self, '_hit_count', 0) / max(getattr(self, '_total_requests', 1), 1),
                'memory_usage': sum(len(pickle.dumps(v)) for v in self.cache.values())
            }

def cached(ttl: int = 3600, key_func: Optional[Callable] = None):
    """Caching decorator with TTL"""
    cache = CacheManager(default_ttl=ttl)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = hashlib.md5(
                    pickle.dumps((func.__name__, args, sorted(kwargs.items())))
                ).hexdigest()
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        wrapper.cache = cache
        return wrapper
    
    return decorator

class ResourcePool:
    """Generic resource pool for connection management"""
    
    def __init__(self, factory: Callable, max_size: int = 10, 
                 timeout: float = 30.0, validate_func: Optional[Callable] = None):
        self.factory = factory
        self.max_size = max_size
        self.timeout = timeout
        self.validate_func = validate_func
        
        self.pool = []
        self.in_use = set()
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
    
    def acquire(self) -> Any:
        """Acquire resource from pool"""
        with self.condition:
            # Wait for available resource
            deadline = time.time() + self.timeout
            
            while len(self.pool) == 0 and len(self.in_use) >= self.max_size:
                remaining = deadline - time.time()
                if remaining <= 0:
                    raise TimeoutError("Resource pool timeout")
                
                self.condition.wait(remaining)
            
            # Get resource from pool or create new one
            if self.pool:
                resource = self.pool.pop()
                
                # Validate resource if validator provided
                if self.validate_func and not self.validate_func(resource):
                    # Resource is invalid, create new one
                    resource = self.factory()
            else:
                resource = self.factory()
            
            self.in_use.add(id(resource))
            return resource
    
    def release(self, resource: Any):
        """Release resource back to pool"""
        with self.condition:
            resource_id = id(resource)
            
            if resource_id not in self.in_use:
                return  # Resource not from this pool
            
            self.in_use.remove(resource_id)
            
            # Return to pool if not at capacity
            if len(self.pool) < self.max_size:
                self.pool.append(resource)
            
            self.condition.notify()
    
    def close_all(self):
        """Close all resources in pool"""
        with self.lock:
            for resource in self.pool:
                if hasattr(resource, 'close'):
                    try:
                        resource.close()
                    except Exception as e:
                        logger.error(f"Error closing resource: {e}")
            
            self.pool.clear()
            self.in_use.clear()

class ParallelExecutor:
    """Optimized parallel execution utility"""
    
    def __init__(self, max_workers: Optional[int] = None, use_processes: bool = False):
        self.max_workers = max_workers or min(32, (multiprocessing.cpu_count() or 1) + 4)
        self.use_processes = use_processes
        self.executor_class = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
    
    def execute_parallel(self, func: Callable, items: List[Any], 
                        chunk_size: Optional[int] = None) -> List[Any]:
        """Execute function in parallel over list of items"""
        if not items:
            return []
        
        # Determine optimal chunk size
        if chunk_size is None:
            chunk_size = max(1, len(items) // (self.max_workers * 4))
        
        # Split items into chunks
        chunks = [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]
        
        def process_chunk(chunk):
            return [func(item) for item in chunk]
        
        # Execute chunks in parallel
        with self.executor_class(max_workers=self.max_workers) as executor:
            future_to_chunk = {executor.submit(process_chunk, chunk): chunk for chunk in chunks}
            
            results = []
            for future in as_completed(future_to_chunk):
                try:
                    chunk_results = future.result()
                    results.extend(chunk_results)
                except Exception as e:
                    logger.error(f"Parallel execution error: {e}")
                    # Continue with other chunks
            
            return results
    
    def execute_batch(self, functions: List[Callable]) -> List[Any]:
        """Execute multiple functions in parallel"""
        with self.executor_class(max_workers=self.max_workers) as executor:
            futures = [executor.submit(func) for func in functions]
            
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Batch execution error: {e}")
                    results.append(None)
            
            return results

class MemoryOptimizer:
    """Memory optimization utilities"""
    
    @staticmethod
    def optimize_memory():
        """Force garbage collection and memory optimization"""
        # Force garbage collection
        collected = gc.collect()
        
        # Get memory info
        process = psutil.Process()
        memory_info = process.memory_info()
        
        logger.info(f"Memory optimization: collected {collected} objects, "
                   f"RSS: {memory_info.rss / 1024 / 1024:.1f} MB")
        
        return {
            'collected_objects': collected,
            'memory_rss_mb': memory_info.rss / 1024 / 1024,
            'memory_vms_mb': memory_info.vms / 1024 / 1024
        }
    
    @staticmethod
    def memory_limit_decorator(max_memory_mb: int):
        """Decorator to limit memory usage of a function"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                process = psutil.Process()
                initial_memory = process.memory_info().rss / 1024 / 1024
                
                try:
                    result = func(*args, **kwargs)
                    
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_used = current_memory - initial_memory
                    
                    if memory_used > max_memory_mb:
                        logger.warning(f"Function {func.__name__} used {memory_used:.1f} MB "
                                     f"(limit: {max_memory_mb} MB)")
                        # Force garbage collection
                        MemoryOptimizer.optimize_memory()
                    
                    return result
                    
                except Exception as e:
                    # Cleanup on error
                    MemoryOptimizer.optimize_memory()
                    raise
            
            return wrapper
        return decorator
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get current memory usage statistics"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / 1024 / 1024
        }

class AsyncOptimizer:
    """Async/await optimization utilities"""
    
    @staticmethod
    async def run_in_executor(func: Callable, *args, executor=None) -> Any:
        """Run synchronous function in executor"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(executor, func, *args)
    
    @staticmethod
    async def gather_with_concurrency(coros: List, max_concurrency: int = 10):
        """Run coroutines with limited concurrency"""
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def sem_coro(coro):
            async with semaphore:
                return await coro
        
        return await asyncio.gather(*[sem_coro(coro) for coro in coros])
    
    @staticmethod
    def async_cache(ttl: int = 3600):
        """Async caching decorator"""
        cache = {}
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                cache_key = hashlib.md5(
                    pickle.dumps((func.__name__, args, sorted(kwargs.items())))
                ).hexdigest()
                
                # Check cache
                if cache_key in cache:
                    result, timestamp = cache[cache_key]
                    if time.time() - timestamp < ttl:
                        return result
                
                # Execute and cache
                result = await func(*args, **kwargs)
                cache[cache_key] = (result, time.time())
                
                return result
            
            return wrapper
        return decorator

# Global instances
profiler = PerformanceProfiler()
cache_manager = CacheManager()
parallel_executor = ParallelExecutor()

# Decorator shortcuts
def profile(name: str = None):
    """Performance profiling decorator"""
    return profiler.profile(name)

def optimize_memory(max_memory_mb: int = None):
    """Memory optimization decorator"""
    if max_memory_mb:
        return MemoryOptimizer.memory_limit_decorator(max_memory_mb)
    else:
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                finally:
                    MemoryOptimizer.optimize_memory()
            return wrapper
        return decorator

def parallel(max_workers: int = None, use_processes: bool = False):
    """Parallel execution decorator"""
    executor = ParallelExecutor(max_workers, use_processes)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(items: List[Any], **kwargs):
            return executor.execute_parallel(func, items, **kwargs)
        return wrapper
    
    return decorator
