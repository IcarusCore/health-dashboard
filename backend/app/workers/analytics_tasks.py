"""
Analytics Background Tasks
==========================
Celery tasks for analytics and insights
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional

from app.workers.celery_app import celery_app
from app.models.database import SyncSessionLocal
from app.models.users import User
from app.models.daily_summary import DailySummary
from app.models.insights import HealthInsight
from app.models.alerts import Alert

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def recalculate_daily_summary(self, user_id: str, target_date: str):
    """Recalculate daily summary for a specific user and date."""
    from app.services.summary_service import SummaryService
    import asyncio
    from app.models.database import AsyncSessionLocal
    
    async def _run():
        async with AsyncSessionLocal() as db:
            service = SummaryService(db, user_id)
            await service.calculate_daily_summary(
                datetime.strptime(target_date, "%Y-%m-%d").date()
            )
    
    try:
        asyncio.run(_run())
        logger.info(f"Recalculated summary for user {user_id} on {target_date}")
    except Exception as e:
        logger.error(f"Failed to recalculate summary: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task
def recalculate_all_daily_summaries():
    """Recalculate today's summary for all active users."""
    db = SyncSessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        today = date.today().strftime("%Y-%m-%d")
        
        for user in users:
            recalculate_daily_summary.delay(str(user.id), today)
        
        logger.info(f"Queued summary recalculation for {len(users)} users")
    finally:
        db.close()


@celery_app.task
def generate_daily_insights():
    """Generate health insights for all users."""
    db = SyncSessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        
        for user in users:
            generate_user_insights.delay(str(user.id))
        
        logger.info(f"Queued insight generation for {len(users)} users")
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2)
def generate_user_insights(self, user_id: str):
    """Generate insights for a specific user."""
    from sqlalchemy import select, func
    
    db = SyncSessionLocal()
    try:
        # Get recent summaries
        summaries = db.query(DailySummary).filter(
            DailySummary.user_id == user_id,
            DailySummary.date >= date.today() - timedelta(days=30)
        ).order_by(DailySummary.date.desc()).all()
        
        if not summaries:
            return
        
        insights_to_create = []
        
        # Check for step streaks
        steps_streak = 0
        for s in summaries:
            if s.steps and s.steps >= 10000:
                steps_streak += 1
            else:
                break
        
        if steps_streak >= 7:
            insights_to_create.append(HealthInsight(
                user_id=user_id,
                insight_type='achievement',
                category='activity',
                title=f'{steps_streak}-day step streak!',
                description=f"You've hit 10,000+ steps for {steps_streak} days in a row. Keep it up!",
                severity='positive',
                metric_keys=['steps'],
                data={'streak_days': steps_streak},
                priority=20,
            ))
        
        # Check for sleep consistency
        sleep_hours = [float(s.sleep_duration_hours) for s in summaries if s.sleep_duration_hours]
        if len(sleep_hours) >= 7:
            avg_sleep = sum(sleep_hours) / len(sleep_hours)
            recent_avg = sum(sleep_hours[:7]) / 7
            
            if recent_avg < 6:
                insights_to_create.append(HealthInsight(
                    user_id=user_id,
                    insight_type='recommendation',
                    category='sleep',
                    title='Sleep deficit detected',
                    description=f"Your average sleep this week is {recent_avg:.1f} hours. Consider prioritizing sleep for better recovery.",
                    severity='warning',
                    metric_keys=['sleep_duration'],
                    data={'avg_hours': recent_avg},
                    priority=30,
                ))
        
        # Add insights to database
        for insight in insights_to_create:
            # Check if similar insight already exists
            existing = db.query(HealthInsight).filter(
                HealthInsight.user_id == user_id,
                HealthInsight.title == insight.title,
                HealthInsight.is_dismissed == False,
                HealthInsight.created_at >= datetime.utcnow() - timedelta(days=7)
            ).first()
            
            if not existing:
                db.add(insight)
        
        db.commit()
        logger.info(f"Generated {len(insights_to_create)} insights for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to generate insights for user {user_id}: {e}")
        raise self.retry(exc=e, countdown=120)
    finally:
        db.close()


@celery_app.task
def check_all_alerts():
    """Check alerts for all users."""
    db = SyncSessionLocal()
    try:
        # Get all active alerts
        alerts = db.query(Alert).filter(
            Alert.is_active == True,
            Alert.is_muted == False,
        ).all()
        
        for alert in alerts:
            check_alert.delay(str(alert.id))
        
        logger.info(f"Queued {len(alerts)} alert checks")
    finally:
        db.close()


@celery_app.task
def check_alert(alert_id: str):
    """Check a specific alert and trigger if conditions met."""
    from app.models.measurements import Measurement
    from app.models.alerts import AlertNotification
    
    db = SyncSessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert or not alert.can_trigger():
            return
        
        # Get latest value for the metric
        latest = db.query(Measurement).filter(
            Measurement.user_id == alert.user_id,
            Measurement.metric_key == alert.metric_key,
        ).order_by(Measurement.timestamp.desc()).first()
        
        if not latest:
            return
        
        value = float(latest.value)
        
        # Check condition
        if alert.check_condition(value):
            # Update trigger count
            alert.consecutive_trigger_count += 1
            
            if alert.consecutive_trigger_count >= alert.consecutive_triggers:
                # Trigger alert
                alert.last_triggered_at = datetime.utcnow()
                alert.last_value = value
                alert.trigger_count += 1
                alert.consecutive_trigger_count = 0
                
                # Create notification
                notification = AlertNotification(
                    alert_id=alert.id,
                    user_id=alert.user_id,
                    channel='app',
                    title=alert.name,
                    message=f"{alert.name}: {alert.metric_key} is {value} ({alert.condition} {alert.threshold_value})",
                    triggered_value=value,
                    threshold_value=float(alert.threshold_value) if alert.threshold_value else None,
                    status='sent',
                    sent_at=datetime.utcnow(),
                )
                db.add(notification)
                
                logger.info(f"Alert {alert.name} triggered for user {alert.user_id}")
        else:
            alert.consecutive_trigger_count = 0
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Failed to check alert {alert_id}: {e}")
    finally:
        db.close()


@celery_app.task
def calculate_all_correlations():
    """Calculate correlations for all users."""
    db = SyncSessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        
        for user in users:
            calculate_user_correlations.delay(str(user.id))
        
        logger.info(f"Queued correlation calculation for {len(users)} users")
    finally:
        db.close()


@celery_app.task
def calculate_user_correlations(user_id: str):
    """Calculate metric correlations for a user."""
    # This would use the AnalyticsService to calculate and store correlations
    logger.info(f"Calculating correlations for user {user_id}")
    pass


@celery_app.task
def cleanup_old_data():
    """Clean up old temporary data and expired records."""
    import os
    from app.config import settings
    
    db = SyncSessionLocal()
    try:
        # Clean up old dismissed insights (older than 90 days)
        cutoff = datetime.utcnow() - timedelta(days=90)
        deleted = db.query(HealthInsight).filter(
            HealthInsight.is_dismissed == True,
            HealthInsight.created_at < cutoff,
        ).delete()
        
        # Clean up old import files
        upload_dir = settings.UPLOAD_DIR
        if os.path.exists(upload_dir):
            for user_dir in os.listdir(upload_dir):
                user_path = os.path.join(upload_dir, user_dir)
                if os.path.isdir(user_path):
                    for filename in os.listdir(user_path):
                        filepath = os.path.join(user_path, filename)
                        if os.path.getmtime(filepath) < (datetime.utcnow() - timedelta(days=7)).timestamp():
                            os.remove(filepath)
        
        db.commit()
        logger.info(f"Cleanup complete. Deleted {deleted} old insights.")
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
    finally:
        db.close()
