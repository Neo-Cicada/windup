from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# The in-code fallback. Safe for local work, fatal anywhere else — see _reject_insecure_secret.
DEV_SECRET_KEY = "change-me-in-production-please-really"


class Settings(BaseSettings):
    """Runtime configuration, read from the environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ENV: str = "development"
    PROJECT_NAME: str = "Windup Academy API"
    API_V1_PREFIX: str = "/api/v1"

    # postgresql+asyncpg://user:password@host:port/dbname
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/windup"
    DB_ECHO: bool = False

    SECRET_KEY: str = DEV_SECRET_KEY
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    JWT_ALGORITHM: str = "HS256"

    # NoDecode so a plain comma-separated env value is handled by the validator below.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    # Gameplay tuning — mirrors the numbers the frontend animates with.
    STARTING_XP_MAX: int = 500
    XP_MAX_GROWTH: float = 1.12
    XP_SOLVE_UNAIDED: int = 120
    XP_SOLVE_AIDED: int = 60
    XP_WIND_UP: int = 40
    COINS_PER_XP_DIVISOR: int = 4
    BOSS_DURATION_SECONDS: int = 900
    DAILY_QUESTS: int = 3

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, v: object) -> object:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @model_validator(mode="after")
    def _reject_insecure_secret(self) -> "Settings":
        """Refuse to boot outside development with a guessable JWT signing key.

        The fallback above is committed to the repo, so anyone could forge a token for
        any user id. Failing startup is far better than silently signing with it.
        """
        if self.ENV == "development":
            return self
        if self.SECRET_KEY == DEV_SECRET_KEY or len(self.SECRET_KEY) < 32:
            raise ValueError(
                f"SECRET_KEY must be set to a unique value of at least 32 characters when "
                f"ENV={self.ENV!r}. Generate one with: "
                'python -c "import secrets; print(secrets.token_urlsafe(48))"'
            )
        return self

    @model_validator(mode="after")
    def _reject_wildcard_cors_with_credentials(self) -> "Settings":
        """`*` plus credentials is the combination browsers refuse; fail loudly instead."""
        if "*" in self.CORS_ORIGINS and self.ENV != "development":
            raise ValueError("CORS_ORIGINS cannot be '*' outside development.")
        return self

    @property
    def sync_database_url(self) -> str:
        """Alembic runs migrations synchronously."""
        return self.DATABASE_URL.replace("+asyncpg", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
