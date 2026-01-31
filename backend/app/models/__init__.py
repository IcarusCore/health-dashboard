"""
Database Models
===============
SQLAlchemy ORM models for the Health Dashboard
"""

from app.models.database import Base, get_db, get_sync_db, AsyncSessionLocal, SyncSessionLocal
from app.models.users import User, UserSettings, DataSource
from app.models.measurements import Measurement, MetricDefinition, MetricCorrelation
from app.models.workouts import Workout
from app.models.sleep import SleepSession
from app.models.daily_summary import DailySummary
from app.models.insights import HealthInsight
from app.models.alerts import Alert, AlertNotification
from app.models.imports import ImportHistory
from app.models.custom_metrics import CustomMetric

__all__ = [
    # Base and sessions
    "Base",
    "get_db",
    "get_sync_db",
    "AsyncSessionLocal",
    "SyncSessionLocal",
    
    # User models
    "User",
    "UserSettings",
    "DataSource",
    
    # Measurement models
    "Measurement",
    "MetricDefinition",
    "MetricCorrelation",
    
    # Activity models
    "Workout",
    "SleepSession",
    
    # Summary models
    "DailySummary",
    
    # Insight models
    "HealthInsight",
    
    # Alert models
    "Alert",
    "AlertNotification",
    
    # Import models
    "ImportHistory",
    
    # Custom models
    "CustomMetric",
]
