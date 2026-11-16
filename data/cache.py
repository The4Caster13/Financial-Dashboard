from __future__ import annotations

import time
from functools import wraps
from typing import Any, Callable

_store: dict[tuple, tuple[float, Any]] = {}


def ttl_cache(ttl_seconds: float) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (func.__module__, func.__qualname__, args, tuple(sorted(kwargs.items())))
            now = time.monotonic()
            cached = _store.get(key)
            if cached is not None and now - cached[0] < ttl_seconds:
                return cached[1]
            result = func(*args, **kwargs)
            _store[key] = (now, result)
            return result

        wrapper.cache_clear = lambda: _store.clear()
        return wrapper

    return decorator
