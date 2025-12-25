"""
Sensor Controller
=================

Unified interface for various sensors.
Includes DHT temperature/humidity, ultrasonic distance, PIR motion, etc.
"""

import asyncio
import random
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .base import BaseHardwareController, SimulationMixin
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class SensorType(Enum):
    """Types of sensors."""
    DHT11 = "DHT11"
    DHT22 = "DHT22"
    ULTRASONIC = "HC-SR04"
    PIR = "PIR"
    LIGHT = "LDR"
    SOIL_MOISTURE = "SOIL"


@dataclass
class SensorReading:
    """Represents a sensor reading."""
    sensor_type: SensorType
    value: Any
    unit: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sensor_type": self.sensor_type.value,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat()
        }


class SensorController(BaseHardwareController, SimulationMixin):
    """
    Controller for various sensors.

    Supported Sensors:
    - DHT11/DHT22: Temperature and Humidity
    - HC-SR04: Ultrasonic Distance
    - PIR: Motion Detection
    - LDR: Light Level
    - Soil Moisture Sensor
    """

    def __init__(self, simulation_mode: bool = False):
        super().__init__("Sensor Controller", simulation_mode)
        self._dht_pin = settings.DHT_PIN
        self._dht_type = settings.DHT_TYPE
        self._dht_sensor = None

        # Simulated sensor values
        self._simulated_values: Dict[str, Any] = {
            "temperature": 25.0,
            "humidity": 50.0,
            "distance": 100.0,  # cm
            "motion": False,
            "light": 500,  # 0-1023
            "soil_moisture": 600  # 0-1023
        }

        # Sensor pins
        self._ultrasonic_trigger = 23
        self._ultrasonic_echo = 24
        self._pir_pin = 25
        self._light_pin = 0  # MCP3008 channel
        self._soil_pin = 1  # MCP3008 channel

    async def _do_initialize(self) -> bool:
        """Initialize sensors."""
        try:
            if not self.simulation_mode:
                try:
                    import adafruit_dht
                    import board

                    pin = getattr(board, f"D{self._dht_pin}")
                    if self._dht_type == "DHT22":
                        self._dht_sensor = adafruit_dht.DHT22(pin)
                    else:
                        self._dht_sensor = adafruit_dht.DHT11(pin)

                except ImportError:
                    logger.warning("DHT library not available, falling back to simulation")
                    self.simulation_mode = True
                except Exception as e:
                    logger.warning(f"DHT sensor init failed: {e}")
                    self.simulation_mode = True

            return True

        except Exception as e:
            logger.error(f"Sensor initialization failed: {e}")
            return False

    async def _do_cleanup(self) -> None:
        """Clean up sensor resources."""
        if self._dht_sensor:
            try:
                self._dht_sensor.exit()
            except:
                pass
            self._dht_sensor = None

    # ==================== DHT Temperature/Humidity ====================

    async def read_dht(self) -> Optional[Dict[str, float]]:
        """
        Read temperature and humidity from DHT sensor (non-blocking).

        Returns:
            Dict with temperature (°C) and humidity (%)
        """
        try:
            if self.simulation_mode:
                await asyncio.sleep(self._simulate_delay(50, 100))

                # Simulate realistic values with drift
                self._simulated_values["temperature"] = self._simulate_drift(
                    self._simulated_values["temperature"],
                    25.0 + random.uniform(-2, 2),
                    0.1
                )
                self._simulated_values["humidity"] = self._simulate_drift(
                    self._simulated_values["humidity"],
                    50.0 + random.uniform(-5, 5),
                    0.1
                )

                return {
                    "temperature": round(self._simulate_noise(
                        self._simulated_values["temperature"], 0.5
                    ), 1),
                    "humidity": round(self._simulate_noise(
                        self._simulated_values["humidity"], 1.0
                    ), 1)
                }
            else:
                # Run blocking DHT read in thread pool
                return await asyncio.to_thread(self._read_dht_sync)

        except Exception as e:
            logger.error(f"DHT read error: {e}")
            return None

    def _read_dht_sync(self) -> Optional[Dict[str, float]]:
        """Synchronous DHT read with retry (runs in thread pool)."""
        import time
        for _ in range(3):
            try:
                temperature = self._dht_sensor.temperature
                humidity = self._dht_sensor.humidity

                if temperature is not None and humidity is not None:
                    return {
                        "temperature": round(temperature, 1),
                        "humidity": round(humidity, 1)
                    }
            except RuntimeError:
                time.sleep(0.1)
        return None

    async def get_temperature(self) -> Optional[float]:
        """Get current temperature."""
        data = await self.read_dht()
        return data["temperature"] if data else None

    async def get_humidity(self) -> Optional[float]:
        """Get current humidity."""
        data = await self.read_dht()
        return data["humidity"] if data else None

    # ==================== Ultrasonic Distance ====================

    async def read_ultrasonic(self) -> Optional[float]:
        """
        Read distance from HC-SR04 ultrasonic sensor (non-blocking).

        Returns:
            Distance in centimeters
        """
        try:
            if self.simulation_mode:
                await asyncio.sleep(self._simulate_delay(20, 50))

                # Simulate object movement
                self._simulated_values["distance"] = self._simulate_drift(
                    self._simulated_values["distance"],
                    100.0 + random.uniform(-20, 20),
                    0.2
                )

                return round(self._simulate_noise(
                    self._simulated_values["distance"], 2.0
                ), 1)
            else:
                # Run blocking ultrasonic measurement in thread pool
                return await asyncio.to_thread(self._read_ultrasonic_sync)

        except Exception as e:
            logger.error(f"Ultrasonic read error: {e}")
            return None

    def _read_ultrasonic_sync(self) -> Optional[float]:
        """Synchronous ultrasonic read (runs in thread pool)."""
        import RPi.GPIO as GPIO
        import time

        GPIO.setup(self._ultrasonic_trigger, GPIO.OUT)
        GPIO.setup(self._ultrasonic_echo, GPIO.IN)

        # Send trigger pulse
        GPIO.output(self._ultrasonic_trigger, True)
        time.sleep(0.00001)
        GPIO.output(self._ultrasonic_trigger, False)

        # Wait for echo
        start_time = time.time()
        stop_time = time.time()

        while GPIO.input(self._ultrasonic_echo) == 0:
            start_time = time.time()
            if start_time - stop_time > 0.1:
                return None

        while GPIO.input(self._ultrasonic_echo) == 1:
            stop_time = time.time()
            if stop_time - start_time > 0.1:
                return None

        # Calculate distance
        elapsed = stop_time - start_time
        distance = (elapsed * 34300) / 2

        return round(distance, 1) if distance < 400 else None

    # ==================== PIR Motion Detection ====================

    async def read_pir(self) -> bool:
        """
        Read motion status from PIR sensor (non-blocking).

        Returns:
            True if motion detected
        """
        try:
            if self.simulation_mode:
                await asyncio.sleep(self._simulate_delay())

                # Random motion with low probability
                if random.random() < 0.05:
                    self._simulated_values["motion"] = not self._simulated_values["motion"]

                return self._simulated_values["motion"]
            else:
                # Run blocking GPIO call in thread pool
                return await asyncio.to_thread(self._read_pir_sync)

        except Exception as e:
            logger.error(f"PIR read error: {e}")
            return False

    def _read_pir_sync(self) -> bool:
        """Synchronous PIR read (runs in thread pool)."""
        import RPi.GPIO as GPIO
        GPIO.setup(self._pir_pin, GPIO.IN)
        return GPIO.input(self._pir_pin) == 1

    # ==================== Light Sensor (LDR) ====================

    async def read_light(self) -> Optional[int]:
        """
        Read light level from LDR (via ADC).

        Returns:
            Light level (0-1023, higher = brighter)
        """
        try:
            if self.simulation_mode:
                await asyncio.sleep(self._simulate_delay())

                # Simulate day/night cycle or random changes
                self._simulated_values["light"] = self._simulate_drift(
                    self._simulated_values["light"],
                    500 + random.uniform(-100, 100),
                    0.1
                )

                return int(self._simulate_noise(self._simulated_values["light"], 3.0))
            else:
                # Would use MCP3008 or ADS1115
                # Placeholder for actual implementation
                return 500

        except Exception as e:
            logger.error(f"Light sensor read error: {e}")
            return None

    # ==================== Soil Moisture ====================

    async def read_soil_moisture(self) -> Optional[int]:
        """
        Read soil moisture level (via ADC).

        Returns:
            Moisture level (0-1023, higher = wetter)
        """
        try:
            if self.simulation_mode:
                await asyncio.sleep(self._simulate_delay())

                # Slow drift for soil moisture
                self._simulated_values["soil_moisture"] = self._simulate_drift(
                    self._simulated_values["soil_moisture"],
                    600 + random.uniform(-50, 50),
                    0.05
                )

                return int(self._simulate_noise(
                    self._simulated_values["soil_moisture"], 2.0
                ))
            else:
                # Would use MCP3008 or ADS1115
                return 600

        except Exception as e:
            logger.error(f"Soil moisture read error: {e}")
            return None

    # ==================== All Sensors ====================

    async def read_all(self) -> Dict[str, Any]:
        """Read all available sensors."""
        results = {}

        # Read all sensors concurrently
        dht_task = asyncio.create_task(self.read_dht())
        distance_task = asyncio.create_task(self.read_ultrasonic())
        motion_task = asyncio.create_task(self.read_pir())
        light_task = asyncio.create_task(self.read_light())
        soil_task = asyncio.create_task(self.read_soil_moisture())

        dht_data = await dht_task
        if dht_data:
            results["temperature"] = dht_data["temperature"]
            results["humidity"] = dht_data["humidity"]

        results["distance"] = await distance_task
        results["motion"] = await motion_task
        results["light"] = await light_task
        results["soil_moisture"] = await soil_task

        self._update_timestamp()
        return results

    def set_simulated_values(self, **kwargs) -> None:
        """Set simulated sensor values."""
        for key, value in kwargs.items():
            if key in self._simulated_values:
                self._simulated_values[key] = value

    def _get_status_details(self) -> Dict[str, Any]:
        """Get sensor-specific status details."""
        return {
            "dht_pin": self._dht_pin,
            "dht_type": self._dht_type,
            "ultrasonic_pins": {
                "trigger": self._ultrasonic_trigger,
                "echo": self._ultrasonic_echo
            },
            "pir_pin": self._pir_pin,
            "simulated_values": self._simulated_values if self.simulation_mode else None
        }
