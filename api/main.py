"""ToolPulse API — FastAPI app entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .alerts import send_alert
from .auth import generate_api_key, require_api_key, require_session, router as auth_router
from .billing import check_quota, increment_usage, router as billing_router
from .config import get_settings
from .db import get_db
from .drift import check_for_drift
from .health_check import (
    get_scheduler,
    register_health_check,
    reload_all_health_checks,
    unregister_health_check,
)
from .models import (
    Account,
    AlertChannel,
    AlertChannelCreate,
    ApiKey,
    DriftEvent,
    HealthCheckConfig,
    HealthCheckConfigCreate,
    ToolCall,
    ToolCallIngest,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("toolpulse")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    sched = get_scheduler()
    sched.start()
    try:
        await reload_all_health_checks()
    except Exception as e:
        logger.warning("health check reload failed (DB may not be ready): %s", e)
    yield
    sched.shutdown(wait=False)


app = FastAPI(
    title="ToolPulse API",
    version="0.1.0",
    description="Agent tool reliability monitoring — ingest, drift detection, synthetic checks.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.public_app_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(billing_router)
app.include_router(auth_router)


# =====================
# Health
# =====================

@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": app.version, "ts": datetime.utcnow().isoformat()}


# =====================
# Ingest (called by SDK)
# =====================

@app.post("/ingest")
async def ingest_tool_calls(
    payload: list[ToolCallIngest],
    account: Account = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if len(payload) == 0:
        return {"ingested": 0}
    if len(payload) > 1000:
        raise HTTPException(status_code=413, detail="batch too large (max 1000)")

    if not await check_quota(account, len(payload)):
        raise HTTPException(status_code=429, detail="monthly call quota exceeded")

    drift_alerts: list = []
    for call in payload:
        record = ToolCall(
            account_id=account.id,
            tool_name=call.tool_name[:200],
            agent_id=call.agent_id[:100],
            latency_ms=call.latency_ms,
            success=call.success,
            error=(call.error[:5000] if call.error else None),
            output_shape=call.output_shape,
            output_shape_tree=call.output_shape_tree,
            tags=call.tags,
            called_at=call.called_at or datetime.utcnow(),
        )
        db.add(record)

        # Drift detection on successful, shape-bearing calls only
        if call.success and call.output_shape:
            try:
                event = await check_for_drift(
                    account_id=account.id,
                    tool_name=call.tool_name,
                    agent_id=call.agent_id,
                    new_shape=call.output_shape,
                    new_shape_tree=call.output_shape_tree,
                    db=db,
                )
                if event:
                    drift_alerts.append(event)
            except Exception as e:
                logger.warning("drift check failed: %s", e)

    await increment_usage(account, len(payload), db)
    await db.commit()
    return {"ingested": len(payload), "drift_events_created": len(drift_alerts)}


# =====================
# Tool listing & detail
# =====================

@app.get("/tools")
async def list_tools(
    account: Account = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    stmt = sa.text(
        """
        SELECT
            tool_name,
            COUNT(*) AS total_calls,
            SUM(CASE WHEN success THEN 1 ELSE 0 END) AS successful,
            AVG(latency_ms)::float AS avg_latency_ms,
            percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms)::float AS p95_latency_ms,
            MAX(called_at) AS last_seen
        FROM tool_calls
        WHERE account_id = :account_id
          AND called_at > NOW() - INTERVAL '24 hours'
        GROUP BY tool_name
        ORDER BY total_calls DESC
        """
    )
    result = await db.execute(stmt, {"account_id": account.id})
    return [dict(row) for row in result.mappings().all()]


@app.get("/tools/{tool_name}/latency")
async def tool_latency_history(
    tool_name: str,
    hours: int = 24,
    account: Account = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    if hours <= 0 or hours > 168:
        raise HTTPException(status_code=400, detail="hours must be 1..168")
    stmt = sa.text(
        """
        SELECT
            date_trunc('hour', called_at) AS hour,
            AVG(latency_ms)::float AS avg_ms,
            MIN(latency_ms) AS min_ms,
            MAX(latency_ms) AS max_ms,
            percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms)::float AS p95_ms,
            COUNT(*) AS calls,
            SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) AS errors
        FROM tool_calls
        WHERE account_id = :account_id
          AND tool_name = :tool_name
          AND called_at > NOW() - make_interval(hours => :hours)
        GROUP BY 1
        ORDER BY 1
        """
    )
    result = await db.execute(
        stmt, {"account_id": account.id, "tool_name": tool_name, "hours": hours}
    )
    return [dict(row) for row in result.mappings().all()]


@app.get("/tools/{tool_name}/recent")
async def tool_recent_calls(
    tool_name: str,
    limit: int = 50,
    account: Account = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    limit = min(max(limit, 1), 500)
    stmt = sa.text(
        """
        SELECT id, agent_id, latency_ms, success, error, output_shape, tags, called_at
        FROM tool_calls
        WHERE account_id = :account_id AND tool_name = :tool_name
        ORDER BY called_at DESC
        LIMIT :limit
        """
    )
    result = await db.execute(
        stmt, {"account_id": account.id, "tool_name": tool_name, "limit": limit}
    )
    return [dict(row) for row in result.mappings().all()]


# =====================
# Drift events
# =====================

@app.get("/drift-events")
async def get_drift_events(
    limit: int = 50,
    account: Account = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    limit = min(max(limit, 1), 500)
    stmt = (
        select(DriftEvent)
        .where(DriftEvent.account_id == account.id)
        .order_by(DriftEvent.detected_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        {
            "tool_name": d.tool_name,
            "agent_id": d.agent_id,
            "baseline_shape": d.baseline_shape,
            "new_shape": d.new_shape,
            "diff": d.diff,
            "detected_at": d.detected_at.isoformat(),
        }
        for d in rows
    ]


# =====================
# Health check management
# =====================

@app.post("/health-checks")
async def create_health_check(
    payload: HealthCheckConfigCreate,
    account: Account = Depends(require_session),
    db: AsyncSession = Depends(get_db),
) -> dict:
    config = HealthCheckConfig(
        account_id=account.id,
        tool_name=payload.tool_name,
        agent_id=payload.agent_id,
        check_type=payload.check_type,
        endpoint_url=payload.endpoint_url,
        method=payload.method,
        headers=payload.headers,
        probe_payload=payload.probe_payload,
        interval_seconds=payload.interval_seconds,
    )
    db.add(config)
    await db.commit()
    register_health_check(config)
    return {"id": str(config.id), "tool_name": config.tool_name}


@app.delete("/health-checks/{config_id}")
async def delete_health_check(
    config_id: str,
    account: Account = Depends(require_session),
    db: AsyncSession = Depends(get_db),
) -> dict:
    stmt = select(HealthCheckConfig).where(
        HealthCheckConfig.id == config_id, HealthCheckConfig.account_id == account.id
    )
    config = (await db.execute(stmt)).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404)
    await db.delete(config)
    await db.commit()
    unregister_health_check(config_id)
    return {"deleted": True}


# =====================
# Alert channels
# =====================

@app.post("/alert-channels")
async def add_alert_channel(
    payload: AlertChannelCreate,
    account: Account = Depends(require_session),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if payload.channel_type not in {"discord", "slack", "email", "webhook"}:
        raise HTTPException(status_code=400, detail="unsupported channel type")
    channel = AlertChannel(
        account_id=account.id, channel_type=payload.channel_type, target=payload.target
    )
    db.add(channel)
    await db.commit()
    return {"id": str(channel.id)}


@app.get("/alert-channels")
async def list_alert_channels(
    account: Account = Depends(require_session),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    stmt = select(AlertChannel).where(AlertChannel.account_id == account.id)
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {"id": str(c.id), "type": c.channel_type, "target": c.target, "active": c.active}
        for c in rows
    ]


# =====================
# API keys
# =====================

@app.get("/me")
async def me(account: Account = Depends(require_session)) -> dict:
    return {
        "id": str(account.id),
        "email": account.email,
        "plan": account.plan,
        "monthly_call_quota": account.monthly_call_quota,
        "calls_this_period": account.calls_this_period,
    }


@app.post("/api-keys")
async def issue_api_key(
    name: str = "default",
    account: Account = Depends(require_session),
    db: AsyncSession = Depends(get_db),
) -> dict:
    full_key, prefix, key_hash = generate_api_key()
    db.add(ApiKey(account_id=account.id, key_prefix=prefix, key_hash=key_hash, name=name))
    await db.commit()
    return {"api_key": full_key, "prefix": prefix, "name": name}


# =====================
# Public status data (for status.toolpulse.io)
# =====================

@app.get("/public/status/summary")
async def public_status_summary(db: AsyncSession = Depends(get_db)) -> dict:
    """Aggregate stats across the whole platform — fuels the public status page
    and the public 'State of LLM Tools' index. No PII, no per-account data."""
    stmt = sa.text(
        """
        SELECT
            tool_name,
            COUNT(*) AS calls_24h,
            AVG(latency_ms)::int AS avg_latency_ms,
            (SUM(CASE WHEN success THEN 1 ELSE 0 END)::float / NULLIF(COUNT(*), 0)) AS success_rate
        FROM tool_calls
        WHERE called_at > NOW() - INTERVAL '24 hours'
          AND tool_name IN (
            'openai_chat', 'anthropic_messages', 'gemini_generate',
            'mistral_chat', 'cohere_chat', 'web_search', 'wolfram_alpha',
            'tavily_search', 'serper', 'brave_search'
          )
        GROUP BY tool_name
        ORDER BY tool_name
        """
    )
    try:
        rows = (await db.execute(stmt)).mappings().all()
        return {"tools": [dict(r) for r in rows], "as_of": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.warning("public status query failed: %s", e)
        return {"tools": [], "as_of": datetime.utcnow().isoformat()}
