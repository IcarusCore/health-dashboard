"""
Workout Routes
==============
Workout and exercise activity management
"""

from datetime import datetime, timedelta, date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.users import User
from app.models.workouts import Workout
from app.schemas.activities import (
    WorkoutCreate,
    WorkoutUpdate,
    WorkoutResponse,
    WorkoutSummary,
    WorkoutStreak,
)
from app.api.dependencies import get_current_user, Pagination, get_pagination

router = APIRouter()


@router.get("", response_model=List[WorkoutResponse])
async def get_workouts(
    workout_type: Optional[str] = Query(None, description="Filter by workout type"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    pagination: Pagination = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get workouts with optional filters.
    """
    query = select(Workout).where(Workout.user_id == current_user.id)
    
    if workout_type:
        query = query.where(Workout.workout_type == workout_type)
    if start_date:
        query = query.where(Workout.start_time >= start_date)
    if end_date:
        query = query.where(Workout.end_time <= end_date)
    
    query = query.order_by(desc(Workout.start_time))
    query = query.offset(pagination.offset).limit(pagination.limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
async def create_workout(
    workout: WorkoutCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new workout.
    """
    db_workout = Workout(
        user_id=current_user.id,
        **workout.model_dump(),
    )
    db.add(db_workout)
    await db.commit()
    await db.refresh(db_workout)
    
    return db_workout


@router.get("/types")
async def get_workout_types(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all workout types used by the current user with counts.
    """
    result = await db.execute(
        select(
            Workout.workout_type,
            func.count(Workout.id).label('count'),
            func.sum(Workout.duration_seconds).label('total_duration'),
        )
        .where(Workout.user_id == current_user.id)
        .group_by(Workout.workout_type)
        .order_by(desc(func.count(Workout.id)))
    )
    
    types = []
    for row in result:
        types.append({
            "type": row.workout_type,
            "display_name": row.workout_type.replace('_', ' ').title(),
            "count": row.count,
            "total_hours": round(row.total_duration / 3600, 1) if row.total_duration else 0,
        })
    
    return types


@router.get("/summary", response_model=WorkoutSummary)
async def get_workout_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get workout summary statistics for a period.
    """
    # Default to last 30 days
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Get aggregate stats
    result = await db.execute(
        select(
            func.count(Workout.id).label('count'),
            func.sum(Workout.duration_seconds).label('total_duration'),
            func.sum(Workout.distance_meters).label('total_distance'),
            func.sum(Workout.total_calories).label('total_calories'),
            func.avg(Workout.avg_heart_rate).label('avg_hr'),
        )
        .where(
            Workout.user_id == current_user.id,
            func.date(Workout.start_time) >= start_date,
            func.date(Workout.start_time) <= end_date,
        )
    )
    row = result.one()
    
    # Get workouts by type
    type_result = await db.execute(
        select(
            Workout.workout_type,
            func.count(Workout.id).label('count'),
        )
        .where(
            Workout.user_id == current_user.id,
            func.date(Workout.start_time) >= start_date,
            func.date(Workout.start_time) <= end_date,
        )
        .group_by(Workout.workout_type)
    )
    
    workouts_by_type = {r.workout_type: r.count for r in type_result}
    
    total_duration = row.total_duration or 0
    total_count = row.count or 0
    
    return WorkoutSummary(
        period_start=start_date,
        period_end=end_date,
        total_workouts=total_count,
        total_duration_minutes=round(total_duration / 60, 1),
        total_distance_km=round((row.total_distance or 0) / 1000, 2),
        total_calories=round(row.total_calories or 0, 0),
        workouts_by_type=workouts_by_type,
        avg_duration_minutes=round(total_duration / 60 / total_count, 1) if total_count > 0 else 0,
        avg_heart_rate=round(row.avg_hr, 0) if row.avg_hr else None,
    )


@router.get("/streak", response_model=WorkoutStreak)
async def get_workout_streak(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the current workout streak (consecutive days with workouts).
    """
    # Get all workout dates
    result = await db.execute(
        select(func.date(Workout.start_time).label('workout_date'))
        .where(Workout.user_id == current_user.id)
        .distinct()
        .order_by(desc(func.date(Workout.start_time)))
    )
    
    dates = [row.workout_date for row in result]
    
    if not dates:
        return WorkoutStreak(
            current_streak_days=0,
            longest_streak_days=0,
            last_workout_date=None,
            streak_start_date=None,
        )
    
    today = date.today()
    last_workout = dates[0]
    
    # Calculate current streak
    current_streak = 0
    streak_start = None
    
    # Only count if last workout was today or yesterday
    if last_workout >= today - timedelta(days=1):
        current_date = last_workout
        for workout_date in dates:
            if workout_date == current_date:
                current_streak += 1
                streak_start = workout_date
                current_date = workout_date - timedelta(days=1)
            elif workout_date < current_date:
                break
    
    # Calculate longest streak
    longest_streak = 0
    temp_streak = 0
    prev_date = None
    
    for workout_date in sorted(dates):
        if prev_date is None or workout_date == prev_date + timedelta(days=1):
            temp_streak += 1
        else:
            longest_streak = max(longest_streak, temp_streak)
            temp_streak = 1
        prev_date = workout_date
    
    longest_streak = max(longest_streak, temp_streak)
    
    return WorkoutStreak(
        current_streak_days=current_streak,
        longest_streak_days=longest_streak,
        last_workout_date=last_workout,
        streak_start_date=streak_start,
    )


@router.get("/{workout_id}", response_model=WorkoutResponse)
async def get_workout(
    workout_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific workout by ID.
    """
    result = await db.execute(
        select(Workout).where(
            Workout.id == workout_id,
            Workout.user_id == current_user.id,
        )
    )
    workout = result.scalar_one_or_none()
    
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )
    
    return workout


@router.patch("/{workout_id}", response_model=WorkoutResponse)
async def update_workout(
    workout_id: UUID,
    update_data: WorkoutUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a workout.
    """
    result = await db.execute(
        select(Workout).where(
            Workout.id == workout_id,
            Workout.user_id == current_user.id,
        )
    )
    workout = result.scalar_one_or_none()
    
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(workout, field, value)
    
    await db.commit()
    await db.refresh(workout)
    
    return workout


@router.delete("/{workout_id}")
async def delete_workout(
    workout_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a workout.
    """
    result = await db.execute(
        select(Workout).where(
            Workout.id == workout_id,
            Workout.user_id == current_user.id,
        )
    )
    workout = result.scalar_one_or_none()
    
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found",
        )
    
    await db.delete(workout)
    await db.commit()
    
    return {"message": "Workout deleted successfully"}
