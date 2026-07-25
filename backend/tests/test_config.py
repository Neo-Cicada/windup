import pytest
from pydantic import ValidationError

from app.core.config import DEV_SECRET_KEY, Settings

# The .env on disk would otherwise leak into these constructions.
BASE = {"_env_file": None, "DATABASE_URL": "postgresql+asyncpg://u@localhost/db"}


def test_dev_tolerates_the_placeholder_secret() -> None:
    settings = Settings(**BASE, ENV="development")
    assert settings.SECRET_KEY == DEV_SECRET_KEY


@pytest.mark.parametrize("env", ["production", "staging"])
def test_placeholder_secret_refuses_to_boot_outside_dev(env: str) -> None:
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(**BASE, ENV=env, SECRET_KEY=DEV_SECRET_KEY)


def test_short_secret_refuses_to_boot_outside_dev() -> None:
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(**BASE, ENV="production", SECRET_KEY="too-short")


def test_strong_secret_boots_in_production() -> None:
    strong = "x" * 48
    assert Settings(**BASE, ENV="production", SECRET_KEY=strong).SECRET_KEY == strong


def test_wildcard_cors_refused_outside_dev() -> None:
    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        Settings(**BASE, ENV="production", SECRET_KEY="x" * 48, CORS_ORIGINS="*")


def test_comma_separated_origins_are_split() -> None:
    settings = Settings(**BASE, CORS_ORIGINS="http://a.test, http://b.test")
    assert settings.CORS_ORIGINS == ["http://a.test", "http://b.test"]
