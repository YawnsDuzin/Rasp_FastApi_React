"""
I2C Controller
==============

Controls I2C devices including sensors, displays, and ADCs.
Supports multiple devices on the I2C bus.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .base import BaseHardwareController, SimulationMixin
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class I2CDevice:
    """Represents an I2C device."""
    address: int
    name: str
    is_connected: bool = False
    last_data: Optional[bytes] = None


class I2CController(BaseHardwareController, SimulationMixin):
    """
    Controller for I2C operations.

    Features:
    - Device scanning
    - Read/Write operations
    - Support for BMP280, ADS1115, OLED displays
    """

    def __init__(self, simulation_mode: bool = False):
        super().__init__("I2C Controller", simulation_mode)
        self._bus = None
        self._bus_number = settings.I2C_BUS
        self._devices: Dict[int, I2CDevice] = {}
        self._simulated_data: Dict[int, Dict[str, Any]] = {}

        # Known device addresses
        self._known_devices = {
            settings.I2C_LCD_ADDRESS: "LCD Display",
            settings.I2C_OLED_ADDRESS: "OLED Display",
            settings.I2C_BMP280_ADDRESS: "BMP280 Sensor",
            settings.I2C_ADS1115_ADDRESS: "ADS1115 ADC"
        }

    async def _do_initialize(self) -> bool:
        """Initialize I2C bus."""
        try:
            if not self.simulation_mode:
                try:
                    import smbus2
                    self._bus = smbus2.SMBus(self._bus_number)
                except ImportError:
                    logger.warning("smbus2 not available, falling back to simulation")
                    self.simulation_mode = True
                except FileNotFoundError:
                    logger.warning("I2C bus not available, falling back to simulation")
                    self.simulation_mode = True

            # Initialize simulated device data
            self._init_simulated_data()

            # Scan for devices
            await self.scan_devices()

            return True

        except Exception as e:
            logger.error(f"I2C initialization failed: {e}")
            return False

    async def _do_cleanup(self) -> None:
        """Clean up I2C resources."""
        if self._bus:
            self._bus.close()
            self._bus = None
        self._devices.clear()

    def _init_simulated_data(self) -> None:
        """Initialize simulated device data."""
        # BMP280 - Temperature and Pressure sensor
        self._simulated_data[settings.I2C_BMP280_ADDRESS] = {
            "temperature": 25.0,
            "pressure": 1013.25,
            "altitude": 0.0
        }

        # ADS1115 - 16-bit ADC
        self._simulated_data[settings.I2C_ADS1115_ADDRESS] = {
            "channel_0": 2.5,
            "channel_1": 1.8,
            "channel_2": 3.3,
            "channel_3": 0.0
        }

        # OLED Display
        self._simulated_data[settings.I2C_OLED_ADDRESS] = {
            "width": 128,
            "height": 64,
            "buffer": None
        }

    async def scan_devices(self) -> List[int]:
        """
        Scan I2C bus for connected devices (non-blocking).

        Returns:
            List of detected device addresses
        """
        detected = []

        if self.simulation_mode:
            # In simulation, return known devices
            for addr in self._known_devices:
                self._devices[addr] = I2CDevice(
                    address=addr,
                    name=self._known_devices[addr],
                    is_connected=True
                )
                detected.append(addr)
        else:
            # Run blocking I2C scan in thread pool
            detected = await asyncio.to_thread(self._scan_devices_sync)

        return detected

    def _scan_devices_sync(self) -> List[int]:
        """Synchronous I2C device scan (runs in thread pool)."""
        detected = []
        for addr in range(0x03, 0x78):
            try:
                self._bus.write_quick(addr)
                name = self._known_devices.get(addr, f"Unknown (0x{addr:02X})")
                self._devices[addr] = I2CDevice(
                    address=addr,
                    name=name,
                    is_connected=True
                )
                detected.append(addr)
                logger.info(f"Found I2C device at 0x{addr:02X}: {name}")
            except Exception:
                pass
        return detected

    async def read_byte(self, address: int, register: int) -> Optional[int]:
        """Read a single byte from an I2C device (non-blocking)."""
        if address not in self._devices:
            logger.error(f"Device at 0x{address:02X} not found")
            return None

        try:
            if self.simulation_mode:
                await asyncio.sleep(self._simulate_delay())
                return 0x00
            else:
                # Run blocking I2C call in thread pool
                return await asyncio.to_thread(
                    self._bus.read_byte_data, address, register
                )

        except Exception as e:
            logger.error(f"I2C read error: {e}")
            return None

    async def write_byte(self, address: int, register: int, value: int) -> bool:
        """Write a single byte to an I2C device (non-blocking)."""
        if address not in self._devices:
            return False

        try:
            if self.simulation_mode:
                await asyncio.sleep(self._simulate_delay())
            else:
                # Run blocking I2C call in thread pool
                await asyncio.to_thread(
                    self._bus.write_byte_data, address, register, value
                )
            return True

        except Exception as e:
            logger.error(f"I2C write error: {e}")
            return False

    async def read_block(self, address: int, register: int, length: int) -> Optional[bytes]:
        """Read a block of data from an I2C device (non-blocking)."""
        if address not in self._devices:
            return None

        try:
            if self.simulation_mode:
                await asyncio.sleep(self._simulate_delay())
                return bytes([0] * length)
            else:
                # Run blocking I2C call in thread pool
                data = await asyncio.to_thread(
                    self._bus.read_i2c_block_data, address, register, length
                )
                return bytes(data)

        except Exception as e:
            logger.error(f"I2C block read error: {e}")
            return None

    async def write_block(self, address: int, register: int, data: bytes) -> bool:
        """Write a block of data to an I2C device (non-blocking)."""
        if address not in self._devices:
            return False

        try:
            if self.simulation_mode:
                await asyncio.sleep(self._simulate_delay())
            else:
                # Run blocking I2C call in thread pool
                await asyncio.to_thread(
                    self._bus.write_i2c_block_data, address, register, list(data)
                )
            return True

        except Exception as e:
            logger.error(f"I2C block write error: {e}")
            return False

    # ==================== BMP280 Sensor ====================

    async def read_bmp280(self) -> Optional[Dict[str, float]]:
        """
        Read temperature and pressure from BMP280 (non-blocking).

        Returns:
            Dict with temperature (°C), pressure (hPa), and altitude (m)
        """
        address = settings.I2C_BMP280_ADDRESS

        if self.simulation_mode:
            await asyncio.sleep(self._simulate_delay())
            data = self._simulated_data[address]
            # Add some realistic variation
            return {
                "temperature": self._simulate_noise(data["temperature"], 0.5),
                "pressure": self._simulate_noise(data["pressure"], 0.2),
                "altitude": self._simulate_noise(data["altitude"], 1.0)
            }

        try:
            # Run blocking sensor read in thread pool
            return await asyncio.to_thread(self._read_bmp280_sync, address)

        except ImportError:
            logger.warning("BMP280 library not available")
            return None
        except Exception as e:
            logger.error(f"BMP280 read error: {e}")
            return None

    def _read_bmp280_sync(self, address: int) -> Optional[Dict[str, float]]:
        """Synchronous BMP280 read (runs in thread pool)."""
        import board
        import adafruit_bmp280

        i2c = board.I2C()
        bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=address)

        return {
            "temperature": bmp280.temperature,
            "pressure": bmp280.pressure,
            "altitude": bmp280.altitude
        }

    def set_simulated_bmp280(self, temperature: float = None, pressure: float = None) -> None:
        """Set simulated BMP280 values."""
        if temperature is not None:
            self._simulated_data[settings.I2C_BMP280_ADDRESS]["temperature"] = temperature
        if pressure is not None:
            self._simulated_data[settings.I2C_BMP280_ADDRESS]["pressure"] = pressure

    # ==================== ADS1115 ADC ====================

    async def read_adc(self, channel: int = 0) -> Optional[float]:
        """
        Read voltage from ADS1115 ADC channel (non-blocking).

        Args:
            channel: ADC channel (0-3)

        Returns:
            Voltage reading in volts
        """
        if channel < 0 or channel > 3:
            logger.error(f"Invalid ADC channel: {channel}")
            return None

        address = settings.I2C_ADS1115_ADDRESS

        if self.simulation_mode:
            await asyncio.sleep(self._simulate_delay())
            data = self._simulated_data[address]
            key = f"channel_{channel}"
            return self._simulate_noise(data[key], 1.0)

        try:
            # Run blocking ADC read in thread pool
            return await asyncio.to_thread(self._read_adc_sync, address, channel)

        except ImportError:
            logger.warning("ADS1115 library not available")
            return None
        except Exception as e:
            logger.error(f"ADC read error: {e}")
            return None

    def _read_adc_sync(self, address: int, channel: int) -> float:
        """Synchronous ADC read (runs in thread pool)."""
        import board
        import busio
        import adafruit_ads1x15.ads1115 as ADS
        from adafruit_ads1x15.analog_in import AnalogIn

        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS.ADS1115(i2c, address=address)

        channels = [ADS.P0, ADS.P1, ADS.P2, ADS.P3]
        chan = AnalogIn(ads, channels[channel])

        return chan.voltage

    async def read_all_adc_channels(self) -> Dict[int, float]:
        """Read all ADC channels."""
        results = {}
        for channel in range(4):
            value = await self.read_adc(channel)
            if value is not None:
                results[channel] = value
        return results

    def set_simulated_adc(self, channel: int, voltage: float) -> None:
        """Set simulated ADC channel value."""
        if 0 <= channel <= 3:
            key = f"channel_{channel}"
            self._simulated_data[settings.I2C_ADS1115_ADDRESS][key] = voltage

    def get_devices(self) -> Dict[int, Dict[str, Any]]:
        """Get all detected I2C devices."""
        return {
            addr: {
                "name": device.name,
                "is_connected": device.is_connected,
                "address_hex": f"0x{addr:02X}"
            }
            for addr, device in self._devices.items()
        }

    def _get_status_details(self) -> Dict[str, Any]:
        """Get I2C-specific status details."""
        return {
            "bus_number": self._bus_number,
            "devices": self.get_devices(),
            "device_count": len(self._devices)
        }
