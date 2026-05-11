"""Synthetic health checks via APScheduler.

On startup, every active HealthCheckConfig is registered as a recurring job.
Each run probes the configured endpoint, records the result, and alerts on
failure.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Optional

import httpx
import sqlalchemy as sa
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from .alerts import send_alert
from .db import session_scope
from .models import HealthCheckConfig, HealthCheckResult

logger = logging.getLogger("toolpulse.health")

scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler()
    return scheduler


async def run_health_check(config_id: str) -> None:
    """Probe a tool endpoint and record the result."""
    async with session_scope() as db:
        config = (
            await db.execute(select(HealthCheckConfig).where(HealthCheckConfig.id == config_id))
        ).scalar_one_or_none()
        if not config or not config.active:
            return

        start = time.perf_counter()
        success = False
        error: Optional[str] = None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if config.check_type == "http":
                    response = await client.request(
                        method=config.method or "GET",
                        url=config.endpoint_url,
                        headers=config.headers or {},
                        json=config.probe_payload or None,
                    )
                    success = response.status_code < 400
                    if not success:
                        error = f"HTTP {response.status_code}"
                elif config.check_type == "mcp":
                    # MCP-style probe: call tools/call with the configured probe payload
                    response = await client.post(
                        config.endpoint_url,
                        headers=config.headers or {},
                        json={
                            "jsonrpc": "2.0",
                            "id": "toolpulse-probe",
                            "method": "tools/call",
                            "params": {
                                "name": config.tool_name,
                                "arguments": config.probe_payload or {},
                            },
                        },
                    )
                    success = response.status_code == 200
                    try:
                        body = response.json()
                        if "error" in body:
                            success = False
                            error = body["error"].get("message", "mcp error")
                    except Exception:
                        if not success:
                            error = f"non-json response status {response.status_code}"
        except Exception as e:
            error = f"{type(e).__name__}: {e}"

        latency_ms = int((time.perf_counter() - start) * 1000)

        db.add(
            HealthCheckResult(
                config_id=config.id,
                tool_name=config.tool_name,
                success=success,
                latency_ms=latency_ms,
                error=error,
                checked_at=datetime.utcnow(),
            )
        )

        if not success:
            await send_alert(
                account_id=config.account_id,
                alert_type="tool_down",
                tool_name=config.tool_name,
                agent_id=config.agent_id or "synthetic",
                message=f"Health check FAILED. Error: {error}. Latency: {latency_ms}ms.",
                db=db,
            )


def register_health_check(config: HealthCheckConfig) -> None:
    """Add or replace a recurring job for this config."""
    sched = get_scheduler()
    sched.add_job(
        run_health_check,
        trigger="interval",
        seconds=config.interval_seconds,
        args=[str(config.id)],
        id=f"health_{config.id}",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )


def unregister_health_check(config_id: str) -> None:
    sched = get_scheduler()
    job_id = f"health_{config_id}"
    if sched.get_job(job_id):
        sched.remove_job(job_id)


async def reload_all_health_checks() -> None:
    """Pull all active configs from DB and register them. Called at app startup."""
    async with session_scope() as db:
        result = await db.execute(select(HealthCheckConfig).where(HealthCheckConfig.active.is_(True)))
        for config in result.scalars().all():
            register_health_check(config)
