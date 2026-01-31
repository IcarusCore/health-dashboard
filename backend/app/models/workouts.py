"""
Workout Models
==============
SQLAlchemy models for workouts and exercise activities
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.models.database import Base


class Workout(Base):
    """Workout/exercise activity record."""
    
    __tablename__ = "workouts"
    
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
    
    # Core workout data
    workout_type: Mapped[str] = mapped_column(String(100), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Distance and movement
    distance_meters: Mapped[Optional[float]] = mapped_column(DECIMAL(12, 2))
    elevation_gain_meters: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2))
    
    # Calories
    active_calories: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2))
    total_calories: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2))
    
    # Heart rate
    avg_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    max_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    min_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Pace/Speed
    avg_pace_seconds_per_km: Mapped[Optional[int]] = mapped_column(Integer)
    avg_speed_kmh: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 2))
    max_speed_kmh: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 2))
    
    # Swimming specific
    pool_length_meters: Mapped[Optional[int]] = mapped_column(Integer)
    swim_strokes: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Cycling specific
    avg_cadence: Mapped[Optional[int]] = mapped_column(Integer)
    avg_power_watts: Mapped[Optional[int]] = mapped_column(Integer)
    max_power_watts: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Running specific
    avg_stride_length_cm: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 2))
    ground_contact_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    vertical_oscillation_cm: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    
    # Weather conditions (if available)
    temperature_celsius: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    humidity_percent: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Additional data
    source_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="workouts")
    source: Mapped[Optional["DataSource"]] = relationship("DataSource", back_populates="workouts")
    
    @property
    def duration_minutes(self) -> float:
        """Duration in minutes."""
        return self.duration_seconds / 60
    
    @property
    def duration_hours(self) -> float:
        """Duration in hours."""
        return self.duration_seconds / 3600
    
    @property
    def distance_km(self) -> Optional[float]:
        """Distance in kilometers."""
        return self.distance_meters / 1000 if self.distance_meters else None
    
    @property
    def distance_miles(self) -> Optional[float]:
        """Distance in miles."""
        return self.distance_meters / 1609.344 if self.distance_meters else None
    
    @property
    def avg_pace_per_mile(self) -> Optional[str]:
        """Average pace in minutes per mile."""
        if self.avg_pace_seconds_per_km:
            pace_per_mile = self.avg_pace_seconds_per_km * 1.60934
            minutes = int(pace_per_mile // 60)
            seconds = int(pace_per_mile % 60)
            return f"{minutes}:{seconds:02d}"
        return None
    
    def __repr__(self):
        return f"<Workout {self.workout_type} on {self.start_time.date()}>"


# Forward reference
from app.models.users import User, DataSource
