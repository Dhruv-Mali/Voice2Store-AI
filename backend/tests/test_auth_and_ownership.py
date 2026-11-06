from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_user_can_register_login_and_manage_own_business():
    email = "owner@example.com"
    password = "StrongPass123!"

    register = client.post(
        "/api/auth/register",
        json={"name": "Shop Owner", "email": email, "password": password},
    )
    assert register.status_code == 200, register.text
    body = register.json()
    assert body["user"]["email"] == email
    assert body["token"]

    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    token = login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    business = client.post(
        "/api/businesses",
        json={"name": "Bharat Bakes", "industry": "bakery", "location": "Ahmedabad", "language": "en"},
        headers=headers,
    )
    assert business.status_code == 200, business.text
    business_id = business.json()["id"]

    website = client.post(
        f"/api/businesses/{business_id}/website",
        json={
            "website_name": "Bharat Bakes Storefront",
            "website_data": {
                "business_name": "Bharat Bakes",
                "theme": {"primary": "#f97316", "secondary": "#facc15"},
            },
        },
        headers=headers,
    )
    assert website.status_code == 200, website.text

    product = client.post(
        "/api/products",
        json={
            "business_id": business_id,
            "name": "Signature Cake",
            "description": "Fresh celebration cake",
            "price": "₹799",
            "category": "Bakery",
        },
        headers=headers,
    )
    assert product.status_code == 200, product.text
    assert product.json()["business_id"] == business_id

    published = client.post(
        "/api/publish",
        json={
            "business_id": business_id,
            "website": {"business_name": "Bharat Bakes"},
            "seo_title": "Bharat Bakes | Storefront",
            "seo_description": "Fresh bakery storefront",
        },
        headers=headers,
    )
    assert published.status_code == 200, published.text
    slug = published.json()["slug"]
    assert slug

    other = client.post(
        "/api/auth/register",
        json={"name": "Other User", "email": "other@example.com", "password": "OtherPass123!"},
    )
    other_token = other.json()["token"]

    blocked = client.get(
        f"/api/businesses/{business_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert blocked.status_code == 403, blocked.text
