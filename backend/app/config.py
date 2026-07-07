"""Application configuration loaded from environment variables (.env)."""
from __future__ import annotations

from functools import lru_cache

from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    """Centralized settings, read once from environment variables."""

    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./farmacia.db")
    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5500",
        ).split(",")
        if origin.strip()
    ]
    dias_alerta_validade: int = int(os.getenv("DIAS_ALERTA_VALIDADE", "15"))

    # Secret: Mercado Pago access token. Only ever read from the environment —
    # never exposed or editable via API/frontend. See .env.example for how to
    # obtain a sandbox/test token.
    mercadopago_access_token: str | None = os.getenv("MERCADOPAGO_ACCESS_TOKEN") or None
    mercadopago_api_base_url: str = os.getenv(
        "MERCADOPAGO_API_BASE_URL", "https://api.mercadopago.com"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
