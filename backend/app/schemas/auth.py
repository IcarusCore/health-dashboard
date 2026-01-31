"""
Authentication Schemas
======================
Pydantic schemas for authentication-related API requests and responses
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    refresh_token: Optional[str] = None


class TokenPayload(BaseModel):
    """JWT token payload data."""
    sub: str  # User ID
    exp: datetime
    iat: datetime
    type: str = "access"  # 'access' or 'refresh'


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Login response with token and user info."""
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    refresh_token: str
    user: "UserResponse"


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)


class PasswordResetRequest(BaseModel):
    """Password reset request (request email)."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation (with token)."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class VerifyEmailRequest(BaseModel):
    """Email verification request."""
    token: str


# Import after to avoid circular import
from app.schemas.users import UserResponse

LoginResponse.model_rebuild()
