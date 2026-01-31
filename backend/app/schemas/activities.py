"""
Activity Schemas
================
Pydantic schemas for workouts, sleep, and daily summaries
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


# ===========================================
# Workout Schemas
# ===========================================

class WorkoutBase(BaseModel):
    """Base workout schema."""
    workout_type: str = Field(..., max_length=100)
    start_time: datetime
    end_time: datetime
    duration_seconds: int = Field(..., ge=0)
    distance_meters: Optional[float] = Field(None, ge=0)
    active_calories: Optional[float] = Field(None, ge=0)
    total_calories: Optional[float] = Field(None, ge=0)
    avg_heart_rate: Optional[int] = Field(None, ge=0, le=300)
    max_heart_rate: Optional[int] = Field(None, ge=0, le=300)
    elevation_gain_meters: Optional[float] = Field(None, ge=0)
    avg_pace_seconds_per_km: Optional[int] = Field(None, ge=0)
    avg_speed_kmh: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None
    source_metadata: dict = Field(default_factory=dict)


class WorkoutCreate(WorkoutBase):
    """Schema for creating a workout."""
    source_id: Optional[UUID] = None


class WorkoutUpdate(BaseModel):
    """Schema for updating a workout."""
    notes: Optional[str] = None
    source_metadata: Optional[dict] = None


class WorkoutResponse(WorkoutBase):
    """Workout response."""
    id: UUID
    user_id: UUID
    source_id: Optional[UUID] = None
    duration_minutes: float
    duration_hours: float
    distance_km: Optional[float] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WorkoutSummary(BaseModel):
    """Workout summary for a period."""
    period_start: date
    period_end: date
    total_workouts: int
    total_duration_minutes: float
    total_distance_km: float
    total_calories: float
    workouts_by_type: dict  # {workout_type: count}
    avg_duration_minutes: float
    avg_heart_rate: Optional[float] = None


class WorkoutStreak(BaseModel):
    """Workout streak information."""
    current_streak_days: int
    longest_streak_days: int
    last_workout_date: Optional[date] = None
    streak_start_date: Optional[date] = None


# ===========================================
# Sleep Schemas
# ===========================================

class SleepSessionBase(BaseModel):
    """Base sleep session schema."""
    start_time: datetime
    end_time: datetime
    duration_seconds: int = Field(..., ge=0)
    time_asleep_seconds: Optional[int] = Field(None, ge=0)
    time_awake_seconds: Optional[int] = Field(None, ge=0)
    time_deep_seconds: Optional[int] = Field(None, ge=0)
    time_light_seconds: Optional[int] = Field(None, ge=0)
    time_rem_seconds: Optional[int] = Field(None, ge=0)
    sleep_efficiency: Optional[float] = Field(None, ge=0, le=100)
    sleep_latency_seconds: Optional[int] = Field(None, ge=0)
    wake_count: Optional[int] = Field(None, ge=0)
    avg_heart_rate: Optional[int] = Field(None, ge=0, le=300)
    min_heart_rate: Optional[int] = Field(None, ge=0, le=300)
    avg_hrv: Optional[float] = Field(None, ge=0)
    avg_respiratory_rate: Optional[float] = Field(None, ge=0)
    avg_spo2: Optional[float] = Field(None, ge=0, le=100)
    notes: Optional[str] = None
    source_metadata: dict = Field(default_factory=dict)


class SleepSessionCreate(SleepSessionBase):
    """Schema for creating a sleep session."""
    source_id: Optional[UUID] = None


class SleepSessionResponse(SleepSessionBase):
    """Sleep session response."""
    id: UUID
    user_id: UUID
    source_id: Optional[UUID] = None
    duration_hours: float
    time_asleep_hours: Optional[float] = None
    time_deep_hours: Optional[float] = None
    time_light_hours: Optional[float] = None
    time_rem_hours: Optional[float] = None
    deep_sleep_percent: Optional[float] = None
    rem_sleep_percent: Optional[float] = None
    light_sleep_percent: Optional[float] = None
    sleep_score: Optional[int] = None
    sleep_date: date
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SleepSummary(BaseModel):
    """Sleep summary for a period."""
    period_start: date
    period_end: date
    total_nights: int
    avg_duration_hours: float
    avg_efficiency: Optional[float] = None
    avg_deep_percent: Optional[float] = None
    avg_rem_percent: Optional[float] = None
    avg_sleep_score: Optional[float] = None
    avg_bedtime: Optional[str] = None  # HH:MM format
    avg_wake_time: Optional[str] = None
    consistency_score: Optional[float] = None


class SleepStagesBreakdown(BaseModel):
    """Sleep stages breakdown for visualization."""
    date: date
    deep_hours: Optional[float] = None
    light_hours: Optional[float] = None
    rem_hours: Optional[float] = None
    awake_hours: Optional[float] = None
    total_hours: float
    efficiency: Optional[float] = None
    score: Optional[int] = None


# ===========================================
# Daily Summary Schemas
# ===========================================

class DailySummaryBase(BaseModel):
    """Base daily summary schema."""
    date: date
    
    # Activity
    steps: Optional[int] = None
    distance_km: Optional[float] = None
    active_calories: Optional[int] = None
    exercise_minutes: Optional[int] = None
    stand_hours: Optional[int] = None
    flights_climbed: Optional[int] = None
    
    # Vitals
    resting_heart_rate: Optional[int] = None
    avg_heart_rate: Optional[int] = None
    hrv_avg: Optional[float] = None
    blood_oxygen_avg: Optional[float] = None
    
    # Sleep
    sleep_duration_hours: Optional[float] = None
    sleep_efficiency: Optional[float] = None
    sleep_score: Optional[int] = None
    
    # Body
    weight_kg: Optional[float] = None
    body_fat_percent: Optional[float] = None
    
    # Nutrition
    water_liters: Optional[float] = None
    dietary_calories: Optional[int] = None
    
    # Scores
    activity_score: Optional[int] = None
    recovery_score: Optional[int] = None
    overall_score: Optional[int] = None


class DailySummaryResponse(DailySummaryBase):
    """Daily summary response with goal progress."""
    id: UUID
    user_id: UUID
    
    # Goal progress
    steps_goal_percent: Optional[float] = None
    calories_goal_percent: Optional[float] = None
    exercise_goal_percent: Optional[float] = None
    sleep_goal_percent: Optional[float] = None
    
    # Workout info
    workout_count: Optional[int] = None
    workout_minutes: Optional[int] = None
    
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DailySummaryTrend(BaseModel):
    """Daily summary with trend information."""
    date: date
    value: Optional[float] = None
    trend_7day: Optional[float] = None
    trend_30day: Optional[float] = None


# ===========================================
# Dashboard Schemas
# ===========================================

class DashboardOverview(BaseModel):
    """Dashboard overview data."""
    today: Optional[DailySummaryResponse] = None
    yesterday: Optional[DailySummaryResponse] = None
    
    # Current streaks
    steps_streak: int = 0
    exercise_streak: int = 0
    sleep_streak: int = 0
    
    # Week summary
    week_avg_steps: Optional[float] = None
    week_avg_sleep_hours: Optional[float] = None
    week_avg_activity_score: Optional[float] = None
    
    # Trends
    weight_trend_7day: Optional[float] = None
    hrv_trend_7day: Optional[float] = None
    
    # Recent insights count
    unread_insights: int = 0
    
    # Last sync
    last_sync_at: Optional[datetime] = None


class DashboardWidget(BaseModel):
    """Dashboard widget configuration."""
    id: str
    type: str  # 'metric', 'chart', 'summary', 'progress', 'streak'
    metric_key: Optional[str] = None
    title: str
    position: int
    size: str = "medium"  # 'small', 'medium', 'large'
    config: dict = Field(default_factory=dict)


class DashboardConfig(BaseModel):
    """User dashboard configuration."""
    widgets: List[DashboardWidget]
    layout: str = "grid"  # 'grid', 'list'
    columns: int = Field(default=3, ge=1, le=4)
