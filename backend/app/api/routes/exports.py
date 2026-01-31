"""
Export Routes
=============
Data export functionality
"""

from datetime import datetime, date
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import json
import io

from app.models.database import get_db
from app.models.users import User
from app.models.measurements import Measurement
from app.models.workouts import Workout
from app.models.sleep import SleepSession
from app.schemas.analytics import ExportRequest, ExportResponse
from app.api.dependencies import get_current_user

router = APIRouter()


@router.post("", response_model=ExportResponse)
async def create_export(
    request: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Request a data export.
    
    Returns immediately with export info. For large exports,
    the download_url will be available when processing completes.
    """
    export_id = uuid4()
    
    # For small exports, generate immediately
    # For larger ones, you'd queue a background task
    
    return ExportResponse(
        export_id=export_id,
        status="ready",
        format=request.format,
        file_size_bytes=None,
        download_url=f"/api/v1/exports/{export_id}/download",
        expires_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )


@router.get("/{export_id}/download")
async def download_export(
    export_id: str,
    format: str = "json",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download exported data."""
    
    # Parse dates
    start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    
    # Fetch data
    measurements_query = select(Measurement).where(Measurement.user_id == current_user.id)
    if start:
        measurements_query = measurements_query.where(Measurement.timestamp >= start)
    if end:
        measurements_query = measurements_query.where(Measurement.timestamp <= end)
    
    measurements_result = await db.execute(measurements_query.limit(10000))
    measurements = measurements_result.scalars().all()
    
    workouts_query = select(Workout).where(Workout.user_id == current_user.id)
    if start:
        workouts_query = workouts_query.where(Workout.start_time >= start)
    if end:
        workouts_query = workouts_query.where(Workout.end_time <= end)
    
    workouts_result = await db.execute(workouts_query)
    workouts = workouts_result.scalars().all()
    
    sleep_query = select(SleepSession).where(SleepSession.user_id == current_user.id)
    if start:
        sleep_query = sleep_query.where(SleepSession.start_time >= start)
    if end:
        sleep_query = sleep_query.where(SleepSession.end_time <= end)
    
    sleep_result = await db.execute(sleep_query)
    sleep_sessions = sleep_result.scalars().all()
    
    if format == "json":
        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "user_id": str(current_user.id),
            "measurements": [
                {
                    "metric_key": m.metric_key,
                    "value": float(m.value),
                    "unit": m.unit,
                    "timestamp": m.timestamp.isoformat(),
                }
                for m in measurements
            ],
            "workouts": [
                {
                    "type": w.workout_type,
                    "start_time": w.start_time.isoformat(),
                    "end_time": w.end_time.isoformat(),
                    "duration_seconds": w.duration_seconds,
                    "distance_meters": float(w.distance_meters) if w.distance_meters else None,
                    "calories": float(w.total_calories) if w.total_calories else None,
                }
                for w in workouts
            ],
            "sleep_sessions": [
                {
                    "start_time": s.start_time.isoformat(),
                    "end_time": s.end_time.isoformat(),
                    "duration_hours": s.duration_hours,
                    "efficiency": float(s.sleep_efficiency) if s.sleep_efficiency else None,
                    "score": s.sleep_score,
                }
                for s in sleep_sessions
            ],
        }
        
        content = json.dumps(data, indent=2)
        media_type = "application/json"
        filename = f"health_export_{datetime.utcnow().strftime('%Y%m%d')}.json"
        
    elif format == "csv":
        # Create CSV for measurements
        lines = ["metric_key,value,unit,timestamp"]
        for m in measurements:
            lines.append(f"{m.metric_key},{m.value},{m.unit or ''},{m.timestamp.isoformat()}")
        
        content = "\n".join(lines)
        media_type = "text/csv"
        filename = f"health_export_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format: {format}",
        )
    
    return StreamingResponse(
        io.BytesIO(content.encode()),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
