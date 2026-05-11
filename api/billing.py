"""Stripe webhooks + quota enforcement."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import stripe
from fastapi import APIRouter, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .db import get_db
from .models import Account

logger = logging.getLogger("toolpulse.billing")
settings = get_settings()

if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key

router = APIRouter(prefix="/billing", tags=["billing"])


PLAN_BY_PRICE: dict[str, dict] = {
    settings.stripe_price_indie or "price_indie": {"plan": "indie", "quota": 100_000},
    settings.stripe_price_pro or "price_pro": {"plan": "pro", "quota": 1_000_000},
    settings.stripe_price_team or "price_team": {"plan": "team", "quota": 100_000_000},
}


async def check_quota(account: Account, calls_to_add: int) -> bool:
    """Returns True if the account has quota for `calls_to_add` more calls.

    Quota resets at the start of each Stripe billing period (or every 30 days
    if no Stripe subscription is attached).
    """
    # Lazy reset if period elapsed
    now = datetime.utcnow()
    period_end = account.period_start.replace(tzinfo=None) if account.period_start.tzinfo else account.period_start
    days_since = (now - period_end).days
    if days_since >= 30:
        account.calls_this_period = 0
        account.period_start = now

    return (account.calls_this_period + calls_to_add) <= account.monthly_call_quota


async def increment_usage(account: Account, calls_added: int, db: AsyncSession) -> None:
    account.calls_this_period += calls_added
    await db.flush()


# =====================
# Stripe webhook
# =====================

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle subscription created/updated/canceled events."""
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="stripe webhook not configured")

    payload = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.stripe_webhook_secret)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"invalid signature: {e}")

    from .db import session_scope
    async with session_scope() as db:
        await _handle_stripe_event(event, db)
    return Response(status_code=200)


async def _handle_stripe_event(event: dict, db: AsyncSession) -> None:
    etype = event["type"]
    data = event["data"]["object"]

    if etype in ("customer.subscription.created", "customer.subscription.updated"):
        customer_id = data["customer"]
        # Determine plan from the first item's price
        items = data.get("items", {}).get("data", [])
        price_id = items[0]["price"]["id"] if items else None
        plan_info = PLAN_BY_PRICE.get(price_id, {"plan": "indie", "quota": 100_000})

        result = await db.execute(select(Account).where(Account.stripe_customer_id == customer_id))
        account = result.scalar_one_or_none()
        if not account:
            logger.warning("stripe webhook: no account for customer %s", customer_id)
            return
        account.plan = plan_info["plan"]
        account.monthly_call_quota = plan_info["quota"]
        account.stripe_subscription_id = data["id"]
        account.calls_this_period = 0
        account.period_start = datetime.utcnow()
        logger.info("upgraded account %s -> %s", account.id, plan_info["plan"])

    elif etype == "customer.subscription.deleted":
        customer_id = data["customer"]
        result = await db.execute(select(Account).where(Account.stripe_customer_id == customer_id))
        account = result.scalar_one_or_none()
        if account:
            account.plan = "indie"
            account.monthly_call_quota = 100_000
            account.stripe_subscription_id = None
            logger.info("downgraded account %s -> indie", account.id)


# =====================
# Checkout session creation
# =====================

@router.post("/checkout")
async def create_checkout_session(plan: str, account_email: str):
    """Create a Stripe Checkout session for a plan upgrade.

    Frontend calls this after the user clicks 'Upgrade' on the pricing page.
    """
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="stripe not configured")
    price_id = {
        "pro": settings.stripe_price_pro,
        "team": settings.stripe_price_team,
    }.get(plan)
    if not price_id:
        raise HTTPException(status_code=400, detail="unknown plan")

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.public_app_url}/dashboard?upgraded=1",
        cancel_url=f"{settings.public_app_url}/pricing",
        customer_email=account_email,
        allow_promotion_codes=True,
    )
    return {"url": session.url, "id": session.id}


@router.post("/portal")
async def create_billing_portal(customer_id: str):
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="stripe not configured")
    portal = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{settings.public_app_url}/dashboard/settings",
    )
    return {"url": portal.url}
