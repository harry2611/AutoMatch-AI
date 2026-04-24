from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AutoMatch AI API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://automatch:automatch@db:5432/automatch"
    redis_url: str = "redis://redis:6379/0"
    secret_key: str = "change-me-in-local-dev"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    seed_demo_data: bool = True
    scheduler_enabled: bool = True
    api_cors_origins: list[str] = ["http://localhost:3000"]

    @field_validator("api_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        return [origin.strip() for origin in value.split(",") if origin.strip()]


settings = Settings()

