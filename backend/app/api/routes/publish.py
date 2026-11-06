from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Business, PublishedSite, User
from app.schemas import PublishWebsiteRequest
from app.security import get_business_for_current_user, get_current_user

router = APIRouter(prefix="/api", tags=["publish"])


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "shop"


def _build_seo(site_data: dict[str, Any], *, business_name: str, seo_title: str | None, seo_description: str | None) -> dict[str, str]:
    description = site_data.get("tagline") or site_data.get("sections", {}).get("hero", {}).get("description") or "Professional storefront made with Voice2Store AI."
    title = seo_title or site_data.get("seo_title") or f"{business_name} | Storefront"
    description = seo_description or site_data.get("seo_description") or str(description)
    return {
        "title": title[:80],
        "description": description[:160],
        "keywords": f"{business_name}, local business, storefront, online shop",
    }


def _build_qr_code(url: str) -> str:
    encoded = quote(url, safe="")
    return f"https://api.qrserver.com/v1/create-qr-code/?size=220x220&margin=10&data={encoded}"


@router.post("/publish")
def publish_website(
    payload: PublishWebsiteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    business_id = payload.business_id
    if not business_id:
        business = db.query(Business).filter(Business.user_id == current_user.id).order_by(Business.created_at.desc()).first()
        if not business:
            raise HTTPException(status_code=400, detail="Create a business before publishing a storefront")
    else:
        business = get_business_for_current_user(business_id, current_user, db)

    website = payload.website or {}
    business_name = payload.business_name or website.get("business_name") or business.name
    slug = f"{_slugify(str(business_name))}-{business.id[:8]}"
    share_url = f"{settings.frontend_url.rstrip('/')}/site/{slug}"
    seo = _build_seo(website, business_name=business_name, seo_title=payload.seo_title, seo_description=payload.seo_description)

    existing = db.query(PublishedSite).filter(PublishedSite.slug == slug).first()
    if existing:
        slug = f"{slug}-{len(db.query(PublishedSite).filter(PublishedSite.business_id == business.id).all()) + 1}"
        share_url = f"{settings.frontend_url.rstrip('/')}/site/{slug}"

    record = PublishedSite(
        business_id=business.id,
        slug=slug,
        share_url=share_url,
        qr_code_url=_build_qr_code(share_url),
        seo_title=seo["title"],
        seo_description=seo["description"],
        website_data=website,
        whatsapp_number=(website.get("sections", {}).get("contact", {}).get("phone", "") or business.location or ""),
        message=payload.message or f"Hi {business_name}! I would like to know more about your products.",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "slug": record.slug,
        "share_url": record.share_url,
        "qr_code_url": record.qr_code_url,
        "business_name": business_name,
        "website": record.website_data,
        "seo": {
            "title": record.seo_title,
            "description": record.seo_description,
            "keywords": seo["keywords"],
        },
        "published_at": record.published_at.isoformat() if hasattr(record.published_at, "isoformat") else str(record.published_at),
        "whatsapp_number": record.whatsapp_number,
        "message": record.message,
    }


@router.get("/publish/{slug}")
def get_published_website(slug: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    site = db.query(PublishedSite).filter(PublishedSite.slug == slug).first()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Published site not found")

    business = db.query(Business).filter(Business.id == site.business_id).first()
    website = site.website_data or {}
    seo = {
        "title": site.seo_title,
        "description": site.seo_description,
        "keywords": f"{business.name if business else 'Local Business'}, local business, storefront, online shop",
    }
    return {
        "id": site.id,
        "slug": site.slug,
        "share_url": site.share_url,
        "qr_code_url": site.qr_code_url,
        "business_name": website.get("business_name") or (business.name if business else "Local Business"),
        "website": website,
        "seo": seo,
        "published_at": site.published_at.isoformat() if hasattr(site.published_at, "isoformat") else str(site.published_at),
        "whatsapp_number": site.whatsapp_number,
        "message": site.message,
    }
