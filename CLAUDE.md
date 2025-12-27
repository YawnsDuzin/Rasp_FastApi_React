# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Raspberry Pi HMI (Human-Machine Interface) system with FastAPI backend and React frontend. Supports both real hardware (Raspberry Pi) and simulation mode (Windows/Linux development).

## Common Commands

### Backend (from `backend/` directory)
```bash
# Activate virtual environment
# Linux/Mac: source venv/bin/activate
# Windows: .\venv\Scripts\activate

# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest
pytest tests/test_hardware.py -v           # Single test file
pytest tests/test_api.py::test_led -v      # Single test function
```

### Frontend (from `frontend/` directory)
```bash
npm install           # Install dependencies
npm run dev           # Development server (port 3000)
npm run build         # TypeScript check + production build
npm run lint          # ESLint (strict, zero warnings allowed)
npm run test          # Vitest unit tests
npm run test -- --run src/hooks/useStore.test.ts  # Single test file
```

### Full Stack Development
Run backend on port 8000, frontend dev server on port 3000. Vite proxies `/api` requests to backend.

### Production Build & Deploy
```bash
cd frontend && npm run build              # Build React app
cp -r dist/* ../backend/static/           # Copy to backend static folder
cd ../backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Architecture

```
frontend/                    # React + TypeScript + Vite
├── src/
│   ├── pages/              # Dashboard, Hardware, Sensors, System, Settings
│   ├── components/         # Layout (Gmail-style sidebar), GaugeChart, Toggle, Slider
│   ├── hooks/              # useStore (Zustand), useWebSocket
│   ├── services/           # api.ts, websocket.ts
│   └── types/              # TypeScript interfaces

backend/                     # FastAPI + SQLAlchemy
├── app/
│   ├── api/                # REST endpoints + WebSocket
│   │   ├── hardware.py     # GPIO, PWM, I2C, SPI, sensors, displays
│   │   ├── system.py       # CPU, memory, disk monitoring
│   │   ├── data.py         # Sensor history queries
│   │   └── websocket.py    # Real-time push updates
│   ├── hardware/           # Hardware abstraction layer
│   │   ├── gpio_controller.py    # LEDs, buttons, relays
│   │   ├── pwm_controller.py     # Motor, servo
│   │   ├── sensor_controller.py  # DHT22, HC-SR04, PIR
│   │   ├── display_controller.py # OLED, LCD
│   │   ├── manager.py           # Unified hardware manager
│   │   └── base.py              # SimulationMixin for dev mode
│   ├── services/           # WebSocket manager, system monitor, data logger
│   ├── models/             # SQLAlchemy models
│   └── core/config.py      # Pydantic settings, GPIO pin mappings
└── data/                   # SQLite database (WAL mode)
```

## Key Patterns

### Simulation Mode
- Auto-detected: Raspberry Pi hardware vs Windows/Linux
- Set `SIMULATION_MODE=true` in `.env` to force simulation
- `SimulationMixin` in `base.py` provides realistic fake values with drift
- Sensor values can be manually set via Settings page (disables auto-drift)

### Real-time Communication
- WebSocket at `/api/ws/live` pushes hardware updates
- Topics: `hardware`, `system` (subscribe via JSON message)
- Frontend uses `useWebSocket` hook for auto-reconnection

### Hardware Controllers
All controllers extend `BaseHardwareController` with:
- `initialize()` / `shutdown()` lifecycle
- `simulation_mode` property for dev environment
- `asyncio.to_thread()` for non-blocking hardware I/O

### State Management
Zustand store in `useStore.ts` manages:
- Hardware data (GPIO, PWM, sensors)
- System metrics (CPU, memory, disk)
- Connection status, alerts, dark mode

### Data Flow
```
Frontend → Backend: REST API (user commands like LED toggle)
Backend → Frontend: WebSocket (real-time sensor data push)
```

## Configuration

### Backend `.env`
```env
SIMULATION_MODE=true          # Force simulation mode
HARDWARE_UPDATE_INTERVAL=0.5  # Seconds between updates
DATA_LOG_INTERVAL=5.0         # Seconds between DB writes
DATA_RETENTION_DAYS=30        # Auto-cleanup period
```

### GPIO Pin Mapping (BCM)
- LEDs: 17, 27, 22, 23
- Buttons: 5, 6, 13, 19
- Relays: 24, 25
- PWM Motor: 18, Servo: 12
- DHT: 4, NeoPixel: 21

### I2C Addresses
- LCD: 0x27, OLED: 0x3C
- BMP280: 0x76, ADS1115: 0x48

## API Documentation
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- Detailed docs: `docs/API.md`

## Database
SQLite with WAL mode at `backend/data/hmi_data.db`. Protects SD card from excessive writes.

## Documentation
All documentation is in the `docs/` folder as flat markdown files:
- `ARCHITECTURE.md` - System design and tech stack
- `INTEGRATION.md` - Frontend-Backend communication details
- `BACKEND.md` / `FRONTEND.md` - Development guides
- `HARDWARE.md` - Wiring and pin configuration
- `DEPLOYMENT.md` - Installation and service setup
