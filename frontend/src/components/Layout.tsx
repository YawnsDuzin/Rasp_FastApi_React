/**
 * Layout Component (레이아웃 컴포넌트)
 * ======================================
 *
 * [한국어 설명]
 * 애플리케이션의 기본 레이아웃을 정의하는 컴포넌트입니다.
 * Gmail 스타일의 사이드바 네비게이션과 상단 헤더를 포함합니다.
 *
 * [컴포넌트 구조]
 * Layout
 *  ├── Sidebar (사이드바)
 *  │    ├── Logo Header (로고 + 햄버거 메뉴)
 *  │    ├── Navigation (네비게이션 메뉴)
 *  │    └── Connection Status (연결 상태)
 *  └── Main Content (메인 콘텐츠)
 *       ├── Header (상단 헤더)
 *       └── Page Content (페이지 내용 - children)
 *
 * [Children 패턴]
 * <Layout>{페이지 컴포넌트}</Layout>
 * children prop으로 실제 페이지 내용을 전달받아 렌더링
 */

// ==================== Imports ====================

// [ReactNode 타입]
// React에서 렌더링 가능한 모든 것을 나타내는 타입
// JSX, 문자열, 숫자, null, 배열 등 포함
import { ReactNode } from 'react';

// [Zustand 스토어]
// 사이드바 상태, 페이지 전환, 연결 상태 등 관리
import { useStore } from '../hooks/useStore';

// [shadcn/ui 컴포넌트]
// Button: 버튼 컴포넌트
import { Button } from '@/components/ui/button';

// [유틸리티 함수]
// cn: 조건부 클래스명 병합 (clsx + tailwind-merge)
import { cn } from '@/lib/utils';

// [Lucide 아이콘]
// 네비게이션 메뉴, 테마 토글, 연결 상태에 사용
import {
  LayoutDashboard, // 대시보드 아이콘
  Cpu,             // 하드웨어/CPU 아이콘
  Thermometer,     // 센서 아이콘
  Activity,        // 시스템 활동 아이콘
  FileText,        // 로그 아이콘
  Settings,        // 설정 아이콘
  Menu,            // 햄버거 메뉴 아이콘
  Moon,            // 다크 모드 아이콘
  Sun,             // 라이트 모드 아이콘
  Wifi,            // 연결됨 아이콘
  WifiOff,         // 연결 끊김 아이콘
} from 'lucide-react';


// ==================== Props 인터페이스 ====================
/**
 * [LayoutProps 인터페이스]
 * Layout 컴포넌트가 받는 props 정의
 *
 * [children: ReactNode]
 * - 레이아웃 내부에 렌더링될 콘텐츠
 * - <Layout>{children}</Layout> 형태로 전달
 */
interface LayoutProps {
  children: ReactNode;
}


// ==================== 네비게이션 메뉴 정의 ====================
/**
 * [navItems 배열]
 * 사이드바 네비게이션 메뉴 항목 정의
 *
 * [항목 구조]
 * - id: 페이지 식별자 (activePage와 비교)
 * - label: 메뉴에 표시되는 텍스트
 * - icon: 메뉴 아이콘 컴포넌트 (Lucide React)
 *
 * [아이콘을 변수로 저장하는 이유]
 * React 컴포넌트도 JavaScript 객체이므로 변수에 저장 가능
 * <Icon />으로 동적 렌더링 가능
 */
const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'hardware', label: 'Hardware', icon: Cpu },
  { id: 'sensors', label: 'Sensors', icon: Thermometer },
  { id: 'system', label: 'System', icon: Activity },
  { id: 'logs', label: 'Logs', icon: FileText },
  { id: 'settings', label: 'Settings', icon: Settings },
];


// ==================== Layout 컴포넌트 ====================
/**
 * [Layout 함수형 컴포넌트]
 * 앱의 기본 레이아웃 구조를 제공
 *
 * [Props 구조 분해]
 * { children }: LayoutProps
 * props 객체에서 children만 추출
 */
export default function Layout({ children }: LayoutProps) {

  // ==================== Zustand 상태 및 액션 ====================
  /**
   * [useStore에서 필요한 상태와 액션 추출]
   *
   * 상태:
   * - sidebarOpen: 사이드바 열림 여부
   * - darkMode: 다크 모드 활성화 여부
   * - activePage: 현재 활성 페이지 ID
   * - isConnected: WebSocket 연결 상태
   * - config: 앱 설정 (시뮬레이션 모드 등)
   *
   * 액션:
   * - toggleSidebar: 사이드바 열기/닫기
   * - toggleDarkMode: 다크/라이트 모드 전환
   * - setActivePage: 페이지 변경
   */
  const {
    sidebarOpen,
    toggleSidebar,
    darkMode,
    toggleDarkMode,
    activePage,
    setActivePage,
    isConnected,
    config,
  } = useStore();

  // ==================== JSX 반환 ====================
  return (
    // [전체 레이아웃 컨테이너]
    // min-h-screen: 최소 높이를 화면 전체로
    // flex: 사이드바와 메인 콘텐츠를 나란히 배치
    <div className="min-h-screen flex">

      {/* ==================== 사이드바 ==================== */}
      {/*
        [aside 태그]
        의미론적 HTML: 사이드 콘텐츠를 나타냄
        스크린 리더에게 네비게이션 영역임을 알림

        [고정 위치]
        fixed: 화면에 고정 (스크롤해도 움직이지 않음)
        inset-y-0 left-0: 왼쪽에 위아래로 꽉 채움
        z-50: 다른 요소 위에 표시 (z-index: 50)

        [너비 전환]
        transition-all duration-300: 모든 속성에 300ms 애니메이션
        sidebarOpen ? 'w-64' : 'w-20': 열림/닫힘에 따라 너비 변경
      */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex flex-col bg-card border-r transition-all duration-300',
          sidebarOpen ? 'w-64' : 'w-20'
        )}
      >

        {/* ---------- 로고 헤더 (Gmail 스타일) ---------- */}
        {/*
          [구성]
          - 햄버거 메뉴 버튼 (항상 표시)
          - 로고와 타이틀 (사이드바 열렸을 때만)
        */}
        <div className="h-16 flex items-center justify-center border-b px-3">

          {/* 햄버거 메뉴 버튼 */}
          {/*
            [Button 컴포넌트]
            variant="ghost": 배경 없는 투명 버튼
            size="icon": 정사각형 아이콘 버튼
            onClick: 클릭 시 사이드바 토글
          */}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="flex-shrink-0"
          >
            <Menu className="w-5 h-5" />
          </Button>

          {/* 로고 - 사이드바 열렸을 때만 표시 */}
          {/*
            [조건부 렌더링]
            sidebarOpen && (...): 사이드바가 열려있을 때만 렌더링
          */}
          {sidebarOpen && (
            <div className="flex items-center gap-3 ml-2">
              {/* 로고 아이콘 박스 */}
              <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
                <Cpu className="w-6 h-6 text-primary-foreground" />
              </div>
              {/* 로고 텍스트 */}
              <div className="flex flex-col">
                <span className="font-bold text-foreground">RasPi HMI</span>
                {/* 현재 모드 표시 */}
                <span className="text-xs text-muted-foreground">
                  {config?.simulation_mode ? 'Simulation' : 'Hardware'}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* ---------- 네비게이션 메뉴 ---------- */}
        {/*
          [nav 태그]
          의미론적 HTML: 네비게이션 영역
          flex-1: 남은 공간 모두 차지 (연결 상태를 아래로 밀어냄)
        */}
        <nav className="flex-1 p-4 space-y-2">
          {/*
            [메뉴 항목 렌더링]
            navItems.map(): 배열의 각 항목을 버튼으로 변환
          */}
          {navItems.map((item) => {
            // [동적 아이콘 컴포넌트]
            // Icon = item.icon (예: LayoutDashboard)
            // <Icon /> 형태로 렌더링 가능
            const Icon = item.icon;

            // [활성 상태 확인]
            // 현재 페이지와 일치하는지 확인
            const isActive = activePage === item.id;

            return (
              <Button
                key={item.id}  // React 리스트의 고유 키
                // [버튼 스타일]
                // 활성 페이지: 기본(채워진) 스타일
                // 비활성 페이지: ghost(투명) 스타일
                variant={isActive ? 'default' : 'ghost'}
                // [페이지 전환]
                onClick={() => setActivePage(item.id)}
                // [버튼 레이아웃]
                // 사이드바 열림: 아이콘 + 텍스트
                // 사이드바 닫힘: 아이콘만 중앙 정렬
                className={cn(
                  'w-full justify-start gap-3',
                  !sidebarOpen && 'justify-center px-0'
                )}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                {/* 사이드바 열렸을 때만 라벨 표시 */}
                {sidebarOpen && <span>{item.label}</span>}
              </Button>
            );
          })}
        </nav>

        {/* ---------- 연결 상태 표시 ---------- */}
        <div className="p-4 border-t">
          {/*
            [연결 상태 배지]
            연결됨: 초록색 배경
            연결 끊김: 빨간색 배경
          */}
          <div
            className={cn(
              'flex items-center gap-3 px-4 py-2 rounded-lg',
              isConnected
                ? 'bg-green-100 dark:bg-green-900/30'
                : 'bg-red-100 dark:bg-red-900/30'
            )}
          >
            {/* 연결 상태 아이콘 */}
            {isConnected ? (
              <Wifi className="w-5 h-5 text-green-600 dark:text-green-400" />
            ) : (
              <WifiOff className="w-5 h-5 text-red-600 dark:text-red-400" />
            )}
            {/* 연결 상태 텍스트 (사이드바 열렸을 때만) */}
            {sidebarOpen && (
              <span
                className={cn(
                  'text-sm font-medium',
                  isConnected
                    ? 'text-green-700 dark:text-green-400'
                    : 'text-red-700 dark:text-red-400'
                )}
              >
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            )}
          </div>
        </div>
      </aside>

      {/* ==================== 메인 콘텐츠 영역 ==================== */}
      {/*
        [마진 조정]
        사이드바 너비에 따라 왼쪽 마진 조정
        ml-64 (사이드바 열림) / ml-20 (사이드바 닫힘)
        사이드바가 fixed이므로 마진으로 겹침 방지
      */}
      <div
        className={cn(
          'flex-1 flex flex-col transition-all duration-300',
          sidebarOpen ? 'ml-64' : 'ml-20'
        )}
      >

        {/* ---------- 상단 헤더 ---------- */}
        <header className="h-16 bg-card border-b flex items-center justify-between px-6">
          {/* 왼쪽: 페이지 제목 */}
          <div className="flex items-center gap-4">
            {/*
              [capitalize 클래스]
              첫 글자를 대문자로 (CSS text-transform)
              'dashboard' → 'Dashboard'
            */}
            <h1 className="text-xl font-semibold capitalize">
              {activePage}
            </h1>
          </div>

          {/* 오른쪽: 상태 표시 및 토글 */}
          <div className="flex items-center gap-4">
            {/* 실시간 연결 인디케이터 */}
            <div className="flex items-center gap-2">
              {/*
                [status-indicator 클래스]
                CSS에서 정의된 깜빡이는 점 애니메이션
                online: 초록색, offline: 빨간색
              */}
              <div className={cn(
                'status-indicator',
                isConnected ? 'online' : 'offline'
              )} />
              <span className="text-sm text-muted-foreground">
                Real-time
              </span>
            </div>

            {/* 다크 모드 토글 버튼 */}
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleDarkMode}
            >
              {/* 현재 모드에 따라 반대 아이콘 표시 */}
              {darkMode ? (
                <Sun className="w-5 h-5 text-yellow-500" />  // 다크모드: 해 아이콘 (클릭시 라이트로)
              ) : (
                <Moon className="w-5 h-5" />  // 라이트모드: 달 아이콘 (클릭시 다크로)
              )}
            </Button>
          </div>
        </header>

        {/* ---------- 페이지 콘텐츠 ---------- */}
        {/*
          [main 태그]
          의미론적 HTML: 메인 콘텐츠 영역

          [children 렌더링]
          <Layout>{페이지}</Layout>에서 전달된 children을 여기에 렌더링
          Dashboard, Hardware, Sensors 등 실제 페이지 컴포넌트가 들어감

          [overflow-auto]
          콘텐츠가 넘칠 경우 스크롤바 표시
        */}
        <main className="flex-1 p-6 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
