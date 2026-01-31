"""
Authentication Routes
=====================
User authentication, registration, and token management
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.users import User, UserSettings
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RefreshTokenRequest,
    Token,
)
from app.schemas.users import UserResponse
from app.api.dependencies import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user account.
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Check if username already exists
    result = await db.execute(
        select(User).where(User.username == request.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )
    
    # Create new user
    user = User(
        email=request.email,
        username=request.username,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    
    # Create default settings for the user
    settings = UserSettings(user_id=user.id)
    db.add(settings)
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and return access token.
    
    Accepts either username or email in the username field.
    """
    # Try to find user by username or email
    result = await db.execute(
        select(User).where(
            (User.username == request.username) | (User.email == request.username)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    
    # Create tokens
    access_token, access_expires = create_access_token(str(user.id))
    refresh_token, _ = create_refresh_token(str(user.id))
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_at=access_expires,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh an access token using a refresh token.
    """
    # Decode refresh token
    payload = decode_token(request.refresh_token)
    
    # Verify it's a refresh token
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    user_id = payload.get("sub")
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new access token
    access_token, expires_at = create_access_token(str(user.id))
    
    # Optionally create new refresh token
    new_refresh_token, _ = create_refresh_token(str(user.id))
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_at=expires_at,
        refresh_token=new_refresh_token,
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
):
    """
    Logout the current user.
    
    Note: With JWT tokens, the token remains valid until expiration.
    This endpoint is provided for client-side token cleanup and
    potential future token blacklisting.
    """
    # In a production system, you might want to:
    # 1. Add the token to a blacklist in Redis
    # 2. Update last_logout timestamp on user
    # For now, we just return success
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get the current authenticated user's information.
    """
    return current_user


@router.post("/verify-token")
async def verify_token(
    current_user: User = Depends(get_current_user),
):
    """
    Verify that the current token is valid.
    
    Returns user info if valid, 401 if invalid.
    """
    return {
        "valid": True,
        "user_id": str(current_user.id),
        "username": current_user.username,
    }
