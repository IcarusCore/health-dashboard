"""
Alert Models
============
SQLAlchemy models for health alerts and notifications
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, DECIMAL, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.models.database import Base


class Alert(Base):
    """
    User-configured health alerts for threshold monitoring,
    anomaly detection, and goal reminders.
    """
    
    __tablename__ = "alerts"
    
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
    
    # Alert configuration
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Types: 'threshold', 'anomaly', 'goal', 'reminder', 'trend', 'absence'
    
    metric_key: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Condition configuration
    condition: Mapped[str] = mapped_column(String(50), nullable=False)
    # Conditions: 'above', 'below', 'equals', 'between', 'outside', 'change_percent', 'missing'
    
    threshold_value: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))
    threshold_value_2: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))  # For 'between' or 'outside'
    
    # Time-based conditions
    time_window_hours: Mapped[Optional[int]] = mapped_column(Integer)  # For trend/absence alerts
    consecutive_triggers: Mapped[int] = mapped_column(Integer, default=1)  # Number of consecutive triggers before alerting
    
    # State
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_muted: Mapped[bool] = mapped_column(Boolean, default=False)
    muted_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Trigger tracking
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_value: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Cooldown to prevent alert spam
    cooldown_minutes: Mapped[int] = mapped_column(Integer, default=60)
    
    # Notification channels
    notification_channels: Mapped[List[str]] = mapped_column(
        ARRAY(String(50)), 
        default=['app']
    )
    # Channels: 'app', 'email', 'discord', 'pushover'
    
    # Priority (lower = higher priority)
    priority: Mapped[int] = mapped_column(Integer, default=50)
    
    # Schedule (optional - for reminder alerts)
    schedule_cron: Mapped[Optional[str]] = mapped_column(String(100))  # Cron expression
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="alerts")
    notifications: Mapped[List["AlertNotification"]] = relationship(
        "AlertNotification",
        back_populates="alert",
        cascade="all, delete-orphan"
    )
    
    def can_trigger(self) -> bool:
        """Check if alert can be triggered based on cooldown and mute status."""
        if not self.is_active:
            return False
        
        if self.is_muted:
            if self.muted_until and datetime.utcnow() < self.muted_until:
                return False
            # Mute period expired, unmute
            self.is_muted = False
        
        if self.last_triggered_at:
            from datetime import timedelta
            cooldown_end = self.last_triggered_at + timedelta(minutes=self.cooldown_minutes)
            if datetime.utcnow() < cooldown_end:
                return False
        
        return True
    
    def check_condition(self, value: float) -> bool:
        """Check if the given value meets the alert condition."""
        if self.threshold_value is None:
            return False
        
        if self.condition == 'above':
            return value > self.threshold_value
        elif self.condition == 'below':
            return value < self.threshold_value
        elif self.condition == 'equals':
            return abs(value - self.threshold_value) < 0.0001
        elif self.condition == 'between':
            if self.threshold_value_2 is None:
                return False
            return self.threshold_value <= value <= self.threshold_value_2
        elif self.condition == 'outside':
            if self.threshold_value_2 is None:
                return False
            return value < self.threshold_value or value > self.threshold_value_2
        elif self.condition == 'change_percent':
            if self.last_value is None:
                return False
            change = abs((value - self.last_value) / self.last_value * 100)
            return change >= self.threshold_value
        
        return False
    
    def __repr__(self):
        return f"<Alert {self.name} ({self.alert_type})>"


class AlertNotification(Base):
    """Record of sent alert notifications."""
    
    __tablename__ = "alert_notifications"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Notification details
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    
    # Trigger data
    triggered_value: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))
    threshold_value: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))
    
    # Delivery status
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # Statuses: 'pending', 'sent', 'failed', 'read'
    
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Metadata
    source_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    alert: Mapped["Alert"] = relationship("Alert", back_populates="notifications")
    
    def __repr__(self):
        return f"<AlertNotification {self.channel}: {self.title}>"


# Forward reference
from app.models.users import User
