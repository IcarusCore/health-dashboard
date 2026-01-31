"""
Import, Insight, and Alert Schemas
==================================
Pydantic schemas for data imports, health insights, and alerts
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


# ===========================================
# Import Schemas
# ===========================================

class ImportCreate(BaseModel):
    """Schema for initiating an import."""
    source_type: str = Field(default="apple_health", max_length=50)


class ImportProgress(BaseModel):
    """Import progress update."""
    import_id: UUID
    status: str
    progress_percent: int
    current_phase: Optional[str] = None
    records_processed: int = 0
    records_total: int = 0
    message: Optional[str] = None


class ImportResponse(BaseModel):
    """Import history response."""
    id: UUID
    user_id: UUID
    source_id: Optional[UUID] = None
    filename: str
    file_size_bytes: Optional[int] = None
    status: str
    progress_percent: int
    current_phase: Optional[str] = None
    records_total: int
    records_imported: int
    records_skipped: int
    records_failed: int
    measurements_imported: int
    workouts_imported: int
    sleep_sessions_imported: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    data_start_date: Optional[datetime] = None
    data_end_date: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    records_per_second: Optional[float] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ImportSummary(BaseModel):
    """Summary of import results."""
    total_imports: int
    successful_imports: int
    failed_imports: int
    total_records_imported: int
    total_measurements: int
    total_workouts: int
    total_sleep_sessions: int
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None


# ===========================================
# Insight Schemas
# ===========================================

class InsightBase(BaseModel):
    """Base insight schema."""
    insight_type: str = Field(..., max_length=50)
    category: str = Field(..., max_length=50)
    title: str = Field(..., max_length=255)
    description: str
    severity: str = Field(default="info", pattern="^(info|positive|warning|alert)$")
    metric_keys: Optional[List[str]] = None
    data: dict = Field(default_factory=dict)


class InsightResponse(InsightBase):
    """Health insight response."""
    id: UUID
    user_id: UUID
    is_read: bool
    is_dismissed: bool
    is_pinned: bool
    priority: int
    valid_from: datetime
    valid_until: Optional[datetime] = None
    is_active: bool
    icon: str
    color: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class InsightUpdate(BaseModel):
    """Schema for updating an insight."""
    is_read: Optional[bool] = None
    is_dismissed: Optional[bool] = None
    is_pinned: Optional[bool] = None


class InsightsList(BaseModel):
    """List of insights with pagination."""
    insights: List[InsightResponse]
    total: int
    unread_count: int
    page: int
    page_size: int


class InsightFilters(BaseModel):
    """Filters for insights query."""
    insight_types: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    severities: Optional[List[str]] = None
    is_read: Optional[bool] = None
    is_dismissed: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


# ===========================================
# Alert Schemas
# ===========================================

class AlertBase(BaseModel):
    """Base alert schema."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    alert_type: str = Field(..., max_length=50)  # 'threshold', 'anomaly', 'goal', 'reminder'
    metric_key: Optional[str] = Field(None, max_length=100)
    condition: str = Field(..., max_length=50)  # 'above', 'below', 'between', etc.
    threshold_value: Optional[float] = None
    threshold_value_2: Optional[float] = None
    time_window_hours: Optional[int] = Field(None, ge=1, le=720)
    consecutive_triggers: int = Field(default=1, ge=1, le=10)
    cooldown_minutes: int = Field(default=60, ge=5, le=1440)
    notification_channels: List[str] = Field(default=["app"])
    priority: int = Field(default=50, ge=1, le=100)


class AlertCreate(AlertBase):
    """Schema for creating an alert."""
    pass


class AlertUpdate(BaseModel):
    """Schema for updating an alert."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    metric_key: Optional[str] = Field(None, max_length=100)
    condition: Optional[str] = Field(None, max_length=50)
    threshold_value: Optional[float] = None
    threshold_value_2: Optional[float] = None
    time_window_hours: Optional[int] = Field(None, ge=1, le=720)
    consecutive_triggers: Optional[int] = Field(None, ge=1, le=10)
    cooldown_minutes: Optional[int] = Field(None, ge=5, le=1440)
    notification_channels: Optional[List[str]] = None
    priority: Optional[int] = Field(None, ge=1, le=100)
    is_active: Optional[bool] = None


class AlertResponse(AlertBase):
    """Alert response."""
    id: UUID
    user_id: UUID
    is_active: bool
    is_muted: bool
    muted_until: Optional[datetime] = None
    last_triggered_at: Optional[datetime] = None
    last_value: Optional[float] = None
    trigger_count: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AlertMute(BaseModel):
    """Schema for muting an alert."""
    mute_hours: int = Field(..., ge=1, le=720)


class AlertNotificationResponse(BaseModel):
    """Alert notification response."""
    id: UUID
    alert_id: UUID
    channel: str
    title: str
    message: str
    triggered_value: Optional[float] = None
    threshold_value: Optional[float] = None
    status: str
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AlertTestResult(BaseModel):
    """Result of testing an alert."""
    would_trigger: bool
    current_value: Optional[float] = None
    threshold_value: Optional[float] = None
    message: str


# ===========================================
# Analytics Schemas
# ===========================================

class TrendAnalysis(BaseModel):
    """Trend analysis for a metric."""
    metric_key: str
    display_name: str
    period_days: int
    direction: str  # 'increasing', 'decreasing', 'stable'
    change_percent: float
    change_absolute: float
    start_value: float
    end_value: float
    confidence: float  # 0-1
    data_points: int
    is_significant: bool


class AnomalyDetection(BaseModel):
    """Anomaly detection result."""
    metric_key: str
    display_name: str
    timestamp: datetime
    value: float
    expected_value: float
    expected_range_low: float
    expected_range_high: float
    z_score: float
    is_anomaly: bool
    anomaly_type: Optional[str] = None  # 'high', 'low'


class HealthReport(BaseModel):
    """Comprehensive health report."""
    period_start: date
    period_end: date
    
    # Summary scores
    overall_health_score: Optional[int] = None
    activity_score: Optional[int] = None
    sleep_score: Optional[int] = None
    recovery_score: Optional[int] = None
    
    # Key metrics summary
    avg_steps: Optional[float] = None
    avg_sleep_hours: Optional[float] = None
    avg_resting_hr: Optional[float] = None
    avg_hrv: Optional[float] = None
    weight_change_kg: Optional[float] = None
    
    # Achievements
    achievements: List[str] = []
    
    # Trends
    improving_metrics: List[str] = []
    declining_metrics: List[str] = []
    
    # Recommendations
    recommendations: List[str] = []
    
    # Data quality
    data_completeness_percent: float
    days_with_data: int
    total_days: int


# ===========================================
# Export Schemas
# ===========================================

class ExportRequest(BaseModel):
    """Data export request."""
    format: str = Field(default="json", pattern="^(json|csv|xlsx)$")
    metric_keys: Optional[List[str]] = None
    include_workouts: bool = True
    include_sleep: bool = True
    include_measurements: bool = True
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    timezone: str = Field(default="UTC")


class ExportResponse(BaseModel):
    """Data export response."""
    export_id: UUID
    status: str
    format: str
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class CorrelationResult(BaseModel):
    """Single correlation result between two metrics."""
    metric_1: str
    metric_2: str
    correlation: float
    p_value: Optional[float] = None
    sample_size: int
    significance: str = "unknown"  # "significant", "not_significant", "unknown"
    
    model_config = ConfigDict(from_attributes=True)


class CorrelationMatrix(BaseModel):
    """Matrix of correlations between multiple metrics."""
    metrics: list[str]
    correlations: list[CorrelationResult]
    computed_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
