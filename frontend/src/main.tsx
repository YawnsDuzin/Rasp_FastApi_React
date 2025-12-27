/**
 * Main Entry Point (메인 진입점)
 * ===============================
 *
 * [한국어 설명]
 * React 애플리케이션의 시작점입니다.
 * HTML의 root 요소에 React 앱을 마운트(mount)합니다.
 *
 * [핵심 개념]
 * 1. React 18+ 클라이언트 렌더링:
 *    - createRoot(): React 18의 새로운 렌더링 API
 *    - 동시성 렌더링(Concurrent Rendering) 지원
 *    - 기존 ReactDOM.render()를 대체
 *
 * 2. StrictMode:
 *    - 개발 모드에서 추가 검사 수행
 *    - 안전하지 않은 생명주기 메서드 경고
 *    - 레거시 API 사용 경고
 *    - 의도적인 이중 렌더링으로 부작용 감지
 *    - 프로덕션에서는 영향 없음
 *
 * [파일 구조]
 * main.tsx (이 파일)
 *   └── App.tsx (루트 컴포넌트)
 *         └── Layout.tsx (레이아웃)
 *               └── 각 페이지 컴포넌트
 */

// [React 라이브러리 import]
// React: React 핵심 라이브러리 (JSX 변환, 컴포넌트 시스템)
import React from 'react'

// [ReactDOM 클라이언트]
// react-dom/client: React 18의 클라이언트 렌더링 API
// DOM(Document Object Model)에 React 컴포넌트를 렌더링하는 기능 제공
import ReactDOM from 'react-dom/client'

// [루트 컴포넌트]
// App: 애플리케이션의 최상위 컴포넌트
// 모든 페이지와 상태 관리를 포함
import App from './App'

// [전역 스타일]
// Tailwind CSS와 커스텀 스타일 포함
// 이 import로 스타일이 번들에 포함됨
import './styles/index.css'

// ==================== React 애플리케이션 마운트 ====================

// [document.getElementById('root')]
// public/index.html의 <div id="root"></div> 요소를 찾음
// 이 div가 React 앱의 컨테이너가 됨

// [! (Non-null assertion)]
// TypeScript에서 null이 아님을 단언
// getElementById는 null을 반환할 수 있지만, root는 항상 존재한다고 확신

// [createRoot()]
// React 18의 새로운 루트 생성 API
// - 동시성 기능 활성화
// - 자동 배치(automatic batching) 지원
// - startTransition 등 새 기능 사용 가능
ReactDOM.createRoot(document.getElementById('root')!).render(
  // [React.StrictMode]
  // 개발 도구: 잠재적 문제를 식별하기 위한 래퍼 컴포넌트
  //
  // [StrictMode가 하는 일]
  // 1. 컴포넌트를 두 번 렌더링하여 순수성 검증
  //    - 부작용(side effect)이 있으면 문제가 드러남
  // 2. useEffect를 두 번 실행하여 정리(cleanup) 검증
  //    - 구독/이벤트 리스너 누수 감지
  // 3. 레거시 API 사용 경고
  //    - findDOMNode, 레거시 context API 등
  // 4. 안전하지 않은 생명주기 메서드 경고
  //    - componentWillMount 등
  //
  // [주의사항]
  // - 개발 모드에서만 활성화됨
  // - 프로덕션 빌드에서는 아무 영향 없음
  // - 이중 렌더링으로 인해 개발 중 console.log가 2번 출력될 수 있음
  <React.StrictMode>
    {/*
      [App 컴포넌트]
      애플리케이션의 루트 컴포넌트
      - 라우팅 (페이지 전환)
      - 전역 상태 초기화
      - WebSocket 연결 설정
      - 레이아웃 적용
    */}
    <App />
  </React.StrictMode>,
)
