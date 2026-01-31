"""
User Models
===========
SQLAlchemy models for users and user settings
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, Text, DECIMAL, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.models.database import Base


class User(Base):
    """User account model."""
    
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    date_format: Mapped[str] = mapped_column(String(20), default="YYYY-MM-DD")
    units_system: Mapped[str] = mapped_column(String(20), default="metric")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    settings: Mapped["UserSettings"] = relationship(
        "UserSettings", 
        back_populates="user", 
        uselist=False,
        cascade="all, delete-orphan"
    )
    data_sources: Mapped[List["DataSource"]] = relationship(
        "DataSource", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    measurements: Mapped[List["Measurement"]] = relationship(
        "Measurement", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    workouts: Mapped[List["Workout"]] = relationship(
        "Workout", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    sleep_sessions: Mapped[List["SleepSession"]] = relationship(
        "SleepSession", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    daily_summaries: Mapped[List["DailySummary"]] = relationship(
        "DailySummary", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    insights: Mapped[List["HealthInsight"]] = relationship(
        "HealthInsight", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    alerts: Mapped[List["Alert"]] = relationship(
        "Alert", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    import_history: Mapped[List["ImportHistory"]] = relationship(
        "ImportHistory", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    custom_metrics: Mapped[List["CustomMetric"]] = relationship(
        "CustomMetric", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User {self.username}>"


class UserSettings(Base):
    """User settings and preferences."""
    
    __tablename__ = "user_settings"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    
    # Dashboard preferences
    default_date_range: Mapped[int] = mapped_column(Integer, default=30)
    show_weekly_summary: Mapped[bool] = mapped_column(Boolean, default=True)
    show_monthly_summary: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Notification preferences
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    discord_notifications: Mapped[bool] = mapped_column(Boolean, default=False)
    pushover_notifications: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Alert thresholds
    resting_hr_low_threshold: Mapped[int] = mapped_column(Integer, default=40)
    resting_hr_high_threshold: Mapped[int] = mapped_column(Integer, default=100)
    weight_change_alert_percent: Mapped[float] = mapped_column(DECIMAL(5, 2), default=5.0)
    sleep_duration_min_hours: Mapped[float] = mapped_column(DECIMAL(4, 2), default=6.0)
    
    # Health goals
    daily_steps_goal: Mapped[int] = mapped_column(Integer, default=10000)
    daily_calories_goal: Mapped[int] = mapped_column(Integer, default=2000)
    daily_active_minutes_goal: Mapped[int] = mapped_column(Integer, default=30)
    sleep_hours_goal: Mapped[float] = mapped_column(DECIMAL(4, 2), default=8.0)
    weight_goal_kg: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    
    # Theme preferences
    theme: Mapped[str] = mapped_column(String(20), default="dark")
    accent_color: Mapped[str] = mapped_column(String(20), default="cyan")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="settings")
    
    def __repr__(self):
        return f"<UserSettings for user {self.user_id}>"


class DataSource(Base):
    """Data source tracking (Apple Health, manual, etc.)"""
    
    __tablename__ = "data_sources"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sync_status: Mapped[str] = mapped_column(String(20), default="never")
    sync_error_message: Mapped[Optional[str]] = mapped_column(Text)
    total_records_imported: Mapped[int] = mapped_column(Integer, default=0)
    source_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="data_sources")
    measurements: Mapped[List["Measurement"]] = relationship(
        "Measurement", 
        back_populates="source"
    )
    workouts: Mapped[List["Workout"]] = relationship(
        "Workout", 
        back_populates="source"
    )
    sleep_sessions: Mapped[List["SleepSession"]] = relationship(
        "SleepSession", 
        back_populates="source"
    )
    
    def __repr__(self):
        return f"<DataSource {self.source_type}: {self.source_name}>"


# Forward references for relationships
from app.models.measurements import Measurement
from app.models.workouts import Workout
from app.models.sleep import SleepSession
from app.models.daily_summary import DailySummary
from app.models.insights import HealthInsight
from app.models.alerts import Alert
from app.models.imports import ImportHistory
from app.models.custom_metrics import CustomMetric
