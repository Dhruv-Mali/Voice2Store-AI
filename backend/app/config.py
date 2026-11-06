from __future__ import annotations

import json
import os
from pathlib import Path


def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = [part.strip() for part in line.split("=", 1)]
        if value and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]

        os.environ.setdefault(key, value)


_load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.app_name = os.getenv("APP_NAME", "Voice2Store AI")
        self.app_env = os.getenv("APP_ENV", "development").lower()
        self.debug = self.app_env not in {"production", "prod"}
        self.backend_port = int(os.getenv("BACKEND_PORT", "8000"))
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        default_domain = self.frontend_url.replace("http://", "").replace("https://", "")
        self.allowed_hosts = self._load_json_list(
            "ALLOWED_HOSTS",
            ["localhost", "127.0.0.1", "0.0.0.0", "testserver", default_domain],
        )
        self.log_level = os.getenv("LOG_LEVEL", "DEBUG" if self.debug else "INFO")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_transcription_model = os.getenv("OPENAI_TRANSCRIPTION_MODEL", "gpt-4o-transcribe")
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "voice2store-dev-secret-key-change-me")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.razorpay_key_id = os.getenv("RAZORPAY_KEY_ID", "")
        self.razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")
        self.razorpay_webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
        self.default_currency = os.getenv("DEFAULT_CURRENCY", "INR")

        default_db = "sqlite:///./voice2store.db" if self.app_env == "test" else "postgresql+psycopg://postgres:postgres@localhost:5432/voice2store"
        self.database_url = os.getenv("DATABASE_URL", default_db)

        self.cors_origins = self._load_json_list("CORS_ORIGINS", [self.frontend_url])

    def _load_json_list(self, env_name: str, fallback: list[str]) -> list[str]:
        raw_value = os.getenv(env_name)
        if raw_value is None:
            return fallback

        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError:
            parsed = [raw_value]

        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]

        if isinstance(parsed, str):
            return [parsed.strip()] if parsed.strip() else fallback

        return fallback


settings = Settings()
