from __future__ import annotations

import re
from typing import Any

import requests
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/api", tags=["voice"])

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "gu": "Gujarati",
}

THEME_LIBRARY = {
    "bakery": {
        "primary": "#f97316",
        "secondary": "#facc15",
        "accent": "#fff7ed",
        "hero_gradient": "from-orange-500 via-amber-400 to-yellow-200",
        "description": "Warm, handcrafted, family-friendly bakery storefront",
    },
    "grocery": {
        "primary": "#0f766e",
        "secondary": "#2dd4bf",
        "accent": "#ecfeff",
        "hero_gradient": "from-teal-600 via-cyan-500 to-sky-400",
        "description": "Fresh, trusted everyday essentials storefront",
    },
    "salon": {
        "primary": "#a855f7",
        "secondary": "#ec4899",
        "accent": "#faf5ff",
        "hero_gradient": "from-violet-600 via-pink-500 to-fuchsia-300",
        "description": "Modern beauty and grooming destination",
    },
    "restaurant": {
        "primary": "#dc2626",
        "secondary": "#fb7185",
        "accent": "#fff1f2",
        "hero_gradient": "from-red-600 via-rose-500 to-orange-300",
        "description": "Bold, flavorful dining experience",
    },
    "default": {
        "primary": "#2563eb",
        "secondary": "#38bdf8",
        "accent": "#eff6ff",
        "hero_gradient": "from-blue-600 via-cyan-500 to-sky-300",
        "description": "Professional local business storefront",
    },
}

INDUSTRY_KEYWORDS = {
    "bakery": ["bakery", "cake", "bread", "sweet", "cookie", "pastry", "bakes", "baking"],
    "grocery": ["grocery", "mart", "store", "market", "vegetable", "fruit", "daily needs", "general store"],
    "salon": ["salon", "beauty", "spa", "hair", "makeup", "facial", "makeup artist"],
    "restaurant": ["restaurant", "cafe", "food", "dining", "catering", "kitchen", "eatery"],
}


class VoiceProcessingRequest(BaseModel):
    transcript: str
    language: str = "en"
    business_name: str | None = None
    location: str | None = None
    industry: str | None = None


def _title_case(value: str) -> str:
    return " ".join(part.capitalize() for part in value.split())


def _infer_industry(transcript: str) -> str:
    normalized = transcript.lower()
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return industry
    return "default"


def _extract_business_name(transcript: str, fallback: str | None) -> str:
    if fallback and fallback.strip():
        return fallback.strip()

    match = re.search(r"(?:for|my|our)\s+([A-Z][A-Za-z0-9&\- ]{2,50})", transcript)
    if match:
        return match.group(1).strip()

    cleaned = re.sub(r"[^A-Za-z0-9 &-]", " ", transcript).strip()
    tokens = [token for token in cleaned.split() if token and token.lower() not in {"my", "our", "this", "we", "i"}]
    if tokens:
        return _title_case(" ".join(tokens[:4]))
    return "Your Business"


def _build_default_products(industry: str) -> list[dict[str, str]]:
    defaults = {
        "bakery": [
            {"name": "Signature Cakes", "description": "Custom celebration cakes and fresh bakes made daily.", "price": "From ₹799"},
            {"name": "Bakery Combo", "description": "Breakfast packs, snacks, and family dessert boxes.", "price": "From ₹499"},
            {"name": "Fresh Bread", "description": "Soft breads and buns baked in small batches.", "price": "From ₹199"},
        ],
        "grocery": [
            {"name": "Daily Essentials", "description": "Groceries, grains, and local pantry staples.", "price": "Home delivery"},
            {"name": "Fresh Produce", "description": "Seasonal vegetables, fruits, and farm-fresh produce.", "price": "Picked daily"},
            {"name": "Family Packs", "description": "Value bundles for homes and small businesses.", "price": "Savings up to 20%"},
        ],
        "salon": [
            {"name": "Hair Styling", "description": "Cuts, trims, and advanced styling sessions.", "price": "From ₹499"},
            {"name": "Skin Facials", "description": "Relaxing facials and glow-boosting treatments.", "price": "From ₹999"},
            {"name": "Bridal Packages", "description": "Complete pre-wedding beauty and grooming care.", "price": "From ₹3,499"},
        ],
        "restaurant": [
            {"name": "Chef Specials", "description": "Signature dishes and chef-crafted favorites.", "price": "From ₹299"},
            {"name": "Family Meal", "description": "Healthy, filling meals designed for groups.", "price": "From ₹999"},
            {"name": "Quick Bites", "description": "Fast snacks, desserts, and takeaway specials.", "price": "From ₹149"},
        ],
    }
    return defaults.get(industry, [
        {"name": "Featured Service", "description": "High-quality service built for faster growth and better customer trust.", "price": "Custom"},
        {"name": "Popular Offer", "description": "Easy-to-order local solutions tailored to everyday customer needs.", "price": "Flexible"},
        {"name": "Value Package", "description": "Hands-on support and consistent follow-through for local buyers.", "price": "Ready to book"},
    ])


def _generate_site_payload(transcript: str, language: str, business_name: str | None = None, location: str | None = None, industry: str | None = None) -> dict[str, Any]:
    industry_key = (industry or _infer_industry(transcript)).lower()
    theme = THEME_LIBRARY.get(industry_key, THEME_LIBRARY["default"])
    business_label = _extract_business_name(transcript, business_name)

    customer_location = location.strip() if location else "Your local market"
    summary_text = transcript.strip() or f"{business_label} brings trusted service and high-quality products to customers in {customer_location}."
    summary_text = re.sub(r"\s+", " ", summary_text).strip()

    hero_headline = f"Fresh, trusted service for {customer_location}."
    if industry_key == "salon":
        hero_headline = f"Style that feels personal, modern, and memorable."
    elif industry_key == "restaurant":
        hero_headline = f"Food that brings people back for more."
    elif industry_key == "grocery":
        hero_headline = f"Everyday essentials, delivered with care."

    products = _build_default_products(industry_key)
    about_text = (
        f"{business_label} is a {theme['description']} serving customers who value quality, convenience, and trust. "
        f"Built around a warm local experience, the business combines reliability with friendly service and a clear focus on customer satisfaction."
    )

    return {
        "business_name": business_label,
        "industry": industry_key,
        "language": language,
        "tagline": f"Your neighborhood {industry_key} experience — modern, trustworthy, and customer-first.",
        "theme": {
            "primary": theme["primary"],
            "secondary": theme["secondary"],
            "accent": theme["accent"],
            "hero_gradient": theme["hero_gradient"],
        },
        "sections": {
            "hero": {
                "headline": hero_headline,
                "description": summary_text[:220],
                "cta_primary": "Shop Now",
                "cta_secondary": "Book a Visit",
            },
            "about": {
                "title": "About Us",
                "description": about_text,
                "highlights": [
                    "Community-first approach",
                    "Reliable local service",
                    "Professional presentation",
                ],
            },
            "products": {
                "title": "Products & Services",
                "items": products,
            },
            "contact": {
                "title": "Contact",
                "phone": "+91 98765 43210",
                "email": "hello@yourbusiness.co.in",
                "address": f"Main market road, {customer_location}",
                "business_hours": "Mon-Sat: 9:00 AM - 9:00 PM",
            },
        },
    }


@router.post("/voice/transcribe")
async def transcribe_voice(
    file: UploadFile = File(...),
    language: str = Form("en"),
) -> dict[str, Any]:
    normalized_language = (language or "en").lower()
    if normalized_language not in SUPPORTED_LANGUAGES:
        normalized_language = "en"

    api_key = settings.openai_api_key
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="OPENAI_API_KEY is not configured. Add it to your backend .env file.",
        )

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="No audio data was provided.")

    try:
        response = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={
                "Authorization": f"Bearer {api_key}",
            },
            files={
                "file": (
                    file.filename or "voice-note.webm",
                    audio_bytes,
                    file.content_type or "audio/webm",
                )
            },
            data={
                "model": settings.openai_transcription_model,
                "language": normalized_language,
            },
            timeout=60,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=503, detail=f"OpenAI transcription request failed: {exc}") from exc

    payload = response.json() if response.content else {}
    if response.status_code >= 400:
        error_message = payload.get("error", {}).get("message", payload.get("message", "Transcription failed."))
        raise HTTPException(status_code=response.status_code, detail=error_message)

    transcript = payload.get("text", "")
    return {
        "text": transcript,
        "language": normalized_language,
        "language_label": SUPPORTED_LANGUAGES[normalized_language],
    }


@router.post("/voice/process")
def process_voice_transcript(payload: VoiceProcessingRequest | dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload, dict):
        payload = VoiceProcessingRequest(**payload)

    transcript = payload.transcript.strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript cannot be empty.")

    language_label = SUPPORTED_LANGUAGES.get((payload.language or "en").lower(), "English")
    website = _generate_site_payload(
        transcript=transcript,
        language=payload.language or "en",
        business_name=payload.business_name,
        location=payload.location,
        industry=payload.industry,
    )

    return {
        "status": "queued",
        "summary": f"Transcript received in {language_label} and queued for AI website generation.",
        "transcript": transcript,
        "website": website,
    }

