"""
Hardware Manager
================

Central manager for all hardware controllers.
Provides unified interface and background data collection.
"""

import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from dataclasses import dataclass, field

from .gpio_controller import GPIOController
from .pwm_controller import PWMController
from .i2c_controller import I2CController
from .spi_controller import SPIController
from .sensor_controller import SensorController
from .display_controller import DisplayController
from .neopixel_controller import NeopixelController
from .base import HardwareState, HardwareStatus

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class HardwareData:
    """Combined hardware data snapshot."""
    timestamp: datetime = field(default_factory=datetime.now)

    # GPIO
    led_states: Dict[int, bool] = field(default_factory=dict)
    button_states: Dict[int, bool] = field(default_factory=dict)
    relay_states: Dict[int, bool] = field(default_factory=dict)

    # PWM
    motor_speed: float = 0.0
    servo_angle: float = 0.0

    # Sensors
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    altitude: Optional[float] = None
    distance: Optional[float] = None
    motion: bool = False
    light_level: Optional[int] = None
    soil_moisture: Optional[int] = None

    # ADC
    adc_values: Dict[int, float] = field(default_factory=dict)
    spi_adc_values: Dict[int, float] = field(default_factory=dict)

    # Display
    lcd_content: List[str] = field(default_factory=list)

    # NeoPixel
    neopixel_colors: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "gpio": {
                "leds": self.led_states,
                "buttons": self.button_states,
                "relays": self.relay_states
            },
            "pwm": {
                "motor_speed": self.motor_speed,
                "servo_angle": self.servo_angle
            },
            "sensors": {
                "temperature": self.temperature,
                "humidity": self.humidity,
                "pressure": self.pressure,
                "altitude": self.altitude,
                "distance": self.distance,
                "motion": self.motion,
                "light_level": self.light_level,
                "soil_moisture": self.soil_moisture
            },
            "adc": {
                "i2c": self.adc_values,
                "spi": self.spi_adc_values
            },
            "display": {
                "lcd_content": self.lcd_content
            },
            "neopixel": {
                "colors": self.neopixel_colors
            }
        }


class HardwareManager:
    """
    Central hardware management class.

    Manages all hardware controllers and provides:
    - Unified initialization and cleanup
    - Background data collection
    - Event callbacks for data changes
    - Hardware status monitoring
    """

    def __init__(self):
        self._simulation_mode = settings.SIMULATION_MODE
        self._initialized = False
        self._update_interval = settings.HARDWARE_UPDATE_INTERVAL
        self._update_task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable[[HardwareData], None]] = []
        self._current_data = HardwareData()
        self._running = False

        # Initialize controllers
        self.gpio = GPIOController(self._simulation_mode)
        self.pwm = PWMController(self._simulation_mode)
        self.i2c = I2CController(self._simulation_mode)
        self.spi = SPIController(self._simulation_mode)
        self.sensors = SensorController(self._simulation_mode)
        self.display = DisplayController(self._simulation_mode)
        self.neopixel = NeopixelController(self._simulation_mode)

        self._controllers = [
            self.gpio,
            self.pwm,
            self.i2c,
            self.spi,
            self.sensors,
            self.display,
            self.neopixel
        ]

    @property
    def is_simulation(self) -> bool:
        """Check if running in simulation mode."""
        return self._simulation_mode

    @property
    def is_initialized(self) -> bool:
        """Check if hardware is initialized."""
        return self._initialized

    @property
    def current_data(self) -> HardwareData:
        """Get current hardware data snapshot."""
        return self._current_data

    async def initialize(self) -> bool:
        """
        Initialize all hardware controllers.

        Returns:
            True if all controllers initialized successfully
        """
        logger.info(f"Initializing hardware manager (simulation={self._simulation_mode})")

        results = await asyncio.gather(
            *[controller.initialize() for controller in self._controllers],
            return_exceptions=True
        )

        # Check for failures
        failed = []
        for controller, result in zip(self._controllers, results):
            if isinstance(result, Exception):
                logger.error(f"{controller.name} failed: {result}")
                failed.append(controller.name)
            elif not result:
                failed.append(controller.name)

        if failed:
            logger.warning(f"Some controllers failed to initialize: {failed}")

        self._initialized = True
        return len(failed) == 0

    async def cleanup(self) -> None:
        """Clean up all hardware resources."""
        logger.info("Cleaning up hardware manager")

        await self.stop_update_loop()

        await asyncio.gather(
            *[controller.cleanup() for controller in self._controllers],
            return_exceptions=True
        )

        self._initialized = False

    async def start_update_loop(self) -> None:
        """Start the background update loop."""
        if self._running:
            return

        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("Hardware update loop started")

    async def stop_update_loop(self) -> None:
        """Stop the background update loop."""
        self._running = False

        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
            self._update_task = None

        logger.info("Hardware update loop stopped")

    async def _update_loop(self) -> None:
        """Background loop for collecting hardware data."""
        while self._running:
            try:
                await self._collect_data()
                await self._notify_callbacks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Update loop error: {e}")

            await asyncio.sleep(self._update_interval)

    async def _collect_data(self) -> None:
        """Collect data from all hardware sources."""
        data = HardwareData(timestamp=datetime.now())

        try:
            # GPIO states
            data.led_states = self.gpio.get_led_states()
            data.button_states = self.gpio.get_button_states()
            data.relay_states = self.gpio.get_relay_states()

            # PWM states
            data.motor_speed = self.pwm.get_motor_speed()
            data.servo_angle = self.pwm.get_servo_angle()

            # Sensor readings
            dht_data = await self.sensors.read_dht()
            if dht_data:
                data.temperature = dht_data.get("temperature")
                data.humidity = dht_data.get("humidity")

            bmp_data = await self.i2c.read_bmp280()
            if bmp_data:
                data.pressure = bmp_data.get("pressure")
                data.altitude = bmp_data.get("altitude")
                # Use BMP280 temperature if DHT not available
                if data.temperature is None:
                    data.temperature = bmp_data.get("temperature")

            data.distance = await self.sensors.read_ultrasonic()
            data.motion = await self.sensors.read_pir()
            data.light_level = await self.sensors.read_light()
            data.soil_moisture = await self.sensors.read_soil_moisture()

            # ADC readings
            data.adc_values = await self.i2c.read_all_adc_channels()
            data.spi_adc_values = await self.spi.read_all_mcp3008_channels()

            # Display content
            data.lcd_content = self.display.get_lcd_content()

            # NeoPixel states
            data.neopixel_colors = self.neopixel.get_led_states()

            self._current_data = data

        except Exception as e:
            logger.error(f"Data collection error: {e}")

    async def _notify_callbacks(self) -> None:
        """Notify registered callbacks with new data."""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self._current_data)
                else:
                    callback(self._current_data)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def register_callback(self, callback: Callable[[HardwareData], None]) -> None:
        """Register a callback for data updates."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[HardwareData], None]) -> None:
        """Unregister a data update callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def get_status(self) -> Dict[str, Any]:
        """Get status of all hardware controllers."""
        return {
            "initialized": self._initialized,
            "simulation_mode": self._simulation_mode,
            "update_interval": self._update_interval,
            "running": self._running,
            "controllers": {
                controller.name: controller.status.to_dict()
                for controller in self._controllers
            }
        }

    def get_all_status(self) -> List[HardwareStatus]:
        """Get status objects for all controllers."""
        return [controller.status for controller in self._controllers]

    # ==================== Convenience Methods ====================

    async def set_led(self, index: int, state: bool) -> bool:
        """Set LED state."""
        return await self.gpio.set_led(index, state)

    async def set_relay(self, index: int, state: bool) -> bool:
        """Set relay state."""
        return await self.gpio.set_relay(index, state)

    async def set_motor_speed(self, speed: float) -> bool:
        """Set motor speed."""
        return await self.pwm.set_motor_speed(speed)

    async def set_servo_angle(self, angle: float) -> bool:
        """Set servo angle."""
        return await self.pwm.set_servo_angle(angle)

    async def lcd_write(self, text: str, row: int = 0) -> bool:
        """Write text to LCD."""
        return await self.display.lcd_write(text, row)

    async def set_neopixel_color(self, index: int, color: str) -> bool:
        """Set NeoPixel LED color."""
        from .neopixel_controller import COLORS, RGBColor
        if color in COLORS:
            return await self.neopixel.set_pixel(index, COLORS[color])
        elif color.startswith("#"):
            return await self.neopixel.set_pixel(index, RGBColor.from_hex(color))
        return False

    async def start_neopixel_effect(self, effect: str) -> bool:
        """Start NeoPixel effect."""
        from .neopixel_controller import NeopixelEffect
        try:
            effect_enum = NeopixelEffect(effect)
            return await self.neopixel.start_effect(effect_enum)
        except ValueError:
            return False


# Global hardware manager instance
hardware_manager = HardwareManager()
