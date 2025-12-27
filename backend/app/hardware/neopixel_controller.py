"""
NeoPixel Controller (NeoPixel 컨트롤러)
=======================================

[한국어 설명]
WS2812B (NeoPixel) 어드레서블 LED 스트립을 제어하는 컨트롤러입니다.

NeoPixel이란?
- Adafruit에서 만든 WS2812B LED의 브랜드명
- "어드레서블 LED": 각 LED를 개별적으로 제어 가능
- 1선 통신 (데이터 선 하나로 모든 LED 제어)
- 각 LED는 RGB 색상 + 밝기 제어 가능

NeoPixel의 특징:
- 연결: VCC(5V), GND, DIN(데이터 입력)
- 데이터 전송: 직렬 방식으로 첫 LED부터 순차 전송
- 전원: LED 1개당 약 60mA (풀 화이트 기준)
- 긴 스트립은 외부 전원 필요

지원 이펙트:
- SOLID: 단색
- RAINBOW: 무지개색 순환
- BREATHING: 숨쉬기 효과 (밝기 변화)
- CHASE: 추적 효과
- SPARKLE: 반짝임
- WAVE: 파도 효과
- FIRE: 불꽃 효과

[English Description]
Controller for WS2812B (NeoPixel) addressable LED strips.
Supports various effects and animations.
"""

# ============================================================================
# 라이브러리 임포트 (Import Libraries)
# ============================================================================

# asyncio: 비동기 I/O 처리 및 이펙트 애니메이션용
import asyncio

# math: 수학 함수 (sin, cos 등 - 이펙트 계산용)
import math

# typing: 타입 힌트용 모듈
from typing import Dict, Optional, Any, List, Tuple

# dataclass: 데이터 저장 클래스를 간편하게 정의
from dataclasses import dataclass

# Enum: 열거형 상수 정의
from enum import Enum

# base: 하드웨어 컨트롤러 기본 클래스
from .base import BaseHardwareController, SimulationMixin

# settings: 애플리케이션 설정 (핀 번호, LED 개수 등)
from app.core.config import settings

# get_logger: 로깅 함수
from app.core.logging_config import get_logger

# 이 모듈 전용 로거 생성
logger = get_logger(__name__)


# ============================================================================
# 열거형 상수 (Enumerations)
# ============================================================================

class NeopixelEffect(Enum):
    """
    LED 이펙트 종류 열거형 (Available LED effects)

    [한국어 설명]
    NeoPixel LED에 적용할 수 있는 다양한 애니메이션 효과입니다.
    각 이펙트는 LED 색상과 밝기를 시간에 따라 변화시킵니다.
    """
    SOLID = "solid"           # 단색: 모든 LED를 같은 색으로
    RAINBOW = "rainbow"       # 무지개: 색상 스펙트럼 순환
    BREATHING = "breathing"   # 숨쉬기: 밝기가 서서히 변화
    CHASE = "chase"           # 추적: LED가 순차적으로 켜짐
    SPARKLE = "sparkle"       # 반짝임: 랜덤 LED가 깜빡임
    WAVE = "wave"             # 파도: 물결 모양 색상 변화
    FIRE = "fire"             # 불꽃: 화염 시뮬레이션


# ============================================================================
# 데이터 클래스 (Data Classes)
# ============================================================================

@dataclass
class RGBColor:
    """
    RGB 색상을 표현하는 데이터 클래스 (RGB color representation)

    [한국어 설명]
    RGB(Red, Green, Blue) 색상 모델:
    - 각 채널은 0~255 값
    - (255, 0, 0) = 빨강
    - (0, 255, 0) = 초록
    - (0, 0, 255) = 파랑
    - (255, 255, 255) = 흰색
    - (0, 0, 0) = 검정 (꺼짐)

    속성:
    - r: 빨강 채널 (0-255)
    - g: 초록 채널 (0-255)
    - b: 파랑 채널 (0-255)
    """
    r: int  # Red 채널 (0-255)
    g: int  # Green 채널 (0-255)
    b: int  # Blue 채널 (0-255)

    def __post_init__(self):
        """
        초기화 후 값 검증 (Post-initialization validation)

        [한국어 설명]
        @dataclass의 특수 메서드로, __init__ 이후에 자동 호출됩니다.
        RGB 값을 0~255 범위로 제한합니다.

        max(0, min(255, value)):
        - min(255, value): value와 255 중 작은 값 (최대 255로 제한)
        - max(0, ...): 결과와 0 중 큰 값 (최소 0으로 제한)
        """
        self.r = max(0, min(255, self.r))
        self.g = max(0, min(255, self.g))
        self.b = max(0, min(255, self.b))

    def to_tuple(self) -> Tuple[int, int, int]:
        """
        튜플로 변환 (Convert to tuple)

        [한국어 설명]
        NeoPixel 라이브러리는 색상을 (R, G, B) 튜플로 받습니다.

        Returns:
            Tuple[int, int, int]: (R, G, B) 튜플
        """
        return (self.r, self.g, self.b)

    def to_hex(self) -> str:
        """
        16진수 색상 코드로 변환 (Convert to hex color code)

        [한국어 설명]
        웹에서 사용하는 #RRGGBB 형식의 색상 코드로 변환합니다.

        예: RGBColor(255, 128, 0) → "#FF8000"

        f"#{self.r:02X}": 포맷 문자열
        - 02: 최소 2자리
        - X: 대문자 16진수

        Returns:
            str: "#RRGGBB" 형식의 문자열
        """
        return f"#{self.r:02X}{self.g:02X}{self.b:02X}"

    @classmethod
    def from_hex(cls, hex_color: str) -> "RGBColor":
        """
        16진수 색상 코드에서 생성 (Create from hex color code)

        [한국어 설명]
        @classmethod: 클래스 메서드 (인스턴스 없이 호출 가능)
        cls: 클래스 자체를 받음 (RGBColor)

        예: RGBColor.from_hex("#FF8000") → RGBColor(255, 128, 0)

        int(hex_color[0:2], 16):
        - hex_color[0:2]: 처음 2글자 추출
        - int(..., 16): 16진수로 해석하여 정수 변환

        Args:
            hex_color: "#RRGGBB" 형식의 문자열

        Returns:
            RGBColor: 새로운 RGBColor 인스턴스
        """
        # '#' 문자 제거
        hex_color = hex_color.lstrip('#')

        # 각 채널 추출 및 변환
        return cls(
            r=int(hex_color[0:2], 16),  # 처음 2글자 → Red
            g=int(hex_color[2:4], 16),  # 다음 2글자 → Green
            b=int(hex_color[4:6], 16)   # 마지막 2글자 → Blue
        )


# ============================================================================
# 미리 정의된 색상 (Predefined Colors)
# ============================================================================

# [한국어 설명]
# 자주 사용하는 색상을 미리 정의해둔 딕셔너리입니다.
# 문자열 이름으로 색상을 쉽게 참조할 수 있습니다.
COLORS = {
    "red": RGBColor(255, 0, 0),       # 빨강
    "green": RGBColor(0, 255, 0),     # 초록
    "blue": RGBColor(0, 0, 255),      # 파랑
    "white": RGBColor(255, 255, 255), # 흰색
    "yellow": RGBColor(255, 255, 0),  # 노랑
    "cyan": RGBColor(0, 255, 255),    # 시안 (하늘색)
    "magenta": RGBColor(255, 0, 255), # 마젠타 (분홍)
    "orange": RGBColor(255, 165, 0),  # 주황
    "purple": RGBColor(128, 0, 128),  # 보라
    "pink": RGBColor(255, 192, 203),  # 분홍
    "off": RGBColor(0, 0, 0)          # 꺼짐 (검정)
}


# ============================================================================
# NeoPixel 컨트롤러 클래스 (NeoPixel Controller Class)
# ============================================================================

class NeopixelController(BaseHardwareController, SimulationMixin):
    """
    WS2812B NeoPixel LED 스트립 컨트롤러
    Controller for WS2812B NeoPixel LED strips

    [한국어 설명]
    개별 LED 제어와 다양한 애니메이션 효과를 지원합니다.

    NeoPixel 연결:
    - VCC → 5V (외부 전원 권장)
    - GND → GND
    - DIN → GPIO 핀 (settings.NEOPIXEL_PIN)

    주의사항:
    - 5V 레벨 시프터 필요할 수 있음 (라즈베리 파이는 3.3V)
    - 긴 스트립은 별도 전원 필요
    - 데이터 핀에 330Ω 저항 권장

    Features:
    - Individual LED control
    - Color effects and animations
    - Brightness control
    - Effect scheduling
    """

    def __init__(self, simulation_mode: bool = False):
        """
        NeoPixel 컨트롤러 초기화 (Initialize NeoPixel Controller)

        [한국어 설명]
        LED 스트립 정보와 이펙트 관련 변수를 초기화합니다.
        """
        # 부모 클래스 초기화
        super().__init__("NeoPixel Controller", simulation_mode)

        # GPIO 핀 번호 (데이터 핀)
        self._pin = settings.NEOPIXEL_PIN

        # LED 개수
        self._num_leds = settings.NEOPIXEL_COUNT

        # NeoPixel 객체 (neopixel 라이브러리 인스턴스)
        self._pixels = None

        # 전체 밝기 (0.0 ~ 1.0)
        # 0.0 = 완전히 어둡게, 1.0 = 최대 밝기
        self._brightness = 0.5

        # 현재 실행 중인 이펙트
        self._current_effect = NeopixelEffect.SOLID

        # 이펙트 실행을 위한 asyncio Task
        # [한국어 설명]
        # asyncio.Task는 비동기 작업을 나타내는 객체입니다.
        # 이펙트 애니메이션은 백그라운드에서 계속 실행됩니다.
        self._effect_task: Optional[asyncio.Task] = None

        # 이펙트 실행 중 여부 플래그
        self._effect_running = False

        # 시뮬레이션용 LED 상태 배열
        # [한국어 설명]
        # 각 LED의 현재 색상을 저장합니다.
        # 리스트 컴프리헨션: [RGBColor(0,0,0) for _ in range(개수)]
        self._led_colors: List[RGBColor] = [RGBColor(0, 0, 0) for _ in range(self._num_leds)]

    # ========================================================================
    # 초기화 및 정리 메서드 (Initialization and Cleanup Methods)
    # ========================================================================

    async def _do_initialize(self) -> bool:
        """
        NeoPixel 스트립 초기화 (비동기)
        Initialize NeoPixel strip (non-blocking)

        [한국어 설명]
        neopixel 라이브러리를 사용하여 LED 스트립을 초기화합니다.

        라이브러리 설치:
        sudo pip3 install adafruit-circuitpython-neopixel

        추가 요구사항:
        - rpi_ws281x 라이브러리도 필요
        - sudo 권한으로 실행해야 할 수 있음

        Returns:
            bool: 초기화 성공 여부
        """
        try:
            if not self.simulation_mode:
                try:
                    # 블로킹 초기화를 스레드 풀에서 실행
                    await asyncio.to_thread(self._init_neopixel_sync)

                except ImportError:
                    # neopixel 라이브러리가 없는 경우
                    logger.warning("NeoPixel library not available, falling back to simulation")
                    self.simulation_mode = True
                except Exception as e:
                    logger.warning(f"NeoPixel init failed: {e}")
                    self.simulation_mode = True

            return True

        except Exception as e:
            logger.error(f"NeoPixel initialization failed: {e}")
            return False

    def _init_neopixel_sync(self) -> None:
        """
        동기 방식 NeoPixel 초기화 (스레드 풀에서 실행됨)
        Synchronous NeoPixel initialization (runs in thread pool)

        [한국어 설명]
        Adafruit neopixel 라이브러리 사용.

        NeoPixel() 파라미터:
        - pin: GPIO 핀 객체 (board.D{핀번호})
        - n: LED 개수
        - brightness: 전체 밝기 (0.0 ~ 1.0)
        - auto_write: False면 show() 호출 필요
        - pixel_order: 색상 순서 (GRB가 일반적)
        """
        import board
        import neopixel

        # GPIO 핀 객체 가져오기
        # getattr(board, "D18") → board.D18
        pin = getattr(board, f"D{self._pin}")

        # NeoPixel 객체 생성
        self._pixels = neopixel.NeoPixel(
            pin,                    # GPIO 핀
            self._num_leds,         # LED 개수
            brightness=self._brightness,  # 밝기
            auto_write=False,       # 자동 갱신 비활성화 (성능 향상)
            pixel_order=neopixel.GRB  # 색상 순서 (Green-Red-Blue)
        )

        # 모든 LED 끄기
        self._pixels.fill((0, 0, 0))
        self._pixels.show()

    async def _do_cleanup(self) -> None:
        """
        NeoPixel 리소스 정리 (비동기)
        Clean up NeoPixel resources (non-blocking)

        [한국어 설명]
        이펙트 중지, LED 끄기, 리소스 해제 순서로 정리합니다.
        """
        # 실행 중인 이펙트 중지
        await self.stop_effect()

        # 모든 LED 끄기
        await self.clear()

        # NeoPixel 객체 해제
        if self._pixels:
            await asyncio.to_thread(self._pixels.deinit)
            self._pixels = None

    # ========================================================================
    # 기본 제어 메서드 (Basic Control Methods)
    # ========================================================================

    async def set_pixel(self, index: int, color: RGBColor) -> bool:
        """
        단일 픽셀 색상 설정 (비동기)
        Set a single pixel color (non-blocking)

        [한국어 설명]
        특정 인덱스의 LED 색상을 설정합니다.
        인덱스는 0부터 시작합니다.

        Args:
            index: LED 인덱스 (0부터 시작)
            color: 설정할 RGB 색상

        Returns:
            bool: 성공 여부
        """
        # 인덱스 범위 검증
        if index < 0 or index >= self._num_leds:
            return False

        try:
            # 시뮬레이션 상태 업데이트
            self._led_colors[index] = color

            if not self.simulation_mode and self._pixels:
                # 실제 하드웨어 제어
                await asyncio.to_thread(self._set_pixel_sync, index, color)

            return True

        except Exception as e:
            logger.error(f"Set pixel error: {e}")
            return False

    def _set_pixel_sync(self, index: int, color: RGBColor) -> None:
        """
        동기 방식 픽셀 설정 (스레드 풀에서 실행됨)
        Synchronous pixel set (runs in thread pool)

        [한국어 설명]
        self._pixels[index] = (R, G, B) 형식으로 색상 설정
        show() 호출로 실제 LED에 반영
        """
        self._pixels[index] = color.to_tuple()
        self._pixels.show()

    async def set_all(self, color: RGBColor) -> bool:
        """
        모든 픽셀을 같은 색으로 설정 (비동기)
        Set all pixels to the same color (non-blocking)

        [한국어 설명]
        전체 LED 스트립을 단일 색상으로 채웁니다.

        Args:
            color: 설정할 RGB 색상

        Returns:
            bool: 성공 여부
        """
        try:
            # 시뮬레이션 상태 업데이트
            for i in range(self._num_leds):
                self._led_colors[i] = color

            if not self.simulation_mode and self._pixels:
                await asyncio.to_thread(self._set_all_sync, color)

            return True

        except Exception as e:
            logger.error(f"Set all pixels error: {e}")
            return False

    def _set_all_sync(self, color: RGBColor) -> None:
        """
        동기 방식 전체 픽셀 설정 (스레드 풀에서 실행됨)
        Synchronous set all pixels (runs in thread pool)

        [한국어 설명]
        fill() 메서드로 모든 LED를 한 번에 설정합니다.
        개별 설정보다 효율적입니다.
        """
        self._pixels.fill(color.to_tuple())
        self._pixels.show()

    async def clear(self) -> bool:
        """
        모든 픽셀 끄기 (Turn off all pixels)

        Returns:
            bool: 성공 여부
        """
        return await self.set_all(COLORS["off"])

    async def set_brightness(self, brightness: float) -> bool:
        """
        전체 밝기 설정 (비동기)
        Set overall brightness (non-blocking)

        [한국어 설명]
        0.0 ~ 1.0 범위로 전체 밝기를 조절합니다.
        1.0 = 100% 밝기

        주의: 높은 밝기는 더 많은 전류를 소비합니다.

        Args:
            brightness: 밝기 레벨 (0.0 ~ 1.0)

        Returns:
            bool: 성공 여부
        """
        # 값 범위 제한
        self._brightness = max(0.0, min(1.0, brightness))

        if not self.simulation_mode and self._pixels:
            # setattr(객체, 속성명, 값): 객체의 속성 설정
            await asyncio.to_thread(setattr, self._pixels, 'brightness', self._brightness)

        return True

    async def show(self) -> bool:
        """
        LED 스트립 화면 갱신 (비동기)
        Update the LED strip display (non-blocking)

        [한국어 설명]
        내부 버퍼의 색상을 실제 LED에 반영합니다.
        auto_write=False일 때 필요합니다.

        Returns:
            bool: 성공 여부
        """
        try:
            if not self.simulation_mode and self._pixels:
                await asyncio.to_thread(self._pixels.show)
            return True
        except Exception as e:
            logger.error(f"Show error: {e}")
            return False

    # ========================================================================
    # 이펙트 메서드 (Effect Methods)
    # ========================================================================

    async def start_effect(self, effect: NeopixelEffect, **kwargs) -> bool:
        """
        LED 이펙트 시작 (Start an LED effect)

        [한국어 설명]
        지정된 이펙트를 백그라운드에서 실행합니다.
        기존 이펙트가 있으면 먼저 중지합니다.

        **kwargs:
        - 파이썬의 가변 키워드 인자
        - 함수 호출 시 이름=값 형태의 인자들을 딕셔너리로 받음
        - 예: start_effect(RAINBOW, speed=0.05)
              → kwargs = {"speed": 0.05}

        asyncio.create_task():
        - 코루틴을 백그라운드에서 실행하도록 예약
        - Task 객체 반환 (나중에 취소 가능)

        Args:
            effect: 이펙트 종류 (NeopixelEffect 열거형)
            **kwargs: 이펙트별 파라미터 (speed, color 등)

        Returns:
            bool: 시작 성공 여부
        """
        # 기존 이펙트 중지
        await self.stop_effect()

        # 새 이펙트 설정
        self._current_effect = effect
        self._effect_running = True

        # 이펙트별 태스크 생성
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
        """
        현재 이펙트 중지 (Stop the current effect)

        [한국어 설명]
        실행 중인 이펙트 태스크를 취소합니다.

        task.cancel():
        - 태스크 취소 요청
        - 태스크 내부에서 CancelledError 발생

        try/except CancelledError:
        - 취소된 태스크를 await하면 CancelledError 발생
        - 이를 잡아서 정상적으로 처리

        Returns:
            bool: 성공 여부
        """
        # 실행 플래그 해제
        self._effect_running = False

        # 태스크 취소
        if self._effect_task:
            self._effect_task.cancel()
            try:
                # 태스크가 완전히 종료될 때까지 대기
                await self._effect_task
            except asyncio.CancelledError:
                # 취소는 정상적인 종료
                pass
            self._effect_task = None

        return True

    async def _rainbow_effect(self, speed: float = 0.05) -> None:
        """
        무지개 색상 순환 이펙트 (Rainbow cycling effect)

        [한국어 설명]
        모든 LED가 무지개 색상 스펙트럼을 순환합니다.
        각 LED는 위치에 따라 다른 색상을 가집니다.

        Args:
            speed: 애니메이션 속도 (초 단위 지연)
        """
        offset = 0  # 색상 오프셋 (0~255 순환)

        while self._effect_running:
            for i in range(self._num_leds):
                # 각 LED의 색상 계산
                # (인덱스 + 오프셋) % 256: 0~255 범위 순환
                hue = (i + offset) % 256
                color = self._wheel(hue)

                # 시뮬레이션 상태 업데이트
                self._led_colors[i] = RGBColor(*color)

                # 실제 하드웨어 업데이트
                if not self.simulation_mode and self._pixels:
                    self._pixels[i] = color

            # 화면 갱신
            await self.show()

            # 오프셋 증가 (다음 프레임에서 색상 이동)
            offset = (offset + 1) % 256

            # 지연
            await asyncio.sleep(speed)

    async def _breathing_effect(self, color: RGBColor = None, speed: float = 0.02) -> None:
        """
        숨쉬기 효과 (페이드 인/아웃)
        Breathing (fade in/out) effect

        [한국어 설명]
        밝기가 sin 곡선을 따라 부드럽게 변합니다.

        math.sin(step):
        - 입력: 라디안 각도
        - 출력: -1 ~ 1 범위의 값
        - (sin(step) + 1) / 2: 0 ~ 1 범위로 정규화

        Args:
            color: 숨쉬기에 사용할 색상 (기본: 파랑)
            speed: 애니메이션 속도
        """
        color = color or COLORS["blue"]  # None이면 파랑 사용
        step = 0  # sin 함수 입력값

        while self._effect_running:
            # sin 곡선으로 밝기 계산 (0 ~ 1)
            # sin은 -1~1 범위이므로 +1 후 /2로 0~1 범위로 변환
            brightness = (math.sin(step) + 1) / 2

            # 밝기가 적용된 색상 계산
            adjusted = RGBColor(
                int(color.r * brightness),
                int(color.g * brightness),
                int(color.b * brightness)
            )

            # 모든 LED에 적용
            await self.set_all(adjusted)

            # 다음 단계로
            step += 0.05
            await asyncio.sleep(speed)

    async def _chase_effect(self, color: RGBColor = None, speed: float = 0.1) -> None:
        """
        극장 추적 효과 (Theater chase effect)

        [한국어 설명]
        3개 LED 중 1개만 켜지며 순환합니다.
        극장 조명처럼 보입니다.

        Args:
            color: 사용할 색상 (기본: 흰색)
            speed: 애니메이션 속도
        """
        color = color or COLORS["white"]

        while self._effect_running:
            # 3단계로 패턴 순환
            for offset in range(3):
                for i in range(self._num_leds):
                    # 3으로 나눈 나머지가 offset과 같으면 켜짐
                    if (i + offset) % 3 == 0:
                        self._led_colors[i] = color
                    else:
                        self._led_colors[i] = COLORS["off"]

                    if not self.simulation_mode and self._pixels:
                        self._pixels[i] = self._led_colors[i].to_tuple()

                await self.show()
                await asyncio.sleep(speed)

    async def _sparkle_effect(self, color: RGBColor = None, speed: float = 0.1) -> None:
        """
        랜덤 반짝임 효과 (Random sparkle effect)

        [한국어 설명]
        무작위 LED가 순간적으로 반짝입니다.

        random.randint(a, b): a~b 범위의 랜덤 정수

        Args:
            color: 반짝이는 색상 (기본: 흰색)
            speed: 반짝임 간격
        """
        import random
        color = color or COLORS["white"]

        while self._effect_running:
            # 모든 LED 끄기
            await self.clear()

            # 랜덤 위치 선택
            pixel = random.randint(0, self._num_leds - 1)

            # 선택된 LED 켜기
            await self.set_pixel(pixel, color)

            # 지연
            await asyncio.sleep(speed)

    async def _wave_effect(self, speed: float = 0.05) -> None:
        """
        색상 파도 효과 (Color wave effect)

        [한국어 설명]
        물결 모양으로 색상이 흐릅니다.
        각 LED의 밝기가 sin 함수로 계산됩니다.

        Args:
            speed: 파도 속도
        """
        offset = 0

        while self._effect_running:
            for i in range(self._num_leds):
                # 각 LED의 밝기 계산 (위치에 따라 다름)
                # i * 0.5: LED 간 위상 차이
                brightness = (math.sin(offset + i * 0.5) + 1) / 2

                # 보라/핑크 계열 색상
                color = RGBColor(
                    int(255 * brightness),      # 빨강
                    int(100 * (1 - brightness)), # 초록 (반전)
                    int(200 * brightness)        # 파랑
                )
                self._led_colors[i] = color

                if not self.simulation_mode and self._pixels:
                    self._pixels[i] = color.to_tuple()

            await self.show()
            offset += 0.2  # 파도 이동
            await asyncio.sleep(speed)

    async def _fire_effect(self, speed: float = 0.05) -> None:
        """
        불꽃/화염 효과 (Fire/flame effect)

        [한국어 설명]
        불꽃처럼 깜빡이는 빨강/주황 색상입니다.
        랜덤 변동으로 자연스러운 화염을 시뮬레이션합니다.

        Args:
            speed: 깜빡임 속도
        """
        import random

        while self._effect_running:
            for i in range(self._num_leds):
                # 랜덤 깜빡임 (0~100)
                flicker = random.randint(0, 100)

                # 빨강 고정, 초록은 깜빡임에 따라 변화
                r = 255
                g = max(0, 100 - flicker)  # 0~100 범위
                b = 0

                color = RGBColor(r, g, b)
                self._led_colors[i] = color

                if not self.simulation_mode and self._pixels:
                    self._pixels[i] = color.to_tuple()

            await self.show()
            await asyncio.sleep(speed)

    def _wheel(self, pos: int) -> Tuple[int, int, int]:
        """
        0~255 위치에서 무지개 색상 생성
        Generate rainbow colors across 0-255 positions

        [한국어 설명]
        0~255 값을 빨강→초록→파랑→빨강 순으로 순환하는
        색상 스펙트럼으로 변환합니다.

        구간:
        - 0~84: 빨강↓ 초록↑
        - 85~169: 초록↓ 파랑↑
        - 170~255: 파랑↓ 빨강↑

        Args:
            pos: 색상 위치 (0-255)

        Returns:
            Tuple[int, int, int]: (R, G, B) 튜플
        """
        if pos < 85:
            # 빨강 감소, 초록 증가
            return (255 - pos * 3, pos * 3, 0)
        elif pos < 170:
            # 초록 감소, 파랑 증가
            pos -= 85
            return (0, 255 - pos * 3, pos * 3)
        else:
            # 파랑 감소, 빨강 증가
            pos -= 170
            return (pos * 3, 0, 255 - pos * 3)

    # ========================================================================
    # 상태 조회 메서드 (Status Query Methods)
    # ========================================================================

    def get_led_states(self) -> List[Dict[str, Any]]:
        """
        모든 LED 상태 반환 (Get all LED states)

        [한국어 설명]
        각 LED의 인덱스, 색상(HEX), RGB 값을 리스트로 반환합니다.

        Returns:
            List[Dict]: LED 상태 리스트
        """
        return [
            {
                "index": i,              # LED 인덱스
                "color": color.to_hex(), # HEX 색상 코드 (#RRGGBB)
                "rgb": color.to_tuple()  # RGB 튜플 (R, G, B)
            }
            for i, color in enumerate(self._led_colors)
        ]

    def _get_status_details(self) -> Dict[str, Any]:
        """
        NeoPixel 컨트롤러 상태 상세 정보
        Get NeoPixel-specific status details

        Returns:
            Dict: 핀 번호, LED 수, 밝기, 이펙트 상태 등
        """
        return {
            "pin": self._pin,                    # GPIO 핀 번호
            "num_leds": self._num_leds,          # LED 개수
            "brightness": self._brightness,       # 현재 밝기
            "current_effect": self._current_effect.value if self._current_effect else None,
            "effect_running": self._effect_running,  # 이펙트 실행 중 여부
            "led_states": self.get_led_states()  # 각 LED 상태
        }
