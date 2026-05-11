"""Schema drift detection.

For each successful tool call with a shape fingerprint, compare against the
most-common shape from the last 24h. If different, fire an alert (deduped).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from .alerts import send_alert
from .models import DriftEvent, ToolCall

logger = logging.getLogger("toolpulse.drift")


async def check_for_drift(
    *,
    account_id: uuid.UUID,
    tool_name: str,
    agent_id: str,
    new_shape: str,
    new_shape_tree: Optional[Any],
    db: AsyncSession,
) -> Optional[DriftEvent]:
    """Compare a new shape fingerprint to the dominant shape over the last 24h.

    Returns the DriftEvent if one was created, otherwise None.
    """
    # Find the most-frequent successful shape over the last 24h, EXCLUDING the new shape
    stmt = sa.text(
        """
        SELECT output_shape, COUNT(*) AS cnt
        FROM tool_calls
        WHERE account_id = :account_id
          AND tool_name = :tool_name
          AND agent_id = :agent_id
          AND success = true
          AND output_shape IS NOT NULL
          AND output_shape != :new_shape
          AND called_at > NOW() - INTERVAL '24 hours'
        GROUP BY output_shape
        ORDER BY cnt DESC
        LIMIT 1
        """
    )
    result = await db.execute(
        stmt,
        {
            "account_id": account_id,
            "tool_name": tool_name,
            "agent_id": agent_id,
            "new_shape": new_shape,
        },
    )
    row = result.fetchone()
    if not row:
        return None  # no baseline yet

    baseline_shape = row.output_shape

    # Require at least N observations of the baseline so a single weird call
    # in the early life of a tool doesn't create a noisy alert
    min_baseline_count = 5
    if row.cnt < min_baseline_count:
        return None

    # Dedup: have we already alerted on this exact (tool, agent, new_shape) in the last hour?
    dedup_stmt = sa.text(
        """
        SELECT 1 FROM drift_events
        WHERE account_id = :account_id
          AND tool_name = :tool_name
          AND agent_id = :agent_id
          AND new_shape = :new_shape
          AND detected_at > NOW() - INTERVAL '1 hour'
        LIMIT 1
        """
    )
    dedup = await db.execute(
        dedup_stmt,
        {
            "account_id": account_id,
            "tool_name": tool_name,
            "agent_id": agent_id,
            "new_shape": new_shape,
        },
    )
    if dedup.fetchone():
        return None

    # Compute human-readable diff if we have the baseline tree on a recent call
    baseline_tree_stmt = sa.text(
        """
        SELECT output_shape_tree
        FROM tool_calls
        WHERE account_id = :account_id
          AND tool_name = :tool_name
          AND agent_id = :agent_id
          AND output_shape = :baseline_shape
          AND output_shape_tree IS NOT NULL
        ORDER BY called_at DESC
        LIMIT 1
        """
    )
    baseline_tree_row = (
        await db.execute(
            baseline_tree_stmt,
            {
                "account_id": account_id,
                "tool_name": tool_name,
                "agent_id": agent_id,
                "baseline_shape": baseline_shape,
            },
        )
    ).fetchone()

    diff_obj = None
    if baseline_tree_row and baseline_tree_row.output_shape_tree and new_shape_tree:
        # Lazy import to avoid a hard dep cycle / import order issue
        from toolpulse.schema_hash import shape_diff  # type: ignore
        try:
            diff_obj = shape_diff(baseline_tree_row.output_shape_tree, new_shape_tree)
        except Exception as e:
            logger.debug("shape_diff failed: %s", e)

    drift = DriftEvent(
        account_id=account_id,
        tool_name=tool_name,
        agent_id=agent_id,
        baseline_shape=baseline_shape,
        new_shape=new_shape,
        diff=diff_obj,
        detected_at=datetime.utcnow(),
    )
    db.add(drift)
    await db.flush()

    diff_summary = ""
    if diff_obj:
        parts = []
        if diff_obj.get("added"):
            parts.append(f"added: {', '.join(diff_obj['added'][:5])}")
        if diff_obj.get("removed"):
            parts.append(f"removed: {', '.join(diff_obj['removed'][:5])}")
        if diff_obj.get("changed"):
            parts.append(f"changed: {', '.join(diff_obj['changed'][:5])}")
        diff_summary = " — " + "; ".join(parts) if parts else ""

    await send_alert(
        account_id=account_id,
        alert_type="schema_drift",
        tool_name=tool_name,
        agent_id=agent_id,
        message=(
            f"Response shape changed from baseline `{baseline_shape[:8]}…` "
            f"to `{new_shape[:8]}…`{diff_summary}. "
            f"Your agent may now be acting on unexpected data."
        ),
        db=db,
    )
    return drift
