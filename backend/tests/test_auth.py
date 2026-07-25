from httpx import AsyncClient


async def test_signup_returns_tokens_and_toy(client: AsyncClient, seeded: None) -> None:
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"toy_name": "Bolt", "email": "Bolt@Playroom.com", "password": "windup123"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["access_token"] and body["refresh_token"]
    assert body["user"]["toy_name"] == "Bolt"
    assert body["user"]["email"] == "bolt@playroom.com"  # normalised
    assert body["user"]["plan"] == "free"
    assert len(body["user"]["trainee_no"]) == 4


async def test_duplicate_email_is_rejected(client: AsyncClient, seeded: None) -> None:
    payload = {"toy_name": "Bolt", "email": "bolt@playroom.com", "password": "windup123"}
    assert (await client.post("/api/v1/auth/signup", json=payload)).status_code == 201
    assert (await client.post("/api/v1/auth/signup", json=payload)).status_code == 409


async def test_short_password_is_rejected(client: AsyncClient, seeded: None) -> None:
    resp = await client.post(
        "/api/v1/auth/signup",
        json={"toy_name": "Bolt", "email": "bolt@playroom.com", "password": "short"},
    )
    assert resp.status_code == 422


async def test_login_and_refresh(client: AsyncClient, seeded: None) -> None:
    await client.post(
        "/api/v1/auth/signup",
        json={"toy_name": "Bolt", "email": "bolt@playroom.com", "password": "windup123"},
    )
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "bolt@playroom.com", "password": "windup123"}
    )
    assert resp.status_code == 200
    refresh = resp.json()["refresh_token"]

    assert (
        await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    ).status_code == 200


async def test_wrong_password_is_401(client: AsyncClient, seeded: None) -> None:
    await client.post(
        "/api/v1/auth/signup",
        json={"toy_name": "Bolt", "email": "bolt@playroom.com", "password": "windup123"},
    )
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "bolt@playroom.com", "password": "nope-nope"}
    )
    assert resp.status_code == 401


async def test_access_token_is_not_accepted_as_refresh(client: AsyncClient, seeded: None) -> None:
    signup = await client.post(
        "/api/v1/auth/signup",
        json={"toy_name": "Bolt", "email": "bolt@playroom.com", "password": "windup123"},
    )
    access = signup.json()["access_token"]
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": access})
    assert resp.status_code == 401


async def test_protected_route_requires_token(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/me")).status_code == 401
    assert (
        await client.get("/api/v1/me", headers={"Authorization": "Bearer nonsense"})
    ).status_code == 401
