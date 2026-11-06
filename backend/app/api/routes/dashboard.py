from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard/summary")
def dashboard_summary() -> dict[str, object]:
    return {
        "brand": "Voice2Store AI",
        "store_name": "Your Store",
        "site_health": 0,
        "monthly_visits": 0,
        "conversion_rate": 0,
        "revenue": 0,
        "orders": 0,
        "lead_score": 0,
        "active_campaigns": 0,
        "recent_actions": [
            "Add your business details to generate a storefront.",
            "Upload products and publish when your website is ready.",
        ],
    }
