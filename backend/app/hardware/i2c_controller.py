"""
I2C Controller (I2C 컨트롤러)
=============================

[한국어 설명]
I2C(Inter-Integrated Circuit) 장치를 제어하는 컨트롤러입니다.
I2C는 2선 통신 프로토콜로, 하나의 버스에 여러 장치를 연결할 수 있습니다.

I2C 통신의 특징:
- SDA(데이터)와 SCL(클록) 2개의 선만 사용
- 마스터-슬레이브 구조 (라즈베리 파이가 마스터)
- 각 장치는 고유한 주소(7비트)를 가짐
- 최대 112개 장치 연결 가능 (0x03~0x77)

지원 장치:
- BMP280: 기압/온도 센서
- ADS1115: 16비트 ADC (아날로그-디지털 변환기)
- OLED 디스플레이: SSD1306 등
- LCD 디스플레이: I2C 백팩 사용

라즈베리 파이의 I2C 핀:
- GPIO 2 (SDA) - 데이터 라인
- GPIO 3 (SCL) - 클록 라인

[English Description]
Controller for I2C (Inter-Integrated Circuit) devices.
Supports multiple devices on the I2C bus including sensors, displays, and ADCs.
"""

# ============================================================================
# 라이브러리 임포트 (Import Libraries)
# ============================================================================

# asyncio: 비동기 I/O 처리를 위한 Python 표준 라이브러리
# I2C 통신은 기본적으로 블로킹(blocking)이므로 asyncio.to_thread로 비동기 처리
import asyncio

# typing: 타입 힌트를 위한 모듈
# Dict: 딕셔너리 타입 힌트
# List: 리스트 타입 힌트
# Optional: None이 될 수 있는 타입
# Any: 어떤 타입이든 허용
# Tuple: 튜플 타입 힌트
from typing import Dict, List, Optional, Any, Tuple

# dataclass: 데이터 저장 클래스를 간편하게 정의
# @dataclass 데코레이터를 사용하면 __init__, __repr__ 등이 자동 생성됨
from dataclasses import dataclass

# base: 이 프로젝트의 하드웨어 컨트롤러 기본 클래스
# BaseHardwareController: 모든 하드웨어 컨트롤러의 추상 기본 클래스
# SimulationMixin: 시뮬레이션 기능을 제공하는 믹스인 클래스
from .base import BaseHardwareController, SimulationMixin

# settings: 애플리케이션 설정 (I2C 주소, 버스 번호 등)
from app.core.config import settings

# get_logger: 로깅을 위한 함수
from app.core.logging_config import get_logger

# 이 모듈 전용 로거 생성
# __name__은 현재 모듈 이름 (app.hardware.i2c_controller)
logger = get_logger(__name__)


# ============================================================================
# I2C 장치 데이터 클래스 (I2C Device Data Class)
# ============================================================================

@dataclass
class I2CDevice:
    """
    I2C 장치 정보를 저장하는 데이터 클래스 (Represents an I2C device)

    [한국어 설명]
    @dataclass 데코레이터로 인해 자동으로 생성되는 메서드:
    - __init__(): 생성자 (address, name 등을 인자로 받음)
    - __repr__(): 객체의 문자열 표현
    - __eq__(): 동등성 비교

    속성 설명:
    - address: I2C 장치의 7비트 주소 (0x03 ~ 0x77)
        - 예: 0x27 = 39, 0x3C = 60, 0x76 = 118
    - name: 장치 이름 (사람이 읽기 위한 용도)
    - is_connected: 장치 연결 상태
    - last_data: 마지막으로 읽은 데이터 (바이트 형태)
    """
    address: int                        # I2C 주소 (7비트, 정수)
    name: str                           # 장치 이름 (문자열)
    is_connected: bool = False          # 연결 상태 (기본값: False)
    last_data: Optional[bytes] = None   # 마지막 데이터 (옵션)


# ============================================================================
# I2C 컨트롤러 클래스 (I2C Controller Class)
# ============================================================================

class I2CController(BaseHardwareController, SimulationMixin):
    """
    I2C 통신 컨트롤러 (Controller for I2C operations)

    [한국어 설명]
    다중 상속 구조:
    - BaseHardwareController: 초기화/정리/상태 관리 기능
    - SimulationMixin: 시뮬레이션 모드 유틸리티 (노이즈, 지연 등)

    Python 다중 상속과 MRO(Method Resolution Order):
    class A(B, C)일 때, 메서드 검색 순서는 A → B → C
    super().__init__()은 MRO에 따라 B의 __init__을 호출

    주요 기능:
    - I2C 버스 스캔 및 장치 탐지
    - 바이트/블록 단위 읽기/쓰기
    - BMP280 센서 데이터 읽기
    - ADS1115 ADC 값 읽기

    Features:
    - Device scanning
    - Read/Write operations
    - Support for BMP280, ADS1115, OLED displays
    """

    def __init__(self, simulation_mode: bool = False):
        """
        I2C 컨트롤러 초기화 (Initialize I2C Controller)

        [한국어 설명]
        Args:
            simulation_mode: 시뮬레이션 모드 여부
                - True: 실제 하드웨어 없이 가짜 데이터 사용
                - False: 실제 I2C 하드웨어 사용

        super().__init__() 호출:
        - BaseHardwareController의 __init__에 컨트롤러 이름 전달
        - _state, _status, _lock 등 기본 속성 초기화됨
        """
        # 부모 클래스 초기화 (컨트롤러 이름과 시뮬레이션 모드 전달)
        super().__init__("I2C Controller", simulation_mode)

        # I2C 버스 객체 (smbus2.SMBus 인스턴스가 저장됨)
        # 초기에는 None, initialize() 시 생성
        self._bus = None

        # I2C 버스 번호 (라즈베리 파이는 보통 버스 1 사용)
        # /dev/i2c-1에 해당
        self._bus_number = settings.I2C_BUS

        # 감지된 I2C 장치들을 저장하는 딕셔너리
        # 키: I2C 주소 (int), 값: I2CDevice 객체
        self._devices: Dict[int, I2CDevice] = {}

        # 시뮬레이션용 가짜 데이터 저장소
        # 키: I2C 주소 (int), 값: 센서 데이터 딕셔너리
        self._simulated_data: Dict[int, Dict[str, Any]] = {}

        # 알려진 I2C 장치 주소와 이름 매핑
        # [한국어 설명]
        # 일반적인 I2C 장치 주소:
        # - 0x27: LCD 디스플레이 (PCF8574 I2C 확장기)
        # - 0x3C: OLED 디스플레이 (SSD1306)
        # - 0x76 또는 0x77: BMP280 기압/온도 센서
        # - 0x48: ADS1115 16비트 ADC
        self._known_devices = {
            settings.I2C_LCD_ADDRESS: "LCD Display",     # LCD 디스플레이
            settings.I2C_OLED_ADDRESS: "OLED Display",   # OLED 디스플레이
            settings.I2C_BMP280_ADDRESS: "BMP280 Sensor", # 기압/온도 센서
            settings.I2C_ADS1115_ADDRESS: "ADS1115 ADC"   # 아날로그-디지털 변환기
        }

    # ========================================================================
    # 초기화 및 정리 메서드 (Initialization and Cleanup Methods)
    # ========================================================================

    async def _do_initialize(self) -> bool:
        """
        I2C 버스 초기화 (Initialize I2C bus)

        [한국어 설명]
        BaseHardwareController의 추상 메서드 구현.
        initialize() 호출 시 내부적으로 이 메서드가 실행됨.

        초기화 과정:
        1. smbus2 라이브러리 임포트 시도
        2. I2C 버스 열기
        3. 실패 시 시뮬레이션 모드로 전환
        4. 시뮬레이션 데이터 초기화
        5. 장치 스캔 실행

        smbus2 라이브러리:
        - 라즈베리 파이에서 I2C 통신을 위한 Python 라이브러리
        - pip install smbus2로 설치
        - 윈도우에서는 설치 불가 → 시뮬레이션 모드 사용

        Returns:
            bool: 초기화 성공 여부
        """
        try:
            if not self.simulation_mode:
                try:
                    # smbus2 라이브러리 동적 임포트
                    # [한국어 설명]
                    # 모듈 상단에서 import하지 않는 이유:
                    # - 윈도우/맥에서는 smbus2가 설치되지 않음
                    # - 여기서 import하여 실패 시 시뮬레이션으로 전환
                    import smbus2

                    # I2C 버스 열기
                    # SMBus(1) → /dev/i2c-1 장치 열기
                    self._bus = smbus2.SMBus(self._bus_number)

                except ImportError:
                    # smbus2 라이브러리가 설치되지 않은 경우
                    logger.warning("smbus2 not available, falling back to simulation")
                    self.simulation_mode = True

                except FileNotFoundError:
                    # I2C 장치 파일이 없는 경우 (/dev/i2c-1 없음)
                    # 라즈베리 파이 설정에서 I2C를 활성화해야 함
                    logger.warning("I2C bus not available, falling back to simulation")
                    self.simulation_mode = True

            # 시뮬레이션용 가짜 데이터 초기화
            self._init_simulated_data()

            # I2C 버스 스캔하여 연결된 장치 탐지
            await self.scan_devices()

            return True

        except Exception as e:
            logger.error(f"I2C initialization failed: {e}")
            return False

    async def _do_cleanup(self) -> None:
        """
        I2C 리소스 정리 (Clean up I2C resources)

        [한국어 설명]
        BaseHardwareController의 추상 메서드 구현.
        cleanup() 호출 시 내부적으로 이 메서드가 실행됨.

        정리 작업:
        1. I2C 버스 닫기 (파일 디스크립터 해제)
        2. 장치 목록 초기화
        """
        # I2C 버스가 열려있으면 닫기
        if self._bus:
            self._bus.close()
            self._bus = None

        # 감지된 장치 목록 초기화
        self._devices.clear()

    def _init_simulated_data(self) -> None:
        """
        시뮬레이션용 가짜 데이터 초기화 (Initialize simulated device data)

        [한국어 설명]
        시뮬레이션 모드에서 사용할 가짜 센서 데이터를 설정합니다.
        실제 하드웨어 없이 개발/테스트할 때 사용됩니다.

        각 장치별 초기값:
        - BMP280: 온도 25°C, 기압 1013.25 hPa, 고도 0m
        - ADS1115: 4개 채널에 각각 다른 전압값
        - OLED: 128x64 해상도, 빈 버퍼
        """
        # ==================== BMP280 센서 데이터 ====================
        # [한국어 설명]
        # BMP280은 Bosch의 기압/온도 센서입니다.
        # - temperature: 온도 (섭씨)
        # - pressure: 기압 (hPa = 헥토파스칼)
        # - altitude: 기압으로 계산한 고도 (미터)
        self._simulated_data[settings.I2C_BMP280_ADDRESS] = {
            "temperature": 25.0,    # 기본 온도 25°C
            "pressure": 1013.25,    # 표준 기압 1기압 ≈ 1013.25 hPa
            "altitude": 0.0         # 해수면 기준 고도
        }

        # ==================== ADS1115 ADC 데이터 ====================
        # [한국어 설명]
        # ADS1115는 16비트 4채널 ADC입니다.
        # - 아날로그 전압을 디지털 값으로 변환
        # - 0~3.3V 또는 0~5V 범위 측정 가능
        # - 4개의 독립 채널 제공
        self._simulated_data[settings.I2C_ADS1115_ADDRESS] = {
            "channel_0": 2.5,   # 채널 0: 2.5V
            "channel_1": 1.8,   # 채널 1: 1.8V
            "channel_2": 3.3,   # 채널 2: 3.3V (VCC)
            "channel_3": 0.0    # 채널 3: 0V (GND)
        }

        # ==================== OLED 디스플레이 데이터 ====================
        # [한국어 설명]
        # SSD1306 OLED 디스플레이 정보.
        # - 128x64 픽셀 해상도
        # - buffer: 화면에 표시할 픽셀 데이터
        self._simulated_data[settings.I2C_OLED_ADDRESS] = {
            "width": 128,       # 가로 픽셀 수
            "height": 64,       # 세로 픽셀 수
            "buffer": None      # 픽셀 버퍼 (시뮬레이션에서는 미사용)
        }

    # ========================================================================
    # I2C 버스 스캔 (I2C Bus Scanning)
    # ========================================================================

    async def scan_devices(self) -> List[int]:
        """
        I2C 버스 스캔하여 연결된 장치 탐지 (비동기)
        Scan I2C bus for connected devices (non-blocking)

        [한국어 설명]
        I2C 버스에 연결된 모든 장치를 찾습니다.
        각 가능한 주소(0x03~0x77)로 통신을 시도하여
        응답하는 장치의 주소를 반환합니다.

        비동기 처리:
        실제 스캔은 블로킹 작업이므로
        asyncio.to_thread()를 사용하여 별도 스레드에서 실행합니다.

        Returns:
            List[int]: 감지된 장치 주소 목록
        """
        detected = []

        if self.simulation_mode:
            # ==================== 시뮬레이션 모드 ====================
            # 알려진 장치 주소를 모두 "연결됨"으로 처리
            for addr in self._known_devices:
                self._devices[addr] = I2CDevice(
                    address=addr,
                    name=self._known_devices[addr],
                    is_connected=True
                )
                detected.append(addr)
        else:
            # ==================== 실제 하드웨어 모드 ====================
            # 블로킹 스캔 작업을 스레드 풀에서 실행
            detected = await asyncio.to_thread(self._scan_devices_sync)

        return detected

    def _scan_devices_sync(self) -> List[int]:
        """
        동기 방식 I2C 장치 스캔 (스레드 풀에서 실행됨)
        Synchronous I2C device scan (runs in thread pool)

        [한국어 설명]
        I2C 스캔 원리:
        1. 0x03부터 0x77까지 모든 주소로 "빈 쓰기" 시도
        2. 장치가 있으면 ACK(응답) 반환 → 성공
        3. 장치가 없으면 NACK(무응답) → 예외 발생

        write_quick(addr):
        - SMBus의 "Quick Command" 기능
        - 데이터 없이 주소만 전송하여 장치 존재 확인
        - 응답이 있으면 장치 존재, 없으면 예외 발생

        Returns:
            List[int]: 감지된 장치 주소 목록
        """
        detected = []

        # 유효한 I2C 주소 범위: 0x03 ~ 0x77 (3 ~ 119)
        # 0x00~0x02와 0x78~0x7F는 예약된 주소
        for addr in range(0x03, 0x78):
            try:
                # Quick Command로 장치 존재 확인
                self._bus.write_quick(addr)

                # 예외 없이 통과 = 장치 발견
                name = self._known_devices.get(addr, f"Unknown (0x{addr:02X})")
                self._devices[addr] = I2CDevice(
                    address=addr,
                    name=name,
                    is_connected=True
                )
                detected.append(addr)

                # 발견된 장치 로깅
                logger.info(f"Found I2C device at 0x{addr:02X}: {name}")

            except Exception:
                # 예외 발생 = 해당 주소에 장치 없음
                pass

        return detected

    # ========================================================================
    # 기본 I2C 읽기/쓰기 (Basic I2C Read/Write Operations)
    # ========================================================================

    async def read_byte(self, address: int, register: int) -> Optional[int]:
        """
        I2C 장치에서 1바이트 읽기 (비동기)
        Read a single byte from an I2C device (non-blocking)

        [한국어 설명]
        I2C 레지스터 읽기 과정:
        1. 마스터가 장치 주소 + 쓰기 비트 전송
        2. 레지스터 주소 전송
        3. 재시작(Repeated Start) 후 읽기 모드로 전환
        4. 장치가 해당 레지스터의 데이터 반환

        Args:
            address: I2C 장치 주소 (0x03~0x77)
            register: 읽을 레지스터 주소 (0x00~0xFF)

        Returns:
            Optional[int]: 읽은 바이트 값 (0~255), 실패 시 None
        """
        # 장치가 등록되어 있는지 확인
        if address not in self._devices:
            logger.error(f"Device at 0x{address:02X} not found")
            return None

        try:
            if self.simulation_mode:
                # 시뮬레이션: 짧은 지연 후 0 반환
                await asyncio.sleep(self._simulate_delay())
                return 0x00
            else:
                # 실제 하드웨어: 블로킹 호출을 스레드 풀에서 실행
                # read_byte_data(addr, reg): 특정 레지스터에서 1바이트 읽기
                return await asyncio.to_thread(
                    self._bus.read_byte_data, address, register
                )

        except Exception as e:
            logger.error(f"I2C read error: {e}")
            return None

    async def write_byte(self, address: int, register: int, value: int) -> bool:
        """
        I2C 장치에 1바이트 쓰기 (비동기)
        Write a single byte to an I2C device (non-blocking)

        [한국어 설명]
        I2C 레지스터 쓰기 과정:
        1. 마스터가 장치 주소 + 쓰기 비트 전송
        2. 레지스터 주소 전송
        3. 데이터 바이트 전송
        4. 장치가 ACK 응답

        Args:
            address: I2C 장치 주소
            register: 쓸 레지스터 주소
            value: 쓸 바이트 값 (0~255)

        Returns:
            bool: 쓰기 성공 여부
        """
        if address not in self._devices:
            return False

        try:
            if self.simulation_mode:
                # 시뮬레이션: 짧은 지연만 추가
                await asyncio.sleep(self._simulate_delay())
            else:
                # 실제 하드웨어: 블로킹 호출을 스레드 풀에서 실행
                # write_byte_data(addr, reg, val): 특정 레지스터에 1바이트 쓰기
                await asyncio.to_thread(
                    self._bus.write_byte_data, address, register, value
                )
            return True

        except Exception as e:
            logger.error(f"I2C write error: {e}")
            return False

    async def read_block(self, address: int, register: int, length: int) -> Optional[bytes]:
        """
        I2C 장치에서 블록 데이터 읽기 (비동기)
        Read a block of data from an I2C device (non-blocking)

        [한국어 설명]
        여러 바이트를 연속으로 읽습니다.
        센서 데이터는 보통 2~6바이트로 구성되어
        블록 읽기가 더 효율적입니다.

        Args:
            address: I2C 장치 주소
            register: 시작 레지스터 주소
            length: 읽을 바이트 수

        Returns:
            Optional[bytes]: 읽은 데이터, 실패 시 None
        """
        if address not in self._devices:
            return None

        try:
            if self.simulation_mode:
                # 시뮬레이션: 지연 후 0으로 채워진 바이트 반환
                await asyncio.sleep(self._simulate_delay())
                return bytes([0] * length)
            else:
                # 실제 하드웨어: 블록 읽기
                # read_i2c_block_data(): 연속된 여러 바이트 읽기
                data = await asyncio.to_thread(
                    self._bus.read_i2c_block_data, address, register, length
                )
                return bytes(data)

        except Exception as e:
            logger.error(f"I2C block read error: {e}")
            return None

    async def write_block(self, address: int, register: int, data: bytes) -> bool:
        """
        I2C 장치에 블록 데이터 쓰기 (비동기)
        Write a block of data to an I2C device (non-blocking)

        [한국어 설명]
        여러 바이트를 연속으로 씁니다.
        디스플레이 버퍼나 설정 데이터 전송에 사용됩니다.

        Args:
            address: I2C 장치 주소
            register: 시작 레지스터 주소
            data: 쓸 바이트 데이터

        Returns:
            bool: 쓰기 성공 여부
        """
        if address not in self._devices:
            return False

        try:
            if self.simulation_mode:
                # 시뮬레이션: 지연만 추가
                await asyncio.sleep(self._simulate_delay())
            else:
                # 실제 하드웨어: 블록 쓰기
                # write_i2c_block_data(): 연속된 여러 바이트 쓰기
                # list(data): bytes를 list로 변환 (smbus2 요구사항)
                await asyncio.to_thread(
                    self._bus.write_i2c_block_data, address, register, list(data)
                )
            return True

        except Exception as e:
            logger.error(f"I2C block write error: {e}")
            return False

    # ========================================================================
    # BMP280 센서 (BMP280 Sensor)
    # ========================================================================

    async def read_bmp280(self) -> Optional[Dict[str, float]]:
        """
        BMP280 센서에서 온도와 기압 읽기 (비동기)
        Read temperature and pressure from BMP280 (non-blocking)

        [한국어 설명]
        BMP280 센서 특징:
        - Bosch사의 고정밀 기압/온도 센서
        - 온도: -40°C ~ +85°C, 정확도 ±1°C
        - 기압: 300 ~ 1100 hPa, 정확도 ±1 hPa
        - 고도 계산 가능 (기압 차이 이용)

        I2C 주소: 0x76 또는 0x77 (SDO 핀에 따라)

        Returns:
            Dict with temperature (°C), pressure (hPa), and altitude (m)
        """
        address = settings.I2C_BMP280_ADDRESS

        if self.simulation_mode:
            # ==================== 시뮬레이션 모드 ====================
            await asyncio.sleep(self._simulate_delay())
            data = self._simulated_data[address]

            # 현실적인 변화를 위해 노이즈 추가
            # _simulate_noise(값, 노이즈범위): 값 ± 노이즈범위의 랜덤값
            return {
                "temperature": self._simulate_noise(data["temperature"], 0.5),
                "pressure": self._simulate_noise(data["pressure"], 0.2),
                "altitude": self._simulate_noise(data["altitude"], 1.0)
            }

        try:
            # ==================== 실제 하드웨어 모드 ====================
            # 블로킹 센서 읽기를 스레드 풀에서 실행
            return await asyncio.to_thread(self._read_bmp280_sync, address)

        except ImportError:
            # adafruit_bmp280 라이브러리가 없는 경우
            logger.warning("BMP280 library not available")
            return None
        except Exception as e:
            logger.error(f"BMP280 read error: {e}")
            return None

    def _read_bmp280_sync(self, address: int) -> Optional[Dict[str, float]]:
        """
        동기 방식 BMP280 읽기 (스레드 풀에서 실행됨)
        Synchronous BMP280 read (runs in thread pool)

        [한국어 설명]
        Adafruit CircuitPython 라이브러리 사용:
        - board: 라즈베리 파이 보드 정보
        - adafruit_bmp280: BMP280 센서 드라이버

        라이브러리 설치:
        pip install adafruit-circuitpython-bmp280
        """
        # Adafruit 라이브러리 임포트
        import board
        import adafruit_bmp280

        # I2C 버스 객체 생성
        # board.I2C(): 보드의 기본 I2C 버스 사용
        i2c = board.I2C()

        # BMP280 센서 객체 생성
        bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=address)

        # 센서 값 읽기 및 반환
        return {
            "temperature": bmp280.temperature,  # 온도 (섭씨)
            "pressure": bmp280.pressure,        # 기압 (hPa)
            "altitude": bmp280.altitude         # 추정 고도 (미터)
        }

    def set_simulated_bmp280(self, temperature: float = None, pressure: float = None) -> None:
        """
        시뮬레이션용 BMP280 값 설정 (Set simulated BMP280 values)

        [한국어 설명]
        Settings 페이지에서 시뮬레이션 값을 수동 설정할 때 사용됩니다.
        값을 None으로 전달하면 해당 값은 변경하지 않습니다.

        Args:
            temperature: 설정할 온도 (°C)
            pressure: 설정할 기압 (hPa)
        """
        if temperature is not None:
            self._simulated_data[settings.I2C_BMP280_ADDRESS]["temperature"] = temperature
        if pressure is not None:
            self._simulated_data[settings.I2C_BMP280_ADDRESS]["pressure"] = pressure

    # ========================================================================
    # ADS1115 ADC (ADS1115 Analog-to-Digital Converter)
    # ========================================================================

    async def read_adc(self, channel: int = 0) -> Optional[float]:
        """
        ADS1115 ADC 채널에서 전압 읽기 (비동기)
        Read voltage from ADS1115 ADC channel (non-blocking)

        [한국어 설명]
        ADS1115 특징:
        - Texas Instruments의 16비트 ADC
        - 4개의 단일 입력 또는 2개의 차동 입력
        - 프로그래밍 가능한 게인 앰프 (PGA)
        - 최대 860 샘플/초

        왜 ADC가 필요한가?
        - 라즈베리 파이에는 내장 ADC가 없음
        - 아날로그 센서(조도, 토양수분 등)를 읽으려면 외부 ADC 필요
        - ADS1115는 I2C로 쉽게 연결 가능

        Args:
            channel: ADC 채널 번호 (0-3)

        Returns:
            float: 전압 값 (볼트)
        """
        # 채널 범위 검증
        if channel < 0 or channel > 3:
            logger.error(f"Invalid ADC channel: {channel}")
            return None

        address = settings.I2C_ADS1115_ADDRESS

        if self.simulation_mode:
            # ==================== 시뮬레이션 모드 ====================
            await asyncio.sleep(self._simulate_delay())
            data = self._simulated_data[address]
            key = f"channel_{channel}"
            # 노이즈를 추가하여 현실적인 ADC 변동 시뮬레이션
            return self._simulate_noise(data[key], 1.0)

        try:
            # ==================== 실제 하드웨어 모드 ====================
            return await asyncio.to_thread(self._read_adc_sync, address, channel)

        except ImportError:
            logger.warning("ADS1115 library not available")
            return None
        except Exception as e:
            logger.error(f"ADC read error: {e}")
            return None

    def _read_adc_sync(self, address: int, channel: int) -> float:
        """
        동기 방식 ADC 읽기 (스레드 풀에서 실행됨)
        Synchronous ADC read (runs in thread pool)

        [한국어 설명]
        Adafruit ADS1x15 라이브러리 사용:
        - busio: I2C 버스 인터페이스
        - ADS1115: ADC 칩 드라이버
        - AnalogIn: 아날로그 입력 채널 래퍼

        라이브러리 설치:
        pip install adafruit-circuitpython-ads1x15
        """
        import board
        import busio
        import adafruit_ads1x15.ads1115 as ADS
        from adafruit_ads1x15.analog_in import AnalogIn

        # I2C 버스 생성 (SCL, SDA 핀 지정)
        i2c = busio.I2C(board.SCL, board.SDA)

        # ADS1115 객체 생성
        ads = ADS.ADS1115(i2c, address=address)

        # 채널 상수 매핑
        # P0, P1, P2, P3: 단일 입력 채널
        channels = [ADS.P0, ADS.P1, ADS.P2, ADS.P3]

        # AnalogIn 객체 생성 및 전압 읽기
        chan = AnalogIn(ads, channels[channel])

        # voltage 속성: 자동으로 ADC 값을 전압으로 변환
        return chan.voltage

    async def read_all_adc_channels(self) -> Dict[int, float]:
        """
        모든 ADC 채널 읽기 (Read all ADC channels)

        [한국어 설명]
        4개의 모든 채널을 순차적으로 읽어 딕셔너리로 반환합니다.

        Returns:
            Dict[int, float]: {채널번호: 전압값} 형태의 딕셔너리
        """
        results = {}
        for channel in range(4):
            value = await self.read_adc(channel)
            if value is not None:
                results[channel] = value
        return results

    def set_simulated_adc(self, channel: int, voltage: float) -> None:
        """
        시뮬레이션용 ADC 값 설정 (Set simulated ADC channel value)

        Args:
            channel: ADC 채널 번호 (0-3)
            voltage: 설정할 전압 값 (볼트)
        """
        if 0 <= channel <= 3:
            key = f"channel_{channel}"
            self._simulated_data[settings.I2C_ADS1115_ADDRESS][key] = voltage

    # ========================================================================
    # 상태 조회 메서드 (Status Query Methods)
    # ========================================================================

    def get_devices(self) -> Dict[int, Dict[str, Any]]:
        """
        감지된 모든 I2C 장치 정보 반환 (Get all detected I2C devices)

        [한국어 설명]
        REST API에서 사용하기 쉬운 딕셔너리 형태로 변환합니다.

        Returns:
            Dict: 장치 주소를 키로 하는 장치 정보 딕셔너리
        """
        return {
            addr: {
                "name": device.name,              # 장치 이름
                "is_connected": device.is_connected,  # 연결 상태
                "address_hex": f"0x{addr:02X}"    # 16진수 주소 문자열
            }
            for addr, device in self._devices.items()
        }

    def _get_status_details(self) -> Dict[str, Any]:
        """
        I2C 컨트롤러 상태 상세 정보 (Get I2C-specific status details)

        [한국어 설명]
        BaseHardwareController의 status 속성에서 사용됩니다.
        컨트롤러별 고유 정보를 추가로 제공합니다.

        Returns:
            Dict: I2C 버스 정보와 연결된 장치 목록
        """
        return {
            "bus_number": self._bus_number,    # I2C 버스 번호
            "devices": self.get_devices(),     # 장치 목록
            "device_count": len(self._devices) # 장치 개수
        }
