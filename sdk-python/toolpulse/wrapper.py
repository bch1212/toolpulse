"""@monitor decorator — wraps any tool function (async or sync).

Critical contract: the decorator MUST NEVER crash or block the caller.
- Network I/O is fire-and-forget (handed to a background thread)
- Exceptions inside the monitoring code are swallowed
- Exceptions from the wrapped function are re-raised unchanged
"""

from __future__ import annotations

import asyncio
import functools
import inspect
import time
from typing import Any, Callable, Optional

from .reporter import get_reporter
from .schema_hash import extract_shape, fingerprint


def monitor(
    tool_name: Optional[str] = None,
    agent_id: Optional[str] = None,
    tags: Optional[dict] = None,
    capture_shape: bool = True,
):
    """Decorator that records latency, success, and response shape for a tool call.

    Args:
        tool_name: logical name to attribute the call to. Defaults to func.__name__.
        agent_id: which agent made the call. Defaults to "default".
        tags: arbitrary key/value metadata attached to every call.
        capture_shape: if False, skip schema fingerprinting (saves CPU on large responses).

    Example:
        @monitor(tool_name="search_web", agent_id="researcher")
        async def search_web(query: str) -> dict:
            ...
    """

    def decorator(func: Callable):
        name = tool_name or getattr(func, "__name__", "anonymous")
        is_async = asyncio.iscoroutinefunction(func) or inspect.iscoroutinefunction(func)

        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = time.perf_counter()
                error: Optional[str] = None
                result: Any = None
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    error = _format_error(e)
                    raise
                finally:
                    _record_safe(name, agent_id, start, result, error, tags, capture_shape)

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            error: Optional[str] = None
            result: Any = None
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = _format_error(e)
                raise
            finally:
                _record_safe(name, agent_id, start, result, error, tags, capture_shape)

        return sync_wrapper

    return decorator


def _format_error(e: BaseException) -> str:
    msg = f"{type(e).__name__}: {e}"
    return msg[:500]  # Cap to avoid sending stack-trace-sized strings


def _record_safe(
    name: str,
    agent_id: Optional[str],
    start: float,
    result: Any,
    error: Optional[str],
    tags: Optional[dict],
    capture_shape: bool,
) -> None:
    """Catch-all wrapper around the report path so we never raise from `finally:`."""
    try:
        latency_ms = int((time.perf_counter() - start) * 1000)
        shape: Optional[str] = None
        shape_tree: Optional[Any] = None
        if capture_shape and result is not None and error is None:
            try:
                shape_tree = extract_shape(result)
                shape = fingerprint(result)
            except Exception:
                pass
        get_reporter().record(
            tool_name=name,
            agent_id=agent_id,
            latency_ms=latency_ms,
            success=error is None,
            error=error,
            output_shape=shape,
            output_shape_tree=shape_tree,
            tags=tags,
        )
    except Exception:
        # Absolute last-resort guard — never propagate.
        pass
