"""
GPIO Controller
===============

Controls GPIO pins for LEDs, buttons, and relays.
Supports both real hardware and simulation mode.
"""

import asyncio
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

from .base import BaseHardwareController, SimulationMixin, HardwareState
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class PinMode(Enum):
    """GPIO pin modes."""
    INPUT = "input"
    OUTPUT = "output"
    INPUT_PULLUP = "input_pullup"
    INPUT_PULLDOWN = "input_pulldown"


class PinState(Enum):
    """GPIO pin states."""
    LOW = 0
    HIGH = 1


@dataclass
class GPIOPin:
    """Represents a GPIO pin configuration."""
    pin: int
    mode: PinMode
    name: str
    state: PinState = PinState.LOW
    is_inverted: bool = False


class GPIOController(BaseHardwareController, SimulationMixin):
    """
    Controller for GPIO operations.

    Features:
    - LED control
    - Button input with callbacks
    - Relay control
    - Event-based button detection
    """

    def __init__(self, simulation_mode: bool = False):
        super().__init__("GPIO Controller", simulation_mode)
        self._pins: Dict[int, GPIOPin] = {}
        self._button_callbacks: Dict[int, List[Callable]] = {}
        self._gpio = None
        self._button_task: Optional[asyncio.Task] = None

        # LED pins
        self._led_pins: List[int] = settings.GPIO_LED_PINS
        # Button pins
        self._button_pins: List[int] = settings.GPIO_BUTTON_PINS
        # Relay pins
        self._relay_pins: List[int] = settings.GPIO_RELAY_PINS

    async def _do_initialize(self) -> bool:
        """Initialize GPIO hardware."""
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

            # Setup LED pins
            for i, pin in enumerate(self._led_pins):
                await self._setup_pin(pin, PinMode.OUTPUT, f"LED_{i+1}")

            # Setup button pins
            for i, pin in enumerate(self._button_pins):
                await self._setup_pin(pin, PinMode.INPUT_PULLUP, f"Button_{i+1}")

            # Setup relay pins
            for i, pin in enumerate(self._relay_pins):
                await self._setup_pin(pin, PinMode.OUTPUT, f"Relay_{i+1}")

            # Start button monitoring
            if not self.simulation_mode:
                self._setup_button_interrupts()
            else:
                self._button_task = asyncio.create_task(self._simulate_button_polling())

            return True

        except Exception as e:
            logger.error(f"GPIO initialization failed: {e}")
            return False

    async def _do_cleanup(self) -> None:
        """Clean up GPIO resources."""
        if self._button_task:
            self._button_task.cancel()
            try:
                await self._button_task
            except asyncio.CancelledError:
                pass

        if self._gpio and not self.simulation_mode:
            self._gpio.cleanup()

        self._pins.clear()
        self._button_callbacks.clear()

    async def _setup_pin(self, pin: int, mode: PinMode, name: str) -> None:
        """Setup a GPIO pin."""
        gpio_pin = GPIOPin(pin=pin, mode=mode, name=name)
        self._pins[pin] = gpio_pin

        if not self.simulation_mode and self._gpio:
            if mode == PinMode.OUTPUT:
                self._gpio.setup(pin, self._gpio.OUT, initial=self._gpio.LOW)
            elif mode == PinMode.INPUT_PULLUP:
                self._gpio.setup(pin, self._gpio.IN, pull_up_down=self._gpio.PUD_UP)
            elif mode == PinMode.INPUT_PULLDOWN:
                self._gpio.setup(pin, self._gpio.IN, pull_up_down=self._gpio.PUD_DOWN)
            else:
                self._gpio.setup(pin, self._gpio.IN)

        logger.debug(f"Setup GPIO pin {pin} as {mode.value} ({name})")

    def _setup_button_interrupts(self) -> None:
        """Setup hardware button interrupts."""
        if not self._gpio:
            return

        for pin in self._button_pins:
            try:
                self._gpio.add_event_detect(
                    pin,
                    self._gpio.FALLING,
                    callback=self._on_button_press,
                    bouncetime=200
                )
            except Exception as e:
                logger.error(f"Failed to setup interrupt for pin {pin}: {e}")

    def _on_button_press(self, pin: int) -> None:
        """Handle button press interrupt."""
        if pin in self._button_callbacks:
            for callback in self._button_callbacks[pin]:
                try:
                    callback(pin)
                except Exception as e:
                    logger.error(f"Button callback error: {e}")

        self._update_timestamp()
        logger.debug(f"Button press detected on pin {pin}")

    async def _simulate_button_polling(self) -> None:
        """Simulate button polling in simulation mode."""
        while True:
            await asyncio.sleep(0.1)
            # In simulation, buttons are triggered programmatically

    # ==================== LED Control ====================

    async def set_led(self, index: int, state: bool) -> bool:
        """
        Set LED state.

        Args:
            index: LED index (0-based)
            state: True for on, False for off

        Returns:
            True if successful
        """
        if index < 0 or index >= len(self._led_pins):
            logger.error(f"Invalid LED index: {index}")
            return False

        pin = self._led_pins[index]
        return await self.write_pin(pin, PinState.HIGH if state else PinState.LOW)

    async def set_all_leds(self, state: bool) -> bool:
        """Set all LEDs to the same state."""
        results = await asyncio.gather(
            *[self.set_led(i, state) for i in range(len(self._led_pins))]
        )
        return all(results)

    async def toggle_led(self, index: int) -> bool:
        """Toggle LED state."""
        if index < 0 or index >= len(self._led_pins):
            return False

        pin = self._led_pins[index]
        current_state = self._pins[pin].state
        new_state = PinState.LOW if current_state == PinState.HIGH else PinState.HIGH
        return await self.write_pin(pin, new_state)

    def get_led_states(self) -> Dict[int, bool]:
        """Get all LED states."""
        return {
            i: self._pins[pin].state == PinState.HIGH
            for i, pin in enumerate(self._led_pins)
            if pin in self._pins
        }

    # ==================== Relay Control ====================

    async def set_relay(self, index: int, state: bool) -> bool:
        """
        Set relay state.

        Args:
            index: Relay index (0-based)
            state: True for on, False for off

        Returns:
            True if successful
        """
        if index < 0 or index >= len(self._relay_pins):
            logger.error(f"Invalid relay index: {index}")
            return False

        pin = self._relay_pins[index]
        return await self.write_pin(pin, PinState.HIGH if state else PinState.LOW)

    def get_relay_states(self) -> Dict[int, bool]:
        """Get all relay states."""
        return {
            i: self._pins[pin].state == PinState.HIGH
            for i, pin in enumerate(self._relay_pins)
            if pin in self._pins
        }

    # ==================== Button Control ====================

    def register_button_callback(self, index: int, callback: Callable[[int], None]) -> None:
        """Register a callback for button press."""
        if index < 0 or index >= len(self._button_pins):
            return

        pin = self._button_pins[index]
        if pin not in self._button_callbacks:
            self._button_callbacks[pin] = []
        self._button_callbacks[pin].append(callback)

    async def read_button(self, index: int) -> bool:
        """
        Read button state.

        Args:
            index: Button index (0-based)

        Returns:
            True if pressed (considering pull-up, so LOW means pressed)
        """
        if index < 0 or index >= len(self._button_pins):
            return False

        pin = self._button_pins[index]
        state = await self.read_pin(pin)
        # With pull-up, pressed = LOW
        return state == PinState.LOW

    def get_button_states(self) -> Dict[int, bool]:
        """Get all button states."""
        result = {}
        for i, pin in enumerate(self._button_pins):
            if pin in self._pins:
                # Simulation always returns False unless triggered
                result[i] = self._pins[pin].state == PinState.LOW
        return result

    async def simulate_button_press(self, index: int) -> None:
        """Simulate a button press (for testing)."""
        if not self.simulation_mode:
            return

        if index < 0 or index >= len(self._button_pins):
            return

        pin = self._button_pins[index]
        self._pins[pin].state = PinState.LOW
        self._on_button_press(pin)

        await asyncio.sleep(0.1)
        self._pins[pin].state = PinState.HIGH

    # ==================== Low-level GPIO ====================

    async def write_pin(self, pin: int, state: PinState) -> bool:
        """Write state to a GPIO pin."""
        if pin not in self._pins:
            logger.error(f"Pin {pin} not configured")
            return False

        try:
            if self.simulation_mode:
                await asyncio.sleep(self._simulate_delay())
            else:
                self._gpio.output(pin, state.value)

            self._pins[pin].state = state
            self._update_timestamp()
            logger.debug(f"Set pin {pin} to {state.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to write pin {pin}: {e}")
            return False

    async def read_pin(self, pin: int) -> PinState:
        """Read state from a GPIO pin."""
        if pin not in self._pins:
            logger.error(f"Pin {pin} not configured")
            return PinState.LOW

        try:
            if self.simulation_mode:
                await asyncio.sleep(self._simulate_delay())
                return self._pins[pin].state
            else:
                value = self._gpio.input(pin)
                state = PinState.HIGH if value else PinState.LOW
                self._pins[pin].state = state
                return state

        except Exception as e:
            logger.error(f"Failed to read pin {pin}: {e}")
            return PinState.LOW

    def _get_status_details(self) -> Dict[str, Any]:
        """Get GPIO-specific status details."""
        return {
            "led_pins": self._led_pins,
            "button_pins": self._button_pins,
            "relay_pins": self._relay_pins,
            "led_states": self.get_led_states(),
            "relay_states": self.get_relay_states(),
            "button_states": self.get_button_states(),
            "total_pins": len(self._pins)
        }
