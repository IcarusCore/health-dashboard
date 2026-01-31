"""
Dashboard Routes
================
Dashboard data and configuration endpoints
"""

from datetime import datetime, timedelta, date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.users import User, UserSettings, DataSource
from app.models.daily_summary import DailySummary
from app.models.measurements import Measurement
from app.models.workouts import Workout
from app.models.sleep import SleepSession
from app.models.insights import HealthInsight
from app.schemas.activities import DashboardOverview, DailySummaryResponse
from app.api.dependencies import get_current_user

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard overview data."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)
    
    # Get today's summary
    today_result = await db.execute(
        select(DailySummary).where(
            DailySummary.user_id == current_user.id,
            DailySummary.date == today,
        )
    )
    today_summary = today_result.scalar_one_or_none()
    
    # Get yesterday's summary
    yesterday_result = await db.execute(
        select(DailySummary).where(
            DailySummary.user_id == current_user.id,
            DailySummary.date == yesterday,
        )
    )
    yesterday_summary = yesterday_result.scalar_one_or_none()
    
    # Get user settings for goals
    settings_result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    user_settings = settings_result.scalar_one_or_none()
    
    # Calculate streaks
    steps_goal = user_settings.daily_steps_goal if user_settings else 10000
    exercise_goal = user_settings.daily_active_minutes_goal if user_settings else 30
    sleep_goal = user_settings.sleep_hours_goal if user_settings else 8.0
    
    # Get summaries for streak calculation
    summaries_result = await db.execute(
        select(DailySummary)
        .where(DailySummary.user_id == current_user.id)
        .order_by(desc(DailySummary.date))
        .limit(90)
    )
    summaries = summaries_result.scalars().all()
    
    # Calculate steps streak
    steps_streak = 0
    for s in summaries:
        if s.steps and s.steps >= steps_goal:
            steps_streak += 1
        else:
            break
    
    # Calculate exercise streak
    exercise_streak = 0
    for s in summaries:
        if s.exercise_minutes and s.exercise_minutes >= exercise_goal:
            exercise_streak += 1
        else:
            break
    
    # Calculate sleep streak
    sleep_streak = 0
    for s in summaries:
        if s.sleep_duration_hours and s.sleep_duration_hours >= sleep_goal:
            sleep_streak += 1
        else:
            break
    
    # Get week averages
    week_summaries = [s for s in summaries if s.date >= week_ago]
    week_avg_steps = None
    week_avg_sleep = None
    week_avg_score = None
    
    if week_summaries:
        steps_vals = [s.steps for s in week_summaries if s.steps]
        week_avg_steps = sum(steps_vals) / len(steps_vals) if steps_vals else None
        
        sleep_vals = [s.sleep_duration_hours for s in week_summaries if s.sleep_duration_hours]
        week_avg_sleep = sum(sleep_vals) / len(sleep_vals) if sleep_vals else None
        
        score_vals = [s.activity_score for s in week_summaries if s.activity_score]
        week_avg_score = sum(score_vals) / len(score_vals) if score_vals else None
    
    # Get 7-day trends for weight and HRV
    weight_trend = None
    hrv_trend = None
    
    # Get unread insights count
    unread_result = await db.execute(
        select(func.count()).where(
            HealthInsight.user_id == current_user.id,
            HealthInsight.is_read == False,
            HealthInsight.is_dismissed == False,
        )
    )
    unread_insights = unread_result.scalar() or 0
    
    # Get last sync time
    source_result = await db.execute(
        select(DataSource)
        .where(DataSource.user_id == current_user.id)
        .order_by(desc(DataSource.last_sync_at))
        .limit(1)
    )
    source = source_result.scalar_one_or_none()
    last_sync = source.last_sync_at if source else None
    
    return DashboardOverview(
        today=DailySummaryResponse.model_validate(today_summary) if today_summary else None,
        yesterday=DailySummaryResponse.model_validate(yesterday_summary) if yesterday_summary else None,
        steps_streak=steps_streak,
        exercise_streak=exercise_streak,
        sleep_streak=sleep_streak,
        week_avg_steps=week_avg_steps,
        week_avg_sleep_hours=week_avg_sleep,
        week_avg_activity_score=week_avg_score,
        weight_trend_7day=weight_trend,
        hrv_trend_7day=hrv_trend,
        unread_insights=unread_insights,
        last_sync_at=last_sync,
    )


@router.get("/daily/{date_str}", response_model=Optional[DailySummaryResponse])
async def get_daily_summary(
    date_str: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get daily summary for a specific date."""
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        target_date = date.today()
    
    result = await db.execute(
        select(DailySummary).where(
            DailySummary.user_id == current_user.id,
            DailySummary.date == target_date,
        )
    )
    return result.scalar_one_or_none()


@router.post("/daily/refresh")
async def refresh_daily_summary(
    date_str: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually refresh/recalculate daily summary."""
    from app.services.summary_service import SummaryService
    
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else date.today()
    except ValueError:
        target_date = date.today()
    
    service = SummaryService(db, current_user.id)
    summary = await service.calculate_daily_summary(target_date)
    
    return {"message": f"Summary refreshed for {target_date}", "summary_id": str(summary.id)}
