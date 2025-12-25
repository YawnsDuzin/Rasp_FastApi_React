"""
SPI Controller
==============

Controls SPI devices including ADCs, DACs, and sensors.
Supports hardware SPI with configurable speed and mode.
"""

import asyncio
from typing import Dict, Optional, Any, List
from dataclasses import dataclass

from .base import BaseHardwareController, SimulationMixin
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SPIDevice:
    """Represents an SPI device."""
    bus: int
    device: int
    name: str
    max_speed: int
    mode: int = 0
    bits_per_word: int = 8


class SPIController(BaseHardwareController, SimulationMixin):
    """
    Controller for SPI operations.

    Features:
    - MCP3008 ADC (10-bit, 8 channels)
    - MCP4725 DAC (12-bit)
    - MAX31855 Thermocouple sensor
    """

    def __init__(self, simulation_mode: bool = False):
        super().__init__("SPI Controller", simulation_mode)
        self._spi = None
        self._bus = settings.SPI_BUS
        self._device = settings.SPI_DEVICE
        self._max_speed = settings.SPI_MAX_SPEED
        self._devices: Dict[str, SPIDevice] = {}
        self._simulated_data: Dict[str, Any] = {}

    async def _do_initialize(self) -> bool:
        """Initialize SPI bus."""
        try:
            if not self.simulation_mode:
                try:
                    import spidev
                    self._spi = spidev.SpiDev()
                    self._spi.open(self._bus, self._device)
                    self._spi.max_speed_hz = self._max_speed
                    self._spi.mode = 0
                except ImportError:
                    logger.warning("spidev not available, falling back to simulation")
                    self.simulation_mode = True
                except FileNotFoundError:
                    logger.warning("SPI device not available, falling back to simulation")
                    self.simulation_mode = True

            # Initialize simulated data
            self._init_simulated_data()

            # Register known devices
            self._devices["MCP3008"] = SPIDevice(
                bus=self._bus,
                device=self._device,
                name="MCP3008 ADC",
                max_speed=1000000
            )

            return True

        except Exception as e:
            logger.error(f"SPI initialization failed: {e}")
            return False

    async def _do_cleanup(self) -> None:
        """Clean up SPI resources."""
        if self._spi:
            self._spi.close()
            self._spi = None
        self._devices.clear()

    def _init_simulated_data(self) -> None:
        """Initialize simulated device data."""
        # MCP3008 - 8-channel 10-bit ADC
        self._simulated_data["MCP3008"] = {
            f"channel_{i}": 512 for i in range(8)  # Mid-range value
        }

        # Update with some varied values
        self._simulated_data["MCP3008"]["channel_0"] = 750  # ~2.4V
        self._simulated_data["MCP3008"]["channel_1"] = 500  # ~1.6V
        self._simulated_data["MCP3008"]["channel_2"] = 1000 # ~3.2V
        self._simulated_data["MCP3008"]["channel_3"] = 100  # ~0.3V

    # ==================== MCP3008 ADC ====================

    async def read_mcp3008(self, channel: int) -> Optional[int]:
        """
        Read raw value from MCP3008 ADC channel (non-blocking).

        Args:
            channel: ADC channel (0-7)

        Returns:
            10-bit value (0-1023)
        """
        if channel < 0 or channel > 7:
            logger.error(f"Invalid MCP3008 channel: {channel}")
            return None

        try:
            if self.simulation_mode:
                await asyncio.sleep(self._simulate_delay())
                key = f"channel_{channel}"
                value = self._simulated_data["MCP3008"].get(key, 512)
                return int(self._simulate_noise(value, 2.0))
            else:
                # Run blocking SPI call in thread pool
                return await asyncio.to_thread(self._read_mcp3008_sync, channel)

        except Exception as e:
            logger.error(f"MCP3008 read error: {e}")
            return None

    def _read_mcp3008_sync(self, channel: int) -> int:
        """Synchronous MCP3008 read (runs in thread pool)."""
        # MCP3008 SPI protocol
        cmd = [1, (8 + channel) << 4, 0]
        result = self._spi.xfer2(cmd)
        value = ((result[1] & 3) << 8) + result[2]
        return value

    async def read_mcp3008_voltage(self, channel: int, vref: float = 3.3) -> Optional[float]:
        """
        Read voltage from MCP3008 ADC channel.

        Args:
            channel: ADC channel (0-7)
            vref: Reference voltage

        Returns:
            Voltage reading
        """
        raw = await self.read_mcp3008(channel)
        if raw is None:
            return None
        return (raw / 1023.0) * vref

    async def read_all_mcp3008_channels(self, vref: float = 3.3) -> Dict[int, float]:
        """Read all MCP3008 ADC channels."""
        results = {}
        for channel in range(8):
            voltage = await self.read_mcp3008_voltage(channel, vref)
            if voltage is not None:
                results[channel] = round(voltage, 3)
        return results

    def set_simulated_mcp3008(self, channel: int, raw_value: int) -> None:
        """Set simulated MCP3008 channel value."""
        if 0 <= channel <= 7 and 0 <= raw_value <= 1023:
            key = f"channel_{channel}"
            self._simulated_data["MCP3008"][key] = raw_value

    # ==================== Generic SPI Operations ====================

    async def transfer(self, data: List[int]) -> Optional[List[int]]:
        """
        Perform SPI transfer (non-blocking).

        Args:
            data: List of bytes to send

        Returns:
            List of received bytes
        """
        try:
            if self.simulation_mode:
                await asyncio.sleep(self._simulate_delay())
                return [0] * len(data)
            else:
                # Run blocking SPI call in thread pool
                return await asyncio.to_thread(self._spi.xfer2, data)

        except Exception as e:
            logger.error(f"SPI transfer error: {e}")
            return None

    async def write(self, data: List[int]) -> bool:
        """Write data to SPI bus."""
        result = await self.transfer(data)
        return result is not None

    def get_devices(self) -> Dict[str, Dict[str, Any]]:
        """Get registered SPI devices."""
        return {
            name: {
                "bus": device.bus,
                "device": device.device,
                "name": device.name,
                "max_speed": device.max_speed,
                "mode": device.mode
            }
            for name, device in self._devices.items()
        }

    def _get_status_details(self) -> Dict[str, Any]:
        """Get SPI-specific status details."""
        return {
            "bus": self._bus,
            "device": self._device,
            "max_speed": self._max_speed,
            "devices": self.get_devices()
        }
