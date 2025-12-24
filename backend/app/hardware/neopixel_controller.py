"""
NeoPixel Controller
===================

Controls WS2812B (NeoPixel) addressable LED strips.
Supports various effects and animations.
"""

import asyncio
import math
from typing import Dict, Optional, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

from .base import BaseHardwareController, SimulationMixin
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class NeopixelEffect(Enum):
    """Available LED effects."""
    SOLID = "solid"
    RAINBOW = "rainbow"
    BREATHING = "breathing"
    CHASE = "chase"
    SPARKLE = "sparkle"
    WAVE = "wave"
    FIRE = "fire"


@dataclass
class RGBColor:
    """RGB color representation."""
    r: int
    g: int
    b: int

    def __post_init__(self):
        self.r = max(0, min(255, self.r))
        self.g = max(0, min(255, self.g))
        self.b = max(0, min(255, self.b))

    def to_tuple(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def to_hex(self) -> str:
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"

    @classmethod
    def from_hex(cls, hex_color: str) -> "RGBColor":
        hex_color = hex_color.lstrip('#')
        return cls(
            r=int(hex_color[0:2], 16),
            g=int(hex_color[2:4], 16),
            b=int(hex_color[4:6], 16)
        )


# Predefined colors
COLORS = {
    "red": RGBColor(255, 0, 0),
    "green": RGBColor(0, 255, 0),
    "blue": RGBColor(0, 0, 255),
    "white": RGBColor(255, 255, 255),
    "yellow": RGBColor(255, 255, 0),
    "cyan": RGBColor(0, 255, 255),
    "magenta": RGBColor(255, 0, 255),
    "orange": RGBColor(255, 165, 0),
    "purple": RGBColor(128, 0, 128),
    "pink": RGBColor(255, 192, 203),
    "off": RGBColor(0, 0, 0)
}


class NeopixelController(BaseHardwareController, SimulationMixin):
    """
    Controller for WS2812B NeoPixel LED strips.

    Features:
    - Individual LED control
    - Color effects and animations
    - Brightness control
    - Effect scheduling
    """

    def __init__(self, simulation_mode: bool = False):
        super().__init__("NeoPixel Controller", simulation_mode)
        self._pin = settings.NEOPIXEL_PIN
        self._num_leds = settings.NEOPIXEL_COUNT
        self._pixels = None
        self._brightness = 0.5
        self._current_effect = NeopixelEffect.SOLID
        self._effect_task: Optional[asyncio.Task] = None
        self._effect_running = False

        # LED state for simulation
        self._led_colors: List[RGBColor] = [RGBColor(0, 0, 0) for _ in range(self._num_leds)]

    async def _do_initialize(self) -> bool:
        """Initialize NeoPixel strip."""
        try:
            if not self.simulation_mode:
                try:
                    import board
                    import neopixel

                    pin = getattr(board, f"D{self._pin}")
                    self._pixels = neopixel.NeoPixel(
                        pin,
                        self._num_leds,
                        brightness=self._brightness,
                        auto_write=False,
                        pixel_order=neopixel.GRB
                    )
                    self._pixels.fill((0, 0, 0))
                    self._pixels.show()

                except ImportError:
                    logger.warning("NeoPixel library not available, falling back to simulation")
                    self.simulation_mode = True
                except Exception as e:
                    logger.warning(f"NeoPixel init failed: {e}")
                    self.simulation_mode = True

            return True

        except Exception as e:
            logger.error(f"NeoPixel initialization failed: {e}")
            return False

    async def _do_cleanup(self) -> None:
        """Clean up NeoPixel resources."""
        await self.stop_effect()
        await self.clear()

        if self._pixels:
            self._pixels.deinit()
            self._pixels = None

    # ==================== Basic Control ====================

    async def set_pixel(self, index: int, color: RGBColor) -> bool:
        """
        Set a single pixel color.

        Args:
            index: Pixel index (0-based)
            color: RGB color
        """
        if index < 0 or index >= self._num_leds:
            return False

        try:
            self._led_colors[index] = color

            if not self.simulation_mode and self._pixels:
                self._pixels[index] = color.to_tuple()
                self._pixels.show()

            return True

        except Exception as e:
            logger.error(f"Set pixel error: {e}")
            return False

    async def set_all(self, color: RGBColor) -> bool:
        """Set all pixels to the same color."""
        try:
            for i in range(self._num_leds):
                self._led_colors[i] = color

            if not self.simulation_mode and self._pixels:
                self._pixels.fill(color.to_tuple())
                self._pixels.show()

            return True

        except Exception as e:
            logger.error(f"Set all pixels error: {e}")
            return False

    async def clear(self) -> bool:
        """Turn off all pixels."""
        return await self.set_all(COLORS["off"])

    async def set_brightness(self, brightness: float) -> bool:
        """
        Set overall brightness.

        Args:
            brightness: Brightness level (0.0-1.0)
        """
        self._brightness = max(0.0, min(1.0, brightness))

        if not self.simulation_mode and self._pixels:
            self._pixels.brightness = self._brightness

        return True

    async def show(self) -> bool:
        """Update the LED strip display."""
        try:
            if not self.simulation_mode and self._pixels:
                self._pixels.show()
            return True
        except Exception as e:
            logger.error(f"Show error: {e}")
            return False

    # ==================== Effects ====================

    async def start_effect(self, effect: NeopixelEffect, **kwargs) -> bool:
        """
        Start an LED effect.

        Args:
            effect: Effect type
            **kwargs: Effect-specific parameters
        """
        await self.stop_effect()

        self._current_effect = effect
        self._effect_running = True

        if effect == NeopixelEffect.RAINBOW:
            self._effect_task = asyncio.create_task(self._rainbow_effect(**kwargs))
        elif effect == NeopixelEffect.BREATHING:
            self._effect_task = asyncio.create_task(self._breathing_effect(**kwargs))
        elif effect == NeopixelEffect.CHASE:
            self._effect_task = asyncio.create_task(self._chase_effect(**kwargs))
        elif effect == NeopixelEffect.SPARKLE:
            self._effect_task = asyncio.create_task(self._sparkle_effect(**kwargs))
        elif effect == NeopixelEffect.WAVE:
            self._effect_task = asyncio.create_task(self._wave_effect(**kwargs))
        elif effect == NeopixelEffect.FIRE:
            self._effect_task = asyncio.create_task(self._fire_effect(**kwargs))
        else:
            self._effect_running = False
            return False

        return True

    async def stop_effect(self) -> bool:
        """Stop the current effect."""
        self._effect_running = False

        if self._effect_task:
            self._effect_task.cancel()
            try:
                await self._effect_task
            except asyncio.CancelledError:
                pass
            self._effect_task = None

        return True

    async def _rainbow_effect(self, speed: float = 0.05) -> None:
        """Rainbow cycling effect."""
        offset = 0
        while self._effect_running:
            for i in range(self._num_leds):
                hue = (i + offset) % 256
                color = self._wheel(hue)
                self._led_colors[i] = RGBColor(*color)

                if not self.simulation_mode and self._pixels:
                    self._pixels[i] = color

            await self.show()
            offset = (offset + 1) % 256
            await asyncio.sleep(speed)

    async def _breathing_effect(self, color: RGBColor = None, speed: float = 0.02) -> None:
        """Breathing (fade in/out) effect."""
        color = color or COLORS["blue"]
        step = 0
        while self._effect_running:
            # Calculate brightness using sine wave
            brightness = (math.sin(step) + 1) / 2
            adjusted = RGBColor(
                int(color.r * brightness),
                int(color.g * brightness),
                int(color.b * brightness)
            )
            await self.set_all(adjusted)
            step += 0.05
            await asyncio.sleep(speed)

    async def _chase_effect(self, color: RGBColor = None, speed: float = 0.1) -> None:
        """Theater chase effect."""
        color = color or COLORS["white"]
        while self._effect_running:
            for offset in range(3):
                for i in range(self._num_leds):
                    if (i + offset) % 3 == 0:
                        self._led_colors[i] = color
                    else:
                        self._led_colors[i] = COLORS["off"]

                    if not self.simulation_mode and self._pixels:
                        self._pixels[i] = self._led_colors[i].to_tuple()

                await self.show()
                await asyncio.sleep(speed)

    async def _sparkle_effect(self, color: RGBColor = None, speed: float = 0.1) -> None:
        """Random sparkle effect."""
        import random
        color = color or COLORS["white"]

        while self._effect_running:
            await self.clear()
            pixel = random.randint(0, self._num_leds - 1)
            await self.set_pixel(pixel, color)
            await asyncio.sleep(speed)

    async def _wave_effect(self, speed: float = 0.05) -> None:
        """Color wave effect."""
        offset = 0
        while self._effect_running:
            for i in range(self._num_leds):
                brightness = (math.sin(offset + i * 0.5) + 1) / 2
                color = RGBColor(
                    int(255 * brightness),
                    int(100 * (1 - brightness)),
                    int(200 * brightness)
                )
                self._led_colors[i] = color

                if not self.simulation_mode and self._pixels:
                    self._pixels[i] = color.to_tuple()

            await self.show()
            offset += 0.2
            await asyncio.sleep(speed)

    async def _fire_effect(self, speed: float = 0.05) -> None:
        """Fire/flame effect."""
        import random

        while self._effect_running:
            for i in range(self._num_leds):
                flicker = random.randint(0, 100)
                r = 255
                g = max(0, 100 - flicker)
                b = 0
                color = RGBColor(r, g, b)
                self._led_colors[i] = color

                if not self.simulation_mode and self._pixels:
                    self._pixels[i] = color.to_tuple()

            await self.show()
            await asyncio.sleep(speed)

    def _wheel(self, pos: int) -> Tuple[int, int, int]:
        """
        Generate rainbow colors across 0-255 positions.
        """
        if pos < 85:
            return (255 - pos * 3, pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return (0, 255 - pos * 3, pos * 3)
        else:
            pos -= 170
            return (pos * 3, 0, 255 - pos * 3)

    def get_led_states(self) -> List[Dict[str, Any]]:
        """Get all LED states."""
        return [
            {
                "index": i,
                "color": color.to_hex(),
                "rgb": color.to_tuple()
            }
            for i, color in enumerate(self._led_colors)
        ]

    def _get_status_details(self) -> Dict[str, Any]:
        """Get NeoPixel-specific status details."""
        return {
            "pin": self._pin,
            "num_leds": self._num_leds,
            "brightness": self._brightness,
            "current_effect": self._current_effect.value if self._current_effect else None,
            "effect_running": self._effect_running,
            "led_states": self.get_led_states()
        }
