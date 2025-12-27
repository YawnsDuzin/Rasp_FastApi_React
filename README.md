# Raspberry Pi HMI (Human-Machine Interface)

라즈베리파이를 활용한 실시간 웹 기반 HMI(Human-Machine Interface) 시스템입니다.

## 주요 특징

- **실시간 통신**: WebSocket 기반 Push 방식으로 즉각적인 데이터 업데이트
- **하드웨어 제어**: GPIO, PWM, I2C, SPI 등 다양한 하드웨어 인터페이스 지원
- **시스템 모니터링**: CPU, 메모리, 디스크, 온도 실시간 모니터링
- **데이터 로깅**: SQLite WAL 모드로 SD 카드 수명 보호
- **시뮬레이션 모드**: 라즈베리파이 없이도 개발 및 테스트 가능 (수동 값 설정 지원)
- **반응형 UI**: 모바일/태블릿/데스크톱 모든 환경 지원
- **Gmail 스타일 UI**: 사이드바 토글 메뉴로 깔끔한 레이아웃

## 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │   React + Tailwind CSS + Recharts (Dashboard UI)        │ │
│  │   - 실시간 게이지 차트                                    │ │
│  │   - 하드웨어 제어 스위치/슬라이더                          │ │
│  │   - 시스템 모니터링 대시보드                               │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │ WebSocket / REST API
┌───────────────────────────▼─────────────────────────────────┐
│                   Communication Layer                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │   FastAPI + WebSocket (Real-time Data Push)             │ │
│  │   - Pydantic 데이터 검증                                  │ │
│  │   - SQLite 데이터 로깅                                    │ │
│  │   - 시스템 리소스 모니터링 (psutil)                       │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │ Hardware Abstraction
┌───────────────────────────▼─────────────────────────────────┐
│                     Hardware Layer                           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │   GPIO Controller (LED, Button, Relay)                  │ │
│  │   PWM Controller (Motor, Servo)                         │ │
│  │   I2C Controller (BMP280, ADS1115, OLED)               │ │
│  │   SPI Controller (MCP3008)                              │ │
│  │   Sensor Controller (DHT22, HC-SR04, PIR)              │ │
│  │   NeoPixel Controller (WS2812B LED Strip)              │ │
│  │   Display Controller (OLED SSD1306, LCD 1602/2004)     │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 지원 하드웨어

| 컴포넌트 | 모델 | 인터페이스 | 설명 |
|---------|------|------------|------|
| LED | 일반 LED | GPIO | 4개 LED 제어 |
| 버튼 | 택트 스위치 | GPIO (풀업) | 4개 버튼 입력 |
| 릴레이 | 5V 릴레이 모듈 | GPIO | 2채널 릴레이 |
| 모터 | DC 모터 | PWM | 속도 제어 0-100% |
| 서보 | SG90/MG996R | PWM | 각도 0-180° |
| 온습도 | DHT11/DHT22 | GPIO | 온도/습도 측정 |
| 기압계 | BMP280 | I2C | 온도/기압/고도 |
| ADC | ADS1115 | I2C | 4채널 16비트 ADC |
| ADC | MCP3008 | SPI | 8채널 10비트 ADC |
| 거리센서 | HC-SR04 | GPIO | 초음파 거리 측정 |
| 모션센서 | HC-SR501 | GPIO | PIR 동작 감지 |
| 조도센서 | LDR | ADC | 밝기 측정 |
| 토양수분 | 아날로그 | ADC | 토양 수분 측정 |
| OLED | SSD1306 | I2C | 128x64 디스플레이 |
| LCD | 1602/2004 | I2C | 문자 LCD |
| LED 스트립 | WS2812B | GPIO | NeoPixel 8개 |

## 빠른 시작

### 🐧 Linux / Raspberry Pi 설치

#### 1. 의존성 설치

```bash
# 저장소 클론
git clone https://github.com/your-repo/Rasp_FastApi_React.git
cd Rasp_FastApi_React

# 설치 스크립트 실행 (라즈베리파이 자동 감지)
chmod +x scripts/install.sh
./scripts/install.sh
```

> **참고**: 라즈베리파이에서 실행 시 GPIO/I2C/SPI 하드웨어가 자동 활성화됩니다.
> 일반 Linux에서는 시뮬레이션 모드로 자동 설정됩니다.

#### 2. 서버 실행

```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 3. 웹 브라우저 접속

```
http://<라즈베리파이_IP>:8000
```

---

### 🪟 Windows PC 설치

Windows에서는 **시뮬레이션 모드**로만 동작합니다 (실제 하드웨어 제어 불가).
개발 및 테스트 목적으로 사용할 수 있습니다.

#### 사전 요구사항

- [Python 3.9+](https://www.python.org/downloads/) 설치
- [Node.js 18+](https://nodejs.org/) 설치
- [Git](https://git-scm.com/downloads) 설치

#### 1. 저장소 클론

```powershell
git clone https://github.com/your-repo/Rasp_FastApi_React.git
cd Rasp_FastApi_React
```

#### 2. Backend 설치

```powershell
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
.\venv\Scripts\activate

# 의존성 설치
python.exe -m pip install --upgrade pip

pip install -r requirements.txt
```

> **참고**: `requirements.txt`는 유연한 버전 지정(`>=`)을 사용하여 Windows/Linux 호환성을 보장합니다.

#### 3. Frontend 설치 및 빌드

```powershell
cd ..\frontend

# 의존성 설치
npm install

# 프로덕션 빌드
npm run build

# 빌드 결과물을 backend로 복사
mkdir ..\backend\static -Force
Copy-Item -Path .\dist\* -Destination ..\backend\static\ -Recurse -Force
```

#### 4. 환경 설정

`backend/.env` 파일을 생성합니다:

```powershell
cd ..\backend
```

다음 내용으로 `.env` 파일 생성:

```env
DEBUG=false
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
SIMULATION_MODE=true
HARDWARE_UPDATE_INTERVAL=0.5
DATA_LOG_INTERVAL=5.0
DATA_RETENTION_DAYS=30
```

#### 5. 서버 실행

```powershell
# backend 폴더에서 가상환경 활성화 상태로 실행
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 6. 웹 브라우저 접속

```
http://localhost:8000
```

---

## 개발 환경 설정

### Backend (FastAPI)

**Linux / Raspberry Pi:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 개발 서버 실행 (자동 리로드)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Windows:**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# 개발 서버 실행 (자동 리로드)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (React)

```bash
cd frontend
npm install

# 개발 서버 실행
npm run dev
```

> **참고**: Frontend 개발 서버는 Linux와 Windows 모두 동일한 명령어입니다.

## 배포

### Systemd 서비스 등록

```bash
sudo ./scripts/install-service.sh
```

### 키오스크 모드 설정

```bash
sudo ./scripts/setup-kiosk.sh
sudo reboot
```

## 프로젝트 구조

```
Rasp_FastApi_React/
├── backend/                    # FastAPI 백엔드
│   ├── app/
│   │   ├── api/               # REST API 라우터
│   │   │   ├── hardware.py    # 하드웨어 제어 API
│   │   │   ├── system.py      # 시스템 모니터링 API
│   │   │   ├── data.py        # 데이터 조회 API
│   │   │   └── websocket.py   # WebSocket 엔드포인트
│   │   ├── core/              # 설정 및 로깅
│   │   ├── hardware/          # 하드웨어 컨트롤러
│   │   │   ├── gpio_controller.py    # LED, 버튼, 릴레이 제어
│   │   │   ├── pwm_controller.py     # 모터, 서보 제어
│   │   │   ├── i2c_controller.py     # BMP280, ADS1115 등
│   │   │   ├── spi_controller.py     # MCP3008 ADC
│   │   │   ├── sensor_controller.py  # DHT, 초음파, PIR 센서
│   │   │   ├── display_controller.py # OLED, LCD 디스플레이
│   │   │   ├── neopixel_controller.py
│   │   │   └── manager.py     # 통합 하드웨어 매니저
│   │   ├── models/            # 데이터베이스 모델
│   │   ├── services/          # 비즈니스 로직
│   │   └── main.py            # 애플리케이션 진입점
│   ├── requirements.txt       # Python 의존성 (유연한 버전)
│   └── data/                  # SQLite 데이터베이스
├── frontend/                   # React 프론트엔드
│   ├── src/
│   │   ├── components/        # UI 컴포넌트 (Layout, Toggle 등)
│   │   ├── pages/             # 페이지 컴포넌트
│   │   │   ├── Dashboard.tsx  # 대시보드 (센서, GPIO 상태)
│   │   │   ├── Hardware.tsx   # 하드웨어 제어 (버튼, LCD 포함)
│   │   │   └── Settings.tsx   # 설정 (시뮬레이션 제어)
│   │   ├── hooks/             # React 훅
│   │   ├── services/          # API 서비스
│   │   └── types/             # TypeScript 타입
│   ├── vite.config.ts         # Vite 설정 (WebSocket 프록시 포함)
│   └── package.json
├── scripts/                    # 배포 스크립트
│   ├── install.sh
│   ├── install-service.sh
│   └── setup-kiosk.sh
├── docs/                       # 문서
└── config/                     # 설정 파일
```

## API 문서

서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### 주요 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/hardware/status` | 하드웨어 상태 조회 |
| GET | `/api/hardware/data` | 실시간 데이터 조회 |
| POST | `/api/hardware/gpio/led` | LED 제어 |
| POST | `/api/hardware/gpio/relay` | 릴레이 제어 |
| POST | `/api/hardware/pwm/motor` | 모터 속도 제어 |
| POST | `/api/hardware/pwm/servo` | 서보 각도 제어 |
| GET | `/api/hardware/sensors` | 센서 데이터 조회 |
| POST | `/api/hardware/neopixel/effect` | NeoPixel 효과 설정 |
| POST | `/api/hardware/display/lcd/write` | LCD 텍스트 쓰기 |
| POST | `/api/hardware/display/lcd/clear` | LCD 화면 지우기 |
| GET | `/api/system/metrics` | 시스템 메트릭 조회 |
| GET | `/api/system/health` | 시스템 상태 확인 |
| GET | `/api/data/sensors` | 센서 기록 조회 |
| GET | `/api/data/temperature` | 온도 트렌드 조회 |
| WS | `/api/ws/live` | WebSocket 실시간 연결 |

## WebSocket 프로토콜

### 연결

```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/live');
```

### 메시지 타입

**수신 메시지:**
```json
{
  "type": "hardware_update",
  "topic": "hardware",
  "data": {
    "timestamp": "2024-01-01T00:00:00",
    "gpio": { "leds": {}, "buttons": {}, "relays": {} },
    "sensors": { "temperature": 25.0, "humidity": 50.0 }
  }
}
```

**구독 요청:**
```json
{
  "type": "subscribe",
  "topics": ["hardware", "system"]
}
```

## 환경 설정

`.env` 파일로 설정을 관리합니다:

```env
DEBUG=false
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
SIMULATION_MODE=false
HARDWARE_UPDATE_INTERVAL=0.5
DATA_LOG_INTERVAL=5.0
DATA_RETENTION_DAYS=30
```

## 하드웨어 연결

### GPIO 핀 배치 (BCM 모드)

```
LED:      GPIO 17, 27, 22, 23
버튼:     GPIO 5, 6, 13, 19
릴레이:   GPIO 24, 25
PWM:      GPIO 18 (모터)
서보:     GPIO 12
DHT:      GPIO 4
NeoPixel: GPIO 21
```

### I2C 연결

```
SDA: GPIO 2
SCL: GPIO 3

BMP280:  0x76
ADS1115: 0x48
OLED:    0x3C
LCD:     0x27
```

### SPI 연결

```
MOSI: GPIO 10
MISO: GPIO 9
SCLK: GPIO 11
CE0:  GPIO 8

MCP3008: CE0
```

## 문제 해결

### I2C 장치가 감지되지 않음

```bash
# I2C 활성화 확인
sudo raspi-config nonint get_i2c
# 0이면 비활성화, 1이면 활성화

# I2C 장치 스캔
i2cdetect -y 1
```

### 권한 오류

```bash
# GPIO 그룹에 사용자 추가
sudo usermod -aG gpio $USER

# I2C 그룹에 사용자 추가
sudo usermod -aG i2c $USER

# 재로그인 필요
```

### 시뮬레이션 모드 강제 활성화

```env
SIMULATION_MODE=true
```

## UI 특징

### Gmail 스타일 사이드바
- 햄버거 메뉴가 사이드바 상단 좌측에 위치
- 사이드바 접힘 시 로고가 숨겨지고 메뉴 아이콘만 표시
- 반응형 레이아웃으로 모바일 환경 지원

### Dashboard 페이지
- 센서 데이터 실시간 게이지 (온도, 습도, 거리, 조도 등)
- LED 상태 표시
- **버튼 상태 표시** (4개 버튼 읽기 전용)
- 릴레이 상태 표시
- 시스템 메트릭 (CPU, 메모리, 디스크)

### Hardware 페이지
- LED 제어 (4개 개별 토글)
- **버튼 상태 모니터링** (읽기 전용, 눌림/해제 상태 표시)
- 릴레이 제어 (2채널)
- 모터 속도 조절 (PWM 0-100%)
- 서보 각도 조절 (0-180°)
- NeoPixel 효과 선택
- **LCD 디스플레이 제어** (텍스트 쓰기, 행 선택, 화면 지우기)
- **OLED 디스플레이 정보** (자동 상태 표시)

### Settings 페이지
- 시뮬레이션 모드 제어 (센서 값 수동 설정)
- 다크 모드 토글
- 시스템 정보 표시

## 시뮬레이션 모드

시뮬레이션 모드에서는 실제 하드웨어 없이 모든 기능을 테스트할 수 있습니다.

### 센서 값 수동 설정
Settings 페이지의 Simulation Controls에서 각 센서 값을 수동으로 설정할 수 있습니다:
- 수동 설정된 값은 자동 드리프트가 비활성화됩니다
- 설정하지 않은 센서는 자동으로 현실적인 값을 시뮬레이션합니다

## 라이선스

MIT License

## 기여

Pull Request 환영합니다!
