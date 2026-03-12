"""Authentication endpoints: register, login, refresh, logout."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    TokenResponse,
)
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    revoke_refresh_token,
    store_refresh_token,
    validate_refresh_token,
    verify_password,
)
from app.services.user import create_user, get_user_by_email, get_user_by_username

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Register a new user account."""
    # Check email uniqueness
    existing = await get_user_by_email(db, user_in.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Check username uniqueness
    existing = await get_user_by_username(db, user_in.username)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken",
        )

    user = await create_user(db, user_in)
    logger.info("User registered: %s", user.email)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Authenticate user and return JWT token pair."""
    user = await get_user_by_email(db, credentials.email)
    if user is None or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    access_token = create_access_token(user.id)
    refresh_token, expires_at = create_refresh_token(user.id)

    await store_refresh_token(db, user.id, refresh_token, expires_at)

    logger.info("User logged in: %s", user.email)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Exchange a valid refresh token for a new token pair."""
    db_token = await validate_refresh_token(db, body.refresh_token)
    if db_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Revoke the old refresh token (rotation)
    await revoke_refresh_token(db, body.refresh_token)

    # Issue new pair
    access_token = create_access_token(db_token.user_id)
    new_refresh_token, expires_at = create_refresh_token(db_token.user_id)
    await store_refresh_token(db, db_token.user_id, new_refresh_token, expires_at)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout", response_model=MessageResponse)
async def logout(
    body: RefreshRequest,
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Revoke the provided refresh token."""
    revoked = await revoke_refresh_token(db, body.refresh_token)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token not found or already revoked",
        )
    return {"message": "Successfully logged out"}
