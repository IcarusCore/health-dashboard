"""
Seed metric definitions into the database.
"""
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.measurements import MetricDefinition

logger = logging.getLogger(__name__)

METRIC_DEFINITIONS = [
    # Vitals
    {"metric_key": "heart_rate", "display_name": "Heart Rate", "category": "vitals", "unit": "bpm", "data_type": "numeric", "aggregation_method": "avg", "icon": "heart", "color": "#ef4444", "sort_order": 1},
    {"metric_key": "resting_heart_rate", "display_name": "Resting Heart Rate", "category": "vitals", "unit": "bpm", "data_type": "numeric", "aggregation_method": "avg", "icon": "heart", "color": "#f97316", "sort_order": 2},
    {"metric_key": "heart_rate_variability", "display_name": "HRV", "category": "vitals", "unit": "ms", "data_type": "numeric", "aggregation_method": "avg", "icon": "activity", "color": "#8b5cf6", "sort_order": 3},
    {"metric_key": "blood_pressure_systolic", "display_name": "Blood Pressure (Systolic)", "category": "vitals", "unit": "mmHg", "data_type": "numeric", "aggregation_method": "avg", "icon": "thermometer", "color": "#ec4899", "sort_order": 4},
    {"metric_key": "blood_pressure_diastolic", "display_name": "Blood Pressure (Diastolic)", "category": "vitals", "unit": "mmHg", "data_type": "numeric", "aggregation_method": "avg", "icon": "thermometer", "color": "#f472b6", "sort_order": 5},
    {"metric_key": "blood_oxygen", "display_name": "Blood Oxygen", "category": "vitals", "unit": "%", "data_type": "numeric", "aggregation_method": "avg", "icon": "droplet", "color": "#06b6d4", "sort_order": 6},
    {"metric_key": "respiratory_rate", "display_name": "Respiratory Rate", "category": "vitals", "unit": "breaths/min", "data_type": "numeric", "aggregation_method": "avg", "icon": "wind", "color": "#14b8a6", "sort_order": 7},
    {"metric_key": "body_temperature", "display_name": "Body Temperature", "category": "vitals", "unit": "°F", "data_type": "numeric", "aggregation_method": "avg", "icon": "thermometer", "color": "#f59e0b", "sort_order": 8},
    
    # Activity
    {"metric_key": "steps", "display_name": "Steps", "category": "activity", "unit": "steps", "data_type": "numeric", "aggregation_method": "sum", "is_cumulative": True, "icon": "footprints", "color": "#22c55e", "sort_order": 10},
    {"metric_key": "distance_walking", "display_name": "Walking Distance", "category": "activity", "unit": "km", "data_type": "numeric", "aggregation_method": "sum", "is_cumulative": True, "icon": "map-pin", "color": "#10b981", "sort_order": 11},
    {"metric_key": "distance_cycling", "display_name": "Cycling Distance", "category": "activity", "unit": "km", "data_type": "numeric", "aggregation_method": "sum", "is_cumulative": True, "icon": "bike", "color": "#84cc16", "sort_order": 12},
    {"metric_key": "flights_climbed", "display_name": "Flights Climbed", "category": "activity", "unit": "floors", "data_type": "numeric", "aggregation_method": "sum", "is_cumulative": True, "icon": "stairs", "color": "#a3e635", "sort_order": 13},
    {"metric_key": "active_energy", "display_name": "Active Energy", "category": "activity", "unit": "kcal", "data_type": "numeric", "aggregation_method": "sum", "is_cumulative": True, "icon": "flame", "color": "#f97316", "sort_order": 14},
    {"metric_key": "basal_energy", "display_name": "Basal Energy", "category": "activity", "unit": "kcal", "data_type": "numeric", "aggregation_method": "sum", "is_cumulative": True, "icon": "zap", "color": "#fbbf24", "sort_order": 15},
    {"metric_key": "exercise_minutes", "display_name": "Exercise Minutes", "category": "activity", "unit": "min", "data_type": "numeric", "aggregation_method": "sum", "is_cumulative": True, "icon": "timer", "color": "#3b82f6", "sort_order": 16},
    {"metric_key": "stand_hours", "display_name": "Stand Hours", "category": "activity", "unit": "hours", "data_type": "numeric", "aggregation_method": "sum", "is_cumulative": True, "icon": "user", "color": "#6366f1", "sort_order": 17},
    {"metric_key": "vo2_max", "display_name": "VO2 Max", "category": "activity", "unit": "mL/kg/min", "data_type": "numeric", "aggregation_method": "avg", "icon": "lungs", "color": "#8b5cf6", "sort_order": 18},
    
    # Body
    {"metric_key": "weight", "display_name": "Weight", "category": "body", "unit": "kg", "data_type": "numeric", "aggregation_method": "avg", "icon": "scale", "color": "#64748b", "sort_order": 20},
    {"metric_key": "body_fat", "display_name": "Body Fat", "category": "body", "unit": "%", "data_type": "numeric", "aggregation_method": "avg", "icon": "percent", "color": "#94a3b8", "sort_order": 21},
    {"metric_key": "lean_body_mass", "display_name": "Lean Body Mass", "category": "body", "unit": "kg", "data_type": "numeric", "aggregation_method": "avg", "icon": "dumbbell", "color": "#475569", "sort_order": 22},
    {"metric_key": "bmi", "display_name": "BMI", "category": "body", "unit": "kg/m²", "data_type": "numeric", "aggregation_method": "avg", "icon": "calculator", "color": "#334155", "sort_order": 23},
    {"metric_key": "waist_circumference", "display_name": "Waist Circumference", "category": "body", "unit": "cm", "data_type": "numeric", "aggregation_method": "avg", "icon": "ruler", "color": "#1e293b", "sort_order": 24},
    {"metric_key": "height", "display_name": "Height", "category": "body", "unit": "cm", "data_type": "numeric", "aggregation_method": "avg", "icon": "ruler", "color": "#0f172a", "sort_order": 25},
]

async def seed_metric_definitions(db: AsyncSession):
    """Seed metric definitions if they don't exist."""
    for metric_data in METRIC_DEFINITIONS:
        result = await db.execute(
            select(MetricDefinition).where(MetricDefinition.metric_key == metric_data["metric_key"])
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            metric = MetricDefinition(**metric_data)
            db.add(metric)
            logger.info(f"Added metric definition: {metric_data['metric_key']}")
    
    await db.commit()
    logger.info("Metric definitions seeding complete")
