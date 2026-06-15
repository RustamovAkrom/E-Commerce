"""Auth endpoint tests: registration, login, refresh rotation, logout."""

from __future__ import annotations

from httpx import AsyncClient

AUTH = "/api/v1/auth"


async def _register(
    client: AsyncClient, email: str, password: str = "password123"
) -> dict:
    resp = await client.post(
        f"{AUTH}/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    return resp


async def test_register_success(client: AsyncClient) -> None:
    resp = await _register(client, "newuser@example.com")
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["user"]["email"] == "newuser@example.com"
    assert body["user"]["role"] == "customer"
    assert body["tokens"]["access_token"]
    assert body["tokens"]["refresh_token"]
    assert body["tokens"]["token_type"] == "bearer"


async def test_register_duplicate_email(client: AsyncClient) -> None:
    first = await _register(client, "dup@example.com")
    assert first.status_code == 201, first.text

    second = await _register(client, "dup@example.com")
    # The API surfaces a duplicate as 409 Conflict (AlreadyExistsError).
    assert second.status_code == 409, second.text
    assert second.json()["error"] == "already_exists"


async def test_login_success(client: AsyncClient) -> None:
    await _register(client, "login@example.com")
    # OAuth2 password flow: form-encoded ``username`` / ``password``.
    resp = await client.post(
        f"{AUTH}/login",
        data={"username": "login@example.com", "password": "password123"},
    )
    assert resp.status_code == 200, resp.text
    tokens = resp.json()["tokens"]
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["expires_in"] > 0


async def test_login_wrong_password(client: AsyncClient) -> None:
    await _register(client, "wrongpass@example.com")
    resp = await client.post(
        f"{AUTH}/login",
        data={"username": "wrongpass@example.com", "password": "not-the-password"},
    )
    assert resp.status_code == 401, resp.text


async def test_refresh_token(client: AsyncClient) -> None:
    reg = await _register(client, "refresh@example.com")
    refresh_token = reg.json()["tokens"]["refresh_token"]

    resp = await client.post(
        f"{AUTH}/refresh", json={"refresh_token": refresh_token}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    # Rotation: the new refresh token differs from the one presented.
    assert body["refresh_token"] != refresh_token


async def test_logout(client: AsyncClient) -> None:
    reg = await _register(client, "logout@example.com")
    tokens = reg.json()["tokens"]
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    out = await client.post(
        f"{AUTH}/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers=headers,
    )
    assert out.status_code == 200, out.text

    # The access token's jti is now blacklisted: a protected call is rejected.
    protected = await client.get("/api/v1/cart", headers=headers)
    assert protected.status_code == 401, protected.text
