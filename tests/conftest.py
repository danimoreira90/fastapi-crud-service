"""Pytest fixtures: async test client with in-memory SQLite database."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.dependencies import get_db
from app.main import app

# Use aiosqlite for fast in-memory testing (no Docker dependency for unit tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """Create all tables before each test and drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override the DB dependency for testing."""
    async with test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Direct database session for test setup."""
    async with test_session_factory() as session:
        yield session
        await session.commit()


async def create_test_user(
    client: AsyncClient,
    email: str = "test@example.com",
    username: str = "testuser",
    password: str = "TestPass123!",
    full_name: str = "Test User",
) -> dict[str, object]:
    """Helper: register a user and return the response data."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": password,
            "full_name": full_name,
        },
    )
    return response.json()


async def get_auth_headers(
    client: AsyncClient,
    email: str = "test@example.com",
    password: str = "TestPass123!",
) -> dict[str, str]:
    """Helper: login and return Authorization headers."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


async def create_user_and_login(
    client: AsyncClient,
    email: str = "test@example.com",
    username: str = "testuser",
    password: str = "TestPass123!",
) -> tuple[dict[str, object], dict[str, str], dict[str, object]]:
    """Helper: register, login, return (user_data, auth_headers, login_data)."""
    user_data = await create_test_user(client, email=email, username=username, password=password)
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    login_data = login_resp.json()
    headers = {"Authorization": f"Bearer {login_data['access_token']}"}
    return user_data, headers, login_data
