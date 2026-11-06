from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.businesses import router as businesses_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.health import router as health_router
from app.api.routes.payments import router as payments_router
from app.api.routes.products import router as products_router
from app.api.routes.publish import router as publish_router
from app.api.routes.subscriptions import router as subscriptions_router
from app.api.routes.transcription import router as transcription_router
from app.config import settings
from app.database import init_db
from app.logging_config import configure_logging

logger = configure_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI-powered voice-to-website platform for local shop owners.",
    docs_url=None if settings.app_env == "production" else "/docs",
    redoc_url=None if settings.app_env == "production" else "/redoc",
    openapi_url=None if settings.app_env == "production" else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if settings.app_env == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


logger.info("Starting Voice2Store AI backend in %s mode", settings.app_env)
init_db()

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(businesses_router)
app.include_router(dashboard_router)
app.include_router(subscriptions_router)
app.include_router(payments_router)
app.include_router(products_router)
app.include_router(publish_router)
app.include_router(transcription_router)


@app.get("/")
def root() -> dict[str, str]:
    logger.info("Root health endpoint accessed")
    return {"message": "Welcome to Voice2Store AI API"}
