"""
Application Configuration
=========================
Centralized configuration using Pydantic Settings
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "Personal Health Dashboard"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "your_super_secret_key_change_this_in_production"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://healthuser:health_secure_pass_2024@localhost:5432/healthdashboard"
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Convert standard postgresql:// URL to async postgresql+asyncpg:// format"""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url
    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Convert DATABASE_URL to sync format (remove +asyncpg if present)"""
        url = self.DATABASE_URL
        # Remove async driver prefix if present
        if "+asyncpg" in url:
            url = url.replace("postgresql+asyncpg://", "postgresql://")
        elif url.startswith("postgresql://"):
            pass  # Already sync format
        return url
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://:health_redis_pass_2024@localhost:6379/0"
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    
    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 500  # Apple Health exports can be large
    UPLOAD_DIR: str = "/app/uploads"
    ALLOWED_EXTENSIONS: List[str] = ["xml", "zip"]
    
    # Email (optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    SMTP_TLS: bool = True
    
    # Discord (optional)
    DISCORD_WEBHOOK_URL: Optional[str] = None
    
    # Pushover (optional)
    PUSHOVER_USER_KEY: Optional[str] = None
    PUSHOVER_API_TOKEN: Optional[str] = None
    
    # Analytics
    CORRELATION_MIN_SAMPLES: int = 14  # Minimum days for correlation analysis
    ANOMALY_ZSCORE_THRESHOLD: float = 2.5
    TREND_MIN_DAYS: int = 7
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    # Background Tasks
    CELERY_BROKER_URL: Optional[str] = None
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def celery_broker(self) -> str:
        """Get Celery broker URL."""
        return self.CELERY_BROKER_URL or self.REDIS_URL
    
    @property
    def max_upload_bytes(self) -> int:
        """Get maximum upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()


# Apple Health type mappings
APPLE_HEALTH_TYPE_MAPPING = {
    # Vitals
    "HKQuantityTypeIdentifierHeartRate": "heart_rate",
    "HKQuantityTypeIdentifierRestingHeartRate": "resting_heart_rate",
    "HKQuantityTypeIdentifierHeartRateVariabilitySDNN": "heart_rate_variability",
    "HKQuantityTypeIdentifierBloodPressureSystolic": "blood_pressure_systolic",
    "HKQuantityTypeIdentifierBloodPressureDiastolic": "blood_pressure_diastolic",
    "HKQuantityTypeIdentifierOxygenSaturation": "blood_oxygen",
    "HKQuantityTypeIdentifierRespiratoryRate": "respiratory_rate",
    "HKQuantityTypeIdentifierBodyTemperature": "body_temperature",
    
    # Activity
    "HKQuantityTypeIdentifierStepCount": "steps",
    "HKQuantityTypeIdentifierDistanceWalkingRunning": "distance_walking",
    "HKQuantityTypeIdentifierDistanceCycling": "distance_cycling",
    "HKQuantityTypeIdentifierFlightsClimbed": "flights_climbed",
    "HKQuantityTypeIdentifierActiveEnergyBurned": "active_energy",
    "HKQuantityTypeIdentifierBasalEnergyBurned": "basal_energy",
    "HKQuantityTypeIdentifierAppleExerciseTime": "exercise_minutes",
    "HKQuantityTypeIdentifierAppleStandHour": "stand_hours",
    "HKQuantityTypeIdentifierVO2Max": "vo2_max",
    
    # Body
    "HKQuantityTypeIdentifierBodyMass": "weight",
    "HKQuantityTypeIdentifierBodyFatPercentage": "body_fat",
    "HKQuantityTypeIdentifierLeanBodyMass": "lean_body_mass",
    "HKQuantityTypeIdentifierBodyMassIndex": "bmi",
    "HKQuantityTypeIdentifierWaistCircumference": "waist_circumference",
    "HKQuantityTypeIdentifierHeight": "height",
    
    # Nutrition
    "HKQuantityTypeIdentifierDietaryWater": "water_intake",
    "HKQuantityTypeIdentifierDietaryCaffeine": "caffeine",
    "HKQuantityTypeIdentifierDietaryEnergyConsumed": "dietary_calories",
    "HKQuantityTypeIdentifierDietaryProtein": "dietary_protein",
    "HKQuantityTypeIdentifierDietaryCarbohydrates": "dietary_carbs",
    "HKQuantityTypeIdentifierDietaryFatTotal": "dietary_fat",
    "HKQuantityTypeIdentifierDietaryFiber": "dietary_fiber",
    "HKQuantityTypeIdentifierDietarySugar": "dietary_sugar",
    "HKQuantityTypeIdentifierNumberOfAlcoholicBeverages": "alcohol",
    
    # Sleep
    "HKCategoryTypeIdentifierSleepAnalysis": "sleep_analysis",
    
    # Mindfulness
    "HKCategoryTypeIdentifierMindfulSession": "mindful_minutes",
}

# Unit conversions
UNIT_CONVERSIONS = {
    # Length
    "mi": ("km", 1.60934),
    "yd": ("m", 0.9144),
    "ft": ("m", 0.3048),
    "in": ("cm", 2.54),
    
    # Mass
    "lb": ("kg", 0.453592),
    "oz": ("g", 28.3495),
    "st": ("kg", 6.35029),
    
    # Temperature
    "degF": ("degC", lambda f: (f - 32) * 5 / 9),
    
    # Energy
    "Cal": ("kcal", 1.0),
    "kJ": ("kcal", 0.239006),
    
    # Volume
    "gal": ("L", 3.78541),
    "qt": ("L", 0.946353),
    "pt": ("L", 0.473176),
    "cup": ("mL", 236.588),
    "fl_oz_us": ("mL", 29.5735),
}

# Workout type mappings
WORKOUT_TYPE_MAPPING = {
    "HKWorkoutActivityTypeRunning": "running",
    "HKWorkoutActivityTypeWalking": "walking",
    "HKWorkoutActivityTypeCycling": "cycling",
    "HKWorkoutActivityTypeSwimming": "swimming",
    "HKWorkoutActivityTypeHiking": "hiking",
    "HKWorkoutActivityTypeYoga": "yoga",
    "HKWorkoutActivityTypeFunctionalStrengthTraining": "strength_training",
    "HKWorkoutActivityTypeTraditionalStrengthTraining": "strength_training",
    "HKWorkoutActivityTypeHighIntensityIntervalTraining": "hiit",
    "HKWorkoutActivityTypeCrossTraining": "cross_training",
    "HKWorkoutActivityTypeCoreTraining": "core_training",
    "HKWorkoutActivityTypePilates": "pilates",
    "HKWorkoutActivityTypeDance": "dance",
    "HKWorkoutActivityTypeElliptical": "elliptical",
    "HKWorkoutActivityTypeRowing": "rowing",
    "HKWorkoutActivityTypeStairClimbing": "stair_climbing",
    "HKWorkoutActivityTypeMixedCardio": "cardio",
    "HKWorkoutActivityTypePlay": "play",
    "HKWorkoutActivityTypeCooldown": "cooldown",
    "HKWorkoutActivityTypeOther": "other",
}

# Sleep stage mappings
SLEEP_STAGE_MAPPING = {
    "HKCategoryValueSleepAnalysisInBed": "in_bed",
    "HKCategoryValueSleepAnalysisAsleep": "asleep",
    "HKCategoryValueSleepAnalysisAsleepCore": "light",
    "HKCategoryValueSleepAnalysisAsleepDeep": "deep",
    "HKCategoryValueSleepAnalysisAsleepREM": "rem",
    "HKCategoryValueSleepAnalysisAwake": "awake",
    "HKCategoryValueSleepAnalysisAsleepUnspecified": "asleep",
}
