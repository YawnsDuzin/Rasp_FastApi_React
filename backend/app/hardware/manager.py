"""
Hardware Manager (하드웨어 매니저)
==================================

[한국어 설명]
모든 하드웨어 컨트롤러를 통합 관리하는 중앙 매니저 클래스입니다.

주요 기능:
1. 통합 초기화/정리: 모든 컨트롤러의 생명주기 관리
2. 백그라운드 데이터 수집: 주기적으로 센서 값 읽기
3. 이벤트 콜백: 데이터 변경 시 등록된 함수 호출
4. 하드웨어 상태 모니터링: 전체 시스템 상태 확인

아키텍처:
                    ┌─────────────────────┐
                    │   HardwareManager   │
                    │   (통합 관리자)      │
                    └──────────┬──────────┘
                               │
       ┌───────────┬───────────┼───────────┬───────────┐
       ▼           ▼           ▼           ▼           ▼
   ┌───────┐  ┌───────┐   ┌───────┐  ┌───────┐  ┌───────┐
   │ GPIO  │  │  PWM  │   │Sensor │  │Display│  │NeoPixel│
   └───────┘  └───────┘   └───────┘  └───────┘  └───────┘

사용 패턴 (Facade 패턴):
- 복잡한 하위 시스템을 단순화된 인터페이스로 제공
- 외부에서는 HardwareManager만 사용
- 개별 컨트롤러에 직접 접근할 필요 없음

[English Description]
Central manager for all hardware controllers.
Provides unified interface and background data collection.
"""

# ============================================================================
# 라이브러리 임포트 (Import Libraries)
# ============================================================================

# asyncio: 비동기 I/O 처리 및 백그라운드 태스크
import asyncio

# typing: 타입 힌트용 모듈
# Callable: 함수 타입 힌트 (호출 가능한 객체)
from typing import Dict, Any, Optional, Callable, List

# datetime: 날짜/시간 처리
from datetime import datetime

# dataclass, field: 데이터 저장 클래스 정의
# field: 기본값 팩토리 함수 지정
from dataclasses import dataclass, field

# 개별 하드웨어 컨트롤러 임포트
from .gpio_controller import GPIOController       # GPIO (LED, 버튼, 릴레이)
from .pwm_controller import PWMController         # PWM (모터, 서보)
from .i2c_controller import I2CController         # I2C (센서, 디스플레이)
from .spi_controller import SPIController         # SPI (ADC)
from .sensor_controller import SensorController   # 센서 (DHT, 초음파 등)
from .display_controller import DisplayController # 디스플레이 (OLED, LCD)
from .neopixel_controller import NeopixelController  # NeoPixel LED

# 기본 클래스에서 상태 관련 클래스 임포트
from .base import HardwareState, HardwareStatus

# 애플리케이션 설정
from app.core.config import settings

# 로깅
from app.core.logging_config import get_logger

# 이 모듈 전용 로거 생성
logger = get_logger(__name__)


# ============================================================================
# 하드웨어 데이터 클래스 (Hardware Data Class)
# ============================================================================

@dataclass
class HardwareData:
    """
    통합 하드웨어 데이터 스냅샷 (Combined hardware data snapshot)

    [한국어 설명]
    특정 시점의 모든 하드웨어 상태를 저장하는 데이터 클래스입니다.
    주기적으로 이 객체가 생성되어 WebSocket으로 프론트엔드에 전송됩니다.

    field(default_factory=...):
    - 가변 객체(리스트, 딕셔너리)의 기본값 지정 시 사용
    - 같은 객체를 공유하지 않고 매번 새로 생성
    - 예: default_factory=dict → 인스턴스마다 새 딕셔너리 생성

    속성 분류:
    - timestamp: 데이터 수집 시간
    - GPIO: LED, 버튼, 릴레이 상태
    - PWM: 모터 속도, 서보 각도
    - 센서: 온도, 습도, 기압, 거리, 동작감지 등
    - ADC: 아날로그 값 (I2C, SPI)
    - 디스플레이: LCD 내용
    - NeoPixel: LED 색상
    """
    # ==================== 타임스탬프 ====================
    # 데이터 수집 시점
    # field(default_factory=datetime.now): 객체 생성 시 현재 시간 자동 설정
    timestamp: datetime = field(default_factory=datetime.now)

    # ==================== GPIO 상태 ====================
    # LED 상태 (인덱스 → True/False)
    led_states: Dict[int, bool] = field(default_factory=dict)
    # 버튼 상태 (인덱스 → True/False)
    button_states: Dict[int, bool] = field(default_factory=dict)
    # 릴레이 상태 (인덱스 → True/False)
    relay_states: Dict[int, bool] = field(default_factory=dict)

    # ==================== PWM 상태 ====================
    # DC 모터 속도 (0~100%)
    motor_speed: float = 0.0
    # 서보 모터 각도 (0~180도)
    servo_angle: float = 0.0

    # ==================== 센서 값 ====================
    # 온도 (섭씨)
    temperature: Optional[float] = None
    # 습도 (%)
    humidity: Optional[float] = None
    # 기압 (hPa)
    pressure: Optional[float] = None
    # 고도 (미터)
    altitude: Optional[float] = None
    # 거리 (cm, 초음파 센서)
    distance: Optional[float] = None
    # 동작 감지 여부 (PIR 센서)
    motion: bool = False
    # 조도 (0~1023, LDR 센서)
    light_level: Optional[int] = None
    # 토양 수분 (0~1023)
    soil_moisture: Optional[int] = None

    # ==================== ADC 값 ====================
    # I2C ADC 값 (ADS1115, 채널별 전압)
    adc_values: Dict[int, float] = field(default_factory=dict)
    # SPI ADC 값 (MCP3008, 채널별 전압)
    spi_adc_values: Dict[int, float] = field(default_factory=dict)

    # ==================== 디스플레이 ====================
    # LCD에 표시 중인 내용 (줄별)
    lcd_content: List[str] = field(default_factory=list)

    # ==================== NeoPixel ====================
    # 각 LED의 색상 정보
    neopixel_colors: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """
        JSON 직렬화를 위해 딕셔너리로 변환
        Convert to dictionary for JSON serialization

        [한국어 설명]
        FastAPI에서 JSON으로 응답하기 위해 딕셔너리로 변환합니다.
        datetime 객체는 ISO 형식 문자열로 변환합니다.

        구조:
        {
            "timestamp": "2024-01-01T12:00:00",
            "gpio": { "leds": {...}, "buttons": {...}, ... },
            "pwm": { "motor_speed": 50.0, ... },
            "sensors": { "temperature": 25.5, ... },
            ...
        }

        Returns:
            Dict: API 응답용 딕셔너리
        """
        return {
            # ISO 형식 문자열로 변환 (예: "2024-01-01T12:00:00.123456")
            "timestamp": self.timestamp.isoformat(),

            # GPIO 관련 데이터 그룹핑
            "gpio": {
                "leds": self.led_states,
                "buttons": self.button_states,
                "relays": self.relay_states
            },

            # PWM 관련 데이터 그룹핑
            "pwm": {
                "motor_speed": self.motor_speed,
                "servo_angle": self.servo_angle
            },

            # 센서 관련 데이터 그룹핑
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

            # ADC 데이터 그룹핑
            "adc": {
                "i2c": self.adc_values,      # ADS1115 (I2C)
                "spi": self.spi_adc_values   # MCP3008 (SPI)
            },

            # 디스플레이 데이터
            "display": {
                "lcd_content": self.lcd_content
            },

            # NeoPixel 데이터
            "neopixel": {
                "colors": self.neopixel_colors
            }
        }


# ============================================================================
# 하드웨어 매니저 클래스 (Hardware Manager Class)
# ============================================================================

class HardwareManager:
    """
    중앙 하드웨어 관리 클래스 (Central hardware management class)

    [한국어 설명]
    모든 하드웨어 컨트롤러를 통합 관리하는 파사드(Facade) 패턴 구현.

    파사드 패턴이란?
    - 복잡한 하위 시스템을 단순한 인터페이스 뒤에 숨김
    - 외부에서는 HardwareManager의 메서드만 호출
    - 내부적으로 적절한 컨트롤러에 작업 위임

    주요 기능:
    - 통합 초기화/정리 (initialize, cleanup)
    - 백그라운드 데이터 수집 루프 (start_update_loop, stop_update_loop)
    - 데이터 변경 콜백 시스템 (register_callback, unregister_callback)
    - 편의 메서드 (set_led, set_motor_speed 등)

    Manages all hardware controllers and provides:
    - Unified initialization and cleanup
    - Background data collection
    - Event callbacks for data changes
    - Hardware status monitoring
    """

    def __init__(self):
        """
        하드웨어 매니저 초기화 (Initialize Hardware Manager)

        [한국어 설명]
        모든 하드웨어 컨트롤러를 생성하고 초기 상태를 설정합니다.
        실제 하드웨어 초기화는 initialize() 메서드에서 수행합니다.
        """
        # ==================== 시뮬레이션 모드 ====================
        # settings에서 시뮬레이션 모드 설정 가져오기
        self._simulation_mode = settings.SIMULATION_MODE

        # ==================== 상태 플래그 ====================
        # 초기화 완료 여부
        self._initialized = False

        # 백그라운드 루프 실행 중 여부
        self._running = False

        # ==================== 업데이트 관련 ====================
        # 데이터 수집 간격 (초)
        self._update_interval = settings.HARDWARE_UPDATE_INTERVAL

        # 백그라운드 업데이트 루프 태스크
        self._update_task: Optional[asyncio.Task] = None

        # ==================== 콜백 시스템 ====================
        # 데이터 변경 시 호출될 함수 목록
        # [한국어 설명]
        # Callable[[HardwareData], None]:
        # - HardwareData를 인자로 받고 None을 반환하는 함수 타입
        # 예: def on_data_change(data: HardwareData) -> None: ...
        self._callbacks: List[Callable[[HardwareData], None]] = []

        # ==================== 현재 데이터 ====================
        # 가장 최근 수집된 하드웨어 데이터
        self._current_data = HardwareData()

        # ==================== 컨트롤러 인스턴스 생성 ====================
        # [한국어 설명]
        # 각 컨트롤러는 동일한 시뮬레이션 모드 설정을 공유합니다.
        # 컨트롤러들은 아직 초기화되지 않음 (initialize 호출 필요)

        # GPIO 컨트롤러 (LED, 버튼, 릴레이)
        self.gpio = GPIOController(self._simulation_mode)

        # PWM 컨트롤러 (모터, 서보)
        self.pwm = PWMController(self._simulation_mode)

        # I2C 컨트롤러 (BMP280, ADS1115, OLED 등)
        self.i2c = I2CController(self._simulation_mode)

        # SPI 컨트롤러 (MCP3008)
        self.spi = SPIController(self._simulation_mode)

        # 센서 컨트롤러 (DHT, 초음파, PIR 등)
        self.sensors = SensorController(self._simulation_mode)

        # 디스플레이 컨트롤러 (OLED, LCD)
        self.display = DisplayController(self._simulation_mode)

        # NeoPixel 컨트롤러 (WS2812B LED)
        self.neopixel = NeopixelController(self._simulation_mode)

        # ==================== 컨트롤러 목록 ====================
        # 일괄 초기화/정리를 위한 리스트
        self._controllers = [
            self.gpio,
            self.pwm,
            self.i2c,
            self.spi,
            self.sensors,
            self.display,
            self.neopixel
        ]

    # ========================================================================
    # 속성 (Properties)
    # ========================================================================

    @property
    def is_simulation(self) -> bool:
        """
        시뮬레이션 모드 여부 확인 (Check if running in simulation mode)

        Returns:
            bool: True면 시뮬레이션 모드
        """
        return self._simulation_mode

    @property
    def is_initialized(self) -> bool:
        """
        초기화 완료 여부 확인 (Check if hardware is initialized)

        Returns:
            bool: True면 초기화 완료
        """
        return self._initialized

    @property
    def current_data(self) -> HardwareData:
        """
        현재 하드웨어 데이터 스냅샷 반환 (Get current hardware data snapshot)

        Returns:
            HardwareData: 가장 최근 수집된 데이터
        """
        return self._current_data

    # ========================================================================
    # 초기화 및 정리 (Initialization and Cleanup)
    # ========================================================================

    async def initialize(self) -> bool:
        """
        모든 하드웨어 컨트롤러 초기화 (Initialize all hardware controllers)

        [한국어 설명]
        asyncio.gather()를 사용하여 모든 컨트롤러를 병렬로 초기화합니다.
        일부 컨트롤러가 실패해도 다른 컨트롤러는 정상 동작합니다.

        asyncio.gather(*iterables, return_exceptions=True):
        - 여러 코루틴을 동시에 실행
        - return_exceptions=True: 예외 발생 시에도 계속 진행
        - 결과는 입력 순서대로 리스트로 반환

        Returns:
            bool: 모든 컨트롤러가 성공하면 True
        """
        logger.info(f"Initializing hardware manager (simulation={self._simulation_mode})")

        # 모든 컨트롤러 병렬 초기화
        # [한국어 설명]
        # *[...]: 리스트를 개별 인자로 풀어서 전달 (언패킹)
        # return_exceptions=True: 예외가 발생해도 다른 작업은 계속 진행
        results = await asyncio.gather(
            *[controller.initialize() for controller in self._controllers],
            return_exceptions=True
        )

        # 실패한 컨트롤러 확인
        failed = []
        for controller, result in zip(self._controllers, results):
            if isinstance(result, Exception):
                # 예외가 발생한 경우
                logger.error(f"{controller.name} failed: {result}")
                failed.append(controller.name)
            elif not result:
                # 초기화가 False를 반환한 경우
                failed.append(controller.name)

        # 실패한 컨트롤러가 있으면 경고 로깅
        if failed:
            logger.warning(f"Some controllers failed to initialize: {failed}")

        # 일부 실패해도 초기화 완료로 표시
        self._initialized = True

        # 모든 컨트롤러가 성공하면 True
        return len(failed) == 0

    async def cleanup(self) -> None:
        """
        모든 하드웨어 리소스 정리 (Clean up all hardware resources)

        [한국어 설명]
        애플리케이션 종료 시 호출됩니다.
        백그라운드 루프를 먼저 중지하고, 모든 컨트롤러를 정리합니다.
        """
        logger.info("Cleaning up hardware manager")

        # 백그라운드 업데이트 루프 중지
        await self.stop_update_loop()

        # 모든 컨트롤러 병렬 정리
        await asyncio.gather(
            *[controller.cleanup() for controller in self._controllers],
            return_exceptions=True  # 예외가 발생해도 모두 정리
        )

        self._initialized = False

    # ========================================================================
    # 백그라운드 업데이트 루프 (Background Update Loop)
    # ========================================================================

    async def start_update_loop(self) -> None:
        """
        백그라운드 업데이트 루프 시작 (Start the background update loop)

        [한국어 설명]
        주기적으로 모든 센서 데이터를 수집하는 백그라운드 태스크를 시작합니다.
        이미 실행 중이면 아무 것도 하지 않습니다.

        asyncio.create_task():
        - 코루틴을 백그라운드에서 실행하도록 예약
        - 메인 로직이 블로킹되지 않음
        """
        if self._running:
            return  # 이미 실행 중

        self._running = True
        # 백그라운드 태스크 생성
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("Hardware update loop started")

    async def stop_update_loop(self) -> None:
        """
        백그라운드 업데이트 루프 중지 (Stop the background update loop)

        [한국어 설명]
        실행 중인 백그라운드 태스크를 취소하고 완전히 종료될 때까지 대기합니다.
        """
        self._running = False

        if self._update_task:
            # 태스크 취소 요청
            self._update_task.cancel()
            try:
                # 태스크가 완전히 종료될 때까지 대기
                await self._update_task
            except asyncio.CancelledError:
                # 취소는 정상적인 종료
                pass
            self._update_task = None

        logger.info("Hardware update loop stopped")

    async def _update_loop(self) -> None:
        """
        하드웨어 데이터 수집 백그라운드 루프 (Background loop for collecting hardware data)

        [한국어 설명]
        무한 루프에서:
        1. 모든 센서/장치에서 데이터 수집
        2. 등록된 콜백 함수 호출
        3. 설정된 간격만큼 대기
        4. 반복

        예외 처리:
        - CancelledError: 루프 종료 (정상)
        - 기타 예외: 로그 기록 후 계속 실행
        """
        while self._running:
            try:
                # 데이터 수집
                await self._collect_data()

                # 콜백 함수 호출 (WebSocket 전송 등)
                await self._notify_callbacks()

            except asyncio.CancelledError:
                # 정상 종료
                break
            except Exception as e:
                # 오류 발생 시 로그 기록하고 계속 실행
                logger.error(f"Update loop error: {e}")

            # 다음 업데이트까지 대기
            await asyncio.sleep(self._update_interval)

    async def _collect_data(self) -> None:
        """
        모든 하드웨어 소스에서 데이터 수집 (Collect data from all hardware sources)

        [한국어 설명]
        각 컨트롤러에서 현재 상태를 읽어 HardwareData 객체에 저장합니다.
        센서 읽기는 비동기 메서드이므로 await로 호출합니다.
        """
        # 새 데이터 객체 생성 (현재 타임스탬프)
        data = HardwareData(timestamp=datetime.now())

        try:
            # ==================== GPIO 상태 ====================
            # 동기 메서드: 내부 상태만 반환하므로 빠름
            data.led_states = self.gpio.get_led_states()
            data.button_states = self.gpio.get_button_states()
            data.relay_states = self.gpio.get_relay_states()

            # ==================== PWM 상태 ====================
            data.motor_speed = self.pwm.get_motor_speed()
            data.servo_angle = self.pwm.get_servo_angle()

            # ==================== 센서 값 ====================
            # 비동기 메서드: 실제 하드웨어 읽기 필요

            # DHT 센서 (온도/습도)
            dht_data = await self.sensors.read_dht()
            if dht_data:
                data.temperature = dht_data.get("temperature")
                data.humidity = dht_data.get("humidity")

            # BMP280 센서 (기압/고도)
            bmp_data = await self.i2c.read_bmp280()
            if bmp_data:
                data.pressure = bmp_data.get("pressure")
                data.altitude = bmp_data.get("altitude")
                # DHT 온도가 없으면 BMP280 온도 사용
                if data.temperature is None:
                    data.temperature = bmp_data.get("temperature")

            # 초음파 센서 (거리)
            data.distance = await self.sensors.read_ultrasonic()

            # PIR 센서 (동작 감지)
            data.motion = await self.sensors.read_pir()

            # 조도 센서
            data.light_level = await self.sensors.read_light()

            # 토양 수분 센서
            data.soil_moisture = await self.sensors.read_soil_moisture()

            # ==================== ADC 값 ====================
            # I2C ADC (ADS1115)
            data.adc_values = await self.i2c.read_all_adc_channels()

            # SPI ADC (MCP3008)
            data.spi_adc_values = await self.spi.read_all_mcp3008_channels()

            # ==================== 디스플레이 ====================
            # LCD 현재 내용
            data.lcd_content = self.display.get_lcd_content()

            # ==================== NeoPixel ====================
            # 각 LED 색상
            data.neopixel_colors = self.neopixel.get_led_states()

            # 현재 데이터로 저장
            self._current_data = data

        except Exception as e:
            logger.error(f"Data collection error: {e}")

    async def _notify_callbacks(self) -> None:
        """
        등록된 콜백 함수에 새 데이터 알림 (Notify registered callbacks with new data)

        [한국어 설명]
        데이터 수집 후 등록된 모든 콜백 함수를 호출합니다.
        콜백은 동기 또는 비동기 함수일 수 있습니다.

        asyncio.iscoroutinefunction():
        - 함수가 async def로 정의된 비동기 함수인지 확인
        - 비동기 함수면 await로 호출
        - 동기 함수면 일반 호출
        """
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    # 비동기 콜백
                    await callback(self._current_data)
                else:
                    # 동기 콜백
                    callback(self._current_data)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    # ========================================================================
    # 콜백 관리 (Callback Management)
    # ========================================================================

    def register_callback(self, callback: Callable[[HardwareData], None]) -> None:
        """
        데이터 업데이트 콜백 등록 (Register a callback for data updates)

        [한국어 설명]
        데이터가 수집될 때마다 호출될 함수를 등록합니다.
        주로 WebSocket으로 클라이언트에 데이터 전송하는 데 사용됩니다.

        Args:
            callback: HardwareData를 인자로 받는 함수
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[HardwareData], None]) -> None:
        """
        데이터 업데이트 콜백 등록 해제 (Unregister a data update callback)

        Args:
            callback: 등록 해제할 콜백 함수
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    # ========================================================================
    # 상태 조회 (Status Query)
    # ========================================================================

    def get_status(self) -> Dict[str, Any]:
        """
        모든 하드웨어 컨트롤러 상태 반환 (Get status of all hardware controllers)

        [한국어 설명]
        시스템 전체 상태를 딕셔너리로 반환합니다.
        디버깅이나 상태 모니터링 페이지에서 사용됩니다.

        Returns:
            Dict: 전체 시스템 상태
        """
        return {
            "initialized": self._initialized,        # 초기화 완료 여부
            "simulation_mode": self._simulation_mode, # 시뮬레이션 모드 여부
            "update_interval": self._update_interval, # 업데이트 간격
            "running": self._running,                # 업데이트 루프 실행 중 여부
            "controllers": {
                # 각 컨트롤러의 상태를 딕셔너리로 변환
                controller.name: controller.status.to_dict()
                for controller in self._controllers
            }
        }

    def get_all_status(self) -> List[HardwareStatus]:
        """
        모든 컨트롤러의 상태 객체 목록 반환 (Get status objects for all controllers)

        Returns:
            List[HardwareStatus]: 컨트롤러 상태 객체 리스트
        """
        return [controller.status for controller in self._controllers]

    # ========================================================================
    # 편의 메서드 (Convenience Methods)
    # ========================================================================

    # [한국어 설명]
    # 아래 메서드들은 파사드 패턴의 핵심입니다.
    # 외부에서 복잡한 컨트롤러 구조를 알 필요 없이
    # 간단한 메서드 호출로 하드웨어를 제어할 수 있습니다.

    async def set_led(self, index: int, state: bool) -> bool:
        """
        LED 상태 설정 (Set LED state)

        Args:
            index: LED 인덱스 (0부터 시작)
            state: True면 켜기, False면 끄기

        Returns:
            bool: 성공 여부
        """
        return await self.gpio.set_led(index, state)

    async def set_relay(self, index: int, state: bool) -> bool:
        """
        릴레이 상태 설정 (Set relay state)

        Args:
            index: 릴레이 인덱스
            state: True면 켜기, False면 끄기

        Returns:
            bool: 성공 여부
        """
        return await self.gpio.set_relay(index, state)

    async def set_motor_speed(self, speed: float) -> bool:
        """
        모터 속도 설정 (Set motor speed)

        Args:
            speed: 속도 (0~100%)

        Returns:
            bool: 성공 여부
        """
        return await self.pwm.set_motor_speed(speed)

    async def set_servo_angle(self, angle: float) -> bool:
        """
        서보 각도 설정 (Set servo angle)

        Args:
            angle: 각도 (0~180도)

        Returns:
            bool: 성공 여부
        """
        return await self.pwm.set_servo_angle(angle)

    async def lcd_write(self, text: str, row: int = 0) -> bool:
        """
        LCD에 텍스트 쓰기 (Write text to LCD)

        Args:
            text: 표시할 텍스트
            row: 행 번호 (0부터 시작)

        Returns:
            bool: 성공 여부
        """
        return await self.display.lcd_write(text, row)

    async def set_neopixel_color(self, index: int, color: str) -> bool:
        """
        NeoPixel LED 색상 설정 (Set NeoPixel LED color)

        [한국어 설명]
        색상 이름 ("red", "blue" 등) 또는 HEX 코드 ("#FF0000")를 받습니다.

        Args:
            index: LED 인덱스
            color: 색상 이름 또는 HEX 코드

        Returns:
            bool: 성공 여부
        """
        # 순환 임포트 방지를 위해 여기서 임포트
        from .neopixel_controller import COLORS, RGBColor

        if color in COLORS:
            # 미리 정의된 색상 이름
            return await self.neopixel.set_pixel(index, COLORS[color])
        elif color.startswith("#"):
            # HEX 색상 코드
            return await self.neopixel.set_pixel(index, RGBColor.from_hex(color))
        return False

    async def start_neopixel_effect(self, effect: str) -> bool:
        """
        NeoPixel 이펙트 시작 (Start NeoPixel effect)

        Args:
            effect: 이펙트 이름 ("rainbow", "breathing" 등)

        Returns:
            bool: 성공 여부
        """
        from .neopixel_controller import NeopixelEffect

        try:
            # 문자열을 Enum으로 변환
            effect_enum = NeopixelEffect(effect)
            return await self.neopixel.start_effect(effect_enum)
        except ValueError:
            # 잘못된 이펙트 이름
            return False


# ============================================================================
# 전역 하드웨어 매니저 인스턴스 (Global Hardware Manager Instance)
# ============================================================================

# [한국어 설명]
# 싱글톤 패턴: 애플리케이션 전체에서 하나의 인스턴스만 사용
# 다른 모듈에서: from app.hardware.manager import hardware_manager
hardware_manager = HardwareManager()
