/**
 * Main Application Component (메인 애플리케이션 컴포넌트)
 * =========================================================
 *
 * [한국어 설명]
 * 애플리케이션의 루트 컴포넌트입니다.
 * 페이지 라우팅, WebSocket 연결, 초기 설정 로드를 담당합니다.
 *
 * [핵심 개념]
 * 1. 함수형 컴포넌트 (Functional Component):
 *    - React 16.8+ 권장 방식
 *    - 클래스 컴포넌트보다 간결하고 이해하기 쉬움
 *    - Hooks를 사용하여 상태와 부수효과 관리
 *
 * 2. React Hooks:
 *    - useEffect: 부수효과(side effect) 처리
 *    - useStore: Zustand 상태 관리 (커스텀 훅)
 *    - useWebSocket: WebSocket 연결 관리 (커스텀 훅)
 *
 * 3. 조건부 렌더링:
 *    - switch문으로 현재 페이지에 맞는 컴포넌트 렌더링
 *    - React Router 대신 간단한 상태 기반 라우팅 사용
 *
 * [컴포넌트 구조]
 * App
 *  ├── useWebSocket() - WebSocket 연결 초기화
 *  ├── useEffect() - 설정 데이터 로드
 *  └── Layout
 *       └── Dashboard | Hardware | Sensors | System | Logs | Settings
 */

// [useEffect Hook]
// React의 부수효과(side effect) 처리 훅
// - 데이터 페칭, 구독, DOM 조작 등
// - 컴포넌트 마운트/업데이트/언마운트 시 실행
import { useEffect } from 'react';

// [커스텀 훅들]
// useWebSocket: WebSocket 연결 관리
// - 자동 연결/재연결
// - 실시간 데이터 수신
// - 전역 상태 업데이트
import { useWebSocket } from './hooks/useWebSocket';

// useStore: Zustand 전역 상태 관리
// - 현재 페이지, 하드웨어 데이터, 시스템 메트릭 등
// - 컴포넌트 간 상태 공유
import { useStore } from './hooks/useStore';

// [API 서비스]
// systemApi: 시스템 관련 REST API 호출
import { systemApi } from './services/api';

// [페이지 컴포넌트들]
// 각 메뉴에 해당하는 페이지 컴포넌트
import Layout from './components/Layout';     // Gmail 스타일 레이아웃
import Dashboard from './pages/Dashboard';    // 대시보드 (요약 정보)
import Hardware from './pages/Hardware';      // 하드웨어 제어 (GPIO, PWM)
import Sensors from './pages/Sensors';        // 센서 데이터 모니터링
import System from './pages/System';          // 시스템 정보 (CPU, 메모리)
import Logs from './pages/Logs';              // 시스템 로그 뷰어
import Settings from './pages/Settings';      // 설정 (시뮬레이션 값 등)


// ==================== 메인 App 컴포넌트 ====================
/**
 * [함수형 컴포넌트]
 * function 키워드 또는 화살표 함수로 정의
 * props를 인자로 받고 JSX를 반환
 *
 * [컴포넌트 명명 규칙]
 * - PascalCase 사용 (App, Dashboard 등)
 * - 소문자로 시작하면 HTML 태그로 인식됨
 */
function App() {
  // ==================== 상태 및 훅 사용 ====================

  // [useStore 훅]
  // Zustand 스토어에서 필요한 상태와 액션 추출
  // - activePage: 현재 활성화된 페이지 이름
  // - setConfig: 설정 데이터를 스토어에 저장하는 함수
  //
  // [객체 구조 분해 할당]
  // const { a, b } = object;
  // object.a와 object.b를 각각 a, b 변수로 추출
  const { activePage, setConfig } = useStore();

  // ==================== WebSocket 연결 ====================
  // [useWebSocket 훅 호출]
  // 이 훅을 호출하면:
  // 1. 컴포넌트 마운트 시 WebSocket 연결 시도
  // 2. 연결 끊어지면 자동 재연결
  // 3. 수신된 데이터를 전역 상태에 업데이트
  // 4. 컴포넌트 언마운트 시 연결 정리
  //
  // 반환값을 사용하지 않으므로 단순 호출
  // (연결 상태가 필요하면 const { isConnected } = useWebSocket() 형태로 사용)
  useWebSocket();

  // ==================== 초기 설정 로드 ====================
  // [useEffect Hook]
  // 컴포넌트가 마운트된 후 실행되는 부수효과
  //
  // [useEffect 구조]
  // useEffect(() => {
  //   // 실행할 코드 (effect)
  //   return () => { /* 정리 코드 (cleanup) */ };
  // }, [의존성 배열]);
  //
  // [의존성 배열]
  // - []: 마운트 시 한 번만 실행
  // - [a, b]: a 또는 b가 변경될 때마다 실행
  // - 생략: 매 렌더링마다 실행 (비권장)
  useEffect(() => {
    // [비동기 함수 정의]
    // useEffect 콜백 자체는 async로 만들 수 없음
    // 내부에 async 함수를 정의하고 호출하는 패턴 사용
    const fetchConfig = async () => {
      try {
        // [API 호출]
        // systemApi.getConfig(): 서버에서 설정 정보 가져오기
        // await: Promise가 완료될 때까지 대기
        const config = await systemApi.getConfig();

        // [설정 저장]
        // Zustand 스토어에 설정 데이터 저장
        // as never: TypeScript 타입 강제 변환 (타입 불일치 해결)
        setConfig(config as never);

      } catch (error) {
        // [에러 처리]
        // API 호출 실패 시 콘솔에 에러 출력
        // 앱이 완전히 멈추지 않도록 에러를 잡아서 처리
        console.error('Failed to fetch config:', error);
      }
    };

    // [비동기 함수 실행]
    // 정의한 함수를 즉시 호출
    fetchConfig();

  }, [setConfig]);
  // [의존성 배열: [setConfig]]
  // setConfig 함수가 변경될 때마다 effect 재실행
  // Zustand에서 setConfig는 안정적(stable)이므로 실제로는 한 번만 실행됨
  // ESLint exhaustive-deps 규칙을 만족시키기 위해 포함

  // ==================== 페이지 렌더링 함수 ====================
  /**
   * [renderPage 함수]
   * 현재 활성 페이지에 따라 적절한 컴포넌트를 반환
   *
   * [조건부 렌더링 패턴]
   * - switch문: 여러 조건 중 하나 선택
   * - 삼항 연산자: condition ? a : b
   * - 논리 연산자: condition && <Component />
   */
  const renderPage = () => {
    // [switch 문]
    // activePage 값에 따라 해당 컴포넌트 반환
    switch (activePage) {
      case 'dashboard':
        // [JSX 반환]
        // <Dashboard />: Dashboard 컴포넌트 인스턴스 생성
        return <Dashboard />;

      case 'hardware':
        return <Hardware />;

      case 'sensors':
        return <Sensors />;

      case 'system':
        return <System />;

      case 'logs':
        return <Logs />;

      case 'settings':
        return <Settings />;

      default:
        // [기본값]
        // 알 수 없는 페이지면 대시보드 표시
        return <Dashboard />;
    }
  };

  // ==================== JSX 반환 ====================
  // [JSX]
  // JavaScript XML - JavaScript 안에서 HTML과 유사한 문법 사용
  // 컴파일 시 React.createElement() 호출로 변환됨
  //
  // [Layout 컴포넌트]
  // Gmail 스타일 사이드바 레이아웃
  // children prop으로 페이지 컴포넌트 전달
  //
  // [children 패턴]
  // <Layout>{renderPage()}</Layout>
  // = <Layout children={renderPage()} />
  // Layout 컴포넌트 내부에서 {children}으로 렌더링
  return <Layout>{renderPage()}</Layout>;
}

// ==================== 컴포넌트 내보내기 ====================
// [default export]
// 파일당 하나의 default export 가능
// import App from './App'로 가져올 수 있음
//
// [named export와의 차이]
// - default: import App from './App' (이름 자유롭게 변경 가능)
// - named: import { App } from './App' (정확한 이름 필요)
export default App;
