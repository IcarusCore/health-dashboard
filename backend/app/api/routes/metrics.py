"""
Metrics Routes
==============
Metric definitions and metadata management
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db
from app.models.users import User
from app.models.measurements import MetricDefinition
from app.models.custom_metrics import CustomMetric
from app.schemas.metrics import (
    MetricDefinitionResponse,
    MetricDefinitionList,
)
from app.api.dependencies import get_current_user

router = APIRouter()


@router.get("", response_model=List[MetricDefinitionResponse])
async def get_all_metrics(
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: bool = Query(True, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all available metric definitions.
    
    Includes both system metrics and user's custom metrics.
    """
    # Get system metrics
    query = select(MetricDefinition).where(MetricDefinition.is_active == is_active)
    if category:
        query = query.where(MetricDefinition.category == category)
    query = query.order_by(MetricDefinition.sort_order, MetricDefinition.display_name)
    
    result = await db.execute(query)
    system_metrics = result.scalars().all()
    
    # Get user's custom metrics
    custom_query = select(CustomMetric).where(
        CustomMetric.user_id == current_user.id,
        CustomMetric.is_active == is_active,
    )
    if category:
        custom_query = custom_query.where(CustomMetric.category == category)
    
    custom_result = await db.execute(custom_query)
    custom_metrics = custom_result.scalars().all()
    
    # Combine and convert custom metrics to same format
    all_metrics = list(system_metrics)
    for cm in custom_metrics:
        # Convert CustomMetric to MetricDefinition-like response
        all_metrics.append(MetricDefinition(
            id=cm.id,
            metric_key=cm.metric_key,
            display_name=cm.display_name,
            description=cm.description,
            category=cm.category,
            unit=cm.unit,
            data_type=cm.data_type,
            aggregation_method=cm.aggregation_method,
            display_precision=cm.display_precision,
            min_value=cm.min_value,
            max_value=cm.max_value,
            icon=cm.icon,
            color=cm.color,
            sort_order=cm.sort_order,
            is_active=cm.is_active,
        ))
    
    return all_metrics


@router.get("/categories")
async def get_metric_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all metric categories with counts.
    """
    result = await db.execute(
        select(
            MetricDefinition.category,
            func.count(MetricDefinition.id).label('count')
        )
        .where(MetricDefinition.is_active == True)
        .group_by(MetricDefinition.category)
        .order_by(MetricDefinition.category)
    )
    
    categories = []
    for row in result:
        categories.append({
            "category": row.category,
            "count": row.count,
            "display_name": row.category.replace('_', ' ').title(),
        })
    
    return categories


@router.get("/grouped", response_model=List[MetricDefinitionList])
async def get_metrics_grouped_by_category(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all metrics grouped by category.
    """
    result = await db.execute(
        select(MetricDefinition)
        .where(MetricDefinition.is_active == True)
        .order_by(MetricDefinition.category, MetricDefinition.sort_order)
    )
    metrics = result.scalars().all()
    
    # Group by category
    grouped = {}
    for metric in metrics:
        if metric.category not in grouped:
            grouped[metric.category] = []
        grouped[metric.category].append(metric)
    
    return [
        MetricDefinitionList(category=cat, metrics=metrics)
        for cat, metrics in grouped.items()
    ]


@router.get("/{metric_key}", response_model=MetricDefinitionResponse)
async def get_metric(
    metric_key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific metric definition by key.
    """
    # Try system metrics first
    result = await db.execute(
        select(MetricDefinition).where(MetricDefinition.metric_key == metric_key)
    )
    metric = result.scalar_one_or_none()
    
    if not metric:
        # Try custom metrics
        result = await db.execute(
            select(CustomMetric).where(
                CustomMetric.metric_key == metric_key,
                CustomMetric.user_id == current_user.id,
            )
        )
        custom = result.scalar_one_or_none()
        
        if not custom:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Metric not found",
            )
        
        # Convert to MetricDefinition response
        return MetricDefinitionResponse(
            id=custom.id,
            metric_key=custom.metric_key,
            display_name=custom.display_name,
            description=custom.description,
            category=custom.category,
            unit=custom.unit,
            data_type=custom.data_type,
            aggregation_method=custom.aggregation_method,
            display_precision=custom.display_precision,
            min_value=custom.min_value,
            max_value=custom.max_value,
            icon=custom.icon,
            color=custom.color,
            sort_order=custom.sort_order,
            is_active=custom.is_active,
            created_at=custom.created_at,
        )
    
    return metric


# ===========================================
# Custom Metrics CRUD
# ===========================================

@router.post("/custom", status_code=status.HTTP_201_CREATED)
async def create_custom_metric(
    metric_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a custom metric for the current user.
    """
    # Check if metric key already exists
    result = await db.execute(
        select(MetricDefinition).where(MetricDefinition.metric_key == metric_data.get('metric_key'))
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Metric key already exists as a system metric",
        )
    
    result = await db.execute(
        select(CustomMetric).where(
            CustomMetric.metric_key == metric_data.get('metric_key'),
            CustomMetric.user_id == current_user.id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Custom metric with this key already exists",
        )
    
    custom_metric = CustomMetric(
        user_id=current_user.id,
        **metric_data,
    )
    db.add(custom_metric)
    await db.commit()
    await db.refresh(custom_metric)
    
    return custom_metric


@router.delete("/custom/{metric_key}")
async def delete_custom_metric(
    metric_key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a custom metric.
    
    Note: This does not delete measurements with this metric key.
    """
    result = await db.execute(
        select(CustomMetric).where(
            CustomMetric.metric_key == metric_key,
            CustomMetric.user_id == current_user.id,
        )
    )
    custom = result.scalar_one_or_none()
    
    if not custom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom metric not found",
        )
    
    await db.delete(custom)
    await db.commit()
    
    return {"message": "Custom metric deleted successfully"}
