"""
Hardware Control Module
=======================

Provides unified interface for Raspberry Pi hardware control.
Automatically selects between real hardware and simulation mode.

Supported Hardware:
- GPIO (LEDs, Buttons, Relays)
- PWM (Motors, Dimmers)
- I2C (Sensors, Displays)
- SPI (ADCs, DACs)
- DHT Temperature/Humidity Sensors
- NeoPixel LED Strips
"""

from .manager import HardwareManager
from .gpio_controller import GPIOController
from .pwm_controller import PWMController
from .i2c_controller import I2CController
from .spi_controller import SPIController
from .sensor_controller import SensorController
from .display_controller import DisplayController
from .neopixel_controller import NeopixelController

__all__ = [
    "HardwareManager",
    "GPIOController",
    "PWMController",
    "I2CController",
    "SPIController",
    "SensorController",
    "DisplayController",
    "NeopixelController"
]
