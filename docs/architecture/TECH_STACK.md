# 기술 스택

## 1. 백엔드 기술 스택

### 1.1 핵심 프레임워크

| 기술 | 버전 | 용도 |
|------|------|------|
| **Python** | 3.9+ | 메인 언어 |
| **FastAPI** | 0.104+ | 웹 프레임워크 |
| **Uvicorn** | 0.24+ | ASGI 서버 |
| **Pydantic** | 2.0+ | 데이터 검증 및 설정 |

### 1.2 비동기 처리

| 기술 | 용도 |
|------|------|
| **asyncio** | Python 비동기 런타임 |
| **aiosqlite** | 비동기 SQLite 드라이버 |
| **websockets** | WebSocket 프로토콜 지원 |

### 1.3 데이터베이스

| 기술 | 버전 | 용도 |
|------|------|------|
| **SQLAlchemy** | 2.0+ | ORM (비동기 모드) |
| **SQLite** | 3.x | 임베디드 데이터베이스 |

**SQLite 설정:**
```python
# WAL 모드 - SD 카드 수명 보호
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
```

### 1.4 시스템 모니터링

| 기술 | 용도 |
|------|------|
| **psutil** | CPU, 메모리, 디스크, 네트워크 정보 |

### 1.5 하드웨어 라이브러리

| 라이브러리 | 용도 | 설치 조건 |
|------------|------|-----------|
| **RPi.GPIO** | GPIO 제어 | 라즈베리파이 |
| **gpiozero** | GPIO 고수준 API | 라즈베리파이 |
| **spidev** | SPI 버스 제어 | 라즈베리파이 |
| **smbus2** | I2C 버스 제어 | 라즈베리파이 |
| **adafruit-circuitpython-dht** | DHT 센서 | 라즈베리파이 |
| **adafruit-circuitpython-bmp280** | BMP280 센서 | 라즈베리파이 |
| **adafruit-circuitpython-ads1x15** | ADS1115 ADC | 라즈베리파이 |
| **adafruit-circuitpython-ssd1306** | OLED 디스플레이 | 라즈베리파이 |
| **adafruit-circuitpython-neopixel** | WS2812B LED | 라즈베리파이 |
| **RPLCD** | LCD 디스플레이 | 라즈베리파이 |

---

## 2. 프론트엔드 기술 스택

### 2.1 핵심 프레임워크

| 기술 | 버전 | 용도 |
|------|------|------|
| **React** | 18.2.0 | UI 라이브러리 |
| **TypeScript** | 5.3.3 | 타입 안전성 |
| **Vite** | 5.0.10 | 빌드 도구 |

### 2.2 상태 관리

| 기술 | 버전 | 용도 |
|------|------|------|
| **Zustand** | 4.4.7 | 전역 상태 관리 |

**Zustand 선택 이유:**
- Redux보다 가벼움 (2KB vs 7KB)
- 보일러플레이트 코드 최소화
- React 외부에서도 상태 접근 가능
- 자동 리렌더링 최적화

### 2.3 UI/스타일링

| 기술 | 버전 | 용도 |
|------|------|------|
| **Tailwind CSS** | 3.4.0 | 유틸리티 CSS |
| **Lucide React** | 0.303.0 | 아이콘 라이브러리 |
| **Recharts** | 2.10.3 | 차트/그래프 |

### 2.4 개발 도구

| 기술 | 용도 |
|------|------|
| **ESLint** | 코드 품질 검사 |
| **PostCSS** | CSS 처리 |
| **Autoprefixer** | 브라우저 호환성 |

---

## 3. 통신 프로토콜

### 3.1 REST API

**특징:**
- JSON 기반 데이터 교환
- OpenAPI (Swagger) 자동 문서화
- Pydantic 기반 요청/응답 검증

**엔드포인트 그룹:**
- `/api/hardware/*` - 하드웨어 제어
- `/api/system/*` - 시스템 정보
- `/api/data/*` - 데이터 조회
- `/api/ws/*` - WebSocket 관리

### 3.2 WebSocket

**프로토콜:**
```
ws://[host]:8000/api/ws/live
```

**메시지 형식:**
```typescript
// 클라이언트 → 서버
{
  "type": "subscribe",
  "topics": ["hardware", "system", "logs"]
}

// 서버 → 클라이언트
{
  "type": "hardware_update",
  "topic": "hardware",
  "timestamp": "2024-01-01T00:00:00Z",
  "data": { ... }
}
```

---

## 4. 데이터 저장

### 4.1 데이터베이스 스키마

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

### 4.2 파일 저장

| 경로 | 용도 |
|------|------|
| `backend/data/hmi_data.db` | SQLite 데이터베이스 |
| `backend/logs/*.log` | 애플리케이션 로그 |
| `backend/.env` | 환경 설정 |

---

## 5. 배포 기술

### 5.1 서비스 관리

| 기술 | 용도 |
|------|------|
| **systemd** | 서비스 관리 및 자동 시작 |
| **journald** | 로그 관리 |

### 5.2 웹 서버

| 기술 | 용도 |
|------|------|
| **Uvicorn** | ASGI 서버 |
| **FastAPI StaticFiles** | React SPA 서빙 |

---

## 6. 개발 환경

### 6.1 Python 환경

```bash
# 가상환경 생성
python3 -m venv venv

# 활성화
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 6.2 Node.js 환경

```bash
# 의존성 설치
npm install

# 개발 서버
npm run dev

# 프로덕션 빌드
npm run build
```

---

## 7. 버전 호환성 매트릭스

| 컴포넌트 | 최소 버전 | 권장 버전 |
|----------|----------|----------|
| Python | 3.9 | 3.11+ |
| Node.js | 16 | 18+ |
| npm | 8 | 9+ |
| Raspberry Pi OS | Bullseye | Bookworm |
| SQLite | 3.31 | 3.40+ |

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
