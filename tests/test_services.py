"""Unit tests for service layer functions."""

from datetime import UTC, datetime, timedelta

from jose import jwt

from app.config import settings
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    """Tests for bcrypt password hashing."""

    def test_hash_password_returns_hash(self) -> None:
        hashed = hash_password("mypassword")
        assert hashed != "mypassword"
        assert hashed.startswith("$2b$")

    def test_verify_correct_password(self) -> None:
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_wrong_password(self) -> None:
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False


class TestJWTTokens:
    """Tests for JWT token creation and decoding."""

    def test_create_access_token(self) -> None:
        token = create_access_token("user-123")
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"
        assert "jti" in payload
        assert "exp" in payload

    def test_create_refresh_token(self) -> None:
        token, expires_at = create_refresh_token("user-456")
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        assert payload["sub"] == "user-456"
        assert payload["type"] == "refresh"
        assert "jti" in payload
        assert expires_at > datetime.now(UTC)

    def test_access_token_uniqueness(self) -> None:
        """Two tokens for the same user should differ due to jti."""
        t1 = create_access_token("user-123")
        t2 = create_access_token("user-123")
        assert t1 != t2

    def test_refresh_token_uniqueness(self) -> None:
        """Two refresh tokens for the same user should differ due to jti."""
        t1, _ = create_refresh_token("user-123")
        t2, _ = create_refresh_token("user-123")
        assert t1 != t2

    def test_decode_valid_token(self) -> None:
        token = create_access_token("user-789")
        payload = decode_token(token)
        assert payload["sub"] == "user-789"
        assert payload["type"] == "access"

    def test_decode_invalid_token(self) -> None:
        import pytest
        from jose import JWTError

        with pytest.raises(JWTError):
            decode_token("invalid.token.here")

    def test_decode_expired_token(self) -> None:
        import pytest
        from jose import JWTError

        payload = {
            "sub": "user-expired",
            "exp": datetime.now(UTC) - timedelta(hours=1),
            "type": "access",
        }
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        with pytest.raises(JWTError):
            decode_token(token)
