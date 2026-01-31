"""
Apple Health Parser Service
===========================
Parses Apple Health export XML files and imports data into the database
"""

import os
import zipfile
import logging
from datetime import datetime
from typing import Optional, Generator, Dict, Any
from uuid import UUID
from decimal import Decimal
import xml.etree.ElementTree as ET
from collections import defaultdict

from app.config import (
    settings, 
    APPLE_HEALTH_TYPE_MAPPING, 
    WORKOUT_TYPE_MAPPING,
    SLEEP_STAGE_MAPPING,
    UNIT_CONVERSIONS,
)
from app.models.database import SyncSessionLocal
from app.models.measurements import Measurement
from app.models.workouts import Workout
from app.models.sleep import SleepSession
from app.models.imports import ImportHistory
from app.models.users import DataSource

logger = logging.getLogger(__name__)


def convert_unit(value: float, from_unit: str, to_unit: str = None) -> tuple[float, str]:
    """Convert value from one unit to another."""
    if from_unit in UNIT_CONVERSIONS:
        target_unit, conversion = UNIT_CONVERSIONS[from_unit]
        if callable(conversion):
            return conversion(value), target_unit
        else:
            return value * conversion, target_unit
    return value, from_unit


def parse_apple_date(date_str: str) -> Optional[datetime]:
    """Parse Apple Health date format."""
    if not date_str:
        return None
    try:
        # Format: 2024-01-15 08:30:00 -0500
        # or: 2024-01-15 08:30:00 +0000
        return datetime.strptime(date_str[:19], "%Y-%m-%d %H:%M:%S")
    except (ValueError, IndexError):
        try:
            return datetime.fromisoformat(date_str.replace(' ', 'T'))
        except ValueError:
            return None


def stream_parse_xml(file_path: str) -> Generator[tuple[str, ET.Element], None, None]:
    """
    Stream parse large XML file without loading entire file into memory.
    Yields (tag, element) tuples.
    """
    context = ET.iterparse(file_path, events=('end',))
    
    for event, elem in context:
        if elem.tag in ('Record', 'Workout', 'WorkoutRoute', 'ActivitySummary'):
            yield elem.tag, elem
            elem.clear()


def process_record(elem: ET.Element, user_id: str, source_id: str) -> Optional[Dict[str, Any]]:
    """Process a Record element into measurement data."""
    record_type = elem.get('type', '')
    
    # Map to our metric key
    metric_key = APPLE_HEALTH_TYPE_MAPPING.get(record_type)
    if not metric_key:
        return None
    
    # Parse value
    value_str = elem.get('value', '')
    if not value_str:
        return None
    
    try:
        value = float(value_str)
    except ValueError:
        # Handle categorical values (like sleep stages)
        return None
    
    # Parse timestamps
    start_date = parse_apple_date(elem.get('startDate', ''))
    if not start_date:
        return None
    
    # Get unit and convert if needed
    unit = elem.get('unit', '')
    value, unit = convert_unit(value, unit)
    
    # Special handling for certain metrics
    if metric_key == 'blood_oxygen':
        value = value * 100  # Convert to percentage
        unit = '%'
    elif metric_key in ['distance_walking', 'distance_running']:
        if unit == 'm':
            value = value / 1000
            unit = 'km'
    
    return {
        'user_id': user_id,
        'source_id': source_id,
        'metric_key': metric_key,
        'timestamp': start_date,
        'value': Decimal(str(round(value, 4))),
        'unit': unit,
        'metadata': {
            'original_type': record_type,
            'source_name': elem.get('sourceName', ''),
            'device': elem.get('device', ''),
        }
    }


def process_workout(elem: ET.Element, user_id: str, source_id: str) -> Optional[Dict[str, Any]]:
    """Process a Workout element."""
    workout_type = elem.get('workoutActivityType', 'other')
    mapped_type = WORKOUT_TYPE_MAPPING.get(workout_type, 'other')
    
    start_date = parse_apple_date(elem.get('startDate', ''))
    end_date = parse_apple_date(elem.get('endDate', ''))
    
    if not start_date or not end_date:
        return None
    
    duration = float(elem.get('duration', 0))
    duration_unit = elem.get('durationUnit', 'min')
    if duration_unit == 'min':
        duration_seconds = int(duration * 60)
    elif duration_unit == 'hr':
        duration_seconds = int(duration * 3600)
    else:
        duration_seconds = int(duration)
    
    # Parse optional fields
    distance = None
    distance_str = elem.get('totalDistance', '')
    if distance_str:
        try:
            distance = float(distance_str)
            distance_unit = elem.get('totalDistanceUnit', 'm')
            if distance_unit == 'km':
                distance = distance * 1000
            elif distance_unit == 'mi':
                distance = distance * 1609.344
        except ValueError:
            pass
    
    calories = None
    calories_str = elem.get('totalEnergyBurned', '')
    if calories_str:
        try:
            calories = float(calories_str)
        except ValueError:
            pass
    
    # Get workout statistics from child elements
    avg_hr = None
    max_hr = None
    
    for stat in elem.findall('.//WorkoutStatistics'):
        stat_type = stat.get('type', '')
        if 'HeartRate' in stat_type:
            if stat.get('average'):
                try:
                    avg_hr = int(float(stat.get('average')))
                except ValueError:
                    pass
            if stat.get('maximum'):
                try:
                    max_hr = int(float(stat.get('maximum')))
                except ValueError:
                    pass
    
    return {
        'user_id': user_id,
        'source_id': source_id,
        'workout_type': mapped_type,
        'start_time': start_date,
        'end_time': end_date,
        'duration_seconds': duration_seconds,
        'distance_meters': Decimal(str(round(distance, 2))) if distance else None,
        'total_calories': Decimal(str(round(calories, 2))) if calories else None,
        'avg_heart_rate': avg_hr,
        'max_heart_rate': max_hr,
        'metadata': {
            'original_type': workout_type,
            'source_name': elem.get('sourceName', ''),
        }
    }


def process_sleep_records(records: list, user_id: str, source_id: str) -> list:
    """
    Process sleep analysis records into sleep sessions.
    Groups records by night and calculates sleep stages.
    """
    if not records:
        return []
    
    # Sort by start time
    records.sort(key=lambda x: x['start'])
    
    sessions = []
    current_session = None
    
    for record in records:
        stage = record['stage']
        start = record['start']
        end = record['end']
        duration = (end - start).total_seconds()
        
        # Check if this is part of the current session (within 2 hours of last record)
        if current_session:
            time_gap = (start - current_session['end']).total_seconds()
            if time_gap > 7200:  # 2 hours gap = new session
                # Save current session
                if current_session['duration'] > 1800:  # At least 30 minutes
                    sessions.append(finalize_sleep_session(current_session, user_id, source_id))
                current_session = None
        
        if not current_session:
            current_session = {
                'start': start,
                'end': end,
                'duration': duration,
                'in_bed': 0,
                'asleep': 0,
                'deep': 0,
                'light': 0,
                'rem': 0,
                'awake': 0,
            }
        else:
            current_session['end'] = max(current_session['end'], end)
            current_session['duration'] += duration
        
        # Accumulate stage times
        if stage == 'in_bed':
            current_session['in_bed'] += duration
        elif stage == 'asleep':
            current_session['asleep'] += duration
        elif stage == 'deep':
            current_session['deep'] += duration
            current_session['asleep'] += duration
        elif stage == 'light':
            current_session['light'] += duration
            current_session['asleep'] += duration
        elif stage == 'rem':
            current_session['rem'] += duration
            current_session['asleep'] += duration
        elif stage == 'awake':
            current_session['awake'] += duration
    
    # Don't forget the last session
    if current_session and current_session['duration'] > 1800:
        sessions.append(finalize_sleep_session(current_session, user_id, source_id))
    
    return sessions


def finalize_sleep_session(session_data: dict, user_id: str, source_id: str) -> Dict[str, Any]:
    """Convert accumulated sleep data into a SleepSession record."""
    duration = int(session_data['duration'])
    time_asleep = int(session_data['asleep']) if session_data['asleep'] > 0 else int(session_data['duration'] - session_data['awake'])
    
    efficiency = None
    if duration > 0 and time_asleep > 0:
        efficiency = round((time_asleep / duration) * 100, 2)
    
    return {
        'user_id': user_id,
        'source_id': source_id,
        'start_time': session_data['start'],
        'end_time': session_data['end'],
        'duration_seconds': duration,
        'time_asleep_seconds': time_asleep if time_asleep > 0 else None,
        'time_awake_seconds': int(session_data['awake']) if session_data['awake'] > 0 else None,
        'time_deep_seconds': int(session_data['deep']) if session_data['deep'] > 0 else None,
        'time_light_seconds': int(session_data['light']) if session_data['light'] > 0 else None,
        'time_rem_seconds': int(session_data['rem']) if session_data['rem'] > 0 else None,
        'sleep_efficiency': Decimal(str(efficiency)) if efficiency else None,
        'metadata': {'source': 'apple_health'},
    }


def process_apple_health_export(
    import_id: str,
    user_id: str,
    source_id: str,
    file_path: str,
    is_zip: bool = False,
):
    """
    Main function to process Apple Health export.
    Runs as a background task.
    """
    db = SyncSessionLocal()
    
    try:
        # Update import status
        import_record = db.query(ImportHistory).filter(ImportHistory.id == import_id).first()
        if not import_record:
            logger.error(f"Import record {import_id} not found")
            return
        
        import_record.status = 'processing'
        import_record.started_at = datetime.utcnow()
        import_record.current_phase = 'extracting'
        db.commit()
        
        # Extract if zip
        xml_path = file_path
        if is_zip:
            import_record.current_phase = 'extracting'
            db.commit()
            
            extract_dir = os.path.dirname(file_path)
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Find export.xml in the zip
                for name in zip_ref.namelist():
                    if name.endswith('export.xml'):
                        zip_ref.extract(name, extract_dir)
                        xml_path = os.path.join(extract_dir, name)
                        break
        
        if not os.path.exists(xml_path):
            raise FileNotFoundError("export.xml not found in archive")
        
        import_record.current_phase = 'parsing'
        db.commit()
        
        # Process records
        measurements_batch = []
        workouts_batch = []
        sleep_records = []
        
        records_processed = 0
        measurements_imported = 0
        workouts_imported = 0
        sleep_sessions_imported = 0
        records_skipped = 0
        
        min_date = None
        max_date = None
        
        # Stream parse the XML
        for tag, elem in stream_parse_xml(xml_path):
            records_processed += 1
            
            if tag == 'Record':
                record_type = elem.get('type', '')
                
                # Handle sleep records separately
                if 'SleepAnalysis' in record_type:
                    stage_value = elem.get('value', '')
                    stage = SLEEP_STAGE_MAPPING.get(stage_value, 'asleep')
                    start = parse_apple_date(elem.get('startDate', ''))
                    end = parse_apple_date(elem.get('endDate', ''))
                    if start and end:
                        sleep_records.append({
                            'stage': stage,
                            'start': start,
                            'end': end,
                        })
                else:
                    measurement = process_record(elem, user_id, source_id)
                    if measurement:
                        measurements_batch.append(measurement)
                        
                        # Track date range
                        ts = measurement['timestamp']
                        if min_date is None or ts < min_date:
                            min_date = ts
                        if max_date is None or ts > max_date:
                            max_date = ts
                    else:
                        records_skipped += 1
            
            elif tag == 'Workout':
                workout = process_workout(elem, user_id, source_id)
                if workout:
                    workouts_batch.append(workout)
                    
                    ts = workout['start_time']
                    if min_date is None or ts < min_date:
                        min_date = ts
                    if max_date is None or ts > max_date:
                        max_date = ts
                else:
                    records_skipped += 1
            
            # Batch insert every 1000 records
            if len(measurements_batch) >= 1000:
                db.bulk_insert_mappings(Measurement, measurements_batch)
                measurements_imported += len(measurements_batch)
                measurements_batch = []
                
                import_record.records_imported = measurements_imported + workouts_imported + sleep_sessions_imported
                import_record.progress_percent = min(90, int((records_processed / 1000000) * 100))
                db.commit()
            
            if len(workouts_batch) >= 100:
                db.bulk_insert_mappings(Workout, workouts_batch)
                workouts_imported += len(workouts_batch)
                workouts_batch = []
                db.commit()
        
        # Insert remaining batches
        if measurements_batch:
            db.bulk_insert_mappings(Measurement, measurements_batch)
            measurements_imported += len(measurements_batch)
        
        if workouts_batch:
            db.bulk_insert_mappings(Workout, workouts_batch)
            workouts_imported += len(workouts_batch)
        
        # Process sleep records into sessions
        import_record.current_phase = 'processing_sleep'
        db.commit()
        
        sleep_sessions = process_sleep_records(sleep_records, user_id, source_id)
        if sleep_sessions:
            db.bulk_insert_mappings(SleepSession, sleep_sessions)
            sleep_sessions_imported = len(sleep_sessions)
        
        # Update import record
        import_record.status = 'completed'
        import_record.current_phase = 'complete'
        import_record.progress_percent = 100
        import_record.completed_at = datetime.utcnow()
        import_record.records_total = records_processed
        import_record.records_imported = measurements_imported + workouts_imported + sleep_sessions_imported
        import_record.records_skipped = records_skipped
        import_record.measurements_imported = measurements_imported
        import_record.workouts_imported = workouts_imported
        import_record.sleep_sessions_imported = sleep_sessions_imported
        import_record.data_start_date = min_date
        import_record.data_end_date = max_date
        
        # Update data source
        source = db.query(DataSource).filter(DataSource.id == source_id).first()
        if source:
            source.last_sync_at = datetime.utcnow()
            source.sync_status = 'success'
            source.total_records_imported += import_record.records_imported
        
        db.commit()
        
        logger.info(f"Import {import_id} completed: {measurements_imported} measurements, {workouts_imported} workouts, {sleep_sessions_imported} sleep sessions")
        
        # Cleanup uploaded file
        try:
            os.remove(file_path)
            if is_zip and xml_path != file_path:
                os.remove(xml_path)
        except OSError:
            pass
        
    except Exception as e:
        logger.error(f"Import {import_id} failed: {str(e)}", exc_info=True)
        
        import_record = db.query(ImportHistory).filter(ImportHistory.id == import_id).first()
        if import_record:
            import_record.status = 'failed'
            import_record.error_message = str(e)
            import_record.completed_at = datetime.utcnow()
            
            source = db.query(DataSource).filter(DataSource.id == source_id).first()
            if source:
                source.sync_status = 'error'
                source.sync_error_message = str(e)
            
            db.commit()
    
    finally:
        db.close()
