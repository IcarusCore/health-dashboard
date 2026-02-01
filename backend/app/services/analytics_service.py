"""
Analytics Service
=================
Health data analytics, trend analysis, and correlations
"""

from datetime import datetime, timedelta, date
from typing import List, Optional, Tuple
from uuid import UUID
import numpy as np
from scipy import stats as scipy_stats
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.measurements import Measurement, MetricDefinition
from app.models.daily_summary import DailySummary
from app.schemas.analytics import TrendAnalysis, CorrelationResult, CorrelationMatrix, HealthReport
from app.schemas.metrics import MeasurementStats


class AnalyticsService:
    """Service for health data analytics."""
    
    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.user_id = user_id
    
    async def analyze_trend(self, metric_key: str, days: int = 30) -> TrendAnalysis:
        """Analyze trend for a specific metric."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get metric definition
        def_result = await self.db.execute(
            select(MetricDefinition).where(MetricDefinition.metric_key == metric_key)
        )
        metric_def = def_result.scalar_one_or_none()
        display_name = metric_def.display_name if metric_def else metric_key
        
        # Handle sleep_duration specially - it's in daily_summaries, not measurements
        if metric_key == 'sleep_duration':
            display_name = 'Sleep Duration'
            result = await self.db.execute(
                select(
                    DailySummary.date.label('date'),
                    DailySummary.sleep_duration_hours.label('avg_value')
                )
                .where(
                    DailySummary.user_id == self.user_id,
                    DailySummary.date >= start_date.date(),
                    DailySummary.date <= end_date.date(),
                    DailySummary.sleep_duration_hours.isnot(None),
                )
                .order_by(DailySummary.date)
            )
            rows = result.all()
        else:
            # Get daily aggregated values from measurements
            result = await self.db.execute(
                select(
                    func.date(Measurement.timestamp).label('date'),
                    func.avg(Measurement.value).label('avg_value')
                )
                .where(
                    Measurement.user_id == self.user_id,
                    Measurement.metric_key == metric_key,
                    Measurement.timestamp >= start_date,
                    Measurement.timestamp <= end_date,
                )
                .group_by(func.date(Measurement.timestamp))
                .order_by(func.date(Measurement.timestamp))
            )
            rows = result.all()
        
        if len(rows) < 2:
            return TrendAnalysis(
                metric_key=metric_key,
                display_name=display_name,
                period_days=days,
                direction='stable',
                change_percent=0,
                change_absolute=0,
                start_value=rows[0].avg_value if rows else 0,
                end_value=rows[-1].avg_value if rows else 0,
                confidence=0,
                data_points=len(rows),
                is_significant=False,
            )
        
        values = [float(r.avg_value) for r in rows]
        x = np.arange(len(values))
        
        # Linear regression
        slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(x, values)
        
        start_value = values[0]
        end_value = values[-1]
        change_absolute = end_value - start_value
        change_percent = (change_absolute / start_value * 100) if start_value != 0 else 0
        
        # Determine direction
        if abs(change_percent) < 2:
            direction = 'stable'
        elif slope > 0:
            direction = 'increasing'
        else:
            direction = 'decreasing'
        
        is_significant = p_value < 0.05 and abs(r_value) > 0.3
        
        return TrendAnalysis(
            metric_key=metric_key,
            display_name=display_name,
            period_days=days,
            direction=direction,
            change_percent=round(change_percent, 2),
            change_absolute=round(change_absolute, 2),
            start_value=round(start_value, 2),
            end_value=round(end_value, 2),
            confidence=round(abs(r_value), 3),
            data_points=len(values),
            is_significant=is_significant,
        )
    
    async def calculate_correlation(
        self,
        metric_a: str,
        metric_b: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        lag_days: int = 0,
    ) -> CorrelationResult:
        """Calculate correlation between two metrics."""
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=90)
        
        # Get metric definitions
        def_a_result = await self.db.execute(
            select(MetricDefinition).where(MetricDefinition.metric_key == metric_a)
        )
        def_a = def_a_result.scalar_one_or_none()
        
        def_b_result = await self.db.execute(
            select(MetricDefinition).where(MetricDefinition.metric_key == metric_b)
        )
        def_b = def_b_result.scalar_one_or_none()
        
        # Get daily values for both metrics
        result_a = await self.db.execute(
            select(
                func.date(Measurement.timestamp).label('date'),
                func.avg(Measurement.value).label('value')
            )
            .where(
                Measurement.user_id == self.user_id,
                Measurement.metric_key == metric_a,
                func.date(Measurement.timestamp) >= start_date,
                func.date(Measurement.timestamp) <= end_date,
            )
            .group_by(func.date(Measurement.timestamp))
        )
        values_a = {r.date: float(r.value) for r in result_a}
        
        result_b = await self.db.execute(
            select(
                func.date(Measurement.timestamp).label('date'),
                func.avg(Measurement.value).label('value')
            )
            .where(
                Measurement.user_id == self.user_id,
                Measurement.metric_key == metric_b,
                func.date(Measurement.timestamp) >= start_date,
                func.date(Measurement.timestamp) <= end_date,
            )
            .group_by(func.date(Measurement.timestamp))
        )
        values_b = {r.date: float(r.value) for r in result_b}
        
        # Align data (accounting for lag)
        paired_values = []
        for date_key, val_a in values_a.items():
            lagged_date = date_key + timedelta(days=lag_days)
            if lagged_date in values_b:
                paired_values.append((val_a, values_b[lagged_date]))
        
        if len(paired_values) < 10:
            return CorrelationResult(
                metric_a=metric_a,
                metric_a_display_name=def_a.display_name if def_a else metric_a,
                metric_b=metric_b,
                metric_b_display_name=def_b.display_name if def_b else metric_b,
                correlation_coefficient=0,
                p_value=1,
                sample_size=len(paired_values),
                lag_days=lag_days,
                is_significant=False,
                interpretation='insufficient_data',
            )
        
        x = np.array([p[0] for p in paired_values])
        y = np.array([p[1] for p in paired_values])
        
        correlation, p_value = scipy_stats.pearsonr(x, y)
        
        # Interpret correlation
        abs_corr = abs(correlation)
        if abs_corr < 0.1:
            interpretation = 'none'
        elif abs_corr < 0.3:
            interpretation = 'weak_positive' if correlation > 0 else 'weak_negative'
        elif abs_corr < 0.5:
            interpretation = 'moderate_positive' if correlation > 0 else 'moderate_negative'
        elif abs_corr < 0.7:
            interpretation = 'strong_positive' if correlation > 0 else 'strong_negative'
        else:
            interpretation = 'very_strong_positive' if correlation > 0 else 'very_strong_negative'
        
        return CorrelationResult(
            metric_a=metric_a,
            metric_a_display_name=def_a.display_name if def_a else metric_a,
            metric_b=metric_b,
            metric_b_display_name=def_b.display_name if def_b else metric_b,
            correlation_coefficient=round(correlation, 4),
            p_value=round(p_value, 6),
            sample_size=len(paired_values),
            lag_days=lag_days,
            is_significant=p_value < 0.05,
            interpretation=interpretation,
        )
    
    async def get_correlation_matrix(self, metrics: List[str], days: int = 90) -> CorrelationMatrix:
        """Calculate correlation matrix for multiple metrics."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get display names
        display_names = []
        for m in metrics:
            result = await self.db.execute(
                select(MetricDefinition).where(MetricDefinition.metric_key == m)
            )
            metric_def = result.scalar_one_or_none()
            display_names.append(metric_def.display_name if metric_def else m)
        
        # Calculate pairwise correlations
        n = len(metrics)
        correlations = [[None] * n for _ in range(n)]
        sample_sizes = [[0] * n for _ in range(n)]
        
        for i in range(n):
            correlations[i][i] = 1.0  # Self-correlation is 1
            sample_sizes[i][i] = days
            
            for j in range(i + 1, n):
                result = await self.calculate_correlation(
                    metrics[i], metrics[j], start_date, end_date
                )
                correlations[i][j] = result.correlation_coefficient
                correlations[j][i] = result.correlation_coefficient
                sample_sizes[i][j] = result.sample_size
                sample_sizes[j][i] = result.sample_size
        
        return CorrelationMatrix(
            metrics=metrics,
            metric_display_names=display_names,
            correlations=correlations,
            sample_sizes=sample_sizes,
        )
    
    async def generate_health_report(self, start_date: date, end_date: date) -> HealthReport:
        """Generate comprehensive health report for a period."""
        # Get daily summaries
        result = await self.db.execute(
            select(DailySummary)
            .where(
                DailySummary.user_id == self.user_id,
                DailySummary.date >= start_date,
                DailySummary.date <= end_date,
            )
            .order_by(DailySummary.date)
        )
        summaries = result.scalars().all()
        
        total_days = (end_date - start_date).days + 1
        days_with_data = len(summaries)
        
        # Calculate averages
        avg_steps = None
        avg_sleep = None
        avg_rhr = None
        avg_hrv = None
        
        if summaries:
            steps_vals = [s.steps for s in summaries if s.steps]
            avg_steps = sum(steps_vals) / len(steps_vals) if steps_vals else None
            
            sleep_vals = [float(s.sleep_duration_hours) for s in summaries if s.sleep_duration_hours]
            avg_sleep = sum(sleep_vals) / len(sleep_vals) if sleep_vals else None
            
            rhr_vals = [s.resting_heart_rate for s in summaries if s.resting_heart_rate]
            avg_rhr = sum(rhr_vals) / len(rhr_vals) if rhr_vals else None
            
            hrv_vals = [float(s.hrv_avg) for s in summaries if s.hrv_avg]
            avg_hrv = sum(hrv_vals) / len(hrv_vals) if hrv_vals else None
        
        # Calculate scores
        activity_scores = [s.activity_score for s in summaries if s.activity_score]
        sleep_scores = [s.sleep_score for s in summaries if s.sleep_score]
        recovery_scores = [s.recovery_score for s in summaries if s.recovery_score]
        
        overall_activity = int(sum(activity_scores) / len(activity_scores)) if activity_scores else None
        overall_sleep = int(sum(sleep_scores) / len(sleep_scores)) if sleep_scores else None
        overall_recovery = int(sum(recovery_scores) / len(recovery_scores)) if recovery_scores else None
        
        overall_health = None
        if any([overall_activity, overall_sleep, overall_recovery]):
            scores = [s for s in [overall_activity, overall_sleep, overall_recovery] if s]
            overall_health = int(sum(scores) / len(scores))
        
        # Find improving/declining metrics
        improving = []
        declining = []
        
        for metric in ['steps', 'sleep_duration', 'resting_heart_rate', 'heart_rate_variability']:
            try:
                trend = await self.analyze_trend(metric, days=(end_date - start_date).days)
                if trend.is_significant:
                    if trend.direction == 'increasing':
                        # For RHR, increasing is bad
                        if metric == 'resting_heart_rate':
                            declining.append(trend.display_name)
                        else:
                            improving.append(trend.display_name)
                    elif trend.direction == 'decreasing':
                        if metric == 'resting_heart_rate':
                            improving.append(trend.display_name)
                        else:
                            declining.append(trend.display_name)
            except:
                pass
        
        # Generate recommendations
        recommendations = []
        if avg_sleep and avg_sleep < 7:
            recommendations.append("Consider getting more sleep. Aim for 7-9 hours per night.")
        if avg_steps and avg_steps < 7000:
            recommendations.append("Try to increase daily steps. Even a short walk can help.")
        
        return HealthReport(
            period_start=start_date,
            period_end=end_date,
            overall_health_score=overall_health,
            activity_score=overall_activity,
            sleep_score=overall_sleep,
            recovery_score=overall_recovery,
            avg_steps=avg_steps,
            avg_sleep_hours=avg_sleep,
            avg_resting_hr=avg_rhr,
            avg_hrv=avg_hrv,
            weight_change_kg=None,
            achievements=[],
            improving_metrics=improving,
            declining_metrics=declining,
            recommendations=recommendations,
            data_completeness_percent=round(days_with_data / total_days * 100, 1),
            days_with_data=days_with_data,
            total_days=total_days,
        )
