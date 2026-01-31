"""
Custom Metrics Models
=====================
SQLAlchemy models for user-defined custom metrics
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, DECIMAL, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.database import Base


class CustomMetric(Base):
    """User-defined custom metric definition."""
    
    __tablename__ = "custom_metrics"
    
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
    
    # Metric definition
    metric_key: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Classification
    category: Mapped[str] = mapped_column(String(50), default="custom")
    
    # Data configuration
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    data_type: Mapped[str] = mapped_column(String(20), default="numeric")
    # Types: 'numeric', 'duration', 'percentage', 'boolean', 'text'
    
    aggregation_method: Mapped[str] = mapped_column(String(20), default="avg")
    # Methods: 'avg', 'sum', 'min', 'max', 'last', 'count'
    
    display_precision: Mapped[int] = mapped_column(Integer, default=1)
    
    # Validation
    min_value: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))
    max_value: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))
    
    # Display
    icon: Mapped[str] = mapped_column(String(50), default="chart-bar")
    color: Mapped[str] = mapped_column(String(20), default="gray")
    sort_order: Mapped[int] = mapped_column(Integer, default=100)
    
    # State
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    show_in_dashboard: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Goals
    daily_goal: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))
    goal_direction: Mapped[Optional[str]] = mapped_column(String(20))
    # Directions: 'higher', 'lower', 'target'
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'metric_key', name='uq_custom_metric_user_key'),
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="custom_metrics")
    
    def __repr__(self):
        return f"<CustomMetric {self.metric_key}: {self.display_name}>"


# Forward reference
from app.models.users import User
