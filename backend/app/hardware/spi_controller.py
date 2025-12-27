"""
SPI Controller (SPI 컨트롤러)
=============================

[한국어 설명]
SPI(Serial Peripheral Interface) 장치를 제어하는 컨트롤러입니다.
SPI는 고속 동기식 직렬 통신 프로토콜로, ADC, DAC, 센서 등에 사용됩니다.

SPI 통신의 특징:
- 4선 통신: MOSI(마스터→슬레이브), MISO(슬레이브→마스터), CLK(클록), CS(칩 선택)
- 전이중(Full Duplex): 송수신 동시 가능
- 마스터-슬레이브 구조
- I2C보다 빠른 통신 속도 (최대 수십 MHz)
- 주소 없음: CS 핀으로 장치 선택

SPI vs I2C 비교:
- SPI: 고속(~MHz), 4선, 주소 없음, 장치당 CS 핀 필요
- I2C: 저속(~kHz), 2선, 주소 사용, 다수 장치 연결 용이

라즈베리 파이의 SPI 핀:
- GPIO 10 (MOSI) - 마스터 출력, 슬레이브 입력
- GPIO 9  (MISO) - 마스터 입력, 슬레이브 출력
- GPIO 11 (SCLK) - 클록
- GPIO 8  (CE0)  - 칩 선택 0
- GPIO 7  (CE1)  - 칩 선택 1

지원 장치:
- MCP3008: 8채널 10비트 ADC

[English Description]
Controller for SPI (Serial Peripheral Interface) devices.
Supports high-speed communication with ADCs, DACs, and sensors.
"""

# ============================================================================
# 라이브러리 임포트 (Import Libraries)
# ============================================================================

# asyncio: 비동기 I/O 처리
# SPI 통신도 블로킹이므로 asyncio.to_thread로 비동기 처리
import asyncio

# typing: 타입 힌트용 모듈
from typing import Dict, Optional, Any, List

# dataclass: 데이터 저장 클래스를 간편하게 정의
from dataclasses import dataclass

# base: 하드웨어 컨트롤러 기본 클래스
from .base import BaseHardwareController, SimulationMixin

# settings: 애플리케이션 설정 (SPI 버스, 속도 등)
from app.core.config import settings

# get_logger: 로깅 함수
from app.core.logging_config import get_logger

# 이 모듈 전용 로거 생성
logger = get_logger(__name__)


# ============================================================================
# SPI 장치 데이터 클래스 (SPI Device Data Class)
# ============================================================================

@dataclass
class SPIDevice:
    """
    SPI 장치 정보를 저장하는 데이터 클래스 (Represents an SPI device)

    [한국어 설명]
    속성 설명:
    - bus: SPI 버스 번호 (라즈베리 파이는 0 또는 1)
    - device: 장치 번호 (CE0=0, CE1=1)
    - name: 장치 이름
    - max_speed: 최대 클록 속도 (Hz)
    - mode: SPI 모드 (0~3, 클록 극성과 위상 조합)
    - bits_per_word: 워드당 비트 수 (보통 8)

    SPI 모드 설명:
    - Mode 0: CPOL=0, CPHA=0 (기본, 상승 에지에서 샘플링)
    - Mode 1: CPOL=0, CPHA=1
    - Mode 2: CPOL=1, CPHA=0
    - Mode 3: CPOL=1, CPHA=1
    """
    bus: int                 # SPI 버스 번호
    device: int              # 장치 번호 (CE0 또는 CE1)
    name: str                # 장치 이름
    max_speed: int           # 최대 클록 속도 (Hz)
    mode: int = 0            # SPI 모드 (0-3, 기본값: 0)
    bits_per_word: int = 8   # 워드당 비트 수 (기본값: 8)


# ============================================================================
# SPI 컨트롤러 클래스 (SPI Controller Class)
# ============================================================================

class SPIController(BaseHardwareController, SimulationMixin):
    """
    SPI 통신 컨트롤러 (Controller for SPI operations)

    [한국어 설명]
    MCP3008 ADC를 주로 사용하여 아날로그 센서 값을 읽습니다.

    MCP3008 특징:
    - 8채널 10비트 ADC (0~1023 범위)
    - 최대 200 ksps (초당 20만 샘플)
    - 0~VCC (보통 3.3V) 입력 범위
    - SPI 인터페이스

    왜 MCP3008을 사용하는가?
    - 라즈베리 파이에는 내장 ADC가 없음
    - ADS1115(I2C)보다 빠른 샘플링 가능
    - 8개의 독립 채널 제공
    - 가격이 저렴

    Features:
    - MCP3008 ADC (10-bit, 8 channels)
    - MCP4725 DAC (12-bit) - 지원 예정
    - MAX31855 Thermocouple sensor - 지원 예정
    """

    def __init__(self, simulation_mode: bool = False):
        """
        SPI 컨트롤러 초기화 (Initialize SPI Controller)

        [한국어 설명]
        Args:
            simulation_mode: 시뮬레이션 모드 여부
        """
        # 부모 클래스 초기화
        super().__init__("SPI Controller", simulation_mode)

        # SPI 장치 객체 (spidev.SpiDev 인스턴스)
        self._spi = None

        # SPI 버스 번호 (보통 0)
        self._bus = settings.SPI_BUS

        # 장치 번호 (CE0=0, CE1=1)
        self._device = settings.SPI_DEVICE

        # 최대 클록 속도 (Hz)
        # MCP3008은 최대 3.6MHz (VCC=5V) 또는 1.35MHz (VCC=2.7V)
        self._max_speed = settings.SPI_MAX_SPEED

        # 등록된 SPI 장치들
        self._devices: Dict[str, SPIDevice] = {}

        # 시뮬레이션용 가짜 데이터
        self._simulated_data: Dict[str, Any] = {}

    # ========================================================================
    # 초기화 및 정리 메서드 (Initialization and Cleanup Methods)
    # ========================================================================

    async def _do_initialize(self) -> bool:
        """
        SPI 버스 초기화 (Initialize SPI bus)

        [한국어 설명]
        spidev 라이브러리를 사용하여 SPI 버스를 엽니다.

        spidev 설치:
        pip install spidev  # 라즈베리 파이에서만 동작

        라즈베리 파이 설정:
        raspi-config → Interface Options → SPI → Enable

        Returns:
            bool: 초기화 성공 여부
        """
        try:
            if not self.simulation_mode:
                try:
                    # spidev 라이브러리 동적 임포트
                    # [한국어 설명]
                    # 윈도우/맥에서는 spidev가 없으므로 여기서 import
                    import spidev

                    # SpiDev 객체 생성 및 SPI 버스 열기
                    self._spi = spidev.SpiDev()

                    # open(bus, device): SPI 버스와 장치 열기
                    # /dev/spidev{bus}.{device} 파일을 엶
                    # 예: open(0, 0) → /dev/spidev0.0
                    self._spi.open(self._bus, self._device)

                    # 최대 클록 속도 설정 (Hz)
                    self._spi.max_speed_hz = self._max_speed

                    # SPI 모드 설정 (0~3)
                    # MCP3008은 Mode 0 사용
                    self._spi.mode = 0

                except ImportError:
                    # spidev 라이브러리가 없는 경우
                    logger.warning("spidev not available, falling back to simulation")
                    self.simulation_mode = True

                except FileNotFoundError:
                    # SPI 장치 파일이 없는 경우
                    logger.warning("SPI device not available, falling back to simulation")
                    self.simulation_mode = True

            # 시뮬레이션용 데이터 초기화
            self._init_simulated_data()

            # MCP3008 장치 등록
            # [한국어 설명]
            # 사용할 SPI 장치를 미리 등록해둡니다.
            self._devices["MCP3008"] = SPIDevice(
                bus=self._bus,
                device=self._device,
                name="MCP3008 ADC",
                max_speed=1000000  # 1 MHz
            )

            return True

        except Exception as e:
            logger.error(f"SPI initialization failed: {e}")
            return False

    async def _do_cleanup(self) -> None:
        """
        SPI 리소스 정리 (Clean up SPI resources)

        [한국어 설명]
        SPI 버스를 닫고 리소스를 해제합니다.
        """
        if self._spi:
            self._spi.close()
            self._spi = None
        self._devices.clear()

    def _init_simulated_data(self) -> None:
        """
        시뮬레이션용 가짜 데이터 초기화 (Initialize simulated device data)

        [한국어 설명]
        MCP3008의 8개 채널에 대한 가짜 ADC 값을 설정합니다.
        10비트 ADC이므로 값 범위는 0~1023입니다.

        전압 계산 공식:
        전압 = (ADC값 / 1023) × Vref
        예: ADC값 512, Vref 3.3V → 약 1.65V
        """
        # MCP3008 - 8채널 10비트 ADC
        # [한국어 설명]
        # 딕셔너리 컴프리헨션을 사용하여 8개 채널 초기화
        # {f"channel_{i}": 512 for i in range(8)}
        # → {"channel_0": 512, "channel_1": 512, ..., "channel_7": 512}
        self._simulated_data["MCP3008"] = {
            f"channel_{i}": 512 for i in range(8)  # 중간값 (약 1.65V)
        }

        # 채널별 다양한 값 설정 (시뮬레이션 다양성)
        self._simulated_data["MCP3008"]["channel_0"] = 750   # ~2.4V (예: 조도 센서)
        self._simulated_data["MCP3008"]["channel_1"] = 500   # ~1.6V (예: 가변저항)
        self._simulated_data["MCP3008"]["channel_2"] = 1000  # ~3.2V (예: 높은 전압)
        self._simulated_data["MCP3008"]["channel_3"] = 100   # ~0.3V (예: 낮은 전압)

    # ========================================================================
    # MCP3008 ADC 읽기 (MCP3008 ADC Reading)
    # ========================================================================

    async def read_mcp3008(self, channel: int) -> Optional[int]:
        """
        MCP3008 ADC 채널에서 원시값 읽기 (비동기)
        Read raw value from MCP3008 ADC channel (non-blocking)

        [한국어 설명]
        MCP3008 SPI 통신 프로토콜:
        1. 시작 비트 전송 (0x01)
        2. 채널 선택 비트 전송 ((8 + channel) << 4)
        3. 더미 바이트 전송 (0x00)
        4. 응답에서 10비트 값 추출

        SPI 전송 형식: [0x01, (8+ch)<<4, 0x00]
        - 바이트 1: 시작 비트 (0x01 = 0b00000001)
        - 바이트 2: 단일 입력 + 채널 번호 ((8+ch)<<4)
            - 채널 0: (8+0)<<4 = 0x80 = 0b10000000
            - 채널 1: (8+1)<<4 = 0x90 = 0b10010000
            - ...
        - 바이트 3: 더미 (0x00)

        응답 형식: [X, high_bits, low_bits]
        - high_bits의 하위 2비트 + low_bits 8비트 = 10비트 값
        - 값 = ((result[1] & 0x03) << 8) | result[2]

        Args:
            channel: ADC 채널 번호 (0-7)

        Returns:
            Optional[int]: 10비트 ADC 값 (0-1023), 실패 시 None
        """
        # 채널 범위 검증
        if channel < 0 or channel > 7:
            logger.error(f"Invalid MCP3008 channel: {channel}")
            return None

        try:
            if self.simulation_mode:
                # ==================== 시뮬레이션 모드 ====================
                await asyncio.sleep(self._simulate_delay())
                key = f"channel_{channel}"
                value = self._simulated_data["MCP3008"].get(key, 512)
                # 노이즈 추가 (±2 범위)
                # int()로 정수 변환 (ADC 값은 정수)
                return int(self._simulate_noise(value, 2.0))
            else:
                # ==================== 실제 하드웨어 모드 ====================
                # 블로킹 SPI 호출을 스레드 풀에서 실행
                return await asyncio.to_thread(self._read_mcp3008_sync, channel)

        except Exception as e:
            logger.error(f"MCP3008 read error: {e}")
            return None

    def _read_mcp3008_sync(self, channel: int) -> int:
        """
        동기 방식 MCP3008 읽기 (스레드 풀에서 실행됨)
        Synchronous MCP3008 read (runs in thread pool)

        [한국어 설명]
        MCP3008 SPI 프로토콜 구현.

        xfer2(data): SPI 전이중 전송
        - data 리스트의 각 바이트를 전송
        - 동시에 같은 개수의 바이트 수신
        - 칩 선택(CS)을 자동으로 토글

        비트 연산 설명:
        - (8 + channel) << 4: 채널 번호를 상위 니블로 이동
        - result[1] & 3: 하위 2비트만 추출 (마스킹)
        - << 8: 상위 8비트 위치로 이동
        - + result[2]: 하위 8비트 추가

        Returns:
            int: 10비트 ADC 값 (0-1023)
        """
        # MCP3008 SPI 프로토콜 명령 구성
        # [시작비트, 채널선택, 더미]
        cmd = [1, (8 + channel) << 4, 0]

        # SPI 전송 및 수신
        # xfer2: 전송하면서 동시에 수신
        result = self._spi.xfer2(cmd)

        # 10비트 값 추출
        # result[1]의 하위 2비트 + result[2]의 8비트 = 10비트
        value = ((result[1] & 3) << 8) + result[2]

        return value

    async def read_mcp3008_voltage(self, channel: int, vref: float = 3.3) -> Optional[float]:
        """
        MCP3008 ADC 채널에서 전압 읽기 (비동기)
        Read voltage from MCP3008 ADC channel

        [한국어 설명]
        원시 ADC 값을 실제 전압으로 변환합니다.

        변환 공식:
        전압 = (ADC값 / 1023) × Vref

        예시:
        - ADC값 = 512, Vref = 3.3V → 전압 = 1.65V
        - ADC값 = 1023, Vref = 3.3V → 전압 = 3.3V
        - ADC값 = 0, Vref = 3.3V → 전압 = 0V

        Args:
            channel: ADC 채널 번호 (0-7)
            vref: 기준 전압 (기본값 3.3V)

        Returns:
            Optional[float]: 전압 값 (볼트)
        """
        # 원시 ADC 값 읽기
        raw = await self.read_mcp3008(channel)
        if raw is None:
            return None

        # 전압 계산
        # 1023 = 10비트 ADC 최대값 (2^10 - 1)
        return (raw / 1023.0) * vref

    async def read_all_mcp3008_channels(self, vref: float = 3.3) -> Dict[int, float]:
        """
        모든 MCP3008 채널 읽기 (Read all MCP3008 ADC channels)

        [한국어 설명]
        8개의 모든 채널을 순차적으로 읽어 딕셔너리로 반환합니다.

        Args:
            vref: 기준 전압

        Returns:
            Dict[int, float]: {채널번호: 전압값} 형태의 딕셔너리
        """
        results = {}
        for channel in range(8):
            voltage = await self.read_mcp3008_voltage(channel, vref)
            if voltage is not None:
                # 소수점 3자리로 반올림
                results[channel] = round(voltage, 3)
        return results

    def set_simulated_mcp3008(self, channel: int, raw_value: int) -> None:
        """
        시뮬레이션용 MCP3008 값 설정 (Set simulated MCP3008 channel value)

        Args:
            channel: ADC 채널 번호 (0-7)
            raw_value: 원시 ADC 값 (0-1023)
        """
        if 0 <= channel <= 7 and 0 <= raw_value <= 1023:
            key = f"channel_{channel}"
            self._simulated_data["MCP3008"][key] = raw_value

    # ========================================================================
    # 일반 SPI 통신 (Generic SPI Operations)
    # ========================================================================

    async def transfer(self, data: List[int]) -> Optional[List[int]]:
        """
        SPI 전송 (비동기)
        Perform SPI transfer (non-blocking)

        [한국어 설명]
        SPI는 전이중(Full Duplex) 통신입니다.
        데이터를 보내면서 동시에 같은 양의 데이터를 받습니다.

        예: [0x01, 0x02, 0x03] 전송 → [응답1, 응답2, 응답3] 수신

        Args:
            data: 전송할 바이트 리스트

        Returns:
            Optional[List[int]]: 수신한 바이트 리스트
        """
        try:
            if self.simulation_mode:
                # 시뮬레이션: 0으로 채워진 응답 반환
                await asyncio.sleep(self._simulate_delay())
                return [0] * len(data)
            else:
                # 실제 하드웨어: 스레드 풀에서 SPI 전송
                return await asyncio.to_thread(self._spi.xfer2, data)

        except Exception as e:
            logger.error(f"SPI transfer error: {e}")
            return None

    async def write(self, data: List[int]) -> bool:
        """
        SPI 쓰기 (Write data to SPI bus)

        [한국어 설명]
        단방향 쓰기. 수신 데이터는 무시합니다.

        Args:
            data: 전송할 바이트 리스트

        Returns:
            bool: 쓰기 성공 여부
        """
        result = await self.transfer(data)
        return result is not None

    # ========================================================================
    # 상태 조회 메서드 (Status Query Methods)
    # ========================================================================

    def get_devices(self) -> Dict[str, Dict[str, Any]]:
        """
        등록된 SPI 장치 정보 반환 (Get registered SPI devices)

        Returns:
            Dict: 장치 이름을 키로 하는 장치 정보 딕셔너리
        """
        return {
            name: {
                "bus": device.bus,
                "device": device.device,
                "name": device.name,
                "max_speed": device.max_speed,
                "mode": device.mode
            }
            for name, device in self._devices.items()
        }

    def _get_status_details(self) -> Dict[str, Any]:
        """
        SPI 컨트롤러 상태 상세 정보 (Get SPI-specific status details)

        Returns:
            Dict: SPI 버스 정보와 장치 목록
        """
        return {
            "bus": self._bus,
            "device": self._device,
            "max_speed": self._max_speed,
            "devices": self.get_devices()
        }
