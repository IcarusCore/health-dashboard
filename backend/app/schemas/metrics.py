"""
Metrics and Measurements Schemas
================================
Pydantic schemas for health metrics and measurements
"""

from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


# ===========================================
# Metric Definition Schemas
# ===========================================

class MetricDefinitionBase(BaseModel):
    """Base metric definition schema."""
    metric_key: str = Field(..., max_length=100)
    display_name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    category: str = Field(..., max_length=50)
    unit: str = Field(..., max_length=50)
    data_type: str = Field(default="numeric", max_length=20)
    aggregation_method: str = Field(default="avg", max_length=20)
    display_precision: int = Field(default=1, ge=0, le=10)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    is_cumulative: bool = False
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=20)
    sort_order: int = Field(default=0)
    is_active: bool = True


class MetricDefinitionResponse(MetricDefinitionBase):
    """Metric definition response."""
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MetricDefinitionList(BaseModel):
    """List of metric definitions grouped by category."""
    category: str
    metrics: List[MetricDefinitionResponse]


# ===========================================
# Measurement Schemas
# ===========================================

class MeasurementBase(BaseModel):
    """Base measurement schema."""
    metric_key: str = Field(..., max_length=100)
    timestamp: datetime
    value: float
    unit: Optional[str] = Field(None, max_length=50)
    metadata: dict = Field(default_factory=dict)


class MeasurementCreate(MeasurementBase):
    """Schema for creating a measurement."""
    source_id: Optional[UUID] = None


class MeasurementBulkCreate(BaseModel):
    """Schema for bulk creating measurements."""
    measurements: List[MeasurementCreate]


class MeasurementResponse(MeasurementBase):
    """Measurement response."""
    id: UUID
    user_id: UUID
    source_id: Optional[UUID] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MeasurementWithDefinition(MeasurementResponse):
    """Measurement with metric definition."""
    metric: Optional[MetricDefinitionResponse] = None


# ===========================================
# Measurement Query Schemas
# ===========================================

class MeasurementQuery(BaseModel):
    """Query parameters for measurements."""
    metric_key: Optional[str] = None
    metric_keys: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source_id: Optional[UUID] = None
    aggregation: Optional[str] = Field(None, pattern="^(none|hourly|daily|weekly|monthly)$")
    limit: int = Field(default=1000, ge=1, le=10000)
    offset: int = Field(default=0, ge=0)


class MeasurementAggregation(BaseModel):
    """Aggregated measurement data."""
    metric_key: str
    period_start: datetime
    period_end: datetime
    avg_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    sum_value: Optional[float] = None
    count: int
    unit: Optional[str] = None


class MeasurementTimeSeries(BaseModel):
    """Time series data for a metric."""
    metric_key: str
    display_name: str
    unit: str
    category: str
    data: List[dict]  # [{timestamp, value}, ...]
    stats: dict  # {avg, min, max, sum, count, trend}


class MeasurementStats(BaseModel):
    """Statistics for a metric over a period."""
    metric_key: str
    display_name: str
    unit: str
    period_start: datetime
    period_end: datetime
    current_value: Optional[float] = None
    average: Optional[float] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    total: Optional[float] = None
    count: int = 0
    trend_percent: Optional[float] = None  # Change from previous period
    trend_direction: Optional[str] = None  # 'up', 'down', 'stable'


# ===========================================
# Latest Measurements Schema
# ===========================================

class LatestMeasurement(BaseModel):
    """Latest measurement for a metric."""
    metric_key: str
    display_name: str
    category: str
    value: float
    unit: str
    timestamp: datetime
    trend_percent: Optional[float] = None
    trend_direction: Optional[str] = None
    goal: Optional[float] = None
    goal_percent: Optional[float] = None


class LatestMeasurementsList(BaseModel):
    """List of latest measurements."""
    measurements: List[LatestMeasurement]
    as_of: datetime


# ===========================================
# Correlation Schemas
# ===========================================

class CorrelationRequest(BaseModel):
    """Request for correlation analysis."""
    metric_a: str
    metric_b: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    lag_days: int = Field(default=0, ge=-30, le=30)


class CorrelationResult(BaseModel):
    """Correlation analysis result."""
    metric_a: str
    metric_a_display_name: str
    metric_b: str
    metric_b_display_name: str
    correlation_coefficient: float
    p_value: Optional[float] = None
    sample_size: int
    lag_days: int
    is_significant: bool
    interpretation: str  # 'strong_positive', 'moderate_positive', 'weak_positive', 'none', etc.


class CorrelationMatrix(BaseModel):
    """Full correlation matrix for multiple metrics."""
    metrics: List[str]
    metric_display_names: List[str]
    correlations: List[List[Optional[float]]]  # 2D matrix
    sample_sizes: List[List[int]]
