"""API key + SendGrid magic-link auth.

Two auth modes:
  - X-API-Key header (used by the SDK ingest endpoint and dashboard read APIs)
  - Bearer session JWT (used by the dashboard after magic-link verification)

Replaces Clerk — fully autonomous, no third-party app to provision. Uses the
same SendGrid that already routes our alerts.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .db import get_db
from .models import Account, ApiKey

settings = get_settings()
logger = logging.getLogger("toolpulse.auth")

API_KEY_PREFIX = "tp_live_"
JWT_ALGO = "HS256"
SESSION_TTL_DAYS = 30
MAGIC_LINK_TTL_SECONDS = 15 * 60  # 15 minutes


# =====================
# API key issuance
# =====================

def generate_api_key() -> tuple[str, str, str]:
    """Generate (full_key, key_prefix, key_hash). The full key is shown once."""
    secret = secrets.token_urlsafe(24).replace("-", "").replace("_", "")[:24]
    full_key = f"{API_KEY_PREFIX}{secret}"
    key_prefix = full_key[:16]
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return full_key, key_prefix, key_hash


async def validate_api_key(api_key: str, db: AsyncSession) -> Optional[Account]:
    if not api_key or not api_key.startswith(API_KEY_PREFIX):
        return None
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    stmt = select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.revoked_at.is_(None))
    result = await db.execute(stmt)
    api_key_row = result.scalar_one_or_none()
    if not api_key_row:
        return None
    api_key_row.last_used_at = datetime.utcnow()
    account_stmt = select(Account).where(Account.id == api_key_row.account_id)
    return (await db.execute(account_stmt)).scalar_one_or_none()


async def require_api_key(request: Request, db: AsyncSession = Depends(get_db)) -> Account:
    api_key = request.headers.get("X-API-Key", "")
    account = await validate_api_key(api_key, db)
    if not account:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid api key")
    return account


# =====================
# Magic-link tokens (HMAC-signed, time-bounded, no DB storage required)
# =====================

def _magic_secret() -> str:
    s = settings.magic_link_secret or settings.session_secret or "dev-only-insecure"
    return s


def _session_secret() -> str:
    return settings.session_secret or settings.magic_link_secret or "dev-only-insecure"


def _make_magic_token(email: str) -> str:
    """Returns a URL-safe token: <expiry>.<email>.<sig>."""
    expiry = int(time.time()) + MAGIC_LINK_TTL_SECONDS
    payload = f"{expiry}.{email.lower()}"
    sig = hmac.new(_magic_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def _verify_magic_token(token: str) -> Optional[str]:
    """Returns the verified email or None if invalid/expired."""
    parts = token.split(".")
    if len(parts) != 3:
        return None
    expiry_str, email, sig = parts
    try:
        expiry = int(expiry_str)
    except ValueError:
        return None
    if expiry < int(time.time()):
        return None
    payload = f"{expiry_str}.{email}"
    expected = hmac.new(_magic_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    return email


def issue_session_jwt(account_id: str) -> str:
    payload = {
        "sub": str(account_id),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=SESSION_TTL_DAYS),
        "iss": "toolpulse",
    }
    return jwt.encode(payload, _session_secret(), algorithm=JWT_ALGO)


async def require_session(request: Request, db: AsyncSession = Depends(get_db)) -> Account:
    """Validate a session JWT (Authorization: Bearer ... or `tp_session` cookie)."""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not token:
        token = request.cookies.get("tp_session", "")
    if not token:
        raise HTTPException(status_code=401, detail="missing session")
    try:
        payload = jwt.decode(token, _session_secret(), algorithms=[JWT_ALGO], issuer="toolpulse")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"invalid session: {e}")
    account_id = payload.get("sub")
    if not account_id:
        raise HTTPException(status_code=401, detail="invalid session")
    stmt = select(Account).where(Account.id == account_id)
    account = (await db.execute(stmt)).scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=401, detail="account not found")
    return account


# =====================
# Routes — request magic link, verify, sign out
# =====================

router = APIRouter(prefix="/auth", tags=["auth"])


class MagicLinkRequest(BaseModel):
    email: EmailStr


@router.post("/request-magic-link")
async def request_magic_link(payload: MagicLinkRequest):
    """Generate a magic link and email it to the user via SendGrid.

    No DB state is created here — the link itself is HMAC-signed, so we can
    verify it on click without remembering it. The Account is only created
    when the link is verified.
    """
    email = payload.email.lower()
    token = _make_magic_token(email)
    link = f"{settings.public_app_url.rstrip('/')}/auth/verify?{urlencode({'token': token})}"

    if not settings.sendgrid_api_key:
        # Dev fallback: log the link rather than emailing it
        logger.warning("SENDGRID not configured; magic link for %s: %s", email, link)
        return {"status": "ok", "dev_link": link}

    body = (
        f"Hi,\n\nClick the link below to sign in to ToolPulse. The link expires in 15 minutes:\n\n"
        f"{link}\n\nIf you didn't request this, ignore this email.\n\n— ToolPulse"
    )
    html = f"""<!doctype html>
<html><body style="font-family:system-ui;max-width:520px;margin:40px auto;line-height:1.5">
<h2 style="color:#7c3aed">Sign in to ToolPulse</h2>
<p>Click the button below to sign in. The link expires in 15 minutes.</p>
<p><a href="{link}" style="display:inline-block;padding:12px 24px;background:#7c3aed;color:#fff;text-decoration:none;border-radius:6px">Sign in</a></p>
<p style="color:#6b7280;font-size:14px">Or paste this link into your browser:<br><a href="{link}">{link}</a></p>
<p style="color:#6b7280;font-size:14px">If you didn't request this, you can ignore this email.</p>
</body></html>"""

    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {settings.sendgrid_api_key}"},
            json={
                "personalizations": [{"to": [{"email": email}]}],
                "from": {"email": settings.alert_from_email, "name": "ToolPulse"},
                "subject": "Sign in to ToolPulse",
                "content": [
                    {"type": "text/plain", "value": body},
                    {"type": "text/html", "value": html},
                ],
            },
        )
        if r.status_code >= 400:
            logger.warning("sendgrid send failed: %s %s", r.status_code, r.text[:200])
            raise HTTPException(status_code=502, detail="email send failed")

    return {"status": "ok", "message": "Check your inbox for the sign-in link."}


@router.get("/verify")
async def verify_magic_link(token: str, db: AsyncSession = Depends(get_db)):
    """Verify a magic link, create the account if needed, and return a session JWT."""
    email = _verify_magic_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="invalid or expired link")

    stmt = select(Account).where(Account.email == email)
    account = (await db.execute(stmt)).scalar_one_or_none()
    is_new = False
    new_api_key: Optional[str] = None
    if not account:
        account = Account(email=email)
        db.add(account)
        await db.flush()
        # Issue first API key on first sign-in
        full_key, prefix, key_hash = generate_api_key()
        db.add(ApiKey(account_id=account.id, key_prefix=prefix, key_hash=key_hash, name="default"))
        new_api_key = full_key
        is_new = True
    await db.commit()

    session_jwt = issue_session_jwt(str(account.id))
    return {
        "status": "ok",
        "session": session_jwt,
        "account_id": str(account.id),
        "email": account.email,
        "is_new_account": is_new,
        "first_api_key": new_api_key,  # only present on first sign-in — show once
    }
