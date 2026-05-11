"""Centralized settings — read from env once, cached."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://toolpulse:toolpulse@localhost:5432/toolpulse"

    # Redis (alert dedup, rate limit)
    redis_url: str = "redis://localhost:6379/0"

    # Auth — magic-link via SendGrid (no Clerk)
    magic_link_secret: Optional[str] = None
    session_secret: Optional[str] = None

    # Billing — Stripe
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_price_indie: Optional[str] = None
    stripe_price_pro: Optional[str] = None
    stripe_price_team: Optional[str] = None

    # Alerts
    sendgrid_api_key: Optional[str] = None
    alert_from_email: str = "alerts@toolpulse.io"
    discord_alert_webhook: Optional[str] = None  # default fallback channel
    slack_alert_webhook: Optional[str] = None

    # Public URLs
    public_app_url: str = "https://toolpulse.io"
    public_api_url: str = "https://api.toolpulse.io"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
