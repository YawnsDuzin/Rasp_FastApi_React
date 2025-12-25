"""
Display Controller
==================

Controls various displays including OLED, LCD, and 7-segment displays.
Supports I2C and SPI interfaces.
"""

import asyncio
from typing import Dict, Optional, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

from .base import BaseHardwareController, SimulationMixin
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class DisplayType(Enum):
    """Types of displays."""
    OLED_SSD1306 = "SSD1306"
    LCD_1602 = "LCD1602"
    LCD_2004 = "LCD2004"
    SEVEN_SEGMENT = "7SEG"


@dataclass
class DisplayInfo:
    """Display information."""
    display_type: DisplayType
    width: int
    height: int
    interface: str  # I2C or SPI
    address: Optional[int] = None


class DisplayController(BaseHardwareController, SimulationMixin):
    """
    Controller for display devices.

    Supported Displays:
    - SSD1306 OLED (128x64, 128x32)
    - LCD1602/2004 with I2C backpack
    - 7-Segment LED displays
    """

    def __init__(self, simulation_mode: bool = False):
        super().__init__("Display Controller", simulation_mode)
        self._oled = None
        self._lcd = None
        self._oled_address = settings.I2C_OLED_ADDRESS
        self._lcd_address = settings.I2C_LCD_ADDRESS

        # Display state for simulation
        self._oled_buffer: List[List[int]] = []
        self._lcd_lines: List[str] = ["", "", "", ""]
        self._lcd_backlight = True

        # Display dimensions
        self._oled_width = 128
        self._oled_height = 64
        self._lcd_cols = 16
        self._lcd_rows = 2

    async def _do_initialize(self) -> bool:
        """Initialize displays."""
        try:
            if not self.simulation_mode:
                # Try to initialize OLED
                await self._init_oled()
                # Try to initialize LCD
                await self._init_lcd()
            else:
                # Initialize simulation buffers
                self._oled_buffer = [[0] * self._oled_width for _ in range(self._oled_height)]

            return True

        except Exception as e:
            logger.error(f"Display initialization failed: {e}")
            return False

    async def _init_oled(self) -> bool:
        """Initialize OLED display (non-blocking)."""
        try:
            # Run blocking I2C initialization in thread pool
            return await asyncio.to_thread(self._init_oled_sync)

        except ImportError:
            logger.warning("OLED library not available")
            return False
        except Exception as e:
            logger.warning(f"OLED initialization failed: {e}")
            return False

    def _init_oled_sync(self) -> bool:
        """Synchronous OLED initialization (runs in thread pool)."""
        import board
        import busio
        import adafruit_ssd1306

        i2c = busio.I2C(board.SCL, board.SDA)
        self._oled = adafruit_ssd1306.SSD1306_I2C(
            self._oled_width, self._oled_height,
            i2c, addr=self._oled_address
        )
        self._oled.fill(0)
        self._oled.show()
        logger.info("OLED display initialized")
        return True

    async def _init_lcd(self) -> bool:
        """Initialize LCD display (non-blocking)."""
        try:
            # Run blocking I2C initialization in thread pool
            return await asyncio.to_thread(self._init_lcd_sync)

        except ImportError:
            logger.warning("LCD library not available")
            return False
        except Exception as e:
            logger.warning(f"LCD initialization failed: {e}")
            return False

    def _init_lcd_sync(self) -> bool:
        """Synchronous LCD initialization (runs in thread pool)."""
        from RPLCD.i2c import CharLCD

        self._lcd = CharLCD(
            i2c_expander='PCF8574',
            address=self._lcd_address,
            port=1,
            cols=self._lcd_cols,
            rows=self._lcd_rows
        )
        self._lcd.clear()
        logger.info("LCD display initialized")
        return True

    async def _do_cleanup(self) -> None:
        """Clean up display resources (non-blocking)."""
        try:
            if self._oled or self._lcd:
                await asyncio.to_thread(self._cleanup_displays_sync)
        except Exception as e:
            logger.error(f"Display cleanup error: {e}")

    def _cleanup_displays_sync(self) -> None:
        """Synchronous display cleanup (runs in thread pool)."""
        if self._oled:
            self._oled.fill(0)
            self._oled.show()

        if self._lcd:
            self._lcd.clear()
            self._lcd.close()

    # ==================== OLED Display ====================

    async def oled_clear(self) -> bool:
        """Clear OLED display (non-blocking)."""
        try:
            if self.simulation_mode:
                self._oled_buffer = [[0] * self._oled_width for _ in range(self._oled_height)]
            else:
                if self._oled:
                    await asyncio.to_thread(self._oled_clear_sync)
            return True
        except Exception as e:
            logger.error(f"OLED clear error: {e}")
            return False

    def _oled_clear_sync(self) -> None:
        """Synchronous OLED clear (runs in thread pool)."""
        self._oled.fill(0)
        self._oled.show()

    async def oled_text(self, text: str, x: int = 0, y: int = 0) -> bool:
        """
        Display text on OLED (non-blocking).

        Args:
            text: Text to display
            x: X position
            y: Y position

        Returns:
            True if successful
        """
        try:
            if self.simulation_mode:
                await asyncio.sleep(self._simulate_delay())
                logger.debug(f"OLED text at ({x}, {y}): {text}")
            else:
                if self._oled:
                    await asyncio.to_thread(self._oled_text_sync, text, x, y)
            return True
        except Exception as e:
            logger.error(f"OLED text error: {e}")
            return False

    def _oled_text_sync(self, text: str, x: int, y: int) -> None:
        """Synchronous OLED text (runs in thread pool)."""
        self._oled.text(text, x, y, 1)
        self._oled.show()

    async def oled_pixel(self, x: int, y: int, color: int = 1) -> bool:
        """Set a single pixel on OLED (non-blocking)."""
        try:
            if 0 <= x < self._oled_width and 0 <= y < self._oled_height:
                if self.simulation_mode:
                    self._oled_buffer[y][x] = color
                else:
                    if self._oled:
                        await asyncio.to_thread(self._oled.pixel, x, y, color)
            return True
        except Exception as e:
            logger.error(f"OLED pixel error: {e}")
            return False

    async def oled_rect(self, x: int, y: int, width: int, height: int, fill: bool = False) -> bool:
        """Draw a rectangle on OLED (non-blocking)."""
        try:
            if self.simulation_mode:
                await asyncio.sleep(self._simulate_delay())
            else:
                if self._oled:
                    await asyncio.to_thread(self._oled_rect_sync, x, y, width, height, fill)
            return True
        except Exception as e:
            logger.error(f"OLED rect error: {e}")
            return False

    def _oled_rect_sync(self, x: int, y: int, width: int, height: int, fill: bool) -> None:
        """Synchronous OLED rect (runs in thread pool)."""
        if fill:
            self._oled.fill_rect(x, y, width, height, 1)
        else:
            self._oled.rect(x, y, width, height, 1)
        self._oled.show()

    async def oled_show(self) -> bool:
        """Update OLED display (non-blocking)."""
        try:
            if not self.simulation_mode and self._oled:
                await asyncio.to_thread(self._oled.show)
            return True
        except Exception as e:
            logger.error(f"OLED show error: {e}")
            return False

    async def oled_display_dashboard(self, data: Dict[str, Any]) -> bool:
        """
        Display a simple dashboard on OLED.

        Args:
            data: Dict with keys like 'temp', 'humidity', 'status'
        """
        try:
            await self.oled_clear()

            y_offset = 0
            for key, value in data.items():
                text = f"{key}: {value}"
                await self.oled_text(text, 0, y_offset)
                y_offset += 10  # Line height

            await self.oled_show()
            return True

        except Exception as e:
            logger.error(f"OLED dashboard error: {e}")
            return False

    # ==================== LCD Display ====================

    async def lcd_clear(self) -> bool:
        """Clear LCD display (non-blocking)."""
        try:
            self._lcd_lines = ["", "", "", ""]
            if not self.simulation_mode and self._lcd:
                await asyncio.to_thread(self._lcd.clear)
            return True
        except Exception as e:
            logger.error(f"LCD clear error: {e}")
            return False

    async def lcd_write(self, text: str, row: int = 0, col: int = 0) -> bool:
        """
        Write text to LCD (non-blocking).

        Args:
            text: Text to display
            row: Row number (0-based)
            col: Column number (0-based)
        """
        try:
            if row < self._lcd_rows:
                # Update simulation state
                line = self._lcd_lines[row]
                new_line = line[:col] + text
                self._lcd_lines[row] = new_line[:self._lcd_cols]

            if self.simulation_mode:
                await asyncio.sleep(self._simulate_delay())
            else:
                if self._lcd:
                    await asyncio.to_thread(self._lcd_write_sync, text, row, col)

            return True

        except Exception as e:
            logger.error(f"LCD write error: {e}")
            return False

    def _lcd_write_sync(self, text: str, row: int, col: int) -> None:
        """Synchronous LCD write (runs in thread pool)."""
        self._lcd.cursor_pos = (row, col)
        self._lcd.write_string(text)

    async def lcd_set_backlight(self, enabled: bool) -> bool:
        """Set LCD backlight state (non-blocking)."""
        try:
            self._lcd_backlight = enabled
            if not self.simulation_mode and self._lcd:
                await asyncio.to_thread(setattr, self._lcd, 'backlight_enabled', enabled)
            return True
        except Exception as e:
            logger.error(f"LCD backlight error: {e}")
            return False

    async def lcd_display_lines(self, lines: List[str]) -> bool:
        """
        Display multiple lines on LCD.

        Args:
            lines: List of strings to display
        """
        try:
            await self.lcd_clear()
            for i, line in enumerate(lines[:self._lcd_rows]):
                await self.lcd_write(line[:self._lcd_cols], row=i)
            return True
        except Exception as e:
            logger.error(f"LCD display lines error: {e}")
            return False

    def get_lcd_content(self) -> List[str]:
        """Get current LCD content (for simulation/status)."""
        return self._lcd_lines[:self._lcd_rows]

    def get_oled_info(self) -> Dict[str, Any]:
        """Get OLED display info."""
        return {
            "width": self._oled_width,
            "height": self._oled_height,
            "address": f"0x{self._oled_address:02X}",
            "connected": self._oled is not None or self.simulation_mode
        }

    def get_lcd_info(self) -> Dict[str, Any]:
        """Get LCD display info."""
        return {
            "cols": self._lcd_cols,
            "rows": self._lcd_rows,
            "address": f"0x{self._lcd_address:02X}",
            "backlight": self._lcd_backlight,
            "content": self._lcd_lines[:self._lcd_rows],
            "connected": self._lcd is not None or self.simulation_mode
        }

    def _get_status_details(self) -> Dict[str, Any]:
        """Get display-specific status details."""
        return {
            "oled": self.get_oled_info(),
            "lcd": self.get_lcd_info()
        }
