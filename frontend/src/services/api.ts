/**
 * API Service (REST API 서비스)
 * ==============================
 *
 * [한국어 설명]
 * 백엔드 FastAPI 서버와의 REST API 통신을 담당합니다.
 * 모든 HTTP 요청은 이 파일의 함수들을 통해 이루어집니다.
 *
 * [REST API란?]
 * - Representational State Transfer
 * - HTTP 메서드(GET, POST, PUT, DELETE)로 리소스 조작
 * - 상태를 저장하지 않는(Stateless) 통신 방식
 *
 * [파일 구조]
 * 1. fetchApi: 공통 HTTP 요청 함수
 * 2. hardwareApi: 하드웨어 제어 API
 * 3. systemApi: 시스템 정보 API
 * 4. dataApi: 데이터/로그 조회 API
 * 5. wsApi: WebSocket 상태 API
 *
 * [Vite 프록시]
 * 개발 환경에서 '/api' 경로는 vite.config.ts에서 설정한
 * 프록시를 통해 백엔드 서버(localhost:8000)로 전달됨
 */

// ==================== 상수 정의 ====================
/**
 * [API_BASE]
 * API 엔드포인트의 기본 경로
 *
 * [왜 '/api'인가?]
 * - Vite 개발 서버가 이 경로를 백엔드로 프록시
 * - 프로덕션에서도 동일한 경로 사용 가능 (nginx 프록시 설정)
 * - CORS 문제 회피 (같은 origin으로 요청)
 */
const API_BASE = '/api';


// ==================== 커스텀 에러 클래스 ====================
/**
 * [ApiError 클래스]
 * API 요청 실패 시 발생하는 커스텀 에러
 *
 * [왜 커스텀 에러를 만드는가?]
 * - HTTP 상태 코드 포함 가능
 * - 에러 종류 구분 가능 (instanceof ApiError)
 * - 일관된 에러 처리 가능
 *
 * [클래스 상속]
 * extends Error: JavaScript 기본 Error 클래스 상속
 * super(message): 부모 클래스 생성자 호출
 */
class ApiError extends Error {
  /**
   * [생성자 매개변수 속성]
   * public status: number
   * - 이 문법은 매개변수를 클래스 속성으로 자동 선언
   * - this.status = status와 동일한 효과
   */
  constructor(public status: number, message: string) {
    // [super 호출]
    // 부모 클래스(Error)의 생성자 호출
    // message를 Error의 message 속성으로 설정
    super(message);

    // [에러 이름 설정]
    // 에러 출력 시 "ApiError: 메시지" 형태로 표시
    this.name = 'ApiError';
  }
}


// ==================== 공통 fetch 함수 ====================
/**
 * [fetchApi 함수]
 * 모든 API 요청에 사용되는 공통 함수
 *
 * [제네릭 함수]
 * fetchApi<T>: T는 응답 데이터의 타입
 * 호출 시 타입 지정: fetchApi<MyType>('/endpoint')
 * 반환 타입이 Promise<T>가 됨
 *
 * [async/await]
 * - async: 이 함수가 Promise를 반환함을 선언
 * - await: Promise가 완료될 때까지 대기
 *
 * @param endpoint - API 경로 (예: '/hardware/status')
 * @param options - fetch 옵션 (method, body, headers 등)
 * @returns Promise<T> - 파싱된 JSON 응답
 */
async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}  // RequestInit: fetch API의 옵션 타입
): Promise<T> {

  // [URL 조합]
  // API_BASE + endpoint = '/api' + '/hardware/status'
  const url = `${API_BASE}${endpoint}`;

  // ==================== fetch 요청 ====================
  /**
   * [fetch API]
   * 브라우저 내장 HTTP 요청 함수
   *
   * [옵션 병합]
   * ...options: 전달받은 옵션 복사
   * headers: 기본 헤더 + 전달받은 헤더 병합
   *
   * [Content-Type]
   * 'application/json': JSON 형식으로 데이터 전송
   * 서버가 요청 본문을 JSON으로 파싱하도록 알림
   */
  const response = await fetch(url, {
    ...options,  // method, body 등 복사
    headers: {
      'Content-Type': 'application/json',  // 기본 헤더
      ...options.headers,                   // 추가 헤더 (덮어쓰기 가능)
    },
  });

  // ==================== 에러 처리 ====================
  /**
   * [response.ok]
   * HTTP 상태 코드가 200-299 범위면 true
   * 그 외(4xx, 5xx)면 false
   */
  if (!response.ok) {
    // [에러 응답 파싱]
    // 서버가 보낸 에러 메시지 추출 시도
    // JSON 파싱 실패 시 빈 객체 반환 (.catch(() => ({})))
    const errorData = await response.json().catch(() => ({}));

    // [ApiError 생성 및 throw]
    // detail: FastAPI의 기본 에러 필드
    // message: 일반적인 에러 메시지 필드
    throw new ApiError(
      response.status,
      errorData.detail || errorData.message || 'API request failed'
    );
  }

  // ==================== 성공 응답 반환 ====================
  // JSON 파싱하여 반환
  // 타입 T로 자동 추론됨
  return response.json();
}


// ==================== Hardware API ====================
/**
 * [hardwareApi 객체]
 * 하드웨어 관련 API 엔드포인트 모음
 *
 * [객체 리터럴 패턴]
 * 관련 함수들을 하나의 객체로 그룹화
 * hardwareApi.getStatus(), hardwareApi.setLed() 형태로 사용
 */
export const hardwareApi = {

  // ==================== 상태 조회 ====================

  /**
   * [getStatus]
   * 전체 하드웨어 상태 조회
   * GET /api/hardware/status
   */
  getStatus: () => fetchApi<Record<string, unknown>>('/hardware/status'),

  /**
   * [getData]
   * 하드웨어 데이터 조회
   * GET /api/hardware/data
   *
   * [Record<string, unknown>]
   * TypeScript 유틸리티 타입
   * - 키: string, 값: unknown (any보다 안전)
   * - 정확한 타입을 모를 때 사용
   */
  getData: () => fetchApi<Record<string, unknown>>('/hardware/data'),

  // ==================== GPIO 제어 ====================

  /**
   * [getGpioStatus]
   * GPIO 상태 조회 (LED, 버튼, 릴레이)
   * GET /api/hardware/gpio
   */
  getGpioStatus: () => fetchApi<Record<string, unknown>>('/hardware/gpio'),

  /**
   * [setLed]
   * 개별 LED 제어
   * POST /api/hardware/gpio/led
   *
   * @param index - LED 인덱스 (0-3)
   * @param state - true: 켜기, false: 끄기
   *
   * [POST 요청]
   * method: 'POST' - 리소스 생성/수정
   * body: JSON.stringify() - 객체를 JSON 문자열로 변환
   */
  setLed: (index: number, state: boolean) =>
    fetchApi<{ success: boolean }>('/hardware/gpio/led', {
      method: 'POST',
      body: JSON.stringify({ index, state }),  // { index: index, state: state } 축약
    }),

  /**
   * [setAllLeds]
   * 모든 LED 일괄 제어
   * POST /api/hardware/gpio/led/all?state=true
   *
   * [쿼리 파라미터]
   * ?state=${state}: URL에 쿼리 스트링 추가
   * body 대신 URL 파라미터로 전달
   */
  setAllLeds: (state: boolean) =>
    fetchApi<{ success: boolean }>(`/hardware/gpio/led/all?state=${state}`, {
      method: 'POST',
    }),

  /**
   * [setRelay]
   * 릴레이 제어
   * POST /api/hardware/gpio/relay
   *
   * @param index - 릴레이 인덱스 (0-1)
   * @param state - true: 켜기, false: 끄기
   */
  setRelay: (index: number, state: boolean) =>
    fetchApi<{ success: boolean }>('/hardware/gpio/relay', {
      method: 'POST',
      body: JSON.stringify({ index, state }),
    }),

  // ==================== PWM 제어 ====================

  /**
   * [getPwmStatus]
   * PWM 상태 조회 (모터, 서보)
   * GET /api/hardware/pwm
   */
  getPwmStatus: () => fetchApi<Record<string, unknown>>('/hardware/pwm'),

  /**
   * [setMotorSpeed]
   * DC 모터 속도 설정
   * POST /api/hardware/pwm/motor
   *
   * @param speed - 속도 (0-100%)
   */
  setMotorSpeed: (speed: number) =>
    fetchApi<{ success: boolean }>('/hardware/pwm/motor', {
      method: 'POST',
      body: JSON.stringify({ speed }),
    }),

  /**
   * [setServoAngle]
   * 서보 모터 각도 설정
   * POST /api/hardware/pwm/servo
   *
   * @param angle - 각도 (0-180°)
   */
  setServoAngle: (angle: number) =>
    fetchApi<{ success: boolean }>('/hardware/pwm/servo', {
      method: 'POST',
      body: JSON.stringify({ angle }),
    }),

  // ==================== 센서 조회 ====================

  /**
   * [getSensors]
   * 모든 센서 데이터 조회
   * GET /api/hardware/sensors
   */
  getSensors: () => fetchApi<Record<string, unknown>>('/hardware/sensors'),

  /**
   * [getDht]
   * DHT22 센서 데이터 조회 (온도, 습도)
   * GET /api/hardware/sensors/dht
   *
   * [반환 타입 명시]
   * { temperature: number; humidity: number }
   * 정확한 응답 구조를 알 때 타입 지정
   */
  getDht: () => fetchApi<{ temperature: number; humidity: number }>('/hardware/sensors/dht'),

  /**
   * [getDistance]
   * HC-SR04 초음파 센서 거리 측정
   * GET /api/hardware/sensors/distance
   */
  getDistance: () => fetchApi<{ distance: number }>('/hardware/sensors/distance'),

  // ==================== I2C 장치 ====================

  /**
   * [getI2cDevices]
   * 연결된 I2C 장치 정보 조회
   * GET /api/hardware/i2c/devices
   */
  getI2cDevices: () => fetchApi<Record<string, unknown>>('/hardware/i2c/devices'),

  /**
   * [scanI2c]
   * I2C 버스 스캔 (연결된 장치 주소 목록)
   * GET /api/hardware/i2c/scan
   *
   * [반환: number[]]
   * I2C 주소 배열 (예: [0x27, 0x3C, 0x76])
   */
  scanI2c: () => fetchApi<number[]>('/hardware/i2c/scan'),

  /**
   * [getBmp280]
   * BMP280 센서 데이터 (온도, 기압)
   * GET /api/hardware/i2c/bmp280
   */
  getBmp280: () => fetchApi<Record<string, number>>('/hardware/i2c/bmp280'),

  /**
   * [getAdc]
   * ADC(아날로그-디지털 변환기) 값 조회
   * GET /api/hardware/i2c/adc
   *
   * [Record<number, number>]
   * 채널 번호 → 아날로그 값 매핑
   * { 0: 1234, 1: 2345, 2: 3456, 3: 4567 }
   */
  getAdc: () => fetchApi<Record<number, number>>('/hardware/i2c/adc'),

  // ==================== SPI 장치 ====================

  /**
   * [getMcp3008]
   * MCP3008 ADC 값 조회 (SPI 인터페이스)
   * GET /api/hardware/spi/mcp3008
   */
  getMcp3008: () => fetchApi<Record<number, number>>('/hardware/spi/mcp3008'),

  // ==================== 디스플레이 ====================

  /**
   * [getLcdInfo]
   * LCD 상태 정보 조회
   * GET /api/hardware/display/lcd
   */
  getLcdInfo: () => fetchApi<Record<string, unknown>>('/hardware/display/lcd'),

  /**
   * [writeLcd]
   * LCD에 텍스트 출력
   * POST /api/hardware/display/lcd/write
   *
   * @param text - 출력할 텍스트
   * @param row - 행 위치 (기본값: 0)
   * @param col - 열 위치 (기본값: 0)
   *
   * [기본값 매개변수]
   * row: number = 0
   * 값을 전달하지 않으면 0 사용
   */
  writeLcd: (text: string, row: number = 0, col: number = 0) =>
    fetchApi<{ success: boolean }>('/hardware/display/lcd/write', {
      method: 'POST',
      body: JSON.stringify({ text, row, col }),
    }),

  /**
   * [clearLcd]
   * LCD 화면 지우기
   * POST /api/hardware/display/lcd/clear
   */
  clearLcd: () =>
    fetchApi<{ success: boolean }>('/hardware/display/lcd/clear', {
      method: 'POST',
    }),

  // ==================== NeoPixel LED ====================

  /**
   * [getNeopixelStatus]
   * NeoPixel LED 상태 조회
   * GET /api/hardware/neopixel
   */
  getNeopixelStatus: () => fetchApi<Record<string, unknown>>('/hardware/neopixel'),

  /**
   * [setNeopixelColor]
   * NeoPixel LED 색상 설정
   * POST /api/hardware/neopixel/color
   *
   * @param index - LED 인덱스 (null이면 전체)
   * @param color - 색상 문자열 (예: "#FF0000", "red")
   *
   * [number | null]
   * 유니온 타입: 숫자 또는 null 허용
   */
  setNeopixelColor: (index: number | null, color: string) =>
    fetchApi<{ success: boolean }>('/hardware/neopixel/color', {
      method: 'POST',
      body: JSON.stringify({ index, color }),
    }),

  /**
   * [startNeopixelEffect]
   * NeoPixel 효과 시작
   * POST /api/hardware/neopixel/effect
   *
   * @param effect - 효과 이름 ('rainbow', 'chase', 'breathing' 등)
   * @param speed - 효과 속도 (기본값: 0.05)
   */
  startNeopixelEffect: (effect: string, speed: number = 0.05) =>
    fetchApi<{ success: boolean }>('/hardware/neopixel/effect', {
      method: 'POST',
      body: JSON.stringify({ effect, speed }),
    }),

  /**
   * [stopNeopixelEffect]
   * NeoPixel 효과 중지
   * POST /api/hardware/neopixel/stop
   */
  stopNeopixelEffect: () =>
    fetchApi<{ success: boolean }>('/hardware/neopixel/stop', {
      method: 'POST',
    }),

  /**
   * [clearNeopixel]
   * NeoPixel LED 끄기 (모든 LED 검정색)
   * POST /api/hardware/neopixel/clear
   */
  clearNeopixel: () =>
    fetchApi<{ success: boolean }>('/hardware/neopixel/clear', {
      method: 'POST',
    }),

  // ==================== 시뮬레이션 ====================

  /**
   * [setSimulationValues]
   * 시뮬레이션 값 수동 설정
   * POST /api/hardware/simulation/values
   *
   * @param values - 설정할 값들 (예: { temperature: 25.5, humidity: 60 })
   *
   * [시뮬레이션 모드]
   * 실제 하드웨어 없이 테스트할 때 센서 값을 임의로 설정
   */
  setSimulationValues: (values: Record<string, unknown>) =>
    fetchApi<{ success: boolean }>('/hardware/simulation/values', {
      method: 'POST',
      body: JSON.stringify(values),
    }),

  /**
   * [simulateButtonPress]
   * 버튼 누름 시뮬레이션
   * POST /api/hardware/simulation/button/{index}
   *
   * @param index - 버튼 인덱스
   *
   * [URL 경로 매개변수]
   * `/button/${index}`: URL에 직접 값 삽입
   */
  simulateButtonPress: (index: number) =>
    fetchApi<{ success: boolean }>(`/hardware/simulation/button/${index}`, {
      method: 'POST',
    }),
};


// ==================== System API ====================
/**
 * [systemApi 객체]
 * 시스템 정보 관련 API 엔드포인트 모음
 */
export const systemApi = {

  /**
   * [getMetrics]
   * 시스템 메트릭 조회 (CPU, 메모리, 디스크)
   * GET /api/system/metrics
   */
  getMetrics: () => fetchApi<Record<string, unknown>>('/system/metrics'),

  /**
   * [getSummary]
   * 시스템 요약 정보
   * GET /api/system/summary
   */
  getSummary: () => fetchApi<Record<string, unknown>>('/system/summary'),

  /**
   * [getHealth]
   * 시스템 헬스 체크
   * GET /api/system/health
   *
   * [헬스 체크 용도]
   * - 서버 상태 확인
   * - 로드밸런서 헬스 체크
   * - 모니터링 시스템 연동
   */
  getHealth: () => fetchApi<Record<string, unknown>>('/system/health'),

  /**
   * [getPlatform]
   * 플랫폼 정보 (OS, 아키텍처 등)
   * GET /api/system/platform
   */
  getPlatform: () => fetchApi<Record<string, unknown>>('/system/platform'),

  /**
   * [getProcess]
   * 현재 프로세스 정보
   * GET /api/system/process
   */
  getProcess: () => fetchApi<Record<string, unknown>>('/system/process'),

  /**
   * [getConfig]
   * 애플리케이션 설정 조회
   * GET /api/system/config
   *
   * [App.tsx에서 사용]
   * 앱 시작 시 서버 설정을 가져와 Zustand에 저장
   */
  getConfig: () => fetchApi<Record<string, unknown>>('/system/config'),
};


// ==================== Data API ====================
/**
 * [dataApi 객체]
 * 데이터 조회 및 관리 API 엔드포인트 모음
 *
 * [용도]
 * - 센서 데이터 히스토리 조회
 * - 시스템 로그 조회
 * - 장치 상태 이력 조회
 * - 통계 데이터 조회
 */
export const dataApi = {

  /**
   * [getSensorHistory]
   * 센서 데이터 이력 조회
   * GET /api/data/sensors?sensor_type=all&hours=24&limit=1000
   *
   * @param sensorType - 센서 종류 ('temperature', 'humidity', 'all')
   * @param hours - 조회 기간 (시간)
   * @param limit - 최대 레코드 수
   *
   * [쿼리 스트링 조합]
   * `?param1=${value1}&param2=${value2}`
   * URL에 여러 매개변수 추가
   */
  getSensorHistory: (sensorType: string = 'all', hours: number = 24, limit: number = 1000) =>
    fetchApi<Record<string, unknown>[]>(
      `/data/sensors?sensor_type=${sensorType}&hours=${hours}&limit=${limit}`
    ),

  /**
   * [getTemperatureTrend]
   * 온도 트렌드 데이터 조회
   * GET /api/data/temperature?hours=24
   *
   * [반환 타입]
   * Array<{ timestamp: string; value: number }>
   * 차트에 직접 사용 가능한 형식
   */
  getTemperatureTrend: (hours: number = 24) =>
    fetchApi<Array<{ timestamp: string; value: number }>>(
      `/data/temperature?hours=${hours}`
    ),

  /**
   * [getSystemLogs]
   * 시스템 로그 조회
   * GET /api/data/logs?hours=24&limit=100&level=warning
   *
   * @param level - 로그 레벨 필터 (선택, 'info', 'warning', 'error')
   * @param hours - 조회 기간
   * @param limit - 최대 레코드 수
   *
   * [조건부 쿼리 파라미터]
   * level이 있을 때만 &level= 추가
   */
  getSystemLogs: (level?: string, hours: number = 24, limit: number = 100) => {
    // [동적 URL 구성]
    let url = `/data/logs?hours=${hours}&limit=${limit}`;
    if (level) url += `&level=${level}`;  // level이 있으면 추가
    return fetchApi<Record<string, unknown>[]>(url);
  },

  /**
   * [getDeviceHistory]
   * 장치 상태 이력 조회
   * GET /api/data/devices?hours=24&device_type=led&device_id=0
   *
   * @param deviceType - 장치 종류 (선택, 'led', 'relay' 등)
   * @param deviceId - 장치 ID (선택)
   * @param hours - 조회 기간
   */
  getDeviceHistory: (deviceType?: string, deviceId?: string, hours: number = 24) => {
    let url = `/data/devices?hours=${hours}`;
    if (deviceType) url += `&device_type=${deviceType}`;
    if (deviceId) url += `&device_id=${deviceId}`;
    return fetchApi<Record<string, unknown>[]>(url);
  },

  /**
   * [getStatistics]
   * 통계 데이터 조회
   * GET /api/data/statistics?hours=24
   *
   * [통계 내용]
   * - 센서별 최소/최대/평균 값
   * - 데이터 수집 횟수
   * - 이벤트 발생 빈도 등
   */
  getStatistics: (hours: number = 24) =>
    fetchApi<Record<string, unknown>>(`/data/statistics?hours=${hours}`),

  /**
   * [cleanupData]
   * 오래된 데이터 정리
   * POST /api/data/cleanup?retention_days=30
   *
   * @param retentionDays - 보존 기간 (일 단위)
   *
   * [반환값]
   * { success: boolean, deleted_records: number }
   * 삭제된 레코드 수 반환
   */
  cleanupData: (retentionDays: number = 30) =>
    fetchApi<{ success: boolean; deleted_records: number }>(
      `/data/cleanup?retention_days=${retentionDays}`,
      { method: 'POST' }
    ),
};


// ==================== WebSocket API ====================
/**
 * [wsApi 객체]
 * WebSocket 관련 REST API 엔드포인트
 *
 * [참고]
 * 실제 WebSocket 연결은 websocket.ts에서 처리
 * 이 API는 WebSocket 상태 조회에만 사용
 */
export const wsApi = {

  /**
   * [getStatus]
   * WebSocket 서비스 상태 조회
   * GET /api/ws/status
   */
  getStatus: () => fetchApi<Record<string, unknown>>('/ws/status'),

  /**
   * [getClients]
   * 연결된 WebSocket 클라이언트 목록
   * GET /api/ws/clients
   *
   * [관리/모니터링 용도]
   * 현재 연결된 클라이언트 수와 정보 확인
   */
  getClients: () => fetchApi<Record<string, unknown>>('/ws/clients'),
};


// ==================== 내보내기 ====================
/**
 * [Named Export]
 * export { ApiError }
 *
 * [사용 예시]
 * import { ApiError } from './api';
 *
 * try {
 *   await hardwareApi.setLed(0, true);
 * } catch (error) {
 *   if (error instanceof ApiError) {
 *     console.log('HTTP 상태:', error.status);
 *     console.log('에러 메시지:', error.message);
 *   }
 * }
 */
export { ApiError };
