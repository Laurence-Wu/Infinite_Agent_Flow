"""
Reusable decorators for thread safety, retry logic, and call logging.

Used across StateManager, AgentRegistry, CardsPlanner, CardsDealer, etc.
to provide consistent cross-cutting concerns without duplicating code.
"""

from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable, Tuple, Type


def locked(attr: str = "_lock") -> Callable:
    """Acquire ``self.<attr>`` (RLock or Lock) around the decorated method.

    The lock attribute must exist on the instance before the first call.

    Usage::

        class Foo:
            def __init__(self):
                self._lock = threading.RLock()

            @locked()
            def safe_method(self): ...
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs) -> Any:
            lock = getattr(self, attr)
            with lock:
                return fn(self, *args, **kwargs)
        return wrapper
    return decorator


def retry(
    n: int = 3,
    exc: Tuple[Type[Exception], ...] = (Exception,),
    delay: float = 0.5,
    backoff: float = 2.0,
) -> Callable:
    """Retry the decorated callable up to *n* times on matching exceptions.

    Each successive retry waits ``delay * (backoff ** attempt)`` seconds.
    Re-raises the last exception if all attempts fail.

    Usage::

        @retry(n=3, exc=(OSError,), delay=0.2)
        def write_file(self): ...
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> Any:
            last_exc: Exception | None = None
            wait = delay
            for attempt in range(n):
                try:
                    return fn(*args, **kwargs)
                except exc as e:  # type: ignore[misc]
                    last_exc = e
                    if attempt < n - 1:
                        time.sleep(wait)
                        wait *= backoff
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator


def log_call(level: str = "DEBUG", logger_attr: str = "_log") -> Callable:
    """Log method entry (with truncated args) and exit on every call.

    Looks for ``self.<logger_attr>`` first; falls back to a logger named
    after the class.  Does not log return values (avoids large objects).

    Usage::

        @log_call(level="DEBUG")
        def deal_card(self, card, card_index, total_cards): ...
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs) -> Any:
            log = getattr(self, logger_attr, None)
            if log is None:
                log = logging.getLogger(type(self).__name__)
            log_fn = getattr(log, level.lower(), log.debug)
            log_fn("→ %s(%s)", fn.__name__, _fmt_args(args, kwargs))
            result = fn(self, *args, **kwargs)
            log_fn("← %s", fn.__name__)
            return result
        return wrapper
    return decorator


# ------------------------------------------------------------------ #
#  Internal helpers
# ------------------------------------------------------------------ #

def _fmt_args(args: tuple, kwargs: dict) -> str:
    """Format positional and keyword args for log output (truncated)."""
    parts = [repr(a)[:60] for a in args]
    parts += [f"{k}={repr(v)[:40]}" for k, v in kwargs.items()]
    s = ", ".join(parts)
    return (s[:120] + "…") if len(s) > 120 else s
