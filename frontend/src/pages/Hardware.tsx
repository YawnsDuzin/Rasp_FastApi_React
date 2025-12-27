/**
 * Hardware Control Page (하드웨어 제어 페이지)
 * =============================================
 *
 * [한국어 설명]
 * GPIO, PWM, NeoPixel, 디스플레이 등 하드웨어를 제어하는 페이지입니다.
 * 사용자가 LED, 릴레이, 모터, 서보 등을 직접 조작할 수 있습니다.
 *
 * [주요 기능]
 * 1. LED 제어: 개별 ON/OFF, 전체 ON/OFF
 * 2. 릴레이 제어: 개별 ON/OFF
 * 3. 버튼 상태: 읽기 전용 (물리 버튼 상태 표시)
 * 4. PWM 제어: 모터 속도, 서보 각도
 * 5. NeoPixel: 색상 선택, 효과 적용
 * 6. LCD/OLED: 텍스트 출력, 화면 지우기
 *
 * [컴포넌트 구조]
 * Hardware
 *  ├── LED Control Card (LED 제어)
 *  ├── Relay Control Card (릴레이 제어)
 *  ├── Button Status Card (버튼 상태 - 읽기 전용)
 *  ├── Motor Speed Card (모터 속도)
 *  ├── Servo Angle Card (서보 각도)
 *  ├── NeoPixel Card (네오픽셀 LED 스트립)
 *  ├── LCD Control Card (LCD 디스플레이)
 *  └── OLED Info Card (OLED 디스플레이 정보)
 */

// ==================== Imports ====================

// [React useState Hook]
// 로컬 상태 관리를 위한 Hook
// 모터 속도, 서보 각도, 로딩 상태 등을 관리
import { useState } from 'react';

// [Zustand 스토어]
// 전역 상태에서 하드웨어 데이터 읽기
import { useStore } from '../hooks/useStore';

// [API 서비스]
// 하드웨어 제어 REST API 호출
import { hardwareApi } from '../services/api';

// ==================== UI 컴포넌트 Imports ====================

// [shadcn/ui Card 컴포넌트]
// 각 하드웨어 섹션을 카드 형태로 그룹화
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

// [Button 컴포넌트]
// 다양한 액션 버튼 (All On/Off, 서보 각도 프리셋 등)
import { Button } from '@/components/ui/button';

// [Switch 컴포넌트]
// LED, 릴레이 토글용 스위치
// iOS 스타일의 ON/OFF 스위치
import { Switch } from '@/components/ui/switch';

// [Slider 컴포넌트]
// 모터 속도, 서보 각도 조절용 슬라이더
import { Slider } from '@/components/ui/slider';

// [Input 컴포넌트]
// LCD 텍스트 입력 필드
import { Input } from '@/components/ui/input';

// [Label 컴포넌트]
// 입력 필드에 대한 라벨
import { Label } from '@/components/ui/label';

// [Select 컴포넌트]
// LCD 행(Row) 선택용 드롭다운
// 여러 하위 컴포넌트로 구성됨
import {
  Select,          // 전체 선택 컨테이너
  SelectContent,   // 드롭다운 내용
  SelectItem,      // 개별 선택 항목
  SelectTrigger,   // 클릭 가능한 버튼 영역
  SelectValue,     // 현재 선택된 값 표시
} from '@/components/ui/select';

// [cn 유틸리티]
// 조건부 클래스명 병합
import { cn } from '@/lib/utils';

// ==================== 아이콘 Imports ====================
// [Lucide React 아이콘]
// 각 하드웨어 타입을 시각적으로 나타내는 아이콘
import {
  Lightbulb,   // LED 아이콘
  Power,       // 릴레이/전원 아이콘
  Gauge,       // 모터 게이지 아이콘
  RotateCw,    // 서보 회전 아이콘
  Palette,     // NeoPixel 색상 팔레트 아이콘
  CircleDot,   // 버튼 아이콘
  Monitor,     // OLED 모니터 아이콘
  Type,        // LCD 텍스트 아이콘
} from 'lucide-react';


// ==================== 상수 정의 ====================

/**
 * [NEOPIXEL_EFFECTS]
 * NeoPixel LED 스트립에서 사용 가능한 효과 목록
 *
 * [id]: 백엔드 API에 전달되는 효과 식별자
 * [label]: 사용자에게 표시되는 이름
 *
 * [효과 설명]
 * - rainbow: 무지개 색상 순환
 * - breathing: 밝기가 서서히 변화하는 호흡 효과
 * - chase: 불빛이 LED를 따라 이동
 * - sparkle: 반짝이는 효과
 * - wave: 파도처럼 밝기가 변화
 * - fire: 불꽃 효과
 */
const NEOPIXEL_EFFECTS = [
  { id: 'rainbow', label: 'Rainbow' },
  { id: 'breathing', label: 'Breathing' },
  { id: 'chase', label: 'Chase' },
  { id: 'sparkle', label: 'Sparkle' },
  { id: 'wave', label: 'Wave' },
  { id: 'fire', label: 'Fire' },
];

/**
 * [NEOPIXEL_COLORS]
 * NeoPixel에서 선택 가능한 단색 목록
 *
 * [value]: HEX 색상 코드 (#RRGGBB 형식)
 * [name]: 색상 이름 (툴팁에 표시)
 */
const NEOPIXEL_COLORS = [
  { name: 'Red', value: '#FF0000' },
  { name: 'Green', value: '#00FF00' },
  { name: 'Blue', value: '#0000FF' },
  { name: 'Yellow', value: '#FFFF00' },
  { name: 'Cyan', value: '#00FFFF' },
  { name: 'Magenta', value: '#FF00FF' },
  { name: 'White', value: '#FFFFFF' },
  { name: 'Orange', value: '#FFA500' },
];


// ==================== Hardware 컴포넌트 ====================
/**
 * [Hardware 함수형 컴포넌트]
 * 하드웨어 제어 페이지의 메인 컴포넌트
 */
export default function Hardware() {
  // ==================== 상태 관리 ====================

  // [전역 상태에서 하드웨어 데이터 가져오기]
  // WebSocket을 통해 실시간으로 업데이트됨
  const { hardwareData } = useStore();

  // [로컬 상태: 모터 속도]
  // 슬라이더 조작 중 표시할 값
  // API 응답 전까지 UI에 반영
  const [motorSpeed, setMotorSpeed] = useState(0);

  // [로컬 상태: 서보 각도]
  // 0~180도 범위
  const [servoAngle, setServoAngle] = useState(90);

  // [로컬 상태: 로딩 상태]
  // 어떤 버튼/컨트롤이 로딩 중인지 추적
  // 예: 'led-0', 'relay-1', 'neopixel-rainbow' 등
  // null이면 아무것도 로딩 중이 아님
  const [loading, setLoading] = useState<string | null>(null);

  // [로컬 상태: LCD 텍스트]
  // LCD에 표시할 텍스트
  const [lcdText, setLcdText] = useState('');

  // [로컬 상태: LCD 행 번호]
  // '0', '1', '2', '3' 문자열 (Select 값)
  const [lcdRow, setLcdRow] = useState('0');

  // ==================== 데이터 추출 ====================

  /**
   * [구조 분해 할당]
   * hardwareData가 null일 수 있으므로 옵셔널 체이닝 사용
   *
   * [옵셔널 체이닝 (?.)]]
   * hardwareData?.gpio
   * = hardwareData가 있으면 gpio 속성 접근, 없으면 undefined
   */
  const gpio = hardwareData?.gpio;
  const pwm = hardwareData?.pwm;

  // ==================== 이벤트 핸들러 ====================

  /**
   * [LED 토글 핸들러]
   * LED를 켜거나 끄는 함수
   *
   * [async/await]
   * 비동기 API 호출을 동기 코드처럼 작성
   *
   * @param index - LED 인덱스 (0, 1, 2, 3)
   * @param state - 새로운 상태 (true=켜기, false=끄기)
   */
  const handleLedToggle = async (index: number, state: boolean) => {
    // 로딩 상태 설정 (해당 LED 버튼 비활성화)
    setLoading(`led-${index}`);
    try {
      // REST API 호출로 LED 상태 변경
      await hardwareApi.setLed(index, state);
    } catch (error) {
      // 에러 발생 시 콘솔에 출력
      // 실제 앱에서는 사용자에게 알림 표시 권장
      console.error('Failed to set LED:', error);
    }
    // 로딩 상태 해제
    setLoading(null);
  };

  /**
   * [릴레이 토글 핸들러]
   * 릴레이를 켜거나 끄는 함수
   *
   * @param index - 릴레이 인덱스 (0, 1)
   * @param state - 새로운 상태
   */
  const handleRelayToggle = async (index: number, state: boolean) => {
    setLoading(`relay-${index}`);
    try {
      await hardwareApi.setRelay(index, state);
    } catch (error) {
      console.error('Failed to set relay:', error);
    }
    setLoading(null);
  };

  /**
   * [모터 속도 변경 핸들러]
   * PWM을 통해 모터 속도 조절
   *
   * [onValueCommit vs onValueChange]
   * - onValueChange: 슬라이더 드래그 중 계속 호출
   * - onValueCommit: 드래그 완료 후 한 번 호출
   * API는 onValueCommit에서만 호출하여 요청 수를 줄임
   *
   * @param speed - 모터 속도 (0-100%)
   */
  const handleMotorChange = async (speed: number) => {
    // 로컬 상태 먼저 업데이트 (UI 반응성)
    setMotorSpeed(speed);
    try {
      // 백엔드에 속도 전달
      await hardwareApi.setMotorSpeed(speed);
    } catch (error) {
      console.error('Failed to set motor speed:', error);
    }
  };

  /**
   * [서보 각도 변경 핸들러]
   * PWM을 통해 서보 모터 각도 조절
   *
   * @param angle - 서보 각도 (0-180도)
   */
  const handleServoChange = async (angle: number) => {
    setServoAngle(angle);
    try {
      await hardwareApi.setServoAngle(angle);
    } catch (error) {
      console.error('Failed to set servo angle:', error);
    }
  };

  /**
   * [NeoPixel 색상 설정 핸들러]
   * 모든 LED를 동일한 단색으로 설정
   *
   * @param color - HEX 색상 코드 (예: '#FF0000')
   */
  const handleNeopixelColor = async (color: string) => {
    setLoading('neopixel-color');
    try {
      // null은 모든 LED에 적용함을 의미
      await hardwareApi.setNeopixelColor(null, color);
    } catch (error) {
      console.error('Failed to set NeoPixel color:', error);
    }
    setLoading(null);
  };

  /**
   * [NeoPixel 효과 시작 핸들러]
   * 선택한 효과를 LED 스트립에 적용
   *
   * @param effect - 효과 ID (예: 'rainbow', 'breathing')
   */
  const handleNeopixelEffect = async (effect: string) => {
    setLoading(`neopixel-${effect}`);
    try {
      await hardwareApi.startNeopixelEffect(effect);
    } catch (error) {
      console.error('Failed to start effect:', error);
    }
    setLoading(null);
  };

  /**
   * [NeoPixel 초기화 핸들러]
   * 모든 LED를 끔 (검은색으로 설정)
   */
  const handleNeopixelClear = async () => {
    setLoading('neopixel-clear');
    try {
      await hardwareApi.clearNeopixel();
    } catch (error) {
      console.error('Failed to clear NeoPixel:', error);
    }
    setLoading(null);
  };

  /**
   * [LCD 쓰기 핸들러]
   * LCD 디스플레이에 텍스트 출력
   */
  const handleLcdWrite = async () => {
    // 빈 텍스트면 무시
    // trim(): 앞뒤 공백 제거
    if (!lcdText.trim()) return;

    setLoading('lcd-write');
    try {
      // parseInt: 문자열을 정수로 변환
      // lcdRow는 '0', '1' 등의 문자열
      await hardwareApi.writeLcd(lcdText, parseInt(lcdRow));
      // 성공 시 입력 필드 초기화
      setLcdText('');
    } catch (error) {
      console.error('Failed to write LCD:', error);
    }
    setLoading(null);
  };

  /**
   * [LCD 지우기 핸들러]
   * LCD 화면 전체 지우기
   */
  const handleLcdClear = async () => {
    setLoading('lcd-clear');
    try {
      await hardwareApi.clearLcd();
    } catch (error) {
      console.error('Failed to clear LCD:', error);
    }
    setLoading(null);
  };

  // ==================== JSX 반환 ====================
  return (
    // [전체 컨테이너]
    // space-y-6: 자식 요소들 사이에 1.5rem(24px) 간격
    <div className="space-y-6">

      {/* ==================== GPIO 제어 영역 ==================== */}
      {/*
        [그리드 레이아웃]
        grid-cols-1: 모바일에서 1열
        md:grid-cols-2: 태블릿 이상에서 2열
        gap-6: 그리드 아이템 간 1.5rem 간격
      */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* ========== LED 제어 카드 ========== */}
        <Card>
          <CardHeader>
            <CardTitle>
              {/* LED 아이콘 (노란색) */}
              <Lightbulb className="w-5 h-5 text-yellow-500" />
              LED Control
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/*
              [LED 목록 렌더링]
              Object.entries(): 객체를 [키, 값] 배열로 변환
              gpio.leds = { 0: true, 1: false, ... }
              → [['0', true], ['1', false], ...]
            */}
            {gpio &&
              Object.entries(gpio.leds).map(([index, state]) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
                >
                  {/* LED 상태 표시 (왼쪽) */}
                  <div className="flex items-center gap-3">
                    {/*
                      [LED 인디케이터]
                      상태에 따라 색상과 그림자 변경
                      - 켜짐: 노란색 + 노란 그림자
                      - 꺼짐: 회색
                    */}
                    <div
                      className={cn(
                        'w-4 h-4 rounded-full transition-all duration-300',
                        state
                          ? 'bg-yellow-400 shadow-md shadow-yellow-400/50'
                          : 'bg-muted-foreground/30'
                      )}
                    />
                    <span className="font-medium">
                      {/* parseInt로 숫자 변환 후 +1 (1-based 표시) */}
                      LED {parseInt(index) + 1}
                    </span>
                  </div>

                  {/* LED 토글 스위치 (오른쪽) */}
                  {/*
                    [Switch 컴포넌트]
                    checked: 현재 상태
                    onCheckedChange: 상태 변경 시 콜백
                    disabled: 로딩 중이면 비활성화
                  */}
                  <Switch
                    checked={state}
                    onCheckedChange={(newState) => handleLedToggle(parseInt(index), newState)}
                    disabled={loading === `led-${index}`}
                  />
                </div>
              ))}

            {/* 전체 ON/OFF 버튼 */}
            {/*
              [조건부 렌더링]
              LED가 있을 때만 버튼 표시
              Object.keys(): 객체의 키 배열 반환
            */}
            {gpio && Object.keys(gpio.leds).length > 0 && (
              <div className="flex gap-2 mt-4">
                {/* All On 버튼 */}
                <Button
                  onClick={() => hardwareApi.setAllLeds(true)}
                  className="flex-1"  // 남은 공간 균등 분배
                >
                  All On
                </Button>
                {/* All Off 버튼 */}
                <Button
                  variant="secondary"  // 보조 버튼 스타일
                  onClick={() => hardwareApi.setAllLeds(false)}
                  className="flex-1"
                >
                  All Off
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* ========== 릴레이 제어 카드 ========== */}
        <Card>
          <CardHeader>
            <CardTitle>
              <Power className="w-5 h-5 text-green-500" />
              Relay Control
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 릴레이 목록 렌더링 (LED와 유사한 구조) */}
            {gpio &&
              Object.entries(gpio.relays).map(([index, state]) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-muted/50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    {/*
                      [아이콘 색상 변경]
                      상태에 따라 Power 아이콘 색상 변경
                    */}
                    <Power
                      className={cn(
                        'w-5 h-5 transition-colors',
                        state ? 'text-green-500' : 'text-muted-foreground'
                      )}
                    />
                    <span className="font-medium">
                      Relay {parseInt(index) + 1}
                    </span>
                  </div>
                  <Switch
                    checked={state}
                    onCheckedChange={(newState) => handleRelayToggle(parseInt(index), newState)}
                    disabled={loading === `relay-${index}`}
                  />
                </div>
              ))}
          </CardContent>
        </Card>
      </div>

      {/* ==================== 버튼 상태 (읽기 전용) ==================== */}
      <Card>
        <CardHeader>
          <CardTitle>
            <CircleDot className="w-5 h-5 text-blue-500" />
            Button Status
            {/* 읽기 전용임을 나타내는 태그 */}
            <span className="ml-2 text-xs font-normal text-muted-foreground">(Read-only)</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/*
            [반응형 그리드]
            모바일: 2열, 태블릿 이상: 4열
          */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {gpio &&
              Object.entries(gpio.buttons).map(([index, state]) => (
                <div
                  key={index}
                  className={cn(
                    'flex flex-col items-center p-4 rounded-lg transition-all duration-300',
                    // 눌린 상태: 파란색 배경 + 테두리
                    state
                      ? 'bg-blue-100 dark:bg-blue-900/40 ring-2 ring-blue-500'
                      : 'bg-muted/50'
                  )}
                >
                  {/* 버튼 아이콘 원형 */}
                  <div
                    className={cn(
                      'w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300',
                      state
                        ? 'bg-blue-500 shadow-lg shadow-blue-500/50'
                        : 'bg-muted'
                    )}
                  >
                    <CircleDot
                      className={cn(
                        'w-6 h-6',
                        state ? 'text-white' : 'text-muted-foreground'
                      )}
                    />
                  </div>
                  {/* 버튼 번호 */}
                  <span className="mt-2 font-medium">
                    Button {parseInt(index) + 1}
                  </span>
                  {/* 상태 텍스트 */}
                  <span
                    className={cn(
                      'text-xs mt-1',
                      state ? 'text-blue-600 dark:text-blue-400' : 'text-muted-foreground'
                    )}
                  >
                    {state ? 'Pressed' : 'Released'}
                  </span>
                </div>
              ))}
          </div>
        </CardContent>
      </Card>

      {/* ==================== PWM 제어 영역 ==================== */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* ========== 모터 속도 제어 ========== */}
        <Card>
          <CardHeader>
            <CardTitle>
              <Gauge className="w-5 h-5 text-blue-500" />
              Motor Speed Control
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              {/* 레이블과 현재 값 */}
              <div className="flex justify-between">
                <Label>Speed</Label>
                <span className="text-sm font-medium text-primary">
                  {/*
                    [Nullish coalescing 연산자 (??)]
                    pwm?.motor_speed ?? motorSpeed
                    = pwm.motor_speed가 있으면 그 값, 없으면 로컬 motorSpeed
                  */}
                  {pwm?.motor_speed ?? motorSpeed}%
                </span>
              </div>

              {/*
                [Slider 컴포넌트]
                value: 배열 형태로 전달 [현재값]
                min/max: 범위 설정
                step: 증가 단위
                onValueChange: 드래그 중 계속 호출 (UI 업데이트)
                onValueCommit: 드래그 완료 시 호출 (API 호출)
              */}
              <Slider
                value={[pwm?.motor_speed ?? motorSpeed]}
                min={0}
                max={100}
                step={1}
                onValueChange={(value) => setMotorSpeed(value[0])}
                onValueCommit={(value) => handleMotorChange(value[0])}
              />

              {/* 범위 표시 */}
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>0</span>
                <span>100</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* ========== 서보 각도 제어 ========== */}
        <Card>
          <CardHeader>
            <CardTitle>
              <RotateCw className="w-5 h-5 text-purple-500" />
              Servo Angle Control
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label>Angle</Label>
                <span className="text-sm font-medium text-primary">
                  {pwm?.servo_angle ?? servoAngle}°
                </span>
              </div>
              <Slider
                value={[pwm?.servo_angle ?? servoAngle]}
                min={0}
                max={180}
                step={1}
                onValueChange={(value) => setServoAngle(value[0])}
                onValueCommit={(value) => handleServoChange(value[0])}
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>0</span>
                <span>180</span>
              </div>
            </div>

            {/* 프리셋 각도 버튼 */}
            {/*
              [빠른 설정 버튼]
              0°, 90°, 180°로 즉시 이동
            */}
            <div className="flex justify-between mt-4">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => handleServoChange(0)}
              >
                0°
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => handleServoChange(90)}
              >
                90°
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => handleServoChange(180)}
              >
                180°
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ==================== NeoPixel 제어 ==================== */}
      <Card>
        <CardHeader>
          <CardTitle>
            <Palette className="w-5 h-5 text-pink-500" />
            NeoPixel LED Strip
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

            {/* 색상 선택 영역 */}
            <div>
              <h4 className="text-sm font-medium mb-3">
                Solid Colors
              </h4>
              {/*
                [색상 버튼 그리드]
                4열 그리드로 색상 버튼 배치
              */}
              <div className="grid grid-cols-4 gap-2">
                {NEOPIXEL_COLORS.map((color) => (
                  <button
                    key={color.name}
                    onClick={() => handleNeopixelColor(color.value)}
                    className={cn(
                      'w-full aspect-square rounded-lg transition-transform hover:scale-105',
                      loading === 'neopixel-color' && 'opacity-50'
                    )}
                    // [인라인 스타일]
                    // 동적 색상은 Tailwind 클래스로 불가능하므로 style 사용
                    style={{ backgroundColor: color.value }}
                    title={color.name}  // 마우스 호버 시 툴팁
                  />
                ))}
              </div>
            </div>

            {/* 효과 선택 영역 */}
            <div>
              <h4 className="text-sm font-medium mb-3">
                Effects
              </h4>
              <div className="grid grid-cols-2 gap-2">
                {NEOPIXEL_EFFECTS.map((effect) => (
                  <Button
                    key={effect.id}
                    variant="secondary"
                    size="sm"
                    onClick={() => handleNeopixelEffect(effect.id)}
                    disabled={loading === `neopixel-${effect.id}`}
                  >
                    {effect.label}
                  </Button>
                ))}
              </div>

              {/* 전체 끄기 버튼 */}
              <Button
                variant="destructive"  // 빨간색 버튼 (위험/삭제 액션)
                className="w-full mt-4"
                onClick={handleNeopixelClear}
                disabled={loading === 'neopixel-clear'}
              >
                Clear All
              </Button>
            </div>
          </div>

          {/* LED 미리보기 */}
          <div className="mt-6 pt-6 border-t">
            <h4 className="text-sm font-medium mb-3">
              LED Preview
            </h4>
            {/*
              [LED 프리뷰]
              각 NeoPixel LED의 현재 색상을 원형으로 표시
            */}
            <div className="flex gap-2 justify-center">
              {hardwareData?.neopixel.colors.map((led, index) => (
                <div
                  key={index}
                  className="w-8 h-8 rounded-full border-2 border-muted transition-all duration-300"
                  style={{
                    backgroundColor: led.color,
                    // [조건부 boxShadow]
                    // 검은색(꺼짐)이 아닐 때만 글로우 효과
                    boxShadow:
                      led.color !== '#000000' ? `0 0 10px ${led.color}` : 'none',
                  }}
                  title={`LED ${index + 1}: ${led.color}`}
                />
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ==================== 디스플레이 제어 ==================== */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* ========== LCD 제어 ========== */}
        <Card>
          <CardHeader>
            <CardTitle>
              <Type className="w-5 h-5 text-teal-500" />
              LCD Display (1602/2004)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* 텍스트 입력 */}
            <div className="space-y-2">
              {/*
                [htmlFor 속성]
                Label 클릭 시 해당 Input에 포커스
                접근성(a11y) 향상
              */}
              <Label htmlFor="lcd-text">Text to Display</Label>
              <Input
                id="lcd-text"
                value={lcdText}
                onChange={(e) => setLcdText(e.target.value)}
                placeholder="Enter text..."
                maxLength={20}  // LCD 한 줄 최대 글자 수
              />
            </div>

            {/* 행 선택 */}
            <div className="space-y-2">
              <Label>Row</Label>
              {/*
                [Select 컴포넌트]
                드롭다운 선택 UI
              */}
              <Select value={lcdRow} onValueChange={setLcdRow}>
                <SelectTrigger>
                  <SelectValue placeholder="Select row" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="0">Row 1</SelectItem>
                  <SelectItem value="1">Row 2</SelectItem>
                  <SelectItem value="2">Row 3</SelectItem>
                  <SelectItem value="3">Row 4</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* 액션 버튼 */}
            <div className="flex gap-2">
              <Button
                onClick={handleLcdWrite}
                // 로딩 중이거나 텍스트가 비어있으면 비활성화
                disabled={loading === 'lcd-write' || !lcdText.trim()}
                className="flex-1"
              >
                Write
              </Button>
              <Button
                variant="secondary"
                onClick={handleLcdClear}
                disabled={loading === 'lcd-clear'}
                className="flex-1"
              >
                Clear
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* ========== OLED 정보 ========== */}
        <Card>
          <CardHeader>
            <CardTitle>
              <Monitor className="w-5 h-5 text-indigo-500" />
              OLED Display (SSD1306)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* OLED 시뮬레이션 화면 */}
            {/*
              [aspect-ratio]
              aspect-[2/1]: 너비:높이 = 2:1 비율 유지
            */}
            <div className="p-4 bg-gray-900 rounded-lg aspect-[2/1] flex items-center justify-center">
              <div className="text-center">
                <Monitor className="w-12 h-12 text-indigo-400 mx-auto mb-2" />
                <p className="text-indigo-400 text-sm">128 x 64 pixels</p>
              </div>
            </div>
            <p className="text-sm text-muted-foreground">
              OLED display shows system status and sensor readings automatically.
              Use LCD controls above to write custom text.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
