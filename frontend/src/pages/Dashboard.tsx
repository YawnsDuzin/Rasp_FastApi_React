/**
 * Dashboard Page (대시보드 페이지)
 * ==================================
 *
 * [한국어 설명]
 * 애플리케이션의 메인 페이지로, 핵심 정보를 한눈에 보여줍니다.
 * 센서 데이터, 시스템 메트릭, GPIO 상태, 실시간 차트를 표시합니다.
 *
 * [페이지 구성]
 * 1. 시뮬레이션 모드 배너
 * 2. 센서 게이지 차트 (온도, 습도, 기압, 거리)
 * 3. 시스템 메트릭 (CPU, 메모리, 디스크, 가동시간)
 * 4. GPIO 상태 (LED, 버튼, 릴레이)
 * 5. 실시간 라인 차트 (온도/습도 트렌드)
 *
 * [사용된 라이브러리]
 * - lucide-react: 아이콘 컴포넌트
 * - recharts: 차트 라이브러리
 * - shadcn/ui: UI 컴포넌트 (Card, Progress)
 */

// ==================== Imports ====================

// [Zustand 스토어]
// 전역 상태에서 하드웨어 데이터, 시스템 메트릭 등을 가져옴
import { useStore } from '../hooks/useStore';

// [커스텀 컴포넌트]
// 원형 게이지 차트 (센서 값 표시용)
import GaugeChart from '../components/GaugeChart';

// [shadcn/ui 컴포넌트]
// Card: 정보를 담는 카드 컨테이너
// Progress: 진행률/사용량 표시 막대
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

// [유틸리티 함수]
// cn: 클래스명을 조건부로 병합하는 유틸리티 (clsx + tailwind-merge)
import { cn } from '@/lib/utils';

// [Lucide 아이콘]
// 각 정보 섹션에 사용되는 아이콘들
import {
  Thermometer,    // 온도계 아이콘
  Droplets,       // 물방울 아이콘 (습도)
  Gauge,          // 게이지 아이콘 (기압)
  Activity,       // 활동 아이콘 (거리)
  Cpu,            // CPU 아이콘
  HardDrive,      // 하드 드라이브 아이콘 (디스크)
  MemoryStick,    // 메모리 아이콘
  Lightbulb,      // 전구 아이콘 (LED)
  Power,          // 전원 아이콘 (릴레이, 가동시간)
  CircleDot,      // 원형 점 아이콘 (버튼)
} from 'lucide-react';

// [Recharts 라이브러리]
// 반응형 라인 차트를 위한 컴포넌트들
import {
  LineChart,           // 라인 차트 컨테이너
  Line,                // 라인 (데이터 선)
  XAxis,               // X축 (시간)
  YAxis,               // Y축 (값)
  CartesianGrid,       // 격자 배경
  Tooltip,             // 마우스 오버 시 툴팁
  ResponsiveContainer, // 반응형 래퍼 (부모 크기에 맞춤)
} from 'recharts';


// ==================== Dashboard 컴포넌트 ====================
/**
 * [Dashboard 함수형 컴포넌트]
 * 메인 대시보드 페이지를 렌더링
 *
 * [export default]
 * 파일의 기본 내보내기
 * import Dashboard from './Dashboard' 형태로 사용
 */
export default function Dashboard() {

  // ==================== Zustand 상태 가져오기 ====================
  /**
   * [useStore 훅 사용]
   * 전역 상태에서 필요한 데이터 추출
   *
   * - hardwareData: GPIO, PWM, 센서 데이터
   * - systemMetrics: CPU, 메모리, 디스크 메트릭
   * - temperatureHistory: 온도 시계열 데이터 (차트용)
   * - humidityHistory: 습도 시계열 데이터 (차트용)
   * - config: 앱 설정 (시뮬레이션 모드 여부 등)
   */
  const { hardwareData, systemMetrics, temperatureHistory, humidityHistory, config } =
    useStore();

  // [옵셔널 체이닝으로 데이터 추출]
  // hardwareData?.sensors: hardwareData가 null이면 undefined 반환
  const sensors = hardwareData?.sensors;
  const gpio = hardwareData?.gpio;

  // ==================== JSX 반환 ====================
  /**
   * [JSX 구조]
   * 전체 페이지는 세로로 섹션들이 나열된 구조
   * space-y-6: 각 섹션 간 1.5rem(24px) 간격
   */
  return (
    <div className="space-y-6">

      {/* ==================== 시뮬레이션 모드 배너 ==================== */}
      {/*
        [조건부 렌더링]
        config?.simulation_mode && (...): simulation_mode가 true일 때만 렌더링

        [JSX 내 조건부 렌더링 패턴]
        1. condition && <Component />: 조건이 true면 렌더링
        2. condition ? <A /> : <B />: 조건에 따라 다른 컴포넌트
      */}
      {config?.simulation_mode && (
        <div className="bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-300 dark:border-yellow-700 rounded-lg p-4">
          <p className="text-yellow-800 dark:text-yellow-200 text-sm">
            {/* 시뮬레이션 모드 안내 메시지 */}
            <strong>Simulation Mode:</strong> Running without hardware. Sensor values are simulated.
          </p>
        </div>
      )}

      {/* ==================== 센서 게이지 차트 ==================== */}
      {/*
        [Grid 레이아웃]
        grid: CSS Grid 사용
        grid-cols-2: 기본 2열
        md:grid-cols-4: 중간 화면 이상에서 4열
        gap-6: 그리드 아이템 간 1.5rem 간격

        [반응형 디자인]
        Tailwind의 반응형 접두사: sm, md, lg, xl, 2xl
        md:grid-cols-4: 768px 이상에서 4열 적용
      */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">

        {/* ---------- 온도 게이지 ---------- */}
        <Card className="flex flex-col items-center p-6">
          {/* 아이콘과 라벨 */}
          <div className="flex items-center gap-2 text-orange-500 mb-4">
            <Thermometer className="w-5 h-5" />
            <span className="font-medium">Temperature</span>
          </div>
          {/*
            [GaugeChart 컴포넌트]
            value: 현재 값 (null이면 0)
            max: 최대값 (게이지 스케일)
            unit: 단위 (°C, %, hPa 등)
            color: 게이지 색상 (HEX 코드)
            showWarning, warningThreshold: 경고 표시 설정

            [Nullish Coalescing]
            sensors?.temperature ?? 0
            - sensors?.temperature가 null 또는 undefined면 0 사용
            - || 와 달리 0이나 ''도 유효한 값으로 취급
          */}
          <GaugeChart
            value={sensors?.temperature ?? 0}
            max={50}
            label=""
            unit="°C"
            color="#f97316"
            showWarning
            warningThreshold={70}
          />
        </Card>

        {/* ---------- 습도 게이지 ---------- */}
        <Card className="flex flex-col items-center p-6">
          <div className="flex items-center gap-2 text-blue-500 mb-4">
            <Droplets className="w-5 h-5" />
            <span className="font-medium">Humidity</span>
          </div>
          <GaugeChart
            value={sensors?.humidity ?? 0}
            max={100}
            label=""
            unit="%"
            color="#3b82f6"
          />
        </Card>

        {/* ---------- 기압 게이지 ---------- */}
        <Card className="flex flex-col items-center p-6">
          <div className="flex items-center gap-2 text-purple-500 mb-4">
            <Gauge className="w-5 h-5" />
            <span className="font-medium">Pressure</span>
          </div>
          <GaugeChart
            value={sensors?.pressure ?? 1013}  // 기본값: 표준 대기압 1013 hPa
            max={1100}
            label=""
            unit="hPa"
            color="#a855f7"
          />
        </Card>

        {/* ---------- 거리 게이지 ---------- */}
        <Card className="flex flex-col items-center p-6">
          <div className="flex items-center gap-2 text-green-500 mb-4">
            <Activity className="w-5 h-5" />
            <span className="font-medium">Distance</span>
          </div>
          <GaugeChart
            value={sensors?.distance ?? 0}
            max={400}  // HC-SR04 최대 측정 거리: 400cm
            label=""
            unit="cm"
            color="#22c55e"
          />
        </Card>
      </div>

      {/* ==================== 시스템 메트릭 ==================== */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">

        {/* ---------- CPU 사용량 ---------- */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {/* 아이콘 배경 박스 */}
                <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <Cpu className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  {/* text-muted-foreground: 흐린 텍스트 색상 (shadcn 변수) */}
                  <p className="text-sm text-muted-foreground">CPU</p>
                  {/*
                    [toFixed(1)]
                    숫자를 소수점 1자리까지 문자열로 변환
                    23.456.toFixed(1) → "23.5"
                  */}
                  <p className="text-2xl font-bold">
                    {systemMetrics?.cpu.percent.toFixed(1) ?? 0}%
                  </p>
                </div>
              </div>
              {/* CPU 온도 표시 (Raspberry Pi에서만) */}
              {systemMetrics?.cpu.temperature && (
                <div className="text-right">
                  <p className="text-xs text-muted-foreground">Temp</p>
                  <p className="text-lg font-semibold text-orange-500">
                    {systemMetrics.cpu.temperature.toFixed(1)}°C
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* ---------- 메모리 사용량 ---------- */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <MemoryStick className="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Memory</p>
                <p className="text-2xl font-bold">
                  {systemMetrics?.memory.percent.toFixed(1) ?? 0}%
                </p>
              </div>
            </div>
            {/* 메모리 사용량 프로그레스 바 */}
            <div className="mt-3">
              {/*
                [Progress 컴포넌트]
                value: 진행률 (0-100)
                indicatorClassName: 프로그레스 바 색상 커스터마이징
              */}
              <Progress
                value={systemMetrics?.memory.percent ?? 0}
                className="h-2"
                indicatorClassName="bg-green-500"
              />
              {/* 사용량/전체 용량 표시 */}
              <p className="text-xs text-muted-foreground mt-1">
                {systemMetrics?.memory.used_gb.toFixed(1)} / {systemMetrics?.memory.total_gb.toFixed(1)} GB
              </p>
            </div>
          </CardContent>
        </Card>

        {/* ---------- 디스크 사용량 ---------- */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <HardDrive className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Disk</p>
                <p className="text-2xl font-bold">
                  {systemMetrics?.disk.percent.toFixed(1) ?? 0}%
                </p>
              </div>
            </div>
            <div className="mt-3">
              <Progress
                value={systemMetrics?.disk.percent ?? 0}
                className="h-2"
                indicatorClassName="bg-purple-500"
              />
              {/* 남은 용량 표시 */}
              <p className="text-xs text-muted-foreground mt-1">
                {systemMetrics?.disk.free_gb.toFixed(1)} GB free
              </p>
            </div>
          </CardContent>
        </Card>

        {/* ---------- 시스템 가동시간 ---------- */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                <Power className="w-5 h-5 text-orange-600 dark:text-orange-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Uptime</p>
                <p className="text-2xl font-bold">
                  {systemMetrics?.system.uptime_hours.toFixed(1) ?? 0}h
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ==================== GPIO 상태 ==================== */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* ---------- LED 상태 ---------- */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle>
              <Lightbulb className="w-5 h-5 text-yellow-500" />
              LED Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              {/*
                [Object.entries()]
                객체를 [key, value] 배열로 변환
                { 0: true, 1: false } → [["0", true], ["1", false]]

                [.map() 메서드]
                배열의 각 요소를 변환하여 새 배열 생성
                React에서 리스트 렌더링에 사용
              */}
              {gpio &&
                Object.entries(gpio.leds).map(([index, state]) => (
                  <div
                    key={index}  // React 리스트의 고유 키 (필수)
                    className="flex flex-col items-center gap-2"
                  >
                    {/*
                      [cn() 함수]
                      조건부 클래스명 병합
                      cn('기본클래스', 조건 && '조건부클래스')
                    */}
                    <div
                      className={cn(
                        'w-8 h-8 rounded-full transition-all duration-300',
                        state
                          ? 'bg-yellow-400 shadow-lg shadow-yellow-400/50'  // LED ON
                          : 'bg-muted'  // LED OFF
                      )}
                    />
                    <span className="text-xs text-muted-foreground">
                      {/* parseInt로 문자열을 숫자로 변환 후 1 더함 (0-based → 1-based) */}
                      LED {parseInt(index) + 1}
                    </span>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>

        {/* ---------- 버튼 상태 ---------- */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle>
              <CircleDot className="w-5 h-5 text-blue-500" />
              Button Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              {gpio &&
                Object.entries(gpio.buttons).map(([index, state]) => (
                  <div
                    key={index}
                    className="flex flex-col items-center gap-2"
                  >
                    <div
                      className={cn(
                        'w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300',
                        state
                          ? 'bg-blue-500 shadow-lg shadow-blue-500/50'  // 버튼 눌림
                          : 'bg-muted'  // 버튼 떼어짐
                      )}
                    >
                      <CircleDot className={cn('w-4 h-4', state ? 'text-white' : 'text-muted-foreground')} />
                    </div>
                    <span className="text-xs text-muted-foreground">
                      BTN {parseInt(index) + 1}
                    </span>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>

        {/* ---------- 릴레이 상태 ---------- */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle>
              <Power className="w-5 h-5 text-green-500" />
              Relay Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              {gpio &&
                Object.entries(gpio.relays).map(([index, state]) => (
                  <div
                    key={index}
                    className="flex flex-col items-center gap-2"
                  >
                    <div
                      className={cn(
                        'w-10 h-10 rounded-lg flex items-center justify-center transition-all duration-300',
                        state
                          ? 'bg-green-500 text-white'  // 릴레이 ON
                          : 'bg-muted text-muted-foreground'  // 릴레이 OFF
                      )}
                    >
                      <Power className="w-5 h-5" />
                    </div>
                    <span className="text-xs text-muted-foreground">
                      Relay {parseInt(index) + 1}
                    </span>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ==================== 실시간 차트 ==================== */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* ---------- 온도 트렌드 차트 ---------- */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle>
              <Thermometer className="w-5 h-5 text-orange-500" />
              Temperature Trend
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/* 차트 컨테이너 높이 고정 */}
            <div className="h-64">
              {/*
                [ResponsiveContainer]
                부모 요소 크기에 맞게 차트 크기 조절
                width="100%" height="100%": 부모 크기에 맞춤
              */}
              <ResponsiveContainer width="100%" height="100%">
                {/*
                  [LineChart]
                  data: 차트에 표시할 데이터 배열
                  [{ time: "14:30:25", value: 25.5 }, ...]
                */}
                <LineChart data={temperatureHistory}>
                  {/*
                    [CartesianGrid]
                    차트 배경 격자선
                    strokeDasharray="3 3": 점선 스타일 (3px 선, 3px 공백)
                  */}
                  <CartesianGrid strokeDasharray="3 3" className="opacity-30" />

                  {/*
                    [XAxis]
                    dataKey: 데이터에서 X축 값으로 사용할 키
                    tick: 축 레이블 스타일
                    interval: 레이블 표시 간격 ("preserveStartEnd": 시작/끝 보존)
                  */}
                  <XAxis
                    dataKey="time"
                    tick={{ fontSize: 10 }}
                    interval="preserveStartEnd"
                  />

                  {/*
                    [YAxis]
                    domain: Y축 범위 ('auto': 데이터에 맞게 자동 조절)
                    width: 축 너비 (레이블 공간)
                  */}
                  <YAxis
                    domain={['auto', 'auto']}
                    tick={{ fontSize: 10 }}
                    width={40}
                  />

                  {/*
                    [Tooltip]
                    마우스 호버 시 표시되는 정보 박스
                    contentStyle: 툴팁 스타일 커스터마이징
                  */}
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(0, 0, 0, 0.8)',
                      border: 'none',
                      borderRadius: '8px',
                    }}
                  />

                  {/*
                    [Line]
                    실제 데이터 라인
                    type="monotone": 부드러운 곡선 (monotonic interpolation)
                    dataKey: 데이터에서 Y축 값으로 사용할 키
                    stroke: 라인 색상
                    strokeWidth: 라인 두께
                    dot={false}: 데이터 포인트 점 표시 안 함
                    name: 툴팁에 표시될 이름
                  */}
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#f97316"
                    strokeWidth={2}
                    dot={false}
                    name="Temperature"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* ---------- 습도 트렌드 차트 ---------- */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle>
              <Droplets className="w-5 h-5 text-blue-500" />
              Humidity Trend
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={humidityHistory}>
                  <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                  <XAxis
                    dataKey="time"
                    tick={{ fontSize: 10 }}
                    interval="preserveStartEnd"
                  />
                  {/* 습도는 0-100% 고정 범위 */}
                  <YAxis
                    domain={[0, 100]}
                    tick={{ fontSize: 10 }}
                    width={40}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(0, 0, 0, 0.8)',
                      border: 'none',
                      borderRadius: '8px',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={false}
                    name="Humidity"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
