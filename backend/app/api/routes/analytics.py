"""
Analytics Routes
================
Health data analytics and trend analysis
"""

from datetime import datetime, timedelta, date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.users import User
from app.models.measurements import Measurement, MetricCorrelation
from app.schemas.analytics import TrendAnalysis, CorrelationResult, CorrelationMatrix, HealthReport
from app.schemas.metrics import CorrelationRequest
from app.api.dependencies import get_current_user
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/trends/{metric_key}", response_model=TrendAnalysis)
async def get_metric_trend(
    metric_key: str,
    days: int = Query(default=30, ge=7, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analyze trend for a specific metric."""
    analytics = AnalyticsService(db, current_user.id)
    return await analytics.analyze_trend(metric_key, days)


@router.post("/correlations", response_model=CorrelationResult)
async def calculate_correlation(
    request: CorrelationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Calculate correlation between two metrics."""
    analytics = AnalyticsService(db, current_user.id)
    return await analytics.calculate_correlation(
        request.metric_a,
        request.metric_b,
        request.start_date,
        request.end_date,
        request.lag_days,
    )


@router.get("/correlations/matrix", response_model=CorrelationMatrix)
async def get_correlation_matrix(
    metrics: str = Query(..., description="Comma-separated metric keys"),
    days: int = Query(default=90, ge=14, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get correlation matrix for multiple metrics."""
    metric_list = [m.strip() for m in metrics.split(",")]
    analytics = AnalyticsService(db, current_user.id)
    return await analytics.get_correlation_matrix(metric_list, days)


@router.get("/report", response_model=HealthReport)
async def get_health_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate comprehensive health report."""
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    analytics = AnalyticsService(db, current_user.id)
    return await analytics.generate_health_report(start_date, end_date)
