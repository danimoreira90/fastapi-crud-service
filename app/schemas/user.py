"""User Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr
    username: str = Field(min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserUpdate(BaseModel):
    """Schema for updating an existing user. All fields optional."""

    email: EmailStr | None = None
    username: str | None = Field(
        default=None, min_length=3, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$"
    )
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class UserResponse(BaseModel):
    """Schema for user in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    username: str
    full_name: str | None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    """Paginated list of users."""

    users: list[UserResponse]
    total: int
    page: int
    per_page: int
