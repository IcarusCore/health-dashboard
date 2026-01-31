"""
Sync Background Tasks
=====================
Celery tasks for data synchronization
"""

import logging
from datetime import datetime

from app.workers.celery_app import celery_app
from app.models.database import SyncSessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_import(self, import_id: str, user_id: str, source_id: str, file_path: str, is_zip: bool = False):
    """Process an Apple Health import file."""
    from app.services.apple_health_parser import process_apple_health_export
    
    try:
        process_apple_health_export(
            import_id=import_id,
            user_id=user_id,
            source_id=source_id,
            file_path=file_path,
            is_zip=is_zip,
        )
        logger.info(f"Import {import_id} completed successfully")
    except Exception as e:
        logger.error(f"Import {import_id} failed: {e}")
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes
