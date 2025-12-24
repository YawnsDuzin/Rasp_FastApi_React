"""
Application Configuration
=========================

Central configuration management using Pydantic Settings.
Supports environment variables and .env files.
"""

import os
import platform
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


def is_raspberry_pi() -> bool:
    """Detect if running on Raspberry Pi hardware."""
    try:
        with open("/proc/cpuinfo", "r") as f:
            cpuinfo = f.read()
            return "Raspberry Pi" in cpuinfo or "BCM" in cpuinfo
    except FileNotFoundError:
        return False


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    APP_NAME: str = "Raspberry Pi HMI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, description="Debug mode")

    # Server
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    RELOAD: bool = Field(default=False, description="Auto-reload on code changes")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/hmi_data.db",
        description="SQLite database URL"
    )
    DATABASE_WAL_MODE: bool = Field(default=True, description="Enable WAL mode for SQLite")

    # Hardware
    SIMULATION_MODE: bool = Field(
        default=not is_raspberry_pi(),
        description="Use simulation instead of real hardware"
    )
    HARDWARE_UPDATE_INTERVAL: float = Field(
        default=0.5,
        description="Hardware polling interval in seconds"
    )

    # WebSocket
    WS_HEARTBEAT_INTERVAL: float = Field(default=30.0, description="WebSocket heartbeat interval")
    WS_MAX_CONNECTIONS: int = Field(default=10, description="Maximum WebSocket connections")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_DIR: Path = Field(default=Path("logs"), description="Log directory")
    LOG_MAX_SIZE: int = Field(default=10 * 1024 * 1024, description="Max log file size (10MB)")
    LOG_BACKUP_COUNT: int = Field(default=5, description="Number of backup log files")

    # Data Logging
    DATA_LOG_INTERVAL: float = Field(default=5.0, description="Data logging interval in seconds")
    DATA_RETENTION_DAYS: int = Field(default=30, description="Data retention period in days")

    # GPIO Pin Configuration (BCM numbering)
    GPIO_LED_PINS: List[int] = Field(default=[17, 27, 22, 23], description="LED GPIO pins")
    GPIO_BUTTON_PINS: List[int] = Field(default=[5, 6, 13, 19], description="Button GPIO pins")
    GPIO_RELAY_PINS: List[int] = Field(default=[24, 25], description="Relay GPIO pins")
    GPIO_PWM_PIN: int = Field(default=18, description="PWM output pin")
    GPIO_SERVO_PIN: int = Field(default=12, description="Servo motor pin")

    # I2C Configuration
    I2C_BUS: int = Field(default=1, description="I2C bus number")
    I2C_LCD_ADDRESS: int = Field(default=0x27, description="I2C LCD address")
    I2C_OLED_ADDRESS: int = Field(default=0x3C, description="I2C OLED address")
    I2C_BMP280_ADDRESS: int = Field(default=0x76, description="BMP280 sensor address")
    I2C_ADS1115_ADDRESS: int = Field(default=0x48, description="ADS1115 ADC address")

    # SPI Configuration
    SPI_BUS: int = Field(default=0, description="SPI bus number")
    SPI_DEVICE: int = Field(default=0, description="SPI device number")
    SPI_MAX_SPEED: int = Field(default=1000000, description="SPI max speed in Hz")

    # DHT Sensor
    DHT_PIN: int = Field(default=4, description="DHT sensor data pin")
    DHT_TYPE: str = Field(default="DHT22", description="DHT sensor type (DHT11 or DHT22)")

    # Neopixel LED Strip
    NEOPIXEL_PIN: int = Field(default=21, description="Neopixel data pin")
    NEOPIXEL_COUNT: int = Field(default=8, description="Number of Neopixel LEDs")

    # Static Files
    STATIC_DIR: Path = Field(default=Path("static"), description="Static files directory")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @property
    def is_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi."""
        return is_raspberry_pi()

    @property
    def platform_info(self) -> dict:
        """Get platform information."""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "is_raspberry_pi": self.is_raspberry_pi,
            "simulation_mode": self.SIMULATION_MODE
        }


# Global settings instance
settings = Settings()
