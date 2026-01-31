"""
Measurement Models
==================
SQLAlchemy models for health measurements (time series data)
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, DECIMAL, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.models.database import Base


class MetricDefinition(Base):
    """Definition of available health metrics."""
    
    __tablename__ = "metric_definitions"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    metric_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    data_type: Mapped[str] = mapped_column(String(20), nullable=False)
    aggregation_method: Mapped[str] = mapped_column(String(20), default="avg")
    display_precision: Mapped[int] = mapped_column(default=1)
    min_value: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))
    max_value: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))
    is_cumulative: Mapped[bool] = mapped_column(default=False)
    icon: Mapped[Optional[str]] = mapped_column(String(50))
    color: Mapped[Optional[str]] = mapped_column(String(20))
    sort_order: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    def __repr__(self):
        return f"<MetricDefinition {self.metric_key}>"


class Measurement(Base):
    """Individual health measurement data point."""
    
    __tablename__ = "measurements"
    
    # Composite primary key for TimescaleDB hypertable
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        UUID(as_uuid=True), 
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    metric_key: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("data_sources.id", ondelete="SET NULL")
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False,
        primary_key=True
    )
    value: Mapped[float] = mapped_column(DECIMAL(15, 4), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(50))
    source_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Set composite primary key
    __table_args__ = (
        Index('idx_measurements_user_metric', 'user_id', 'metric_key', 'timestamp'),
        Index('idx_measurements_timestamp', 'timestamp'),
        {'timescaledb_hypertable': {'time_column': 'timestamp'}},
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="measurements")
    source: Mapped[Optional["DataSource"]] = relationship("DataSource", back_populates="measurements")
    
    def __repr__(self):
        return f"<Measurement {self.metric_key}: {self.value} at {self.timestamp}>"


class MetricCorrelation(Base):
    """Pre-computed correlations between metrics."""
    
    __tablename__ = "metric_correlations"
    
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    metric_a: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_b: Mapped[str] = mapped_column(String(100), nullable=False)
    correlation_coefficient: Mapped[float] = mapped_column(DECIMAL(6, 4), nullable=False)
    p_value: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 8))
    sample_size: Mapped[int] = mapped_column(nullable=False)
    lag_days: Mapped[int] = mapped_column(default=0)
    date_range_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    date_range_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_significant: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    def __repr__(self):
        return f"<MetricCorrelation {self.metric_a} <-> {self.metric_b}: {self.correlation_coefficient}>"


# Forward reference
from app.models.users import User, DataSource
