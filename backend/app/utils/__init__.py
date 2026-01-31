"""
Utilities Package
=================
Helper functions and utilities
"""

from datetime import datetime, date
from typing import Optional


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable string."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s" if secs else f"{minutes}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m" if minutes else f"{hours}h"


def format_pace(seconds_per_km: int) -> str:
    """Format pace in seconds per km to min:sec string."""
    minutes = seconds_per_km // 60
    seconds = seconds_per_km % 60
    return f"{minutes}:{seconds:02d}"


def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """Calculate BMI from weight and height."""
    if height_m <= 0:
        return 0
    return round(weight_kg / (height_m ** 2), 1)


def get_bmi_category(bmi: float) -> str:
    """Get BMI category string."""
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


def parse_date(date_str: str, default: Optional[date] = None) -> Optional[date]:
    """Parse date string in various formats."""
    if not date_str:
        return default
    
    formats = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%m-%d-%Y", "%m/%d/%Y"]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    return default


def calculate_age(birth_date: date) -> int:
    """Calculate age from birth date."""
    today = date.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def round_to_precision(value: float, precision: int = 1) -> float:
    """Round value to specified decimal precision."""
    return round(value, precision)


def safe_divide(numerator: float, denominator: float, default: float = 0) -> float:
    """Safely divide with default value for division by zero."""
    if denominator == 0:
        return default
    return numerator / denominator
