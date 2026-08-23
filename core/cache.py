# core/cache.py
import time
from functools import wraps
from typing import Callable, Any

def cache_ttl(ttl_seconds: int = 600) -> Callable:
    """Decorador simple y eficiente de cache en memoria con expiracion por TTL."""
    def decorator(func: Callable) -> Callable:
        cache: dict[tuple, tuple[float, Any]] = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            key = (args, tuple(sorted(kwargs.items())))
            now = time.time()
            if key in cache:
                timestamp, result = cache[key]
                if now - timestamp < ttl_seconds:
                    return result
            result = func(*args, **kwargs)
            cache[key] = (now, result)
            return result
            
        wrapper.clear_cache = lambda: cache.clear()
        return wrapper
    return decorator
