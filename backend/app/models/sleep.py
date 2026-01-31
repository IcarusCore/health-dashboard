"""
Sleep Models
============
SQLAlchemy models for sleep sessions and sleep analysis
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.models.database import Base


class SleepSession(Base):
    """Sleep session record with detailed sleep stage analysis."""
    
    __tablename__ = "sleep_sessions"
    
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
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("data_sources.id", ondelete="SET NULL")
    )
    
    # Core sleep times
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # In bed times (may differ from actual sleep times)
    in_bed_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    in_bed_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Duration
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    time_asleep_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    time_awake_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Sleep stages (in seconds)
    time_deep_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    time_light_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    time_rem_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Sleep quality metrics
    sleep_efficiency: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    sleep_latency_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    wake_count: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Vitals during sleep
    avg_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    min_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    max_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    avg_hrv: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 2))
    avg_respiratory_rate: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    avg_spo2: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    
    # Environmental
    avg_noise_level_db: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    avg_room_temperature_c: Mapped[Optional[float]] = mapped_column(DECIMAL(4, 2))
    
    # Additional data
    source_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sleep_sessions")
    source: Mapped[Optional["DataSource"]] = relationship("DataSource", back_populates="sleep_sessions")
    
    @property
    def duration_hours(self) -> float:
        return round(float(self.duration_seconds) / 3600, 2) if self.duration_seconds else 0.0
    
    @property
    def time_asleep_hours(self) -> Optional[float]:
        return round(float(self.time_asleep_seconds) / 3600, 2) if self.time_asleep_seconds else None
    
    @property
    def time_deep_hours(self) -> Optional[float]:
        return round(float(self.time_deep_seconds) / 3600, 2) if self.time_deep_seconds else None
    
    @property
    def time_light_hours(self) -> Optional[float]:
        return round(float(self.time_light_seconds) / 3600, 2) if self.time_light_seconds else None
    
    @property
    def time_rem_hours(self) -> Optional[float]:
        return round(float(self.time_rem_seconds) / 3600, 2) if self.time_rem_seconds else None
    
    @property
    def time_awake_hours(self) -> Optional[float]:
        return round(float(self.time_awake_seconds) / 3600, 2) if self.time_awake_seconds else None
    
    @property
    def deep_sleep_percent(self) -> Optional[float]:
        if self.time_deep_seconds and self.time_asleep_seconds:
            return (self.time_deep_seconds / self.time_asleep_seconds) * 100
        return None
    
    @property
    def rem_sleep_percent(self) -> Optional[float]:
        if self.time_rem_seconds and self.time_asleep_seconds:
            return (self.time_rem_seconds / self.time_asleep_seconds) * 100
        return None
    
    @property
    def light_sleep_percent(self) -> Optional[float]:
        if self.time_light_seconds and self.time_asleep_seconds:
            return (self.time_light_seconds / self.time_asleep_seconds) * 100
        return None
    
    @property
    def sleep_score(self) -> Optional[int]:
        """Calculate a sleep score (0-100) based on multiple factors."""
        if not self.time_asleep_seconds:
            return None
        
        score = 0.0
        factors = 0
        
        # Efficiency factor (0-25 points)
        if self.sleep_efficiency:
            efficiency_score = min(25, self.sleep_efficiency / 100 * 25)
            score += float(efficiency_score)
            factors += 1
        
        # Deep sleep factor (0-25 points) - target ~20% of sleep
        if self.time_deep_seconds and self.time_asleep_seconds:
            deep_percent = (self.time_deep_seconds / self.time_asleep_seconds) * 100
            deep_score = min(25, (deep_percent / 20) * 25)
            score += float(deep_score)
            factors += 1
        
        # REM sleep factor (0-25 points) - target ~25% of sleep
        if self.time_rem_seconds and self.time_asleep_seconds:
            rem_percent = (self.time_rem_seconds / self.time_asleep_seconds) * 100
            rem_score = min(25, (rem_percent / 25) * 25)
            score += float(rem_score)
            factors += 1
        
        # Duration factor (0-25 points) - target 8 hours
        target_hours = 8
        actual_hours = self.time_asleep_seconds / 3600
        if actual_hours >= target_hours:
            duration_score = 25
        else:
            duration_score = (actual_hours / target_hours) * 25
        score += float(duration_score)
        factors += 1
        
        if factors == 0:
            return None
        
        normalized_score = (score / factors) * 4
        return min(100, int(normalized_score))
    
    @property
    def sleep_date(self) -> datetime:
        """Get the date this sleep session belongs to."""
        if self.start_time.hour < 6:
            return (self.start_time - timedelta(days=1)).date()
        return self.start_time.date()
    
    def __repr__(self):
        return f"<SleepSession {self.duration_hours:.1f}h on {self.start_time.date()}>"


# Forward reference
from app.models.users import User, DataSource
