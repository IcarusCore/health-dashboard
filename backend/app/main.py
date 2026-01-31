"""
Personal Health Dashboard - Main Application
============================================
FastAPI application with comprehensive health data aggregation
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import logging
import time

from app.config import settings
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
from app.models.database import init_db, close_db

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting Health Dashboard API...")
    await init_db()
    logger.info("Database connection established")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Health Dashboard API...")
    await close_db()
    logger.info("Database connection closed")


# Create FastAPI application
app = FastAPI(
    title="Personal Health Dashboard API",
    description="""
    A comprehensive personal health data aggregation and analytics platform.
    
    ## Features
    
    - **Apple Health Import**: Import and process Apple Health export data
    - **Metrics Tracking**: Track vitals, activity, sleep, body composition, nutrition
    - **Workout Logging**: Detailed workout and exercise tracking
    - **Sleep Analysis**: Comprehensive sleep stage and quality analysis
    - **Analytics**: Trends, correlations, anomaly detection
    - **Insights**: AI-generated health insights and recommendations
    - **Alerts**: Configurable threshold and anomaly alerts
    - **Dashboard**: Customizable health overview dashboard
    
    ## Authentication
    
    All endpoints except `/api/v1/health` and `/api/v1/auth/*` require authentication.
    Use the `/api/v1/auth/login` endpoint to obtain a JWT token.
    
    ## Rate Limiting
    
    API requests are rate limited to prevent abuse. Standard limit is 100 requests per minute.
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all API requests."""
    logger.debug(f"{request.method} {request.url.path}")
    response = await call_next(request)
    return response


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred",
            "error_type": type(exc).__name__,
        },
    )


# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health Check"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Metrics"])
app.include_router(measurements.router, prefix="/api/v1/measurements", tags=["Measurements"])
app.include_router(workouts.router, prefix="/api/v1/workouts", tags=["Workouts"])
app.include_router(sleep.router, prefix="/api/v1/sleep", tags=["Sleep"])
app.include_router(imports.router, prefix="/api/v1/imports", tags=["Imports"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(insights.router, prefix="/api/v1/insights", tags=["Insights"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["Alerts"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(exports.router, prefix="/api/v1/exports", tags=["Exports"])


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint redirect to API docs."""
    return {
        "message": "Personal Health Dashboard API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
