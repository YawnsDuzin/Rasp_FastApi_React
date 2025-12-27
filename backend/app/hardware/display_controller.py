"""
Display Controller (디스플레이 컨트롤러)
========================================

[한국어 설명]
OLED, LCD 등 다양한 디스플레이 장치를 제어하는 컨트롤러입니다.
I2C 인터페이스를 통해 디스플레이와 통신합니다.

지원 디스플레이:
1. SSD1306 OLED (128x64 또는 128x32 픽셀)
   - 자체 발광 (백라이트 불필요)
   - 고대비, 저전력
   - 그래픽/텍스트 표시 가능

2. LCD1602/2004 (16x2 또는 20x4 문자)
   - 문자 전용 디스플레이
   - I2C 백팩(PCF8574) 사용
   - 백라이트 ON/OFF 제어 가능

사용 사례:
- 온도/습도 표시
- 시스템 상태 모니터링
- IP 주소 표시
- 간단한 메뉴 UI

[English Description]
Controller for display devices including OLED and LCD displays.
Supports text and graphics display through I2C interface.
"""

# ============================================================================
# 라이브러리 임포트 (Import Libraries)
# ============================================================================

# asyncio: 비동기 I/O 처리
import asyncio

# typing: 타입 힌트용 모듈
from typing import Dict, Optional, Any, List, Tuple

# dataclass: 데이터 저장 클래스를 간편하게 정의
from dataclasses import dataclass

# Enum: 열거형 상수 정의
from enum import Enum

# base: 하드웨어 컨트롤러 기본 클래스
from .base import BaseHardwareController, SimulationMixin

# settings: 애플리케이션 설정
from app.core.config import settings

# get_logger: 로깅 함수
from app.core.logging_config import get_logger

# 이 모듈 전용 로거 생성
logger = get_logger(__name__)


# ============================================================================
# 열거형 상수 (Enumerations)
# ============================================================================

class DisplayType(Enum):
    """
    디스플레이 종류 열거형 (Types of displays)

    [한국어 설명]
    지원하는 디스플레이 타입을 정의합니다.
    Enum을 사용하면 오타를 방지하고 자동완성이 가능합니다.
    """
    OLED_SSD1306 = "SSD1306"     # OLED 디스플레이 (128x64 또는 128x32)
    LCD_1602 = "LCD1602"         # 16자 2줄 LCD
    LCD_2004 = "LCD2004"         # 20자 4줄 LCD
    SEVEN_SEGMENT = "7SEG"       # 7세그먼트 LED (숫자 표시용)


# ============================================================================
# 데이터 클래스 (Data Classes)
# ============================================================================

@dataclass
class DisplayInfo:
    """
    디스플레이 정보를 저장하는 데이터 클래스 (Display information)

    [한국어 설명]
    각 디스플레이의 하드웨어 사양을 저장합니다.

    속성 설명:
    - display_type: 디스플레이 종류 (Enum)
    - width: 가로 픽셀/문자 수
    - height: 세로 픽셀/줄 수
    - interface: 통신 인터페이스 ("I2C" 또는 "SPI")
    - address: I2C 주소 (I2C 인터페이스인 경우)
    """
    display_type: DisplayType       # 디스플레이 종류
    width: int                      # 가로 크기
    height: int                     # 세로 크기
    interface: str                  # 통신 방식 ("I2C" or "SPI")
    address: Optional[int] = None   # I2C 주소 (옵션)


# ============================================================================
# 디스플레이 컨트롤러 클래스 (Display Controller Class)
# ============================================================================

class DisplayController(BaseHardwareController, SimulationMixin):
    """
    디스플레이 장치 컨트롤러 (Controller for display devices)

    [한국어 설명]
    OLED와 LCD 디스플레이를 제어합니다.
    각 디스플레이 타입에 맞는 라이브러리를 사용합니다.

    OLED (SSD1306):
    - 라이브러리: adafruit-circuitpython-ssd1306
    - 픽셀 단위 그래픽 가능
    - 텍스트, 도형, 이미지 표시

    LCD (1602/2004):
    - 라이브러리: RPLCD
    - 문자 단위 표시
    - 백라이트 제어 가능

    Supported Displays:
    - SSD1306 OLED (128x64, 128x32)
    - LCD1602/2004 with I2C backpack
    - 7-Segment LED displays
    """

    def __init__(self, simulation_mode: bool = False):
        """
        디스플레이 컨트롤러 초기화 (Initialize Display Controller)

        [한국어 설명]
        두 종류의 디스플레이(OLED, LCD)를 위한 초기값을 설정합니다.
        """
        # 부모 클래스 초기화
        super().__init__("Display Controller", simulation_mode)

        # ==================== OLED 관련 변수 ====================
        # OLED 장치 객체 (adafruit_ssd1306 인스턴스)
        self._oled = None

        # OLED I2C 주소 (보통 0x3C)
        self._oled_address = settings.I2C_OLED_ADDRESS

        # ==================== LCD 관련 변수 ====================
        # LCD 장치 객체 (RPLCD CharLCD 인스턴스)
        self._lcd = None

        # LCD I2C 주소 (보통 0x27)
        self._lcd_address = settings.I2C_LCD_ADDRESS

        # ==================== 시뮬레이션용 변수 ====================
        # OLED 픽셀 버퍼 (2D 리스트)
        # [한국어 설명]
        # 128x64 픽셀을 2차원 배열로 표현
        # 각 값은 0(꺼짐) 또는 1(켜짐)
        self._oled_buffer: List[List[int]] = []

        # LCD 줄 내용 (최대 4줄)
        self._lcd_lines: List[str] = ["", "", "", ""]

        # LCD 백라이트 상태
        self._lcd_backlight = True

        # ==================== 디스플레이 크기 설정 ====================
        # OLED 크기 (픽셀)
        self._oled_width = 128   # 가로 128픽셀
        self._oled_height = 64   # 세로 64픽셀

        # LCD 크기 (문자)
        self._lcd_cols = 16      # 가로 16문자
        self._lcd_rows = 2       # 세로 2줄

    # ========================================================================
    # 초기화 및 정리 메서드 (Initialization and Cleanup Methods)
    # ========================================================================

    async def _do_initialize(self) -> bool:
        """
        디스플레이 초기화 (Initialize displays)

        [한국어 설명]
        OLED와 LCD를 순차적으로 초기화합니다.
        각 디스플레이 초기화 실패는 독립적으로 처리됩니다.
        (하나가 실패해도 다른 것은 동작)

        Returns:
            bool: 초기화 성공 여부
        """
        try:
            if not self.simulation_mode:
                # OLED 초기화 시도
                await self._init_oled()

                # LCD 초기화 시도
                await self._init_lcd()
            else:
                # 시뮬레이션 모드: 버퍼만 초기화
                # [한국어 설명]
                # 리스트 컴프리헨션으로 2D 배열 생성
                # [[0]*128 for _ in range(64)] → 64행 × 128열의 0으로 채워진 배열
                self._oled_buffer = [[0] * self._oled_width for _ in range(self._oled_height)]

            return True

        except Exception as e:
            logger.error(f"Display initialization failed: {e}")
            return False

    async def _init_oled(self) -> bool:
        """
        OLED 디스플레이 초기화 (비동기)
        Initialize OLED display (non-blocking)

        [한국어 설명]
        SSD1306 OLED를 I2C를 통해 초기화합니다.
        블로킹 작업이므로 스레드 풀에서 실행합니다.

        라이브러리 설치:
        pip install adafruit-circuitpython-ssd1306

        Returns:
            bool: 초기화 성공 여부
        """
        try:
            # 블로킹 초기화를 스레드 풀에서 실행
            return await asyncio.to_thread(self._init_oled_sync)

        except ImportError:
            logger.warning("OLED library not available")
            return False
        except Exception as e:
            logger.warning(f"OLED initialization failed: {e}")
            return False

    def _init_oled_sync(self) -> bool:
        """
        동기 방식 OLED 초기화 (스레드 풀에서 실행됨)
        Synchronous OLED initialization (runs in thread pool)

        [한국어 설명]
        Adafruit CircuitPython 라이브러리 사용.

        board: 라즈베리 파이 보드 핀 정보
        busio: I2C/SPI 버스 인터페이스
        adafruit_ssd1306: SSD1306 OLED 드라이버
        """
        import board
        import busio
        import adafruit_ssd1306

        # I2C 버스 생성
        i2c = busio.I2C(board.SCL, board.SDA)

        # SSD1306 OLED 객체 생성
        # [한국어 설명]
        # SSD1306_I2C(width, height, i2c, addr=address)
        # - width, height: 디스플레이 크기
        # - i2c: I2C 버스 객체
        # - addr: I2C 주소
        self._oled = adafruit_ssd1306.SSD1306_I2C(
            self._oled_width, self._oled_height,
            i2c, addr=self._oled_address
        )

        # 화면 초기화 (모두 꺼짐)
        self._oled.fill(0)    # 모든 픽셀을 0으로
        self._oled.show()     # 버퍼를 화면에 반영

        logger.info("OLED display initialized")
        return True

    async def _init_lcd(self) -> bool:
        """
        LCD 디스플레이 초기화 (비동기)
        Initialize LCD display (non-blocking)

        [한국어 설명]
        I2C 백팩이 달린 HD44780 호환 LCD를 초기화합니다.
        PCF8574 I/O 확장기를 통해 I2C 통신합니다.

        라이브러리 설치:
        pip install RPLCD

        Returns:
            bool: 초기화 성공 여부
        """
        try:
            return await asyncio.to_thread(self._init_lcd_sync)

        except ImportError:
            logger.warning("LCD library not available")
            return False
        except Exception as e:
            logger.warning(f"LCD initialization failed: {e}")
            return False

    def _init_lcd_sync(self) -> bool:
        """
        동기 방식 LCD 초기화 (스레드 풀에서 실행됨)
        Synchronous LCD initialization (runs in thread pool)

        [한국어 설명]
        RPLCD 라이브러리의 CharLCD 클래스 사용.

        CharLCD 파라미터:
        - i2c_expander: I/O 확장기 종류 ('PCF8574' 또는 'MCP23008')
        - address: I2C 주소
        - port: I2C 포트 번호 (라즈베리 파이는 1)
        - cols: 가로 문자 수
        - rows: 세로 줄 수
        """
        from RPLCD.i2c import CharLCD

        # LCD 객체 생성
        self._lcd = CharLCD(
            i2c_expander='PCF8574',    # PCF8574 I/O 확장기 사용
            address=self._lcd_address,  # I2C 주소 (보통 0x27)
            port=1,                     # I2C 포트 1 (/dev/i2c-1)
            cols=self._lcd_cols,        # 16자
            rows=self._lcd_rows         # 2줄
        )

        # 화면 초기화
        self._lcd.clear()

        logger.info("LCD display initialized")
        return True

    async def _do_cleanup(self) -> None:
        """
        디스플레이 리소스 정리 (비동기)
        Clean up display resources (non-blocking)

        [한국어 설명]
        디스플레이를 초기 상태로 되돌리고 리소스를 해제합니다.
        """
        try:
            if self._oled or self._lcd:
                await asyncio.to_thread(self._cleanup_displays_sync)
        except Exception as e:
            logger.error(f"Display cleanup error: {e}")

    def _cleanup_displays_sync(self) -> None:
        """
        동기 방식 디스플레이 정리 (스레드 풀에서 실행됨)
        Synchronous display cleanup (runs in thread pool)
        """
        # OLED 정리: 화면 끄기
        if self._oled:
            self._oled.fill(0)
            self._oled.show()

        # LCD 정리: 화면 지우고 닫기
        if self._lcd:
            self._lcd.clear()
            self._lcd.close()

    # ========================================================================
    # OLED 디스플레이 메서드 (OLED Display Methods)
    # ========================================================================

    async def oled_clear(self) -> bool:
        """
        OLED 화면 지우기 (비동기)
        Clear OLED display (non-blocking)

        [한국어 설명]
        모든 픽셀을 끄고 화면을 갱신합니다.

        Returns:
            bool: 성공 여부
        """
        try:
            if self.simulation_mode:
                # 시뮬레이션: 버퍼 초기화
                self._oled_buffer = [[0] * self._oled_width for _ in range(self._oled_height)]
            else:
                if self._oled:
                    await asyncio.to_thread(self._oled_clear_sync)
            return True
        except Exception as e:
            logger.error(f"OLED clear error: {e}")
            return False

    def _oled_clear_sync(self) -> None:
        """동기 방식 OLED 지우기 (Synchronous OLED clear)"""
        self._oled.fill(0)
        self._oled.show()

    async def oled_text(self, text: str, x: int = 0, y: int = 0) -> bool:
        """
        OLED에 텍스트 표시 (비동기)
        Display text on OLED (non-blocking)

        [한국어 설명]
        지정된 좌표에 텍스트를 표시합니다.
        폰트는 기본 5x8 픽셀 폰트가 사용됩니다.

        Args:
            text: 표시할 텍스트
            x: X 좌표 (픽셀)
            y: Y 좌표 (픽셀)

        Returns:
            bool: 성공 여부
        """
        try:
            if self.simulation_mode:
                # 시뮬레이션: 지연 추가 및 로그 출력
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
        """
        동기 방식 OLED 텍스트 표시
        Synchronous OLED text (runs in thread pool)

        [한국어 설명]
        self._oled.text(문자열, x, y, 색상)
        - 색상 1: 켜짐 (흰색)
        - 색상 0: 꺼짐 (검은색)
        """
        self._oled.text(text, x, y, 1)  # 1 = 흰색
        self._oled.show()

    async def oled_pixel(self, x: int, y: int, color: int = 1) -> bool:
        """
        OLED에 단일 픽셀 설정 (비동기)
        Set a single pixel on OLED (non-blocking)

        [한국어 설명]
        특정 좌표의 픽셀을 켜거나 끕니다.

        Args:
            x: X 좌표 (0 ~ width-1)
            y: Y 좌표 (0 ~ height-1)
            color: 0(꺼짐) 또는 1(켜짐)

        Returns:
            bool: 성공 여부
        """
        try:
            # 좌표 범위 검증
            if 0 <= x < self._oled_width and 0 <= y < self._oled_height:
                if self.simulation_mode:
                    # 시뮬레이션: 버퍼에 저장
                    self._oled_buffer[y][x] = color
                else:
                    if self._oled:
                        # 실제 하드웨어: 픽셀 설정
                        await asyncio.to_thread(self._oled.pixel, x, y, color)
            return True
        except Exception as e:
            logger.error(f"OLED pixel error: {e}")
            return False

    async def oled_rect(self, x: int, y: int, width: int, height: int, fill: bool = False) -> bool:
        """
        OLED에 사각형 그리기 (비동기)
        Draw a rectangle on OLED (non-blocking)

        [한국어 설명]
        지정된 위치에 사각형을 그립니다.

        Args:
            x: 시작 X 좌표
            y: 시작 Y 좌표
            width: 사각형 너비
            height: 사각형 높이
            fill: True면 채워진 사각형, False면 테두리만

        Returns:
            bool: 성공 여부
        """
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
        """
        동기 방식 OLED 사각형 그리기
        Synchronous OLED rect (runs in thread pool)
        """
        if fill:
            # 채워진 사각형
            self._oled.fill_rect(x, y, width, height, 1)
        else:
            # 테두리만
            self._oled.rect(x, y, width, height, 1)
        self._oled.show()

    async def oled_show(self) -> bool:
        """
        OLED 화면 갱신 (비동기)
        Update OLED display (non-blocking)

        [한국어 설명]
        내부 버퍼의 내용을 실제 디스플레이에 반영합니다.
        여러 그리기 작업 후 한 번만 호출하면 효율적입니다.

        Returns:
            bool: 성공 여부
        """
        try:
            if not self.simulation_mode and self._oled:
                await asyncio.to_thread(self._oled.show)
            return True
        except Exception as e:
            logger.error(f"OLED show error: {e}")
            return False

    async def oled_display_dashboard(self, data: Dict[str, Any]) -> bool:
        """
        OLED에 간단한 대시보드 표시 (비동기)
        Display a simple dashboard on OLED

        [한국어 설명]
        딕셔너리 형태의 데이터를 줄별로 표시합니다.
        예: {"온도": "25°C", "습도": "60%"} → 2줄 표시

        Args:
            data: 표시할 데이터 (키-값 쌍)

        Returns:
            bool: 성공 여부
        """
        try:
            # 화면 지우기
            await self.oled_clear()

            # 각 항목을 줄별로 표시
            y_offset = 0
            for key, value in data.items():
                text = f"{key}: {value}"
                await self.oled_text(text, 0, y_offset)
                y_offset += 10  # 줄 간격 (10픽셀)

            # 화면 갱신
            await self.oled_show()
            return True

        except Exception as e:
            logger.error(f"OLED dashboard error: {e}")
            return False

    # ========================================================================
    # LCD 디스플레이 메서드 (LCD Display Methods)
    # ========================================================================

    async def lcd_clear(self) -> bool:
        """
        LCD 화면 지우기 (비동기)
        Clear LCD display (non-blocking)

        [한국어 설명]
        모든 줄을 빈 문자열로 초기화합니다.

        Returns:
            bool: 성공 여부
        """
        try:
            # 시뮬레이션 상태 초기화
            self._lcd_lines = ["", "", "", ""]

            if not self.simulation_mode and self._lcd:
                await asyncio.to_thread(self._lcd.clear)
            return True
        except Exception as e:
            logger.error(f"LCD clear error: {e}")
            return False

    async def lcd_write(self, text: str, row: int = 0, col: int = 0) -> bool:
        """
        LCD에 텍스트 쓰기 (비동기)
        Write text to LCD (non-blocking)

        [한국어 설명]
        지정된 행과 열에 텍스트를 표시합니다.

        Args:
            text: 표시할 텍스트
            row: 행 번호 (0부터 시작)
            col: 열 번호 (0부터 시작)

        Returns:
            bool: 성공 여부
        """
        try:
            if row < self._lcd_rows:
                # 시뮬레이션 상태 업데이트
                # [한국어 설명]
                # 기존 줄에서 col 위치부터 새 텍스트로 교체
                line = self._lcd_lines[row]
                new_line = line[:col] + text
                # 줄 길이가 최대 열 수를 넘지 않도록 자름
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
        """
        동기 방식 LCD 쓰기
        Synchronous LCD write (runs in thread pool)

        [한국어 설명]
        cursor_pos: 커서 위치 설정 (행, 열)
        write_string: 문자열 출력
        """
        self._lcd.cursor_pos = (row, col)
        self._lcd.write_string(text)

    async def lcd_set_backlight(self, enabled: bool) -> bool:
        """
        LCD 백라이트 설정 (비동기)
        Set LCD backlight state (non-blocking)

        [한국어 설명]
        LCD 뒤의 LED 백라이트를 켜거나 끕니다.

        Args:
            enabled: True면 켜기, False면 끄기

        Returns:
            bool: 성공 여부
        """
        try:
            self._lcd_backlight = enabled

            if not self.simulation_mode and self._lcd:
                # setattr(객체, 속성명, 값): 객체의 속성 설정
                await asyncio.to_thread(setattr, self._lcd, 'backlight_enabled', enabled)
            return True
        except Exception as e:
            logger.error(f"LCD backlight error: {e}")
            return False

    async def lcd_display_lines(self, lines: List[str]) -> bool:
        """
        LCD에 여러 줄 표시 (비동기)
        Display multiple lines on LCD

        [한국어 설명]
        문자열 리스트를 받아 각 줄에 순서대로 표시합니다.

        Args:
            lines: 표시할 문자열 리스트

        Returns:
            bool: 성공 여부
        """
        try:
            await self.lcd_clear()

            # 줄 수 제한 (최대 _lcd_rows 줄)
            # lines[:self._lcd_rows]: 리스트 슬라이싱으로 최대 줄 수만큼만 사용
            for i, line in enumerate(lines[:self._lcd_rows]):
                # 문자 수 제한 (최대 _lcd_cols 자)
                await self.lcd_write(line[:self._lcd_cols], row=i)
            return True
        except Exception as e:
            logger.error(f"LCD display lines error: {e}")
            return False

    # ========================================================================
    # 상태 조회 메서드 (Status Query Methods)
    # ========================================================================

    def get_lcd_content(self) -> List[str]:
        """
        현재 LCD 내용 반환 (시뮬레이션/상태 확인용)
        Get current LCD content (for simulation/status)

        Returns:
            List[str]: 각 줄의 내용
        """
        return self._lcd_lines[:self._lcd_rows]

    def get_oled_info(self) -> Dict[str, Any]:
        """
        OLED 디스플레이 정보 반환 (Get OLED display info)

        Returns:
            Dict: OLED 하드웨어 정보
        """
        return {
            "width": self._oled_width,       # 가로 픽셀
            "height": self._oled_height,     # 세로 픽셀
            "address": f"0x{self._oled_address:02X}",  # I2C 주소 (16진수)
            "connected": self._oled is not None or self.simulation_mode  # 연결 상태
        }

    def get_lcd_info(self) -> Dict[str, Any]:
        """
        LCD 디스플레이 정보 반환 (Get LCD display info)

        Returns:
            Dict: LCD 하드웨어 정보 및 현재 상태
        """
        return {
            "cols": self._lcd_cols,          # 가로 문자 수
            "rows": self._lcd_rows,          # 세로 줄 수
            "address": f"0x{self._lcd_address:02X}",  # I2C 주소
            "backlight": self._lcd_backlight,         # 백라이트 상태
            "content": self._lcd_lines[:self._lcd_rows],  # 현재 표시 내용
            "connected": self._lcd is not None or self.simulation_mode
        }

    def _get_status_details(self) -> Dict[str, Any]:
        """
        디스플레이 컨트롤러 상태 상세 정보
        Get display-specific status details

        Returns:
            Dict: OLED와 LCD의 상태 정보
        """
        return {
            "oled": self.get_oled_info(),
            "lcd": self.get_lcd_info()
        }
