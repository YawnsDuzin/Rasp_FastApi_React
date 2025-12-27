# Frontend-Backend 연동 가이드

## 1. 시스템 아키텍처 개요

본 시스템은 Frontend(React)와 Backend(FastAPI)가 명확하게 분리된 모던 웹 아키텍처를 채용합니다.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Client                                      │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                     React Frontend (Port 3000 개발 / 8000 프로덕션)  │ │
│  │                                                                     │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐│ │
│  │  │   Pages     │  │ Components  │  │      Hooks (useStore,       ││ │
│  │  │  Dashboard  │  │  Layout     │  │      useWebSocket)          ││ │
│  │  │  Hardware   │  │  GaugeChart │  └─────────────────────────────┘│ │
│  │  │  Sensors    │  │  Toggle     │                                  │ │
│  │  └─────────────┘  └─────────────┘                                  │ │
│  │           │              │                      │                   │ │
│  │           └──────────────┴──────────────────────┘                   │ │
│  │                          │                                          │ │
│  │  ┌───────────────────────┴───────────────────────┐                 │ │
│  │  │              Services Layer                    │                 │ │
│  │  │  ┌─────────────────┐  ┌─────────────────────┐ │                 │ │
│  │  │  │    api.ts       │  │   websocket.ts      │ │                 │ │
│  │  │  │  (REST Client)  │  │  (WebSocket Client) │ │                 │ │
│  │  │  └─────────────────┘  └─────────────────────┘ │                 │ │
│  │  └───────────────────────────────────────────────┘                 │ │
│  └───────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                    │ HTTP/REST                │ WebSocket
                    │ (요청-응답)               │ (실시간 양방향)
                    ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              Server                                      │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                    FastAPI Backend (Port 8000)                     │ │
│  │                                                                     │ │
│  │  ┌─────────────────────────────────────────────────────────────┐   │ │
│  │  │                      API Layer                               │   │ │
│  │  │  /api/hardware    /api/system    /api/data    /api/ws/live  │   │ │
│  │  └─────────────────────────────────────────────────────────────┘   │ │
│  │                          │                                          │ │
│  │  ┌───────────────────────┴───────────────────────┐                 │ │
│  │  │              Services Layer                    │                 │ │
│  │  │   WebSocketManager   SystemMonitor  DataLogger │                 │ │
│  │  └───────────────────────────────────────────────┘                 │ │
│  │                          │                                          │ │
│  │  ┌───────────────────────┴───────────────────────┐                 │ │
│  │  │              Hardware Manager                  │                 │ │
│  │  │   GPIO  PWM  I2C  SPI  Sensors  Display       │                 │ │
│  │  └───────────────────────────────────────────────┘                 │ │
│  └───────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Physical Hardware                                 │
│              GPIO Pins, I2C Bus, SPI Bus, Sensors, Displays             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 통신 방식

Frontend와 Backend는 두 가지 통신 채널을 사용합니다:

### 2.1 REST API (HTTP)

**용도:** 사용자 액션에 의한 명령 전송 및 데이터 조회

```
┌──────────────────┐         HTTP Request          ┌──────────────────┐
│     Frontend     │  ─────────────────────────▶  │     Backend      │
│   (User Action)  │                               │    (FastAPI)     │
│                  │  ◀─────────────────────────  │                  │
└──────────────────┘         HTTP Response         └──────────────────┘
```

**특징:**
- 요청-응답 패턴 (동기적)
- 사용자가 버튼을 클릭하거나 값을 변경할 때 사용
- LED 켜기, 모터 속도 변경, 설정 조회 등

**예시 흐름:**
```
1. 사용자가 LED 토글 버튼 클릭
2. Frontend: POST /api/hardware/gpio/led { led_index: 0, state: true }
3. Backend: GPIO 핀 출력 변경
4. Backend: { success: true, led: 0, state: true } 응답
5. Frontend: UI 상태 업데이트
```

### 2.2 WebSocket

**용도:** 실시간 데이터 푸시 (서버 → 클라이언트)

```
┌──────────────────┐                               ┌──────────────────┐
│     Frontend     │  ════════════════════════▶  │     Backend      │
│                  │         Subscribe            │                  │
│                  │  ◀════════════════════════  │                  │
│                  │      Continuous Updates      │                  │
└──────────────────┘                               └──────────────────┘
```

**특징:**
- 양방향 지속 연결
- 서버가 데이터 변경 시 클라이언트에 푸시
- 센서 값, 시스템 메트릭 등 실시간 데이터

**메시지 타입:**

| 타입 | 방향 | 설명 |
|------|------|------|
| `subscribe` | Client → Server | 토픽 구독 요청 |
| `hardware_update` | Server → Client | 하드웨어 데이터 업데이트 |
| `system_update` | Server → Client | 시스템 메트릭 업데이트 |
| `ping` | Server → Client | 연결 상태 확인 |
| `pong` | Client → Server | ping 응답 |

---

## 3. 데이터 흐름 상세

### 3.1 사용자 명령 흐름 (Frontend → Backend → Hardware)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. User Action                                                          │
│    사용자가 LED 버튼 클릭                                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. React Component Event Handler                                         │
│                                                                          │
│    const handleLedToggle = async (index: number) => {                   │
│      setLoading(true);                                                  │
│      await hardwareApi.setLed(index, !leds[index]);                     │
│      setLoading(false);                                                 │
│    };                                                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. API Service (api.ts)                                                  │
│                                                                          │
│    setLed: (index: number, state: boolean) =>                           │
│      fetchApi('/hardware/gpio/led', {                                   │
│        method: 'POST',                                                  │
│        body: JSON.stringify({ led_index: index, state })                │
│      })                                                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP POST /api/hardware/gpio/led
                                    │ Content-Type: application/json
                                    │ { "led_index": 0, "state": true }
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. FastAPI Route Handler (hardware.py)                                   │
│                                                                          │
│    @router.post("/gpio/led")                                            │
│    async def control_led(request: LEDControlRequest):                   │
│        success = await hardware_manager.gpio.set_led(                   │
│            request.led_index,                                           │
│            request.state                                                │
│        )                                                                │
│        return {"success": True, "led": request.led_index, ...}          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 5. Hardware Controller (gpio_controller.py)                              │
│                                                                          │
│    async def set_led(self, index: int, state: bool):                    │
│        if self.simulation_mode:                                         │
│            await asyncio.sleep(self._simulate_delay())                  │
│        else:                                                            │
│            await asyncio.to_thread(                                     │
│                self._gpio.output, LED_PINS[index], state                │
│            )                                                            │
│        self._led_states[index] = state                                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 6. Physical GPIO                                                         │
│    GPIO 핀 17 (LED 0) → HIGH (3.3V) → LED ON                            │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 실시간 데이터 흐름 (Hardware → Backend → Frontend)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. Hardware Sensor Reading                                               │
│    DHT22 센서에서 온도 25.5°C, 습도 60% 읽음                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. Hardware Manager Background Loop                                       │
│                                                                          │
│    async def _update_loop(self):                                        │
│        while self._running:                                             │
│            data = await self._collect_all_data()                        │
│            if self._on_data_update:                                     │
│                await self._on_data_update(data)  # 콜백 호출           │
│            await asyncio.sleep(self._update_interval)  # 0.5초         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. WebSocket Manager Broadcast                                           │
│                                                                          │
│    async def broadcast_hardware_data(self, data: dict):                 │
│        message = {                                                      │
│            "type": "hardware_update",                                   │
│            "topic": "hardware",                                         │
│            "timestamp": datetime.now().isoformat(),                     │
│            "data": data                                                 │
│        }                                                                │
│        for client in subscribed_clients:                                │
│            await client.send_json(message)                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ WebSocket Message
                                    │ { "type": "hardware_update",
                                    │   "data": { "sensors": { "temperature": 25.5, ... } } }
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. WebSocket Service (websocket.ts)                                      │
│                                                                          │
│    this.ws.onmessage = (event) => {                                     │
│      const message = JSON.parse(event.data);                            │
│      this.emit(message.type, message);  // 이벤트 발생                  │
│    };                                                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 5. useWebSocket Hook                                                     │
│                                                                          │
│    const handleHardwareUpdate = (message: any) => {                     │
│      setHardwareData(message.data);  // Zustand 스토어 업데이트        │
│    };                                                                   │
│    wsService.on('hardware_update', handleHardwareUpdate);               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 6. Zustand Store (useStore.ts)                                           │
│                                                                          │
│    setHardwareData: (data) => {                                         │
│      set({ hardwareData: data });                                       │
│      // 히스토리에도 추가                                               │
│      if (data.sensors?.temperature) {                                   │
│        get().addTemperature(data.sensors.temperature);                  │
│      }                                                                  │
│    }                                                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 7. React Component Re-render                                             │
│                                                                          │
│    function SensorCard() {                                              │
│      const { hardwareData } = useStore();                               │
│      return <div>{hardwareData?.sensors?.temperature}°C</div>;          │
│    }                                                                    │
│    // 25.5°C 표시                                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Frontend 서비스 레이어

### 4.1 API 서비스 (api.ts)

REST API 호출을 담당하는 서비스 레이어입니다.

```typescript
// 기본 fetch 래퍼
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api${endpoint}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options
  });

  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }

  return response.json();
}

// 하드웨어 API 객체
export const hardwareApi = {
  // 상태 조회
  getStatus: () => fetchApi('/hardware/status'),
  getData: () => fetchApi('/hardware/data'),

  // GPIO 제어
  setLed: (index: number, state: boolean) =>
    fetchApi('/hardware/gpio/led', {
      method: 'POST',
      body: JSON.stringify({ led_index: index, state })
    }),

  // PWM 제어
  setMotorSpeed: (speed: number) =>
    fetchApi('/hardware/pwm/motor', {
      method: 'POST',
      body: JSON.stringify({ speed })
    }),

  // ... 기타 API
};
```

### 4.2 WebSocket 서비스 (websocket.ts)

실시간 통신을 담당하는 WebSocket 클라이언트입니다.

```typescript
class WebSocketService {
  private ws: WebSocket | null = null;
  private handlers: Map<string, MessageHandler[]> = new Map();

  connect(): void {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.ws = new WebSocket(`${protocol}//${window.location.host}/api/ws/live`);

    this.ws.onopen = () => {
      this.emit('connect', null);
      this.subscribe(['all']);  // 모든 토픽 구독
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.emit(message.type, message);
    };

    this.ws.onclose = () => {
      this.emit('disconnect', null);
      this.attemptReconnect();  // 자동 재연결
    };
  }

  // 이벤트 핸들러 등록
  on(event: string, handler: MessageHandler): void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, []);
    }
    this.handlers.get(event)!.push(handler);
  }

  // 이벤트 발생
  private emit(event: string, data: any): void {
    this.handlers.get(event)?.forEach(handler => handler(data));
  }
}
```

---

## 5. 상태 관리와 데이터 동기화

### 5.1 Zustand 스토어 구조

```typescript
interface StoreState {
  // 연결 상태
  isConnected: boolean;

  // 하드웨어 데이터 (WebSocket으로 수신)
  hardwareData: HardwareData | null;

  // 시스템 메트릭 (WebSocket으로 수신)
  systemMetrics: SystemMetrics | null;

  // 히스토리 (차트용)
  temperatureHistory: Array<{ time: string; value: number }>;
  humidityHistory: Array<{ time: string; value: number }>;

  // UI 상태
  darkMode: boolean;
  activePage: string;

  // 알림
  alerts: Alert[];
}
```

### 5.2 데이터 동기화 패턴

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         데이터 동기화 전략                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────┐     WebSocket     ┌────────────────────────────┐   │
│  │    Backend     │  ══════════════▶  │      Zustand Store         │   │
│  │  (Real-time)   │   (자동 푸시)     │   (Single Source of Truth) │   │
│  └────────────────┘                   └────────────────────────────┘   │
│                                                    │                     │
│                                                    │ subscribe           │
│                                                    ▼                     │
│                                        ┌─────────────────────────┐      │
│                                        │    React Components     │      │
│                                        │  (자동 리렌더링)         │      │
│                                        └─────────────────────────┘      │
│                                                    │                     │
│                                                    │ user action         │
│                                                    ▼                     │
│  ┌────────────────┐     REST API      ┌────────────────────────────┐   │
│  │    Backend     │  ◀══════════════  │      API Service           │   │
│  │   (Control)    │    (명령 전송)     │   (hardwareApi.setLed())   │   │
│  └────────────────┘                   └────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

**핵심 원칙:**
1. **Single Source of Truth**: 모든 상태는 Zustand 스토어에 저장
2. **Unidirectional Data Flow**: 데이터는 Backend → Store → Components 단방향 흐름
3. **Optimistic UI**: 사용자 액션 즉시 UI 반영, 서버 응답 후 확정

---

## 6. 타입 시스템 통일

Frontend와 Backend에서 동일한 데이터 구조를 사용합니다.

### 6.1 Backend (Pydantic Models)

```python
# backend/app/models/sensor_data.py
from pydantic import BaseModel

class SensorData(BaseModel):
    temperature: float | None = None
    humidity: float | None = None
    pressure: float | None = None
    altitude: float | None = None
    distance: float | None = None
    motion: bool = False
    light_level: int | None = None
    soil_moisture: int | None = None
```

### 6.2 Frontend (TypeScript Interfaces)

```typescript
// frontend/src/types/index.ts
export interface SensorData {
  temperature: number | null;
  humidity: number | null;
  pressure: number | null;
  altitude: number | null;
  distance: number | null;
  motion: boolean;
  light_level: number | null;
  soil_moisture: number | null;
}
```

### 6.3 대응 관계

| Python Type | TypeScript Type | JSON |
|-------------|-----------------|------|
| `int` | `number` | number |
| `float` | `number` | number |
| `str` | `string` | string |
| `bool` | `boolean` | true/false |
| `None` | `null` | null |
| `list[T]` | `T[]` | array |
| `dict[K, V]` | `Record<K, V>` | object |
| `Optional[T]` | `T \| null` | value or null |

---

## 7. 개발 환경 프록시 설정

개발 시 Vite 개발 서버가 API 요청을 Backend로 프록시합니다.

### 7.1 Vite 프록시 설정 (vite.config.ts)

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // REST API 프록시
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      // WebSocket 프록시
      '/api/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
})
```

### 7.2 개발 vs 프로덕션

```
개발 환경:
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│   Browser      │────▶│  Vite (3000)   │────▶│  FastAPI       │
│                │     │  (Dev Server)  │     │  (8000)        │
│                │     │  + Proxy       │     │                │
└────────────────┘     └────────────────┘     └────────────────┘

프로덕션 환경:
┌────────────────┐     ┌────────────────────────────────────────┐
│   Browser      │────▶│             FastAPI (8000)             │
│                │     │  ┌────────────────────────────────────┐│
│                │     │  │  Static Files (React Build)        ││
│                │     │  │  /static/*                          ││
│                │     │  └────────────────────────────────────┘│
│                │     │  ┌────────────────────────────────────┐│
│                │     │  │  API Routes                         ││
│                │     │  │  /api/*                             ││
│                │     │  └────────────────────────────────────┘│
└────────────────┘     └────────────────────────────────────────┘
```

---

## 8. 에러 처리 패턴

### 8.1 Frontend 에러 처리

```typescript
// API 호출 시 에러 처리
const handleLedToggle = async (index: number) => {
  setLoading(true);
  setError(null);

  try {
    await hardwareApi.setLed(index, !leds[index]);
    // 성공 시 WebSocket으로 업데이트 수신
  } catch (e) {
    if (e instanceof ApiError) {
      if (e.status === 503) {
        setError('하드웨어에 연결할 수 없습니다');
      } else {
        setError(e.message);
      }
    } else {
      setError('알 수 없는 오류가 발생했습니다');
    }
  } finally {
    setLoading(false);
  }
};
```

### 8.2 Backend 에러 처리

```python
from fastapi import HTTPException

@router.post("/gpio/led")
async def control_led(request: LEDControlRequest):
    if not hardware_manager.gpio.is_ready:
        raise HTTPException(
            status_code=503,
            detail="GPIO Controller is not available"
        )

    try:
        success = await hardware_manager.gpio.set_led(
            request.led_index,
            request.state
        )
        if not success:
            raise HTTPException(status_code=400, detail="LED 제어 실패")
        return {"success": True, "led": request.led_index, "state": request.state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 8.3 에러 코드 체계

| 상태 코드 | 의미 | Frontend 처리 |
|----------|------|--------------|
| 200 | 성공 | 정상 처리 |
| 400 | 잘못된 요청 | 사용자 입력 오류 메시지 |
| 404 | 리소스 없음 | 페이지/데이터 없음 메시지 |
| 422 | 유효성 검사 실패 | 필드별 오류 메시지 |
| 500 | 서버 오류 | 일반 오류 메시지 |
| 503 | 서비스 불가 | 하드웨어 연결 오류 메시지 |

---

## 9. WebSocket 재연결 전략

```typescript
class WebSocketService {
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;  // 시작 지연 1초

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached');
      return;
    }

    this.reconnectAttempts++;

    // 지수 백오프: 1초, 2초, 4초, 8초, 16초
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    setTimeout(() => {
      console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
      this.connect();
    }, delay);
  }
}
```

```
연결 끊김
    │
    ▼
1초 후 재시도 (1회차)
    │
    ├─ 성공 → 정상 운영
    │
    └─ 실패 → 2초 후 재시도 (2회차)
                │
                ├─ 성공 → 정상 운영
                │
                └─ 실패 → 4초 후 재시도 (3회차)
                            │
                            └─ ... 최대 5회까지
```

---

## 10. 디버깅 가이드

### 10.1 Frontend 디버깅

```typescript
// WebSocket 메시지 로깅
wsService.on('hardware_update', (msg) => {
  console.log('[WS] Hardware Update:', msg);
});

// API 호출 로깅
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  console.log(`[API] ${options?.method || 'GET'} ${endpoint}`);
  const response = await fetch(...);
  console.log(`[API] Response:`, response.status);
  return response.json();
}
```

### 10.2 Backend 디버깅

```python
import logging

logger = logging.getLogger(__name__)

@router.post("/gpio/led")
async def control_led(request: LEDControlRequest):
    logger.info(f"LED control request: index={request.led_index}, state={request.state}")
    # ...
    logger.info(f"LED control success: {result}")
    return result
```

### 10.3 네트워크 디버깅

```bash
# API 요청 테스트
curl http://localhost:8000/api/hardware/status

# WebSocket 테스트
wscat -c ws://localhost:8000/api/ws/live
> {"type": "subscribe", "topics": ["all"]}
```

### 10.4 브라우저 개발자 도구

1. **Network 탭**: HTTP 요청/응답 확인
2. **Console 탭**: WebSocket 메시지 로그
3. **Application 탭**: LocalStorage (다크모드 등 저장된 설정)
4. **React DevTools**: 컴포넌트 상태 확인

---

## 11. 성능 최적화

### 11.1 WebSocket 메시지 최적화

```python
# Backend: 변경된 데이터만 전송
async def broadcast_hardware_data(self, new_data: dict):
    if self._last_data == new_data:
        return  # 변경 없으면 전송 안함

    # 변경된 필드만 전송 (선택적)
    diff = self._calculate_diff(self._last_data, new_data)
    await self._broadcast(diff)
    self._last_data = new_data
```

### 11.2 Frontend 리렌더링 최적화

```typescript
// 필요한 데이터만 구독 (선택적 구독)
const temperature = useStore((state) => state.hardwareData?.sensors?.temperature);

// 전체 객체 구독 대신 특정 값만 구독하면 해당 값 변경 시에만 리렌더링
```

### 11.3 API 요청 최적화

```typescript
// Debounce: 슬라이더 값 변경 시 너무 많은 요청 방지
const debouncedSetMotorSpeed = useMemo(
  () => debounce((speed: number) => hardwareApi.setMotorSpeed(speed), 100),
  []
);

const handleSpeedChange = (speed: number) => {
  setLocalSpeed(speed);  // 즉시 UI 업데이트
  debouncedSetMotorSpeed(speed);  // 100ms 디바운스 후 서버 전송
};
```

---

## 12. 확장 가이드

### 12.1 새 API 엔드포인트 추가

1. **Backend**: `backend/app/api/` 에 라우터 추가
2. **Frontend**: `frontend/src/services/api.ts` 에 API 함수 추가
3. **Types**: 양쪽에 타입 정의 추가

### 12.2 새 WebSocket 토픽 추가

1. **Backend**: `websocket_manager.py` 에 토픽 처리 추가
2. **Frontend**: `useWebSocket.ts` 에 핸들러 추가
3. **Store**: `useStore.ts` 에 상태 및 액션 추가

### 12.3 인증 추가 (향후 확장)

```typescript
// Frontend: 인증 토큰 헤더 추가
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem('auth_token');
  const response = await fetch(`/api${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,  // 인증 헤더
      ...options?.headers
    },
    ...options
  });
  // ...
}

// Backend: 의존성 주입으로 인증 검사
from fastapi import Depends

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # 토큰 검증
    return user

@router.post("/gpio/led")
async def control_led(
    request: LEDControlRequest,
    user: User = Depends(get_current_user)  # 인증 필수
):
    # ...
```
