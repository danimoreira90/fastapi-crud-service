"""Tests for authentication endpoints: register, login, refresh, logout."""

from httpx import AsyncClient

from tests.conftest import create_test_user, create_user_and_login


class TestRegister:
    """Tests for POST /api/v1/auth/register."""

    async def test_register_success(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "SecurePass123!",
                "full_name": "New User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert data["full_name"] == "New User"
        assert data["is_active"] is True
        assert data["is_superuser"] is False
        assert "id" in data
        assert "hashed_password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient) -> None:
        await create_test_user(client, email="dup@example.com", username="user1")
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "dup@example.com",
                "username": "user2",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 409
        assert "Email already registered" in response.json()["detail"]

    async def test_register_duplicate_username(self, client: AsyncClient) -> None:
        await create_test_user(client, email="a@example.com", username="sameuser")
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "b@example.com",
                "username": "sameuser",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 409
        assert "Username already taken" in response.json()["detail"]

    async def test_register_invalid_email(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "username": "user",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 422

    async def test_register_short_password(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "a@example.com",
                "username": "user",
                "password": "short",
            },
        )
        assert response.status_code == 422

    async def test_register_invalid_username(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "a@example.com",
                "username": "no spaces!",
                "password": "SecurePass123!",
            },
        )
        assert response.status_code == 422


class TestLogin:
    """Tests for POST /api/v1/auth/login."""

    async def test_login_success(self, client: AsyncClient) -> None:
        await create_test_user(client)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "TestPass123!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient) -> None:
        await create_test_user(client)
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "WrongPass123!"},
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    async def test_login_nonexistent_user(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "noone@example.com", "password": "Whatever123!"},
        )
        assert response.status_code == 401


class TestRefresh:
    """Tests for POST /api/v1/auth/refresh."""

    async def test_refresh_success(self, client: AsyncClient) -> None:
        _, _, login_data = await create_user_and_login(client)
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": login_data["refresh_token"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # New refresh token should be different (rotation via jti)
        assert data["refresh_token"] != login_data["refresh_token"]

    async def test_refresh_with_revoked_token(self, client: AsyncClient) -> None:
        _, _, login_data = await create_user_and_login(client)
        # Use it once (rotates it -- old one gets revoked)
        await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": login_data["refresh_token"]},
        )
        # Try to use the old one again
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": login_data["refresh_token"]},
        )
        assert response.status_code == 401

    async def test_refresh_with_invalid_token(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "completely-invalid-token"},
        )
        assert response.status_code == 401


class TestLogout:
    """Tests for POST /api/v1/auth/logout."""

    async def test_logout_success(self, client: AsyncClient) -> None:
        _, headers, login_data = await create_user_and_login(client)
        response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": login_data["refresh_token"]},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"

    async def test_logout_requires_auth(self, client: AsyncClient) -> None:
        """Without Authorization header, HTTPBearer returns 401."""
        response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "some-token"},
        )
        assert response.status_code == 401


class TestHealthCheck:
    """Tests for GET /health."""

    async def test_health_check(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
