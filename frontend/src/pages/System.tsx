/**
 * System Monitoring Page (시스템 모니터링 페이지)
 * ================================================
 *
 * [한국어 설명]
 * Raspberry Pi 시스템의 상태를 모니터링하는 페이지입니다.
 * CPU, 메모리, 디스크, 네트워크 등 시스템 리소스를 실시간으로 표시합니다.
 *
 * [주요 기능]
 * 1. CPU 모니터링: 사용률, 코어 수, 주파수, 온도
 * 2. CPU 히스토리 차트: 시간에 따른 사용률 변화 그래프
 * 3. 메모리 모니터링: 사용률, 사용량, 총 용량
 * 4. 디스크 모니터링: 사용률, 여유 공간, 총 용량
 * 5. 네트워크 I/O: 송수신 데이터량
 * 6. 시스템 업타임: 부팅 후 경과 시간
 * 7. 플랫폼 정보: OS, 아키텍처, Raspberry Pi 여부
 *
 * [컴포넌트 구조]
 * System
 *  ├── CPU Usage Card (게이지 + 상세 정보)
 *  ├── CPU Temperature Card (게이지 + 온도 레벨 가이드)
 *  ├── CPU History Chart (AreaChart - 시계열)
 *  ├── Memory Card (게이지 + 용량 정보)
 *  ├── Disk Card (게이지 + 용량 정보)
 *  ├── Network Card (송수신 데이터)
 *  ├── Uptime Card (가동 시간)
 *  └── Platform Info Card (시스템 정보)
 */

// ==================== Imports ====================

// [Zustand 스토어]
// 전역 상태에서 시스템 메트릭과 설정 가져오기
import { useStore } from '../hooks/useStore';

// [GaugeChart 컴포넌트]
// 원형 게이지로 퍼센트 값 시각화
import GaugeChart from '../components/GaugeChart';

// [shadcn/ui 컴포넌트]
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

// [Lucide 아이콘]
// 각 시스템 메트릭을 나타내는 아이콘
import {
  Cpu,          // CPU
  MemoryStick,  // 메모리 (RAM)
  HardDrive,    // 디스크 (스토리지)
  Thermometer,  // 온도
  Activity,     // 활동/히스토리
  Clock,        // 업타임/시간
  Wifi,         // 네트워크
  Server,       // 서버/플랫폼
} from 'lucide-react';

// ==================== Recharts Imports ====================
/**
 * [Recharts 라이브러리]
 * React용 차트 라이브러리
 * D3.js 기반이지만 React 선언적 방식으로 사용 가능
 *
 * [사용되는 컴포넌트]
 * - AreaChart: 영역 차트 (선 아래가 채워진 차트)
 * - Area: 실제 영역 요소
 * - XAxis: X축 (시간)
 * - YAxis: Y축 (CPU %)
 * - CartesianGrid: 격자 배경
 * - Tooltip: 마우스 호버 시 값 표시
 * - ResponsiveContainer: 반응형 컨테이너 (부모 크기에 맞춤)
 */
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

// [React Hooks]
import { useState, useEffect } from 'react';


// ==================== System 컴포넌트 ====================
/**
 * [System 함수형 컴포넌트]
 * 시스템 모니터링 페이지의 메인 컴포넌트
 */
export default function System() {
  // ==================== 상태 관리 ====================

  // [전역 상태에서 데이터 가져오기]
  const { systemMetrics, config } = useStore();

  // [CPU 히스토리 상태]
  // 시계열 데이터를 로컬에서 관리
  // 배열 형태: [{ time: '14:30:05', value: 45.2 }, ...]
  const [cpuHistory, setCpuHistory] = useState<Array<{ time: string; value: number }>>([]);

  // ==================== CPU 히스토리 추적 ====================
  /**
   * [useEffect로 히스토리 관리]
   * systemMetrics의 CPU 사용률이 변경될 때마다 실행
   * 히스토리 배열에 새 데이터 추가
   */
  useEffect(() => {
    // CPU 퍼센트 값이 있는 경우에만 실행
    if (systemMetrics?.cpu.percent !== undefined) {
      // [현재 시간 포맷팅]
      const now = new Date();
      const time = now.toLocaleTimeString('en-US', {
        hour12: false,       // 24시간 형식
        hour: '2-digit',     // 시: 2자리
        minute: '2-digit',   // 분: 2자리
        second: '2-digit',   // 초: 2자리
      });
      // 결과: "14:30:05"

      // [히스토리 업데이트]
      setCpuHistory((prev) => {
        // 스프레드 연산자로 기존 배열 복사 후 새 데이터 추가
        const newHistory = [...prev, { time, value: systemMetrics.cpu.percent }];

        // [최대 60개 유지]
        // 60개 초과 시 가장 오래된 데이터 제거
        // shift(): 배열 첫 번째 요소 제거
        if (newHistory.length > 60) newHistory.shift();

        return newHistory;
      });
    }
  }, [systemMetrics?.cpu.percent]);
  // [의존성 배열]
  // CPU 퍼센트가 변경될 때만 effect 실행

  // ==================== 데이터 추출 ====================
  /**
   * [구조 분해 할당]
   * systemMetrics 객체에서 필요한 데이터 추출
   * 옵셔널 체이닝으로 null 안전하게 처리
   */
  const cpu = systemMetrics?.cpu;
  const memory = systemMetrics?.memory;
  const disk = systemMetrics?.disk;
  const network = systemMetrics?.network;
  const system = systemMetrics?.system;

  // ==================== JSX 반환 ====================
  return (
    <div className="space-y-6">

      {/* ==================== CPU & 온도 섹션 ==================== */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* ========== CPU 사용률 카드 ========== */}
        <Card>
          <CardHeader>
            <CardTitle>
              <Cpu className="w-5 h-5 text-blue-500" />
              CPU Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/*
              [플렉스 레이아웃]
              게이지와 상세 정보를 가로로 배치
              gap-8: 요소 간 2rem(32px) 간격
            */}
            <div className="flex items-center justify-center gap-8">
              {/* CPU 게이지 */}
              {/*
                [GaugeChart Props]
                showWarning: 경고 표시 활성화
                warningThreshold: 90% 이상이면 빨간색
              */}
              <GaugeChart
                value={cpu?.percent ?? 0}
                max={100}
                label="Usage"
                unit="%"
                color="#3b82f6"  // Tailwind blue-500
                size="lg"
                showWarning
                warningThreshold={90}
              />

              {/* CPU 상세 정보 */}
              <div className="space-y-3">
                {/* 코어 수 */}
                <div>
                  <span className="text-sm text-muted-foreground">Cores</span>
                  <p className="text-xl font-bold">
                    {cpu?.count ?? 0}
                  </p>
                </div>
                {/* 주파수 */}
                <div>
                  <span className="text-sm text-muted-foreground">Frequency</span>
                  <p className="text-xl font-bold">
                    {/*
                      [toFixed(0)]
                      정수로 표시 (MHz 단위)
                    */}
                    {cpu?.frequency.current.toFixed(0) ?? 0} MHz
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* ========== CPU 온도 카드 ========== */}
        <Card>
          <CardHeader>
            <CardTitle>
              <Thermometer className="w-5 h-5 text-orange-500" />
              CPU Temperature
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center gap-8">
              {/* 온도 게이지 */}
              {/*
                [최대값 85°C]
                Raspberry Pi의 일반적인 최대 안전 온도
              */}
              <GaugeChart
                value={cpu?.temperature ?? 0}
                max={85}
                label="Temperature"
                unit="°C"
                color="#f97316"  // Tailwind orange-500
                size="lg"
                showWarning
                warningThreshold={80}  // 80% = 68°C에서 경고
              />

              {/* 온도 레벨 가이드 */}
              <div className="space-y-2">
                {/* 정상 */}
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-green-500" />
                  <span className="text-sm text-muted-foreground">&lt;60°C Normal</span>
                </div>
                {/* 따뜻함 */}
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-yellow-500" />
                  <span className="text-sm text-muted-foreground">60-70°C Warm</span>
                </div>
                {/* 뜨거움 */}
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-orange-500" />
                  <span className="text-sm text-muted-foreground">70-80°C Hot</span>
                </div>
                {/* 위험 */}
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-red-500" />
                  <span className="text-sm text-muted-foreground">&gt;80°C Critical</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ==================== CPU 히스토리 차트 ==================== */}
      <Card>
        <CardHeader>
          <CardTitle>
            <Activity className="w-5 h-5 text-blue-500" />
            CPU Usage History
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/*
            [차트 높이 설정]
            h-64: 16rem(256px) 높이
          */}
          <div className="h-64">
            {/*
              [ResponsiveContainer]
              부모 요소의 크기에 맞춰 차트 크기 자동 조절
              width/height="100%": 부모 크기의 100%
            */}
            <ResponsiveContainer width="100%" height="100%">
              {/*
                [AreaChart]
                data: 차트에 표시할 데이터 배열
                각 데이터 객체는 { time, value } 구조
              */}
              <AreaChart data={cpuHistory}>
                {/*
                  [CartesianGrid]
                  배경 격자선
                  strokeDasharray="3 3": 점선 패턴 (3px 선, 3px 공백)
                */}
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />

                {/*
                  [XAxis]
                  X축 (시간)
                  dataKey: 데이터에서 사용할 키
                  tick: 눈금 레이블 스타일
                  interval: "preserveStartEnd" - 시작/끝 레이블 유지
                */}
                <XAxis dataKey="time" tick={{ fontSize: 10 }} interval="preserveStartEnd" />

                {/*
                  [YAxis]
                  Y축 (퍼센트)
                  domain: 범위 [최소, 최대]
                  width: Y축 영역 너비
                */}
                <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} width={40} />

                {/*
                  [Tooltip]
                  마우스 호버 시 표시되는 툴팁
                  contentStyle: 툴팁 박스 스타일
                  formatter: 값 표시 형식
                */}
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    border: 'none',
                    borderRadius: '8px',
                  }}
                  // [formatter 함수]
                  // value: 데이터 값
                  // 반환: [표시할 값, 레이블]
                  formatter={(value: number) => [`${value.toFixed(1)}%`, 'CPU']}
                />

                {/*
                  [Area]
                  실제 영역 그래프
                  type="monotone": 부드러운 곡선
                  dataKey: 데이터에서 Y값으로 사용할 키
                  stroke: 선 색상
                  fill: 채우기 색상
                  fillOpacity: 채우기 투명도 (0-1)
                */}
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#3b82f6"  // 파란색 선
                  fill="#3b82f6"   // 파란색 채우기
                  fillOpacity={0.3} // 30% 투명도
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* ==================== 메모리 & 디스크 섹션 ==================== */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* ========== 메모리 카드 ========== */}
        <Card>
          <CardHeader>
            <CardTitle>
              <MemoryStick className="w-5 h-5 text-green-500" />
              Memory Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center gap-8">
              {/* 메모리 게이지 */}
              <GaugeChart
                value={memory?.percent ?? 0}
                max={100}
                label="Usage"
                unit="%"
                color="#22c55e"  // Tailwind green-500
                size="lg"
                showWarning
                warningThreshold={90}
              />

              {/* 메모리 상세 정보 */}
              <div className="space-y-3">
                <div>
                  <span className="text-sm text-muted-foreground">Used</span>
                  <p className="text-xl font-bold">
                    {memory?.used_gb.toFixed(2) ?? 0} GB
                  </p>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">Total</span>
                  <p className="text-xl font-bold">
                    {memory?.total_gb.toFixed(2) ?? 0} GB
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* ========== 디스크 카드 ========== */}
        <Card>
          <CardHeader>
            <CardTitle>
              <HardDrive className="w-5 h-5 text-purple-500" />
              Disk Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center gap-8">
              {/* 디스크 게이지 */}
              <GaugeChart
                value={disk?.percent ?? 0}
                max={100}
                label="Usage"
                unit="%"
                color="#a855f7"  // Tailwind purple-500
                size="lg"
                showWarning
                warningThreshold={90}
              />

              {/* 디스크 상세 정보 */}
              <div className="space-y-3">
                <div>
                  <span className="text-sm text-muted-foreground">Free</span>
                  <p className="text-xl font-bold">
                    {disk?.free_gb.toFixed(2) ?? 0} GB
                  </p>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">Total</span>
                  <p className="text-xl font-bold">
                    {disk?.total_gb.toFixed(2) ?? 0} GB
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ==================== 네트워크 & 업타임 섹션 ==================== */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* ========== 네트워크 I/O 카드 ========== */}
        <Card>
          <CardHeader>
            <CardTitle>
              <Wifi className="w-5 h-5 text-cyan-500" />
              Network I/O
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/*
              [2열 그리드]
              송신과 수신 데이터를 나란히 표시
            */}
            <div className="grid grid-cols-2 gap-4">
              {/* 송신 데이터 */}
              <div className="p-4 bg-cyan-50 dark:bg-cyan-900/20 rounded-lg text-center">
                <p className="text-sm text-muted-foreground">Sent</p>
                <p className="text-2xl font-bold">
                  {network?.sent_mb.toFixed(1) ?? 0}
                </p>
                <p className="text-sm text-muted-foreground">MB</p>
              </div>
              {/* 수신 데이터 */}
              <div className="p-4 bg-cyan-50 dark:bg-cyan-900/20 rounded-lg text-center">
                <p className="text-sm text-muted-foreground">Received</p>
                <p className="text-2xl font-bold">
                  {network?.recv_mb.toFixed(1) ?? 0}
                </p>
                <p className="text-sm text-muted-foreground">MB</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* ========== 시스템 업타임 카드 ========== */}
        <Card>
          <CardHeader>
            <CardTitle>
              <Clock className="w-5 h-5 text-amber-500" />
              System Uptime
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center py-4">
              <div className="text-center">
                {/* 가동 시간 (시간 단위) */}
                <p className="text-4xl font-bold">
                  {system?.uptime_hours.toFixed(1) ?? 0}
                </p>
                <p className="text-lg text-muted-foreground">hours</p>

                {/* 부팅 시간 표시 */}
                {/*
                  [조건부 렌더링]
                  boot_time이 있을 때만 표시
                */}
                {system?.boot_time && (
                  <p className="text-sm text-muted-foreground mt-2">
                    {/*
                      [Date 변환 및 포맷팅]
                      ISO 문자열을 Date 객체로 변환 후 로컬 형식으로 표시
                    */}
                    Since {new Date(system.boot_time).toLocaleString()}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ==================== 플랫폼 정보 섹션 ==================== */}
      <Card>
        <CardHeader>
          <CardTitle>
            <Server className="w-5 h-5 text-muted-foreground" />
            Platform Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/*
            [4열 그리드]
            플랫폼 정보를 균등하게 표시
          */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* 플랫폼 (OS) */}
            <div>
              <span className="text-sm text-muted-foreground">Platform</span>
              <p className="font-medium">
                {config?.platform.system ?? 'Unknown'}
              </p>
            </div>
            {/* 아키텍처 */}
            <div>
              <span className="text-sm text-muted-foreground">Architecture</span>
              <p className="font-medium">
                {config?.platform.machine ?? 'Unknown'}
              </p>
            </div>
            {/* Raspberry Pi 여부 */}
            <div>
              <span className="text-sm text-muted-foreground">Raspberry Pi</span>
              <p className="font-medium">
                {config?.platform.is_raspberry_pi ? 'Yes' : 'No'}
              </p>
            </div>
            {/* 동작 모드 */}
            <div>
              <span className="text-sm text-muted-foreground">Mode</span>
              <p className="font-medium">
                {config?.simulation_mode ? 'Simulation' : 'Hardware'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
