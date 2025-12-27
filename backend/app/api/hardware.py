"""
Hardware API Routes (하드웨어 API 라우트)
==========================================

[한국어 설명]
하드웨어 제어를 위한 REST API 엔드포인트들을 정의합니다.

이 모듈에서 제공하는 기능:
1. GPIO 제어 - LED, 버튼, 릴레이
2. PWM 제어 - 모터 속도, 서보 각도
3. 센서 읽기 - 온습도(DHT), 거리(초음파), 동작감지(PIR)
4. I2C 통신 - LCD, OLED, BMP280, ADS1115
5. SPI 통신 - MCP3008 ADC
6. NeoPixel LED 스트립 제어
7. 시뮬레이션 모드 제어

REST API란?
- HTTP 프로토콜을 사용한 웹 API 설계 방식
- GET: 데이터 조회 (읽기)
- POST: 데이터 생성/변경 (쓰기)
- PUT: 데이터 전체 수정
- DELETE: 데이터 삭제

[English Description]
REST API endpoints for hardware control.
Handles GPIO, PWM, sensors, I2C, SPI, NeoPixel, and simulation.
"""

# ============================================================================
# 라이브러리 임포트 (Import Libraries)
# ============================================================================

# typing: Python 타입 힌트를 위한 모듈
# Dict[str, Any]: 문자열 키와 임의의 값을 가진 딕셔너리
# Optional[int]: int 또는 None이 될 수 있는 타입
# List[Dict]: 딕셔너리의 리스트
from typing import Dict, Any, Optional, List

# FastAPI 핵심 클래스들
# APIRouter: 엔드포인트 그룹화를 위한 라우터
# HTTPException: HTTP 에러 응답을 발생시키는 예외 클래스
# Query: URL 쿼리 파라미터를 정의하는 함수
from fastapi import APIRouter, HTTPException, Query

# Pydantic: 데이터 검증(validation)과 직렬화를 위한 라이브러리
# BaseModel: Pydantic 모델의 기본 클래스 (요청/응답 스키마 정의)
# Field: 필드에 대한 추가 정보와 제약 조건 정의
from pydantic import BaseModel, Field

# 프로젝트 내부 모듈 임포트
# hardware_manager: 모든 하드웨어 컨트롤러를 통합 관리하는 싱글톤 객체
from app.hardware.manager import hardware_manager

# NeopixelEffect: NeoPixel LED 효과 종류를 정의한 열거형(Enum)
from app.hardware.neopixel_controller import NeopixelEffect

# data_logger: 센서 데이터와 이벤트를 DB에 저장하는 서비스
from app.services.data_logger import data_logger

# LogLevel: 로그 레벨을 정의한 열거형 (INFO, WARNING, ERROR 등)
from app.models.system_log import LogLevel

# get_logger: 로거 인스턴스를 가져오는 함수
from app.core.logging_config import get_logger

# 이 모듈용 로거 생성
logger = get_logger(__name__)

# 라우터 인스턴스 생성
# 이 router는 __init__.py에서 api_router에 포함됨
router = APIRouter()


# ============================================================================
# Pydantic 모델 정의 (Pydantic Models)
# ============================================================================
# [한국어 설명]
# Pydantic 모델은 API 요청/응답의 데이터 구조를 정의합니다.
#
# Pydantic의 장점:
# 1. 자동 데이터 검증 (타입 체크, 범위 체크 등)
# 2. 자동 JSON 직렬화/역직렬화
# 3. Swagger 문서 자동 생성
# 4. IDE 자동완성 지원
#
# Field() 함수:
# - ...: 필수 필드 (값이 반드시 있어야 함)
# - default=값: 기본값이 있는 선택 필드
# - ge=0: 0 이상 (greater than or equal)
# - le=100: 100 이하 (less than or equal)
# - description: API 문서에 표시될 설명

class LEDControlRequest(BaseModel):
    """
    LED 제어 요청 모델 (LED Control Request Model)

    [한국어 설명]
    LED의 상태를 변경할 때 사용하는 요청 본문(Request Body) 스키마입니다.

    사용 예 (HTTP 요청):
    POST /api/hardware/gpio/led
    Content-Type: application/json

    {
        "index": 0,
        "state": true
    }
    """
    # LED 인덱스 (0-7 범위)
    # ...: 필수 필드, ge=0: 최소값 0, le=7: 최대값 7
    index: int = Field(..., ge=0, le=7, description="LED index (0-7)")

    # LED 상태 (true=켜짐, false=꺼짐)
    state: bool = Field(..., description="LED state (true=on, false=off)")


class RelayControlRequest(BaseModel):
    """
    릴레이 제어 요청 모델 (Relay Control Request Model)

    [한국어 설명]
    릴레이(전자 스위치)의 상태를 변경할 때 사용합니다.
    릴레이는 저전압 신호로 고전압 장치를 제어하는 데 사용됩니다.
    예: 220V 전등, 모터 등을 라즈베리 파이의 3.3V 신호로 제어
    """
    index: int = Field(..., ge=0, le=3, description="Relay index (0-3)")
    state: bool = Field(..., description="Relay state (true=on, false=off)")


class MotorControlRequest(BaseModel):
    """
    모터 제어 요청 모델 (Motor Control Request Model)

    [한국어 설명]
    DC 모터의 속도를 PWM으로 제어합니다.
    0% = 정지, 100% = 최대 속도
    """
    speed: float = Field(..., ge=0, le=100, description="Motor speed (0-100%)")


class ServoControlRequest(BaseModel):
    """
    서보 모터 제어 요청 모델 (Servo Control Request Model)

    [한국어 설명]
    서보 모터의 각도를 제어합니다.
    서보 모터는 정확한 각도로 회전할 수 있는 특수 모터입니다.
    일반적으로 0~180도 범위로 제어합니다.
    """
    angle: float = Field(..., ge=0, le=180, description="Servo angle (0-180 degrees)")


class NeopixelColorRequest(BaseModel):
    """
    NeoPixel 색상 설정 요청 모델 (NeoPixel Color Request Model)

    [한국어 설명]
    WS2812B NeoPixel LED의 색상을 설정합니다.
    개별 LED 또는 전체 LED의 색상을 변경할 수 있습니다.

    색상 지정 방법:
    1. 색상 이름: "red", "green", "blue", "white" 등
    2. 16진수 코드: "#FF0000" (빨강), "#00FF00" (녹색)
    """
    # index가 None이면 모든 LED에 적용
    index: Optional[int] = Field(None, ge=0, description="LED index (None for all)")

    # 색상 값 (이름 또는 16진수 코드)
    color: str = Field(..., description="Color name or hex code (#RRGGBB)")


class NeopixelEffectRequest(BaseModel):
    """
    NeoPixel 효과 요청 모델 (NeoPixel Effect Request Model)

    [한국어 설명]
    NeoPixel LED 스트립에 애니메이션 효과를 적용합니다.

    사용 가능한 효과:
    - rainbow: 무지개 색상 순환
    - chase: 쫓아가는 불빛 효과
    - pulse: 밝기 펄스 효과
    - breathe: 숨쉬기 효과
    """
    effect: str = Field(..., description="Effect name")
    speed: Optional[float] = Field(0.05, description="Effect speed")


class LCDWriteRequest(BaseModel):
    """
    LCD 쓰기 요청 모델 (LCD Write Request Model)

    [한국어 설명]
    I2C LCD 디스플레이에 텍스트를 출력합니다.
    일반적인 16x2 LCD: 2행, 16열
    일반적인 20x4 LCD: 4행, 20열
    """
    # 표시할 텍스트 (최대 20자)
    text: str = Field(..., max_length=20, description="Text to display")

    # 행 번호 (0부터 시작)
    row: int = Field(0, ge=0, le=3, description="Row number")

    # 열 번호 (0부터 시작)
    col: int = Field(0, ge=0, le=19, description="Column number")


class SimulationValueRequest(BaseModel):
    """
    시뮬레이션 값 설정 요청 모델 (Simulation Value Request Model)

    [한국어 설명]
    시뮬레이션 모드에서 센서 값을 수동으로 설정할 때 사용합니다.
    테스트나 개발 중에 특정 센서 값을 시뮬레이션할 수 있습니다.

    모든 필드가 Optional이므로 변경하고 싶은 값만 전송하면 됩니다.
    """
    temperature: Optional[float] = None  # 온도 (°C)
    humidity: Optional[float] = None     # 습도 (%)
    distance: Optional[float] = None     # 거리 (cm)
    motion: Optional[bool] = None        # 동작 감지 여부
    light: Optional[int] = None          # 조도 (0-1023)


# ============================================================================
# 상태 조회 엔드포인트 (Status Endpoints)
# ============================================================================
# [한국어 설명]
# @router.get(): HTTP GET 요청을 처리하는 엔드포인트 데코레이터
# async def: 비동기 함수 정의 (FastAPI는 비동기 처리 권장)
# -> Dict[str, Any]: 반환 타입 힌트 (문자열 키 딕셔너리)

@router.get("/status")
async def get_hardware_status() -> Dict[str, Any]:
    """
    모든 하드웨어 컨트롤러 상태 조회 (Get All Hardware Controller Status)

    [한국어 설명]
    모든 하드웨어 컨트롤러(GPIO, PWM, I2C 등)의 현재 상태를 반환합니다.
    초기화 여부, 시뮬레이션 모드 여부 등의 정보를 포함합니다.

    API 경로: GET /api/hardware/status

    응답 예시:
    {
        "gpio": {"initialized": true, "simulation": false},
        "pwm": {"initialized": true, "simulation": false},
        "sensors": {"initialized": true, "simulation": true},
        ...
    }
    """
    return hardware_manager.get_status()


@router.get("/data")
async def get_current_data() -> Dict[str, Any]:
    """
    현재 하드웨어 데이터 스냅샷 조회 (Get Current Hardware Data Snapshot)

    [한국어 설명]
    모든 하드웨어의 현재 상태 데이터를 한 번에 가져옵니다.
    LED 상태, 센서 값, 모터 속도 등 모든 정보를 포함합니다.

    API 경로: GET /api/hardware/data
    """
    return hardware_manager.current_data.to_dict()


# ============================================================================
# GPIO 엔드포인트 (GPIO Endpoints)
# ============================================================================
# [한국어 설명]
# GPIO (General Purpose Input/Output): 범용 입출력 핀
# 라즈베리 파이의 GPIO 핀으로 LED, 버튼, 릴레이 등을 제어합니다.

@router.get("/gpio")
async def get_gpio_status() -> Dict[str, Any]:
    """
    GPIO 상태 조회 (Get GPIO Status)

    [한국어 설명]
    모든 GPIO 장치(LED, 버튼, 릴레이)의 현재 상태를 조회합니다.

    API 경로: GET /api/hardware/gpio

    응답 예시:
    {
        "leds": [true, false, false, true],
        "buttons": [false, false, false, false],
        "relays": [true, false]
    }
    """
    return {
        "leds": hardware_manager.gpio.get_led_states(),      # LED 상태 배열
        "buttons": hardware_manager.gpio.get_button_states(), # 버튼 상태 배열
        "relays": hardware_manager.gpio.get_relay_states()    # 릴레이 상태 배열
    }


@router.post("/gpio/led")
async def control_led(request: LEDControlRequest) -> Dict[str, Any]:
    """
    LED 제어 (Control LED)

    [한국어 설명]
    @router.post(): HTTP POST 요청을 처리
    request: LEDControlRequest: Pydantic 모델을 매개변수로 받으면
                                FastAPI가 자동으로 요청 본문을 파싱하고 검증

    API 경로: POST /api/hardware/gpio/led

    요청 본문:
    {
        "index": 0,
        "state": true
    }

    동작 과정:
    1. 요청 데이터 검증 (Pydantic이 자동 수행)
    2. 하드웨어 매니저를 통해 LED 상태 변경
    3. 성공 시 데이터베이스에 변경 이력 기록
    4. 시스템 로그에 이벤트 기록
    5. 결과 반환
    """
    # 하드웨어 매니저를 통해 LED 상태 변경
    # await: 비동기 함수 호출, 완료될 때까지 대기
    success = await hardware_manager.set_led(request.index, request.state)

    # 성공 시 로그 기록
    if success:
        # 장치 상태 변경 이력을 DB에 저장
        await data_logger.log_device_change(
            device_type="led",                    # 장치 종류
            device_id=str(request.index),         # 장치 ID (LED 인덱스)
            new_state={"on": request.state},      # 새로운 상태
            changed_by="user"                     # 변경한 주체
        )

        # 시스템 로그에 이벤트 기록
        await data_logger.log_system_event(
            LogLevel.INFO,                        # 로그 레벨
            "hardware.gpio",                      # 컴포넌트 이름
            f"LED {request.index} set to {'ON' if request.state else 'OFF'}",  # 메시지
            user_action=True                      # 사용자 액션 여부
        )

    # 응답 반환
    # FastAPI가 자동으로 JSON으로 직렬화
    return {
        "success": success,
        "led_index": request.index,
        "state": request.state
    }


@router.post("/gpio/led/all")
async def control_all_leds(state: bool = Query(..., description="LED state")) -> Dict[str, Any]:
    """
    모든 LED 일괄 제어 (Control All LEDs)

    [한국어 설명]
    Query(): URL 쿼리 파라미터를 정의
    - 사용 예: POST /api/hardware/gpio/led/all?state=true
    - ...: 필수 파라미터
    - description: API 문서에 표시될 설명

    모든 LED를 한 번에 켜거나 끕니다.

    API 경로: POST /api/hardware/gpio/led/all?state=true
    """
    success = await hardware_manager.gpio.set_all_leds(state)
    return {
        "success": success,
        "state": state,
        "leds": hardware_manager.gpio.get_led_states()
    }


@router.post("/gpio/relay")
async def control_relay(request: RelayControlRequest) -> Dict[str, Any]:
    """
    릴레이 제어 (Control Relay)

    [한국어 설명]
    릴레이를 켜거나 끕니다.
    LED 제어와 동일한 패턴으로 구현되어 있습니다.

    API 경로: POST /api/hardware/gpio/relay
    """
    success = await hardware_manager.set_relay(request.index, request.state)

    if success:
        await data_logger.log_device_change(
            device_type="relay",
            device_id=str(request.index),
            new_state={"on": request.state},
            changed_by="user"
        )
        await data_logger.log_system_event(
            LogLevel.INFO,
            "hardware.gpio",
            f"Relay {request.index} set to {'ON' if request.state else 'OFF'}",
            user_action=True
        )

    return {
        "success": success,
        "relay_index": request.index,
        "state": request.state
    }


# ============================================================================
# PWM 엔드포인트 (PWM Endpoints)
# ============================================================================
# [한국어 설명]
# PWM (Pulse Width Modulation): 펄스 폭 변조
# 디지털 신호를 이용해 아날로그 효과를 만드는 기술
# 예: LED 밝기 조절, 모터 속도 제어, 서보 각도 제어

@router.get("/pwm")
async def get_pwm_status() -> Dict[str, Any]:
    """
    PWM 상태 조회 (Get PWM Status)

    [한국어 설명]
    현재 PWM 출력 상태 (모터 속도, 서보 각도 등)를 조회합니다.

    API 경로: GET /api/hardware/pwm
    """
    return {
        "motor_speed": hardware_manager.pwm.get_motor_speed(),  # 모터 속도 (0-100%)
        "servo_angle": hardware_manager.pwm.get_servo_angle(),  # 서보 각도 (0-180°)
        "outputs": hardware_manager.pwm.get_pwm_states()        # 전체 PWM 상태
    }


@router.post("/pwm/motor")
async def control_motor(request: MotorControlRequest) -> Dict[str, Any]:
    """
    모터 속도 제어 (Control Motor Speed)

    [한국어 설명]
    DC 모터의 속도를 0-100% 범위로 설정합니다.
    PWM 듀티 사이클을 조절하여 속도를 제어합니다.

    API 경로: POST /api/hardware/pwm/motor
    """
    success = await hardware_manager.set_motor_speed(request.speed)

    if success:
        await data_logger.log_device_change(
            device_type="motor",
            device_id="0",
            new_state={"speed": request.speed},
            changed_by="user"
        )

    return {
        "success": success,
        "speed": request.speed
    }


@router.post("/pwm/servo")
async def control_servo(request: ServoControlRequest) -> Dict[str, Any]:
    """
    서보 각도 제어 (Control Servo Angle)

    [한국어 설명]
    서보 모터의 각도를 0-180도 범위로 설정합니다.
    서보 모터는 PWM 신호의 펄스 폭에 따라 정확한 각도로 회전합니다.

    일반적인 서보 PWM:
    - 1ms 펄스 = 0도
    - 1.5ms 펄스 = 90도
    - 2ms 펄스 = 180도

    API 경로: POST /api/hardware/pwm/servo
    """
    success = await hardware_manager.set_servo_angle(request.angle)

    if success:
        await data_logger.log_device_change(
            device_type="servo",
            device_id="0",
            new_state={"angle": request.angle},
            changed_by="user"
        )

    return {
        "success": success,
        "angle": request.angle
    }


# ============================================================================
# 센서 엔드포인트 (Sensor Endpoints)
# ============================================================================
# [한국어 설명]
# 다양한 센서에서 데이터를 읽어오는 엔드포인트들입니다.
# - DHT22: 온습도 센서
# - HC-SR04: 초음파 거리 센서
# - PIR: 적외선 동작 감지 센서

@router.get("/sensors")
async def get_sensor_readings() -> Dict[str, Any]:
    """
    모든 센서 데이터 조회 (Get All Sensor Readings)

    [한국어 설명]
    연결된 모든 센서의 현재 값을 한 번에 조회합니다.

    API 경로: GET /api/hardware/sensors

    응답 예시:
    {
        "temperature": 25.5,
        "humidity": 60.0,
        "distance": 150.5,
        "motion": false,
        "light": 512
    }
    """
    return await hardware_manager.sensors.read_all()


@router.get("/sensors/dht")
async def get_dht_reading() -> Dict[str, Any]:
    """
    DHT 온습도 센서 조회 (Get DHT Temperature and Humidity)

    [한국어 설명]
    DHT11 또는 DHT22 센서에서 온도와 습도를 읽습니다.

    API 경로: GET /api/hardware/sensors/dht

    응답 예시:
    {
        "temperature": 25.5,
        "humidity": 60.0
    }

    HTTPException 발생 조건:
    - 센서 읽기 실패 시 500 에러 반환
    """
    data = await hardware_manager.sensors.read_dht()
    if data:
        return data
    # raise: 예외를 발생시킴
    # HTTPException(status_code=500): HTTP 500 에러 응답
    raise HTTPException(status_code=500, detail="Failed to read DHT sensor")


@router.get("/sensors/distance")
async def get_distance() -> Dict[str, float]:
    """
    초음파 거리 센서 조회 (Get Ultrasonic Distance Reading)

    [한국어 설명]
    HC-SR04 초음파 센서로 거리를 측정합니다.

    초음파 거리 측정 원리:
    1. 트리거 핀에 초음파 펄스 발생
    2. 초음파가 물체에 반사되어 돌아옴
    3. 에코 핀에서 반사파 수신
    4. 왕복 시간 / 2 × 음속 = 거리

    API 경로: GET /api/hardware/sensors/distance
    """
    distance = await hardware_manager.sensors.read_ultrasonic()
    if distance is not None:
        return {"distance": distance, "unit": "cm"}
    raise HTTPException(status_code=500, detail="Failed to read distance sensor")


@router.get("/sensors/motion")
async def get_motion() -> Dict[str, bool]:
    """
    PIR 동작 감지 센서 조회 (Get PIR Motion Status)

    [한국어 설명]
    PIR (Passive Infrared) 센서로 동작(움직임)을 감지합니다.
    PIR 센서는 적외선 변화를 감지하여 사람이나 동물의 움직임을 탐지합니다.

    API 경로: GET /api/hardware/sensors/motion
    """
    motion = await hardware_manager.sensors.read_pir()
    return {"motion": motion}


# ============================================================================
# I2C 엔드포인트 (I2C Endpoints)
# ============================================================================
# [한국어 설명]
# I2C (Inter-Integrated Circuit): 2선식 직렬 통신 프로토콜
# - SDA (Serial Data): 데이터 라인
# - SCL (Serial Clock): 클럭 라인
# 여러 장치를 같은 버스에 연결하고 주소로 구분

@router.get("/i2c/devices")
async def get_i2c_devices() -> Dict[str, Any]:
    """
    I2C 장치 목록 조회 (Get Detected I2C Devices)

    [한국어 설명]
    현재 감지된 I2C 장치들의 정보를 반환합니다.

    API 경로: GET /api/hardware/i2c/devices
    """
    return hardware_manager.i2c.get_devices()


@router.get("/i2c/scan")
async def scan_i2c() -> List[int]:
    """
    I2C 버스 스캔 (Scan I2C Bus for Devices)

    [한국어 설명]
    I2C 버스를 스캔하여 연결된 모든 장치의 주소를 찾습니다.
    각 주소로 응답이 오는지 확인하는 방식으로 탐지합니다.

    API 경로: GET /api/hardware/i2c/scan

    응답 예시: [39, 60, 72, 118]  (10진수 주소 목록)
    """
    return await hardware_manager.i2c.scan_devices()


@router.get("/i2c/bmp280")
async def get_bmp280() -> Dict[str, Any]:
    """
    BMP280 센서 조회 (Get BMP280 Temperature and Pressure)

    [한국어 설명]
    BMP280 I2C 센서에서 온도와 기압을 읽습니다.

    BMP280 센서 특징:
    - 온도 측정 범위: -40°C ~ +85°C
    - 기압 측정 범위: 300 ~ 1100 hPa
    - 해발고도 계산에 사용 가능

    API 경로: GET /api/hardware/i2c/bmp280
    """
    data = await hardware_manager.i2c.read_bmp280()
    if data:
        return data
    raise HTTPException(status_code=500, detail="Failed to read BMP280 sensor")


@router.get("/i2c/adc")
async def get_adc_values() -> Dict[int, float]:
    """
    ADS1115 ADC 채널 조회 (Get All ADC Channel Values)

    [한국어 설명]
    ADS1115 I2C ADC(Analog-to-Digital Converter)의 모든 채널 값을 읽습니다.

    ADS1115 특징:
    - 16비트 해상도
    - 4채널 (싱글엔드) 또는 2채널 (차동)
    - PGA(Programmable Gain Amplifier) 내장

    API 경로: GET /api/hardware/i2c/adc
    """
    return await hardware_manager.i2c.read_all_adc_channels()


# ============================================================================
# SPI 엔드포인트 (SPI Endpoints)
# ============================================================================
# [한국어 설명]
# SPI (Serial Peripheral Interface): 4선식 고속 직렬 통신
# - MOSI (Master Out Slave In): 마스터 → 슬레이브 데이터
# - MISO (Master In Slave Out): 슬레이브 → 마스터 데이터
# - SCLK (Serial Clock): 클럭
# - CS/SS (Chip Select): 슬레이브 선택

@router.get("/spi/mcp3008")
async def get_mcp3008_values() -> Dict[int, float]:
    """
    MCP3008 ADC 채널 조회 (Get All MCP3008 ADC Channel Values)

    [한국어 설명]
    MCP3008 SPI ADC의 모든 8채널 값을 읽습니다.

    MCP3008 특징:
    - 10비트 해상도 (0-1023)
    - 8채널
    - SPI 통신 (I2C보다 빠름)
    - 최대 200ksps 샘플링 속도

    API 경로: GET /api/hardware/spi/mcp3008
    """
    return await hardware_manager.spi.read_all_mcp3008_channels()


# ============================================================================
# 디스플레이 엔드포인트 (Display Endpoints)
# ============================================================================

@router.get("/display/lcd")
async def get_lcd_info() -> Dict[str, Any]:
    """
    LCD 정보 조회 (Get LCD Display Info and Content)

    [한국어 설명]
    I2C LCD 디스플레이의 정보와 현재 표시 내용을 조회합니다.

    API 경로: GET /api/hardware/display/lcd
    """
    return hardware_manager.display.get_lcd_info()


@router.post("/display/lcd/write")
async def write_lcd(request: LCDWriteRequest) -> Dict[str, Any]:
    """
    LCD에 텍스트 쓰기 (Write Text to LCD)

    [한국어 설명]
    LCD의 지정된 위치에 텍스트를 출력합니다.

    API 경로: POST /api/hardware/display/lcd/write
    """
    success = await hardware_manager.display.lcd_write(
        request.text, request.row, request.col
    )
    return {
        "success": success,
        "content": hardware_manager.display.get_lcd_content()
    }


@router.post("/display/lcd/clear")
async def clear_lcd() -> Dict[str, Any]:
    """
    LCD 화면 지우기 (Clear LCD Display)

    [한국어 설명]
    LCD 화면의 모든 내용을 지웁니다.

    API 경로: POST /api/hardware/display/lcd/clear
    """
    success = await hardware_manager.display.lcd_clear()
    return {"success": success}


@router.get("/display/oled")
async def get_oled_info() -> Dict[str, Any]:
    """
    OLED 정보 조회 (Get OLED Display Info)

    [한국어 설명]
    OLED 디스플레이의 정보를 조회합니다.
    일반적으로 SSD1306 컨트롤러를 사용하는 128x64 OLED입니다.

    API 경로: GET /api/hardware/display/oled
    """
    return hardware_manager.display.get_oled_info()


# ============================================================================
# NeoPixel 엔드포인트 (NeoPixel Endpoints)
# ============================================================================
# [한국어 설명]
# NeoPixel (WS2812B): 개별 주소 지정이 가능한 RGB LED
# 하나의 데이터 라인으로 여러 LED를 개별 제어할 수 있음

@router.get("/neopixel")
async def get_neopixel_status() -> Dict[str, Any]:
    """
    NeoPixel 상태 조회 (Get NeoPixel Status)

    [한국어 설명]
    NeoPixel LED 스트립의 현재 상태를 조회합니다.
    각 LED의 색상, 전체 밝기, 효과 실행 여부 등을 반환합니다.

    API 경로: GET /api/hardware/neopixel
    """
    return {
        "leds": hardware_manager.neopixel.get_led_states(),    # 각 LED 상태
        "brightness": hardware_manager.neopixel._brightness,    # 전체 밝기
        "effect_running": hardware_manager.neopixel._effect_running  # 효과 실행 중 여부
    }


@router.post("/neopixel/color")
async def set_neopixel_color(request: NeopixelColorRequest) -> Dict[str, Any]:
    """
    NeoPixel 색상 설정 (Set NeoPixel Color)

    [한국어 설명]
    NeoPixel LED의 색상을 설정합니다.
    index가 지정되면 해당 LED만, 아니면 모든 LED의 색상을 변경합니다.

    색상 지정 방법:
    1. 사전 정의된 색상 이름: "red", "green", "blue" 등
    2. 16진수 코드: "#FF0000", "#00FF00", "#0000FF" 등

    API 경로: POST /api/hardware/neopixel/color
    """
    # 색상 파싱을 위한 헬퍼 모듈 임포트
    from app.hardware.neopixel_controller import COLORS, RGBColor

    # 색상 문자열을 RGB 값으로 변환
    if request.color.lower() in COLORS:
        # 사전 정의된 색상 이름 (대소문자 무관)
        color = COLORS[request.color.lower()]
    elif request.color.startswith("#"):
        # 16진수 색상 코드
        color = RGBColor.from_hex(request.color)
    else:
        # 유효하지 않은 색상
        raise HTTPException(status_code=400, detail="Invalid color")

    # 색상 적용
    if request.index is not None:
        # 특정 LED만 변경
        success = await hardware_manager.neopixel.set_pixel(request.index, color)
    else:
        # 모든 LED 변경
        success = await hardware_manager.neopixel.set_all(color)

    return {
        "success": success,
        "leds": hardware_manager.neopixel.get_led_states()
    }


@router.post("/neopixel/effect")
async def start_neopixel_effect(request: NeopixelEffectRequest) -> Dict[str, Any]:
    """
    NeoPixel 효과 시작 (Start NeoPixel Effect)

    [한국어 설명]
    NeoPixel LED 스트립에 애니메이션 효과를 시작합니다.

    사용 가능한 효과:
    - rainbow: 무지개 색상 순환
    - chase: 쫓아가는 불빛
    - pulse: 밝기 펄스
    - breathe: 숨쉬기 효과

    API 경로: POST /api/hardware/neopixel/effect
    """
    try:
        # 문자열을 Enum 값으로 변환
        effect = NeopixelEffect(request.effect)
        success = await hardware_manager.neopixel.start_effect(effect, speed=request.speed)
        return {
            "success": success,
            "effect": request.effect
        }
    except ValueError:
        # 유효하지 않은 효과 이름
        available = [e.value for e in NeopixelEffect]  # 사용 가능한 효과 목록
        raise HTTPException(
            status_code=400,
            detail=f"Invalid effect. Available: {available}"
        )


@router.post("/neopixel/stop")
async def stop_neopixel_effect() -> Dict[str, Any]:
    """
    NeoPixel 효과 중지 (Stop Current NeoPixel Effect)

    [한국어 설명]
    현재 실행 중인 NeoPixel 효과를 중지합니다.

    API 경로: POST /api/hardware/neopixel/stop
    """
    success = await hardware_manager.neopixel.stop_effect()
    return {"success": success}


@router.post("/neopixel/clear")
async def clear_neopixel() -> Dict[str, Any]:
    """
    NeoPixel 끄기 (Turn Off All NeoPixels)

    [한국어 설명]
    모든 NeoPixel LED를 끕니다.
    진행 중인 효과도 함께 중지됩니다.

    API 경로: POST /api/hardware/neopixel/clear
    """
    await hardware_manager.neopixel.stop_effect()  # 효과 먼저 중지
    success = await hardware_manager.neopixel.clear()  # LED 끄기
    return {"success": success}


# ============================================================================
# 시뮬레이션 엔드포인트 (Simulation Endpoints)
# ============================================================================
# [한국어 설명]
# 시뮬레이션 모드에서만 사용 가능한 엔드포인트들입니다.
# 실제 하드웨어 없이 개발/테스트할 때 센서 값을 수동으로 설정할 수 있습니다.

@router.post("/simulation/values")
async def set_simulation_values(request: SimulationValueRequest) -> Dict[str, Any]:
    """
    시뮬레이션 센서 값 설정 (Set Simulation Values for Testing)

    [한국어 설명]
    시뮬레이션 모드에서 센서 값을 수동으로 설정합니다.
    실제 하드웨어 없이 특정 시나리오를 테스트할 때 유용합니다.

    예: 온도 경고 테스트를 위해 temperature를 80으로 설정

    API 경로: POST /api/hardware/simulation/values

    주의: 시뮬레이션 모드가 아니면 400 에러 반환
    """
    # 시뮬레이션 모드 확인
    if not hardware_manager.is_simulation:
        raise HTTPException(
            status_code=400,
            detail="Not in simulation mode"
        )

    # 변경된 값을 추적
    updates = {}

    # 각 값이 제공되면 시뮬레이션 값으로 설정
    if request.temperature is not None:
        hardware_manager.sensors.set_simulated_values(temperature=request.temperature)
        updates["temperature"] = request.temperature

    if request.humidity is not None:
        hardware_manager.sensors.set_simulated_values(humidity=request.humidity)
        updates["humidity"] = request.humidity

    if request.distance is not None:
        hardware_manager.sensors.set_simulated_values(distance=request.distance)
        updates["distance"] = request.distance

    if request.motion is not None:
        hardware_manager.sensors.set_simulated_values(motion=request.motion)
        updates["motion"] = request.motion

    if request.light is not None:
        hardware_manager.sensors.set_simulated_values(light=request.light)
        updates["light"] = request.light

    return {
        "success": True,
        "updates": updates
    }


@router.post("/simulation/button/{index}")
async def simulate_button_press(index: int) -> Dict[str, Any]:
    """
    버튼 누름 시뮬레이션 (Simulate Button Press)

    [한국어 설명]
    경로 매개변수 {index}:
    - URL 경로의 일부로 값을 받음
    - 예: POST /api/hardware/simulation/button/0 → index = 0

    시뮬레이션 모드에서 버튼 누름을 가상으로 발생시킵니다.

    API 경로: POST /api/hardware/simulation/button/{index}
    """
    if not hardware_manager.is_simulation:
        raise HTTPException(status_code=400, detail="Not in simulation mode")

    await hardware_manager.gpio.simulate_button_press(index)
    return {"success": True, "button_index": index}
