# 백엔드 개발 가이드

## 1. 디렉토리 구조

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # 애플리케이션 엔트리포인트
│   ├── api/                    # API 라우트
│   │   ├── __init__.py
│   │   ├── hardware.py         # 하드웨어 제어 API
│   │   ├── system.py           # 시스템 모니터링 API
│   │   ├── data.py             # 데이터 조회 API
│   │   └── websocket.py        # WebSocket 엔드포인트
│   ├── core/                   # 핵심 설정
│   │   ├── __init__.py
│   │   ├── config.py           # 환경 설정
│   │   └── logging_config.py   # 로깅 설정
│   ├── hardware/               # 하드웨어 컨트롤러
│   │   ├── __init__.py
│   │   ├── base.py             # 베이스 클래스
│   │   ├── manager.py          # 하드웨어 매니저
│   │   ├── gpio_controller.py
│   │   ├── pwm_controller.py
│   │   ├── i2c_controller.py
│   │   ├── spi_controller.py
│   │   ├── sensor_controller.py
│   │   ├── display_controller.py
│   │   └── neopixel_controller.py
│   ├── models/                 # 데이터베이스 모델
│   │   ├── __init__.py
│   │   ├── database.py         # DB 연결
│   │   ├── sensor_data.py
│   │   ├── system_log.py
│   │   └── device_state.py
│   └── services/               # 비즈니스 로직
│       ├── __init__.py
│       ├── system_monitor.py
│       ├── websocket_manager.py
│       └── data_logger.py
├── data/                       # 데이터베이스 파일
├── logs/                       # 로그 파일
├── static/                     # React 빌드 파일
├── requirements.txt            # Python 의존성
└── .env                        # 환경 변수
```

---

## 2. 핵심 모듈 상세

### 2.1 main.py - 애플리케이션 엔트리포인트

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시
    await init_database()
    await hardware_manager.initialize()
    await system_monitor.start()
    await data_logger.start()

    yield  # 애플리케이션 실행

    # 종료 시
    await hardware_manager.cleanup()
    await system_monitor.stop()
    await data_logger.stop()

app = FastAPI(
    title="Raspberry Pi HMI",
    lifespan=lifespan
)

# API 라우트 등록
app.include_router(api_router, prefix="/api")

# React SPA 서빙
app.mount("/", StaticFiles(directory="static", html=True))
```

### 2.2 config.py - 환경 설정

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # 하드웨어 설정
    SIMULATION_MODE: bool = True  # 라즈베리파이에서 자동 False
    HARDWARE_UPDATE_INTERVAL: float = 0.5
    DATA_LOG_INTERVAL: float = 5.0

    # GPIO 핀 설정 (BCM 번호)
    LED_PINS: list = [17, 27, 22, 23]
    BUTTON_PINS: list = [5, 6, 13, 19]
    RELAY_PINS: list = [24, 25]
    PWM_MOTOR_PIN: int = 18
    PWM_SERVO_PIN: int = 12
    DHT_PIN: int = 4
    NEOPIXEL_PIN: int = 21

    # I2C 설정
    I2C_BUS: int = 1
    I2C_BMP280_ADDRESS: int = 0x76
    I2C_ADS1115_ADDRESS: int = 0x48
    I2C_OLED_ADDRESS: int = 0x3C
    I2C_LCD_ADDRESS: int = 0x27

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

---

## 3. 하드웨어 컨트롤러

### 3.1 베이스 클래스 (base.py)

```python
from abc import ABC, abstractmethod
from enum import Enum
import asyncio

class ControllerState(Enum):
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    DISABLED = "disabled"

class BaseHardwareController(ABC):
    def __init__(self, name: str, simulation_mode: bool = False):
        self.name = name
        self.simulation_mode = simulation_mode
        self._state = ControllerState.UNINITIALIZED
        self._lock = asyncio.Lock()
        self._last_update = None

    async def initialize(self) -> bool:
        """컨트롤러 초기화"""
        async with self._lock:
            self._state = ControllerState.INITIALIZING
            try:
                success = await self._do_initialize()
                self._state = ControllerState.READY if success else ControllerState.ERROR
                return success
            except Exception as e:
                self._state = ControllerState.ERROR
                raise

    async def cleanup(self) -> None:
        """컨트롤러 정리"""
        async with self._lock:
            await self._do_cleanup()
            self._state = ControllerState.DISABLED

    @abstractmethod
    async def _do_initialize(self) -> bool:
        """실제 초기화 로직 (하위 클래스 구현)"""
        pass

    @abstractmethod
    async def _do_cleanup(self) -> None:
        """실제 정리 로직 (하위 클래스 구현)"""
        pass

    def get_status(self) -> dict:
        """컨트롤러 상태 반환"""
        return {
            "name": self.name,
            "state": self._state.value,
            "simulation_mode": self.simulation_mode,
            "last_update": self._last_update.isoformat() if self._last_update else None
        }
```

### 3.2 시뮬레이션 믹스인 (base.py)

```python
import random

class SimulationMixin:
    """시뮬레이션 모드 지원 믹스인"""

    def _simulate_delay(self, min_ms: int = 1, max_ms: int = 10) -> float:
        """현실적인 지연 시뮬레이션"""
        return random.uniform(min_ms, max_ms) / 1000

    def _simulate_noise(self, value: float, percent: float = 2.0) -> float:
        """센서 노이즈 시뮬레이션"""
        noise = value * (percent / 100) * random.uniform(-1, 1)
        return value + noise

    def _simulate_drift(self, current: float, target: float, rate: float = 0.1) -> float:
        """센서 드리프트 시뮬레이션"""
        diff = target - current
        return current + diff * rate
```

### 3.3 GPIO 컨트롤러 예제 (gpio_controller.py)

```python
class GPIOController(BaseHardwareController, SimulationMixin):
    def __init__(self, simulation_mode: bool = False):
        super().__init__("GPIO Controller", simulation_mode)
        self._gpio = None
        self._pins = {}

    async def _do_initialize(self) -> bool:
        if not self.simulation_mode:
            import RPi.GPIO as GPIO
            self._gpio = GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
        return True

    async def write_pin(self, pin: int, state: PinState) -> bool:
        """GPIO 핀 출력 (비동기)"""
        if self.simulation_mode:
            await asyncio.sleep(self._simulate_delay())
        else:
            # 블로킹 I/O를 스레드풀에서 실행
            await asyncio.to_thread(self._gpio.output, pin, state.value)

        self._pins[pin].state = state
        return True

    async def read_pin(self, pin: int) -> PinState:
        """GPIO 핀 입력 (비동기)"""
        if self.simulation_mode:
            await asyncio.sleep(self._simulate_delay())
            return self._pins[pin].state
        else:
            value = await asyncio.to_thread(self._gpio.input, pin)
            return PinState.HIGH if value else PinState.LOW
```

---

## 4. 서비스 계층

### 4.1 WebSocket 매니저 (websocket_manager.py)

```python
from fastapi import WebSocket
from typing import Dict, Set
import asyncio
import json

class WebSocketManager:
    def __init__(self, max_clients: int = 10):
        self._clients: Dict[str, WebSocket] = {}
        self._subscriptions: Dict[str, Set[str]] = {}
        self._max_clients = max_clients
        self._heartbeat_interval = 30

    async def connect_client(self, client_id: str, websocket: WebSocket) -> bool:
        """클라이언트 연결"""
        if len(self._clients) >= self._max_clients:
            return False

        await websocket.accept()
        self._clients[client_id] = websocket
        self._subscriptions[client_id] = set()

        # 하트비트 태스크 시작
        asyncio.create_task(self._heartbeat_loop(client_id))
        return True

    async def broadcast_hardware_data(self, data: dict) -> None:
        """하드웨어 데이터 브로드캐스트"""
        message = {
            "type": "hardware_update",
            "topic": "hardware",
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        for client_id, topics in self._subscriptions.items():
            if "hardware" in topics or "all" in topics:
                await self._send_to_client(client_id, message)

    async def _send_to_client(self, client_id: str, message: dict) -> None:
        """개별 클라이언트에 메시지 전송"""
        if client_id in self._clients:
            try:
                await self._clients[client_id].send_json(message)
            except Exception:
                await self.disconnect_client(client_id)
```

### 4.2 시스템 모니터 (system_monitor.py)

```python
import psutil
from dataclasses import dataclass

@dataclass
class SystemMetrics:
    cpu_percent: float
    cpu_count: int
    cpu_freq_current: float
    cpu_freq_max: float
    cpu_temperature: float

    memory_total: float  # GB
    memory_available: float
    memory_used: float
    memory_percent: float

    disk_total: float  # GB
    disk_used: float
    disk_free: float
    disk_percent: float

    network_bytes_sent: int
    network_bytes_recv: int

    boot_time: float
    uptime: float

class SystemMonitor:
    def __init__(self, interval: float = 1.0):
        self._interval = interval
        self._running = False
        self._task = None
        self._on_update = None

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())

    async def _monitor_loop(self):
        while self._running:
            metrics = await self._collect_metrics()
            if self._on_update:
                await self._on_update(metrics)
            await asyncio.sleep(self._interval)

    async def _collect_metrics(self) -> SystemMetrics:
        # psutil은 블로킹이므로 스레드풀에서 실행
        return await asyncio.to_thread(self._collect_metrics_sync)

    def _collect_metrics_sync(self) -> SystemMetrics:
        cpu_freq = psutil.cpu_freq()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()

        return SystemMetrics(
            cpu_percent=psutil.cpu_percent(),
            cpu_count=psutil.cpu_count(),
            cpu_freq_current=cpu_freq.current if cpu_freq else 0,
            cpu_freq_max=cpu_freq.max if cpu_freq else 0,
            cpu_temperature=self._get_cpu_temperature(),
            memory_total=memory.total / (1024**3),
            memory_available=memory.available / (1024**3),
            memory_used=memory.used / (1024**3),
            memory_percent=memory.percent,
            disk_total=disk.total / (1024**3),
            disk_used=disk.used / (1024**3),
            disk_free=disk.free / (1024**3),
            disk_percent=disk.percent,
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv,
            boot_time=psutil.boot_time(),
            uptime=time.time() - psutil.boot_time()
        )

    def _get_cpu_temperature(self) -> float:
        try:
            temps = psutil.sensors_temperatures()
            if 'cpu_thermal' in temps:
                return temps['cpu_thermal'][0].current
        except Exception:
            pass
        return 0.0
```

---

## 5. API 라우트

### 5.1 하드웨어 API (hardware.py)

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/hardware", tags=["Hardware"])

# === Request Models ===

class LEDControlRequest(BaseModel):
    led_index: int = Field(..., ge=0, le=3, description="LED 인덱스 (0-3)")
    state: bool = Field(..., description="LED 상태 (True=ON, False=OFF)")

class MotorControlRequest(BaseModel):
    speed: int = Field(..., ge=0, le=100, description="모터 속도 (0-100%)")

class ServoControlRequest(BaseModel):
    angle: int = Field(..., ge=0, le=180, description="서보 각도 (0-180°)")

# === Endpoints ===

@router.get("/status")
async def get_hardware_status():
    """모든 하드웨어 컨트롤러 상태 조회"""
    return hardware_manager.get_all_status()

@router.get("/data")
async def get_hardware_data():
    """현재 하드웨어 데이터 스냅샷"""
    return hardware_manager.get_current_data()

@router.post("/gpio/led")
async def control_led(request: LEDControlRequest):
    """LED 제어"""
    success = await hardware_manager.gpio.set_led(
        request.led_index,
        request.state
    )
    if not success:
        raise HTTPException(status_code=400, detail="LED 제어 실패")
    return {"success": True, "led": request.led_index, "state": request.state}

@router.post("/pwm/motor")
async def control_motor(request: MotorControlRequest):
    """모터 속도 제어"""
    await hardware_manager.pwm.set_motor_speed(request.speed)
    return {"success": True, "speed": request.speed}

@router.post("/pwm/servo")
async def control_servo(request: ServoControlRequest):
    """서보 각도 제어"""
    await hardware_manager.pwm.set_servo_angle(request.angle)
    return {"success": True, "angle": request.angle}

@router.get("/sensors")
async def get_sensor_readings():
    """모든 센서 읽기"""
    return await hardware_manager.sensors.read_all()
```

### 5.2 WebSocket 엔드포인트 (websocket.py)

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import uuid

router = APIRouter(prefix="/ws", tags=["WebSocket"])

@router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    """실시간 데이터 WebSocket"""
    client_id = str(uuid.uuid4())

    if not await ws_manager.connect_client(client_id, websocket):
        await websocket.close(code=1008, reason="Maximum clients reached")
        return

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "subscribe":
                topics = data.get("topics", ["all"])
                await ws_manager.subscribe(client_id, topics)

            elif data.get("type") == "pong":
                # 하트비트 응답 처리
                pass

    except WebSocketDisconnect:
        await ws_manager.disconnect_client(client_id)
```

---

## 6. 데이터베이스 모델

### 6.1 센서 데이터 (sensor_data.py)

```python
from sqlalchemy import Column, Integer, Float, String, DateTime, JSON, Index
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    sensor_type = Column(String(50), index=True)

    # 센서 값
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    pressure = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    distance = Column(Float, nullable=True)
    light_level = Column(Integer, nullable=True)
    soil_moisture = Column(Integer, nullable=True)
    motion = Column(Integer, nullable=True)  # 0 or 1

    # ADC 값 (JSON)
    adc_values = Column(JSON, nullable=True)

    # 추가 데이터
    extra_data = Column(JSON, nullable=True)

    # 복합 인덱스
    __table_args__ = (
        Index('idx_sensor_type_timestamp', 'sensor_type', 'timestamp'),
    )
```

---

## 7. 개발 가이드라인

### 7.1 새 하드웨어 컨트롤러 추가

1. `BaseHardwareController` 상속
2. `SimulationMixin` 적용
3. `_do_initialize()`, `_do_cleanup()` 구현
4. 블로킹 I/O는 `asyncio.to_thread()` 사용
5. `HardwareManager`에 등록

### 7.2 새 API 엔드포인트 추가

1. Pydantic 요청/응답 모델 정의
2. 라우터 함수 작성
3. 에러 처리 추가
4. `api/__init__.py`에서 라우터 등록

### 7.3 테스트

```bash
# 시뮬레이션 모드로 실행
SIMULATION_MODE=true uvicorn app.main:app --reload

# API 테스트
curl http://localhost:8000/api/hardware/status

# WebSocket 테스트
wscat -c ws://localhost:8000/api/ws/live
```
