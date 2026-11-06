from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_products_crud_round_trip():
    register = client.post(
        "/api/auth/register",
        json={"name": "Product Owner", "email": "products@example.com", "password": "StrongPass123!"},
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

    response = client.get("/api/products", headers=headers)
    assert response.status_code == 200
    initial = response.json()
    assert isinstance(initial, list)

    payload = {
        "business_id": business_id,
        "name": "Signature Cake",
        "description": "Artisan celebration cake",
        "price": "₹799",
        "category": "Bakery",
        "image_url": "https://example.com/cake.jpg",
    }

    created = client.post("/api/products", json=payload, headers=headers)
    assert created.status_code == 200, created.text
    created_body = created.json()
    product_id = created_body["id"]
    assert created_body["name"] == payload["name"]
    assert created_body["category"] == payload["category"]

    response = client.get(f"/api/products/{product_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == payload["name"]

    updated = client.put(f"/api/products/{product_id}", json={**payload, "price": "₹999"}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["price"] == "₹999"

    deleted = client.delete(f"/api/products/{product_id}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["status"] == "deleted"
