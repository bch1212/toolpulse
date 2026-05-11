"""Async batch reporter — never blocks, never crashes the caller.

The reporter buffers tool-call records in memory and flushes them to the
ToolPulse ingest endpoint either when the batch fills or when a periodic
timer elapses. All errors are silently swallowed: the calling agent must
never crash because of monitoring overhead.
"""

from __future__ import annotations

import asyncio
import atexit
import json
import logging
import os
import queue
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

logger = logging.getLogger("toolpulse")
logger.addHandler(logging.NullHandler())

DEFAULT_ENDPOINT = "https://api.toolpulse.io"
DEFAULT_BATCH_SIZE = 50
DEFAULT_FLUSH_INTERVAL = 5.0  # seconds
DEFAULT_QUEUE_LIMIT = 5000


@dataclass
class _Config:
    api_key: Optional[str] = None
    endpoint: str = DEFAULT_ENDPOINT
    batch_size: int = DEFAULT_BATCH_SIZE
    flush_interval: float = DEFAULT_FLUSH_INTERVAL
    queue_limit: int = DEFAULT_QUEUE_LIMIT
    enabled: bool = True


_config = _Config(
    api_key=os.getenv("TOOLPULSE_API_KEY"),
    endpoint=os.getenv("TOOLPULSE_ENDPOINT", DEFAULT_ENDPOINT),
)


def configure(
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    batch_size: Optional[int] = None,
    flush_interval: Optional[float] = None,
    enabled: Optional[bool] = None,
) -> None:
    """Override configuration at runtime."""
    if api_key is not None:
        _config.api_key = api_key
    if endpoint is not None:
        _config.endpoint = endpoint
    if batch_size is not None:
        _config.batch_size = batch_size
    if flush_interval is not None:
        _config.flush_interval = flush_interval
    if enabled is not None:
        _config.enabled = enabled


@dataclass
class _Record:
    tool_name: str
    agent_id: str
    latency_ms: int
    success: bool
    error: Optional[str]
    output_shape: Optional[str]
    output_shape_tree: Optional[Any]
    tags: dict = field(default_factory=dict)
    called_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ToolPulseReporter:
    """Singleton reporter — owns the background flush thread.

    Thread-based so that sync callers don't need an event loop, and async
    callers don't have to await the network on the hot path. Both worlds
    just enqueue and return.
    """

    _instance: Optional["ToolPulseReporter"] = None
    _instance_lock = threading.Lock()

    def __new__(cls) -> "ToolPulseReporter":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._queue: queue.Queue[_Record] = queue.Queue(maxsize=_config.queue_limit)
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._worker_loop,
            name="toolpulse-reporter",
            daemon=True,
        )
        self._thread.start()
        atexit.register(self._shutdown)

    def record(
        self,
        tool_name: str,
        agent_id: Optional[str],
        latency_ms: int,
        success: bool,
        error: Optional[str],
        output_shape: Optional[str],
        output_shape_tree: Optional[Any] = None,
        tags: Optional[dict] = None,
    ) -> None:
        """Enqueue a record. Never raises, never blocks meaningfully."""
        if not _config.enabled or not _config.api_key:
            return
        try:
            rec = _Record(
                tool_name=tool_name,
                agent_id=agent_id or "default",
                latency_ms=latency_ms,
                success=success,
                error=error,
                output_shape=output_shape,
                output_shape_tree=output_shape_tree,
                tags=tags or {},
            )
            self._queue.put_nowait(rec)
        except queue.Full:
            # Drop on backpressure rather than crashing the caller.
            logger.debug("toolpulse queue full, dropping record")
        except Exception as e:  # belt-and-suspenders
            logger.debug("toolpulse record failed: %s", e)

    def _worker_loop(self) -> None:
        """Background thread: drain the queue on a timer or when the batch fills."""
        last_flush = time.time()
        batch: list[_Record] = []
        while not self._stop.is_set():
            timeout = max(0.05, _config.flush_interval - (time.time() - last_flush))
            try:
                rec = self._queue.get(timeout=timeout)
                batch.append(rec)
            except queue.Empty:
                pass

            now = time.time()
            should_flush = (
                len(batch) >= _config.batch_size
                or (batch and now - last_flush >= _config.flush_interval)
            )
            if should_flush:
                self._flush(batch)
                batch = []
                last_flush = now

        # Drain on shutdown
        while True:
            try:
                batch.append(self._queue.get_nowait())
            except queue.Empty:
                break
        if batch:
            self._flush(batch)

    def _flush(self, batch: list[_Record]) -> None:
        if not batch:
            return
        payload = [
            {
                "tool_name": r.tool_name,
                "agent_id": r.agent_id,
                "latency_ms": r.latency_ms,
                "success": r.success,
                "error": r.error,
                "output_shape": r.output_shape,
                "output_shape_tree": r.output_shape_tree,
                "tags": r.tags,
                "called_at": r.called_at,
            }
            for r in batch
        ]
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(
                    f"{_config.endpoint.rstrip('/')}/ingest",
                    headers={"X-API-Key": _config.api_key or "", "Content-Type": "application/json"},
                    content=json.dumps(payload),
                )
                if resp.status_code >= 400:
                    logger.debug("toolpulse ingest non-2xx: %s", resp.status_code)
        except Exception as e:
            logger.debug("toolpulse ingest failed: %s", e)

    def _shutdown(self) -> None:
        self._stop.set()
        try:
            self._thread.join(timeout=3.0)
        except Exception:
            pass


# Singleton accessor
def get_reporter() -> ToolPulseReporter:
    return ToolPulseReporter()
