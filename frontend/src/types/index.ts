/**
 * Type Definitions for HMI Application
 * (HMI 애플리케이션 타입 정의)
 * ======================================
 *
 * [한국어 설명]
 * 애플리케이션 전체에서 사용되는 TypeScript 타입/인터페이스를 정의합니다.
 * 타입 안전성을 보장하고 IDE 자동완성 기능을 활용할 수 있게 합니다.
 *
 * [핵심 개념]
 * 1. TypeScript Interface:
 *    - 객체의 형태(shape)를 정의
 *    - 런타임에는 존재하지 않음 (컴파일 시 제거)
 *    - 확장(extends) 가능
 *
 * 2. 타입 내보내기:
 *    - export interface로 다른 파일에서 사용 가능
 *    - import { TypeName } from './types'로 가져옴
 *
 * 3. 제네릭 (Generic):
 *    - <T>로 타입 매개변수 정의
 *    - 유연한 타입 재사용 가능
 *
 * 4. Union 타입:
 *    - |로 여러 타입 중 하나
 *    - 예: number | null = 숫자 또는 null
 *
 * [파일 구조]
 * - Hardware Data Types: GPIO, PWM, 센서 데이터
 * - System Metrics Types: CPU, 메모리, 디스크 정보
 * - WebSocket Types: 실시간 통신 메시지
 * - API Types: REST API 응답 형식
 * - Chart Types: 차트 데이터 형식
 */

// ==============================================================================
// 하드웨어 데이터 타입 (Hardware Data Types)
// ==============================================================================

/**
 * [GPIOState 인터페이스]
 * GPIO 핀 상태를 정의합니다.
 *
 * [Record<K, V> 타입]
 * 키 타입 K, 값 타입 V인 객체 타입
 * Record<number, boolean> = { 0: true, 1: false, 2: true, ... }
 *
 * [사용 예시]
 * const gpio: GPIOState = {
 *   leds: { 0: true, 1: false, 2: true, 3: false },
 *   buttons: { 0: false, 1: true },
 *   relays: { 0: true, 1: false }
 * };
 */
export interface GPIOState {
  // LED 상태: 핀 번호(인덱스) -> on/off 상태
  leds: Record<number, boolean>;

  // 버튼 상태: 핀 번호 -> 눌림/안눌림 상태
  buttons: Record<number, boolean>;

  // 릴레이 상태: 핀 번호 -> on/off 상태
  relays: Record<number, boolean>;
}

/**
 * [PWMState 인터페이스]
 * PWM(Pulse Width Modulation) 출력 상태를 정의합니다.
 *
 * [PWM이란?]
 * 디지털 신호로 아날로그 효과를 만드는 기술
 * 듀티 사이클(duty cycle)로 평균 전압 조절
 */
export interface PWMState {
  // 모터 속도: 0-100 (%)
  motor_speed: number;

  // 서보 각도: 0-180 (도)
  servo_angle: number;
}

/**
 * [SensorData 인터페이스]
 * 다양한 센서의 측정값을 정의합니다.
 *
 * [number | null]
 * 숫자 또는 null (센서가 없거나 읽기 실패 시 null)
 */
export interface SensorData {
  // 온도 (섭씨) - DHT22, BMP280
  temperature: number | null;

  // 습도 (%) - DHT22
  humidity: number | null;

  // 기압 (hPa) - BMP280
  pressure: number | null;

  // 고도 (미터) - BMP280에서 기압으로 계산
  altitude: number | null;

  // 거리 (센티미터) - HC-SR04 초음파 센서
  distance: number | null;

  // 움직임 감지 - PIR 센서
  motion: boolean;

  // 조도 (0-1023) - 광센서/ADC
  light_level: number | null;

  // 토양 습도 (0-1023) - 토양 센서/ADC
  soil_moisture: number | null;
}

/**
 * [ADCData 인터페이스]
 * ADC(Analog-to-Digital Converter) 데이터를 정의합니다.
 */
export interface ADCData {
  // I2C ADC (ADS1115): 채널 번호 -> 값
  i2c: Record<number, number>;

  // SPI ADC (MCP3008): 채널 번호 -> 값
  spi: Record<number, number>;
}

/**
 * [NeopixelLED 인터페이스]
 * WS2812B NeoPixel LED의 개별 LED 상태를 정의합니다.
 *
 * [[number, number, number]]
 * 튜플 타입: 정확히 3개의 숫자를 가진 배열
 */
export interface NeopixelLED {
  // LED 인덱스 (0부터 시작)
  index: number;

  // 16진수 색상 코드 (예: "#FF0000")
  color: string;

  // RGB 값 튜플 [Red, Green, Blue] (각 0-255)
  rgb: [number, number, number];
}

/**
 * [HardwareData 인터페이스]
 * 전체 하드웨어 상태를 포함하는 통합 인터페이스입니다.
 * WebSocket으로 수신되는 하드웨어 업데이트 데이터 형식입니다.
 */
export interface HardwareData {
  // ISO 8601 형식 타임스탬프
  timestamp: string;

  // GPIO 상태 (LED, 버튼, 릴레이)
  gpio: GPIOState;

  // PWM 상태 (모터, 서보)
  pwm: PWMState;

  // 센서 데이터
  sensors: SensorData;

  // ADC 데이터 (I2C, SPI)
  adc: ADCData;

  // 디스플레이 상태
  display: {
    // LCD 표시 내용 (줄 단위)
    lcd_content: string[];
  };

  // NeoPixel LED 상태
  neopixel: {
    // 각 LED의 색상 정보
    colors: NeopixelLED[];
  };
}


// ==============================================================================
// 시스템 메트릭 타입 (System Metrics Types)
// ==============================================================================

/**
 * [CPUMetrics 인터페이스]
 * CPU 정보를 정의합니다.
 */
export interface CPUMetrics {
  // CPU 사용률 (%)
  percent: number;

  // 논리 코어 수
  count: number;

  // CPU 주파수 정보
  frequency: {
    current: number;  // 현재 주파수 (MHz)
    max: number;      // 최대 주파수 (MHz)
  };

  // CPU 온도 (섭씨) - 가용 시에만
  temperature: number | null;
}

/**
 * [MemoryMetrics 인터페이스]
 * 메모리(RAM) 정보를 정의합니다.
 */
export interface MemoryMetrics {
  // 전체 메모리 (바이트)
  total: number;

  // 가용 메모리 (바이트)
  available: number;

  // 사용 중인 메모리 (바이트)
  used: number;

  // 메모리 사용률 (%)
  percent: number;

  // 전체 메모리 (GB) - 표시용
  total_gb: number;

  // 사용 중인 메모리 (GB) - 표시용
  used_gb: number;
}

/**
 * [DiskMetrics 인터페이스]
 * 디스크 정보를 정의합니다.
 */
export interface DiskMetrics {
  // 전체 공간 (바이트)
  total: number;

  // 사용 중인 공간 (바이트)
  used: number;

  // 남은 공간 (바이트)
  free: number;

  // 사용률 (%)
  percent: number;

  // 전체 공간 (GB) - 표시용
  total_gb: number;

  // 남은 공간 (GB) - 표시용
  free_gb: number;
}

/**
 * [NetworkMetrics 인터페이스]
 * 네트워크 I/O 정보를 정의합니다.
 */
export interface NetworkMetrics {
  // 총 송신 바이트
  bytes_sent: number;

  // 총 수신 바이트
  bytes_recv: number;

  // 송신량 (MB) - 표시용
  sent_mb: number;

  // 수신량 (MB) - 표시용
  recv_mb: number;
}

/**
 * [SystemInfo 인터페이스]
 * 시스템 기본 정보를 정의합니다.
 */
export interface SystemInfo {
  // 부팅 시간 (ISO 8601)
  boot_time: string;

  // 가동 시간 (초)
  uptime_seconds: number;

  // 가동 시간 (시간) - 표시용
  uptime_hours: number;
}

/**
 * [SystemMetrics 인터페이스]
 * 전체 시스템 메트릭을 포함하는 통합 인터페이스입니다.
 * WebSocket으로 수신되는 시스템 업데이트 데이터 형식입니다.
 */
export interface SystemMetrics {
  // 측정 시간
  timestamp: string;

  // CPU 정보
  cpu: CPUMetrics;

  // 메모리 정보
  memory: MemoryMetrics;

  // 디스크 정보
  disk: DiskMetrics;

  // 네트워크 정보
  network: NetworkMetrics;

  // 시스템 정보
  system: SystemInfo;
}


// ==============================================================================
// WebSocket 메시지 타입 (WebSocket Message Types)
// ==============================================================================

/**
 * [WebSocketMessage 인터페이스]
 * WebSocket 메시지의 기본 형태를 정의합니다.
 *
 * [unknown 타입]
 * any보다 안전한 "알 수 없는 타입"
 * 사용 전에 타입 검사 필요
 */
export interface WebSocketMessage {
  // 메시지 타입 (예: "hardware_update", "connected")
  type: string;

  // 메시지 토픽 (선택적)
  topic?: string;

  // 구독 토픽 목록 (선택적)
  topics?: string[];

  // 메시지 데이터 (선택적, 타입 불명)
  data?: unknown;

  // 메시지 생성 시간 (선택적)
  timestamp?: string;

  // 클라이언트 ID (선택적)
  client_id?: string;

  // 브로드캐스트 시간 (선택적)
  broadcast_time?: string;
}

/**
 * [HardwareUpdateMessage 인터페이스]
 * 하드웨어 업데이트 메시지 타입입니다.
 *
 * [extends 키워드]
 * 기본 인터페이스를 확장하여 새 인터페이스 정의
 * WebSocketMessage의 모든 속성 + 추가 속성
 */
export interface HardwareUpdateMessage extends WebSocketMessage {
  // 타입 리터럴: 정확히 'hardware_update' 문자열만 허용
  type: 'hardware_update';

  // 데이터는 HardwareData 타입
  data: HardwareData;
}

/**
 * [SystemUpdateMessage 인터페이스]
 * 시스템 메트릭 업데이트 메시지 타입입니다.
 */
export interface SystemUpdateMessage extends WebSocketMessage {
  type: 'system_update';
  data: SystemMetrics;
}


// ==============================================================================
// API 응답 타입 (API Response Types)
// ==============================================================================

/**
 * [ApiResponse<T> 인터페이스]
 * REST API 응답의 표준 형식입니다.
 *
 * [제네릭 <T>]
 * 타입 매개변수: 사용 시 구체적인 타입으로 대체
 * 예: ApiResponse<User> -> data?: User
 *
 * [사용 예시]
 * const response: ApiResponse<SensorData> = await api.getSensors();
 * if (response.success && response.data) {
 *   console.log(response.data.temperature);
 * }
 */
export interface ApiResponse<T> {
  // 성공 여부
  success: boolean;

  // 응답 데이터 (성공 시)
  data?: T;

  // 에러 메시지 (실패 시)
  error?: string;

  // 일반 메시지
  message?: string;
}

/**
 * [HealthStatus 인터페이스]
 * 시스템 건강 상태 정보입니다.
 *
 * [리터럴 Union 타입]
 * 특정 문자열 값만 허용
 * 'healthy' | 'warning' | 'critical' | 'unknown' 중 하나
 */
export interface HealthStatus {
  // 상태: 정상, 경고, 위험, 알 수 없음
  status: 'healthy' | 'warning' | 'critical' | 'unknown';

  // 경고 메시지 목록
  warnings: string[];

  // 확인 시간
  timestamp: string;
}

/**
 * [SystemSummary 인터페이스]
 * 시스템 요약 정보입니다.
 * 대시보드에 표시할 핵심 지표입니다.
 */
export interface SystemSummary {
  // CPU 사용률 (%)
  cpu_percent: number;

  // CPU 온도 (섭씨)
  cpu_temp: number | null;

  // 메모리 사용률 (%)
  memory_percent: number;

  // 디스크 사용률 (%)
  disk_percent: number;

  // 가동 시간 (시간)
  uptime_hours: number;

  // 건강 상태
  health_status: string;

  // 경고 목록
  warnings: string[];
}


// ==============================================================================
// 차트 데이터 타입 (Chart Data Types)
// ==============================================================================

/**
 * [ChartDataPoint 인터페이스]
 * 차트의 개별 데이터 포인트입니다.
 * 시계열 차트에서 사용됩니다.
 */
export interface ChartDataPoint {
  // X축: 시간
  timestamp: string;

  // Y축: 값
  value: number;
}

/**
 * [SensorHistoryItem 인터페이스]
 * 센서 데이터 히스토리 항목입니다.
 * DB에서 조회한 센서 데이터 레코드 형식입니다.
 */
export interface SensorHistoryItem {
  // 레코드 ID
  id: number;

  // 측정 시간
  timestamp: string;

  // 센서 타입
  sensor_type: string;

  // 각 센서 값 (해당 센서만 값 있음)
  temperature: number | null;
  humidity: number | null;
  pressure: number | null;
  altitude: number | null;
  distance: number | null;
  light_level: number | null;
  soil_moisture: number | null;
  motion: boolean | null;
}


// ==============================================================================
// 하드웨어 컨트롤러 상태 타입 (Hardware Controller Status Types)
// ==============================================================================

/**
 * [ControllerStatus 인터페이스]
 * 개별 하드웨어 컨트롤러의 상태입니다.
 */
export interface ControllerStatus {
  // 컨트롤러 이름
  name: string;

  // 상태: 미초기화, 초기화중, 준비됨, 에러, 비활성화
  state: 'uninitialized' | 'initializing' | 'ready' | 'error' | 'disabled';

  // 시뮬레이션 모드 여부
  is_simulation: boolean;

  // 마지막 업데이트 시간
  last_update: string;

  // 에러 메시지 (에러 상태 시)
  error_message: string | null;

  // 추가 상세 정보
  details: Record<string, unknown>;
}

/**
 * [HardwareStatus 인터페이스]
 * 전체 하드웨어 시스템 상태입니다.
 */
export interface HardwareStatus {
  // 초기화 완료 여부
  initialized: boolean;

  // 시뮬레이션 모드 여부
  simulation_mode: boolean;

  // 업데이트 간격 (초)
  update_interval: number;

  // 실행 중 여부
  running: boolean;

  // 각 컨트롤러 상태
  // 키: 컨트롤러 이름 (예: "gpio", "pwm", "sensor")
  controllers: Record<string, ControllerStatus>;
}


// ==============================================================================
// 설정 타입 (Config Types)
// ==============================================================================

/**
 * [AppConfig 인터페이스]
 * 애플리케이션 설정입니다.
 * 서버에서 가져오는 설정 정보입니다.
 */
export interface AppConfig {
  // 앱 이름
  app_name: string;

  // 앱 버전
  app_version: string;

  // 디버그 모드
  debug: boolean;

  // 시뮬레이션 모드
  simulation_mode: boolean;

  // 하드웨어 업데이트 간격 (초)
  hardware_update_interval: number;

  // 데이터 로깅 간격 (초)
  data_log_interval: number;

  // 데이터 보관 기간 (일)
  data_retention_days: number;

  // 플랫폼 정보
  platform: {
    // OS 이름
    system: string;

    // OS 버전
    release: string;

    // 아키텍처
    machine: string;

    // Raspberry Pi 여부
    is_raspberry_pi: boolean;

    // 시뮬레이션 모드
    simulation_mode: boolean;
  };
}
