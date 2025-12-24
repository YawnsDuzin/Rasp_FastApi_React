"""
System Log Model
================

Stores system events and error logs.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Index
from sqlalchemy.orm import Mapped

from .database import Base


class LogLevel(str, Enum):
    """Log severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SystemLog(Base):
    """
    Model for storing system logs and events.

    Attributes:
        id: Primary key
        timestamp: When the event occurred
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        source: Source of the log (module/component name)
        message: Log message
        details: Additional details as JSON
        user_action: Whether this was triggered by user action
    """

    __tablename__ = "system_logs"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = Column(DateTime, default=datetime.now, nullable=False, index=True)
    level: Mapped[str] = Column(String(20), nullable=False, index=True)
    source: Mapped[str] = Column(String(100), nullable=False, index=True)
    message: Mapped[str] = Column(Text, nullable=False)
    details: Mapped[Optional[Dict]] = Column(JSON, nullable=True)
    user_action: Mapped[bool] = Column(Integer, default=0)  # SQLite doesn't have bool

    __table_args__ = (
        Index('idx_log_level_time', 'level', 'timestamp'),
        Index('idx_log_source_time', 'source', 'timestamp'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "level": self.level,
            "source": self.source,
            "message": self.message,
            "details": self.details,
            "user_action": bool(self.user_action)
        }

    @classmethod
    def create_log(
        cls,
        level: LogLevel,
        source: str,
        message: str,
        details: Dict[str, Any] = None,
        user_action: bool = False
    ) -> "SystemLog":
        """Create a new log entry."""
        return cls(
            level=level.value,
            source=source,
            message=message,
            details=details,
            user_action=1 if user_action else 0
        )
