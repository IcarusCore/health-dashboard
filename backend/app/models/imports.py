"""
Import History Models
=====================
SQLAlchemy models for tracking data imports
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.models.database import Base


class ImportHistory(Base):
    """Record of data import operations."""
    
    __tablename__ = "import_history"
    
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
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("data_sources.id", ondelete="SET NULL")
    )
    
    # File information
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64))  # SHA256
    
    # Import status
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # Statuses: 'pending', 'processing', 'completed', 'failed', 'cancelled'
    
    # Progress tracking
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    current_phase: Mapped[Optional[str]] = mapped_column(String(50))
    # Phases: 'uploading', 'extracting', 'parsing', 'processing', 'finalizing'
    
    # Record counts
    records_total: Mapped[int] = mapped_column(Integer, default=0)
    records_imported: Mapped[int] = mapped_column(Integer, default=0)
    records_skipped: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)
    records_duplicate: Mapped[int] = mapped_column(Integer, default=0)
    
    # Breakdown by type
    measurements_imported: Mapped[int] = mapped_column(Integer, default=0)
    workouts_imported: Mapped[int] = mapped_column(Integer, default=0)
    sleep_sessions_imported: Mapped[int] = mapped_column(Integer, default=0)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    error_details: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Date range of imported data
    data_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    data_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Metadata
    source_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="import_history")
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate import duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def records_per_second(self) -> Optional[float]:
        """Calculate import speed."""
        duration = self.duration_seconds
        if duration and duration > 0 and self.records_imported:
            return self.records_imported / duration
        return None
    
    @property
    def success_rate(self) -> Optional[float]:
        """Calculate percentage of successfully imported records."""
        if self.records_total > 0:
            return (self.records_imported / self.records_total) * 100
        return None
    
    def __repr__(self):
        return f"<ImportHistory {self.filename} ({self.status})>"


# Forward reference
from app.models.users import User
