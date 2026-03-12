"""Authentication service: JWT creation/validation, password hashing."""

import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import RefreshToken


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(user_id: str) -> str:
    """Create a short-lived JWT access token."""
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "access",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: str) -> tuple[str, datetime]:
    """Create a long-lived JWT refresh token. Returns (token, expires_at)."""
    expire = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expire


def decode_token(token: str) -> dict[str, str | int]:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    try:
        payload: dict[str, str | int] = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        raise


async def store_refresh_token(
    db: AsyncSession,
    user_id: str,
    token: str,
    expires_at: datetime,
) -> RefreshToken:
    """Store a refresh token in the database."""
    db_token = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(db_token)
    await db.flush()
    return db_token


async def revoke_refresh_token(db: AsyncSession, token: str) -> bool:
    """Revoke a refresh token. Returns True if found and revoked."""
    result = await db.execute(
        select(RefreshToken)
        .where(RefreshToken.token == token)
        .where(RefreshToken.revoked.is_(False))
    )
    db_token = result.scalar_one_or_none()
    if db_token is None:
        return False
    db_token.revoked = True
    await db.flush()
    return True


async def validate_refresh_token(db: AsyncSession, token: str) -> RefreshToken | None:
    """Validate a refresh token exists, is not revoked, and not expired."""
    result = await db.execute(
        select(RefreshToken)
        .where(RefreshToken.token == token)
        .where(RefreshToken.revoked.is_(False))
    )
    db_token = result.scalar_one_or_none()
    if db_token is None:
        return None
    if db_token.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        return None
    return db_token
