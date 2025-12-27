# 시스템 아키텍처

## 1. 3계층 아키텍처

본 시스템은 3계층 아키텍처로 설계되어 관심사의 분리와 유지보수성을 보장합니다.

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│                    (React Frontend)                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │  Dashboard  │ │  Hardware   │ │   Sensors/System/Logs   ││
│  │    Page     │ │   Control   │ │        Pages            ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
│           │              │                    │              │
│           └──────────────┼────────────────────┘              │
│                          │                                   │
│           ┌──────────────┴──────────────┐                   │
│           │    WebSocket + REST API      │                   │
│           └──────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Communication Layer                        │
│                    (FastAPI Backend)                         │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    API Routes                            ││
│  │  /api/hardware  /api/system  /api/data  /api/ws         ││
│  └─────────────────────────────────────────────────────────┘│
│           │              │              │                    │
│  ┌────────┴──────────────┴──────────────┴────────┐          │
│  │                 Services Layer                 │          │
│  │  WebSocketManager  SystemMonitor  DataLogger  │          │
│  └───────────────────────────────────────────────┘          │
│                          │                                   │
│           ┌──────────────┴──────────────┐                   │
│           │    Hardware Manager         │                   │
│           └──────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Hardware Layer                            │
│              (Hardware Controllers)                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │  GPIO   │ │   PWM   │ │   I2C   │ │   SPI   │           │
│  │Controller│ │Controller│ │Controller│ │Controller│          │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
│  ┌─────────┐ ┌─────────┐ ┌───────────────────────┐          │
│  │ Sensor  │ │ Display │ │      NeoPixel         │          │
│  │Controller│ │Controller│ │      Controller       │          │
│  └─────────┘ └─────────┘ └───────────────────────┘          │
│                          │                                   │
│           ┌──────────────┴──────────────┐                   │
│           │   Physical Hardware / GPIO   │                   │
│           └──────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 데이터 흐름

### 2.1 실시간 데이터 흐름 (Hardware → Frontend)

```
Hardware Sensor
      │
      ▼
Hardware Controller (asyncio.to_thread)
      │
      ▼
Hardware Manager (Background Loop)
      │
      ▼
Event Callback
      │
      ▼
WebSocket Manager
      │
      ▼
Broadcast to Clients
      │
      ▼
React State (Zustand)
      │
      ▼
UI Component Re-render
```

### 2.2 제어 명령 흐름 (Frontend → Hardware)

```
UI Button Click
      │
      ▼
API Service (fetch)
      │
      ▼
FastAPI Route Handler
      │
      ▼
Hardware Manager
      │
      ▼
Hardware Controller
      │
      ▼
asyncio.to_thread()
      │
      ▼
Physical GPIO/I2C/SPI
```

---

## 3. 기술 스택

### 3.1 백엔드

| 기술 | 버전 | 용도 |
|------|------|------|
| **Python** | 3.9+ | 메인 언어 |
| **FastAPI** | 0.104+ | 웹 프레임워크 |
| **Uvicorn** | 0.24+ | ASGI 서버 |
| **Pydantic** | 2.0+ | 데이터 검증 및 설정 |
| **SQLAlchemy** | 2.0+ | ORM (비동기 모드) |
| **SQLite** | 3.x | 임베디드 데이터베이스 (WAL 모드) |
| **psutil** | - | 시스템 모니터링 |

**하드웨어 라이브러리 (라즈베리파이 전용):**
- RPi.GPIO, gpiozero, spidev, smbus2
- adafruit-circuitpython-dht, adafruit-circuitpython-bmp280
- adafruit-circuitpython-ads1x15, adafruit-circuitpython-ssd1306
- adafruit-circuitpython-neopixel, RPLCD

### 3.2 프론트엔드

| 기술 | 버전 | 용도 |
|------|------|------|
| **React** | 18.2.0 | UI 라이브러리 |
| **TypeScript** | 5.3.3 | 타입 안전성 |
| **Vite** | 5.0.10 | 빌드 도구 |
| **Zustand** | 4.4.7 | 전역 상태 관리 |
| **Tailwind CSS** | 3.4.0 | 유틸리티 CSS |
| **Lucide React** | 0.303.0 | 아이콘 라이브러리 |
| **Recharts** | 2.10.3 | 차트/그래프 |

### 3.3 통신 프로토콜

**REST API:**
- JSON 기반 데이터 교환
- OpenAPI (Swagger) 자동 문서화
- `/api/hardware/*`, `/api/system/*`, `/api/data/*`

**WebSocket:**
- 실시간 양방향 통신
- `ws://[host]:8000/api/ws/live`
- 토픽 기반 구독 (hardware, system, logs)

---

## 4. 핵심 설계 원칙

### 4.1 비동기 우선 (Async-First)

모든 I/O 작업은 비동기로 처리하여 웹 서비스의 응답성을 보장합니다.

```python
# 블로킹 하드웨어 I/O를 스레드풀에서 실행
async def read_sensor(self):
    if self.simulation_mode:
        await asyncio.sleep(self._simulate_delay())
        return simulated_value
    else:
        return await asyncio.to_thread(self._read_sensor_sync)
```

### 4.2 하드웨어 추상화

모든 하드웨어 컨트롤러는 공통 베이스 클래스를 상속하여 일관된 인터페이스를 제공합니다.

```python
class BaseHardwareController(ABC):
    @abstractmethod
    async def _do_initialize(self) -> bool: ...

    @abstractmethod
    async def _do_cleanup(self) -> None: ...

    def get_status(self) -> ControllerStatus: ...
```

### 4.3 시뮬레이션 모드

실제 하드웨어 없이도 개발과 테스트가 가능합니다.

```python
class SimulationMixin:
    def _simulate_delay(self) -> float:
        """1-10ms 랜덤 지연"""

    def _simulate_noise(self, value: float, percent: float = 2.0) -> float:
        """현실적인 노이즈 추가"""

    def _simulate_drift(self, current: float, target: float, rate: float) -> float:
        """센서 드리프트 시뮬레이션"""
```

### 4.4 이벤트 기반 통신

하드웨어 상태 변경 시 콜백을 통해 즉시 WebSocket 클라이언트에 전파합니다.

```python
async def _update_loop(self):
    while self._running:
        data = await self._collect_all_data()
        if self._on_data_update:
            await self._on_data_update(data)
        await asyncio.sleep(self._update_interval)
```

---

## 5. 컴포넌트 상호작용

### 5.1 애플리케이션 시작 시퀀스

```
1. FastAPI App 생성
        │
        ▼
2. Lifespan Context 시작
        │
        ├─→ Database 초기화 (SQLite + WAL)
        │
        ├─→ Hardware Manager 초기화
        │         │
        │         ├─→ GPIO Controller
        │         ├─→ PWM Controller
        │         ├─→ I2C Controller
        │         ├─→ SPI Controller
        │         ├─→ Sensor Controller
        │         ├─→ Display Controller
        │         └─→ NeoPixel Controller
        │
        ├─→ System Monitor 시작
        │
        ├─→ WebSocket Manager 초기화
        │
        ├─→ Data Logger 시작
        │
        └─→ Background Update Loop 시작
                  │
                  ▼
3. API 서버 시작 (0.0.0.0:8000)
```

### 5.2 WebSocket 연결 시퀀스

```
Client                          Server
  │                                │
  │──── WS Connect ────────────────►│
  │                                │
  │◄─── Connection Accepted ────────│
  │                                │
  │──── Subscribe {"topics": [...]} ►│
  │                                │
  │◄─── hardware_update ────────────│
  │◄─── system_update ──────────────│
  │                                │
  │◄─── ping (30초 간격) ────────────│
  │──── pong ──────────────────────►│
  │                                │
```

---

## 6. 데이터베이스 스키마

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   sensor_data   │    │   system_log    │    │  device_state   │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id              │    │ id              │    │ id              │
│ timestamp       │    │ timestamp       │    │ timestamp       │
│ sensor_type     │    │ level           │    │ device_type     │
│ temperature     │    │ message         │    │ device_id       │
│ humidity        │    │ source          │    │ state           │
│ pressure        │    │ extra_data      │    │ extra_data      │
│ altitude        │    └─────────────────┘    └─────────────────┘
│ distance        │
│ light_level     │
│ soil_moisture   │
│ motion          │
│ adc_values      │
│ extra_data      │
└─────────────────┘
```

---

## 7. 보안 고려사항

### 7.1 네트워크 보안

- CORS 설정으로 허용된 출처만 API 접근
- WebSocket 연결 수 제한 (기본 10개)
- Rate limiting 적용 가능

### 7.2 데이터 보안

- SQLite WAL 모드로 데이터 무결성 보장
- 환경 변수를 통한 민감 설정 관리
- Systemd 서비스의 파일시스템 보호

### 7.3 하드웨어 보안

- GPIO 접근 권한 관리
- 입력 값 검증 (PWM 범위, GPIO 핀 번호 등)
- 타임아웃을 통한 무한 루프 방지

---

## 8. 성능 특성

### 8.1 응답 시간

| 작업 | 예상 시간 |
|------|----------|
| REST API 응답 | < 50ms |
| WebSocket 메시지 | < 10ms |
| 하드웨어 읽기 (실제) | 1-100ms |
| 하드웨어 읽기 (시뮬레이션) | 1-10ms |

### 8.2 리소스 사용량

| 리소스 | 일반 사용량 |
|--------|------------|
| CPU (유휴) | < 5% |
| CPU (활성) | 10-30% |
| 메모리 | 100-200MB |
| 디스크 (데이터베이스) | 10-100MB |

### 8.3 버전 호환성

| 컴포넌트 | 최소 버전 | 권장 버전 |
|----------|----------|----------|
| Python | 3.9 | 3.11+ |
| Node.js | 16 | 18+ |
| npm | 8 | 9+ |
| Raspberry Pi OS | Bullseye | Bookworm |
| SQLite | 3.31 | 3.40+ |

---

## 9. 확장성

### 9.1 새 하드웨어 추가

1. `BaseHardwareController` 상속
2. `_do_initialize()` 및 `_do_cleanup()` 구현
3. `SimulationMixin` 통합
4. Hardware Manager에 등록
5. API 라우트 추가

### 9.2 새 API 엔드포인트 추가

1. `app/api/` 디렉토리에 라우터 생성
2. Pydantic 모델 정의
3. `__init__.py`에서 라우터 등록

### 9.3 새 프론트엔드 페이지 추가

1. `pages/` 디렉토리에 컴포넌트 생성
2. `App.tsx`에서 라우팅 추가
3. `Layout.tsx` 네비게이션에 추가
