"""
PWM Controller
==============

Controls PWM outputs for motors, servos, and dimmers.
Supports both hardware PWM and software PWM.
"""

import asyncio
from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

from .base import BaseHardwareController, SimulationMixin
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class PWMChannel(Enum):
    """PWM channel types."""
    MOTOR = "motor"
    SERVO = "servo"
    DIMMER = "dimmer"


@dataclass
class PWMOutput:
    """Represents a PWM output configuration."""
    pin: int
    channel_type: PWMChannel
    frequency: float
    duty_cycle: float  # 0-100
    min_duty: float = 0.0
    max_duty: float = 100.0
    is_running: bool = False


class PWMController(BaseHardwareController, SimulationMixin):
    """
    Controller for PWM operations.

    Features:
    - Hardware PWM for precise timing
    - Servo motor control (0-180 degrees)
    - DC motor speed control
    - LED dimming
    """

    def __init__(self, simulation_mode: bool = False):
        super().__init__("PWM Controller", simulation_mode)
        self._outputs: Dict[int, PWMOutput] = {}
        self._pwm_instances: Dict[int, Any] = {}
        self._gpio = None

        # PWM pin configuration
        self._pwm_pin = settings.GPIO_PWM_PIN
        self._servo_pin = settings.GPIO_SERVO_PIN

    async def _do_initialize(self) -> bool:
        """Initialize PWM hardware."""
        try:
            if not self.simulation_mode:
                try:
                    import RPi.GPIO as GPIO
                    self._gpio = GPIO
                    GPIO.setmode(GPIO.BCM)
                    GPIO.setwarnings(False)
                except ImportError:
                    logger.warning("RPi.GPIO not available, falling back to simulation")
                    self.simulation_mode = True

            # Setup default PWM outputs
            await self._setup_pwm(self._pwm_pin, PWMChannel.MOTOR, 1000)  # 1kHz for motor
            await self._setup_pwm(self._servo_pin, PWMChannel.SERVO, 50)  # 50Hz for servo

            return True

        except Exception as e:
            logger.error(f"PWM initialization failed: {e}")
            return False

    async def _do_cleanup(self) -> None:
        """Clean up PWM resources."""
        for pin, pwm in self._pwm_instances.items():
            try:
                if not self.simulation_mode and pwm:
                    pwm.stop()
            except Exception as e:
                logger.error(f"Failed to stop PWM on pin {pin}: {e}")

        self._pwm_instances.clear()
        self._outputs.clear()

    async def _setup_pwm(self, pin: int, channel_type: PWMChannel, frequency: float) -> None:
        """Setup a PWM output."""
        output = PWMOutput(
            pin=pin,
            channel_type=channel_type,
            frequency=frequency,
            duty_cycle=0.0
        )

        if channel_type == PWMChannel.SERVO:
            output.min_duty = 2.5   # 0 degrees
            output.max_duty = 12.5  # 180 degrees

        self._outputs[pin] = output

        if not self.simulation_mode and self._gpio:
            self._gpio.setup(pin, self._gpio.OUT)
            pwm = self._gpio.PWM(pin, frequency)
            self._pwm_instances[pin] = pwm

        logger.debug(f"Setup PWM on pin {pin}: {channel_type.value} @ {frequency}Hz")

    # ==================== Motor Control ====================

    async def set_motor_speed(self, speed: float) -> bool:
        """
        Set motor speed.

        Args:
            speed: Speed percentage (-100 to 100, negative for reverse)

        Returns:
            True if successful
        """
        # For simplicity, we use absolute speed (0-100)
        # Direction control would require an H-bridge driver
        speed = max(0, min(100, abs(speed)))
        return await self.set_duty_cycle(self._pwm_pin, speed)

    def get_motor_speed(self) -> float:
        """Get current motor speed."""
        if self._pwm_pin in self._outputs:
            return self._outputs[self._pwm_pin].duty_cycle
        return 0.0

    # ==================== Servo Control ====================

    async def set_servo_angle(self, angle: float) -> bool:
        """
        Set servo angle.

        Args:
            angle: Angle in degrees (0-180)

        Returns:
            True if successful
        """
        angle = max(0, min(180, angle))
        output = self._outputs.get(self._servo_pin)

        if not output:
            logger.error("Servo not configured")
            return False

        # Convert angle to duty cycle
        # 0 degrees = 2.5% duty cycle
        # 180 degrees = 12.5% duty cycle
        duty_cycle = output.min_duty + (angle / 180.0) * (output.max_duty - output.min_duty)

        return await self.set_duty_cycle(self._servo_pin, duty_cycle)

    def get_servo_angle(self) -> float:
        """Get current servo angle."""
        output = self._outputs.get(self._servo_pin)
        if not output:
            return 0.0

        # Convert duty cycle back to angle
        duty_range = output.max_duty - output.min_duty
        angle = (output.duty_cycle - output.min_duty) / duty_range * 180.0
        return max(0, min(180, angle))

    # ==================== Generic PWM Control ====================

    async def set_duty_cycle(self, pin: int, duty_cycle: float) -> bool:
        """
        Set PWM duty cycle.

        Args:
            pin: GPIO pin number
            duty_cycle: Duty cycle percentage (0-100)

        Returns:
            True if successful
        """
        if pin not in self._outputs:
            logger.error(f"PWM pin {pin} not configured")
            return False

        duty_cycle = max(0, min(100, duty_cycle))

        try:
            output = self._outputs[pin]

            if self.simulation_mode:
                await asyncio.sleep(self._simulate_delay())
            else:
                pwm = self._pwm_instances.get(pin)
                if pwm:
                    if not output.is_running:
                        pwm.start(duty_cycle)
                        output.is_running = True
                    else:
                        pwm.ChangeDutyCycle(duty_cycle)

            output.duty_cycle = duty_cycle
            self._update_timestamp()
            logger.debug(f"Set PWM pin {pin} duty cycle to {duty_cycle}%")
            return True

        except Exception as e:
            logger.error(f"Failed to set PWM duty cycle: {e}")
            return False

    async def set_frequency(self, pin: int, frequency: float) -> bool:
        """
        Set PWM frequency.

        Args:
            pin: GPIO pin number
            frequency: Frequency in Hz

        Returns:
            True if successful
        """
        if pin not in self._outputs:
            return False

        try:
            if not self.simulation_mode:
                pwm = self._pwm_instances.get(pin)
                if pwm:
                    pwm.ChangeFrequency(frequency)

            self._outputs[pin].frequency = frequency
            return True

        except Exception as e:
            logger.error(f"Failed to set PWM frequency: {e}")
            return False

    async def stop_pwm(self, pin: int) -> bool:
        """Stop PWM output on a pin."""
        if pin not in self._outputs:
            return False

        try:
            if not self.simulation_mode:
                pwm = self._pwm_instances.get(pin)
                if pwm:
                    pwm.stop()

            self._outputs[pin].is_running = False
            self._outputs[pin].duty_cycle = 0
            return True

        except Exception as e:
            logger.error(f"Failed to stop PWM: {e}")
            return False

    def get_pwm_states(self) -> Dict[int, Dict[str, Any]]:
        """Get all PWM output states."""
        return {
            pin: {
                "type": output.channel_type.value,
                "frequency": output.frequency,
                "duty_cycle": output.duty_cycle,
                "is_running": output.is_running
            }
            for pin, output in self._outputs.items()
        }

    def _get_status_details(self) -> Dict[str, Any]:
        """Get PWM-specific status details."""
        return {
            "pwm_pin": self._pwm_pin,
            "servo_pin": self._servo_pin,
            "motor_speed": self.get_motor_speed(),
            "servo_angle": self.get_servo_angle(),
            "outputs": self.get_pwm_states()
        }
