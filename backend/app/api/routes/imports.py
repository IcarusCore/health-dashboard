"""
Import Routes
=============
Data import endpoints for Apple Health exports
"""

import os
import hashlib
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.database import get_db
from app.models.users import User, DataSource
from app.models.imports import ImportHistory
from app.schemas.analytics import ImportResponse, ImportSummary, ImportProgress
from app.api.dependencies import get_current_user
from app.services.apple_health_parser import process_apple_health_export

router = APIRouter()


@router.post("/apple-health", response_model=ImportResponse, status_code=status.HTTP_202_ACCEPTED)
async def import_apple_health(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Apple Health export.xml or export.zip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Import Apple Health export data.
    
    Accepts either:
    - export.xml (uncompressed Apple Health export)
    - export.zip (compressed Apple Health export)
    
    The import runs in the background. Use the returned import_id to check progress.
    """
    filename = file.filename or "unknown"
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    
    if ext not in ['xml', 'zip']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be .xml or .zip",
        )
    
    content = await file.read()
    file_size = len(content)
    
    if file_size > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB",
        )
    
    file_hash = hashlib.sha256(content).hexdigest()
    
    existing = await db.execute(
        select(ImportHistory).where(
            ImportHistory.user_id == current_user.id,
            ImportHistory.file_hash == file_hash,
            ImportHistory.status == 'completed',
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This file has already been imported",
        )
    
    source_result = await db.execute(
        select(DataSource).where(
            DataSource.user_id == current_user.id,
            DataSource.source_type == 'apple_health',
        )
    )
    source = source_result.scalar_one_or_none()
    
    if not source:
        source = DataSource(
            user_id=current_user.id,
            source_type='apple_health',
            source_name='Apple Health',
            is_active=True,
        )
        db.add(source)
        await db.flush()
    
    import_record = ImportHistory(
        user_id=current_user.id,
        source_id=source.id,
        filename=filename,
        file_size_bytes=file_size,
        file_hash=file_hash,
        status='pending',
        current_phase='uploading',
    )
    db.add(import_record)
    await db.commit()
    await db.refresh(import_record)
    
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{import_record.id}_{filename}")
    with open(file_path, 'wb') as f:
        f.write(content)
    
    background_tasks.add_task(
        process_apple_health_export,
        import_id=str(import_record.id),
        user_id=str(current_user.id),
        source_id=str(source.id),
        file_path=file_path,
        is_zip=ext == 'zip',
    )
    
    return import_record


@router.get("", response_model=List[ImportResponse])
async def get_import_history(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get import history for the current user."""
    query = select(ImportHistory).where(ImportHistory.user_id == current_user.id)
    
    if status_filter:
        query = query.where(ImportHistory.status == status_filter)
    
    query = query.order_by(desc(ImportHistory.created_at))
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/summary", response_model=ImportSummary)
async def get_import_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get summary of all imports."""
    result = await db.execute(
        select(ImportHistory).where(ImportHistory.user_id == current_user.id)
    )
    imports = result.scalars().all()
    
    total = len(imports)
    successful = sum(1 for i in imports if i.status == 'completed')
    failed = sum(1 for i in imports if i.status == 'failed')
    
    total_records = sum(i.records_imported for i in imports if i.status == 'completed')
    total_measurements = sum(i.measurements_imported for i in imports if i.status == 'completed')
    total_workouts = sum(i.workouts_imported for i in imports if i.status == 'completed')
    total_sleep = sum(i.sleep_sessions_imported for i in imports if i.status == 'completed')
    
    dates = [i.data_start_date for i in imports if i.data_start_date]
    date_start = min(dates).date() if dates else None
    dates = [i.data_end_date for i in imports if i.data_end_date]
    date_end = max(dates).date() if dates else None
    
    return ImportSummary(
        total_imports=total,
        successful_imports=successful,
        failed_imports=failed,
        total_records_imported=total_records,
        total_measurements=total_measurements,
        total_workouts=total_workouts,
        total_sleep_sessions=total_sleep,
        date_range_start=date_start,
        date_range_end=date_end,
    )


@router.get("/{import_id}", response_model=ImportResponse)
async def get_import(
    import_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific import by ID."""
    result = await db.execute(
        select(ImportHistory).where(
            ImportHistory.id == import_id,
            ImportHistory.user_id == current_user.id,
        )
    )
    import_record = result.scalar_one_or_none()
    
    if not import_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import not found",
        )
    
    return import_record


@router.get("/{import_id}/progress", response_model=ImportProgress)
async def get_import_progress(
    import_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the progress of an ongoing import."""
    result = await db.execute(
        select(ImportHistory).where(
            ImportHistory.id == import_id,
            ImportHistory.user_id == current_user.id,
        )
    )
    import_record = result.scalar_one_or_none()
    
    if not import_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import not found",
        )
    
    return ImportProgress(
        import_id=import_record.id,
        status=import_record.status,
        progress_percent=import_record.progress_percent,
        current_phase=import_record.current_phase,
        records_processed=import_record.records_imported + import_record.records_skipped + import_record.records_failed,
        records_total=import_record.records_total,
        message=import_record.error_message if import_record.status == 'failed' else None,
    )


@router.delete("/{import_id}")
async def delete_import(
    import_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an import record."""
    result = await db.execute(
        select(ImportHistory).where(
            ImportHistory.id == import_id,
            ImportHistory.user_id == current_user.id,
        )
    )
    import_record = result.scalar_one_or_none()
    
    if not import_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import not found",
        )
    
    if import_record.status in ['pending', 'processing']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete an import that is in progress",
        )
    
    await db.delete(import_record)
    await db.commit()
    
    return {"message": "Import record deleted successfully"}
