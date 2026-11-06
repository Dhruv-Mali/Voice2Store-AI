from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Business, Product, Subscription, User
from app.security import get_current_user

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])

PLAN_LIBRARY: dict[str, dict[str, Any]] = {
    "free": {
        "code": "free",
        "name": "Free",
        "price": 0,
        "currency": "INR",
        "description": "Try the platform with essential storefront tools.",
        "features": [
            "1 active storefront",
            "3 product listings",
            "AI voice capture for one business",
            "Email support",
        ],
        "usage_limits": {"businesses": 1, "products": 3, "website_generations": 2, "storage_mb": 250},
    },
    "starter": {
        "code": "starter",
        "name": "Starter",
        "price": 999,
        "currency": "INR",
        "description": "For growing local businesses ready to publish and manage more.",
        "features": [
            "5 active storefronts",
            "25 product listings",
            "Unlimited AI prompts",
            "Priority WhatsApp support",
        ],
        "usage_limits": {"businesses": 5, "products": 25, "website_generations": 25, "storage_mb": 2000},
    },
    "pro": {
        "code": "pro",
        "name": "Pro",
        "price": 2499,
        "currency": "INR",
        "description": "Advanced growth plan for multi-store operators and agencies.",
        "features": [
            "Unlimited storefronts",
            "Unlimited product listings",
            "Advanced AI editing tools",
            "Premium onboarding and analytics",
        ],
        "usage_limits": {"businesses": 999, "products": 9999, "website_generations": 999, "storage_mb": 10000},
    },
}


def _serialize_plan(plan_code: str, plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "code": plan_code,
        "name": plan["name"],
        "price": plan["price"],
        "currency": plan["currency"],
        "description": plan["description"],
        "features": plan["features"],
        "usage_limits": plan["usage_limits"],
    }


def get_plan_details(plan_code: str) -> dict[str, Any]:
    plan = PLAN_LIBRARY.get(plan_code)
    if not plan:
        raise ValueError(f"Unknown subscription plan: {plan_code}")
    return plan


def get_usage_summary(db: Session, user: User) -> dict[str, Any]:
    business_count = db.query(Business).filter(Business.user_id == user.id).count()
    product_count = db.query(Product).join(Business).filter(Business.user_id == user.id).count()
    active_subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.id)
        .order_by(Subscription.started_at.desc())
        .first()
    )
    plan_code = (active_subscription.plan_code if active_subscription else "free")
    limits = get_plan_details(plan_code)["usage_limits"]
    return {
        "plan_code": plan_code,
        "businesses_used": business_count,
        "products_used": product_count,
        "usage_limits": limits,
        "remaining": {
            "businesses": max(limits["businesses"] - business_count, 0),
            "products": max(limits["products"] - product_count, 0),
        },
    }


@router.get("/plans")
def list_subscription_plans() -> dict[str, Any]:
    return {"plans": [_serialize_plan(code, plan) for code, plan in PLAN_LIBRARY.items()]}


@router.get("/me")
def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == current_user.id)
        .order_by(Subscription.started_at.desc())
        .first()
    )
    if not subscription:
        subscription = Subscription(
            user_id=current_user.id,
            plan_code="free",
            status="active",
            amount_paid="0",
            currency="INR",
            usage_limits=PLAN_LIBRARY["free"]["usage_limits"],
            current_usage={"businesses": 0, "products": 0},
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)

    plan = get_plan_details(subscription.plan_code)
    current_usage = get_usage_summary(db, current_user)
    return {
        "plan_code": subscription.plan_code,
        "plan_name": plan["name"],
        "status": subscription.status,
        "amount_paid": subscription.amount_paid,
        "currency": subscription.currency,
        "started_at": subscription.started_at.isoformat() if hasattr(subscription.started_at, "isoformat") else str(subscription.started_at),
        "ends_at": subscription.ends_at.isoformat() if subscription.ends_at and hasattr(subscription.ends_at, "isoformat") else None,
        "usage_limits": plan["usage_limits"],
        "current_usage": {
            "businesses": current_usage["businesses_used"],
            "products": current_usage["products_used"],
        },
    }


@router.get("/usage")
def get_subscription_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return get_usage_summary(db, current_user)
