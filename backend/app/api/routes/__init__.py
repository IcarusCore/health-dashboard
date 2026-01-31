"""
API Routes
==========
All API route modules
"""

from app.api.routes import (
    health,
    auth,
    users,
    metrics,
    measurements,
    workouts,
    sleep,
    imports,
    analytics,
    insights,
    alerts,
    dashboard,
    exports,
)

__all__ = [
    "health",
    "auth",
    "users",
    "metrics",
    "measurements",
    "workouts",
    "sleep",
    "imports",
    "analytics",
    "insights",
    "alerts",
    "dashboard",
    "exports",
]
