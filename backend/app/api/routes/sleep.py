"""
Sleep Routes
============
Sleep session tracking and analysis
"""

from datetime import datetime, timedelta, date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.users import User
from app.models.sleep import SleepSession
from app.schemas.activities import (
    SleepSessionCreate,
    SleepSessionResponse,
    SleepSummary,
    SleepStagesBreakdown,
)
from app.api.dependencies import get_current_user, Pagination, get_pagination

router = APIRouter()


@router.get("", response_model=List[SleepSessionResponse])
async def get_sleep_sessions(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    pagination: Pagination = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get sleep sessions with optional filters.
    """
    query = select(SleepSession).where(SleepSession.user_id == current_user.id)
    
    if start_date:
        query = query.where(SleepSession.start_time >= start_date)
    if end_date:
        query = query.where(SleepSession.end_time <= end_date)
    
    query = query.order_by(desc(SleepSession.start_time))
    query = query.offset(pagination.offset).limit(pagination.limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=SleepSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_sleep_session(
    session: SleepSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new sleep session.
    """
    db_session = SleepSession(
        user_id=current_user.id,
        **session.model_dump(),
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    
    return db_session


@router.get("/latest", response_model=Optional[SleepSessionResponse])
async def get_latest_sleep(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the most recent sleep session.
    """
    result = await db.execute(
        select(SleepSession)
        .where(SleepSession.user_id == current_user.id)
        .order_by(desc(SleepSession.end_time))
        .limit(1)
    )
    return result.scalar_one_or_none()


@router.get("/summary", response_model=SleepSummary)
async def get_sleep_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get sleep summary statistics for a period.
    """
    # Default to last 30 days
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Get sleep sessions in range
    result = await db.execute(
        select(SleepSession)
        .where(
            SleepSession.user_id == current_user.id,
            func.date(SleepSession.start_time) >= start_date,
            func.date(SleepSession.start_time) <= end_date,
        )
        .order_by(SleepSession.start_time)
    )
    sessions = result.scalars().all()
    
    if not sessions:
        return SleepSummary(
            period_start=start_date,
            period_end=end_date,
            total_nights=0,
            avg_duration_hours=0,
            avg_efficiency=None,
            avg_deep_percent=None,
            avg_rem_percent=None,
            avg_sleep_score=None,
            avg_bedtime=None,
            avg_wake_time=None,
            consistency_score=None,
        )
    
    # Calculate averages
    total_duration = sum(s.duration_seconds for s in sessions)
    avg_duration = total_duration / len(sessions) / 3600
    
    efficiencies = [s.sleep_efficiency for s in sessions if s.sleep_efficiency]
    avg_efficiency = sum(efficiencies) / len(efficiencies) if efficiencies else None
    
    deep_percents = [s.deep_sleep_percent for s in sessions if s.deep_sleep_percent is not None]
    avg_deep = sum(deep_percents) / len(deep_percents) if deep_percents else None
    
    rem_percents = [s.rem_sleep_percent for s in sessions if s.rem_sleep_percent is not None]
    avg_rem = sum(rem_percents) / len(rem_percents) if rem_percents else None
    
    scores = [s.sleep_score for s in sessions if s.sleep_score is not None]
    avg_score = sum(scores) / len(scores) if scores else None
    
    # Calculate average bedtime and wake time
    bedtimes = []
    waketimes = []
    for s in sessions:
        # Convert to minutes from midnight for averaging
        bedtime_mins = s.start_time.hour * 60 + s.start_time.minute
        # Handle times after midnight (treat as previous day)
        if s.start_time.hour < 6:
            bedtime_mins += 24 * 60
        bedtimes.append(bedtime_mins)
        
        waketime_mins = s.end_time.hour * 60 + s.end_time.minute
        waketimes.append(waketime_mins)
    
    avg_bedtime_mins = sum(bedtimes) / len(bedtimes)
    avg_waketime_mins = sum(waketimes) / len(waketimes)
    
    # Convert back to time string
    if avg_bedtime_mins >= 24 * 60:
        avg_bedtime_mins -= 24 * 60
    avg_bedtime = f"{int(avg_bedtime_mins // 60):02d}:{int(avg_bedtime_mins % 60):02d}"
    avg_waketime = f"{int(avg_waketime_mins // 60):02d}:{int(avg_waketime_mins % 60):02d}"
    
    # Calculate consistency score (based on bedtime variance)
    if len(bedtimes) > 1:
        import statistics
        bedtime_std = statistics.stdev(bedtimes)
        # Lower variance = higher consistency. 60 min std = 50%, 0 min = 100%
        consistency_score = max(0, min(100, 100 - (bedtime_std / 60) * 50))
    else:
        consistency_score = None
    
    return SleepSummary(
        period_start=start_date,
        period_end=end_date,
        total_nights=len(sessions),
        avg_duration_hours=round(avg_duration, 2),
        avg_efficiency=round(avg_efficiency, 1) if avg_efficiency else None,
        avg_deep_percent=round(avg_deep, 1) if avg_deep else None,
        avg_rem_percent=round(avg_rem, 1) if avg_rem else None,
        avg_sleep_score=round(avg_score, 0) if avg_score else None,
        avg_bedtime=avg_bedtime,
        avg_wake_time=avg_waketime,
        consistency_score=round(consistency_score, 0) if consistency_score else None,
    )


@router.get("/stages", response_model=List[SleepStagesBreakdown])
async def get_sleep_stages_breakdown(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get sleep stages breakdown for each night in a period.
    """
    # Default to last 14 days
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=14)
    
    result = await db.execute(
        select(SleepSession)
        .where(
            SleepSession.user_id == current_user.id,
            func.date(SleepSession.start_time) >= start_date,
            func.date(SleepSession.start_time) <= end_date,
        )
        .order_by(SleepSession.start_time)
    )
    sessions = result.scalars().all()
    
    breakdown = []
    for s in sessions:
        breakdown.append(SleepStagesBreakdown(
            date=s.sleep_date,
            deep_hours=s.time_deep_hours,
            light_hours=s.time_light_hours,
            rem_hours=s.time_rem_hours,
            awake_hours=s.time_awake_hours,
            total_hours=s.duration_hours,
            efficiency=float(s.sleep_efficiency) if s.sleep_efficiency else None,
            score=s.sleep_score,
        ))
    
    return breakdown


@router.get("/{session_id}", response_model=SleepSessionResponse)
async def get_sleep_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific sleep session by ID.
    """
    result = await db.execute(
        select(SleepSession).where(
            SleepSession.id == session_id,
            SleepSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sleep session not found",
        )
    
    return session


@router.delete("/{session_id}")
async def delete_sleep_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a sleep session.
    """
    result = await db.execute(
        select(SleepSession).where(
            SleepSession.id == session_id,
            SleepSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sleep session not found",
        )
    
    await db.delete(session)
    await db.commit()
    
    return {"message": "Sleep session deleted successfully"}
