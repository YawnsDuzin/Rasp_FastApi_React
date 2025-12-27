/**
 * Gauge Chart Component (게이지 차트 컴포넌트)
 * ==============================================
 *
 * [한국어 설명]
 * 원형 게이지 차트를 렌더링하는 재사용 가능한 컴포넌트입니다.
 * 센서 값, 시스템 메트릭 등을 시각적으로 표시하는 데 사용됩니다.
 *
 * [SVG 원 게이지 원리]
 * 1. 배경 원 (회색): 전체 범위 표시
 * 2. 값 원 (컬러): strokeDasharray/strokeDashoffset로 부분만 표시
 * 3. 중앙 텍스트: 실제 숫자 값과 단위 표시
 *
 * [strokeDasharray / strokeDashoffset]
 * - strokeDasharray: 선을 점선으로 만듦 (선 길이, 공백 길이)
 * - strokeDashoffset: 점선 시작 위치를 이동
 * - 두 값을 조합하여 원의 일부만 채워진 것처럼 표시
 *
 * [사용 예시]
 * <GaugeChart
 *   value={25.5}
 *   max={50}
 *   label="Temperature"
 *   unit="°C"
 *   color="#f97316"
 *   showWarning
 *   warningThreshold={70}
 * />
 */

// ==================== Imports ====================

// [clsx 라이브러리]
// 조건부 클래스명 병합 유틸리티
// cn()과 비슷하지만 tailwind-merge 기능 없음
import clsx from 'clsx';


// ==================== Props 인터페이스 ====================
/**
 * [GaugeChartProps 인터페이스]
 * 게이지 차트 컴포넌트의 props 타입 정의
 *
 * [필수 Props]
 * - value: 현재 값 (표시할 숫자)
 * - max: 최대값 (게이지 스케일의 100%)
 * - label: 게이지 아래 표시되는 라벨
 * - unit: 값의 단위 (°C, %, hPa 등)
 *
 * [선택적 Props]
 * - color: 게이지 색상 (기본값: 하늘색)
 * - size: 게이지 크기 (sm, md, lg)
 * - showWarning: 경고 표시 활성화
 * - warningThreshold: 경고 임계값 (%)
 */
interface GaugeChartProps {
  value: number;              // 현재 값
  max: number;                // 최대값
  label: string;              // 라벨 텍스트
  unit: string;               // 단위
  color?: string;             // 게이지 색상 (선택, 기본: #0ea5e9)
  size?: 'sm' | 'md' | 'lg';  // 크기 (선택, 기본: md)
  showWarning?: boolean;      // 경고 표시 여부 (선택)
  warningThreshold?: number;  // 경고 임계값 % (선택, 기본: 80)
}


// ==================== GaugeChart 컴포넌트 ====================
/**
 * [GaugeChart 함수형 컴포넌트]
 * 원형 게이지 차트를 렌더링
 *
 * [기본값 설정]
 * color = '#0ea5e9': 기본 색상 (하늘색)
 * size = 'md': 기본 크기 (중간)
 * showWarning = false: 기본적으로 경고 비활성화
 * warningThreshold = 80: 80% 이상일 때 경고 색상
 */
export default function GaugeChart({
  value,
  max,
  label,
  unit,
  color = '#0ea5e9',         // 기본 색상: 하늘색
  size = 'md',                // 기본 크기: 중간
  showWarning = false,        // 기본: 경고 비활성화
  warningThreshold = 80,      // 기본 임계값: 80%
}: GaugeChartProps) {

  // ==================== 계산 로직 ====================

  /**
   * [퍼센트 계산]
   * (현재값 / 최대값) * 100 = 퍼센트
   * Math.min(..., 100): 100%를 초과하지 않도록 제한
   *
   * [예시]
   * value=25, max=50 → (25/50)*100 = 50%
   */
  const percentage = Math.min((value / max) * 100, 100);

  /**
   * [경고 상태 확인]
   * showWarning이 true이고, 퍼센트가 임계값 이상이면 경고
   *
   * [단축 평가 (Short-circuit evaluation)]
   * showWarning && percentage >= warningThreshold
   * 앞이 false면 뒤는 평가하지 않음
   */
  const isWarning = showWarning && percentage >= warningThreshold;

  // ==================== 크기별 스타일 정의 ====================
  /**
   * [sizes 객체]
   * 크기에 따른 CSS 클래스 매핑
   *
   * - container: 게이지 컨테이너 크기
   * - text: 값 텍스트 크기
   * - label: 라벨 텍스트 크기
   */
  const sizes = {
    sm: { container: 'w-24 h-24', text: 'text-lg', label: 'text-xs' },
    md: { container: 'w-32 h-32', text: 'text-2xl', label: 'text-sm' },
    lg: { container: 'w-40 h-40', text: 'text-3xl', label: 'text-base' },
  };

  // ==================== SVG 원 계산 ====================

  /**
   * [strokeWidth]
   * 원의 선 두께 (크기에 비례)
   * 작은 게이지: 6px, 중간: 8px, 큰: 10px
   *
   * [삼항 연산자 체이닝]
   * condition1 ? value1 : condition2 ? value2 : value3
   */
  const strokeWidth = size === 'sm' ? 6 : size === 'md' ? 8 : 10;

  /**
   * [radius (반지름)]
   * SVG viewBox가 100x100이므로 중심이 50,50
   * 반지름 = 50 - (선 두께 / 2)
   * 선 두께의 절반을 빼야 원이 viewBox 안에 맞음
   */
  const radius = 50 - strokeWidth / 2;

  /**
   * [circumference (원주)]
   * 원의 둘레 = 2 * π * 반지름
   * 이 값은 strokeDasharray에 사용됨
   *
   * [Math.PI]
   * JavaScript의 파이 상수 (≈ 3.14159)
   */
  const circumference = 2 * Math.PI * radius;

  /**
   * [strokeDashoffset]
   * 게이지가 채워지는 정도를 결정
   *
   * [원리]
   * - strokeDasharray를 원주 길이로 설정하면 전체가 선(하나의 dash)
   * - strokeDashoffset으로 시작점을 이동
   * - offset이 크면 안 보이는 부분이 많음, 작으면 많이 보임
   *
   * [공식]
   * 전체 원주 - (퍼센트/100) * 원주 = 보이지 않는 부분
   *
   * [예시]
   * 50% 채우려면: circumference - 0.5 * circumference = 0.5 * circumference
   * 즉, 절반이 보이지 않게 됨 (=절반만 보임)
   */
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  /**
   * [gaugeColor]
   * 경고 상태면 빨간색, 아니면 지정된 색상
   *
   * [빨간색 경고]
   * #ef4444: Tailwind의 red-500 색상
   */
  const gaugeColor = isWarning ? '#ef4444' : color;

  // ==================== JSX 반환 ====================
  return (
    /**
     * [게이지 컨테이너]
     * relative: 내부 요소 절대 위치 기준점
     * sizes[size].container: 크기별 너비/높이 클래스
     */
    <div className={clsx('relative', sizes[size].container)}>

      {/* ==================== SVG 게이지 ==================== */}
      {/*
        [SVG 요소]
        viewBox="0 0 100 100": 좌표계 설정 (0,0부터 100x100)
        -rotate-90: 시작점을 12시 방향으로 (기본은 3시)

        [왜 -90도 회전?]
        SVG의 0도는 3시 방향 (오른쪽)
        게이지는 보통 12시 방향에서 시작하므로 -90도 회전
      */}
      <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">

        {/* ---------- 배경 원 (트랙) ---------- */}
        {/*
          [원 속성]
          cx, cy: 중심 좌표 (50, 50)
          r: 반지름
          fill="none": 내부 채우기 없음 (테두리만)
          stroke="currentColor": 현재 텍스트 색상 사용
          strokeWidth: 선 두께

          [색상 클래스]
          text-gray-200 dark:text-gray-700
          라이트모드: 밝은 회색, 다크모드: 어두운 회색
        */}
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-gray-200 dark:text-gray-700"
        />

        {/* ---------- 값 원 (채워지는 부분) ---------- */}
        {/*
          [strokeDasharray]
          점선 패턴 정의
          값이 circumference 하나면 "선 길이"만 설정
          = 전체가 하나의 긴 dash

          [strokeDashoffset]
          dash 시작 위치 오프셋
          이 값을 조절하여 원이 부분적으로 채워진 것처럼 표시

          [strokeLinecap="round"]
          선 끝을 둥글게 처리

          [transition-all duration-500]
          값 변경 시 500ms 동안 부드럽게 애니메이션
        */}
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke={gaugeColor}          // 게이지 색상 (경고 시 빨간색)
          strokeWidth={strokeWidth}
          strokeLinecap="round"        // 끝을 둥글게
          strokeDasharray={circumference}    // 전체 원주 길이의 dash
          strokeDashoffset={strokeDashoffset} // 채워지지 않은 부분
          className="transition-all duration-500"  // 부드러운 애니메이션
        />
      </svg>

      {/* ==================== 중앙 값 표시 ==================== */}
      {/*
        [gauge-value 클래스]
        CSS에서 정의된 스타일
        절대 위치로 게이지 중앙에 배치
        flex column으로 값, 단위, 라벨을 세로로 정렬
      */}
      <div className="gauge-value">
        {/* 숫자 값 */}
        {/*
          [toFixed(1)]
          소수점 1자리까지 표시
          25.456 → "25.5"
        */}
        <span className={clsx('font-bold text-gray-900 dark:text-white', sizes[size].text)}>
          {value.toFixed(1)}
        </span>

        {/* 단위 (°C, %, hPa 등) */}
        <span className={clsx('text-gray-500 dark:text-gray-400', sizes[size].label)}>
          {unit}
        </span>

        {/* 라벨 (Temperature, Humidity 등) */}
        <span className={clsx('text-gray-600 dark:text-gray-300 mt-1', sizes[size].label)}>
          {label}
        </span>
      </div>
    </div>
  );
}
