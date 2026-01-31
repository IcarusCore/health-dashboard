"""
Health Insights Models
======================
SQLAlchemy models for AI-generated health insights and recommendations
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, Text, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.models.database import Base


class HealthInsight(Base):
    """
    Generated health insights including trends, anomalies, 
    correlations, achievements, and recommendations.
    """
    
    __tablename__ = "health_insights"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Insight classification
    insight_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Types: 'trend', 'anomaly', 'correlation', 'achievement', 'recommendation', 'alert'
    
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    # Categories: 'vitals', 'activity', 'sleep', 'body', 'nutrition', 'general'
    
    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Severity/importance
    severity: Mapped[str] = mapped_column(String(20), default="info")
    # Severities: 'info', 'positive', 'warning', 'alert'
    
    # Related metrics
    metric_keys: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(100)))
    
    # Detailed data for rendering charts/details
    data: Mapped[dict] = mapped_column(JSONB, default=dict)
    # Example data structures:
    # For trends: {"direction": "increasing", "change_percent": 5.2, "period_days": 30, "values": [...]}
    # For anomalies: {"value": 120, "expected_range": [60, 90], "z_score": 3.2}
    # For correlations: {"metric_a": "sleep", "metric_b": "hrv", "correlation": 0.72}
    # For achievements: {"type": "streak", "metric": "steps", "value": 30, "previous_best": 25}
    
    # State
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Validity period
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Priority for sorting (lower = higher priority)
    priority: Mapped[int] = mapped_column(Integer, default=50)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="insights")
    
    @property
    def is_active(self) -> bool:
        """Check if insight is currently active."""
        now = datetime.utcnow()
        if self.valid_until and now > self.valid_until:
            return False
        return not self.is_dismissed
    
    @property
    def icon(self) -> str:
        """Get appropriate icon based on insight type and severity."""
        icons = {
            'trend': 'trending-up',
            'anomaly': 'alert-triangle',
            'correlation': 'git-branch',
            'achievement': 'award',
            'recommendation': 'lightbulb',
            'alert': 'bell',
        }
        return icons.get(self.insight_type, 'info')
    
    @property
    def color(self) -> str:
        """Get color based on severity."""
        colors = {
            'info': 'blue',
            'positive': 'green',
            'warning': 'orange',
            'alert': 'red',
        }
        return colors.get(self.severity, 'gray')
    
    def __repr__(self):
        return f"<HealthInsight [{self.insight_type}] {self.title}>"


# Insight templates for common patterns
INSIGHT_TEMPLATES = {
    # Trend insights
    'trend_improving': {
        'type': 'trend',
        'severity': 'positive',
        'title_template': '{metric_name} is improving',
        'description_template': 'Your {metric_name} has improved by {change_percent:.1f}% over the past {period_days} days.',
    },
    'trend_declining': {
        'type': 'trend',
        'severity': 'warning',
        'title_template': '{metric_name} is declining',
        'description_template': 'Your {metric_name} has declined by {change_percent:.1f}% over the past {period_days} days. Consider reviewing your habits.',
    },
    
    # Anomaly insights
    'anomaly_high': {
        'type': 'anomaly',
        'severity': 'warning',
        'title_template': 'Unusually high {metric_name}',
        'description_template': 'Your {metric_name} of {value} is significantly higher than your typical range of {expected_low}-{expected_high}.',
    },
    'anomaly_low': {
        'type': 'anomaly',
        'severity': 'warning',
        'title_template': 'Unusually low {metric_name}',
        'description_template': 'Your {metric_name} of {value} is significantly lower than your typical range of {expected_low}-{expected_high}.',
    },
    
    # Achievement insights
    'achievement_streak': {
        'type': 'achievement',
        'severity': 'positive',
        'title_template': '{streak_days}-day {metric_name} streak!',
        'description_template': "You've met your {metric_name} goal for {streak_days} days in a row. Keep it up!",
    },
    'achievement_personal_best': {
        'type': 'achievement',
        'severity': 'positive',
        'title_template': 'New personal best: {metric_name}',
        'description_template': 'Congratulations! You achieved a new personal best {metric_name} of {value} {unit}.',
    },
    
    # Correlation insights
    'correlation_positive': {
        'type': 'correlation',
        'severity': 'info',
        'title_template': '{metric_a} and {metric_b} are correlated',
        'description_template': "When your {metric_a} is higher, your {metric_b} tends to be higher too (correlation: {correlation:.2f}). This could mean they're related.",
    },
    'correlation_negative': {
        'type': 'correlation',
        'severity': 'info',
        'title_template': '{metric_a} affects {metric_b}',
        'description_template': 'When your {metric_a} is higher, your {metric_b} tends to be lower (correlation: {correlation:.2f}). Consider how changes in one might affect the other.',
    },
    
    # Recommendation insights
    'recommendation_sleep': {
        'type': 'recommendation',
        'severity': 'info',
        'title_template': 'Sleep improvement suggestion',
        'description_template': 'Based on your data, going to bed {minutes} minutes earlier could improve your sleep quality and next-day energy.',
    },
    'recommendation_activity': {
        'type': 'recommendation',
        'severity': 'info',
        'title_template': 'Activity suggestion',
        'description_template': 'You tend to have better {metric_name} on days when you exercise. Consider adding a short workout to your routine.',
    },
}


# Forward reference
from app.models.users import User
