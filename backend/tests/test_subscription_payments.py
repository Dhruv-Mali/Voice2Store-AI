from __future__ import annotations

import hashlib
import hmac
import os

from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///./voice2store_test.db")

from app.main import app

client = TestClient(app)


def test_subscription_plans_include_core_offerings():
    response = client.get("/api/subscriptions/plans")
    assert response.status_code == 200, response.text
    payload = response.json()
    codes = {plan["code"] for plan in payload["plans"]}
    assert {"free", "starter", "pro"}.issubset(codes)


def test_secure_payment_verification_rejects_invalid_signature():
    register = client.post(
        "/api/auth/register",
        json={"name": "Payment User", "email": "billing@example.com", "password": "StrongPass123!"},
    )
    assert register.status_code == 200, register.text
    token = register.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    order = client.post(
        "/api/payments/create-order",
        json={"plan_code": "starter"},
        headers=headers,
    )
    assert order.status_code == 200, order.text
    order_id = order.json()["order_id"]

    invalid = client.post(
        "/api/payments/verify",
        json={
            "plan_code": "starter",
            "razorpay_order_id": order_id,
            "razorpay_payment_id": "pay_invalid_123",
            "razorpay_signature": "invalid-signature",
        },
        headers=headers,
    )
    assert invalid.status_code == 400, invalid.text
    assert "signature" in invalid.json()["detail"].lower()
