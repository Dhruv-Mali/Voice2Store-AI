from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "service": "Voice2Store AI",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "healthy": True,
    }
