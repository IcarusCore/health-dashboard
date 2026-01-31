"""
Celery Application
==================
Background task queue configuration
"""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

# Create Celery app
celery_app = Celery(
    "health_dashboard",
    broker=settings.celery_broker,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.sync_tasks",
        "app.workers.analytics_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # Soft limit at 55 minutes
    worker_prefetch_multiplier=1,
    worker_concurrency=2,
    result_expires=86400,  # Results expire after 24 hours
)

# Scheduled tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    # Recalculate daily summaries every hour
    "recalculate-daily-summaries": {
        "task": "app.workers.analytics_tasks.recalculate_all_daily_summaries",
        "schedule": crontab(minute=0),  # Every hour at :00
    },
    # Generate insights daily at 6 AM
    "generate-daily-insights": {
        "task": "app.workers.analytics_tasks.generate_daily_insights",
        "schedule": crontab(hour=6, minute=0),
    },
    # Check alerts every 15 minutes
    "check-alerts": {
        "task": "app.workers.analytics_tasks.check_all_alerts",
        "schedule": crontab(minute="*/15"),
    },
    # Calculate correlations weekly on Sunday at 3 AM
    "calculate-correlations": {
        "task": "app.workers.analytics_tasks.calculate_all_correlations",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),
    },
    # Clean up old data monthly
    "cleanup-old-data": {
        "task": "app.workers.analytics_tasks.cleanup_old_data",
        "schedule": crontab(hour=2, minute=0, day_of_month=1),
    },
}
