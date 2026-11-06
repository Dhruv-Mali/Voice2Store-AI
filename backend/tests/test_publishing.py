from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_publish_site_generates_slug_and_share_url():
    register = client.post(
        "/api/auth/register",
        json={"name": "Publisher", "email": "publish@example.com", "password": "StrongPass123!"},
    )
    assert register.status_code == 200, register.text
    token = register.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    business = client.post(
        "/api/businesses",
        json={"name": "Bharat Bakes", "industry": "bakery", "location": "Ahmedabad", "language": "en"},
        headers=headers,
    )
    assert business.status_code == 200, business.text
    business_id = business.json()["id"]

    payload = {
        "business_id": business_id,
        "website": {
            "business_name": "Bharat Bakes",
            "industry": "bakery",
            "language": "en",
            "tagline": "Fresh and warm bakery",
            "sections": {
                "hero": {"headline": "Fresh bakery for your neighborhood", "description": "Fresh cakes and breads", "cta_primary": "Shop Now", "cta_secondary": "Call us"},
                "about": {"title": "About Us", "description": "We bake fresh daily", "highlights": ["Fresh", "Local"]},
                "products": {"title": "Products", "items": [{"name": "Cake", "description": "Sweet celebration cake", "price": "₹799"}]},
                "contact": {"title": "Contact", "phone": "+919876543210", "email": "hello@bharatbakes.in", "address": "Ahmedabad", "business_hours": "Mon-Sat"},
            },
        }
    }

    response = client.post("/api/publish", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["slug"]
    assert body["share_url"].endswith(f"/site/{body['slug']}")
    assert body["seo"]["title"]

    fetched = client.get(f"/api/publish/{body['slug']}")
    assert fetched.status_code == 200
    assert fetched.json()["website"]["business_name"] == "Bharat Bakes"
