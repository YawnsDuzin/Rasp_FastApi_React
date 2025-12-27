"""
GPIO Controller (GPIO 컨트롤러)
===============================

[한국어 설명]
라즈베리 파이의 GPIO(General Purpose Input/Output) 핀을 제어하는 모듈입니다.

GPIO란?
- 범용 입출력 핀 (General Purpose Input/Output)
- 라즈베리 파이에서 외부 장치와 통신하는 기본 인터페이스
- 디지털 신호 (HIGH/LOW, 1/0, 3.3V/0V)만 처리

이 모듈에서 제어하는 장치:
1. **LED** (Light Emitting Diode)
   - 출력 장치
   - HIGH → LED 켜짐, LOW → LED 꺼짐

2. **버튼** (Button/Switch)
   - 입력 장치
   - 눌림 → LOW (풀업 저항 사용 시), 안눌림 → HIGH

3. **릴레이** (Relay)
   - 출력 장치
   - 고전압/고전류 장치를 제어하는 스위치
   - HIGH → 릴레이 ON, LOW → 릴레이 OFF

핀 번호 체계:
- **BCM (Broadcom)**: GPIO 번호 사용 (예: GPIO17)
- **BOARD**: 물리적 핀 번호 사용 (예: 핀 11)
- 이 프로젝트는 BCM 모드 사용

[English Description]
Controls GPIO pins for LEDs, buttons, and relays.
Supports both real hardware and simulation mode.
"""

# ============================================================================
# 라이브러리 임포트 (Import Libraries)
# ============================================================================

# asyncio: 비동기 프로그래밍 모듈
import asyncio

# typing: 타입 힌트용 모듈
# Dict: 딕셔너리 타입 (키-값 쌍)
# List: 리스트 타입 (순서 있는 컬렉션)
# Optional: None이 될 수 있는 타입
# Callable: 호출 가능한 객체 (함수, 메서드 등)
# Any: 모든 타입 허용
from typing import Dict, List, Optional, Callable, Any

# dataclasses: 데이터 저장용 클래스 간편 생성
from dataclasses import dataclass

# enum: 열거형 정의 모듈
from enum import Enum

# 베이스 클래스와 시뮬레이션 믹스인 임포트
# BaseHardwareController: 모든 하드웨어 컨트롤러의 기반 클래스
# SimulationMixin: 시뮬레이션용 유틸리티 메서드 제공
# HardwareState: 하드웨어 상태 열거형
from .base import BaseHardwareController, SimulationMixin, HardwareState

# 설정 값 가져오기 (GPIO 핀 번호 등)
from app.core.config import settings

# 로거 가져오기
from app.core.logging_config import get_logger

# 이 모듈용 로거 생성
logger = get_logger(__name__)


# ============================================================================
# 핀 모드 열거형 (Pin Mode Enum)
# ============================================================================

class PinMode(Enum):
    """
    GPIO 핀 모드 (GPIO Pin Modes)

    [한국어 설명]
    GPIO 핀이 동작하는 방식을 정의합니다.

    핀 모드 종류:
    1. INPUT: 순수 입력 (외부에서 신호 읽기)
    2. OUTPUT: 출력 (외부로 신호 보내기)
    3. INPUT_PULLUP: 입력 + 내부 풀업 저항 활성화
    4. INPUT_PULLDOWN: 입력 + 내부 풀다운 저항 활성화

    풀업/풀다운 저항이란?
    - 버튼이 눌리지 않았을 때 핀의 상태를 정의
    - 풀업: 기본 HIGH (3.3V), 버튼 누르면 LOW (GND에 연결)
    - 풀다운: 기본 LOW (GND), 버튼 누르면 HIGH (3.3V에 연결)

    회로도 예시 (풀업):
        3.3V ─┬─[내부저항]─ GPIO핀
              │
              └─[ 버튼 ]─ GND

        버튼 안눌림: GPIO = HIGH (저항 통해 3.3V)
        버튼 눌림: GPIO = LOW (GND에 직접 연결)
    """
    INPUT = "input"                # 순수 입력 모드
    OUTPUT = "output"              # 출력 모드
    INPUT_PULLUP = "input_pullup"  # 입력 + 풀업 저항
    INPUT_PULLDOWN = "input_pulldown"  # 입력 + 풀다운 저항


# ============================================================================
# 핀 상태 열거형 (Pin State Enum)
# ============================================================================

class PinState(Enum):
    """
    GPIO 핀 상태 (GPIO Pin States)

    [한국어 설명]
    디지털 핀의 두 가지 상태:
    - LOW (0): 0V, 꺼짐, False
    - HIGH (1): 3.3V, 켜짐, True

    주의사항:
    - 라즈베리 파이는 3.3V 로직 사용 (5V 아님!)
    - 5V를 직접 연결하면 GPIO 핀 손상 가능
    """
    LOW = 0   # 낮은 전압 (0V, 꺼짐)
    HIGH = 1  # 높은 전압 (3.3V, 켜짐)


# ============================================================================
# GPIO 핀 데이터 클래스 (GPIO Pin Dataclass)
# ============================================================================

@dataclass
class GPIOPin:
    """
    GPIO 핀 설정 정보 (GPIO Pin Configuration)

    [한국어 설명]
    각 GPIO 핀의 설정과 현재 상태를 저장하는 데이터 클래스입니다.

    Attributes:
        pin: GPIO 핀 번호 (BCM 기준)
        mode: 핀 모드 (INPUT/OUTPUT/INPUT_PULLUP/INPUT_PULLDOWN)
        name: 핀 이름 (예: "LED_1", "Button_1")
        state: 현재 핀 상태 (LOW/HIGH)
        is_inverted: 반전 모드 (True면 로직 반전)
            - 일부 릴레이 모듈은 LOW일 때 켜짐

    @dataclass 데코레이터가 자동으로 생성하는 것:
    - __init__(self, pin, mode, name, state=PinState.LOW, is_inverted=False)
    - __repr__ 메서드
    - __eq__ 메서드
    """
    pin: int                          # GPIO 핀 번호 (BCM)
    mode: PinMode                     # 핀 모드
    name: str                         # 핀 이름 (설명용)
    state: PinState = PinState.LOW    # 현재 상태 (기본: LOW)
    is_inverted: bool = False         # 로직 반전 여부


# ============================================================================
# GPIO 컨트롤러 클래스 (GPIO Controller Class)
# ============================================================================

class GPIOController(BaseHardwareController, SimulationMixin):
    """
    GPIO 작업을 위한 컨트롤러 (Controller for GPIO Operations)

    [한국어 설명]
    다중 상속 구조:
    - BaseHardwareController: 초기화, 정리, 상태 관리 기능
    - SimulationMixin: 시뮬레이션용 유틸리티 메서드

    제공 기능:
    1. LED 제어 (켜기/끄기/토글)
    2. 버튼 입력 감지 (풀링/인터럽트)
    3. 릴레이 제어
    4. 콜백 기반 버튼 이벤트 처리

    비동기 설계:
    - 모든 하드웨어 조작은 async 함수
    - asyncio.to_thread()로 블로킹 I/O를 비동기로 변환
    - 이벤트 루프 블로킹 방지

    사용 예시:
        controller = GPIOController(simulation_mode=True)
        await controller.initialize()

        await controller.set_led(0, True)   # LED 0 켜기
        await controller.set_led(0, False)  # LED 0 끄기
        await controller.toggle_led(0)      # LED 0 토글

        button_pressed = await controller.read_button(0)  # 버튼 0 상태 읽기

        await controller.cleanup()
    """

    def __init__(self, simulation_mode: bool = False):
        """
        생성자 (Constructor)

        [한국어 설명]
        super().__init__() 호출:
        - 부모 클래스(BaseHardwareController)의 __init__ 실행
        - name="GPIO Controller"로 컨트롤러 이름 설정

        Args:
            simulation_mode: 시뮬레이션 모드 여부
                - True: 실제 하드웨어 없이 가상으로 동작
                - False: 실제 RPi.GPIO 라이브러리 사용
        """
        # 부모 클래스 초기화 (컨트롤러 이름 전달)
        super().__init__("GPIO Controller", simulation_mode)

        # 핀 정보 저장 딕셔너리 {핀번호: GPIOPin 객체}
        self._pins: Dict[int, GPIOPin] = {}

        # 버튼 콜백 함수 저장 {핀번호: [콜백함수 리스트]}
        # 콜백: 특정 이벤트 발생 시 자동으로 호출되는 함수
        self._button_callbacks: Dict[int, List[Callable]] = {}

        # RPi.GPIO 모듈 참조 (초기화 후 설정됨)
        self._gpio = None

        # 버튼 폴링 태스크 (시뮬레이션 모드에서 사용)
        self._button_task: Optional[asyncio.Task] = None

        # 설정에서 핀 번호 가져오기
        # LED 핀 목록 (예: [17, 27, 22, 23])
        self._led_pins: List[int] = settings.GPIO_LED_PINS

        # 버튼 핀 목록 (예: [5, 6, 13, 19])
        self._button_pins: List[int] = settings.GPIO_BUTTON_PINS

        # 릴레이 핀 목록 (예: [24, 25])
        self._relay_pins: List[int] = settings.GPIO_RELAY_PINS

    async def _do_initialize(self) -> bool:
        """
        GPIO 하드웨어 초기화 (Initialize GPIO Hardware)

        [한국어 설명]
        BaseHardwareController의 추상 메서드 구현.
        initialize() 메서드에서 호출됩니다.

        초기화 순서:
        1. RPi.GPIO 라이브러리 임포트 시도
        2. BCM 모드 설정
        3. LED 핀 설정 (OUTPUT)
        4. 버튼 핀 설정 (INPUT_PULLUP)
        5. 릴레이 핀 설정 (OUTPUT)
        6. 버튼 인터럽트 또는 폴링 태스크 시작

        Returns:
            True: 초기화 성공
            False: 초기화 실패
        """
        try:
            # 시뮬레이션 모드가 아닐 때만 실제 GPIO 라이브러리 로드
            if not self.simulation_mode:
                try:
                    # RPi.GPIO: 라즈베리 파이 공식 GPIO 라이브러리
                    import RPi.GPIO as GPIO
                    self._gpio = GPIO

                    # BCM 모드 설정 (Broadcom SOC 채널 번호 사용)
                    # 다른 옵션: GPIO.BOARD (물리적 핀 번호)
                    GPIO.setmode(GPIO.BCM)

                    # 경고 메시지 비활성화
                    # (이미 사용 중인 핀에 대한 경고 무시)
                    GPIO.setwarnings(False)

                except ImportError:
                    # 라즈베리 파이가 아닌 환경에서 실행 시
                    logger.warning("RPi.GPIO not available, falling back to simulation")
                    self.simulation_mode = True

            # LED 핀 설정 (출력 모드)
            # enumerate: (인덱스, 값) 튜플 반환
            # 예: enumerate([17, 27]) → (0, 17), (1, 27)
            for i, pin in enumerate(self._led_pins):
                await self._setup_pin(pin, PinMode.OUTPUT, f"LED_{i+1}")

            # 버튼 핀 설정 (입력 모드 + 풀업 저항)
            for i, pin in enumerate(self._button_pins):
                await self._setup_pin(pin, PinMode.INPUT_PULLUP, f"Button_{i+1}")

            # 릴레이 핀 설정 (출력 모드)
            for i, pin in enumerate(self._relay_pins):
                await self._setup_pin(pin, PinMode.OUTPUT, f"Relay_{i+1}")

            # 버튼 모니터링 시작
            if not self.simulation_mode:
                # 실제 하드웨어: 인터럽트 기반 버튼 감지
                self._setup_button_interrupts()
            else:
                # 시뮬레이션: 폴링 기반 (주기적으로 상태 확인)
                self._button_task = asyncio.create_task(self._simulate_button_polling())

            return True

        except Exception as e:
            logger.error(f"GPIO initialization failed: {e}")
            return False

    async def _do_cleanup(self) -> None:
        """
        GPIO 리소스 정리 (Clean up GPIO Resources)

        [한국어 설명]
        프로그램 종료 시 GPIO 리소스를 정리합니다.

        정리 작업:
        1. 버튼 폴링 태스크 취소
        2. GPIO.cleanup() 호출 (핀을 안전한 상태로 리셋)
        3. 내부 데이터 구조 초기화
        """
        # 버튼 폴링 태스크가 있으면 취소
        if self._button_task:
            self._button_task.cancel()
            try:
                await self._button_task
            except asyncio.CancelledError:
                # 태스크 취소는 정상적인 종료
                pass

        # 실제 하드웨어일 때 GPIO 정리
        if self._gpio and not self.simulation_mode:
            # GPIO.cleanup(): 모든 핀을 입력 모드로 리셋
            # 전류 누출과 회로 손상 방지
            self._gpio.cleanup()

        # 내부 데이터 구조 초기화
        self._pins.clear()
        self._button_callbacks.clear()

    async def _setup_pin(self, pin: int, mode: PinMode, name: str) -> None:
        """
        GPIO 핀 설정 (Setup a GPIO Pin)

        [한국어 설명]
        개별 GPIO 핀을 설정합니다.

        Args:
            pin: GPIO 핀 번호 (BCM)
            mode: 핀 모드 (INPUT/OUTPUT/INPUT_PULLUP/INPUT_PULLDOWN)
            name: 핀 이름 (로깅/디버깅용)
        """
        # GPIOPin 객체 생성 및 저장
        gpio_pin = GPIOPin(pin=pin, mode=mode, name=name)
        self._pins[pin] = gpio_pin

        # 실제 하드웨어일 때만 GPIO 설정
        if not self.simulation_mode and self._gpio:
            if mode == PinMode.OUTPUT:
                # 출력 모드: 초기 상태 LOW
                # GPIO.OUT: 출력 방향
                # initial=GPIO.LOW: 초기값 0V
                self._gpio.setup(pin, self._gpio.OUT, initial=self._gpio.LOW)

            elif mode == PinMode.INPUT_PULLUP:
                # 입력 모드 + 내부 풀업 저항
                # GPIO.IN: 입력 방향
                # pull_up_down=GPIO.PUD_UP: 내부 풀업 저항 활성화
                self._gpio.setup(pin, self._gpio.IN, pull_up_down=self._gpio.PUD_UP)

            elif mode == PinMode.INPUT_PULLDOWN:
                # 입력 모드 + 내부 풀다운 저항
                self._gpio.setup(pin, self._gpio.IN, pull_up_down=self._gpio.PUD_DOWN)

            else:
                # 순수 입력 모드 (외부 저항 필요)
                self._gpio.setup(pin, self._gpio.IN)

        logger.debug(f"Setup GPIO pin {pin} as {mode.value} ({name})")

    def _setup_button_interrupts(self) -> None:
        """
        하드웨어 버튼 인터럽트 설정 (Setup Hardware Button Interrupts)

        [한국어 설명]
        인터럽트(Interrupt)란?
        - 특정 이벤트 발생 시 CPU에 알리는 메커니즘
        - 폴링(주기적 확인)보다 효율적
        - 이벤트 발생 즉시 처리 가능

        add_event_detect() 파라미터:
        - pin: 모니터링할 GPIO 핀
        - GPIO.FALLING: 신호가 HIGH→LOW로 떨어질 때 감지
            - 다른 옵션: GPIO.RISING (LOW→HIGH), GPIO.BOTH (둘 다)
        - callback: 이벤트 발생 시 호출할 함수
        - bouncetime: 디바운싱 시간 (밀리초)

        디바운싱(Debouncing)이란?
        - 기계식 버튼은 눌릴 때 여러 번 접촉/해제됨 (채터링)
        - bouncetime 동안 추가 이벤트 무시
        - 200ms = 버튼 한 번 누름으로 인식되는 최소 간격
        """
        if not self._gpio:
            return

        for pin in self._button_pins:
            try:
                # 인터럽트 이벤트 감지 등록
                self._gpio.add_event_detect(
                    pin,                        # 모니터링할 핀
                    self._gpio.FALLING,         # HIGH→LOW 변화 감지
                    callback=self._on_button_press,  # 콜백 함수
                    bouncetime=200              # 디바운싱 200ms
                )
            except Exception as e:
                logger.error(f"Failed to setup interrupt for pin {pin}: {e}")

    def _on_button_press(self, pin: int) -> None:
        """
        버튼 누름 인터럽트 핸들러 (Handle Button Press Interrupt)

        [한국어 설명]
        버튼이 눌렸을 때 자동으로 호출되는 콜백 함수입니다.
        등록된 모든 콜백 함수를 실행합니다.

        Args:
            pin: 눌린 버튼의 GPIO 핀 번호
        """
        # 해당 핀에 등록된 콜백이 있는지 확인
        if pin in self._button_callbacks:
            # 등록된 모든 콜백 함수 실행
            for callback in self._button_callbacks[pin]:
                try:
                    callback(pin)  # 콜백 함수에 핀 번호 전달
                except Exception as e:
                    logger.error(f"Button callback error: {e}")

        # 마지막 업데이트 시간 갱신
        self._update_timestamp()
        logger.debug(f"Button press detected on pin {pin}")

    async def _simulate_button_polling(self) -> None:
        """
        시뮬레이션 버튼 폴링 (Simulate Button Polling)

        [한국어 설명]
        시뮬레이션 모드에서 버튼 상태를 주기적으로 확인합니다.
        실제로는 버튼이 눌리지 않으므로 대기만 합니다.
        simulate_button_press() 메서드로 프로그래밍 방식으로 버튼을 누를 수 있습니다.
        """
        while True:
            await asyncio.sleep(0.1)  # 100ms 간격으로 폴링
            # 시뮬레이션에서는 버튼이 프로그래밍 방식으로만 트리거됨

    # ==================== LED 제어 (LED Control) ====================

    async def set_led(self, index: int, state: bool) -> bool:
        """
        LED 상태 설정 (Set LED State)

        [한국어 설명]
        인덱스로 LED를 제어합니다.

        Args:
            index: LED 인덱스 (0부터 시작)
                - 0: 첫 번째 LED (settings.GPIO_LED_PINS[0])
                - 1: 두 번째 LED (settings.GPIO_LED_PINS[1])
                - ...
            state: LED 상태
                - True: 켜기 (HIGH, 3.3V)
                - False: 끄기 (LOW, 0V)

        Returns:
            True: 성공
            False: 실패 (잘못된 인덱스 등)

        사용 예시:
            await controller.set_led(0, True)   # LED 0 켜기
            await controller.set_led(0, False)  # LED 0 끄기
        """
        # 인덱스 범위 확인
        if index < 0 or index >= len(self._led_pins):
            logger.error(f"Invalid LED index: {index}")
            return False

        # 인덱스로 핀 번호 가져오기
        pin = self._led_pins[index]

        # 핀에 상태 쓰기
        # state가 True면 HIGH, False면 LOW
        return await self.write_pin(pin, PinState.HIGH if state else PinState.LOW)

    async def set_all_leds(self, state: bool) -> bool:
        """
        모든 LED를 같은 상태로 설정 (Set All LEDs to Same State)

        [한국어 설명]
        asyncio.gather()를 사용하여 모든 LED를 동시에 제어합니다.

        asyncio.gather(*tasks):
        - 여러 코루틴을 동시에 실행
        - *: 리스트를 개별 인자로 풀어줌 (언패킹)
        - 모든 작업이 완료될 때까지 대기
        - 결과를 리스트로 반환

        Args:
            state: True면 모두 켜기, False면 모두 끄기

        Returns:
            True: 모든 LED 설정 성공
            False: 하나라도 실패
        """
        # 모든 LED에 대해 set_led 코루틴 생성 후 동시 실행
        results = await asyncio.gather(
            *[self.set_led(i, state) for i in range(len(self._led_pins))]
        )
        # 모든 결과가 True인지 확인
        return all(results)

    async def toggle_led(self, index: int) -> bool:
        """
        LED 상태 토글 (Toggle LED State)

        [한국어 설명]
        현재 상태의 반대로 변경합니다.
        - 켜져 있으면 끄기
        - 꺼져 있으면 켜기

        Args:
            index: LED 인덱스

        Returns:
            True: 성공
            False: 실패
        """
        if index < 0 or index >= len(self._led_pins):
            return False

        pin = self._led_pins[index]

        # 현재 상태 가져오기
        current_state = self._pins[pin].state

        # 상태 반전
        new_state = PinState.LOW if current_state == PinState.HIGH else PinState.HIGH

        return await self.write_pin(pin, new_state)

    def get_led_states(self) -> Dict[int, bool]:
        """
        모든 LED 상태 조회 (Get All LED States)

        [한국어 설명]
        현재 모든 LED의 켜짐/꺼짐 상태를 딕셔너리로 반환합니다.

        Returns:
            {인덱스: 상태} 딕셔너리
            예: {0: True, 1: False, 2: True, 3: False}
        """
        return {
            i: self._pins[pin].state == PinState.HIGH
            for i, pin in enumerate(self._led_pins)
            if pin in self._pins  # 핀이 등록되어 있는지 확인
        }

    # ==================== 릴레이 제어 (Relay Control) ====================

    async def set_relay(self, index: int, state: bool) -> bool:
        """
        릴레이 상태 설정 (Set Relay State)

        [한국어 설명]
        릴레이는 저전압 신호로 고전압 장치를 제어하는 스위치입니다.

        릴레이 동작:
        - state=True (HIGH): 릴레이 ON → 연결된 장치 켜짐
        - state=False (LOW): 릴레이 OFF → 연결된 장치 꺼짐

        주의사항:
        - 릴레이가 제어하는 장치의 전압/전류를 확인할 것
        - 고전압 작업 시 안전에 주의

        Args:
            index: 릴레이 인덱스 (0부터 시작)
            state: 릴레이 상태 (True: ON, False: OFF)

        Returns:
            True: 성공
            False: 실패
        """
        if index < 0 or index >= len(self._relay_pins):
            logger.error(f"Invalid relay index: {index}")
            return False

        pin = self._relay_pins[index]
        return await self.write_pin(pin, PinState.HIGH if state else PinState.LOW)

    def get_relay_states(self) -> Dict[int, bool]:
        """
        모든 릴레이 상태 조회 (Get All Relay States)

        Returns:
            {인덱스: 상태} 딕셔너리
        """
        return {
            i: self._pins[pin].state == PinState.HIGH
            for i, pin in enumerate(self._relay_pins)
            if pin in self._pins
        }

    # ==================== 버튼 제어 (Button Control) ====================

    def register_button_callback(self, index: int, callback: Callable[[int], None]) -> None:
        """
        버튼 콜백 등록 (Register Button Press Callback)

        [한국어 설명]
        버튼이 눌렸을 때 호출될 함수를 등록합니다.

        Callable[[int], None]:
        - int 인자를 받고 None을 반환하는 함수
        - 인자: 눌린 버튼의 핀 번호

        Args:
            index: 버튼 인덱스
            callback: 콜백 함수

        사용 예시:
            def on_button_press(pin: int):
                print(f"Button on pin {pin} pressed!")

            controller.register_button_callback(0, on_button_press)
        """
        if index < 0 or index >= len(self._button_pins):
            return

        pin = self._button_pins[index]

        # 해당 핀의 콜백 리스트가 없으면 생성
        if pin not in self._button_callbacks:
            self._button_callbacks[pin] = []

        # 콜백 함수 추가
        self._button_callbacks[pin].append(callback)

    async def read_button(self, index: int) -> bool:
        """
        버튼 상태 읽기 (Read Button State)

        [한국어 설명]
        버튼이 현재 눌려있는지 확인합니다.

        풀업 저항 사용 시:
        - 버튼 안눌림: HIGH (풀업 저항으로 인해)
        - 버튼 눌림: LOW (GND에 연결)

        따라서 LOW일 때 "눌림"으로 판단합니다.

        Args:
            index: 버튼 인덱스

        Returns:
            True: 눌림
            False: 안눌림
        """
        if index < 0 or index >= len(self._button_pins):
            return False

        pin = self._button_pins[index]
        state = await self.read_pin(pin)

        # 풀업 사용 시, LOW = 눌림
        return state == PinState.LOW

    def get_button_states(self) -> Dict[int, bool]:
        """
        모든 버튼 상태 조회 (Get All Button States)

        Returns:
            {인덱스: 눌림여부} 딕셔너리
        """
        result = {}
        for i, pin in enumerate(self._button_pins):
            if pin in self._pins:
                # 시뮬레이션은 항상 False 반환 (수동 트리거 필요)
                result[i] = self._pins[pin].state == PinState.LOW
        return result

    async def simulate_button_press(self, index: int) -> None:
        """
        버튼 누름 시뮬레이션 (Simulate Button Press for Testing)

        [한국어 설명]
        시뮬레이션 모드에서 버튼 누름을 프로그래밍 방식으로 발생시킵니다.
        테스트나 UI에서 가상 버튼을 누를 때 사용합니다.

        Args:
            index: 버튼 인덱스
        """
        # 시뮬레이션 모드에서만 동작
        if not self.simulation_mode:
            return

        if index < 0 or index >= len(self._button_pins):
            return

        pin = self._button_pins[index]

        # 버튼 눌림 상태로 변경 (LOW)
        self._pins[pin].state = PinState.LOW

        # 콜백 함수 호출
        self._on_button_press(pin)

        # 잠시 대기 후 버튼 해제
        await asyncio.sleep(0.1)

        # 버튼 해제 상태로 변경 (HIGH)
        self._pins[pin].state = PinState.HIGH

    # ==================== 저수준 GPIO (Low-level GPIO) ====================

    async def write_pin(self, pin: int, state: PinState) -> bool:
        """
        GPIO 핀에 상태 쓰기 - 비블로킹 (Write State to GPIO Pin - Non-blocking)

        [한국어 설명]
        지정된 GPIO 핀에 HIGH 또는 LOW 신호를 출력합니다.

        asyncio.to_thread() 사용 이유:
        - GPIO.output()은 블로킹 함수 (완료될 때까지 대기)
        - 블로킹 함수를 직접 호출하면 이벤트 루프가 멈춤
        - to_thread()는 별도 스레드에서 실행하여 이벤트 루프 유지

        Args:
            pin: GPIO 핀 번호
            state: 출력할 상태 (PinState.HIGH 또는 PinState.LOW)

        Returns:
            True: 성공
            False: 실패
        """
        # 핀이 등록되어 있는지 확인
        if pin not in self._pins:
            logger.error(f"Pin {pin} not configured")
            return False

        try:
            if self.simulation_mode:
                # 시뮬레이션: 가상 지연만 추가
                await asyncio.sleep(self._simulate_delay())
            else:
                # 실제 하드웨어: 블로킹 GPIO 호출을 스레드 풀에서 실행
                # asyncio.to_thread(): 동기 함수를 비동기로 래핑
                await asyncio.to_thread(self._gpio.output, pin, state.value)

            # 내부 상태 업데이트
            self._pins[pin].state = state
            self._update_timestamp()
            logger.debug(f"Set pin {pin} to {state.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to write pin {pin}: {e}")
            return False

    async def read_pin(self, pin: int) -> PinState:
        """
        GPIO 핀 상태 읽기 - 비블로킹 (Read State from GPIO Pin - Non-blocking)

        [한국어 설명]
        지정된 GPIO 핀의 현재 상태(HIGH/LOW)를 읽습니다.

        Args:
            pin: GPIO 핀 번호

        Returns:
            현재 핀 상태 (PinState.HIGH 또는 PinState.LOW)
        """
        if pin not in self._pins:
            logger.error(f"Pin {pin} not configured")
            return PinState.LOW

        try:
            if self.simulation_mode:
                # 시뮬레이션: 저장된 상태 반환
                await asyncio.sleep(self._simulate_delay())
                return self._pins[pin].state
            else:
                # 실제 하드웨어: GPIO 입력 읽기
                value = await asyncio.to_thread(self._gpio.input, pin)
                state = PinState.HIGH if value else PinState.LOW
                self._pins[pin].state = state
                return state

        except Exception as e:
            logger.error(f"Failed to read pin {pin}: {e}")
            return PinState.LOW

    def _get_status_details(self) -> Dict[str, Any]:
        """
        GPIO 상세 상태 정보 (Get GPIO-specific Status Details)

        [한국어 설명]
        BaseHardwareController의 메서드를 오버라이드합니다.
        GPIO 컨트롤러에 특화된 상태 정보를 반환합니다.

        Returns:
            상세 정보 딕셔너리
        """
        return {
            "led_pins": self._led_pins,         # LED 핀 번호 목록
            "button_pins": self._button_pins,   # 버튼 핀 번호 목록
            "relay_pins": self._relay_pins,     # 릴레이 핀 번호 목록
            "led_states": self.get_led_states(),      # 현재 LED 상태
            "relay_states": self.get_relay_states(),  # 현재 릴레이 상태
            "button_states": self.get_button_states(), # 현재 버튼 상태
            "total_pins": len(self._pins)        # 등록된 총 핀 수
        }
