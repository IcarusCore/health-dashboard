"""
Insights Service
================
Generate health insights from daily summaries and measurements
"""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.insights import HealthInsight
from app.models.daily_summary import DailySummary


class InsightsService:
    """Service for generating health insights."""
    
    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.user_id = user_id
    
    async def generate_insights(self) -> List[HealthInsight]:
        """Generate insights from recent daily summaries."""
        insights = []
        
        # Get last 30 days of summaries
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        result = await self.db.execute(
            select(DailySummary)
            .where(
                DailySummary.user_id == self.user_id,
                DailySummary.date >= start_date,
                DailySummary.date <= end_date,
            )
            .order_by(desc(DailySummary.date))
        )
        summaries = result.scalars().all()
        
        if not summaries:
            return insights
        
        # Clear old insights first
        await self.db.execute(
            select(HealthInsight).where(HealthInsight.user_id == self.user_id)
        )
        from sqlalchemy import delete
        await self.db.execute(
            delete(HealthInsight).where(HealthInsight.user_id == self.user_id)
        )
        
        # Generate various insight types
        insights.extend(await self._generate_trend_insights(summaries))
        insights.extend(await self._generate_achievement_insights(summaries))
        insights.extend(await self._generate_recommendation_insights(summaries))
        
        # Save all insights
        for insight in insights:
            self.db.add(insight)
        
        return insights
    
    async def _generate_trend_insights(self, summaries: List[DailySummary]) -> List[HealthInsight]:
        """Generate trend-based insights."""
        insights = []
        
        if len(summaries) < 7:
            return insights
        
        # Steps trend
        recent_steps = [s.steps for s in summaries[:7] if s.steps]
        older_steps = [s.steps for s in summaries[7:14] if s.steps]
        
        if recent_steps and older_steps:
            recent_avg = sum(recent_steps) / len(recent_steps)
            older_avg = sum(older_steps) / len(older_steps)
            
            if older_avg > 0:
                change_pct = ((recent_avg - older_avg) / older_avg) * 100
                
                if change_pct > 10:
                    insights.append(HealthInsight(
                        user_id=self.user_id,
                        insight_type='trend',
                        category='activity',
                        title='Steps are improving! 🚶',
                        description=f'Your average daily steps increased by {change_pct:.1f}% compared to the previous week. Keep up the great work!',
                        severity='positive',
                        metric_keys=['steps'],
                        data={'direction': 'increasing', 'change_percent': change_pct, 'recent_avg': recent_avg},
                        priority=30,
                    ))
                elif change_pct < -10:
                    insights.append(HealthInsight(
                        user_id=self.user_id,
                        insight_type='trend',
                        category='activity',
                        title='Steps have decreased',
                        description=f'Your average daily steps decreased by {abs(change_pct):.1f}% compared to the previous week. Try to get more movement in!',
                        severity='warning',
                        metric_keys=['steps'],
                        data={'direction': 'decreasing', 'change_percent': change_pct, 'recent_avg': recent_avg},
                        priority=40,
                    ))
        
        # Sleep trend
        recent_sleep = [float(s.sleep_score) for s in summaries[:7] if s.sleep_score]
        older_sleep = [float(s.sleep_score) for s in summaries[7:14] if s.sleep_score]
        
        if recent_sleep and older_sleep:
            recent_avg = sum(recent_sleep) / len(recent_sleep)
            older_avg = sum(older_sleep) / len(older_sleep)
            
            if older_avg > 0:
                change_pct = ((recent_avg - older_avg) / older_avg) * 100
                
                if change_pct > 5:
                    insights.append(HealthInsight(
                        user_id=self.user_id,
                        insight_type='trend',
                        category='sleep',
                        title='Sleep quality improving! 😴',
                        description=f'Your sleep score improved by {change_pct:.1f}% this week. Great sleep habits!',
                        severity='positive',
                        metric_keys=['sleep_score'],
                        data={'direction': 'increasing', 'change_percent': change_pct, 'recent_avg': recent_avg},
                        priority=25,
                    ))
                elif change_pct < -5:
                    insights.append(HealthInsight(
                        user_id=self.user_id,
                        insight_type='trend',
                        category='sleep',
                        title='Sleep quality declining',
                        description=f'Your sleep score decreased by {abs(change_pct):.1f}% this week. Consider reviewing your sleep habits.',
                        severity='warning',
                        metric_keys=['sleep_score'],
                        data={'direction': 'decreasing', 'change_percent': change_pct, 'recent_avg': recent_avg},
                        priority=35,
                    ))
        
        # HRV trend (higher is generally better)
        recent_hrv = [float(s.hrv_avg) for s in summaries[:7] if s.hrv_avg]
        older_hrv = [float(s.hrv_avg) for s in summaries[7:14] if s.hrv_avg]
        
        if recent_hrv and older_hrv:
            recent_avg = sum(recent_hrv) / len(recent_hrv)
            older_avg = sum(older_hrv) / len(older_hrv)
            
            if older_avg > 0:
                change_pct = ((recent_avg - older_avg) / older_avg) * 100
                
                if change_pct > 10:
                    insights.append(HealthInsight(
                        user_id=self.user_id,
                        insight_type='trend',
                        category='vitals',
                        title='HRV is up! 💪',
                        description=f'Your heart rate variability increased by {change_pct:.1f}%, indicating better recovery and stress resilience.',
                        severity='positive',
                        metric_keys=['heart_rate_variability'],
                        data={'direction': 'increasing', 'change_percent': change_pct, 'recent_avg': recent_avg},
                        priority=20,
                    ))
        
        return insights
    
    async def _generate_achievement_insights(self, summaries: List[DailySummary]) -> List[HealthInsight]:
        """Generate achievement insights."""
        insights = []
        
        # Check for step goal streaks
        streak = 0
        for s in summaries:
            if s.steps_goal_percent and float(s.steps_goal_percent) >= 100:
                streak += 1
            else:
                break
        
        if streak >= 3:
            insights.append(HealthInsight(
                user_id=self.user_id,
                insight_type='achievement',
                category='activity',
                title=f'{streak}-day step goal streak! 🔥',
                description=f"You've hit your step goal for {streak} days in a row. Fantastic consistency!",
                severity='positive',
                metric_keys=['steps'],
                data={'streak_days': streak, 'metric': 'steps'},
                priority=10,
            ))
        
        # Check for sleep consistency
        sleep_scores = [float(s.sleep_score) for s in summaries[:7] if s.sleep_score]
        if sleep_scores and len(sleep_scores) >= 5:
            avg_score = sum(sleep_scores) / len(sleep_scores)
            if avg_score >= 75:
                insights.append(HealthInsight(
                    user_id=self.user_id,
                    insight_type='achievement',
                    category='sleep',
                    title='Excellent sleep week! 🌟',
                    description=f'Your average sleep score this week is {avg_score:.0f}. Outstanding sleep quality!',
                    severity='positive',
                    metric_keys=['sleep_score'],
                    data={'avg_score': avg_score, 'days': len(sleep_scores)},
                    priority=15,
                ))
        
        return insights
    
    async def _generate_recommendation_insights(self, summaries: List[DailySummary]) -> List[HealthInsight]:
        """Generate recommendation insights."""
        insights = []
        
        if not summaries:
            return insights
        
        # Low activity recommendation
        recent_steps = [s.steps for s in summaries[:7] if s.steps]
        if recent_steps:
            avg_steps = sum(recent_steps) / len(recent_steps)
            if avg_steps < 5000:
                insights.append(HealthInsight(
                    user_id=self.user_id,
                    insight_type='recommendation',
                    category='activity',
                    title='Boost your daily movement',
                    description=f'Your average is {avg_steps:.0f} steps/day. Try adding a 15-minute walk to increase activity.',
                    severity='info',
                    metric_keys=['steps'],
                    data={'current_avg': avg_steps, 'target': 7500},
                    priority=50,
                ))
        
        # Sleep duration recommendation
        recent_sleep_hours = [float(s.sleep_duration_hours) for s in summaries[:7] if s.sleep_duration_hours]
        if recent_sleep_hours:
            avg_sleep = sum(recent_sleep_hours) / len(recent_sleep_hours)
            if avg_sleep < 7:
                insights.append(HealthInsight(
                    user_id=self.user_id,
                    insight_type='recommendation',
                    category='sleep',
                    title='Consider more sleep time',
                    description=f'You\'re averaging {avg_sleep:.1f} hours of sleep. Aim for 7-9 hours for optimal recovery.',
                    severity='info',
                    metric_keys=['sleep_duration'],
                    data={'current_avg': avg_sleep, 'target_min': 7, 'target_max': 9},
                    priority=45,
                ))
        
        # Resting heart rate insight
        recent_rhr = [s.resting_heart_rate for s in summaries[:7] if s.resting_heart_rate]
        if recent_rhr:
            avg_rhr = sum(recent_rhr) / len(recent_rhr)
            if avg_rhr > 75:
                insights.append(HealthInsight(
                    user_id=self.user_id,
                    insight_type='recommendation',
                    category='vitals',
                    title='Monitor your resting heart rate',
                    description=f'Your average resting heart rate is {avg_rhr:.0f} bpm. Regular cardio exercise can help lower this over time.',
                    severity='info',
                    metric_keys=['resting_heart_rate'],
                    data={'current_avg': avg_rhr},
                    priority=55,
                ))
        
        return insights
