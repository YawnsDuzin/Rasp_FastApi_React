# API 레퍼런스

## 1. 개요

### 1.1 기본 정보

| 항목 | 값 |
|------|-----|
| Base URL | `http://<host>:8000` |
| API Prefix | `/api` |
| Content-Type | `application/json` |
| 인증 | 없음 (로컬 네트워크용) |

### 1.2 응답 형식

**성공 응답:**
```json
{
  "success": true,
  "data": { ... }
}
```

**에러 응답:**
```json
{
  "detail": "에러 메시지"
}
```

### 1.3 자동 문서화

- **Swagger UI**: `http://<host>:8000/docs`
- **ReDoc**: `http://<host>:8000/redoc`

---

## 2. 하드웨어 API (`/api/hardware`)

### 2.1 상태 조회

#### GET `/hardware/status`

모든 하드웨어 컨트롤러의 상태를 조회합니다.

**응답:**
```json
{
  "gpio": {
    "name": "GPIO Controller",
    "state": "ready",
    "simulation_mode": false,
    "last_update": "2024-01-01T12:00:00Z"
  },
  "pwm": { ... },
  "i2c": { ... },
  "spi": { ... },
  "sensors": { ... },
  "display": { ... },
  "neopixel": { ... }
}
```

#### GET `/hardware/data`

현재 하드웨어 데이터 스냅샷을 조회합니다.

**응답:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "gpio": {
    "leds": [true, false, false, true],
    "buttons": [false, false, false, false],
    "relays": [false, false]
  },
  "pwm": {
    "motor_speed": 50,
    "servo_angle": 90
  },
  "sensors": {
    "temperature": 25.5,
    "humidity": 60.0,
    "pressure": 1013.25,
    "altitude": 100.5,
    "distance": 45.2,
    "motion": false,
    "light_level": 512,
    "soil_moisture": 600
  },
  "adc": {
    "i2c": {"0": 2.5, "1": 1.2, "2": 0.8, "3": 3.0},
    "spi": {"0": 750, "1": 500, "2": 1000, "3": 100}
  }
}
```

---

### 2.2 GPIO 제어

#### GET `/hardware/gpio`

GPIO 상태를 조회합니다.

**응답:**
```json
{
  "leds": [
    {"pin": 17, "state": true, "name": "LED 0"},
    {"pin": 27, "state": false, "name": "LED 1"},
    {"pin": 22, "state": false, "name": "LED 2"},
    {"pin": 23, "state": true, "name": "LED 3"}
  ],
  "buttons": [
    {"pin": 5, "state": false, "name": "Button 0"},
    {"pin": 6, "state": false, "name": "Button 1"},
    {"pin": 13, "state": false, "name": "Button 2"},
    {"pin": 19, "state": false, "name": "Button 3"}
  ],
  "relays": [
    {"pin": 24, "state": false, "name": "Relay 0"},
    {"pin": 25, "state": false, "name": "Relay 1"}
  ]
}
```

#### POST `/hardware/gpio/led`

LED를 제어합니다.

**요청:**
```json
{
  "led_index": 0,
  "state": true
}
```

| 파라미터 | 타입 | 범위 | 설명 |
|---------|------|------|------|
| led_index | int | 0-3 | LED 인덱스 |
| state | bool | true/false | LED 상태 |

**응답:**
```json
{
  "success": true,
  "led": 0,
  "state": true
}
```

#### POST `/hardware/gpio/leds/all`

모든 LED를 동시에 제어합니다.

**요청:**
```json
{
  "state": true
}
```

#### POST `/hardware/gpio/relay`

릴레이를 제어합니다.

**요청:**
```json
{
  "relay_index": 0,
  "state": true
}
```

| 파라미터 | 타입 | 범위 | 설명 |
|---------|------|------|------|
| relay_index | int | 0-1 | 릴레이 인덱스 |
| state | bool | true/false | 릴레이 상태 |

---

### 2.3 PWM 제어

#### GET `/hardware/pwm`

PWM 상태를 조회합니다.

**응답:**
```json
{
  "motor": {
    "pin": 18,
    "speed": 50,
    "frequency": 1000
  },
  "servo": {
    "pin": 12,
    "angle": 90,
    "frequency": 50
  }
}
```

#### POST `/hardware/pwm/motor`

모터 속도를 설정합니다.

**요청:**
```json
{
  "speed": 75
}
```

| 파라미터 | 타입 | 범위 | 설명 |
|---------|------|------|------|
| speed | int | 0-100 | 모터 속도 (%) |

#### POST `/hardware/pwm/servo`

서보 각도를 설정합니다.

**요청:**
```json
{
  "angle": 90
}
```

| 파라미터 | 타입 | 범위 | 설명 |
|---------|------|------|------|
| angle | int | 0-180 | 서보 각도 (°) |

---

### 2.4 센서 읽기

#### GET `/hardware/sensors`

모든 센서 데이터를 조회합니다.

**응답:**
```json
{
  "temperature": 25.5,
  "humidity": 60.0,
  "distance": 45.2,
  "motion": false,
  "light": 512,
  "soil_moisture": 600
}
```

#### GET `/hardware/sensors/dht`

DHT 센서 데이터를 조회합니다.

**응답:**
```json
{
  "temperature": 25.5,
  "humidity": 60.0
}
```

#### GET `/hardware/sensors/distance`

초음파 거리 센서 데이터를 조회합니다.

**응답:**
```json
{
  "distance": 45.2,
  "unit": "cm"
}
```

---

### 2.5 I2C 장치

#### GET `/hardware/i2c/scan`

I2C 버스를 스캔합니다.

**응답:**
```json
{
  "devices": [
    {"address": 39, "hex": "0x27", "name": "LCD"},
    {"address": 60, "hex": "0x3C", "name": "OLED"},
    {"address": 72, "hex": "0x48", "name": "ADS1115"},
    {"address": 118, "hex": "0x76", "name": "BMP280"}
  ]
}
```

#### GET `/hardware/i2c/bmp280`

BMP280 센서 데이터를 조회합니다.

**응답:**
```json
{
  "temperature": 25.5,
  "pressure": 1013.25,
  "altitude": 100.5
}
```

#### GET `/hardware/i2c/adc`

ADS1115 ADC 데이터를 조회합니다.

**쿼리 파라미터:**
| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|-------|------|
| channel | int | 모든 채널 | 특정 채널만 조회 (0-3) |

**응답:**
```json
{
  "channels": {
    "0": 2.5,
    "1": 1.2,
    "2": 0.8,
    "3": 3.0
  }
}
```

---

### 2.6 SPI 장치

#### GET `/hardware/spi/mcp3008`

MCP3008 ADC 데이터를 조회합니다.

**쿼리 파라미터:**
| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|-------|------|
| channel | int | 모든 채널 | 특정 채널만 조회 (0-7) |

**응답:**
```json
{
  "channels": {
    "0": 750,
    "1": 500,
    "2": 1000,
    "3": 100,
    "4": 512,
    "5": 512,
    "6": 512,
    "7": 512
  },
  "voltage": {
    "0": 2.42,
    "1": 1.61,
    "2": 3.23,
    "3": 0.32
  }
}
```

---

### 2.7 디스플레이

#### POST `/hardware/display/lcd/write`

LCD에 텍스트를 출력합니다.

**요청:**
```json
{
  "text": "Hello World!",
  "row": 0,
  "col": 0
}
```

| 파라미터 | 타입 | 범위 | 설명 |
|---------|------|------|------|
| text | string | - | 표시할 텍스트 |
| row | int | 0-3 | 행 번호 |
| col | int | 0-19 | 열 번호 |

#### POST `/hardware/display/lcd/clear`

LCD를 지웁니다.

#### POST `/hardware/display/oled/text`

OLED에 텍스트를 출력합니다.

**요청:**
```json
{
  "text": "Hello",
  "x": 0,
  "y": 0
}
```

---

### 2.8 NeoPixel

#### POST `/hardware/neopixel/color`

NeoPixel 색상을 설정합니다.

**요청:**
```json
{
  "color": "#FF0000",
  "index": null
}
```

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| color | string | HEX 색상 코드 |
| index | int/null | 특정 LED 인덱스 (null = 전체) |

#### POST `/hardware/neopixel/effect`

NeoPixel 효과를 시작합니다.

**요청:**
```json
{
  "effect": "rainbow",
  "speed": 0.05
}
```

| 효과 | 설명 |
|------|------|
| rainbow | 무지개 순환 |
| breathing | 숨쉬기 효과 |
| chase | 추적 효과 |
| sparkle | 반짝임 |
| wave | 파도 효과 |
| fire | 불꽃 효과 |

#### POST `/hardware/neopixel/effect/stop`

현재 효과를 중지합니다.

#### POST `/hardware/neopixel/clear`

모든 LED를 끕니다.

---

### 2.9 시뮬레이션

#### POST `/hardware/simulation/values`

시뮬레이션 값을 설정합니다.

**요청:**
```json
{
  "temperature": 30.0,
  "humidity": 70.0,
  "pressure": 1000.0,
  "distance": 50.0,
  "motion": true,
  "light_level": 800
}
```

#### POST `/hardware/simulation/button`

버튼 누름을 시뮬레이션합니다.

**요청:**
```json
{
  "button_index": 0,
  "duration_ms": 100
}
```

---

## 3. 시스템 API (`/api/system`)

### 3.1 GET `/system/metrics`

시스템 메트릭을 조회합니다.

**응답:**
```json
{
  "cpu": {
    "percent": 15.5,
    "count": 4,
    "freq_current": 1500,
    "freq_max": 1800,
    "temperature": 45.0
  },
  "memory": {
    "total": 4.0,
    "available": 2.5,
    "used": 1.5,
    "percent": 37.5
  },
  "disk": {
    "total": 32.0,
    "used": 8.0,
    "free": 24.0,
    "percent": 25.0
  },
  "network": {
    "bytes_sent": 1234567,
    "bytes_recv": 9876543
  },
  "uptime": 86400,
  "boot_time": 1704067200
}
```

### 3.2 GET `/system/summary`

시스템 요약 정보를 조회합니다.

**응답:**
```json
{
  "cpu_percent": 15.5,
  "memory_percent": 37.5,
  "disk_percent": 25.0,
  "temperature": 45.0,
  "uptime_hours": 24.0
}
```

### 3.3 GET `/system/health`

시스템 건강 상태를 조회합니다.

**응답:**
```json
{
  "status": "healthy",
  "warnings": [],
  "checks": {
    "cpu": {"status": "ok", "value": 15.5},
    "memory": {"status": "ok", "value": 37.5},
    "disk": {"status": "ok", "value": 25.0},
    "temperature": {"status": "ok", "value": 45.0}
  }
}
```

**경고 예시:**
```json
{
  "status": "warning",
  "warnings": [
    "CPU temperature is high (75°C)",
    "Memory usage is high (92%)"
  ]
}
```

### 3.4 GET `/system/platform`

플랫폼 정보를 조회합니다.

**응답:**
```json
{
  "system": "Linux",
  "node": "raspberrypi",
  "release": "6.1.0-rpi7-rpi-v8",
  "version": "#1 SMP PREEMPT Debian 1:6.1.63-1+rpt1",
  "machine": "aarch64",
  "processor": "aarch64",
  "python_version": "3.11.2",
  "is_raspberry_pi": true
}
```

### 3.5 GET `/system/config`

애플리케이션 설정을 조회합니다.

**응답:**
```json
{
  "simulation_mode": false,
  "hardware_update_interval": 0.5,
  "data_log_interval": 5.0,
  "data_retention_days": 30,
  "is_raspberry_pi": true,
  "debug": false
}
```

---

## 4. 데이터 API (`/api/data`)

### 4.1 GET `/data/sensors`

센서 데이터 히스토리를 조회합니다.

**쿼리 파라미터:**
| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|-------|------|
| sensor_type | string | 모든 타입 | 센서 타입 필터 |
| hours | int | 24 | 조회 시간 범위 |
| limit | int | 1000 | 최대 결과 수 |

**응답:**
```json
{
  "data": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "sensor_type": "DHT",
      "temperature": 25.5,
      "humidity": 60.0
    }
  ],
  "count": 100
}
```

### 4.2 GET `/data/temperature`

온도 추세 데이터를 조회합니다.

**쿼리 파라미터:**
| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|-------|------|
| hours | int | 24 | 조회 시간 범위 |

**응답:**
```json
{
  "data": [
    {"timestamp": "2024-01-01T00:00:00Z", "value": 24.5},
    {"timestamp": "2024-01-01T01:00:00Z", "value": 25.0}
  ],
  "min": 24.0,
  "max": 26.5,
  "avg": 25.2
}
```

### 4.3 GET `/data/logs`

시스템 로그를 조회합니다.

**쿼리 파라미터:**
| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|-------|------|
| level | string | 모든 레벨 | 로그 레벨 필터 |
| limit | int | 100 | 최대 결과 수 |

**응답:**
```json
{
  "logs": [
    {
      "timestamp": "2024-01-01T12:00:00Z",
      "level": "INFO",
      "message": "System started",
      "source": "main"
    }
  ],
  "count": 50
}
```

### 4.4 POST `/data/cleanup`

오래된 데이터를 정리합니다.

**요청:**
```json
{
  "retention_days": 30
}
```

**응답:**
```json
{
  "deleted_sensor_records": 1500,
  "deleted_log_records": 500,
  "deleted_device_records": 200
}
```

---

## 5. WebSocket API (`/api/ws`)

### 5.1 연결

**엔드포인트:**
```
ws://<host>:8000/api/ws/live
```

### 5.2 메시지 형식

#### 클라이언트 → 서버

**구독:**
```json
{
  "type": "subscribe",
  "topics": ["hardware", "system", "logs"]
}
```

| 토픽 | 설명 |
|------|------|
| hardware | 하드웨어 데이터 업데이트 |
| system | 시스템 메트릭 업데이트 |
| logs | 로그 업데이트 |
| all | 모든 토픽 |

**하트비트 응답:**
```json
{
  "type": "pong"
}
```

#### 서버 → 클라이언트

**하드웨어 업데이트:**
```json
{
  "type": "hardware_update",
  "topic": "hardware",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "gpio": { ... },
    "pwm": { ... },
    "sensors": { ... },
    "adc": { ... }
  }
}
```

**시스템 업데이트:**
```json
{
  "type": "system_update",
  "topic": "system",
  "timestamp": "2024-01-01T12:00:00Z",
  "data": {
    "cpu": { ... },
    "memory": { ... },
    "disk": { ... },
    "network": { ... }
  }
}
```

**하트비트:**
```json
{
  "type": "ping"
}
```

### 5.3 상태 조회

#### GET `/ws/status`

WebSocket 매니저 상태를 조회합니다.

**응답:**
```json
{
  "connected_clients": 2,
  "max_clients": 10,
  "heartbeat_interval": 30
}
```

#### GET `/ws/clients`

연결된 클라이언트 목록을 조회합니다.

**응답:**
```json
{
  "clients": [
    {
      "id": "abc123",
      "connected_at": "2024-01-01T12:00:00Z",
      "topics": ["all"]
    }
  ]
}
```

---

## 6. 에러 코드

| 상태 코드 | 설명 |
|----------|------|
| 200 | 성공 |
| 400 | 잘못된 요청 (파라미터 오류) |
| 404 | 리소스 없음 |
| 422 | 유효성 검사 실패 |
| 500 | 서버 내부 오류 |
| 503 | 하드웨어 사용 불가 |

**에러 응답 예시:**
```json
{
  "detail": [
    {
      "loc": ["body", "led_index"],
      "msg": "ensure this value is less than or equal to 3",
      "type": "value_error.number.not_le"
    }
  ]
}
```
