"""
Summary Service
===============
Daily summary calculation and aggregation
"""

from datetime import datetime, date, timedelta
from typing import Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User, UserSettings
from app.models.measurements import Measurement
from app.models.workouts import Workout
from app.models.sleep import SleepSession
from app.models.daily_summary import DailySummary


class SummaryService:
    """Service for calculating daily health summaries."""
    
    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.user_id = user_id
    
    async def calculate_daily_summary(self, target_date: date) -> DailySummary:
        """Calculate or update daily summary for a specific date."""
        
        result = await self.db.execute(
            select(DailySummary).where(
                DailySummary.user_id == self.user_id,
                DailySummary.date == target_date,
            )
        )
        summary = result.scalar_one_or_none()
        
        if not summary:
            summary = DailySummary(user_id=self.user_id, date=target_date)
            self.db.add(summary)
        
        settings_result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == self.user_id)
        )
        user_settings = settings_result.scalar_one_or_none()
        
        day_start = datetime.combine(target_date, datetime.min.time())
        day_end = datetime.combine(target_date, datetime.max.time())
        
        await self._aggregate_activity_metrics(summary, day_start, day_end)
        await self._aggregate_vitals(summary, day_start, day_end)
        await self._aggregate_body_metrics(summary, day_start, day_end)
        await self._aggregate_nutrition(summary, day_start, day_end)
        await self._aggregate_workouts(summary, target_date)
        await self._aggregate_sleep(summary, target_date)
        
        if user_settings:
            if summary.steps and user_settings.daily_steps_goal:
                summary.steps_goal_percent = Decimal(str(
                    round(summary.steps / user_settings.daily_steps_goal * 100, 2)
                ))
            if summary.active_calories and user_settings.daily_calories_goal:
                summary.calories_goal_percent = Decimal(str(
                    round(summary.active_calories / user_settings.daily_calories_goal * 100, 2)
                ))
            if summary.exercise_minutes and user_settings.daily_active_minutes_goal:
                summary.exercise_goal_percent = Decimal(str(
                    round(summary.exercise_minutes / user_settings.daily_active_minutes_goal * 100, 2)
                ))
            if summary.sleep_duration_hours and user_settings.sleep_hours_goal:
                summary.sleep_goal_percent = Decimal(str(
                    round(float(summary.sleep_duration_hours) / float(user_settings.sleep_hours_goal) * 100, 2)
                ))
        
        summary.activity_score = summary.calculate_activity_score()
        summary.vitals_score = summary.calculate_vitals_score()
        summary.recovery_score = summary.calculate_recovery_score()
        summary.overall_score = summary.calculate_overall_score()
        
        await self.db.commit()
        await self.db.refresh(summary)
        
        return summary
    
    async def _aggregate_activity_metrics(self, summary: DailySummary, start: datetime, end: datetime):
        """Aggregate activity metrics for the day."""
        steps_result = await self.db.execute(
            select(func.sum(Measurement.value)).where(
                Measurement.user_id == self.user_id,
                Measurement.metric_key == 'steps',
                Measurement.timestamp >= start,
                Measurement.timestamp <= end,
            )
        )
        steps = steps_result.scalar()
        summary.steps = int(steps) if steps else None
        
        distance_result = await self.db.execute(
            select(func.sum(Measurement.value)).where(
                Measurement.user_id == self.user_id,
                Measurement.metric_key.in_(['distance_walking', 'distance_running']),
                Measurement.timestamp >= start,
                Measurement.timestamp <= end,
            )
        )
        distance = distance_result.scalar()
        summary.distance_km = Decimal(str(round(float(distance), 2))) if distance else None
        
        active_cal_result = await self.db.execute(
            select(func.sum(Measurement.value)).where(
                Measurement.user_id == self.user_id,
                Measurement.metric_key == 'active_energy',
                Measurement.timestamp >= start,
                Measurement.timestamp <= end,
            )
        )
        active_cal = active_cal_result.scalar()
        summary.active_calories = int(active_cal) if active_cal else None
        
        exercise_result = await self.db.execute(
            select(func.sum(Measurement.value)).where(
                Measurement.user_id == self.user_id,
                Measurement.metric_key == 'exercise_minutes',
                Measurement.timestamp >= start,
                Measurement.timestamp <= end,
            )
        )
        exercise = exercise_result.scalar()
        summary.exercise_minutes = int(exercise) if exercise else None
        
        flights_result = await self.db.execute(
            select(func.sum(Measurement.value)).where(
                Measurement.user_id == self.user_id,
                Measurement.metric_key == 'flights_climbed',
                Measurement.timestamp >= start,
                Measurement.timestamp <= end,
            )
        )
        flights = flights_result.scalar()
        summary.flights_climbed = int(flights) if flights else None
    
    async def _aggregate_vitals(self, summary: DailySummary, start: datetime, end: datetime):
        """Aggregate vital metrics for the day."""
        rhr_result = await self.db.execute(
            select(func.avg(Measurement.value)).where(
                Measurement.user_id == self.user_id,
                Measurement.metric_key == 'resting_heart_rate',
                Measurement.timestamp >= start,
                Measurement.timestamp <= end,
            )
        )
        rhr = rhr_result.scalar()
        summary.resting_heart_rate = int(rhr) if rhr else None
        
        hr_result = await self.db.execute(
            select(
                func.avg(Measurement.value).label('avg'),
                func.max(Measurement.value).label('max'),
                func.min(Measurement.value).label('min'),
            ).where(
                Measurement.user_id == self.user_id,
                Measurement.metric_key == 'heart_rate',
                Measurement.timestamp >= start,
                Measurement.timestamp <= end,
            )
        )
        hr = hr_result.one()
        summary.avg_heart_rate = int(hr.avg) if hr.avg else None
        summary.max_heart_rate = int(hr.max) if hr.max else None
        summary.min_heart_rate = int(hr.min) if hr.min else None
        
        hrv_result = await self.db.execute(
            select(
                func.avg(Measurement.value).label('avg'),
                func.min(Measurement.value).label('min'),
                func.max(Measurement.value).label('max'),
            ).where(
                Measurement.user_id == self.user_id,
                Measurement.metric_key == 'heart_rate_variability',
                Measurement.timestamp >= start,
                Measurement.timestamp <= end,
            )
        )
        hrv = hrv_result.one()
        summary.hrv_avg = Decimal(str(round(float(hrv.avg), 2))) if hrv.avg else None
        summary.hrv_min = Decimal(str(round(float(hrv.min), 2))) if hrv.min else None
        summary.hrv_max = Decimal(str(round(float(hrv.max), 2))) if hrv.max else None
        
        spo2_result = await self.db.execute(
            select(
                func.avg(Measurement.value).label('avg'),
                func.min(Measurement.value).label('min'),
            ).where(
                Measurement.user_id == self.user_id,
                Measurement.metric_key == 'blood_oxygen',
                Measurement.timestamp >= start,
                Measurement.timestamp <= end,
            )
        )
        spo2 = spo2_result.one()
        summary.blood_oxygen_avg = Decimal(str(round(float(spo2.avg), 1))) if spo2.avg else None
        summary.blood_oxygen_min = Decimal(str(round(float(spo2.min), 1))) if spo2.min else None
        
        resp_result = await self.db.execute(
            select(func.avg(Measurement.value)).where(
                Measurement.user_id == self.user_id,
                Measurement.metric_key == 'respiratory_rate',
                Measurement.timestamp >= start,
                Measurement.timestamp <= end,
            )
        )
        resp = resp_result.scalar()
        summary.respiratory_rate_avg = Decimal(str(round(float(resp), 1))) if resp else None
    
    async def _aggregate_body_metrics(self, summary: DailySummary, start: datetime, end: datetime):
        """Aggregate body composition metrics."""
        weight_result = await self.db.execute(
            select(Measurement.value)
            .where(
                Measurement.user_id == self.user_id,
                Measurement.metric_key == 'weight',
                Measurement.timestamp >= start,
                Measurement.timestamp <= end,
            )
            .order_by(Measurement.timestamp.desc())
            .limit(1)
        )
        weight = weight_result.scalar()
        summary.weight_kg = Decimal(str(round(float(weight), 2))) if weight else None
        
        bf_result = await self.db.execute(
            select(Measurement.value)
            .where(
                Measurement.user_id == self.user_id,
                Measurement.metric_key == 'body_fat',
                Measurement.timestamp >= start,
                Measurement.timestamp <= end,
            )
            .order_by(Measurement.timestamp.desc())
            .limit(1)
        )
        bf = bf_result.scalar()
        summary.body_fat_percent = Decimal(str(round(float(bf), 1))) if bf else None
    
    async def _aggregate_nutrition(self, summary: DailySummary, start: datetime, end: datetime):
        """Aggregate nutrition metrics."""
        water_result = await self.db.execute(
            select(func.sum(Measurement.value)).where(
                Measurement.user_id == self.user_id,
                Measurement.metric_key == 'water_intake',
                Measurement.timestamp >= start,
                Measurement.timestamp <= end,
            )
        )
        water = water_result.scalar()
        summary.water_liters = Decimal(str(round(float(water), 2))) if water else None
        
        caffeine_result = await self.db.execute(
            select(func.sum(Measurement.value)).where(
                Measurement.user_id == self.user_id,
                Measurement.metric_key == 'caffeine',
                Measurement.timestamp >= start,
                Measurement.timestamp <= end,
            )
        )
        caffeine = caffeine_result.scalar()
        summary.caffeine_mg = int(caffeine) if caffeine else None
        
        cal_result = await self.db.execute(
            select(func.sum(Measurement.value)).where(
                Measurement.user_id == self.user_id,
                Measurement.metric_key == 'dietary_calories',
                Measurement.timestamp >= start,
                Measurement.timestamp <= end,
            )
        )
        cal = cal_result.scalar()
        summary.dietary_calories = int(cal) if cal else None
    
    async def _aggregate_workouts(self, summary: DailySummary, target_date: date):
        """Aggregate workout data for the day."""
        result = await self.db.execute(
            select(
                func.count(Workout.id).label('count'),
                func.sum(Workout.duration_seconds).label('duration'),
                func.sum(Workout.total_calories).label('calories'),
            ).where(
                Workout.user_id == self.user_id,
                func.date(Workout.start_time) == target_date,
            )
        )
        row = result.one()
        
        summary.workout_count = row.count if row.count else None
        summary.workout_minutes = int(row.duration / 60) if row.duration else None
        summary.workout_calories = int(row.calories) if row.calories else None
    
    async def _aggregate_sleep(self, summary: DailySummary, target_date: date):
        """Aggregate sleep data (from the night before)."""
        # Sleep for a date is the sleep session that ended on that date
        # or started the night before
        sleep_start = datetime.combine(target_date - timedelta(days=1), datetime.min.time().replace(hour=18))
        sleep_end = datetime.combine(target_date, datetime.max.time().replace(hour=12))
        
        result = await self.db.execute(
            select(SleepSession)
            .where(
                SleepSession.user_id == self.user_id,
                SleepSession.start_time >= sleep_start,
                SleepSession.end_time <= sleep_end,
            )
            .order_by(SleepSession.duration_seconds.desc())
            .limit(1)
        )
        sleep = result.scalar_one_or_none()
        
        if sleep:
            summary.sleep_duration_hours = Decimal(str(round(sleep.duration_hours, 2)))
            summary.sleep_efficiency = sleep.sleep_efficiency
            summary.sleep_score = sleep.sleep_score
            
            if sleep.time_deep_seconds:
                summary.sleep_deep_hours = Decimal(str(round(sleep.time_deep_seconds / 3600, 2)))
            if sleep.time_rem_seconds:
                summary.sleep_rem_hours = Decimal(str(round(sleep.time_rem_seconds / 3600, 2)))
            if sleep.time_light_seconds:
                summary.sleep_light_hours = Decimal(str(round(sleep.time_light_seconds / 3600, 2)))
            if sleep.time_awake_seconds:
                summary.sleep_awake_hours = Decimal(str(round(sleep.time_awake_seconds / 3600, 2)))
