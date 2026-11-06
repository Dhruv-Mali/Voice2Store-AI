from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Payment, Subscription, User
from app.schemas import CreateCheckoutRequest, VerifyPaymentRequest
from app.security import get_current_user
from app.api.routes.subscriptions import PLAN_LIBRARY, get_plan_details

router = APIRouter(prefix="/api/payments", tags=["payments"])


def _razorpay_enabled() -> bool:
    return bool(settings.razorpay_key_id and settings.razorpay_key_secret)


def _build_signature(order_id: str, payment_id: str) -> str:
    if not settings.razorpay_key_secret:
        raise ValueError("RAZORPAY_KEY_SECRET is not configured")
    generated = hmac.new(
        settings.razorpay_key_secret.encode("utf-8"),
        f"{order_id}|{payment_id}".encode("utf-8"),
        hashlib.sha256,
    )
    return generated.hexdigest()


@router.post("/create-order")
def create_payment_order(
    payload: CreateCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        plan = get_plan_details(payload.plan_code)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    amount_in_paise = int(plan["price"]) * 100
    order_id = f"order_{uuid.uuid4().hex[:18]}"

    if not _razorpay_enabled():
        payment_record = Payment(
            user_id=current_user.id,
            plan_code=plan["code"],
            order_id=order_id,
            amount=str(plan["price"]),
            currency=plan["currency"],
            status="pending",
            payment_metadata={"mock_mode": True, "plan_name": plan["name"]},
        )
        db.add(payment_record)
        db.commit()
        return {
            "order_id": order_id,
            "amount": amount_in_paise,
            "currency": plan["currency"],
            "key": settings.razorpay_key_id or "rzp_test_mock_key",
            "plan_code": plan["code"],
            "mock_mode": True,
        }

    order_payload = {
        "amount": amount_in_paise,
        "currency": settings.default_currency,
        "receipt": f"{current_user.id}:{plan['code']}:{uuid.uuid4().hex[:8]}",
        "notes": {"user_id": current_user.id, "plan_code": plan["code"]},
    }
    response = requests.post(
        "https://api.razorpay.com/v1/orders",
        auth=(settings.razorpay_key_id, settings.razorpay_key_secret),
        data=order_payload,
        timeout=20,
    )
    if response.status_code >= 400:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to create Razorpay order")

    order_data = response.json()
    order_id = order_data.get("id") or order_id

    payment_record = Payment(
        user_id=current_user.id,
        plan_code=plan["code"],
        order_id=order_id,
        amount=str(plan["price"]),
        currency=plan["currency"],
        status="pending",
        payment_metadata={"provider_response": order_data},
    )
    db.add(payment_record)
    db.commit()

    return {
        "order_id": order_id,
        "amount": amount_in_paise,
        "currency": plan["currency"],
        "key": settings.razorpay_key_id,
        "plan_code": plan["code"],
        "mock_mode": False,
    }


@router.post("/verify")
def verify_payment(
    payload: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        plan = get_plan_details(payload.plan_code)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if not payload.razorpay_payment_id or not payload.razorpay_order_id or not payload.razorpay_signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Razorpay payment details")

    if _razorpay_enabled():
        expected_signature = _build_signature(payload.razorpay_order_id, payload.razorpay_payment_id)
        if not hmac.compare_digest(expected_signature, payload.razorpay_signature):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment signature")
    elif payload.razorpay_signature == "mock-valid-signature":
        pass
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment signature")

    payment_record = (
        db.query(Payment)
        .filter(Payment.user_id == current_user.id, Payment.order_id == payload.razorpay_order_id)
        .order_by(Payment.created_at.desc())
        .first()
    )
    if payment_record is None:
        payment_record = Payment(
            user_id=current_user.id,
            plan_code=payload.plan_code,
            order_id=payload.razorpay_order_id,
            payment_id=payload.razorpay_payment_id,
            amount=str(plan["price"]),
            currency=plan["currency"],
            status="paid",
            signature=payload.razorpay_signature,
            payment_metadata={"verified": True, "plan_name": plan["name"]},
        )
        db.add(payment_record)
    else:
        payment_record.plan_code = payload.plan_code
        payment_record.payment_id = payload.razorpay_payment_id
        payment_record.signature = payload.razorpay_signature
        payment_record.amount = str(plan["price"])
        payment_record.currency = plan["currency"]
        payment_record.status = "paid"
        payment_record.verified_at = datetime.now(timezone.utc)
        payment_record.payment_metadata = {**payment_record.payment_metadata, "verified": True, "plan_name": plan["name"]}

    subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == current_user.id)
        .order_by(Subscription.started_at.desc())
        .first()
    )
    if subscription is None:
        subscription = Subscription(
            user_id=current_user.id,
            plan_code=payload.plan_code,
            status="active",
            amount_paid=str(plan["price"]),
            currency=plan["currency"],
            usage_limits=plan["usage_limits"],
            current_usage={"businesses": 0, "products": 0},
            last_payment_id=payload.razorpay_payment_id,
        )
        db.add(subscription)
    else:
        subscription.plan_code = payload.plan_code
        subscription.status = "active"
        subscription.amount_paid = str(plan["price"])
        subscription.currency = plan["currency"]
        subscription.usage_limits = plan["usage_limits"]
        subscription.last_payment_id = payload.razorpay_payment_id
        subscription.ends_at = datetime.now(timezone.utc) + timedelta(days=30)

    payment_record.verified_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(payment_record)
    db.refresh(subscription)

    return {
        "status": "paid",
        "plan_code": payload.plan_code,
        "payment_id": payload.razorpay_payment_id,
        "order_id": payload.razorpay_order_id,
        "amount": plan["price"],
        "currency": plan["currency"],
        "subscription_status": subscription.status,
        "verified": True,
    }


@router.get("/history")
def list_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    records = (
        db.query(Payment)
        .filter(Payment.user_id == current_user.id)
        .order_by(Payment.created_at.desc())
        .all()
    )
    return {
        "payments": [
            {
                "id": record.id,
                "plan_code": record.plan_code,
                "order_id": record.order_id,
                "payment_id": record.payment_id,
                "status": record.status,
                "amount": record.amount,
                "currency": record.currency,
                "provider": record.provider,
                "created_at": record.created_at.isoformat() if hasattr(record.created_at, "isoformat") else str(record.created_at),
                "verified_at": record.verified_at.isoformat() if record.verified_at and hasattr(record.verified_at, "isoformat") else None,
                "failure_reason": record.failure_reason,
            }
            for record in records
        ]
    }
