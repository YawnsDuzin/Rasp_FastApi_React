"""
PWM Controller (PWM 컨트롤러)
=============================

[한국어 설명]
PWM(Pulse Width Modulation, 펄스 폭 변조)을 제어하는 모듈입니다.

PWM이란?
- 디지털 신호의 ON/OFF 비율(듀티 사이클)을 조절하여
  아날로그와 유사한 효과를 내는 기술
- 라즈베리 파이의 GPIO는 디지털(0 or 1)만 출력 가능
- PWM을 사용하면 모터 속도, LED 밝기 등을 제어 가능

PWM 파형 예시:
    주기 (Period) = 1/주파수
    ┌────┐    ┌────┐    ┌────┐
    │    │    │    │    │    │
────┘    └────┘    └────┘    └────
    ←──────────────────────────→
           전체 주기 (Period)
    ←────→
    ON 시간 (Pulse Width)

듀티 사이클 (Duty Cycle):
- ON 시간 / 전체 주기 × 100%
- 0%: 항상 OFF (0V)
- 50%: 절반 ON, 절반 OFF
- 100%: 항상 ON (3.3V)

이 모듈에서 제어하는 장치:
1. **DC 모터** (Motor): 속도 제어
2. **서보 모터** (Servo): 각도 제어 (0~180도)
3. **LED 디머** (Dimmer): 밝기 제어

[English Description]
Controls PWM outputs for motors, servos, and dimmers.
Supports both hardware PWM and software PWM.
"""

# ============================================================================
# 라이브러리 임포트 (Import Libraries)
# ============================================================================

# asyncio: 비동기 프로그래밍 모듈
import asyncio

# typing: 타입 힌트용 모듈
from typing import Dict, Optional, Any

# dataclasses: 데이터 클래스 정의
from dataclasses import dataclass

# enum: 열거형 정의
from enum import Enum

# 베이스 클래스와 시뮬레이션 믹스인 임포트
from .base import BaseHardwareController, SimulationMixin

# 설정 값 가져오기 (PWM 핀 번호 등)
from app.core.config import settings

# 로거 가져오기
from app.core.logging_config import get_logger

# 이 모듈용 로거 생성
logger = get_logger(__name__)


# ============================================================================
# PWM 채널 열거형 (PWM Channel Enum)
# ============================================================================

class PWMChannel(Enum):
    """
    PWM 채널 타입 (PWM Channel Types)

    [한국어 설명]
    PWM을 사용하는 장치의 종류를 정의합니다.

    각 타입별 특성:
    - MOTOR: DC 모터 속도 제어
        - 주파수: 1kHz~20kHz (높을수록 조용함)
        - 듀티 사이클: 0~100% (속도)

    - SERVO: 서보 모터 각도 제어
        - 주파수: 50Hz (표준)
        - 듀티 사이클: 2.5%~12.5% (0~180도)

    - DIMMER: LED 밝기 제어
        - 주파수: 100Hz~1kHz
        - 듀티 사이클: 0~100% (밝기)
    """
    MOTOR = "motor"      # DC 모터 (속도 제어)
    SERVO = "servo"      # 서보 모터 (각도 제어)
    DIMMER = "dimmer"    # LED 디머 (밝기 제어)


# ============================================================================
# PWM 출력 데이터 클래스 (PWM Output Dataclass)
# ============================================================================

@dataclass
class PWMOutput:
    """
    PWM 출력 설정 정보 (PWM Output Configuration)

    [한국어 설명]
    각 PWM 출력의 설정과 현재 상태를 저장합니다.

    Attributes:
        pin: GPIO 핀 번호
        channel_type: 채널 타입 (MOTOR/SERVO/DIMMER)
        frequency: PWM 주파수 (Hz)
            - 모터: 1000Hz (1kHz)
            - 서보: 50Hz
        duty_cycle: 현재 듀티 사이클 (0-100%)
        min_duty: 최소 듀티 사이클 (서보: 2.5%)
        max_duty: 최대 듀티 사이클 (서보: 12.5%)
        is_running: PWM 출력 활성화 여부
    """
    pin: int                           # GPIO 핀 번호
    channel_type: PWMChannel           # 채널 타입
    frequency: float                   # 주파수 (Hz)
    duty_cycle: float                  # 듀티 사이클 (0-100%)
    min_duty: float = 0.0              # 최소 듀티 사이클
    max_duty: float = 100.0            # 최대 듀티 사이클
    is_running: bool = False           # 실행 중 여부


# ============================================================================
# PWM 컨트롤러 클래스 (PWM Controller Class)
# ============================================================================

class PWMController(BaseHardwareController, SimulationMixin):
    """
    PWM 작업을 위한 컨트롤러 (Controller for PWM Operations)

    [한국어 설명]
    DC 모터와 서보 모터를 제어합니다.

    하드웨어 PWM vs 소프트웨어 PWM:
    - 하드웨어 PWM: GPIO 12, 13, 18, 19에서만 지원
        - 더 정밀하고 CPU 부하 없음
        - 핀 수가 제한됨
    - 소프트웨어 PWM: 모든 GPIO에서 사용 가능
        - CPU 부하 있음
        - 정밀도가 떨어짐

    라즈베리 파이 PWM 핀 (하드웨어):
    - PWM0: GPIO 12, 18
    - PWM1: GPIO 13, 19

    서보 모터 제어 원리:
    - 50Hz (20ms 주기) 신호 사용
    - 펄스 폭에 따라 각도 결정:
        - 1ms (5%): 0도
        - 1.5ms (7.5%): 90도
        - 2ms (10%): 180도

    사용 예시:
        controller = PWMController(simulation_mode=True)
        await controller.initialize()

        await controller.set_motor_speed(50)    # 모터 50% 속도
        await controller.set_servo_angle(90)    # 서보 90도

        await controller.cleanup()
    """

    def __init__(self, simulation_mode: bool = False):
        """
        생성자 (Constructor)

        Args:
            simulation_mode: 시뮬레이션 모드 여부
        """
        # 부모 클래스 초기화
        super().__init__("PWM Controller", simulation_mode)

        # PWM 출력 저장 {핀번호: PWMOutput 객체}
        self._outputs: Dict[int, PWMOutput] = {}

        # 실제 PWM 인스턴스 저장 {핀번호: GPIO.PWM 객체}
        self._pwm_instances: Dict[int, Any] = {}

        # RPi.GPIO 모듈 참조
        self._gpio = None

        # 설정에서 핀 번호 가져오기
        self._pwm_pin = settings.GPIO_PWM_PIN      # DC 모터용 핀 (예: 18)
        self._servo_pin = settings.GPIO_SERVO_PIN  # 서보 모터용 핀 (예: 12)

    async def _do_initialize(self) -> bool:
        """
        PWM 하드웨어 초기화 (Initialize PWM Hardware)

        [한국어 설명]
        PWM 핀을 초기화하고 기본 설정을 적용합니다.

        초기화 순서:
        1. RPi.GPIO 라이브러리 로드
        2. BCM 모드 설정
        3. 모터용 PWM 설정 (1kHz)
        4. 서보용 PWM 설정 (50Hz)

        Returns:
            True: 초기화 성공
            False: 초기화 실패
        """
        try:
            # 시뮬레이션 모드가 아닐 때만 실제 GPIO 로드
            if not self.simulation_mode:
                try:
                    import RPi.GPIO as GPIO
                    self._gpio = GPIO

                    # BCM 모드 설정 (이미 설정되어 있어도 OK)
                    GPIO.setmode(GPIO.BCM)
                    GPIO.setwarnings(False)

                except ImportError:
                    logger.warning("RPi.GPIO not available, falling back to simulation")
                    self.simulation_mode = True

            # 기본 PWM 출력 설정
            # 모터: 1kHz (1000Hz) - 모터 제어에 적합
            await self._setup_pwm(self._pwm_pin, PWMChannel.MOTOR, 1000)

            # 서보: 50Hz - 서보 모터 표준 주파수
            await self._setup_pwm(self._servo_pin, PWMChannel.SERVO, 50)

            return True

        except Exception as e:
            logger.error(f"PWM initialization failed: {e}")
            return False

    async def _do_cleanup(self) -> None:
        """
        PWM 리소스 정리 (Clean up PWM Resources)

        [한국어 설명]
        모든 PWM 출력을 중지하고 리소스를 해제합니다.
        """
        # 모든 PWM 인스턴스 중지
        for pin, pwm in self._pwm_instances.items():
            try:
                if not self.simulation_mode and pwm:
                    # PWM 출력 중지
                    pwm.stop()
            except Exception as e:
                logger.error(f"Failed to stop PWM on pin {pin}: {e}")

        # 데이터 구조 초기화
        self._pwm_instances.clear()
        self._outputs.clear()

    async def _setup_pwm(self, pin: int, channel_type: PWMChannel, frequency: float) -> None:
        """
        PWM 출력 설정 (Setup a PWM Output)

        [한국어 설명]
        개별 PWM 핀을 설정합니다.

        Args:
            pin: GPIO 핀 번호
            channel_type: 채널 타입 (MOTOR/SERVO/DIMMER)
            frequency: PWM 주파수 (Hz)
        """
        # PWMOutput 객체 생성
        output = PWMOutput(
            pin=pin,
            channel_type=channel_type,
            frequency=frequency,
            duty_cycle=0.0
        )

        # 서보 모터는 듀티 사이클 범위가 제한됨
        if channel_type == PWMChannel.SERVO:
            # 서보 모터 듀티 사이클 범위:
            # 2.5% = 0도 (약 0.5ms 펄스)
            # 12.5% = 180도 (약 2.5ms 펄스)
            output.min_duty = 2.5
            output.max_duty = 12.5

        # 출력 저장
        self._outputs[pin] = output

        # 실제 하드웨어일 때 GPIO 설정
        if not self.simulation_mode and self._gpio:
            # 핀을 출력으로 설정
            self._gpio.setup(pin, self._gpio.OUT)

            # PWM 객체 생성 (핀, 주파수)
            # GPIO.PWM(pin, frequency): PWM 인스턴스 생성
            pwm = self._gpio.PWM(pin, frequency)
            self._pwm_instances[pin] = pwm

        logger.debug(f"Setup PWM on pin {pin}: {channel_type.value} @ {frequency}Hz")

    # ==================== 모터 제어 (Motor Control) ====================

    async def set_motor_speed(self, speed: float) -> bool:
        """
        모터 속도 설정 (Set Motor Speed)

        [한국어 설명]
        DC 모터의 속도를 제어합니다.

        듀티 사이클과 모터 속도:
        - 0%: 정지
        - 50%: 절반 속도
        - 100%: 최대 속도

        주의사항:
        - 이 구현은 속도만 제어 (방향 제어 없음)
        - 양방향 제어를 위해서는 H-브리지 모터 드라이버 필요
        - 예: L298N, L293D, DRV8833 등

        Args:
            speed: 속도 백분율
                - 이 구현에서는 음수를 절대값으로 변환
                - -100 ~ 100 입력 → 0 ~ 100 사용

        Returns:
            True: 성공
            False: 실패

        사용 예시:
            await controller.set_motor_speed(50)   # 50% 속도
            await controller.set_motor_speed(100)  # 최대 속도
            await controller.set_motor_speed(0)    # 정지
        """
        # 속도를 0~100 범위로 제한
        # abs(): 절대값 (음수 → 양수)
        # max(0, min(100, x)): 0~100 범위로 클램핑
        speed = max(0, min(100, abs(speed)))

        # 듀티 사이클 설정
        return await self.set_duty_cycle(self._pwm_pin, speed)

    def get_motor_speed(self) -> float:
        """
        현재 모터 속도 조회 (Get Current Motor Speed)

        Returns:
            현재 모터 속도 (0-100%)
        """
        if self._pwm_pin in self._outputs:
            return self._outputs[self._pwm_pin].duty_cycle
        return 0.0

    # ==================== 서보 제어 (Servo Control) ====================

    async def set_servo_angle(self, angle: float) -> bool:
        """
        서보 각도 설정 (Set Servo Angle)

        [한국어 설명]
        서보 모터의 각도를 제어합니다 (0~180도).

        서보 모터 동작 원리:
        - 50Hz (20ms 주기) PWM 신호 사용
        - 펄스 폭에 따라 각도 결정

        각도-듀티 사이클 변환:
        - 0도: 2.5% 듀티 (0.5ms 펄스)
        - 90도: 7.5% 듀티 (1.5ms 펄스)
        - 180도: 12.5% 듀티 (2.5ms 펄스)

        변환 공식:
        duty_cycle = min_duty + (angle / 180) * (max_duty - min_duty)
        duty_cycle = 2.5 + (angle / 180) * (12.5 - 2.5)
        duty_cycle = 2.5 + (angle / 180) * 10

        Args:
            angle: 각도 (0-180도)

        Returns:
            True: 성공
            False: 실패

        사용 예시:
            await controller.set_servo_angle(0)    # 0도
            await controller.set_servo_angle(90)   # 90도 (중앙)
            await controller.set_servo_angle(180)  # 180도
        """
        # 각도를 0~180 범위로 제한
        angle = max(0, min(180, angle))

        # 서보 출력 가져오기
        output = self._outputs.get(self._servo_pin)

        if not output:
            logger.error("Servo not configured")
            return False

        # 각도를 듀티 사이클로 변환
        # 선형 보간(linear interpolation) 사용
        # 0도 → min_duty (2.5%)
        # 180도 → max_duty (12.5%)
        duty_cycle = output.min_duty + (angle / 180.0) * (output.max_duty - output.min_duty)

        return await self.set_duty_cycle(self._servo_pin, duty_cycle)

    def get_servo_angle(self) -> float:
        """
        현재 서보 각도 조회 (Get Current Servo Angle)

        [한국어 설명]
        듀티 사이클을 각도로 역변환하여 반환합니다.

        Returns:
            현재 서보 각도 (0-180도)
        """
        output = self._outputs.get(self._servo_pin)
        if not output:
            return 0.0

        # 듀티 사이클을 각도로 역변환
        # 역변환 공식:
        # angle = (duty_cycle - min_duty) / (max_duty - min_duty) * 180
        duty_range = output.max_duty - output.min_duty
        angle = (output.duty_cycle - output.min_duty) / duty_range * 180.0

        # 0~180 범위로 클램핑
        return max(0, min(180, angle))

    # ==================== 일반 PWM 제어 (Generic PWM Control) ====================

    async def set_duty_cycle(self, pin: int, duty_cycle: float) -> bool:
        """
        PWM 듀티 사이클 설정 (Set PWM Duty Cycle)

        [한국어 설명]
        지정된 핀의 PWM 듀티 사이클을 설정합니다.

        PWM 시작/변경 로직:
        - 처음 호출: pwm.start(duty_cycle)로 시작
        - 이후 호출: pwm.ChangeDutyCycle(duty_cycle)로 변경

        Args:
            pin: GPIO 핀 번호
            duty_cycle: 듀티 사이클 (0-100%)

        Returns:
            True: 성공
            False: 실패
        """
        # 핀이 설정되어 있는지 확인
        if pin not in self._outputs:
            logger.error(f"PWM pin {pin} not configured")
            return False

        # 듀티 사이클을 0~100 범위로 제한
        duty_cycle = max(0, min(100, duty_cycle))

        try:
            output = self._outputs[pin]

            if self.simulation_mode:
                # 시뮬레이션: 가상 지연만 추가
                await asyncio.sleep(self._simulate_delay())
            else:
                # 실제 하드웨어: PWM 제어
                pwm = self._pwm_instances.get(pin)
                if pwm:
                    if not output.is_running:
                        # 첫 실행: PWM 시작
                        # start(duty_cycle): 지정된 듀티 사이클로 PWM 시작
                        pwm.start(duty_cycle)
                        output.is_running = True
                    else:
                        # 이미 실행 중: 듀티 사이클만 변경
                        # ChangeDutyCycle(duty_cycle): 듀티 사이클 변경
                        pwm.ChangeDutyCycle(duty_cycle)

            # 내부 상태 업데이트
            output.duty_cycle = duty_cycle
            self._update_timestamp()
            logger.debug(f"Set PWM pin {pin} duty cycle to {duty_cycle}%")
            return True

        except Exception as e:
            logger.error(f"Failed to set PWM duty cycle: {e}")
            return False

    async def set_frequency(self, pin: int, frequency: float) -> bool:
        """
        PWM 주파수 설정 (Set PWM Frequency)

        [한국어 설명]
        PWM 신호의 주파수를 변경합니다.

        주의사항:
        - 서보 모터는 50Hz 유지 필요
        - 모터는 청각 범위 밖 (>20kHz) 권장

        Args:
            pin: GPIO 핀 번호
            frequency: 주파수 (Hz)

        Returns:
            True: 성공
            False: 실패
        """
        if pin not in self._outputs:
            return False

        try:
            if not self.simulation_mode:
                pwm = self._pwm_instances.get(pin)
                if pwm:
                    # ChangeFrequency(freq): 주파수 변경
                    pwm.ChangeFrequency(frequency)

            # 내부 상태 업데이트
            self._outputs[pin].frequency = frequency
            return True

        except Exception as e:
            logger.error(f"Failed to set PWM frequency: {e}")
            return False

    async def stop_pwm(self, pin: int) -> bool:
        """
        PWM 출력 중지 (Stop PWM Output)

        [한국어 설명]
        지정된 핀의 PWM 출력을 중지합니다.
        모터 정지, 서보 해제 등에 사용합니다.

        Args:
            pin: GPIO 핀 번호

        Returns:
            True: 성공
            False: 실패
        """
        if pin not in self._outputs:
            return False

        try:
            if not self.simulation_mode:
                pwm = self._pwm_instances.get(pin)
                if pwm:
                    # stop(): PWM 출력 중지
                    pwm.stop()

            # 상태 업데이트
            self._outputs[pin].is_running = False
            self._outputs[pin].duty_cycle = 0
            return True

        except Exception as e:
            logger.error(f"Failed to stop PWM: {e}")
            return False

    def get_pwm_states(self) -> Dict[int, Dict[str, Any]]:
        """
        모든 PWM 출력 상태 조회 (Get All PWM Output States)

        Returns:
            {핀번호: 상태정보} 딕셔너리
        """
        return {
            pin: {
                "type": output.channel_type.value,
                "frequency": output.frequency,
                "duty_cycle": output.duty_cycle,
                "is_running": output.is_running
            }
            for pin, output in self._outputs.items()
        }

    def _get_status_details(self) -> Dict[str, Any]:
        """
        PWM 상세 상태 정보 (Get PWM-specific Status Details)

        Returns:
            상세 정보 딕셔너리
        """
        return {
            "pwm_pin": self._pwm_pin,           # 모터용 핀
            "servo_pin": self._servo_pin,       # 서보용 핀
            "motor_speed": self.get_motor_speed(),  # 현재 모터 속도
            "servo_angle": self.get_servo_angle(),  # 현재 서보 각도
            "outputs": self.get_pwm_states()    # 모든 PWM 출력 상태
        }
