"""Tests for User CRUD endpoints."""

from httpx import AsyncClient

from tests.conftest import create_test_user, create_user_and_login


class TestGetMe:
    """Tests for GET /api/v1/users/me."""

    async def test_get_me_success(self, client: AsyncClient) -> None:
        user_data, headers, _ = await create_user_and_login(client)
        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"

    async def test_get_me_unauthenticated(self, client: AsyncClient) -> None:
        """Without Authorization header, HTTPBearer returns 401."""
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401


class TestListUsers:
    """Tests for GET /api/v1/users."""

    async def test_list_users_success(self, client: AsyncClient) -> None:
        _, headers, _ = await create_user_and_login(client)
        # Create a second user
        await create_test_user(
            client, email="user2@example.com", username="user2", password="TestPass123!"
        )

        response = await client.get("/api/v1/users", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["users"]) == 2
        assert data["page"] == 1
        assert data["per_page"] == 20

    async def test_list_users_pagination(self, client: AsyncClient) -> None:
        _, headers, _ = await create_user_and_login(client)
        # Create additional users
        for i in range(3):
            await create_test_user(
                client,
                email=f"user{i}@example.com",
                username=f"user{i}",
                password="TestPass123!",
            )

        response = await client.get(
            "/api/v1/users", params={"page": 1, "per_page": 2}, headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert len(data["users"]) == 2

    async def test_list_users_unauthenticated(self, client: AsyncClient) -> None:
        """Without Authorization header, HTTPBearer returns 401."""
        response = await client.get("/api/v1/users")
        assert response.status_code == 401


class TestGetUser:
    """Tests for GET /api/v1/users/{user_id}."""

    async def test_get_user_by_id(self, client: AsyncClient) -> None:
        user_data, headers, _ = await create_user_and_login(client)
        user_id = user_data["id"]

        response = await client.get(f"/api/v1/users/{user_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_id
        assert data["email"] == "test@example.com"

    async def test_get_user_not_found(self, client: AsyncClient) -> None:
        _, headers, _ = await create_user_and_login(client)
        response = await client.get(
            "/api/v1/users/nonexistent-id-12345", headers=headers
        )
        assert response.status_code == 404


class TestUpdateMe:
    """Tests for PATCH /api/v1/users/me."""

    async def test_update_full_name(self, client: AsyncClient) -> None:
        _, headers, _ = await create_user_and_login(client)
        response = await client.patch(
            "/api/v1/users/me",
            json={"full_name": "Updated Name"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated Name"

    async def test_update_email(self, client: AsyncClient) -> None:
        _, headers, _ = await create_user_and_login(client)
        response = await client.patch(
            "/api/v1/users/me",
            json={"email": "newemail@example.com"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["email"] == "newemail@example.com"

    async def test_update_email_conflict(self, client: AsyncClient) -> None:
        _, headers, _ = await create_user_and_login(client)
        await create_test_user(
            client, email="taken@example.com", username="other", password="TestPass123!"
        )

        response = await client.patch(
            "/api/v1/users/me",
            json={"email": "taken@example.com"},
            headers=headers,
        )
        assert response.status_code == 409

    async def test_update_username_conflict(self, client: AsyncClient) -> None:
        _, headers, _ = await create_user_and_login(client)
        await create_test_user(
            client, email="other@example.com", username="taken", password="TestPass123!"
        )

        response = await client.patch(
            "/api/v1/users/me",
            json={"username": "taken"},
            headers=headers,
        )
        assert response.status_code == 409


class TestDeleteMe:
    """Tests for DELETE /api/v1/users/me."""

    async def test_delete_me_success(self, client: AsyncClient) -> None:
        _, headers, _ = await create_user_and_login(client)
        response = await client.delete("/api/v1/users/me", headers=headers)
        assert response.status_code == 204

        # Verify user is gone -- token should now be invalid
        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401

    async def test_delete_me_unauthenticated(self, client: AsyncClient) -> None:
        """Without Authorization header, HTTPBearer returns 401."""
        response = await client.delete("/api/v1/users/me")
        assert response.status_code == 401
