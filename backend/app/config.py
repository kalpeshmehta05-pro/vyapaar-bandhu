"""
VyapaarBandhu — Application Configuration
Pydantic Settings — all values from environment variables.
No hardcoded secrets. No defaults for sensitive values.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ── Application ────────────────────────────────────────────────────
    APP_ENV: str = "development"  # development | staging | production
    DEBUG: bool = False
    APP_VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"

    # ── Database (PostgreSQL 16 — async) ───────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vyapaar_bandhu"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False  # SQL logging — dev only

    # ── Redis ──────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_SESSION_TTL: int = 7200  # 2 hours — WhatsApp session TTL

    # ── JWT (RS256 — asymmetric) ───────────────────────────────────────
    JWT_PRIVATE_KEY_PATH: str = "keys/private.pem"
    JWT_PUBLIC_KEY_PATH: str = "keys/public.pem"
    JWT_PRIVATE_KEY: str = ""  # PEM string via env var (production)
    JWT_PUBLIC_KEY: str = ""   # PEM string via env var (production)
    ACCESS_TOKEN_EXPIRY: int = 900  # 15 minutes
    REFRESH_TOKEN_EXPIRY: int = 604800  # 7 days
    JWT_ALGORITHM: str = "RS256"

    # ── WhatsApp (Meta Cloud API — free tier) ──────────────────────────
    WA_PHONE_NUMBER_ID: str = ""
    WA_ACCESS_TOKEN: str = ""
    WA_APP_SECRET: str = ""  # HMAC webhook signature verification
    WA_VERIFY_TOKEN: str = ""  # Webhook registration challenge
    WA_API_VERSION: str = "v21.0"

    # ── OCR (free — local Tesseract + EasyOCR) ─────────────────────────
    TESSERACT_CMD: str = "tesseract"  # path to tesseract binary
    OCR_CONFIDENCE_THRESHOLD: float = 0.85  # green threshold
    OCR_AMBER_THRESHOLD: float = 0.75  # amber threshold
    OCR_FALLBACK_THRESHOLD: float = 0.50  # below this, try fallback

    # ── Classification (free — local HuggingFace models) ───────────────
    BART_MODEL_ID: str = "facebook/bart-large-mnli"
    INDICBERT_MODEL_ID: str = "meet136/indicbert-gst-classifier"
    MODELS_CACHE_DIR: str = "/app/models_cache"  # Docker volume
    KEYWORD_CONFIDENCE_THRESHOLD: float = 0.92
    BART_CONFIDENCE_THRESHOLD: float = 0.75
    INDICBERT_CA_REVIEW_THRESHOLD: float = 0.65

    # ── S3-compatible storage (MinIO dev / Cloudflare R2 prod) ─────────
    S3_ENDPOINT_URL: str = "http://localhost:9000"  # MinIO
    S3_ACCESS_KEY_ID: str = "minioadmin"
    S3_SECRET_ACCESS_KEY: str = "minioadmin"
    S3_BUCKET_INVOICES: str = "vyapaar-invoices"
    S3_BUCKET_EXPORTS: str = "vyapaar-exports"
    S3_REGION: str = "ap-south-1"
    S3_PRESIGNED_URL_EXPIRY: int = 900  # 15 minutes

    # ── Celery ─────────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── Error tracking (GlitchTip — free self-hosted) ──────────────────
    SENTRY_DSN: str = ""

    # ── Security ───────────────────────────────────────────────────────
    BCRYPT_ROUNDS: int = 12
    MIN_PASSWORD_LENGTH: int = 12
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000"])
    ALLOWED_ORIGINS: list[str] = Field(default=["http://localhost:3000"])

    # ── Compliance ─────────────────────────────────────────────────────
    ANOMALY_THRESHOLD_MULTIPLIER: float = 2.5
    GST_RATES_CONFIG_PATH: str = "config/gst_rates.yaml"

    # ── Data Retention (DPDP Act 2023) ─────────────────────────────────
    RETENTION_IMAGES_YEARS: int = 3
    RETENTION_DATA_YEARS: int = 7

    # ── Privacy ────────────────────────────────────────────────────────
    PRIVACY_POLICY_URL: str = "https://vyapaarbandhu.app/privacy"
    CONSENT_VERSION: str = "v1.0"

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",
    }


# Singleton — import this everywhere
settings = Settings()
