"""Test fixtures.

Tests run against a throwaway database (default `windup_test`); override with
TEST_DATABASE_URL. Tables are created once per session and truncated per test.
"""

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", settings.DATABASE_URL.rsplit("/", 1)[0] + "/windup_test"
)

test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=None)
TestSession = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
async def _schema() -> AsyncGenerator[None, None]:
    from app.models import Base

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()


@pytest.fixture(autouse=True)
async def _clean() -> AsyncGenerator[None, None]:
    from app.models import Base

    tables = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    async with test_engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSession() as session:
        yield session


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    from app.db.session import get_db
    from app.main import app

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def seeded(db: AsyncSession) -> None:
    from app.db.seed import seed_catalogue

    await seed_catalogue(db)


@pytest.fixture
async def auth(client: AsyncClient, seeded: None) -> dict[str, str]:
    """A signed-up toy's Authorization header."""
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"toy_name": "Patches", "email": "patches@playroom.com", "password": "windup123"},
    )
    assert resp.status_code == 201, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
