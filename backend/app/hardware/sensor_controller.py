"""
Sensor Controller (센서 컨트롤러)
=================================

[한국어 설명]
다양한 센서들을 통합 관리하는 모듈입니다.

지원하는 센서:
1. **DHT11/DHT22**: 온도 및 습도 센서
   - 디지털 원 와이어(1-Wire) 통신
   - DHT11: 저정밀 (±2°C, ±5%RH)
   - DHT22: 고정밀 (±0.5°C, ±2%RH)

2. **HC-SR04**: 초음파 거리 센서
   - 2~400cm 측정 범위
   - 초음파 반사 시간으로 거리 계산

3. **PIR**: 적외선 모션 감지 센서
   - 인체에서 방출되는 적외선 감지
   - 움직임 감지 시 HIGH 출력

4. **LDR**: 조도 센서 (광저항)
   - 빛의 양에 따라 저항값 변화
   - ADC를 통해 읽음 (아날로그 → 디지털)

5. **토양 습도 센서**: 흙의 수분 측정
   - 전극 사이의 저항으로 측정
   - ADC를 통해 읽음

센서 읽기 비동기화:
- 센서 읽기는 블로킹 작업 (완료될 때까지 대기)
- asyncio.to_thread()로 스레드 풀에서 실행
- 이벤트 루프가 멈추지 않음

[English Description]
Unified interface for various sensors including temperature, humidity,
distance, motion, light, and soil moisture sensors.
"""

# ============================================================================
# 라이브러리 임포트 (Import Libraries)
# ============================================================================

# asyncio: 비동기 프로그래밍 모듈
import asyncio

# random: 랜덤 값 생성 (시뮬레이션용)
import random

# typing: 타입 힌트용 모듈
from typing import Dict, Optional, Any

# dataclasses: 데이터 클래스 정의
from dataclasses import dataclass

# datetime: 날짜/시간 처리
from datetime import datetime

# enum: 열거형 정의
from enum import Enum

# 베이스 클래스와 시뮬레이션 믹스인 임포트
from .base import BaseHardwareController, SimulationMixin

# 설정 값 가져오기
from app.core.config import settings

# 로거 가져오기
from app.core.logging_config import get_logger

# 이 모듈용 로거 생성
logger = get_logger(__name__)


# ============================================================================
# 센서 타입 열거형 (Sensor Type Enum)
# ============================================================================

class SensorType(Enum):
    """
    센서 종류 (Types of Sensors)

    [한국어 설명]
    지원하는 센서의 종류를 정의합니다.

    각 센서별 특성:
    - DHT11: 저가형 온습도 센서, 정밀도 낮음
    - DHT22: 고정밀 온습도 센서, 가격 높음
    - ULTRASONIC: 초음파 거리 센서 (HC-SR04)
    - PIR: 적외선 모션 센서
    - LIGHT: 조도 센서 (LDR - Light Dependent Resistor)
    - SOIL_MOISTURE: 토양 습도 센서
    """
    DHT11 = "DHT11"              # 저정밀 온습도 센서
    DHT22 = "DHT22"              # 고정밀 온습도 센서
    ULTRASONIC = "HC-SR04"       # 초음파 거리 센서
    PIR = "PIR"                  # 적외선 모션 센서
    LIGHT = "LDR"                # 조도 센서
    SOIL_MOISTURE = "SOIL"       # 토양 습도 센서


# ============================================================================
# 센서 읽기 데이터 클래스 (Sensor Reading Dataclass)
# ============================================================================

@dataclass
class SensorReading:
    """
    센서 읽기 결과 (Sensor Reading Result)

    [한국어 설명]
    센서에서 읽은 데이터를 저장하는 데이터 클래스입니다.

    Attributes:
        sensor_type: 센서 종류
        value: 측정값 (숫자, 불린 등)
        unit: 단위 (°C, %, cm 등)
        timestamp: 측정 시간

    __post_init__:
    - __init__ 호출 후 자동으로 실행되는 메서드
    - timestamp가 None이면 현재 시간으로 설정
    """
    sensor_type: SensorType     # 센서 종류
    value: Any                  # 측정값
    unit: str                   # 단위
    timestamp: datetime = None  # 측정 시간

    def __post_init__(self):
        """
        초기화 후처리 (Post Initialization)

        @dataclass의 __post_init__은 __init__ 호출 후 자동 실행됩니다.
        """
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (Convert to Dictionary)"""
        return {
            "sensor_type": self.sensor_type.value,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat()
        }


# ============================================================================
# 센서 컨트롤러 클래스 (Sensor Controller Class)
# ============================================================================

class SensorController(BaseHardwareController, SimulationMixin):
    """
    다양한 센서를 위한 컨트롤러 (Controller for Various Sensors)

    [한국어 설명]
    여러 종류의 센서를 통합 관리합니다.

    지원 센서:
    - DHT11/DHT22: 온도와 습도
    - HC-SR04: 초음파 거리
    - PIR: 모션 감지
    - LDR: 조도
    - 토양 습도 센서

    시뮬레이션 모드 동작:
    - 현실적인 가짜 데이터 생성
    - 노이즈 추가로 자연스러운 변화
    - 드리프트로 점진적 값 변화
    - 수동 설정 시 자동 드리프트 비활성화 (Settings 페이지에서 설정한 값 유지)
    """

    def __init__(self, simulation_mode: bool = False):
        """
        생성자 (Constructor)

        Args:
            simulation_mode: 시뮬레이션 모드 여부
        """
        # 부모 클래스 초기화
        super().__init__("Sensor Controller", simulation_mode)

        # DHT 센서 설정
        self._dht_pin = settings.DHT_PIN        # DHT 데이터 핀 (예: GPIO 4)
        self._dht_type = settings.DHT_TYPE      # 센서 타입 ("DHT11" 또는 "DHT22")
        self._dht_sensor = None                 # DHT 센서 객체 (실제 하드웨어용)

        # 시뮬레이션 센서 값
        # [한국어] 시뮬레이션 모드에서 반환할 가짜 데이터
        self._simulated_values: Dict[str, Any] = {
            "temperature": 25.0,    # 온도 (°C)
            "humidity": 50.0,       # 습도 (%)
            "distance": 100.0,      # 거리 (cm)
            "motion": False,        # 움직임 감지
            "light": 500,           # 조도 (0-1023)
            "soil_moisture": 600    # 토양 습도 (0-1023)
        }

        # 수동 설정 추적
        # [한국어] True면 해당 값의 자동 드리프트 비활성화
        # 사용자가 Settings 페이지에서 값을 직접 설정하면 True로 변경됨
        self._manually_set: Dict[str, bool] = {
            "temperature": False,
            "humidity": False,
            "distance": False,
            "motion": False,
            "light": False,
            "soil_moisture": False
        }

        # 초음파 센서 핀 (Ultrasonic Sensor Pins)
        self._ultrasonic_trigger = 23  # 트리거 핀 (초음파 송신)
        self._ultrasonic_echo = 24     # 에코 핀 (초음파 수신)

        # PIR 모션 센서 핀
        self._pir_pin = 25

        # ADC 채널 (MCP3008 또는 ADS1115 사용 시)
        self._light_pin = 0        # 조도 센서가 연결된 ADC 채널
        self._soil_pin = 1         # 토양 습도 센서가 연결된 ADC 채널

    async def _do_initialize(self) -> bool:
        """
        센서 초기화 (Initialize Sensors)

        [한국어 설명]
        DHT 센서와 기타 센서들을 초기화합니다.

        DHT 센서 라이브러리:
        - adafruit_dht: Adafruit에서 제공하는 DHT 라이브러리
        - board: 라즈베리 파이 핀 정의 모듈

        Returns:
            True: 초기화 성공
            False: 초기화 실패
        """
        try:
            # 시뮬레이션 모드가 아닐 때만 실제 센서 초기화
            if not self.simulation_mode:
                try:
                    # Adafruit DHT 라이브러리 임포트
                    import adafruit_dht
                    import board

                    # board.D4 → GPIO 4를 의미
                    # getattr(board, f"D{pin}"): 동적으로 핀 가져오기
                    pin = getattr(board, f"D{self._dht_pin}")

                    # 센서 타입에 따라 적절한 클래스 사용
                    if self._dht_type == "DHT22":
                        self._dht_sensor = adafruit_dht.DHT22(pin)
                    else:
                        self._dht_sensor = adafruit_dht.DHT11(pin)

                except ImportError:
                    # 라이브러리가 없으면 시뮬레이션으로 전환
                    logger.warning("DHT library not available, falling back to simulation")
                    self.simulation_mode = True
                except Exception as e:
                    logger.warning(f"DHT sensor init failed: {e}")
                    self.simulation_mode = True

            return True

        except Exception as e:
            logger.error(f"Sensor initialization failed: {e}")
            return False

    async def _do_cleanup(self) -> None:
        """
        센서 리소스 정리 (Clean up Sensor Resources)

        [한국어 설명]
        DHT 센서의 리소스를 해제합니다.
        exit() 메서드로 센서 연결을 정리합니다.
        """
        if self._dht_sensor:
            try:
                # DHT 센서 정리
                self._dht_sensor.exit()
            except:
                pass  # 정리 실패는 무시
            self._dht_sensor = None

    # ==================== DHT 온습도 센서 (DHT Temperature/Humidity) ====================

    async def read_dht(self) -> Optional[Dict[str, float]]:
        """
        DHT 센서에서 온도와 습도 읽기 (Read Temperature and Humidity from DHT)
        비블로킹 (Non-blocking) 방식

        [한국어 설명]
        DHT11/DHT22 센서에서 온도와 습도 데이터를 읽습니다.

        DHT 센서 동작 원리:
        1. MCU가 시작 신호 전송 (LOW 18ms)
        2. 센서가 응답 신호 전송
        3. 40비트 데이터 전송:
           - 16비트: 습도 정수/소수부
           - 16비트: 온도 정수/소수부
           - 8비트: 체크섬

        시뮬레이션 모드:
        - _simulate_drift(): 목표값으로 천천히 이동
        - _simulate_noise(): 랜덤 변화 추가
        - _manually_set이 True면 드리프트 비활성화

        Returns:
            {"temperature": 온도(°C), "humidity": 습도(%)} 또는 None
        """
        try:
            if self.simulation_mode:
                # 시뮬레이션: 50-100ms 지연 (실제 DHT 읽기 시간과 유사)
                await asyncio.sleep(self._simulate_delay(50, 100))

                # 수동 설정되지 않은 값만 드리프트 적용
                if not self._manually_set.get("temperature", False):
                    # 온도를 25°C ± 2°C 범위에서 드리프트
                    self._simulated_values["temperature"] = self._simulate_drift(
                        self._simulated_values["temperature"],
                        25.0 + random.uniform(-2, 2),  # 목표값: 23~27°C
                        0.1  # 드리프트 속도 10%
                    )
                if not self._manually_set.get("humidity", False):
                    # 습도를 50% ± 5% 범위에서 드리프트
                    self._simulated_values["humidity"] = self._simulate_drift(
                        self._simulated_values["humidity"],
                        50.0 + random.uniform(-5, 5),  # 목표값: 45~55%
                        0.1
                    )

                # 노이즈 추가 후 반환
                return {
                    "temperature": round(self._simulate_noise(
                        self._simulated_values["temperature"], 0.5  # 0.5% 노이즈
                    ), 1),
                    "humidity": round(self._simulate_noise(
                        self._simulated_values["humidity"], 1.0  # 1% 노이즈
                    ), 1)
                }
            else:
                # 실제 하드웨어: 블로킹 DHT 읽기를 스레드 풀에서 실행
                return await asyncio.to_thread(self._read_dht_sync)

        except Exception as e:
            logger.error(f"DHT read error: {e}")
            return None

    def _read_dht_sync(self) -> Optional[Dict[str, float]]:
        """
        동기 DHT 읽기 (Synchronous DHT Read with Retry)
        스레드 풀에서 실행됨

        [한국어 설명]
        실제 DHT 센서 읽기는 블로킹 작업입니다.
        asyncio.to_thread()에 의해 스레드 풀에서 실행됩니다.

        재시도 로직:
        - DHT 센서는 간헐적으로 읽기 실패할 수 있음
        - 최대 3번 재시도
        - 실패 시 100ms 대기

        Returns:
            {"temperature": 온도, "humidity": 습도} 또는 None
        """
        import time

        # 최대 3번 재시도
        for _ in range(3):
            try:
                # DHT 센서에서 값 읽기
                temperature = self._dht_sensor.temperature
                humidity = self._dht_sensor.humidity

                # 둘 다 유효한 값인지 확인
                if temperature is not None and humidity is not None:
                    return {
                        "temperature": round(temperature, 1),
                        "humidity": round(humidity, 1)
                    }
            except RuntimeError:
                # DHT 읽기 실패 시 재시도
                time.sleep(0.1)

        return None

    async def get_temperature(self) -> Optional[float]:
        """
        온도만 가져오기 (Get Current Temperature)

        Returns:
            온도 (°C) 또는 None
        """
        data = await self.read_dht()
        return data["temperature"] if data else None

    async def get_humidity(self) -> Optional[float]:
        """
        습도만 가져오기 (Get Current Humidity)

        Returns:
            습도 (%) 또는 None
        """
        data = await self.read_dht()
        return data["humidity"] if data else None

    # ==================== 초음파 거리 센서 (Ultrasonic Distance) ====================

    async def read_ultrasonic(self) -> Optional[float]:
        """
        HC-SR04 초음파 센서에서 거리 읽기 (Read Distance from Ultrasonic Sensor)
        비블로킹 (Non-blocking) 방식

        [한국어 설명]
        초음파 센서 동작 원리:
        1. 트리거 핀에 10μs HIGH 펄스 전송
        2. 센서가 8개의 40kHz 초음파 버스트 송신
        3. 초음파가 물체에 반사되어 돌아옴
        4. 에코 핀이 HIGH로 변하는 시간 측정

        거리 계산:
        - 음속 = 343m/s = 34,300cm/s
        - 왕복 시간이므로 2로 나눔
        - 거리 = (시간 × 34,300) / 2 cm

        Returns:
            거리 (cm) 또는 None
        """
        try:
            if self.simulation_mode:
                # 시뮬레이션: 20-50ms 지연
                await asyncio.sleep(self._simulate_delay(20, 50))

                # 수동 설정되지 않은 경우만 드리프트
                if not self._manually_set.get("distance", False):
                    self._simulated_values["distance"] = self._simulate_drift(
                        self._simulated_values["distance"],
                        100.0 + random.uniform(-20, 20),  # 80~120cm 범위
                        0.2  # 빠른 변화
                    )

                # 노이즈 추가 (2%)
                return round(self._simulate_noise(
                    self._simulated_values["distance"], 2.0
                ), 1)
            else:
                # 실제 하드웨어: 스레드 풀에서 측정
                return await asyncio.to_thread(self._read_ultrasonic_sync)

        except Exception as e:
            logger.error(f"Ultrasonic read error: {e}")
            return None

    def _read_ultrasonic_sync(self) -> Optional[float]:
        """
        동기 초음파 측정 (Synchronous Ultrasonic Measurement)
        스레드 풀에서 실행됨

        [한국어 설명]
        실제 초음파 센서 측정은 정밀한 타이밍이 필요합니다.
        time.time()으로 마이크로초 단위 측정을 합니다.

        타임아웃:
        - 에코 신호가 100ms 이내에 오지 않으면 실패
        - 물체가 너무 멀거나 없는 경우

        Returns:
            거리 (cm) 또는 None (측정 실패 시)
        """
        import RPi.GPIO as GPIO
        import time

        # 핀 설정
        GPIO.setup(self._ultrasonic_trigger, GPIO.OUT)
        GPIO.setup(self._ultrasonic_echo, GPIO.IN)

        # 트리거 펄스 전송 (10μs HIGH)
        GPIO.output(self._ultrasonic_trigger, True)
        time.sleep(0.00001)  # 10μs = 10 마이크로초
        GPIO.output(self._ultrasonic_trigger, False)

        # 에코 시작/종료 시간 측정 변수 초기화
        start_time = time.time()
        stop_time = time.time()

        # 에코 시작 대기 (LOW → HIGH 전환)
        while GPIO.input(self._ultrasonic_echo) == 0:
            start_time = time.time()
            # 타임아웃 체크 (100ms)
            if start_time - stop_time > 0.1:
                return None

        # 에코 종료 대기 (HIGH → LOW 전환)
        while GPIO.input(self._ultrasonic_echo) == 1:
            stop_time = time.time()
            # 타임아웃 체크
            if stop_time - start_time > 0.1:
                return None

        # 거리 계산: (시간 × 음속) / 2
        elapsed = stop_time - start_time
        distance = (elapsed * 34300) / 2  # cm

        # 유효 범위 체크 (2-400cm), 범위 밖이면 None
        return round(distance, 1) if distance < 400 else None

    # ==================== PIR 모션 감지 (PIR Motion Detection) ====================

    async def read_pir(self) -> bool:
        """
        PIR 센서에서 모션 상태 읽기 (Read Motion Status from PIR Sensor)
        비블로킹 (Non-blocking) 방식

        [한국어 설명]
        PIR (Passive Infrared) 센서 동작:
        - 인체에서 방출되는 적외선(체온)을 감지
        - 움직임이 감지되면 HIGH 출력
        - 정지 상태면 LOW 출력

        센서 조정 (하드웨어):
        - 감도(Sensitivity): 감지 거리 조절 (가변저항)
        - 시간(Time Delay): HIGH 유지 시간 조절

        Returns:
            True: 움직임 감지됨
            False: 움직임 없음
        """
        try:
            if self.simulation_mode:
                await asyncio.sleep(self._simulate_delay())

                # 수동 설정되지 않은 경우만 랜덤 변화
                if not self._manually_set.get("motion", False):
                    # 5% 확률로 상태 토글 (랜덤 시뮬레이션)
                    if random.random() < 0.05:
                        self._simulated_values["motion"] = not self._simulated_values["motion"]

                return self._simulated_values["motion"]
            else:
                # 실제 하드웨어: GPIO 읽기를 스레드 풀에서 실행
                return await asyncio.to_thread(self._read_pir_sync)

        except Exception as e:
            logger.error(f"PIR read error: {e}")
            return False

    def _read_pir_sync(self) -> bool:
        """
        동기 PIR 읽기 (Synchronous PIR Read)
        스레드 풀에서 실행됨

        Returns:
            True: 움직임 감지됨
            False: 움직임 없음
        """
        import RPi.GPIO as GPIO
        GPIO.setup(self._pir_pin, GPIO.IN)
        return GPIO.input(self._pir_pin) == 1

    # ==================== 조도 센서 (Light Sensor - LDR) ====================

    async def read_light(self) -> Optional[int]:
        """
        LDR에서 조도 읽기 (Read Light Level from LDR via ADC)

        [한국어 설명]
        LDR (Light Dependent Resistor, 광저항):
        - 빛이 많으면 저항이 낮아짐
        - 빛이 적으면 저항이 높아짐

        ADC (Analog-to-Digital Converter):
        - 라즈베리 파이는 아날로그 입력 불가
        - MCP3008 같은 외부 ADC 필요
        - 10비트 해상도: 0-1023 값

        Returns:
            조도 (0-1023, 높을수록 밝음) 또는 None
        """
        try:
            if self.simulation_mode:
                await asyncio.sleep(self._simulate_delay())

                # 수동 설정되지 않은 경우만 드리프트
                if not self._manually_set.get("light", False):
                    self._simulated_values["light"] = self._simulate_drift(
                        self._simulated_values["light"],
                        500 + random.uniform(-100, 100),  # 400~600 범위
                        0.1
                    )

                return int(self._simulate_noise(self._simulated_values["light"], 3.0))
            else:
                # 실제 구현: MCP3008 또는 ADS1115 사용 필요
                # 여기서는 플레이스홀더 값 반환
                return 500

        except Exception as e:
            logger.error(f"Light sensor read error: {e}")
            return None

    # ==================== 토양 습도 (Soil Moisture) ====================

    async def read_soil_moisture(self) -> Optional[int]:
        """
        토양 습도 읽기 (Read Soil Moisture Level via ADC)

        [한국어 설명]
        토양 습도 센서 동작:
        - 두 전극 사이의 저항을 측정
        - 물이 많으면 저항이 낮아짐 (전도성 증가)
        - 건조하면 저항이 높아짐

        값 해석 (일반적인 기준):
        - 0-300: 건조 (물 필요)
        - 300-700: 습함 (적정)
        - 700-1023: 매우 습함 (물 과다)

        Returns:
            토양 습도 (0-1023, 높을수록 습함) 또는 None
        """
        try:
            if self.simulation_mode:
                await asyncio.sleep(self._simulate_delay())

                # 수동 설정되지 않은 경우만 드리프트
                if not self._manually_set.get("soil_moisture", False):
                    self._simulated_values["soil_moisture"] = self._simulate_drift(
                        self._simulated_values["soil_moisture"],
                        600 + random.uniform(-50, 50),  # 550~650 범위
                        0.05  # 느린 변화 (토양은 천천히 마름)
                    )

                return int(self._simulate_noise(
                    self._simulated_values["soil_moisture"], 2.0
                ))
            else:
                # 실제 구현: MCP3008 사용 필요
                return 600

        except Exception as e:
            logger.error(f"Soil moisture read error: {e}")
            return None

    # ==================== 모든 센서 읽기 (Read All Sensors) ====================

    async def read_all(self) -> Dict[str, Any]:
        """
        모든 센서 동시 읽기 (Read All Available Sensors Concurrently)

        [한국어 설명]
        asyncio.create_task()를 사용하여 모든 센서를 병렬로 읽습니다.

        병렬 실행의 장점:
        - 순차 실행: 5개 센서 × 50ms = 250ms
        - 병렬 실행: 가장 느린 센서 시간 ≈ 50-100ms

        asyncio.create_task():
        - 코루틴을 태스크로 스케줄링 (백그라운드 실행)
        - 즉시 반환됨 (비동기)
        - await로 결과 대기

        Returns:
            모든 센서 데이터가 담긴 딕셔너리
            예: {"temperature": 25.0, "humidity": 50.0, "distance": 100.0, ...}
        """
        results = {}

        # 모든 센서 읽기 태스크 생성 및 병렬 시작
        dht_task = asyncio.create_task(self.read_dht())
        distance_task = asyncio.create_task(self.read_ultrasonic())
        motion_task = asyncio.create_task(self.read_pir())
        light_task = asyncio.create_task(self.read_light())
        soil_task = asyncio.create_task(self.read_soil_moisture())

        # DHT 데이터 대기 및 결과 저장
        dht_data = await dht_task
        if dht_data:
            results["temperature"] = dht_data["temperature"]
            results["humidity"] = dht_data["humidity"]

        # 나머지 센서 결과 대기
        results["distance"] = await distance_task
        results["motion"] = await motion_task
        results["light"] = await light_task
        results["soil_moisture"] = await soil_task

        # 마지막 업데이트 시간 갱신
        self._update_timestamp()

        return results

    def set_simulated_values(self, **kwargs) -> None:
        """
        시뮬레이션 센서 값 설정 (Set Simulated Sensor Values)
        수동 설정으로 표시하여 자동 드리프트 비활성화

        [한국어 설명]
        Settings 페이지에서 시뮬레이션 값을 수동으로 설정할 때 사용합니다.
        설정된 값은 자동 드리프트가 적용되지 않습니다.

        **kwargs: Python의 키워드 인자 수집
        - 여러 개의 키-값 쌍을 딕셔너리로 받음

        Args:
            **kwargs: 설정할 센서 값들
                - temperature: 온도 (°C)
                - humidity: 습도 (%)
                - distance: 거리 (cm)
                - motion: 움직임 (bool)
                - light: 조도 (0-1023)
                - soil_moisture: 토양 습도 (0-1023)

        사용 예시:
            controller.set_simulated_values(
                temperature=30.0,
                humidity=60.0
            )
        """
        for key, value in kwargs.items():
            if key in self._simulated_values:
                self._simulated_values[key] = value
                self._manually_set[key] = True  # 수동 설정 표시 → 드리프트 비활성화

    def _get_status_details(self) -> Dict[str, Any]:
        """
        센서 상세 상태 정보 (Get Sensor-specific Status Details)

        Returns:
            상세 정보 딕셔너리
        """
        return {
            "dht_pin": self._dht_pin,
            "dht_type": self._dht_type,
            "ultrasonic_pins": {
                "trigger": self._ultrasonic_trigger,
                "echo": self._ultrasonic_echo
            },
            "pir_pin": self._pir_pin,
            "simulated_values": self._simulated_values if self.simulation_mode else None
        }
