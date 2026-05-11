"""Alert routing — Discord, Slack, SendGrid email, generic webhook.

Per-account channels are stored in the alert_channels table; we fan out to
all active channels for that account, plus any env-configured global fallbacks
(useful while bootstrapping).

Dedup is enforced upstream in drift.py / health_check.py via Redis or DB.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Iterable

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .models import AlertChannel

logger = logging.getLogger("toolpulse.alerts")
settings = get_settings()


EMOJI_BY_TYPE = {
    "tool_down": "🔴",
    "schema_drift": "⚠️",
    "latency_spike": "🐢",
    "quota_warning": "💸",
}


async def send_alert(
    *,
    account_id,
    alert_type: str,
    tool_name: str,
    agent_id: str,
    message: str,
    db: AsyncSession,
) -> None:
    """Look up account channels and dispatch in parallel."""
    emoji = EMOJI_BY_TYPE.get(alert_type, "🔔")
    title = f"{emoji} ToolPulse Alert: {alert_type.replace('_', ' ').title()}"
    body = (
        f"{title}\n"
        f"**Tool:** `{tool_name}`\n"
        f"**Agent:** `{agent_id}`\n\n"
        f"{message}\n\n"
        f"View in dashboard: {settings.public_app_url}/dashboard/tools/{tool_name}"
    )

    stmt = select(AlertChannel).where(
        AlertChannel.account_id == account_id, AlertChannel.active.is_(True)
    )
    result = await db.execute(stmt)
    channels = list(result.scalars().all())

    tasks = [_dispatch(c.channel_type, c.target, title, body) for c in channels]

    # Global fallbacks (env)
    if settings.discord_alert_webhook:
        tasks.append(_dispatch("discord", settings.discord_alert_webhook, title, body))
    if settings.slack_alert_webhook:
        tasks.append(_dispatch("slack", settings.slack_alert_webhook, title, body))

    if not tasks:
        return
    await asyncio.gather(*tasks, return_exceptions=True)


async def _dispatch(channel_type: str, target: str, title: str, body: str) -> None:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if channel_type == "discord":
                await client.post(target, json={"content": body})
            elif channel_type == "slack":
                await client.post(target, json={"text": body})
            elif channel_type == "webhook":
                await client.post(target, json={"title": title, "body": body})
            elif channel_type == "email":
                await _send_email(target, title, body)
    except Exception as e:
        logger.warning("alert dispatch %s -> %s failed: %s", channel_type, target[:40], e)


async def _send_email(to_email: str, subject: str, body: str) -> None:
    if not settings.sendgrid_api_key:
        return
    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": settings.alert_from_email, "name": "ToolPulse"},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {settings.sendgrid_api_key}"},
            json=payload,
        )
