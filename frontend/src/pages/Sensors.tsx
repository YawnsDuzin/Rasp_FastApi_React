/**
 * Sensors Page (센서 페이지)
 * ==========================
 *
 * [한국어 설명]
 * 다양한 센서 데이터를 시각적으로 표시하는 페이지입니다.
 * 온도, 습도, 거리, 조도 등 환경 센서와 ADC 값을 모니터링합니다.
 *
 * [표시되는 센서 종류]
 * 1. 환경 센서 (Environmental):
 *    - 온도 (DHT22)
 *    - 습도 (DHT22)
 *    - 기압 (BMP280)
 *    - 고도 (BMP280에서 계산)
 *
 * 2. 기타 센서:
 *    - 거리 (HC-SR04 초음파)
 *    - 모션 (PIR 적외선)
 *    - 조도 (LDR)
 *    - 토양 습도 (Soil Moisture)
 *
 * 3. ADC 데이터:
 *    - I2C ADC (ADS1115)
 *    - SPI ADC (MCP3008)
 *
 * [컴포넌트 구조]
 * Sensors
 *  ├── Environmental Sensors Card (환경 센서)
 *  ├── Distance Card (초음파 센서)
 *  ├── Motion Card (PIR 센서)
 *  ├── Light Card (조도 센서)
 *  ├── Soil Moisture Card (토양 습도)
 *  ├── I2C ADC Card (ADS1115)
 *  └── SPI ADC Card (MCP3008)
 */

// ==================== Imports ====================

// [Zustand 스토어]
// 전역 상태에서 하드웨어 데이터(센서 포함) 가져오기
import { useStore } from '../hooks/useStore';

// [GaugeChart 컴포넌트]
// 원형 게이지 차트로 센서 값 시각화
import GaugeChart from '../components/GaugeChart';

// [shadcn/ui 컴포넌트]
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

// [cn 유틸리티]
// 조건부 클래스명 병합
import { cn } from '@/lib/utils';

// [Lucide 아이콘]
// 각 센서 타입을 나타내는 아이콘
import {
  Thermometer,  // 온도
  Droplets,     // 습도
  Gauge,        // 기압/고도
  Ruler,        // 거리
  Eye,          // 모션 감지
  Sun,          // 조도
  Droplet,      // 토양 습도
  Cpu,          // ADC 칩
} from 'lucide-react';


// ==================== Sensors 컴포넌트 ====================
/**
 * [Sensors 함수형 컴포넌트]
 * 센서 모니터링 페이지의 메인 컴포넌트
 */
export default function Sensors() {
  // ==================== 상태 가져오기 ====================

  // [전역 상태에서 하드웨어 데이터 추출]
  const { hardwareData } = useStore();

  // [센서 및 ADC 데이터 추출]
  // 옵셔널 체이닝으로 안전하게 접근
  const sensors = hardwareData?.sensors;
  const adc = hardwareData?.adc;

  // ==================== JSX 반환 ====================
  return (
    <div className="space-y-6">

      {/* ==================== 환경 센서 섹션 ==================== */}
      <Card>
        <CardHeader>
          <CardTitle>
            <Thermometer className="w-5 h-5 text-orange-500" />
            Environmental Sensors
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/*
            [4열 그리드]
            모바일: 2열
            태블릿 이상: 4열
          */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">

            {/* ========== 온도 ========== */}
            {/*
              [색상 구분]
              각 센서마다 고유한 배경색 사용
              - 온도: 주황색 (따뜻함을 연상)
              - 습도: 파란색 (물방울 연상)
              - 기압: 보라색
              - 고도: 초록색
            */}
            <div className="flex flex-col items-center p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
              <Thermometer className="w-8 h-8 text-orange-500 mb-2" />
              {/*
                [toFixed(1)]
                소수점 1자리까지 표시
                25.456 → "25.5"

                [?? '--']
                Nullish coalescing: 값이 없으면 '--' 표시
              */}
              <span className="text-3xl font-bold">
                {sensors?.temperature?.toFixed(1) ?? '--'}
              </span>
              <span className="text-sm text-muted-foreground">°C</span>
              <span className="text-xs text-muted-foreground mt-1">
                Temperature
              </span>
            </div>

            {/* ========== 습도 ========== */}
            <div className="flex flex-col items-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <Droplets className="w-8 h-8 text-blue-500 mb-2" />
              <span className="text-3xl font-bold">
                {sensors?.humidity?.toFixed(1) ?? '--'}
              </span>
              <span className="text-sm text-muted-foreground">%</span>
              <span className="text-xs text-muted-foreground mt-1">
                Humidity
              </span>
            </div>

            {/* ========== 기압 ========== */}
            {/*
              [toFixed(0)]
              정수로 표시 (소수점 없음)
              기압은 보통 정수로 표시
            */}
            <div className="flex flex-col items-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <Gauge className="w-8 h-8 text-purple-500 mb-2" />
              <span className="text-3xl font-bold">
                {sensors?.pressure?.toFixed(0) ?? '--'}
              </span>
              <span className="text-sm text-muted-foreground">hPa</span>
              <span className="text-xs text-muted-foreground mt-1">
                Pressure
              </span>
            </div>

            {/* ========== 고도 ========== */}
            {/*
              [BMP280 고도 계산]
              기압에서 고도를 추정
              표준 기압(1013.25 hPa)을 기준으로 계산
            */}
            <div className="flex flex-col items-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <Gauge className="w-8 h-8 text-green-500 mb-2" />
              <span className="text-3xl font-bold">
                {sensors?.altitude?.toFixed(1) ?? '--'}
              </span>
              <span className="text-sm text-muted-foreground">m</span>
              <span className="text-xs text-muted-foreground mt-1">
                Altitude
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ==================== 기타 센서 섹션 ==================== */}
      {/*
        [3열 그리드]
        거리, 모션, 조도 센서를 가로로 배치
      */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* ========== 거리 센서 (HC-SR04) ========== */}
        <Card>
          <CardHeader>
            <CardTitle>
              <Ruler className="w-5 h-5 text-cyan-500" />
              Distance (Ultrasonic)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/*
              [GaugeChart 사용]
              value: 현재 거리 값
              max: 최대 측정 가능 거리 (400cm)
              color: 시안색 (hex)
            */}
            <div className="flex justify-center py-4">
              <GaugeChart
                value={sensors?.distance ?? 0}
                max={400}
                label="Distance"
                unit="cm"
                color="#06b6d4"  // Tailwind cyan-500
              />
            </div>
            <div className="text-center text-sm text-muted-foreground">
              HC-SR04 Sensor
            </div>
          </CardContent>
        </Card>

        {/* ========== 모션 센서 (PIR) ========== */}
        <Card>
          <CardHeader>
            <CardTitle>
              <Eye className="w-5 h-5 text-red-500" />
              Motion (PIR)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/*
              [모션 상태 표시]
              모션 감지 시:
              - 빨간색 원 + 펄스 애니메이션
              - "Motion Detected!" 텍스트
            */}
            <div className="flex flex-col items-center py-4">
              <div
                className={cn(
                  'w-24 h-24 rounded-full flex items-center justify-center transition-all duration-500',
                  sensors?.motion
                    ? 'bg-red-500 animate-pulse-ring'  // 커스텀 애니메이션 (CSS에 정의)
                    : 'bg-muted'
                )}
              >
                <Eye
                  className={cn(
                    'w-12 h-12',
                    sensors?.motion ? 'text-white' : 'text-muted-foreground'
                  )}
                />
              </div>
              <span
                className={cn(
                  'mt-4 text-lg font-bold',
                  sensors?.motion
                    ? 'text-red-500'
                    : 'text-muted-foreground'
                )}
              >
                {sensors?.motion ? 'Motion Detected!' : 'No Motion'}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* ========== 조도 센서 (LDR) ========== */}
        <Card>
          <CardHeader>
            <CardTitle>
              <Sun className="w-5 h-5 text-yellow-500" />
              Light Level (LDR)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/*
              [LDR 값 범위]
              0: 완전 어둠
              1023: 매우 밝음 (10비트 ADC 최대값)
            */}
            <div className="flex justify-center py-4">
              <GaugeChart
                value={sensors?.light_level ?? 0}
                max={1023}
                label="Light"
                unit=""  // 단위 없음 (상대값)
                color="#eab308"  // Tailwind yellow-500
              />
            </div>
            {/* 범위 표시 */}
            <div className="flex justify-between px-4 text-xs text-muted-foreground">
              <span>Dark</span>
              <span>Bright</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ==================== 토양 습도 센서 ==================== */}
      <Card>
        <CardHeader>
          <CardTitle>
            <Droplet className="w-5 h-5 text-blue-500" />
            Soil Moisture
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/*
            [2열 레이아웃]
            왼쪽: 게이지 차트
            오른쪽: 수분 레벨 가이드
          */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 게이지 (큰 사이즈) */}
            <div className="flex justify-center">
              <GaugeChart
                value={sensors?.soil_moisture ?? 0}
                max={1023}
                label="Moisture"
                unit=""
                color="#3b82f6"  // Tailwind blue-500
                size="lg"        // 큰 게이지
              />
            </div>

            {/* 수분 레벨 가이드 */}
            {/*
              [색상 코드 설명]
              사용자가 토양 수분 상태를 쉽게 이해할 수 있도록
              색상과 범위를 시각적으로 표시
            */}
            <div className="flex flex-col justify-center space-y-4">
              {/* 건조 (빨간색) */}
              <div className="flex items-center gap-4">
                <div className="w-4 h-4 rounded bg-red-500" />
                <span className="text-sm text-muted-foreground">
                  0-300: Dry - Needs water
                </span>
              </div>
              {/* 보통 (노란색) */}
              <div className="flex items-center gap-4">
                <div className="w-4 h-4 rounded bg-yellow-500" />
                <span className="text-sm text-muted-foreground">
                  300-600: Moderate
                </span>
              </div>
              {/* 양호 (초록색) */}
              <div className="flex items-center gap-4">
                <div className="w-4 h-4 rounded bg-green-500" />
                <span className="text-sm text-muted-foreground">
                  600-900: Good moisture
                </span>
              </div>
              {/* 과습 (파란색) */}
              <div className="flex items-center gap-4">
                <div className="w-4 h-4 rounded bg-blue-500" />
                <span className="text-sm text-muted-foreground">
                  900+: Very wet
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ==================== ADC 데이터 섹션 ==================== */}
      {/*
        [ADC란?]
        Analog to Digital Converter
        아날로그 신호(전압)를 디지털 값으로 변환

        [사용되는 ADC]
        - ADS1115: I2C 인터페이스, 16비트, 4채널
        - MCP3008: SPI 인터페이스, 10비트, 8채널
      */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* ========== I2C ADC (ADS1115) ========== */}
        <Card>
          <CardHeader>
            <CardTitle>
              <Cpu className="w-5 h-5 text-indigo-500" />
              I2C ADC (ADS1115)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/*
              [채널 데이터 렌더링]
              adc.i2c = { 0: 1.234, 1: 2.345, ... }
              Object.entries()로 [채널번호, 전압] 배열로 변환
            */}
            {adc?.i2c &&
              Object.entries(adc.i2c).map(([channel, voltage]) => (
                <div key={channel} className="space-y-1">
                  {/* 채널 번호와 전압 값 */}
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">
                      Channel {channel}
                    </span>
                    <span className="font-medium">
                      {/*
                        [Type Assertion]
                        (voltage as number).toFixed(3)
                        TypeScript에 voltage가 number임을 명시
                        소수점 3자리까지 표시
                      */}
                      {(voltage as number).toFixed(3)} V
                    </span>
                  </div>

                  {/*
                    [Progress 컴포넌트]
                    전압을 진행률 바로 시각화
                    최대 전압 3.3V를 100%로 계산
                  */}
                  <Progress
                    value={((voltage as number) / 3.3) * 100}
                    className="h-2"
                    indicatorClassName="bg-indigo-500"  // 커스텀 색상
                  />
                </div>
              ))}

            {/* 데이터 없음 표시 */}
            {(!adc?.i2c || Object.keys(adc.i2c).length === 0) && (
              <p className="text-muted-foreground text-center py-4">
                No I2C ADC data available
              </p>
            )}
          </CardContent>
        </Card>

        {/* ========== SPI ADC (MCP3008) ========== */}
        <Card>
          <CardHeader>
            <CardTitle>
              <Cpu className="w-5 h-5 text-pink-500" />
              SPI ADC (MCP3008)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* I2C ADC와 동일한 구조 */}
            {adc?.spi &&
              Object.entries(adc.spi).map(([channel, voltage]) => (
                <div key={channel} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">
                      Channel {channel}
                    </span>
                    <span className="font-medium">
                      {(voltage as number).toFixed(3)} V
                    </span>
                  </div>
                  <Progress
                    value={((voltage as number) / 3.3) * 100}
                    className="h-2"
                    indicatorClassName="bg-pink-500"  // 핑크색 진행률 바
                  />
                </div>
              ))}

            {/* 데이터 없음 표시 */}
            {(!adc?.spi || Object.keys(adc.spi).length === 0) && (
              <p className="text-muted-foreground text-center py-4">
                No SPI ADC data available
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
