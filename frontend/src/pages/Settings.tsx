/**
 * Settings Page (설정 페이지)
 * ============================
 *
 * [한국어 설명]
 * 애플리케이션 설정과 시뮬레이션 제어를 관리하는 페이지입니다.
 * 다크 모드 전환, 시뮬레이션 값 조절, 시스템 구성 확인 등의 기능을 제공합니다.
 *
 * [주요 기능]
 * 1. 애플리케이션 설정:
 *    - 다크 모드 토글
 *
 * 2. 시뮬레이션 컨트롤 (시뮬레이션 모드일 때만):
 *    - 온도, 습도, 거리, 조도 조절 슬라이더
 *    - 모션 감지 시뮬레이션 스위치
 *    - 버튼 누름 시뮬레이션
 *
 * 3. 시스템 구성 정보:
 *    - 동작 모드 (Simulation/Hardware)
 *    - 플랫폼 정보
 *    - 업데이트 간격 설정
 *
 * 4. 앱 정보:
 *    - 프로젝트 설명
 *    - 데이터베이스 정보
 *
 * [컴포넌트 구조]
 * Settings
 *  ├── Application Settings Card (다크 모드)
 *  ├── Simulation Controls Card (시뮬레이션 모드 전용)
 *  ├── System Configuration Card (플랫폼, 모드, 인터벌)
 *  ├── About Card (프로젝트 설명)
 *  └── Database Card (DB 정보)
 */

// ==================== Imports ====================

// [React useState Hook]
// 로컬 상태 관리 (시뮬레이션 값, 로딩 상태)
import { useState } from 'react';

// [Zustand 스토어]
// 전역 상태에서 설정 정보와 다크 모드 상태 가져오기
import { useStore } from '../hooks/useStore';

// [API 서비스]
// hardwareApi: 시뮬레이션 값 설정
// systemApi: 시스템 설정 조회
import { hardwareApi, systemApi } from '../services/api';

// [shadcn/ui 컴포넌트]
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';

// [cn 유틸리티]
// 조건부 클래스명 병합
import { cn } from '@/lib/utils';

// [Lucide 아이콘]
import {
  Settings as SettingsIcon,  // 설정 (이름 충돌 방지를 위해 별칭 사용)
  Cpu,                        // 시스템/CPU
  Database,                   // 데이터베이스
  Sliders,                    // 시뮬레이션 슬라이더
  Info,                       // 정보
  RefreshCw,                  // 새로고침
} from 'lucide-react';


// ==================== Settings 컴포넌트 ====================
/**
 * [Settings 함수형 컴포넌트]
 * 설정 페이지의 메인 컴포넌트
 */
export default function Settings() {
  // ==================== 전역 상태 ====================

  /**
   * [useStore에서 상태 추출]
   * - config: 시스템 설정 정보 (시뮬레이션 모드, 플랫폼 등)
   * - darkMode: 현재 다크 모드 상태
   * - toggleDarkMode: 다크 모드 전환 함수
   */
  const { config, darkMode, toggleDarkMode } = useStore();

  // ==================== 로컬 상태 ====================

  /**
   * [simValues 상태]
   * 시뮬레이션 센서 값들
   *
   * [각 값의 범위]
   * - temperature: -10 ~ 50 (°C)
   * - humidity: 0 ~ 100 (%)
   * - distance: 2 ~ 400 (cm)
   * - motion: true/false
   * - light: 0 ~ 1023 (ADC 값)
   */
  const [simValues, setSimValues] = useState({
    temperature: 25,   // 기본 온도: 25°C
    humidity: 50,      // 기본 습도: 50%
    distance: 100,     // 기본 거리: 100cm
    motion: false,     // 기본 모션: 감지 안됨
    light: 500,        // 기본 조도: 중간값
  });

  /**
   * [loading 상태]
   * API 호출 중임을 나타내는 플래그
   */
  const [loading, setLoading] = useState(false);

  // ==================== 이벤트 핸들러 ====================

  /**
   * [handleSimValueChange 함수]
   * 시뮬레이션 값 변경 처리
   *
   * [동작 흐름]
   * 1. 로컬 상태 즉시 업데이트 (UI 반응성)
   * 2. 시뮬레이션 모드일 때만 API 호출
   * 3. 백엔드에 새 값 전달
   *
   * @param key - 변경할 센서 키 (temperature, humidity 등)
   * @param value - 새로운 값
   */
  const handleSimValueChange = async (key: string, value: number | boolean) => {
    // [로컬 상태 업데이트]
    // 스프레드 연산자로 기존 값 유지하며 특정 키만 변경
    // [key]: value는 계산된 속성명 (Computed Property Name)
    setSimValues((prev) => ({ ...prev, [key]: value }));

    // [시뮬레이션 모드 확인]
    // 하드웨어 모드에서는 시뮬레이션 값 설정이 의미 없음
    if (!config?.simulation_mode) return;

    try {
      // [API 호출]
      // { [key]: value }: 동적 키-값 객체 생성
      await hardwareApi.setSimulationValues({ [key]: value });
    } catch (error) {
      console.error('Failed to set simulation value:', error);
    }
  };

  /**
   * [handleSimulateButton 함수]
   * 버튼 누름 시뮬레이션
   *
   * [사용 목적]
   * 개발/테스트 시 물리 버튼 없이 버튼 이벤트 발생
   *
   * @param index - 버튼 인덱스 (0-3)
   */
  const handleSimulateButton = async (index: number) => {
    // 시뮬레이션 모드에서만 동작
    if (!config?.simulation_mode) return;

    setLoading(true);
    try {
      await hardwareApi.simulateButtonPress(index);
    } catch (error) {
      console.error('Failed to simulate button press:', error);
    }
    setLoading(false);
  };

  /**
   * [handleRefreshConfig 함수]
   * 시스템 설정 다시 가져오기
   *
   * [사용 목적]
   * 백엔드 설정이 변경된 경우 수동으로 갱신
   */
  const handleRefreshConfig = async () => {
    setLoading(true);
    try {
      await systemApi.getConfig();
    } catch (error) {
      console.error('Failed to refresh config:', error);
    }
    setLoading(false);
  };

  // ==================== JSX 반환 ====================
  return (
    <div className="space-y-6">

      {/* ==================== 애플리케이션 설정 ==================== */}
      <Card>
        <CardHeader>
          <CardTitle>
            <SettingsIcon className="w-5 h-5 text-muted-foreground" />
            Application Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">

          {/* 다크 모드 토글 */}
          <div className="flex items-center justify-between">
            <div>
              {/*
                [Label 컴포넌트]
                text-base: 기본 텍스트 크기
              */}
              <Label className="text-base">Dark Mode</Label>
              <p className="text-sm text-muted-foreground">
                Switch between light and dark themes
              </p>
            </div>
            {/*
              [Switch 컴포넌트]
              checked: 현재 다크 모드 상태
              onCheckedChange: 상태 변경 콜백
            */}
            <Switch checked={darkMode} onCheckedChange={toggleDarkMode} />
          </div>
        </CardContent>
      </Card>

      {/* ==================== 시뮬레이션 컨트롤 ==================== */}
      {/*
        [조건부 렌더링]
        시뮬레이션 모드일 때만 표시
        config?.simulation_mode && (...): 단축 평가
      */}
      {config?.simulation_mode && (
        <Card>
          <CardHeader>
            <CardTitle>
              <Sliders className="w-5 h-5 text-blue-500" />
              Simulation Controls
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* 설명 텍스트 */}
            <p className="text-sm text-muted-foreground pb-4">
              Adjust these values to simulate sensor readings in development mode.
            </p>

            {/* ========== 온도 슬라이더 ========== */}
            <div className="space-y-2">
              {/* 레이블과 현재 값 */}
              <div className="flex justify-between">
                <Label>Temperature</Label>
                <span className="text-sm font-medium text-primary">
                  {simValues.temperature}°C
                </span>
              </div>
              {/*
                [Slider 컴포넌트]
                value: 배열로 전달 [현재값]
                min/max: 범위
                step: 증가 단위 (0.5°C)
                onValueChange: 드래그 중 호출 (UI 업데이트)
                onValueCommit: 드래그 완료 시 호출 (API 호출)
              */}
              <Slider
                value={[simValues.temperature]}
                min={-10}
                max={50}
                step={0.5}
                onValueChange={(value) => setSimValues((prev) => ({ ...prev, temperature: value[0] }))}
                onValueCommit={(value) => handleSimValueChange('temperature', value[0])}
              />
            </div>

            {/* ========== 습도 슬라이더 ========== */}
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label>Humidity</Label>
                <span className="text-sm font-medium text-primary">
                  {simValues.humidity}%
                </span>
              </div>
              <Slider
                value={[simValues.humidity]}
                min={0}
                max={100}
                step={1}
                onValueChange={(value) => setSimValues((prev) => ({ ...prev, humidity: value[0] }))}
                onValueCommit={(value) => handleSimValueChange('humidity', value[0])}
              />
            </div>

            {/* ========== 거리 슬라이더 ========== */}
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label>Distance</Label>
                <span className="text-sm font-medium text-primary">
                  {simValues.distance} cm
                </span>
              </div>
              <Slider
                value={[simValues.distance]}
                min={2}      // HC-SR04 최소 측정 거리
                max={400}    // HC-SR04 최대 측정 거리
                step={1}
                onValueChange={(value) => setSimValues((prev) => ({ ...prev, distance: value[0] }))}
                onValueCommit={(value) => handleSimValueChange('distance', value[0])}
              />
            </div>

            {/* ========== 조도 슬라이더 ========== */}
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label>Light Level</Label>
                <span className="text-sm font-medium text-primary">
                  {simValues.light}
                </span>
              </div>
              <Slider
                value={[simValues.light]}
                min={0}       // 완전 어둠
                max={1023}    // 10비트 ADC 최대값
                step={1}
                onValueChange={(value) => setSimValues((prev) => ({ ...prev, light: value[0] }))}
                onValueCommit={(value) => handleSimValueChange('light', value[0])}
              />
            </div>

            {/* ========== 모션 감지 스위치 ========== */}
            <div className="flex items-center justify-between">
              <div>
                <Label>Motion Detected</Label>
                <p className="text-sm text-muted-foreground">
                  Simulate PIR sensor motion
                </p>
              </div>
              <Switch
                checked={simValues.motion}
                onCheckedChange={(checked) => handleSimValueChange('motion', checked)}
              />
            </div>

            {/* ========== 버튼 시뮬레이션 ========== */}
            {/*
              [border-t]
              상단 테두리로 섹션 구분
            */}
            <div className="pt-4 border-t">
              <Label className="block mb-3">Simulate Button Press</Label>
              <div className="flex gap-2">
                {/*
                  [배열 매핑]
                  [0, 1, 2, 3].map()으로 4개 버튼 생성
                */}
                {[0, 1, 2, 3].map((index) => (
                  <Button
                    key={index}
                    variant="secondary"
                    size="sm"
                    onClick={() => handleSimulateButton(index)}
                    disabled={loading}
                    className="flex-1"  // 균등 너비
                  >
                    BTN {index + 1}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ==================== 시스템 구성 ==================== */}
      <Card>
        <CardHeader>
          <CardTitle>
            <Cpu className="w-5 h-5 text-purple-500" />
            System Configuration
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/*
            [2열 그리드]
            시스템 정보를 좌우 2열로 표시
          */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

            {/* 왼쪽 열 */}
            <div className="space-y-4">
              {/* 모드 (Simulation/Hardware) */}
              <div className="p-4 bg-muted/50 rounded-lg">
                <Label className="text-muted-foreground">Mode</Label>
                {/*
                  [조건부 텍스트 색상]
                  시뮬레이션: 노란색
                  하드웨어: 초록색
                */}
                <p className={cn(
                  'text-lg font-medium',
                  config?.simulation_mode ? 'text-yellow-600 dark:text-yellow-400' : 'text-green-600 dark:text-green-400'
                )}>
                  {config?.simulation_mode ? 'Simulation' : 'Hardware'}
                </p>
              </div>

              {/* 플랫폼 정보 */}
              <div className="p-4 bg-muted/50 rounded-lg">
                <Label className="text-muted-foreground">Platform</Label>
                <p className="text-lg font-medium">
                  {/*
                    [선택적 체이닝과 괄호]
                    config?.platform.system: OS 이름 (Linux, Windows 등)
                    config?.platform.machine: 아키텍처 (aarch64, x86_64 등)
                  */}
                  {config?.platform.system} ({config?.platform.machine})
                </p>
              </div>

              {/* Raspberry Pi 여부 */}
              <div className="p-4 bg-muted/50 rounded-lg">
                <Label className="text-muted-foreground">Raspberry Pi</Label>
                <p className={cn(
                  'text-lg font-medium',
                  config?.platform.is_raspberry_pi ? 'text-green-600 dark:text-green-400' : 'text-muted-foreground'
                )}>
                  {config?.platform.is_raspberry_pi ? 'Yes' : 'No'}
                </p>
              </div>
            </div>

            {/* 오른쪽 열 */}
            <div className="space-y-4">
              {/* 업데이트 인터벌 */}
              <div className="p-4 bg-muted/50 rounded-lg">
                <Label className="text-muted-foreground">Update Interval</Label>
                <p className="text-lg font-medium">
                  {/*
                    [Nullish coalescing (??)]
                    값이 없으면 기본값 0.5 사용
                  */}
                  {config?.hardware_update_interval ?? 0.5}s
                </p>
              </div>

              {/* 로그 인터벌 */}
              <div className="p-4 bg-muted/50 rounded-lg">
                <Label className="text-muted-foreground">Log Interval</Label>
                <p className="text-lg font-medium">
                  {config?.data_log_interval ?? 5}s
                </p>
              </div>

              {/* 데이터 보존 기간 */}
              <div className="p-4 bg-muted/50 rounded-lg">
                <Label className="text-muted-foreground">Data Retention</Label>
                <p className="text-lg font-medium">
                  {config?.data_retention_days ?? 30} days
                </p>
              </div>
            </div>
          </div>

          {/* 설정 새로고침 버튼 */}
          <Button
            onClick={handleRefreshConfig}
            disabled={loading}
            className="mt-6"
          >
            {/*
              [조건부 애니메이션]
              로딩 중이면 아이콘 회전
            */}
            <RefreshCw className={cn('w-4 h-4 mr-2', loading && 'animate-spin')} />
            Refresh Configuration
          </Button>
        </CardContent>
      </Card>

      {/* ==================== 앱 정보 ==================== */}
      <Card>
        <CardHeader>
          <CardTitle>
            <Info className="w-5 h-5 text-blue-500" />
            About
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {/* 프로젝트 제목 */}
            <p className="text-sm">
              <strong>Raspberry Pi HMI System</strong>
            </p>
            {/* 프로젝트 설명 */}
            <p className="text-sm text-muted-foreground">
              A comprehensive Human-Machine Interface for Raspberry Pi with real-time
              hardware monitoring, GPIO control, and sensor data visualization.
            </p>
            {/* 기술 스택 */}
            <p className="text-sm text-muted-foreground mt-4">
              Built with FastAPI (backend) and React + TypeScript (frontend).
            </p>
          </div>
        </CardContent>
      </Card>

      {/* ==================== 데이터베이스 정보 ==================== */}
      <Card>
        <CardHeader>
          <CardTitle>
            <Database className="w-5 h-5 text-green-500" />
            Database
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/*
            [3열 그리드]
            DB 정보를 균등하게 표시
          */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* DB 타입 */}
            <div className="p-4 bg-muted/50 rounded-lg">
              <Label className="text-muted-foreground">Type</Label>
              {/*
                [SQLite WAL 모드]
                Write-Ahead Logging
                동시 읽기/쓰기 성능 향상
                SD 카드 수명 보호
              */}
              <p className="text-lg font-medium">SQLite (WAL mode)</p>
            </div>
            {/* DB 위치 */}
            <div className="p-4 bg-muted/50 rounded-lg">
              <Label className="text-muted-foreground">Location</Label>
              <p className="text-lg font-medium">backend/data/hmi_data.db</p>
            </div>
            {/* 자동 정리 */}
            <div className="p-4 bg-muted/50 rounded-lg">
              <Label className="text-muted-foreground">Auto-cleanup</Label>
              <p className="text-lg font-medium">
                After {config?.data_retention_days ?? 30} days
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
