"""
Hardware Base Classes
=====================

Abstract base classes for hardware controllers.
Provides unified interface for both real hardware and simulation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class HardwareState(Enum):
    """Hardware component states."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class HardwareStatus:
    """Status information for hardware component."""
    name: str
    state: HardwareState
    is_simulation: bool
    last_update: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "is_simulation": self.is_simulation,
            "last_update": self.last_update.isoformat(),
            "error_message": self.error_message,
            "details": self.details
        }


class BaseHardwareController(ABC):
    """
    Abstract base class for all hardware controllers.

    Provides common functionality for initialization,
    cleanup, and status reporting.
    """

    def __init__(self, name: str, simulation_mode: bool = False):
        self.name = name
        self.simulation_mode = simulation_mode
        self._state = HardwareState.UNINITIALIZED
        self._error_message: Optional[str] = None
        self._last_update = datetime.now()
        self._initialized = False
        self._lock = asyncio.Lock()

    @property
    def is_ready(self) -> bool:
        """Check if hardware is ready for use."""
        return self._state == HardwareState.READY

    @property
    def status(self) -> HardwareStatus:
        """Get current hardware status."""
        return HardwareStatus(
            name=self.name,
            state=self._state,
            is_simulation=self.simulation_mode,
            last_update=self._last_update,
            error_message=self._error_message,
            details=self._get_status_details()
        )

    def _get_status_details(self) -> Dict[str, Any]:
        """Override to provide component-specific status details."""
        return {}

    async def initialize(self) -> bool:
        """
        Initialize the hardware controller.

        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True

        async with self._lock:
            try:
                self._state = HardwareState.INITIALIZING
                logger.info(f"Initializing {self.name} (simulation={self.simulation_mode})")

                success = await self._do_initialize()

                if success:
                    self._state = HardwareState.READY
                    self._initialized = True
                    self._error_message = None
                    logger.info(f"{self.name} initialized successfully")
                else:
                    self._state = HardwareState.ERROR
                    logger.error(f"{self.name} initialization failed")

                return success

            except Exception as e:
                self._state = HardwareState.ERROR
                self._error_message = str(e)
                logger.exception(f"{self.name} initialization error: {e}")
                return False

    async def cleanup(self) -> None:
        """Clean up hardware resources."""
        async with self._lock:
            try:
                logger.info(f"Cleaning up {self.name}")
                await self._do_cleanup()
                self._state = HardwareState.UNINITIALIZED
                self._initialized = False
            except Exception as e:
                logger.exception(f"{self.name} cleanup error: {e}")

    @abstractmethod
    async def _do_initialize(self) -> bool:
        """Perform actual initialization. Override in subclass."""
        pass

    @abstractmethod
    async def _do_cleanup(self) -> None:
        """Perform actual cleanup. Override in subclass."""
        pass

    def _update_timestamp(self) -> None:
        """Update last update timestamp."""
        self._last_update = datetime.now()


class SimulationMixin:
    """Mixin class providing simulation utilities."""

    def _simulate_delay(self, min_ms: float = 1, max_ms: float = 10) -> float:
        """
        Generate a realistic delay for simulation.

        Returns:
            Delay in seconds
        """
        import random
        return random.uniform(min_ms, max_ms) / 1000

    def _simulate_noise(self, value: float, noise_percent: float = 2.0) -> float:
        """
        Add realistic noise to a simulated value.

        Args:
            value: Base value
            noise_percent: Noise as percentage of value

        Returns:
            Value with noise added
        """
        import random
        noise = value * (noise_percent / 100) * random.uniform(-1, 1)
        return value + noise

    def _simulate_drift(self, value: float, target: float, rate: float = 0.1) -> float:
        """
        Simulate gradual drift towards a target value.

        Args:
            value: Current value
            target: Target value
            rate: Drift rate (0-1)

        Returns:
            New value after drift
        """
        return value + (target - value) * rate
