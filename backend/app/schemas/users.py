"""
User Schemas
============
Pydantic schemas for user-related API requests and responses
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from uuid import UUID


# ===========================================
# User Schemas
# ===========================================

class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    timezone: str = Field(default="UTC", max_length=50)
    date_format: str = Field(default="YYYY-MM-DD", max_length=20)
    units_system: str = Field(default="metric", pattern="^(metric|imperial)$")


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    timezone: Optional[str] = Field(None, max_length=50)
    date_format: Optional[str] = Field(None, max_length=20)
    units_system: Optional[str] = Field(None, pattern="^(metric|imperial)$")


class UserPasswordChange(BaseModel):
    """Schema for changing password."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class UserResponse(UserBase):
    """Schema for user response."""
    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserWithSettings(UserResponse):
    """Schema for user response with settings."""
    settings: Optional["UserSettingsResponse"] = None


# ===========================================
# User Settings Schemas
# ===========================================

class UserSettingsBase(BaseModel):
    """Base settings schema."""
    # Dashboard preferences
    default_date_range: int = Field(default=30, ge=1, le=365)
    show_weekly_summary: bool = True
    show_monthly_summary: bool = True
    
    # Notification preferences
    email_notifications: bool = True
    discord_notifications: bool = False
    pushover_notifications: bool = False
    
    # Alert thresholds
    resting_hr_low_threshold: int = Field(default=40, ge=20, le=100)
    resting_hr_high_threshold: int = Field(default=100, ge=50, le=200)
    weight_change_alert_percent: float = Field(default=5.0, ge=0.1, le=50.0)
    sleep_duration_min_hours: float = Field(default=6.0, ge=1.0, le=12.0)
    
    # Health goals
    daily_steps_goal: int = Field(default=10000, ge=1000, le=100000)
    daily_calories_goal: int = Field(default=2000, ge=500, le=10000)
    daily_active_minutes_goal: int = Field(default=30, ge=5, le=300)
    sleep_hours_goal: float = Field(default=8.0, ge=4.0, le=12.0)
    weight_goal_kg: Optional[float] = Field(None, ge=20.0, le=500.0)
    
    # Theme
    theme: str = Field(default="dark", pattern="^(dark|light|system)$")
    accent_color: str = Field(default="cyan", max_length=20)


class UserSettingsUpdate(BaseModel):
    """Schema for updating settings."""
    default_date_range: Optional[int] = Field(None, ge=1, le=365)
    show_weekly_summary: Optional[bool] = None
    show_monthly_summary: Optional[bool] = None
    email_notifications: Optional[bool] = None
    discord_notifications: Optional[bool] = None
    pushover_notifications: Optional[bool] = None
    resting_hr_low_threshold: Optional[int] = Field(None, ge=20, le=100)
    resting_hr_high_threshold: Optional[int] = Field(None, ge=50, le=200)
    weight_change_alert_percent: Optional[float] = Field(None, ge=0.1, le=50.0)
    sleep_duration_min_hours: Optional[float] = Field(None, ge=1.0, le=12.0)
    daily_steps_goal: Optional[int] = Field(None, ge=1000, le=100000)
    daily_calories_goal: Optional[int] = Field(None, ge=500, le=10000)
    daily_active_minutes_goal: Optional[int] = Field(None, ge=5, le=300)
    sleep_hours_goal: Optional[float] = Field(None, ge=4.0, le=12.0)
    weight_goal_kg: Optional[float] = Field(None, ge=20.0, le=500.0)
    theme: Optional[str] = Field(None, pattern="^(dark|light|system)$")
    accent_color: Optional[str] = Field(None, max_length=20)


class UserSettingsResponse(UserSettingsBase):
    """Schema for settings response."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ===========================================
# Data Source Schemas
# ===========================================

class DataSourceBase(BaseModel):
    """Base data source schema."""
    source_type: str = Field(..., max_length=50)
    source_name: str = Field(..., max_length=100)
    is_active: bool = True


class DataSourceCreate(DataSourceBase):
    """Schema for creating a data source."""
    metadata: dict = Field(default_factory=dict)


class DataSourceUpdate(BaseModel):
    """Schema for updating a data source."""
    source_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    metadata: Optional[dict] = None


class DataSourceResponse(DataSourceBase):
    """Schema for data source response."""
    id: UUID
    user_id: UUID
    last_sync_at: Optional[datetime] = None
    sync_status: str
    sync_error_message: Optional[str] = None
    total_records_imported: int
    metadata: dict
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Resolve forward reference
UserWithSettings.model_rebuild()
