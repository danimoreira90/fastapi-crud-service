"""Authentication Pydantic schemas."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Schema for login credentials."""

    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    """Schema for JWT token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Schema for token refresh."""

    refresh_token: str


class TokenPayload(BaseModel):
    """Decoded JWT token payload."""

    sub: str
    exp: int
    type: str  # "access" or "refresh"


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
