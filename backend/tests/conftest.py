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


def solution_for(slug: str) -> str:
    """The seeded reference solution — a submission that ought to pass."""
    from app.db.seed_data import PROBLEMS

    return next(p for p in PROBLEMS if p["slug"] == slug)["solution"]


class Judge:
    """Stands in for the worker process.

    Submitting is asynchronous now, so a test that wants a verdict has to run
    the judge itself. This drains the queue against the test database using the
    same `claim_batch` / `process_one` the real worker uses.
    """

    def __init__(self, client: AsyncClient, auth: dict[str, str]) -> None:
        from app.judge.runner import SubprocessRunner

        self._client = client
        self._auth = auth
        # Subprocess rather than wasm: no 20MB artifact needed, and it's the
        # faster of the two per run. The wasm runner has its own tests.
        self._runner = SubprocessRunner()

    async def drain(self) -> int:
        from app.judge.worker import claim_batch, process_one

        done = 0
        while True:
            async with TestSession() as db:
                ids = [s.id for s in await claim_batch(db, 10)]
            if not ids:
                return done
            for submission_id in ids:
                async with TestSession() as db:
                    await process_one(db, self._runner, submission_id)
                done += 1

    async def submit(self, slug: str, code: str, **extra: object) -> dict:
        """Submit without judging — returns the 202 body."""
        resp = await self._client.post(
            f"/api/v1/problems/{slug}/submit",
            headers=self._auth,
            json={"code": code, **extra},
        )
        assert resp.status_code == 202, resp.text
        return resp.json()

    async def result(self, submission_id: str) -> dict:
        resp = await self._client.get(f"/api/v1/submissions/{submission_id}", headers=self._auth)
        assert resp.status_code == 200, resp.text
        return resp.json()

    async def solve(self, slug: str, code: str | None = None, **extra: object) -> dict:
        """Submit, run the judge, and return the settled result."""
        if code is None:
            code = solution_for(slug)
        accepted = await self.submit(slug, code, **extra)
        await self.drain()
        return await self.result(accepted["submission_id"])


@pytest.fixture
async def judge(client: AsyncClient, auth: dict[str, str]) -> Judge:
    return Judge(client, auth)
