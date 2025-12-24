/**
 * Type definitions for the HMI application
 */

// Hardware Data Types
export interface GPIOState {
  leds: Record<number, boolean>;
  buttons: Record<number, boolean>;
  relays: Record<number, boolean>;
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
  i2c: Record<number, number>;
  spi: Record<number, number>;
}

export interface NeopixelLED {
  index: number;
  color: string;
  rgb: [number, number, number];
}

export interface HardwareData {
  timestamp: string;
  gpio: GPIOState;
  pwm: PWMState;
  sensors: SensorData;
  adc: ADCData;
  display: {
    lcd_content: string[];
  };
  neopixel: {
    colors: NeopixelLED[];
  };
}

// System Metrics Types
export interface CPUMetrics {
  percent: number;
  count: number;
  frequency: {
    current: number;
    max: number;
  };
  temperature: number | null;
}

export interface MemoryMetrics {
  total: number;
  available: number;
  used: number;
  percent: number;
  total_gb: number;
  used_gb: number;
}

export interface DiskMetrics {
  total: number;
  used: number;
  free: number;
  percent: number;
  total_gb: number;
  free_gb: number;
}

export interface NetworkMetrics {
  bytes_sent: number;
  bytes_recv: number;
  sent_mb: number;
  recv_mb: number;
}

export interface SystemInfo {
  boot_time: string;
  uptime_seconds: number;
  uptime_hours: number;
}

export interface SystemMetrics {
  timestamp: string;
  cpu: CPUMetrics;
  memory: MemoryMetrics;
  disk: DiskMetrics;
  network: NetworkMetrics;
  system: SystemInfo;
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: string;
  topic?: string;
  data?: unknown;
  timestamp?: string;
  client_id?: string;
  broadcast_time?: string;
}

export interface HardwareUpdateMessage extends WebSocketMessage {
  type: 'hardware_update';
  data: HardwareData;
}

export interface SystemUpdateMessage extends WebSocketMessage {
  type: 'system_update';
  data: SystemMetrics;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface HealthStatus {
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  warnings: string[];
  timestamp: string;
}

export interface SystemSummary {
  cpu_percent: number;
  cpu_temp: number | null;
  memory_percent: number;
  disk_percent: number;
  uptime_hours: number;
  health_status: string;
  warnings: string[];
}

// Chart Data Types
export interface ChartDataPoint {
  timestamp: string;
  value: number;
}

export interface SensorHistoryItem {
  id: number;
  timestamp: string;
  sensor_type: string;
  temperature: number | null;
  humidity: number | null;
  pressure: number | null;
  altitude: number | null;
  distance: number | null;
  light_level: number | null;
  soil_moisture: number | null;
  motion: boolean | null;
}

// Hardware Controller Status
export interface ControllerStatus {
  name: string;
  state: 'uninitialized' | 'initializing' | 'ready' | 'error' | 'disabled';
  is_simulation: boolean;
  last_update: string;
  error_message: string | null;
  details: Record<string, unknown>;
}

export interface HardwareStatus {
  initialized: boolean;
  simulation_mode: boolean;
  update_interval: number;
  running: boolean;
  controllers: Record<string, ControllerStatus>;
}

// Config Types
export interface AppConfig {
  app_name: string;
  app_version: string;
  debug: boolean;
  simulation_mode: boolean;
  hardware_update_interval: number;
  data_log_interval: number;
  data_retention_days: number;
  platform: {
    system: string;
    release: string;
    machine: string;
    is_raspberry_pi: boolean;
    simulation_mode: boolean;
  };
}
