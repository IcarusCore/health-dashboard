"""
Alerts Routes
=============
Health alert configuration and management
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.users import User
from app.models.alerts import Alert, AlertNotification
from app.schemas.analytics import (
    AlertCreate, AlertUpdate, AlertResponse, AlertMute,
    AlertNotificationResponse, AlertTestResult,
)
from app.api.dependencies import get_current_user

router = APIRouter()


@router.get("", response_model=List[AlertResponse])
async def get_alerts(
    is_active: Optional[bool] = Query(None),
    alert_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all alerts for the current user."""
    query = select(Alert).where(Alert.user_id == current_user.id)
    
    if is_active is not None:
        query = query.where(Alert.is_active == is_active)
    if alert_type:
        query = query.where(Alert.alert_type == alert_type)
    
    query = query.order_by(Alert.priority, Alert.created_at)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new alert."""
    alert = Alert(
        user_id=current_user.id,
        **alert_data.model_dump(),
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    
    return alert


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific alert."""
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.user_id == current_user.id,
        )
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    
    return alert


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: UUID,
    update_data: AlertUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an alert."""
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.user_id == current_user.id,
        )
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(alert, field, value)
    
    await db.commit()
    await db.refresh(alert)
    
    return alert


@router.post("/{alert_id}/mute")
async def mute_alert(
    alert_id: UUID,
    mute_data: AlertMute,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mute an alert for a specified duration."""
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.user_id == current_user.id,
        )
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    
    alert.is_muted = True
    alert.muted_until = datetime.utcnow() + timedelta(hours=mute_data.mute_hours)
    
    await db.commit()
    
    return {"message": f"Alert muted until {alert.muted_until.isoformat()}"}


@router.post("/{alert_id}/unmute")
async def unmute_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unmute an alert."""
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.user_id == current_user.id,
        )
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    
    alert.is_muted = False
    alert.muted_until = None
    
    await db.commit()
    
    return {"message": "Alert unmuted"}


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an alert."""
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.user_id == current_user.id,
        )
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    
    await db.delete(alert)
    await db.commit()
    
    return {"message": "Alert deleted"}


@router.get("/{alert_id}/notifications", response_model=List[AlertNotificationResponse])
async def get_alert_notifications(
    alert_id: UUID,
    limit: int = Query(default=50, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get notification history for an alert."""
    result = await db.execute(
        select(AlertNotification)
        .where(
            AlertNotification.alert_id == alert_id,
            AlertNotification.user_id == current_user.id,
        )
        .order_by(desc(AlertNotification.created_at))
        .limit(limit)
    )
    return result.scalars().all()
