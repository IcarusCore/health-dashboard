"""
Daily Summary Models
====================
SQLAlchemy models for aggregated daily health summaries
"""

from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Date, ForeignKey, DECIMAL, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.models.database import Base


class DailySummary(Base):
    """Aggregated daily health summary for fast dashboard queries."""
    
    __tablename__ = "daily_summaries"
    
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
    date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # Activity metrics
    steps: Mapped[Optional[int]] = mapped_column(Integer)
    distance_km: Mapped[Optional[float]] = mapped_column(DECIMAL(8, 2))
    active_calories: Mapped[Optional[int]] = mapped_column(Integer)
    basal_calories: Mapped[Optional[int]] = mapped_column(Integer)
    total_calories: Mapped[Optional[int]] = mapped_column(Integer)
    exercise_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    stand_hours: Mapped[Optional[int]] = mapped_column(Integer)
    flights_climbed: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Vitals
    resting_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    avg_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    max_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    min_heart_rate: Mapped[Optional[int]] = mapped_column(Integer)
    hrv_avg: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 2))
    hrv_min: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 2))
    hrv_max: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 2))
    blood_oxygen_avg: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    blood_oxygen_min: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    respiratory_rate_avg: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    
    # Blood pressure
    blood_pressure_systolic: Mapped[Optional[int]] = mapped_column(Integer)
    blood_pressure_diastolic: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Sleep (from previous night)
    sleep_duration_hours: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    sleep_efficiency: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    sleep_deep_hours: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    sleep_rem_hours: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    sleep_light_hours: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    sleep_awake_hours: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    sleep_score: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Body composition
    weight_kg: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    body_fat_percent: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    lean_body_mass_kg: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    bmi: Mapped[Optional[float]] = mapped_column(DECIMAL(4, 2))
    
    # Nutrition
    water_liters: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))
    caffeine_mg: Mapped[Optional[int]] = mapped_column(Integer)
    dietary_calories: Mapped[Optional[int]] = mapped_column(Integer)
    dietary_protein_g: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 2))
    dietary_carbs_g: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 2))
    dietary_fat_g: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 2))
    dietary_fiber_g: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 2))
    
    # Mindfulness
    mindful_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Workout summary
    workout_count: Mapped[Optional[int]] = mapped_column(Integer)
    workout_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    workout_calories: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Goal progress (percentage, 0-100+)
    steps_goal_percent: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 2))
    calories_goal_percent: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 2))
    exercise_goal_percent: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 2))
    sleep_goal_percent: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 2))
    water_goal_percent: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 2))
    
    # Computed scores (0-100)
    activity_score: Mapped[Optional[int]] = mapped_column(Integer)
    vitals_score: Mapped[Optional[int]] = mapped_column(Integer)
    recovery_score: Mapped[Optional[int]] = mapped_column(Integer)
    overall_score: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Metadata
    source_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    notes: Mapped[Optional[str]] = mapped_column(String(1000))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uq_daily_summary_user_date'),
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="daily_summaries")
    
    def calculate_activity_score(self) -> Optional[int]:
        """Calculate activity score based on steps, exercise, and calories."""
        factors = []
        
        if self.steps_goal_percent is not None:
            factors.append(min(100, float(self.steps_goal_percent)))
        if self.exercise_goal_percent is not None:
            factors.append(min(100, float(self.exercise_goal_percent)))
        if self.calories_goal_percent is not None:
            factors.append(min(100, float(self.calories_goal_percent)))
        
        if not factors:
            return None
        return int(sum(factors) / len(factors))
    
    def calculate_vitals_score(self) -> Optional[int]:
        """Calculate vitals score based on heart rate, HRV, blood oxygen."""
        score = 100
        penalties = 0
        
        # Resting heart rate (optimal: 50-70)
        if self.resting_heart_rate:
            if self.resting_heart_rate < 45 or self.resting_heart_rate > 100:
                penalties += 20
            elif self.resting_heart_rate < 50 or self.resting_heart_rate > 80:
                penalties += 10
        
        # HRV (higher is generally better, but very individual)
        if self.hrv_avg:
            if self.hrv_avg < 20:
                penalties += 15
            elif self.hrv_avg < 30:
                penalties += 10
        
        # Blood oxygen (optimal: 95-100)
        if self.blood_oxygen_avg:
            if self.blood_oxygen_avg < 90:
                penalties += 25
            elif self.blood_oxygen_avg < 95:
                penalties += 10
        
        return max(0, score - penalties)
    
    def calculate_recovery_score(self) -> Optional[int]:
        """Calculate recovery score based on sleep and HRV."""
        factors = []
        
        if self.sleep_score is not None:
            factors.append(float(self.sleep_score))
        
        if self.hrv_avg is not None:
            # Normalize HRV to a 0-100 scale (assuming 20-80 range is typical)
            hrv_score = min(100, max(0, (float(self.hrv_avg) - 20) / 60 * 100))
            factors.append(hrv_score)
        
        if self.resting_heart_rate is not None:
            # Lower resting HR is better (assuming 40-80 range)
            rhr_score = min(100, max(0, (80 - float(self.resting_heart_rate)) / 40 * 100))
            factors.append(rhr_score)
        
        if not factors:
            return None
        return int(sum(factors) / len(factors))
    
    def calculate_overall_score(self) -> Optional[int]:
        """Calculate overall health score combining all factors."""
        scores = []
        
        activity = self.activity_score or self.calculate_activity_score()
        if activity is not None:
            scores.append(activity * 0.3)  # 30% weight
        
        vitals = self.vitals_score or self.calculate_vitals_score()
        if vitals is not None:
            scores.append(vitals * 0.3)  # 30% weight
        
        recovery = self.recovery_score or self.calculate_recovery_score()
        if recovery is not None:
            scores.append(recovery * 0.4)  # 40% weight
        
        if not scores:
            return None
        
        # Normalize based on weights present
        total_weight = sum([0.3 if activity else 0, 0.3 if vitals else 0, 0.4 if recovery else 0])
        if total_weight == 0:
            return None
        
        return int(sum(scores) / total_weight)
    
    def __repr__(self):
        return f"<DailySummary {self.date} for user {self.user_id}>"


# Forward reference
from app.models.users import User
