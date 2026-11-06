import os

from app.api.routes.transcription import process_voice_transcript
from app.config import Settings


def test_production_settings_define_safe_runtime_defaults():
    os.environ["APP_ENV"] = "production"
    os.environ["FRONTEND_URL"] = "https://app.example.com"
    os.environ["CORS_ORIGINS"] = '["https://app.example.com","https://www.app.example.com"]'
    os.environ["ALLOWED_HOSTS"] = '["app.example.com","www.app.example.com"]'

    config = Settings()

    assert config.app_env == "production"
    assert config.debug is False
    assert config.log_level == "INFO"
    assert config.allowed_hosts == ["app.example.com", "www.app.example.com"]
    assert config.cors_origins == ["https://app.example.com", "https://www.app.example.com"]


def test_multilingual_voice_processing_keeps_language_and_defaults():
    payload = {
        "transcript": "मैं अपनी मिठाई की दुकान शुरू करना चाहता हूँ",
        "language": "hi",
        "business_name": "Rajat Sweets",
        "location": "Ahmedabad",
        "industry": "bakery",
    }

    result = process_voice_transcript(payload)

    assert result["transcript"] == payload["transcript"]
    assert result["website"]["language"] == "hi"
    assert result["website"]["industry"] == "bakery"
    assert result["website"]["business_name"] == "Rajat Sweets"
