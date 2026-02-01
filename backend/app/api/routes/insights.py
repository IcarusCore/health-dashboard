"""
Insights Routes
===============
Health insights and recommendations
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.users import User
from app.models.insights import HealthInsight
from app.schemas.analytics import InsightResponse, InsightUpdate, InsightsList
from app.api.dependencies import get_current_user, Pagination, get_pagination

router = APIRouter()


@router.get("", response_model=InsightsList)
async def get_insights(
    insight_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    pagination: Pagination = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get health insights with optional filters."""
    query = select(HealthInsight).where(
        HealthInsight.user_id == current_user.id,
        HealthInsight.is_dismissed == False,
    )
    
    if insight_type:
        query = query.where(HealthInsight.insight_type == insight_type)
    if category:
        query = query.where(HealthInsight.category == category)
    if severity:
        query = query.where(HealthInsight.severity == severity)
    if is_read is not None:
        query = query.where(HealthInsight.is_read == is_read)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get unread count
    unread_result = await db.execute(
        select(func.count()).where(
            HealthInsight.user_id == current_user.id,
            HealthInsight.is_read == False,
            HealthInsight.is_dismissed == False,
        )
    )
    unread_count = unread_result.scalar() or 0
    
    # Apply pagination and ordering
    query = query.order_by(HealthInsight.priority, desc(HealthInsight.created_at))
    query = query.offset(pagination.offset).limit(pagination.limit)
    
    result = await db.execute(query)
    insights = result.scalars().all()
    
    return InsightsList(
        insights=[InsightResponse.model_validate(i) for i in insights],
        total=total,
        unread_count=unread_count,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{insight_id}", response_model=InsightResponse)
async def get_insight(
    insight_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific insight."""
    result = await db.execute(
        select(HealthInsight).where(
            HealthInsight.id == insight_id,
            HealthInsight.user_id == current_user.id,
        )
    )
    insight = result.scalar_one_or_none()
    
    if not insight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")
    
    return insight


@router.patch("/{insight_id}", response_model=InsightResponse)
async def update_insight(
    insight_id: UUID,
    update_data: InsightUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an insight (mark as read, dismiss, pin)."""
    result = await db.execute(
        select(HealthInsight).where(
            HealthInsight.id == insight_id,
            HealthInsight.user_id == current_user.id,
        )
    )
    insight = result.scalar_one_or_none()
    
    if not insight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(insight, field, value)
    
    await db.commit()
    await db.refresh(insight)
    
    return insight


@router.post("/mark-all-read")
async def mark_all_insights_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all insights as read."""
    from sqlalchemy import update
    
    await db.execute(
        update(HealthInsight)
        .where(HealthInsight.user_id == current_user.id)
        .values(is_read=True)
    )
    await db.commit()
    
    return {"message": "All insights marked as read"}


@router.delete("/{insight_id}")
async def dismiss_insight(
    insight_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dismiss an insight."""
    result = await db.execute(
        select(HealthInsight).where(
            HealthInsight.id == insight_id,
            HealthInsight.user_id == current_user.id,
        )
    )
    insight = result.scalar_one_or_none()
    
    if not insight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")
    
    insight.is_dismissed = True
    await db.commit()
    
    return {"message": "Insight dismissed"}


@router.post("/generate")
async def generate_insights(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate new health insights based on recent data."""
    from app.services.insights_service import InsightsService
    
    service = InsightsService(db, current_user.id)
    insights = await service.generate_insights()
    
    return {"message": f"Generated {len(insights)} new insights", "count": len(insights)}
