# 시스템 아키텍처 개요

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

## 3. 핵심 설계 원칙

### 3.1 비동기 우선 (Async-First)

모든 I/O 작업은 비동기로 처리하여 웹 서비스의 응답성을 보장합니다.

```python
# 블로킹 하드웨어 I/O를 스레드풀에서 실행
async def read_sensor(self):
    if self.simulation_mode:
        await asyncio.sleep(self._simulate_delay())
        return simulated_value
    else:
        # 블로킹 호출을 별도 스레드에서 실행
        return await asyncio.to_thread(self._read_sensor_sync)
```

### 3.2 하드웨어 추상화

모든 하드웨어 컨트롤러는 공통 베이스 클래스를 상속하여 일관된 인터페이스를 제공합니다.

```python
class BaseHardwareController(ABC):
    @abstractmethod
    async def _do_initialize(self) -> bool: ...

    @abstractmethod
    async def _do_cleanup(self) -> None: ...

    def get_status(self) -> ControllerStatus: ...
```

### 3.3 시뮬레이션 모드

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

### 3.4 이벤트 기반 통신

하드웨어 상태 변경 시 콜백을 통해 즉시 WebSocket 클라이언트에 전파합니다.

```python
# Hardware Manager
self._on_data_update = None  # 콜백 함수

async def _update_loop(self):
    while self._running:
        data = await self._collect_all_data()
        if self._on_data_update:
            await self._on_data_update(data)
        await asyncio.sleep(self._update_interval)
```

---

## 4. 컴포넌트 상호작용

### 4.1 애플리케이션 시작 시퀀스

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

### 4.2 WebSocket 연결 시퀀스

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

## 5. 보안 고려사항

### 5.1 네트워크 보안

- CORS 설정으로 허용된 출처만 API 접근
- WebSocket 연결 수 제한 (기본 10개)
- Rate limiting 적용 가능

### 5.2 데이터 보안

- SQLite WAL 모드로 데이터 무결성 보장
- 환경 변수를 통한 민감 설정 관리
- Systemd 서비스의 파일시스템 보호

### 5.3 하드웨어 보안

- GPIO 접근 권한 관리
- 입력 값 검증 (PWM 범위, GPIO 핀 번호 등)
- 타임아웃을 통한 무한 루프 방지

---

## 6. 확장성

### 6.1 새 하드웨어 추가

1. `BaseHardwareController` 상속
2. `_do_initialize()` 및 `_do_cleanup()` 구현
3. `SimulationMixin` 통합
4. Hardware Manager에 등록
5. API 라우트 추가

### 6.2 새 API 엔드포인트 추가

1. `app/api/` 디렉토리에 라우터 생성
2. Pydantic 모델 정의
3. `__init__.py`에서 라우터 등록

### 6.3 새 프론트엔드 페이지 추가

1. `pages/` 디렉토리에 컴포넌트 생성
2. `App.tsx`에서 라우팅 추가
3. `Layout.tsx` 네비게이션에 추가
