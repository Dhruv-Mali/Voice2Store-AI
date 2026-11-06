from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Business, User, WebsiteConfiguration
from app.schemas import BusinessCreate, BusinessUpdate, WebsiteConfigCreate
from app.security import get_business_for_current_user, get_current_user

router = APIRouter(prefix="/api", tags=["businesses"])


@router.get("/businesses")
def list_businesses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict[str, object]]:
    businesses = db.query(Business).filter(Business.user_id == current_user.id).order_by(Business.created_at.desc()).all()
    return [
        {
            "id": business.id,
            "name": business.name,
            "industry": business.industry,
            "location": business.location,
            "language": business.language,
            "created_at": business.created_at.isoformat() if hasattr(business.created_at, "isoformat") else str(business.created_at),
        }
        for business in businesses
    ]


@router.post("/businesses")
def create_business(payload: BusinessCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    business = Business(
        user_id=current_user.id,
        name=payload.name.strip(),
        industry=payload.industry.strip() or "default",
        location=payload.location.strip() if payload.location else None,
        language=payload.language.strip() or "en",
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    return {
        "id": business.id,
        "user_id": business.user_id,
        "name": business.name,
        "industry": business.industry,
        "location": business.location,
        "language": business.language,
    }


@router.get("/businesses/{business_id}")
def get_business(business_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    business = get_business_for_current_user(business_id, current_user, db)
    website = db.query(WebsiteConfiguration).filter(WebsiteConfiguration.business_id == business.id).order_by(WebsiteConfiguration.created_at.desc()).first()
    return {
        "id": business.id,
        "user_id": business.user_id,
        "name": business.name,
        "industry": business.industry,
        "location": business.location,
        "language": business.language,
        "website": website.website_data if website else {},
    }


@router.put("/businesses/{business_id}")
def update_business(business_id: str, payload: BusinessUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    business = get_business_for_current_user(business_id, current_user, db)
    business.name = payload.name.strip()
    business.industry = payload.industry.strip() or "default"
    business.location = payload.location.strip() if payload.location else None
    business.language = payload.language.strip() or "en"
    db.add(business)
    db.commit()
    db.refresh(business)
    return {
        "id": business.id,
        "user_id": business.user_id,
        "name": business.name,
        "industry": business.industry,
        "location": business.location,
        "language": business.language,
    }


@router.post("/businesses/{business_id}/website")
def upsert_website(
    business_id: str,
    payload: WebsiteConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    business = get_business_for_current_user(business_id, current_user, db)
    website = db.query(WebsiteConfiguration).filter(WebsiteConfiguration.business_id == business.id).order_by(WebsiteConfiguration.created_at.desc()).first()
    if website is None:
        website = WebsiteConfiguration(
            business_id=business.id,
            website_name=payload.website_name,
            website_data=payload.website_data,
        )
        db.add(website)
    else:
        website.website_name = payload.website_name
        website.website_data = payload.website_data
        db.add(website)

    db.commit()
    db.refresh(website)
    return {
        "id": website.id,
        "business_id": website.business_id,
        "website_name": website.website_name,
        "website_data": website.website_data,
    }
