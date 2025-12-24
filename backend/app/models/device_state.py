"""
Device State Model
==================

Stores device state history for auditing and recovery.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, String, DateTime, JSON, Index
from sqlalchemy.orm import Mapped

from .database import Base


class DeviceState(Base):
    """
    Model for storing device state history.

    Attributes:
        id: Primary key
        timestamp: When the state was recorded
        device_type: Type of device (led, relay, servo, etc.)
        device_id: Identifier for the specific device
        state: Current state as JSON
        previous_state: Previous state as JSON
        changed_by: What triggered the change (user, system, schedule)
    """

    __tablename__ = "device_states"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = Column(DateTime, default=datetime.now, nullable=False, index=True)
    device_type: Mapped[str] = Column(String(50), nullable=False, index=True)
    device_id: Mapped[str] = Column(String(50), nullable=False, index=True)
    state: Mapped[Dict] = Column(JSON, nullable=False)
    previous_state: Mapped[Optional[Dict]] = Column(JSON, nullable=True)
    changed_by: Mapped[str] = Column(String(50), default="system")

    __table_args__ = (
        Index('idx_device_type_id', 'device_type', 'device_id'),
        Index('idx_device_time', 'device_type', 'timestamp'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "device_type": self.device_type,
            "device_id": self.device_id,
            "state": self.state,
            "previous_state": self.previous_state,
            "changed_by": self.changed_by
        }

    @classmethod
    def record_change(
        cls,
        device_type: str,
        device_id: str,
        new_state: Dict[str, Any],
        previous_state: Dict[str, Any] = None,
        changed_by: str = "system"
    ) -> "DeviceState":
        """Record a device state change."""
        return cls(
            device_type=device_type,
            device_id=device_id,
            state=new_state,
            previous_state=previous_state,
            changed_by=changed_by
        )
