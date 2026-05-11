"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("clerk_user_id", sa.String, unique=True, nullable=True),
        sa.Column("email", sa.String, nullable=False),
        sa.Column("stripe_customer_id", sa.String, nullable=True),
        sa.Column("stripe_subscription_id", sa.String, nullable=True),
        sa.Column("plan", sa.String, server_default="indie", nullable=False),
        sa.Column("monthly_call_quota", sa.Integer, server_default="100000", nullable=False),
        sa.Column("calls_this_period", sa.Integer, server_default="0", nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_accounts_stripe_customer", "accounts", ["stripe_customer_id"])

    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key_prefix", sa.String(16), nullable=False),
        sa.Column("key_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("name", sa.String, server_default="default"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_api_keys_account", "api_keys", ["account_id"])
    op.create_index("ix_api_keys_prefix", "api_keys", ["key_prefix"])

    op.create_table(
        "tool_calls",
        sa.Column("id", sa.BigInteger, autoincrement=True, primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_name", sa.String, nullable=False),
        sa.Column("agent_id", sa.String, server_default="default"),
        sa.Column("latency_ms", sa.Integer, nullable=False),
        sa.Column("success", sa.Boolean, nullable=False),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("output_shape", sa.String(32), nullable=True),
        sa.Column("output_shape_tree", postgresql.JSONB, nullable=True),
        sa.Column("tags", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("called_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_tool_calls_account_tool_called", "tool_calls", ["account_id", "tool_name", "called_at"])
    op.create_index("ix_tool_calls_account_agent", "tool_calls", ["account_id", "agent_id"])
    op.create_index("ix_tool_calls_called_at", "tool_calls", ["called_at"])

    # Convert to TimescaleDB hypertable if extension is present
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
                PERFORM create_hypertable('tool_calls', 'called_at', if_not_exists => TRUE);
            END IF;
        END$$;
        """
    )

    op.create_table(
        "drift_events",
        sa.Column("id", sa.BigInteger, autoincrement=True, primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_name", sa.String, nullable=False),
        sa.Column("agent_id", sa.String, server_default="default"),
        sa.Column("baseline_shape", sa.String(32), nullable=False),
        sa.Column("new_shape", sa.String(32), nullable=False),
        sa.Column("diff", postgresql.JSONB, nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_drift_events_account", "drift_events", ["account_id"])
    op.create_index("ix_drift_events_detected", "drift_events", ["detected_at"])

    op.create_table(
        "health_check_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_name", sa.String, nullable=False),
        sa.Column("agent_id", sa.String, nullable=True),
        sa.Column("check_type", sa.String, nullable=False),
        sa.Column("endpoint_url", sa.String, nullable=False),
        sa.Column("method", sa.String, server_default="GET"),
        sa.Column("headers", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("probe_payload", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("interval_seconds", sa.Integer, server_default="300"),
        sa.Column("active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_health_check_configs_account", "health_check_configs", ["account_id"])

    op.create_table(
        "health_check_results",
        sa.Column("id", sa.BigInteger, autoincrement=True, primary_key=True),
        sa.Column("config_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("health_check_configs.id", ondelete="CASCADE")),
        sa.Column("tool_name", sa.String, nullable=False),
        sa.Column("success", sa.Boolean, nullable=False),
        sa.Column("latency_ms", sa.Integer, nullable=False),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_health_check_results_config", "health_check_results", ["config_id"])
    op.create_index("ix_health_check_results_checked", "health_check_results", ["checked_at"])

    op.create_table(
        "alert_channels",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel_type", sa.String, nullable=False),
        sa.Column("target", sa.String, nullable=False),
        sa.Column("active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("ix_alert_channels_account", "alert_channels", ["account_id"])


def downgrade() -> None:
    op.drop_table("alert_channels")
    op.drop_table("health_check_results")
    op.drop_table("health_check_configs")
    op.drop_table("drift_events")
    op.drop_table("tool_calls")
    op.drop_table("api_keys")
    op.drop_table("accounts")
