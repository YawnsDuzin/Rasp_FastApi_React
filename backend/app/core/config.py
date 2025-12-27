"""
Application Configuration (애플리케이션 설정)
=============================================

[한국어 설명]
Pydantic Settings를 사용한 중앙 집중식 설정 관리 모듈입니다.

Pydantic Settings란?
- Pydantic은 Python의 데이터 검증(validation) 라이브러리입니다.
- Pydantic Settings는 환경 변수와 .env 파일에서 설정값을 읽어옵니다.
- 타입 검증, 기본값 설정, 문서화 등을 자동으로 처리합니다.

설정값 우선순위 (높은 순서부터):
1. 환경 변수 (export SIMULATION_MODE=true)
2. .env 파일의 값
3. 코드에 정의된 기본값

[English Description]
Central configuration management using Pydantic Settings.
Supports environment variables and .env files.
"""

# ============================================================================
# 필수 라이브러리 임포트 (Import Required Libraries)
# ============================================================================

# os: 운영체제와 상호작용하는 기능 제공 (환경 변수 읽기 등)
import os

# platform: 현재 실행 중인 플랫폼(운영체제) 정보를 가져옴
# 예: Windows, Linux, Darwin(macOS) 등 구분
import platform

# pathlib.Path: 파일 경로를 객체지향적으로 다루는 클래스
# 예: Path("logs") / "app.log" -> "logs/app.log" (크로스 플랫폼 호환)
from pathlib import Path

# typing.List, Optional: 타입 힌트를 위한 제네릭 타입
# List[int]: 정수 리스트, Optional[str]: 문자열 또는 None
from typing import List, Optional

# pydantic_settings.BaseSettings: 환경 변수 기반 설정 클래스의 부모 클래스
# 이 클래스를 상속하면 자동으로 환경 변수에서 값을 읽어옴
from pydantic_settings import BaseSettings

# pydantic.Field: 필드에 대한 추가 정보(설명, 기본값, 제약 조건 등)를 정의
from pydantic import Field


# ============================================================================
# 유틸리티 함수 (Utility Functions)
# ============================================================================

def is_raspberry_pi() -> bool:
    """
    라즈베리 파이 하드웨어 감지 (Detect Raspberry Pi Hardware)

    [한국어 설명]
    현재 코드가 라즈베리 파이에서 실행 중인지 확인합니다.

    작동 방식:
    1. /proc/cpuinfo 파일을 읽습니다 (Linux 시스템 정보 파일)
    2. 파일 내용에 "Raspberry Pi" 또는 "BCM" 문자열이 있는지 확인
       - BCM: Broadcom, 라즈베리 파이 CPU 제조사
    3. Windows에서는 /proc/cpuinfo가 없어서 FileNotFoundError 발생 -> False 반환

    반환값:
        bool: 라즈베리 파이이면 True, 아니면 False

    사용 예:
        if is_raspberry_pi():
            # 실제 GPIO 사용
        else:
            # 시뮬레이션 모드 사용

    [English Description]
    Detects if the code is running on Raspberry Pi hardware.
    Checks /proc/cpuinfo for Raspberry Pi or BCM identifiers.
    """
    try:
        # Linux 시스템의 CPU 정보 파일 읽기
        with open("/proc/cpuinfo", "r") as f:
            cpuinfo = f.read()
            # "Raspberry Pi" 또는 "BCM" 문자열 검색
            return "Raspberry Pi" in cpuinfo or "BCM" in cpuinfo
    except FileNotFoundError:
        # Windows 등 다른 OS에서는 이 파일이 없음
        return False


# ============================================================================
# 설정 클래스 정의 (Settings Class Definition)
# ============================================================================

class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스 (Application Settings Class)

    [한국어 설명]
    BaseSettings를 상속하여 환경 변수 지원 설정 클래스를 만듭니다.

    Pydantic BaseSettings 특징:
    1. 클래스 변수가 자동으로 환경 변수에서 값을 읽어옴
       - 예: APP_NAME 변수는 환경 변수 APP_NAME의 값을 사용
    2. Field()로 기본값, 설명, 제약 조건 등을 지정할 수 있음
    3. .env 파일을 자동으로 로드 (Config 클래스에서 설정)
    4. 타입 자동 변환 (환경 변수는 문자열이지만 int, bool 등으로 변환)

    환경 변수 설정 예시:
        # Linux/Mac
        export SIMULATION_MODE=true
        export PORT=9000

        # Windows PowerShell
        $env:SIMULATION_MODE = "true"
        $env:PORT = "9000"

    [English Description]
    Application settings with environment variable support.
    Inherits from Pydantic BaseSettings for automatic env var loading.
    """

    # ============================================================================
    # 애플리케이션 기본 설정 (Application Basic Settings)
    # ============================================================================

    # 앱 이름 - API 문서와 로그에 표시됨
    APP_NAME: str = "Raspberry Pi HMI"

    # 앱 버전 - API 문서와 헬스 체크에 표시됨
    # 시맨틱 버저닝: MAJOR.MINOR.PATCH
    APP_VERSION: str = "1.0.0"

    # 디버그 모드 - True이면 상세한 에러 메시지와 로그 출력
    # Field(): Pydantic의 필드 메타데이터 정의
    # default: 기본값, description: 문서화용 설명
    DEBUG: bool = Field(default=False, description="Debug mode")

    # ============================================================================
    # 서버 설정 (Server Settings)
    # ============================================================================

    # 서버가 바인딩할 호스트 주소
    # "0.0.0.0": 모든 네트워크 인터페이스에서 접속 허용
    # "127.0.0.1": 로컬에서만 접속 허용
    HOST: str = Field(default="0.0.0.0", description="Server host")

    # 서버 포트 번호
    # 기본값 8000, HTTP 기본 포트인 80을 사용하려면 관리자 권한 필요
    PORT: int = Field(default=8000, description="Server port")

    # 코드 변경 시 자동 재시작 여부
    # 개발 중에는 True로 설정하면 편리함 (uvicorn --reload와 동일)
    RELOAD: bool = Field(default=False, description="Auto-reload on code changes")

    # ============================================================================
    # CORS 설정 (Cross-Origin Resource Sharing Settings)
    # ============================================================================

    # 허용할 출처(Origin) 목록
    # [한국어 설명]
    # CORS는 브라우저 보안 기능으로, 다른 도메인에서 오는 요청을 기본적으로 차단합니다.
    # 예: React 개발 서버(localhost:3000)에서 FastAPI(localhost:8000)로 요청할 때
    #     CORS 정책에 의해 차단될 수 있음
    # 여기에 등록된 출처에서의 요청만 허용됩니다.
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
        description="Allowed CORS origins"
    )

    # ============================================================================
    # 데이터베이스 설정 (Database Settings)
    # ============================================================================

    # SQLite 데이터베이스 연결 URL
    # [한국어 설명]
    # "sqlite+aiosqlite:///./data/hmi_data.db" 구조:
    # - sqlite: 데이터베이스 종류 (SQLite)
    # - aiosqlite: 비동기 드라이버 (async/await 지원)
    # - ///: 상대 경로 (////는 절대 경로)
    # - ./data/hmi_data.db: 데이터베이스 파일 경로
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/hmi_data.db",
        description="SQLite database URL"
    )

    # SQLite WAL(Write-Ahead Logging) 모드 활성화
    # [한국어 설명]
    # WAL 모드 장점:
    # 1. 읽기와 쓰기가 동시에 가능 (동시성 향상)
    # 2. 쓰기 성능 향상 (SD 카드 수명 연장에 도움)
    # 3. 데이터 손실 위험 감소
    DATABASE_WAL_MODE: bool = Field(default=True, description="Enable WAL mode for SQLite")

    # ============================================================================
    # 하드웨어 설정 (Hardware Settings)
    # ============================================================================

    # 시뮬레이션 모드 여부
    # [한국어 설명]
    # True: 실제 하드웨어 없이 가상의 센서 값을 생성
    # False: 실제 라즈베리 파이 GPIO, I2C 등을 사용
    # 기본값: 라즈베리 파이가 아니면 자동으로 True
    SIMULATION_MODE: bool = Field(
        default=not is_raspberry_pi(),  # 라즈베리 파이가 아니면 시뮬레이션 모드
        description="Use simulation instead of real hardware"
    )

    # 하드웨어 상태 업데이트 간격 (초)
    # [한국어 설명]
    # 센서 값을 읽고 WebSocket으로 전송하는 주기
    # 0.5초 = 초당 2회 업데이트 (적절한 반응성과 성능의 균형)
    HARDWARE_UPDATE_INTERVAL: float = Field(
        default=0.5,
        description="Hardware polling interval in seconds"
    )

    # ============================================================================
    # WebSocket 설정 (WebSocket Settings)
    # ============================================================================

    # WebSocket 하트비트 간격 (초)
    # [한국어 설명]
    # 클라이언트-서버 간 연결이 살아있는지 확인하는 ping/pong 메시지 간격
    # 네트워크 장애나 연결 끊김을 감지하는 데 사용
    WS_HEARTBEAT_INTERVAL: float = Field(default=30.0, description="WebSocket heartbeat interval")

    # 최대 동시 WebSocket 연결 수
    # [한국어 설명]
    # 서버 리소스 보호를 위해 동시 연결 수를 제한
    # 라즈베리 파이의 제한된 리소스를 고려한 값
    WS_MAX_CONNECTIONS: int = Field(default=10, description="Maximum WebSocket connections")

    # ============================================================================
    # 로깅 설정 (Logging Settings)
    # ============================================================================

    # 로그 레벨
    # [한국어 설명]
    # 로그 레벨 순서 (낮은 순서부터): DEBUG < INFO < WARNING < ERROR < CRITICAL
    # INFO: 일반적인 정보 메시지부터 출력
    # DEBUG: 디버깅용 상세 정보까지 출력
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # 로그 파일 저장 디렉토리
    LOG_DIR: Path = Field(default=Path("logs"), description="Log directory")

    # 로그 파일 최대 크기 (바이트)
    # 10 * 1024 * 1024 = 10MB
    # 이 크기를 초과하면 새 파일로 교체됨 (log rotation)
    LOG_MAX_SIZE: int = Field(default=10 * 1024 * 1024, description="Max log file size (10MB)")

    # 보관할 백업 로그 파일 수
    # 5개를 초과하면 가장 오래된 파일이 삭제됨
    LOG_BACKUP_COUNT: int = Field(default=5, description="Number of backup log files")

    # ============================================================================
    # 데이터 로깅 설정 (Data Logging Settings)
    # ============================================================================

    # 센서 데이터를 DB에 저장하는 간격 (초)
    # [한국어 설명]
    # 너무 짧으면 DB 쓰기가 잦아져 SD 카드 수명에 영향
    # 너무 길면 데이터 해상도가 낮아짐
    # 5초는 적절한 균형점
    DATA_LOG_INTERVAL: float = Field(default=5.0, description="Data logging interval in seconds")

    # 데이터 보관 기간 (일)
    # [한국어 설명]
    # 이 기간이 지난 데이터는 자동으로 삭제됨
    # SD 카드 용량 관리를 위해 필요
    DATA_RETENTION_DAYS: int = Field(default=30, description="Data retention period in days")

    # ============================================================================
    # GPIO 핀 설정 (GPIO Pin Configuration)
    # ============================================================================
    # [한국어 설명]
    # BCM(Broadcom) 핀 번호 체계를 사용합니다.
    # BCM vs BOARD:
    # - BCM: GPIO 칩의 핀 번호 (GPIO17, GPIO27 등)
    # - BOARD: 물리적인 핀 위치 (핀 1, 핀 2 등)
    # BCM이 더 일관되고 라이브러리에서 널리 사용됨

    # LED 제어용 GPIO 핀 목록
    # 각 핀에 LED를 연결하여 On/Off 제어
    GPIO_LED_PINS: List[int] = Field(default=[17, 27, 22, 23], description="LED GPIO pins")

    # 버튼 입력용 GPIO 핀 목록
    # 버튼 누름을 감지하여 이벤트 처리
    GPIO_BUTTON_PINS: List[int] = Field(default=[5, 6, 13, 19], description="Button GPIO pins")

    # 릴레이 제어용 GPIO 핀 목록
    # 릴레이는 높은 전압/전류 장치를 제어하는 스위치
    GPIO_RELAY_PINS: List[int] = Field(default=[24, 25], description="Relay GPIO pins")

    # PWM(Pulse Width Modulation) 출력 핀
    # [한국어 설명]
    # PWM: 펄스 폭 변조, 디지털 신호로 아날로그 효과를 만듦
    # 용도: 모터 속도 제어, LED 밝기 조절 등
    GPIO_PWM_PIN: int = Field(default=18, description="PWM output pin")

    # 서보 모터 제어용 핀
    # [한국어 설명]
    # 서보 모터: 특정 각도로 정확하게 회전하는 모터
    # PWM 신호로 각도를 제어 (보통 0~180도)
    GPIO_SERVO_PIN: int = Field(default=12, description="Servo motor pin")

    # ============================================================================
    # I2C 설정 (I2C Configuration)
    # ============================================================================
    # [한국어 설명]
    # I2C (Inter-Integrated Circuit): 직렬 통신 프로토콜
    # 2개의 선(SDA: 데이터, SCL: 클럭)으로 여러 장치와 통신
    # 각 장치는 고유한 주소를 가짐 (0x00 ~ 0x7F)

    # I2C 버스 번호
    # 라즈베리 파이는 보통 버스 1을 사용 (GPIO 2, 3)
    I2C_BUS: int = Field(default=1, description="I2C bus number")

    # I2C LCD 디스플레이 주소
    # 0x27: 일반적인 16x2 LCD (PCF8574 I/O 확장기 사용)
    I2C_LCD_ADDRESS: int = Field(default=0x27, description="I2C LCD address")

    # I2C OLED 디스플레이 주소
    # 0x3C: 일반적인 SSD1306 OLED 모듈
    I2C_OLED_ADDRESS: int = Field(default=0x3C, description="I2C OLED address")

    # BMP280 온도/기압 센서 주소
    # 0x76 또는 0x77 (SDO 핀 연결에 따라 다름)
    I2C_BMP280_ADDRESS: int = Field(default=0x76, description="BMP280 sensor address")

    # ADS1115 ADC(아날로그-디지털 변환기) 주소
    # 0x48: 기본 주소 (ADDR 핀이 GND에 연결)
    I2C_ADS1115_ADDRESS: int = Field(default=0x48, description="ADS1115 ADC address")

    # ============================================================================
    # SPI 설정 (SPI Configuration)
    # ============================================================================
    # [한국어 설명]
    # SPI (Serial Peripheral Interface): 고속 직렬 통신 프로토콜
    # 4개의 선 사용: MOSI(출력), MISO(입력), SCLK(클럭), CS(칩 선택)
    # I2C보다 빠르지만 더 많은 핀이 필요

    # SPI 버스 번호
    SPI_BUS: int = Field(default=0, description="SPI bus number")

    # SPI 장치 번호 (CE0 또는 CE1)
    SPI_DEVICE: int = Field(default=0, description="SPI device number")

    # SPI 최대 통신 속도 (Hz)
    # 1MHz = 1,000,000 Hz
    SPI_MAX_SPEED: int = Field(default=1000000, description="SPI max speed in Hz")

    # ============================================================================
    # DHT 센서 설정 (DHT Sensor Configuration)
    # ============================================================================
    # [한국어 설명]
    # DHT (Digital Humidity and Temperature): 온습도 센서
    # DHT11: 저가형, 정확도 낮음 (습도 ±5%, 온도 ±2°C)
    # DHT22: 고정밀, 범위 넓음 (습도 ±2~5%, 온도 ±0.5°C)

    # DHT 센서 데이터 핀
    DHT_PIN: int = Field(default=4, description="DHT sensor data pin")

    # DHT 센서 종류 (DHT11 또는 DHT22)
    DHT_TYPE: str = Field(default="DHT22", description="DHT sensor type (DHT11 or DHT22)")

    # ============================================================================
    # Neopixel LED 스트립 설정 (Neopixel LED Strip Configuration)
    # ============================================================================
    # [한국어 설명]
    # Neopixel (WS2812B): 개별 주소 지정이 가능한 RGB LED
    # 하나의 데이터 핀으로 여러 LED를 개별 제어 가능
    # 각 LED마다 RGB 색상을 독립적으로 설정

    # Neopixel 데이터 핀
    # GPIO 21: PWM0 하드웨어 채널, 안정적인 타이밍 제공
    NEOPIXEL_PIN: int = Field(default=21, description="Neopixel data pin")

    # LED 개수
    NEOPIXEL_COUNT: int = Field(default=8, description="Number of Neopixel LEDs")

    # ============================================================================
    # 정적 파일 설정 (Static Files Configuration)
    # ============================================================================

    # 정적 파일 디렉토리 (React 빌드 결과물 위치)
    STATIC_DIR: Path = Field(default=Path("static"), description="Static files directory")

    # ============================================================================
    # Pydantic 설정 클래스 (Pydantic Config Class)
    # ============================================================================

    class Config:
        """
        Pydantic 설정 (Pydantic Configuration)

        [한국어 설명]
        BaseSettings의 동작을 커스터마이징하는 내부 클래스입니다.

        주요 설정:
        - env_file: 환경 변수를 읽어올 파일 (.env)
        - env_file_encoding: 파일 인코딩 (UTF-8)
        - case_sensitive: 변수명 대소문자 구분 여부
        """
        # .env 파일 경로
        # 프로젝트 루트에 .env 파일이 있으면 자동으로 로드됨
        env_file = ".env"

        # .env 파일 인코딩
        env_file_encoding = "utf-8"

        # 대소문자 구분
        # True: PORT와 port를 다른 변수로 취급
        case_sensitive = True

    # ============================================================================
    # 프로퍼티 (Properties)
    # ============================================================================
    # [한국어 설명]
    # @property 데코레이터: 메서드를 속성처럼 접근할 수 있게 함
    # 예: settings.is_raspberry_pi 처럼 () 없이 호출

    @property
    def is_raspberry_pi(self) -> bool:
        """
        라즈베리 파이 여부 확인 (Check if Running on Raspberry Pi)

        [한국어 설명]
        현재 시스템이 라즈베리 파이인지 확인합니다.
        위에서 정의한 is_raspberry_pi() 함수를 호출합니다.

        반환값:
            bool: 라즈베리 파이이면 True, 아니면 False
        """
        return is_raspberry_pi()

    @property
    def platform_info(self) -> dict:
        """
        플랫폼 정보 조회 (Get Platform Information)

        [한국어 설명]
        현재 실행 환경의 상세 정보를 딕셔너리로 반환합니다.
        API 응답이나 디버깅에 유용합니다.

        반환값:
            dict: 플랫폼 정보를 담은 딕셔너리
                - system: OS 이름 (Windows, Linux, Darwin 등)
                - release: OS 버전
                - machine: CPU 아키텍처 (x86_64, armv7l 등)
                - processor: 프로세서 정보
                - is_raspberry_pi: 라즈베리 파이 여부
                - simulation_mode: 시뮬레이션 모드 여부
        """
        return {
            "system": platform.system(),          # OS 이름
            "release": platform.release(),        # OS 버전
            "machine": platform.machine(),        # CPU 아키텍처
            "processor": platform.processor(),    # 프로세서 정보
            "is_raspberry_pi": self.is_raspberry_pi,
            "simulation_mode": self.SIMULATION_MODE
        }


# ============================================================================
# 전역 설정 인스턴스 생성 (Create Global Settings Instance)
# ============================================================================

# Settings 클래스의 싱글톤 인스턴스
# [한국어 설명]
# 앱 전체에서 이 settings 객체를 import하여 사용
# 인스턴스 생성 시점에 환경 변수와 .env 파일에서 값을 읽어옴
#
# 사용 예:
#   from app.core.config import settings
#   print(settings.PORT)  # 8000
#   print(settings.SIMULATION_MODE)  # True 또는 False
settings = Settings()
