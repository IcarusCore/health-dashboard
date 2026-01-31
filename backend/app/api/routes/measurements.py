"""
Measurements Routes
===================
Health measurement data CRUD and querying
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.users import User
from app.models.measurements import Measurement, MetricDefinition
from app.schemas.metrics import (
    MeasurementCreate,
    MeasurementBulkCreate,
    MeasurementResponse,
    MeasurementTimeSeries,
    MeasurementStats,
    LatestMeasurement,
    LatestMeasurementsList,
)
from app.api.dependencies import get_current_user, Pagination, get_pagination

router = APIRouter()


@router.get("", response_model=List[MeasurementResponse])
async def get_measurements(
    metric_key: Optional[str] = Query(None, description="Filter by metric key"),
    metric_keys: Optional[str] = Query(None, description="Comma-separated metric keys"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    source_id: Optional[UUID] = Query(None, description="Filter by data source"),
    pagination: Pagination = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get measurements with optional filters.
    """
    query = select(Measurement).where(Measurement.user_id == current_user.id)
    
    # Apply filters
    if metric_key:
        query = query.where(Measurement.metric_key == metric_key)
    elif metric_keys:
        keys = [k.strip() for k in metric_keys.split(",")]
        query = query.where(Measurement.metric_key.in_(keys))
    
    if start_date:
        query = query.where(Measurement.timestamp >= start_date)
    if end_date:
        query = query.where(Measurement.timestamp <= end_date)
    if source_id:
        query = query.where(Measurement.source_id == source_id)
    
    # Order and paginate
    query = query.order_by(desc(Measurement.timestamp))
    query = query.offset(pagination.offset).limit(pagination.limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=MeasurementResponse, status_code=status.HTTP_201_CREATED)
async def create_measurement(
    measurement: MeasurementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a single measurement.
    """
    db_measurement = Measurement(
        user_id=current_user.id,
        **measurement.model_dump(),
    )
    db.add(db_measurement)
    await db.commit()
    await db.refresh(db_measurement)
    
    return db_measurement


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def create_measurements_bulk(
    data: MeasurementBulkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create multiple measurements in a single request.
    """
    measurements = []
    for m in data.measurements:
        measurements.append(Measurement(
            user_id=current_user.id,
            **m.model_dump(),
        ))
    
    db.add_all(measurements)
    await db.commit()
    
    return {
        "message": f"Successfully created {len(measurements)} measurements",
        "count": len(measurements),
    }


@router.get("/latest", response_model=LatestMeasurementsList)
async def get_latest_measurements(
    metric_keys: Optional[str] = Query(None, description="Comma-separated metric keys"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the latest measurement for each metric.
    """
    # Get user's settings for goals
    from app.models.users import UserSettings
    settings_result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    user_settings = settings_result.scalar_one_or_none()
    
    # Build subquery to get latest timestamp per metric
    subquery = (
        select(
            Measurement.metric_key,
            func.max(Measurement.timestamp).label('max_timestamp')
        )
        .where(Measurement.user_id == current_user.id)
        .group_by(Measurement.metric_key)
        .subquery()
    )
    
    # Join to get full measurement data
    query = (
        select(Measurement)
        .join(
            subquery,
            and_(
                Measurement.metric_key == subquery.c.metric_key,
                Measurement.timestamp == subquery.c.max_timestamp,
            )
        )
        .where(Measurement.user_id == current_user.id)
    )
    
    if metric_keys:
        keys = [k.strip() for k in metric_keys.split(",")]
        query = query.where(Measurement.metric_key.in_(keys))
    
    result = await db.execute(query)
    measurements = result.scalars().all()
    
    # Get metric definitions for display names
    metric_defs = {}
    defs_result = await db.execute(select(MetricDefinition))
    for m in defs_result.scalars().all():
        metric_defs[m.metric_key] = m
    
    # Map goals
    goals = {
        'steps': user_settings.daily_steps_goal if user_settings else 10000,
        'active_energy': user_settings.daily_calories_goal if user_settings else 2000,
        'exercise_minutes': user_settings.daily_active_minutes_goal if user_settings else 30,
        'sleep_duration': user_settings.sleep_hours_goal if user_settings else 8.0,
    }
    
    # Calculate trends (compare to 7-day average)
    latest_list = []
    for m in measurements:
        metric_def = metric_defs.get(m.metric_key)
        
        # Get 7-day average for trend
        week_ago = m.timestamp - timedelta(days=7)
        avg_result = await db.execute(
            select(func.avg(Measurement.value))
            .where(
                Measurement.user_id == current_user.id,
                Measurement.metric_key == m.metric_key,
                Measurement.timestamp >= week_ago,
                Measurement.timestamp < m.timestamp,
            )
        )
        avg_value = avg_result.scalar()
        
        trend_percent = None
        trend_direction = None
        if avg_value and avg_value > 0:
            trend_percent = ((m.value - avg_value) / avg_value) * 100
            if trend_percent > 5:
                trend_direction = 'up'
            elif trend_percent < -5:
                trend_direction = 'down'
            else:
                trend_direction = 'stable'
        
        goal = goals.get(m.metric_key)
        goal_percent = None
        if goal and goal > 0:
            goal_percent = (m.value / goal) * 100
        
        latest_list.append(LatestMeasurement(
            metric_key=m.metric_key,
            display_name=metric_def.display_name if metric_def else m.metric_key,
            category=metric_def.category if metric_def else 'custom',
            value=m.value,
            unit=m.unit or (metric_def.unit if metric_def else ''),
            timestamp=m.timestamp,
            trend_percent=trend_percent,
            trend_direction=trend_direction,
            goal=goal,
            goal_percent=goal_percent,
        ))
    
    return LatestMeasurementsList(
        measurements=latest_list,
        as_of=datetime.utcnow(),
    )


@router.get("/stats/{metric_key}", response_model=MeasurementStats)
async def get_measurement_stats(
    metric_key: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get statistics for a specific metric over a time period.
    """
    # Default to last 30 days
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Get metric definition
    def_result = await db.execute(
        select(MetricDefinition).where(MetricDefinition.metric_key == metric_key)
    )
    metric_def = def_result.scalar_one_or_none()
    
    # Calculate stats
    result = await db.execute(
        select(
            func.avg(Measurement.value).label('avg'),
            func.min(Measurement.value).label('min'),
            func.max(Measurement.value).label('max'),
            func.sum(Measurement.value).label('sum'),
            func.count(Measurement.id).label('count'),
        )
        .where(
            Measurement.user_id == current_user.id,
            Measurement.metric_key == metric_key,
            Measurement.timestamp >= start_date,
            Measurement.timestamp <= end_date,
        )
    )
    row = result.one()
    
    # Get latest value
    latest_result = await db.execute(
        select(Measurement.value)
        .where(
            Measurement.user_id == current_user.id,
            Measurement.metric_key == metric_key,
        )
        .order_by(desc(Measurement.timestamp))
        .limit(1)
    )
    current_value = latest_result.scalar()
    
    # Calculate trend vs previous period
    period_length = (end_date - start_date).days
    prev_start = start_date - timedelta(days=period_length)
    prev_end = start_date
    
    prev_result = await db.execute(
        select(func.avg(Measurement.value))
        .where(
            Measurement.user_id == current_user.id,
            Measurement.metric_key == metric_key,
            Measurement.timestamp >= prev_start,
            Measurement.timestamp < prev_end,
        )
    )
    prev_avg = prev_result.scalar()
    
    trend_percent = None
    trend_direction = None
    if prev_avg and prev_avg > 0 and row.avg:
        trend_percent = ((row.avg - prev_avg) / prev_avg) * 100
        if trend_percent > 5:
            trend_direction = 'up'
        elif trend_percent < -5:
            trend_direction = 'down'
        else:
            trend_direction = 'stable'
    
    return MeasurementStats(
        metric_key=metric_key,
        display_name=metric_def.display_name if metric_def else metric_key,
        unit=metric_def.unit if metric_def else '',
        period_start=start_date,
        period_end=end_date,
        current_value=current_value,
        average=row.avg,
        minimum=row.min,
        maximum=row.max,
        total=row.sum,
        count=row.count or 0,
        trend_percent=trend_percent,
        trend_direction=trend_direction,
    )


@router.get("/timeseries/{metric_key}", response_model=MeasurementTimeSeries)
async def get_measurement_timeseries(
    metric_key: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    aggregation: str = Query("daily", pattern="^(none|hourly|daily|weekly)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get time series data for a metric.
    """
    # Default to last 30 days
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Get metric definition
    def_result = await db.execute(
        select(MetricDefinition).where(MetricDefinition.metric_key == metric_key)
    )
    metric_def = def_result.scalar_one_or_none()
    
    if not metric_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metric not found",
        )
    
    # Get raw data
    result = await db.execute(
        select(Measurement)
        .where(
            Measurement.user_id == current_user.id,
            Measurement.metric_key == metric_key,
            Measurement.timestamp >= start_date,
            Measurement.timestamp <= end_date,
        )
        .order_by(Measurement.timestamp)
    )
    measurements = result.scalars().all()
    
    # Format data points
    if aggregation == "none":
        data = [
            {"timestamp": m.timestamp.isoformat(), "value": float(m.value)}
            for m in measurements
        ]
    else:
        # Aggregate data
        from collections import defaultdict
        import pandas as pd
        
        if not measurements:
            data = []
        else:
            df_data = [
                {"timestamp": m.timestamp, "value": float(m.value)}
                for m in measurements
            ]
            df = pd.DataFrame(df_data)
            df.set_index('timestamp', inplace=True)
            
            # Resample based on aggregation
            freq_map = {"hourly": "H", "daily": "D", "weekly": "W"}
            freq = freq_map.get(aggregation, "D")
            
            agg_method = metric_def.aggregation_method or 'mean'
            if agg_method == 'sum':
                resampled = df.resample(freq).sum()
            elif agg_method == 'max':
                resampled = df.resample(freq).max()
            elif agg_method == 'min':
                resampled = df.resample(freq).min()
            elif agg_method == 'last':
                resampled = df.resample(freq).last()
            else:
                resampled = df.resample(freq).mean()
            
            data = [
                {"timestamp": idx.isoformat(), "value": round(float(row['value']), 2) if pd.notna(row['value']) else None}
                for idx, row in resampled.iterrows()
            ]
    
    # Calculate stats
    values = [d['value'] for d in data if d['value'] is not None]
    stats = {}
    if values:
        stats = {
            "avg": round(sum(values) / len(values), 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "sum": round(sum(values), 2),
            "count": len(values),
        }
        # Trend (linear regression slope)
        if len(values) > 1:
            n = len(values)
            x_mean = (n - 1) / 2
            y_mean = sum(values) / n
            numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            if denominator > 0:
                slope = numerator / denominator
                stats["trend"] = "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
            else:
                stats["trend"] = "stable"
    
    return MeasurementTimeSeries(
        metric_key=metric_key,
        display_name=metric_def.display_name,
        unit=metric_def.unit,
        category=metric_def.category,
        data=data,
        stats=stats,
    )


@router.delete("/{measurement_id}")
async def delete_measurement(
    measurement_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a specific measurement.
    """
    result = await db.execute(
        select(Measurement).where(
            Measurement.id == measurement_id,
            Measurement.user_id == current_user.id,
        )
    )
    measurement = result.scalar_one_or_none()
    
    if not measurement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Measurement not found",
        )
    
    await db.delete(measurement)
    await db.commit()
    
    return {"message": "Measurement deleted successfully"}
