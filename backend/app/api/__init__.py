"""
API Routes Package
==================
FastAPI route handlers for the Health Dashboard
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
