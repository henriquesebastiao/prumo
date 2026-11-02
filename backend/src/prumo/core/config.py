from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Instance configuration, read from `PRUMO_*` environment variables (or a `.env` file)."""

    model_config = SettingsConfigDict(
        env_prefix="PRUMO_",
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://prumo:prumo@localhost:5432/prumo"

    cookie_secure: bool = True
    session_days_web: int = 30
    session_days_app: int = 180
    session_hours_web_transient: int = 12

    login_max_failures: int = 5
    login_window_minutes: int = 15
    login_lockout_minutes: int = 15

    default_timezone: str = "America/Sao_Paulo"
    default_locale: str = "pt-BR"
    default_currency: str = "BRL"

    uploads_dir: Path = Path("/data/uploads")
    cors_origins: Annotated[list[str], NoDecode] = []

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
