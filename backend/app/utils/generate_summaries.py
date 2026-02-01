"""
Generate daily summaries from measurements data.
"""
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.measurements import Measurement
from app.models.dashboard import DailySummary
from app.models.sleep import SleepSession

logger = logging.getLogger(__name__)

async def generate_daily_summaries(db: AsyncSession, user_id: str, start_date: date = None, end_date: date = None):
    """Generate daily summaries from measurements for a user."""
    
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=365)
    
    current_date = start_date
    summaries_created = 0
    
    while current_date <= end_date:
        day_start = datetime.combine(current_date, datetime.min.time())
        day_end = datetime.combine(current_date, datetime.max.time())
        
        # Check if summary already exists
        existing = await db.execute(
            select(DailySummary).where(
                DailySummary.user_id == user_id,
                DailySummary.date == current_date
            )
        )
        if existing.scalar_one_or_none():
            current_date += timedelta(days=1)
            continue
        
        # Get steps (sum for the day)
        steps_result = await db.execute(
            select(func.sum(Measurement.value)).where(
                Measurement.user_id == user_id,
                Measurement.metric_key == 'steps',
                Measurement.timestamp >= day_start,
                Measurement.timestamp <= day_end
            )
        )
        steps = steps_result.scalar() or 0
        
        # Get active energy (sum)
        active_result = await db.execute(
            select(func.sum(Measurement.value)).where(
                Measurement.user_id == user_id,
                Measurement.metric_key == 'active_energy',
                Measurement.timestamp >= day_start,
                Measurement.timestamp <= day_end
            )
        )
        active_energy = active_result.scalar() or 0
        
        # Get exercise minutes (sum)
        exercise_result = await db.execute(
            select(func.sum(Measurement.value)).where(
                Measurement.user_id == user_id,
                Measurement.metric_key == 'exercise_minutes',
                Measurement.timestamp >= day_start,
                Measurement.timestamp <= day_end
            )
        )
        exercise_mins = exercise_result.scalar() or 0
        
        # Get resting heart rate (avg)
        rhr_result = await db.execute(
            select(func.avg(Measurement.value)).where(
                Measurement.user_id == user_id,
                Measurement.metric_key == 'resting_heart_rate',
                Measurement.timestamp >= day_start,
                Measurement.timestamp <= day_end
            )
        )
        resting_hr = rhr_result.scalar()
        
        # Get HRV (avg)
        hrv_result = await db.execute(
            select(func.avg(Measurement.value)).where(
                Measurement.user_id == user_id,
                Measurement.metric_key == 'heart_rate_variability',
                Measurement.timestamp >= day_start,
                Measurement.timestamp <= day_end
            )
        )
        hrv = hrv_result.scalar()
        
        # Get weight (latest of the day)
        weight_result = await db.execute(
            select(Measurement.value).where(
                Measurement.user_id == user_id,
                Measurement.metric_key == 'weight',
                Measurement.timestamp >= day_start,
                Measurement.timestamp <= day_end
            ).order_by(Measurement.timestamp.desc()).limit(1)
        )
        weight = weight_result.scalar()
        
        # Get sleep duration from sleep_sessions
        sleep_result = await db.execute(
            select(func.sum(SleepSession.duration_minutes)).where(
                SleepSession.user_id == user_id,
                SleepSession.start_time >= day_start - timedelta(hours=12),
                SleepSession.end_time <= day_end + timedelta(hours=12)
            )
        )
        sleep_mins = sleep_result.scalar() or 0
        sleep_hours = float(sleep_mins) / 60.0 if sleep_mins else None
        
        # Only create summary if we have some data
        if steps or active_energy or exercise_mins or resting_hr or sleep_hours:
            summary = DailySummary(
                user_id=user_id,
                date=current_date,
                steps=int(steps) if steps else None,
                active_calories=int(active_energy) if active_energy else None,
                exercise_minutes=int(exercise_mins) if exercise_mins else None,
                resting_heart_rate=float(resting_hr) if resting_hr else None,
                hrv_average=float(hrv) if hrv else None,
                sleep_hours=sleep_hours,
                weight=float(weight) if weight else None,
            )
            db.add(summary)
            summaries_created += 1
        
        current_date += timedelta(days=1)
    
    await db.commit()
    logger.info(f"Generated {summaries_created} daily summaries for user {user_id}")
    return summaries_created
