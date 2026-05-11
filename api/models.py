"""SQLAlchemy ORM models + Pydantic request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


# =====================
# ORM models
# =====================

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_user_id: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=False)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    plan: Mapped[str] = mapped_column(String, default="indie", nullable=False)
    monthly_call_quota: Mapped[int] = mapped_column(Integer, default=100_000, nullable=False)
    calls_this_period: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    api_keys: Mapped[list["ApiKey"]] = relationship(back_populates="account", cascade="all, delete-orphan")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), index=True)
    key_prefix: Mapped[str] = mapped_column(String(16), nullable=False, index=True)  # tp_live_abcd
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)  # sha256 of full key
    name: Mapped[str] = mapped_column(String, default="default")
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    account: Mapped["Account"] = relationship(back_populates="api_keys")


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    agent_id: Mapped[str] = mapped_column(String, default="default")
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_shape: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    output_shape_tree: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    tags: Mapped[Optional[Any]] = mapped_column(JSONB, default=dict)
    called_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_tool_calls_account_tool_called", "account_id", "tool_name", "called_at"),
        Index("ix_tool_calls_account_agent", "account_id", "agent_id"),
    )


class DriftEvent(Base):
    __tablename__ = "drift_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    agent_id: Mapped[str] = mapped_column(String, default="default")
    baseline_shape: Mapped[str] = mapped_column(String(32), nullable=False)
    new_shape: Mapped[str] = mapped_column(String(32), nullable=False)
    diff: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)  # human-readable shape_diff()
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)


class HealthCheckConfig(Base):
    __tablename__ = "health_check_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    agent_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    check_type: Mapped[str] = mapped_column(String, nullable=False)  # 'http' or 'mcp'
    endpoint_url: Mapped[str] = mapped_column(String, nullable=False)
    method: Mapped[str] = mapped_column(String, default="GET")
    headers: Mapped[Optional[Any]] = mapped_column(JSONB, default=dict)
    probe_payload: Mapped[Optional[Any]] = mapped_column(JSONB, default=dict)
    interval_seconds: Mapped[int] = mapped_column(Integer, default=300)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class HealthCheckResult(Base):
    __tablename__ = "health_check_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    config_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("health_check_configs.id", ondelete="CASCADE"), index=True)
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)


class AlertChannel(Base):
    __tablename__ = "alert_channels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    channel_type: Mapped[str] = mapped_column(String, nullable=False)  # discord, slack, email, webhook
    target: Mapped[str] = mapped_column(String, nullable=False)  # webhook URL, email address
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


# =====================
# Public API schemas
# =====================

class ToolCallIngest(BaseModel):
    tool_name: str
    agent_id: str = "default"
    latency_ms: int = Field(ge=0, le=600_000)
    success: bool
    error: Optional[str] = None
    output_shape: Optional[str] = None
    output_shape_tree: Optional[Any] = None
    tags: dict = Field(default_factory=dict)
    called_at: Optional[datetime] = None


class ToolHealthSummary(BaseModel):
    tool_name: str
    total_calls: int
    successful: int
    avg_latency_ms: float
    p95_latency_ms: Optional[float] = None
    last_seen: datetime


class DriftEventOut(BaseModel):
    tool_name: str
    agent_id: str
    baseline_shape: str
    new_shape: str
    diff: Optional[dict] = None
    detected_at: datetime


class HealthCheckConfigCreate(BaseModel):
    tool_name: str
    agent_id: Optional[str] = None
    check_type: str = "http"
    endpoint_url: str
    method: str = "GET"
    headers: dict = Field(default_factory=dict)
    probe_payload: dict = Field(default_factory=dict)
    interval_seconds: int = Field(default=300, ge=60, le=86400)


class AlertChannelCreate(BaseModel):
    channel_type: str  # discord, slack, email, webhook
    target: str
