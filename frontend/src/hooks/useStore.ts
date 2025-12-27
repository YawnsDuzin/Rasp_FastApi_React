/**
 * Global State Store using Zustand (Zustand 전역 상태 스토어)
 * ==========================================================
 *
 * [한국어 설명]
 * Zustand를 사용한 전역 상태 관리 스토어입니다.
 * 애플리케이션 전체에서 공유되는 데이터를 관리합니다.
 *
 * [Zustand란?]
 * - 가볍고 빠른 React 상태 관리 라이브러리
 * - Redux보다 간단하고 보일러플레이트 코드가 적음
 * - Hook 기반으로 사용이 쉬움
 * - 불필요한 리렌더링 최소화
 *
 * [Redux vs Zustand]
 * - Redux: 액션, 리듀서, 스토어 등 많은 코드 필요
 * - Zustand: create() 함수 하나로 간단하게 스토어 생성
 *
 * [사용 예시]
 * const { hardwareData, setHardwareData } = useStore();
 * // hardwareData로 현재 상태 읽기
 * // setHardwareData()로 상태 업데이트
 */

// ==================== Imports ====================

// [Zustand create 함수]
// 스토어를 생성하는 팩토리 함수
// create<StateType>((set, get) => ({ ...initialState, ...actions }))
import { create } from 'zustand';

// [타입 정의 import]
// TypeScript 인터페이스들 - 데이터 구조 정의
import { HardwareData, SystemMetrics, AppConfig } from '../types';


// ==================== 상태 인터페이스 정의 ====================
/**
 * [StoreState 인터페이스]
 * 스토어에 저장되는 모든 상태와 액션의 타입 정의
 *
 * [인터페이스 구조]
 * - 상태 (state): 실제 데이터 값
 * - 액션 (actions): 상태를 변경하는 함수들
 *
 * [명명 규칙]
 * - 상태: 명사형 (isConnected, hardwareData)
 * - 액션: 동사형, set/toggle/add 접두사 (setConnected, toggleDarkMode)
 */
interface StoreState {
  // ==================== 연결 상태 ====================
  // [isConnected]
  // WebSocket 연결 여부를 나타내는 boolean 값
  // true: 서버와 연결됨, false: 연결 끊김
  isConnected: boolean;

  // [setConnected]
  // 연결 상태를 업데이트하는 액션 함수
  // 매개변수: connected (boolean) - 새로운 연결 상태
  setConnected: (connected: boolean) => void;

  // ==================== 하드웨어 데이터 ====================
  // [hardwareData]
  // GPIO, PWM, 센서 등 하드웨어 상태 데이터
  // null: 아직 데이터를 받지 않음
  // HardwareData: 서버에서 받은 최신 하드웨어 상태
  hardwareData: HardwareData | null;

  // [setHardwareData]
  // 하드웨어 데이터 업데이트 및 히스토리 기록
  setHardwareData: (data: HardwareData) => void;

  // ==================== 시스템 메트릭 ====================
  // [systemMetrics]
  // CPU, 메모리, 디스크 사용량 등 시스템 정보
  systemMetrics: SystemMetrics | null;

  // [setSystemMetrics]
  // 시스템 메트릭 업데이트
  setSystemMetrics: (metrics: SystemMetrics) => void;

  // ==================== 앱 설정 ====================
  // [config]
  // 서버에서 받아온 애플리케이션 설정
  // 시뮬레이션 모드, 업데이트 간격 등
  config: AppConfig | null;

  // [setConfig]
  // 설정 데이터 업데이트
  setConfig: (config: AppConfig) => void;

  // ==================== UI 상태 ====================
  // [darkMode]
  // 다크 모드 활성화 여부
  // true: 다크 테마, false: 라이트 테마
  darkMode: boolean;

  // [toggleDarkMode]
  // 다크/라이트 모드 전환
  // 현재 상태의 반대로 토글
  toggleDarkMode: () => void;

  // ==================== 사이드바 상태 ====================
  // [sidebarOpen]
  // 사이드바 열림/닫힘 상태
  // true: 사이드바 펼쳐짐, false: 접힘
  sidebarOpen: boolean;

  // [toggleSidebar]
  // 사이드바 열기/닫기 토글
  toggleSidebar: () => void;

  // ==================== 현재 페이지 ====================
  // [activePage]
  // 현재 활성화된 페이지 이름
  // 'dashboard' | 'hardware' | 'sensors' | 'system' | 'logs' | 'settings'
  activePage: string;

  // [setActivePage]
  // 페이지 전환 (네비게이션)
  setActivePage: (page: string) => void;

  // ==================== 온도 히스토리 (차트용) ====================
  // [temperatureHistory]
  // 온도 데이터 배열 (시계열 차트에 사용)
  // { time: "14:30:25", value: 25.5 } 형태의 객체 배열
  temperatureHistory: Array<{ time: string; value: number }>;

  // [addTemperaturePoint]
  // 온도 데이터 포인트 추가
  // 최대 60개 유지 (오래된 데이터는 자동 삭제)
  addTemperaturePoint: (value: number) => void;

  // ==================== 습도 히스토리 (차트용) ====================
  // [humidityHistory]
  // 습도 데이터 배열 (시계열 차트에 사용)
  humidityHistory: Array<{ time: string; value: number }>;

  // [addHumidityPoint]
  // 습도 데이터 포인트 추가
  addHumidityPoint: (value: number) => void;

  // ==================== 알림/경고 ====================
  // [alerts]
  // 시스템 알림 목록
  // { id: 유니크ID, type: 'warning'|'error'|'info', message: 메시지, timestamp: 시간 }
  alerts: Array<{ id: string; type: string; message: string; timestamp: Date }>;

  // [addAlert]
  // 새 알림 추가
  addAlert: (type: string, message: string) => void;

  // [removeAlert]
  // 특정 알림 제거 (ID로 식별)
  removeAlert: (id: string) => void;

  // [clearAlerts]
  // 모든 알림 삭제
  clearAlerts: () => void;
}


// ==================== 상수 정의 ====================
/**
 * [MAX_HISTORY_POINTS]
 * 차트에 표시할 최대 데이터 포인트 수
 * 60개 = 약 1분 (1초당 1포인트 기준)
 *
 * [왜 제한하는가?]
 * - 메모리 사용량 관리
 * - 차트 렌더링 성능 유지
 * - 가독성 (너무 많은 데이터는 차트를 읽기 어렵게 함)
 */
const MAX_HISTORY_POINTS = 60; // Keep 60 data points


// ==================== Zustand 스토어 생성 ====================
/**
 * [useStore Hook]
 * Zustand로 생성된 커스텀 훅
 *
 * [create 함수 구조]
 * create<StateType>((set, get) => ({
 *   // 초기 상태값
 *   myState: initialValue,
 *
 *   // 액션 함수
 *   setMyState: (newValue) => set({ myState: newValue }),
 * }))
 *
 * [set 함수]
 * 상태를 업데이트하는 함수
 * - set({ key: value }): 특정 키만 업데이트
 * - set((state) => ({ key: state.key + 1 })): 이전 상태 기반 업데이트
 *
 * [get 함수]
 * 현재 상태를 읽는 함수
 * - get().myState: 현재 myState 값 읽기
 * - 액션 내에서 다른 상태나 액션에 접근할 때 사용
 *
 * [사용 예시]
 * // 컴포넌트에서
 * const { hardwareData, setHardwareData } = useStore();
 *
 * // 특정 상태만 구독 (성능 최적화)
 * const hardwareData = useStore((state) => state.hardwareData);
 */
export const useStore = create<StoreState>((set, get) => ({
  // ==================== 연결 상태 초기값 및 액션 ====================

  // [초기값]
  // 시작 시 연결되어 있지 않으므로 false
  isConnected: false,

  // [setConnected 액션]
  // 간단한 상태 업데이트
  // set()에 객체를 전달하면 해당 키만 업데이트됨 (불변성 유지)
  setConnected: (connected) => set({ isConnected: connected }),

  // ==================== 하드웨어 데이터 초기값 및 액션 ====================

  // [초기값]
  // 아직 데이터를 받지 않았으므로 null
  hardwareData: null,

  // [setHardwareData 액션]
  // 하드웨어 데이터 업데이트 + 센서 히스토리 자동 추가
  setHardwareData: (data) => {
    // [1단계] 하드웨어 데이터 저장
    set({ hardwareData: data });

    // [2단계] 온도 히스토리에 데이터 추가
    // null 체크: 센서가 읽지 못한 경우 null일 수 있음
    if (data.sensors.temperature !== null) {
      // get(): 현재 스토어 상태 접근
      // addTemperaturePoint: 다른 액션 호출
      get().addTemperaturePoint(data.sensors.temperature);
    }

    // [3단계] 습도 히스토리에 데이터 추가
    if (data.sensors.humidity !== null) {
      get().addHumidityPoint(data.sensors.humidity);
    }
  },

  // ==================== 시스템 메트릭 초기값 및 액션 ====================

  systemMetrics: null,
  setSystemMetrics: (metrics) => set({ systemMetrics: metrics }),

  // ==================== 앱 설정 초기값 및 액션 ====================

  config: null,
  setConfig: (config) => set({ config }),

  // ==================== UI 상태 (다크 모드) ====================

  // [darkMode 초기값]
  // window.matchMedia(): 브라우저의 미디어 쿼리 API
  // '(prefers-color-scheme: dark)': OS의 다크 모드 설정 확인
  // .matches: 조건이 맞으면 true, 아니면 false
  //
  // [시스템 설정 연동]
  // 사용자의 OS 다크 모드 설정을 자동으로 따름
  // 예: macOS/Windows에서 다크 모드 설정하면 자동 적용
  darkMode: window.matchMedia('(prefers-color-scheme: dark)').matches,

  // [toggleDarkMode 액션]
  // 다크 모드 토글 + DOM 클래스 조작
  toggleDarkMode: () =>
    set((state) => {
      // [이전 상태 반전]
      const newDarkMode = !state.darkMode;

      // [DOM 조작]
      // document.documentElement: <html> 요소
      // classList.add/remove: CSS 클래스 추가/제거
      //
      // [Tailwind CSS 다크 모드]
      // 'dark' 클래스가 있으면 dark: 접두사가 붙은 스타일 적용
      // 예: className="bg-white dark:bg-gray-900"
      if (newDarkMode) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }

      // [새 상태 반환]
      // set 함수가 이 객체로 상태를 업데이트
      return { darkMode: newDarkMode };
    }),

  // ==================== 사이드바 상태 ====================

  // [초기값]
  // true: 시작 시 사이드바 열려있음
  sidebarOpen: true,

  // [toggleSidebar 액션]
  // 화살표 함수로 간단하게 토글
  // (state) => ({ sidebarOpen: !state.sidebarOpen })
  // 이전 상태(state)를 받아서 반전된 값을 가진 새 객체 반환
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

  // ==================== 현재 페이지 ====================

  // [초기값]
  // 앱 시작 시 대시보드 페이지 표시
  activePage: 'dashboard',

  // [setActivePage 액션]
  // 페이지 네비게이션 처리
  setActivePage: (page) => set({ activePage: page }),

  // ==================== 온도 히스토리 ====================

  // [초기값]
  // 빈 배열로 시작
  temperatureHistory: [],

  // [addTemperaturePoint 액션]
  // 새 온도 데이터 포인트 추가
  addTemperaturePoint: (value) =>
    set((state) => {
      // [현재 시간 포맷팅]
      const now = new Date();

      // toLocaleTimeString(): 현지화된 시간 문자열
      // 옵션:
      //   hour12: false - 24시간 형식 (14:30 형태)
      //   hour/minute/second: '2-digit' - 두 자리 숫자
      // 결과: "14:30:25" 형태
      const time = now.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });

      // [새 히스토리 배열 생성]
      // 스프레드 연산자(...): 기존 배열 복사
      // 불변성(Immutability): 원본 배열을 수정하지 않고 새 배열 생성
      // React가 상태 변경을 감지하려면 불변성 유지 필요
      const newHistory = [...state.temperatureHistory, { time, value }];

      // [최대 길이 제한]
      // 60개 초과 시 가장 오래된 데이터(첫 번째) 제거
      // shift(): 배열 첫 요소 제거 및 반환
      if (newHistory.length > MAX_HISTORY_POINTS) {
        newHistory.shift();
      }

      // [새 상태 반환]
      return { temperatureHistory: newHistory };
    }),

  // ==================== 습도 히스토리 ====================

  humidityHistory: [],

  // [addHumidityPoint 액션]
  // 온도와 동일한 로직으로 습도 데이터 추가
  addHumidityPoint: (value) =>
    set((state) => {
      const now = new Date();
      const time = now.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });

      const newHistory = [...state.humidityHistory, { time, value }];
      if (newHistory.length > MAX_HISTORY_POINTS) {
        newHistory.shift();
      }

      return { humidityHistory: newHistory };
    }),

  // ==================== 알림/경고 시스템 ====================

  // [초기값]
  // 빈 알림 배열
  alerts: [],

  // [addAlert 액션]
  // 새 알림 추가
  addAlert: (type, message) =>
    set((state) => {
      // [유니크 ID 생성]
      // Date.now(): 현재 타임스탬프 (밀리초)
      // Math.random().toString(36): 랜덤 문자열 (36진수)
      // substr(2, 9): 'a1b2c3d4e' 형태로 9자 추출
      // 결과: "1703123456789-a1b2c3d4e" 형태의 유니크 ID
      const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

      // [새 알림 객체 생성]
      const newAlert = { id, type, message, timestamp: new Date() };

      // [알림 추가 + 최대 10개 유지]
      // slice(-10): 배열의 마지막 10개 요소만 유지
      // 오래된 알림은 자동으로 제거됨
      return { alerts: [...state.alerts, newAlert].slice(-10) }; // Keep last 10 alerts
    }),

  // [removeAlert 액션]
  // ID로 특정 알림 제거
  removeAlert: (id) =>
    set((state) => ({
      // filter(): 조건에 맞는 요소만 남김
      // a.id !== id: 제거할 ID가 아닌 것만 유지
      alerts: state.alerts.filter((a) => a.id !== id),
    })),

  // [clearAlerts 액션]
  // 모든 알림 삭제
  clearAlerts: () => set({ alerts: [] }),
}));


// ==================== 다크 모드 초기화 ====================
/**
 * [브라우저 환경 체크]
 * typeof window !== 'undefined'
 * - 서버 사이드 렌더링(SSR)에서 window 객체가 없을 수 있음
 * - 이 코드는 클라이언트에서만 실행되어야 함
 *
 * [다크 모드 클래스 적용]
 * 페이지 로드 시 OS 설정에 따라 다크 모드 클래스 추가
 * 이렇게 하면 Zustand 스토어 초기화 전에도 깜빡임 없이 올바른 테마 적용
 */
if (typeof window !== 'undefined') {
  // OS 다크 모드 설정 확인
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    // <html> 요소에 'dark' 클래스 추가
    // Tailwind CSS가 이 클래스를 기반으로 다크 스타일 적용
    document.documentElement.classList.add('dark');
  }
}
