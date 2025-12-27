# 프론트엔드 개발 가이드

## 1. 디렉토리 구조

```
frontend/
├── src/
│   ├── main.tsx                    # 애플리케이션 엔트리포인트
│   ├── App.tsx                     # 메인 App 컴포넌트
│   ├── components/                 # 재사용 가능한 UI 컴포넌트
│   │   ├── Layout.tsx              # Gmail 스타일 레이아웃 (사이드바, 네비게이션)
│   │   ├── GaugeChart.tsx          # SVG 게이지 차트 컴포넌트
│   │   └── ui/                     # shadcn/ui 스타일 컴포넌트
│   │       ├── button.tsx          # 버튼 컴포넌트
│   │       ├── card.tsx            # 카드 컴포넌트
│   │       ├── switch.tsx          # 토글 스위치 컴포넌트
│   │       ├── slider.tsx          # 슬라이더 컴포넌트
│   │       ├── badge.tsx           # 뱃지 컴포넌트
│   │       ├── select.tsx          # 셀렉트 컴포넌트
│   │       ├── input.tsx           # 인풋 컴포넌트
│   │       ├── label.tsx           # 라벨 컴포넌트
│   │       ├── progress.tsx        # 프로그레스 바 컴포넌트
│   │       └── index.ts            # 컴포넌트 re-export
│   ├── lib/                        # 유틸리티 함수
│   │   └── utils.ts                # cn() 클래스명 병합 유틸리티
│   ├── pages/                      # 페이지 컴포넌트
│   │   ├── Dashboard.tsx           # 대시보드
│   │   ├── Hardware.tsx            # 하드웨어 제어
│   │   ├── Sensors.tsx             # 센서 모니터링
│   │   ├── System.tsx              # 시스템 정보
│   │   ├── Logs.tsx                # 로그 뷰어
│   │   └── Settings.tsx            # 설정
│   ├── hooks/                      # 커스텀 훅
│   │   ├── useStore.ts             # Zustand 스토어
│   │   └── useWebSocket.ts         # WebSocket 연결 관리
│   ├── services/                   # 외부 서비스 연동
│   │   ├── api.ts                  # REST API 클라이언트
│   │   └── websocket.ts            # WebSocket 서비스
│   ├── types/                      # TypeScript 타입 정의
│   │   └── index.ts
│   └── styles/                     # 스타일 (Tailwind)
│       └── index.css
├── public/                         # 정적 파일
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── postcss.config.js
```

---

## 2. 핵심 컴포넌트

### 2.1 App.tsx - 메인 애플리케이션

```tsx
import { useEffect } from 'react';
import { useStore } from './hooks/useStore';
import { useWebSocket } from './hooks/useWebSocket';
import { systemApi } from './services/api';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Hardware from './pages/Hardware';
// ... 다른 페이지 imports

function App() {
  const { activePage, setConfig } = useStore();

  // WebSocket 연결 관리
  useWebSocket();

  // 초기 설정 로드
  useEffect(() => {
    systemApi.getConfig().then(setConfig);
  }, []);

  // 페이지 렌더링
  const renderPage = () => {
    switch (activePage) {
      case 'dashboard': return <Dashboard />;
      case 'hardware': return <Hardware />;
      case 'sensors': return <Sensors />;
      case 'system': return <System />;
      case 'logs': return <Logs />;
      case 'settings': return <Settings />;
      default: return <Dashboard />;
    }
  };

  return (
    <Layout>
      {renderPage()}
    </Layout>
  );
}

export default App;
```

### 2.2 Layout.tsx - 레이아웃 컴포넌트

```tsx
import { ReactNode } from 'react';
import { useStore } from '../hooks/useStore';
import {
  Home, Cpu, Thermometer, Monitor, FileText, Settings,
  Sun, Moon, Menu, Wifi, WifiOff
} from 'lucide-react';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const {
    darkMode,
    toggleDarkMode,
    sidebarOpen,
    toggleSidebar,
    activePage,
    setActivePage,
    isConnected
  } = useStore();

  const navItems = [
    { id: 'dashboard', icon: Home, label: '대시보드' },
    { id: 'hardware', icon: Cpu, label: '하드웨어' },
    { id: 'sensors', icon: Thermometer, label: '센서' },
    { id: 'system', icon: Monitor, label: '시스템' },
    { id: 'logs', icon: FileText, label: '로그' },
    { id: 'settings', icon: Settings, label: '설정' },
  ];

  return (
    <div className={`min-h-screen ${darkMode ? 'dark bg-gray-900' : 'bg-gray-100'}`}>
      {/* 사이드바 */}
      <aside className={`fixed left-0 top-0 h-full w-64 bg-white dark:bg-gray-800
                        shadow-lg transform transition-transform
                        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
                        md:translate-x-0`}>
        {/* 로고 */}
        <div className="p-4 border-b dark:border-gray-700">
          <h1 className="text-xl font-bold text-blue-600">Raspberry Pi HMI</h1>
        </div>

        {/* 네비게이션 */}
        <nav className="p-4">
          {navItems.map(({ id, icon: Icon, label }) => (
            <button
              key={id}
              onClick={() => setActivePage(id)}
              className={`w-full flex items-center gap-3 p-3 rounded-lg mb-2
                         ${activePage === id
                           ? 'bg-blue-100 text-blue-600 dark:bg-blue-900'
                           : 'hover:bg-gray-100 dark:hover:bg-gray-700'}`}
            >
              <Icon size={20} />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        {/* 연결 상태 */}
        <div className="absolute bottom-4 left-4 right-4">
          <div className={`flex items-center gap-2 p-3 rounded-lg
                          ${isConnected ? 'bg-green-100 text-green-600'
                                        : 'bg-red-100 text-red-600'}`}>
            {isConnected ? <Wifi size={20} /> : <WifiOff size={20} />}
            <span>{isConnected ? '연결됨' : '연결 끊김'}</span>
          </div>
        </div>
      </aside>

      {/* 메인 콘텐츠 */}
      <main className="md:ml-64 min-h-screen">
        {/* 헤더 */}
        <header className="bg-white dark:bg-gray-800 shadow p-4 flex justify-between">
          <button onClick={toggleSidebar} className="md:hidden">
            <Menu size={24} />
          </button>

          <button onClick={toggleDarkMode}>
            {darkMode ? <Sun size={24} /> : <Moon size={24} />}
          </button>
        </header>

        {/* 페이지 콘텐츠 */}
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  );
}
```

---

## 3. 상태 관리 (Zustand)

### 3.1 useStore.ts - 전역 상태

```tsx
import { create } from 'zustand';
import { HardwareData, SystemMetrics, AppConfig, Alert } from '../types';

interface StoreState {
  // 연결 상태
  isConnected: boolean;
  setConnected: (connected: boolean) => void;

  // 하드웨어 데이터
  hardwareData: HardwareData | null;
  setHardwareData: (data: HardwareData) => void;

  // 시스템 메트릭
  systemMetrics: SystemMetrics | null;
  setSystemMetrics: (metrics: SystemMetrics) => void;

  // 설정
  config: AppConfig | null;
  setConfig: (config: AppConfig) => void;

  // UI 상태
  darkMode: boolean;
  toggleDarkMode: () => void;
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  activePage: string;
  setActivePage: (page: string) => void;

  // 히스토리 데이터 (차트용)
  temperatureHistory: Array<{ time: string; value: number }>;
  humidityHistory: Array<{ time: string; value: number }>;
  addTemperature: (value: number) => void;
  addHumidity: (value: number) => void;

  // 알림
  alerts: Alert[];
  addAlert: (alert: Omit<Alert, 'id' | 'timestamp'>) => void;
  removeAlert: (id: string) => void;
}

export const useStore = create<StoreState>((set, get) => ({
  // 초기 상태
  isConnected: false,
  hardwareData: null,
  systemMetrics: null,
  config: null,
  darkMode: window.matchMedia('(prefers-color-scheme: dark)').matches,
  sidebarOpen: true,
  activePage: 'dashboard',
  temperatureHistory: [],
  humidityHistory: [],
  alerts: [],

  // 액션
  setConnected: (connected) => set({ isConnected: connected }),

  setHardwareData: (data) => {
    set({ hardwareData: data });
    // 히스토리에 추가
    if (data.sensors?.temperature) {
      get().addTemperature(data.sensors.temperature);
    }
    if (data.sensors?.humidity) {
      get().addHumidity(data.sensors.humidity);
    }
  },

  setSystemMetrics: (metrics) => {
    set({ systemMetrics: metrics });
    // 경고 체크
    if (metrics.cpu.temperature > 70) {
      get().addAlert({ type: 'warning', message: 'CPU 온도가 높습니다!' });
    }
    if (metrics.memory.percent > 90) {
      get().addAlert({ type: 'warning', message: '메모리 사용량이 높습니다!' });
    }
  },

  setConfig: (config) => set({ config }),

  toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setActivePage: (page) => set({ activePage: page }),

  addTemperature: (value) => set((state) => {
    const newHistory = [...state.temperatureHistory, {
      time: new Date().toLocaleTimeString(),
      value
    }];
    // 최대 60개 유지
    return { temperatureHistory: newHistory.slice(-60) };
  }),

  addHumidity: (value) => set((state) => {
    const newHistory = [...state.humidityHistory, {
      time: new Date().toLocaleTimeString(),
      value
    }];
    return { humidityHistory: newHistory.slice(-60) };
  }),

  addAlert: (alert) => set((state) => {
    const newAlert = {
      ...alert,
      id: crypto.randomUUID(),
      timestamp: new Date().toISOString()
    };
    // 최대 10개 유지
    return { alerts: [...state.alerts, newAlert].slice(-10) };
  }),

  removeAlert: (id) => set((state) => ({
    alerts: state.alerts.filter(a => a.id !== id)
  }))
}));
```

---

## 4. 서비스 계층

### 4.1 api.ts - REST API 클라이언트

```tsx
const API_BASE = '/api';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers
    },
    ...options
  });

  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }

  return response.json();
}

// === Hardware API ===

export const hardwareApi = {
  getStatus: () => fetchApi<any>('/hardware/status'),
  getData: () => fetchApi<any>('/hardware/data'),

  // LED 제어
  setLed: (index: number, state: boolean) =>
    fetchApi('/hardware/gpio/led', {
      method: 'POST',
      body: JSON.stringify({ led_index: index, state })
    }),

  setAllLeds: (state: boolean) =>
    fetchApi('/hardware/gpio/leds/all', {
      method: 'POST',
      body: JSON.stringify({ state })
    }),

  // 릴레이 제어
  setRelay: (index: number, state: boolean) =>
    fetchApi('/hardware/gpio/relay', {
      method: 'POST',
      body: JSON.stringify({ relay_index: index, state })
    }),

  // PWM 제어
  setMotorSpeed: (speed: number) =>
    fetchApi('/hardware/pwm/motor', {
      method: 'POST',
      body: JSON.stringify({ speed })
    }),

  setServoAngle: (angle: number) =>
    fetchApi('/hardware/pwm/servo', {
      method: 'POST',
      body: JSON.stringify({ angle })
    }),

  // 센서 읽기
  getDht: () => fetchApi('/hardware/sensors/dht'),
  getDistance: () => fetchApi('/hardware/sensors/distance'),
  getBmp280: () => fetchApi('/hardware/i2c/bmp280'),
  getAdc: () => fetchApi('/hardware/i2c/adc'),
  getMcp3008: () => fetchApi('/hardware/spi/mcp3008'),

  // NeoPixel 제어
  setNeopixelColor: (color: string) =>
    fetchApi('/hardware/neopixel/color', {
      method: 'POST',
      body: JSON.stringify({ color })
    }),

  startNeopixelEffect: (effect: string) =>
    fetchApi('/hardware/neopixel/effect', {
      method: 'POST',
      body: JSON.stringify({ effect })
    }),

  stopNeopixelEffect: () =>
    fetchApi('/hardware/neopixel/effect/stop', { method: 'POST' }),

  // LCD 제어
  writeLcd: (text: string, row: number = 0) =>
    fetchApi('/hardware/display/lcd/write', {
      method: 'POST',
      body: JSON.stringify({ text, row })
    }),

  clearLcd: () =>
    fetchApi('/hardware/display/lcd/clear', { method: 'POST' })
};

// === System API ===

export const systemApi = {
  getMetrics: () => fetchApi<SystemMetrics>('/system/metrics'),
  getSummary: () => fetchApi<any>('/system/summary'),
  getHealth: () => fetchApi<any>('/system/health'),
  getPlatform: () => fetchApi<any>('/system/platform'),
  getProcess: () => fetchApi<any>('/system/process'),
  getConfig: () => fetchApi<AppConfig>('/system/config')
};

// === Data API ===

export const dataApi = {
  getSensorHistory: (sensorType?: string, hours?: number, limit?: number) => {
    const params = new URLSearchParams();
    if (sensorType) params.append('sensor_type', sensorType);
    if (hours) params.append('hours', hours.toString());
    if (limit) params.append('limit', limit.toString());
    return fetchApi(`/data/sensors?${params}`);
  },

  getTemperatureTrend: (hours: number = 24) =>
    fetchApi(`/data/temperature?hours=${hours}`),

  getSystemLogs: (level?: string, limit?: number) => {
    const params = new URLSearchParams();
    if (level) params.append('level', level);
    if (limit) params.append('limit', limit.toString());
    return fetchApi(`/data/logs?${params}`);
  },

  cleanupData: (days: number) =>
    fetchApi('/data/cleanup', {
      method: 'POST',
      body: JSON.stringify({ retention_days: days })
    })
};
```

### 4.2 websocket.ts - WebSocket 서비스

```tsx
type MessageHandler = (data: any) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private handlers: Map<string, MessageHandler[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect(): void {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}/api/ws/live`;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.emit('connect', null);

      // 모든 토픽 구독
      this.subscribe(['all']);
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        this.emit(message.type, message);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.emit('disconnect', null);
      this.attemptReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  subscribe(topics: string[]): void {
    this.send({ type: 'subscribe', topics });
  }

  send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  on(event: string, handler: MessageHandler): void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, []);
    }
    this.handlers.get(event)!.push(handler);
  }

  off(event: string, handler: MessageHandler): void {
    const handlers = this.handlers.get(event);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) handlers.splice(index, 1);
    }
  }

  private emit(event: string, data: any): void {
    this.handlers.get(event)?.forEach(handler => handler(data));
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

    setTimeout(() => {
      console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`);
      this.connect();
    }, delay);
  }
}

export const wsService = new WebSocketService();
```

### 4.3 useWebSocket.ts - WebSocket 훅

```tsx
import { useEffect } from 'react';
import { useStore } from './useStore';
import { wsService } from '../services/websocket';

export function useWebSocket() {
  const { setConnected, setHardwareData, setSystemMetrics } = useStore();

  useEffect(() => {
    // 이벤트 핸들러 등록
    const handleConnect = () => setConnected(true);
    const handleDisconnect = () => setConnected(false);

    const handleHardwareUpdate = (message: any) => {
      setHardwareData(message.data);
    };

    const handleSystemUpdate = (message: any) => {
      setSystemMetrics(message.data);
    };

    const handlePing = () => {
      wsService.send({ type: 'pong' });
    };

    wsService.on('connect', handleConnect);
    wsService.on('disconnect', handleDisconnect);
    wsService.on('hardware_update', handleHardwareUpdate);
    wsService.on('system_update', handleSystemUpdate);
    wsService.on('ping', handlePing);

    // 연결 시작
    wsService.connect();

    // 클린업
    return () => {
      wsService.off('connect', handleConnect);
      wsService.off('disconnect', handleDisconnect);
      wsService.off('hardware_update', handleHardwareUpdate);
      wsService.off('system_update', handleSystemUpdate);
      wsService.off('ping', handlePing);
      wsService.disconnect();
    };
  }, []);
}
```

---

## 5. 타입 정의

### 5.1 types/index.ts

```tsx
// === Hardware Types ===

export interface GPIOState {
  leds: boolean[];
  buttons: boolean[];
  relays: boolean[];
}

export interface PWMState {
  motor_speed: number;
  servo_angle: number;
}

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

export interface ADCData {
  i2c: Record<number, number>;  // ADS1115 채널
  spi: Record<number, number>;  // MCP3008 채널
}

export interface HardwareData {
  gpio: GPIOState;
  pwm: PWMState;
  sensors: SensorData;
  adc: ADCData;
  timestamp: string;
}

// === System Types ===

export interface CPUMetrics {
  percent: number;
  count: number;
  freq_current: number;
  freq_max: number;
  temperature: number;
}

export interface MemoryMetrics {
  total: number;
  available: number;
  used: number;
  percent: number;
}

export interface DiskMetrics {
  total: number;
  used: number;
  free: number;
  percent: number;
}

export interface NetworkMetrics {
  bytes_sent: number;
  bytes_recv: number;
}

export interface SystemMetrics {
  cpu: CPUMetrics;
  memory: MemoryMetrics;
  disk: DiskMetrics;
  network: NetworkMetrics;
  uptime: number;
  boot_time: number;
}

// === Config Types ===

export interface AppConfig {
  simulation_mode: boolean;
  hardware_update_interval: number;
  data_log_interval: number;
  data_retention_days: number;
  is_raspberry_pi: boolean;
}

// === UI Types ===

export interface Alert {
  id: string;
  type: 'info' | 'warning' | 'error';
  message: string;
  timestamp: string;
}

// === WebSocket Types ===

export interface WebSocketMessage {
  type: string;
  topic?: string;
  timestamp?: string;
  data?: any;
}
```

---

## 6. 개발 가이드라인

### 6.1 새 페이지 추가

1. `pages/` 디렉토리에 컴포넌트 생성
2. `App.tsx`의 `renderPage()` 함수에 추가
3. `Layout.tsx`의 `navItems`에 추가

### 6.2 새 컴포넌트 추가

1. `components/` 디렉토리에 생성
2. Props 인터페이스 정의
3. Tailwind CSS로 스타일링

### 6.3 API 호출 패턴

```tsx
// 좋은 예: 로딩/에러 상태 처리
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

const handleClick = async () => {
  setLoading(true);
  setError(null);
  try {
    await hardwareApi.setLed(0, true);
  } catch (e) {
    setError(e instanceof ApiError ? e.message : '알 수 없는 오류');
  } finally {
    setLoading(false);
  }
};
```

### 6.4 빌드 및 배포

```bash
# 개발 서버
npm run dev

# 프로덕션 빌드
npm run build

# 빌드 파일은 dist/ 에 생성됨
# 백엔드 static/ 폴더로 복사됨
```
