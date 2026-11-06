from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Business, Product, User
from app.schemas import ProductCreate, ProductUpdate
from app.security import get_business_for_current_user, get_current_user

router = APIRouter(prefix="/api", tags=["products"])


def _serialize_product(product: Product) -> dict[str, Any]:
    return {
        "id": product.id,
        "business_id": product.business_id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "category": product.category,
        "image_url": product.image_url,
        "featured": product.featured,
    }


@router.get("/products")
def list_products(
    business_id: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    query = db.query(Product).join(Business).filter(Business.user_id == current_user.id)
    if business_id:
        query = query.filter(Product.business_id == business_id)
    return [_serialize_product(product) for product in query.order_by(Product.created_at.desc()).all()]


@router.get("/products/categories")
def list_product_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    categories = (
        db.query(Product.category)
        .join(Business)
        .filter(Business.user_id == current_user.id)
        .distinct()
        .order_by(Product.category)
        .all()
    )
    return {"categories": [category[0] for category in categories]}


@router.get("/products/{product_id}")
def get_product(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    product = db.query(Product).join(Business).filter(Product.id == product_id, Business.user_id == current_user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _serialize_product(product)


@router.post("/products")
def create_product(
    product: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    business_id = product.business_id or db.query(Business.id).filter(Business.user_id == current_user.id).order_by(Business.created_at.desc()).first()
    if not business_id:
        raise HTTPException(status_code=400, detail="Create a business before adding products")
    business = get_business_for_current_user(business_id[0] if isinstance(business_id, tuple) else business_id, current_user, db)

    created = Product(
        business_id=business.id,
        name=product.name.strip(),
        description=product.description.strip(),
        price=product.price.strip() or "Custom",
        category=(product.category or "General").strip() or "General",
        image_url=(product.image_url.strip() if product.image_url else None),
        featured=bool(product.featured),
    )
    db.add(created)
    db.commit()
    db.refresh(created)
    return _serialize_product(created)


@router.put("/products/{product_id}")
def update_product(
    product_id: str,
    product: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    existing = db.query(Product).join(Business).filter(Product.id == product_id, Business.user_id == current_user.id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.business_id:
        get_business_for_current_user(product.business_id, current_user, db)
        existing.business_id = product.business_id

    existing.name = product.name.strip()
    existing.description = product.description.strip()
    existing.price = product.price.strip() or "Custom"
    existing.category = (product.category or "General").strip() or "General"
    existing.image_url = product.image_url.strip() if product.image_url else None
    existing.featured = bool(product.featured)

    db.add(existing)
    db.commit()
    db.refresh(existing)
    return _serialize_product(existing)


@router.delete("/products/{product_id}")
def delete_product(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    product = db.query(Product).join(Business).filter(Product.id == product_id, Business.user_id == current_user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"status": "deleted", "id": product_id}
