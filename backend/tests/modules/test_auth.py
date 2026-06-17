"""Auth endpoint tests: register, login, refresh, logout, and edge cases."""

from __future__ import annotations

import uuid

import jwt
from httpx import AsyncClient
from src.config import settings
from src.core.security import decode_token

AUTH = "/api/v1/auth"


# ─── Helpers ────────────────────────────────────────────────────────────────

async def _register(
    client: AsyncClient, email: str, password: str = "password123"
) -> dict:
    resp = await client.post(
        f"{AUTH}/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    return resp


# ─── Registration ──────────────────────────────────────────────────────────

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
    assert second.status_code == 409, second.text
    assert second.json()["error"] == "already_exists"


async def test_register_minimal_fields(client: AsyncClient) -> None:
    """Only email + password are mandatory; full_name and phone default to null."""
    resp = await client.post(
        f"{AUTH}/register",
        json={"email": "minimal@example.com", "password": "strongpass1"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["tokens"]["access_token"]
    assert body["tokens"]["refresh_token"]


async def test_register_weak_password(client: AsyncClient) -> None:
    resp = await client.post(
        f"{AUTH}/register",
        json={"email": "weak@example.com", "password": "short"},
    )
    assert resp.status_code == 422, resp.text


# ─── Login ──────────────────────────────────────────────────────────────────

async def test_login_success(client: AsyncClient) -> None:
    await _register(client, "login@example.com")
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


async def test_login_nonexistent_user(client: AsyncClient) -> None:
    resp = await client.post(
        f"{AUTH}/login",
        data={"username": "ghost@example.com", "password": "anything"},
    )
    assert resp.status_code == 401, resp.text


async def test_login_missing_password(client: AsyncClient) -> None:
    """OAuth2 form without password returns 422 (Pydantic validation) or 401."""
    resp = await client.post(
        f"{AUTH}/login",
        data={"username": "a@example.com", "password": ""},
    )
    assert resp.status_code in (401, 422), resp.text


# ─── Refresh ────────────────────────────────────────────────────────────────

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
    assert body["refresh_token"] != refresh_token


async def test_refresh_token_rotation(client: AsyncClient) -> None:
    """Each refresh issues a new pair and invalidates the old one."""
    reg = await _register(client, "rotate@example.com")
    old_refresh = reg.json()["tokens"]["refresh_token"]

    # First refresh
    r1 = await client.post(
        f"{AUTH}/refresh", json={"refresh_token": old_refresh}
    )
    assert r1.status_code == 200, r1.text
    tokens1 = r1.json()

    # Second refresh with the NEW token
    r2 = await client.post(
        f"{AUTH}/refresh", json={"refresh_token": tokens1["refresh_token"]}
    )
    assert r2.status_code == 200, r2.text
    tokens2 = r2.json()

    # The old token must no longer work
    stale = await client.post(
        f"{AUTH}/refresh", json={"refresh_token": tokens1["refresh_token"]}
    )
    assert stale.status_code == 401, stale.text

    # New tokens keep changing
    assert tokens2["refresh_token"] != tokens1["refresh_token"]


async def test_refresh_invalid_token(client: AsyncClient) -> None:
    resp = await client.post(
        f"{AUTH}/refresh", json={"refresh_token": "totally.fake.token"}
    )
    assert resp.status_code == 401, resp.text


async def test_refresh_empty_body(client: AsyncClient) -> None:
    resp = await client.post(f"{AUTH}/refresh", json={})
    assert resp.status_code == 422, resp.text


async def test_refresh_access_token_as_refresh(client: AsyncClient) -> None:
    """Using an access token where a refresh is expected → 401."""
    reg = await _register(client, "wrong_type@example.com")
    access_token = reg.json()["tokens"]["access_token"]

    resp = await client.post(
        f"{AUTH}/refresh", json={"refresh_token": access_token}
    )
    assert resp.status_code == 401, resp.text


async def test_refresh_expired_token(client: AsyncClient) -> None:
    """Craft a token with a past expiry → decode raises PyJWTError → 401."""
    expired_payload = {
        "sub": str(uuid.uuid4()),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": decode_token.__module__,  # dummy
        "exp": 1000000000,  # 2001 — definitely expired
    }
    expired_jwt = jwt.encode(
        expired_payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    resp = await client.post(
        f"{AUTH}/refresh", json={"refresh_token": expired_jwt}
    )
    assert resp.status_code == 401, resp.text


async def test_refresh_revoked_token(client: AsyncClient) -> None:
    """Token that was already used in a refresh → should be invalidated."""
    reg = await _register(client, "revoke@example.com")
    refresh_token = reg.json()["tokens"]["refresh_token"]

    # First refresh consumes it
    r1 = await client.post(
        f"{AUTH}/refresh", json={"refresh_token": refresh_token}
    )
    assert r1.status_code == 200

    # Same token again → revoked
    r2 = await client.post(
        f"{AUTH}/refresh", json={"refresh_token": refresh_token}
    )
    assert r2.status_code == 401, r2.text


# ─── Logout ─────────────────────────────────────────────────────────────────

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

    protected = await client.get("/api/v1/cart", headers=headers)
    assert protected.status_code == 401, protected.text


async def test_logout_without_access_token(client: AsyncClient) -> None:
    """Logout still invalidates the refresh token even without an access token."""
    reg = await _register(client, "nacctn@example.com")
    tokens = reg.json()["tokens"]

    out = await client.post(
        f"{AUTH}/logout",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert out.status_code == 200, out.text

    # Refresh should fail after logout
    r = await client.post(
        f"{AUTH}/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert r.status_code == 401, r.text


# ─── Telegram Auth ─────────────────────────────────────────────────────────

async def test_telegram_auth_success(client: AsyncClient, monkeypatch: object) -> None:
    import hmac

    monkeypatch.setattr(settings, "TELEGRAM_AUTH_SECRET", "test-secret")
    monkeypatch.setattr(settings, "BOT_TOKEN", "123:ABC")

    resp = await client.post(
        f"{AUTH}/telegram",
        json={
            "telegram_id": 42,
            "full_name": "TG User",
            "auth_secret": "test-secret",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user"]["role"] == "customer"
    assert body["tokens"]["access_token"]


async def test_telegram_auth_bad_secret(client: AsyncClient, monkeypatch: object) -> None:
    monkeypatch.setattr(settings, "TELEGRAM_AUTH_SECRET", "correct-secret")
    resp = await client.post(
        f"{AUTH}/telegram",
        json={
            "telegram_id": 42,
            "full_name": "TG User",
            "auth_secret": "wrong-secret",
        },
    )
    assert resp.status_code == 401, resp.text


# ─── Health & System ────────────────────────────────────────────────────────

async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body
