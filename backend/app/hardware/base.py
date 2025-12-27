"""
Hardware Base Classes (하드웨어 베이스 클래스)
==============================================

[한국어 설명]
모든 하드웨어 컨트롤러의 공통 기능을 제공하는 추상 베이스 클래스입니다.

이 모듈의 핵심 개념:
1. **추상 클래스 (Abstract Base Class, ABC)**:
   - 직접 인스턴스화할 수 없는 클래스
   - 자식 클래스에서 반드시 구현해야 하는 메서드를 정의
   - "설계도" 역할을 하여 일관된 인터페이스 보장

2. **시뮬레이션 모드**:
   - 실제 하드웨어 없이도 개발/테스트 가능
   - Windows/Linux 개발 환경에서 동작 확인
   - 현실적인 가짜 값 생성 (노이즈, 드리프트 포함)

3. **비동기 초기화/정리**:
   - 리소스 누수 방지
   - 안전한 시작/종료 보장

사용 예시:
    # GPIO 컨트롤러가 이 베이스 클래스를 상속
    class GPIOController(BaseHardwareController, SimulationMixin):
        async def _do_initialize(self) -> bool:
            # 실제 초기화 로직
            ...
        async def _do_cleanup(self) -> None:
            # 정리 로직
            ...

[English Description]
Abstract base classes for all hardware controllers.
Provides unified interface for initialization, cleanup, and status reporting.
Supports both real hardware and simulation mode.
"""

# ============================================================================
# 라이브러리 임포트 (Import Libraries)
# ============================================================================

# abc: Abstract Base Class (추상 베이스 클래스) 모듈
# ABC: 추상 클래스의 베이스 클래스
# abstractmethod: 자식 클래스에서 반드시 구현해야 하는 메서드 표시
from abc import ABC, abstractmethod

# typing: 타입 힌트용 모듈
# Any: 모든 타입 허용
# Dict: 딕셔너리 타입 (예: Dict[str, int] = {"key": 1})
# Optional: None이 될 수 있는 타입 (예: Optional[str] = str 또는 None)
# List: 리스트 타입 (예: List[int] = [1, 2, 3])
from typing import Any, Dict, Optional, List

# dataclasses: 데이터 저장용 클래스를 간단히 만들 수 있는 모듈
# @dataclass 데코레이터를 사용하면 __init__, __repr__ 등을 자동 생성
# field: 기본값 설정 시 mutable 객체(dict, list 등)를 안전하게 처리
from dataclasses import dataclass, field

# datetime: 날짜/시간 처리 모듈
from datetime import datetime

# enum: 열거형(상수 집합) 정의 모듈
# Enum 클래스를 상속하여 관련 상수들을 그룹화
from enum import Enum

# asyncio: 비동기 프로그래밍 모듈
# async/await 패턴의 핵심 라이브러리
import asyncio

# 로깅 설정 가져오기 (로그 출력용)
from app.core.logging_config import get_logger

# 이 모듈용 로거 생성
# __name__: 현재 모듈의 이름 (예: "app.hardware.base")
logger = get_logger(__name__)


# ============================================================================
# 하드웨어 상태 열거형 (Hardware State Enum)
# ============================================================================

class HardwareState(Enum):
    """
    하드웨어 컴포넌트 상태 (Hardware Component States)

    [한국어 설명]
    Enum(열거형)이란?
    - 관련된 상수들을 하나의 클래스로 묶어 관리
    - 문자열 대신 사용하여 오타 방지
    - IDE 자동완성 지원

    상태 흐름:
    UNINITIALIZED → INITIALIZING → READY (정상)
                                 → ERROR (실패)
                 → DISABLED (비활성화)

    사용 예시:
        state = HardwareState.READY
        if state == HardwareState.READY:
            print("하드웨어 준비 완료!")
    """
    UNINITIALIZED = "uninitialized"  # 초기화되지 않음 (시작 상태)
    INITIALIZING = "initializing"    # 초기화 진행 중
    READY = "ready"                  # 준비 완료 (사용 가능)
    ERROR = "error"                  # 오류 발생
    DISABLED = "disabled"            # 비활성화됨 (의도적으로 꺼짐)


# ============================================================================
# 하드웨어 상태 데이터 클래스 (Hardware Status Dataclass)
# ============================================================================

@dataclass
class HardwareStatus:
    """
    하드웨어 컴포넌트의 상태 정보 (Hardware Component Status Information)

    [한국어 설명]
    @dataclass 데코레이터란?
    - 데이터 저장용 클래스를 간단히 만들 수 있게 해줌
    - __init__, __repr__, __eq__ 등을 자동 생성
    - 보일러플레이트 코드(반복적인 코드) 감소

    일반 클래스 vs dataclass:
        # 일반 클래스 (길고 반복적)
        class Person:
            def __init__(self, name, age):
                self.name = name
                self.age = age
            def __repr__(self):
                return f"Person(name={self.name}, age={self.age})"

        # dataclass (간결함)
        @dataclass
        class Person:
            name: str
            age: int

    field() 함수:
    - default_factory: 기본값으로 함수 호출 결과 사용
    - 예: field(default_factory=dict) → 각 인스턴스마다 새 dict 생성
    - 주의: 리스트나 딕셔너리는 반드시 field(default_factory=...)를 사용
          그렇지 않으면 모든 인스턴스가 같은 객체를 공유함!

    Attributes:
        name: 컨트롤러 이름 (예: "GPIO Controller")
        state: 현재 상태 (HardwareState enum 값)
        is_simulation: 시뮬레이션 모드 여부
        last_update: 마지막 업데이트 시간
        error_message: 오류 발생 시 메시지
        details: 추가 상세 정보 (딕셔너리)
    """
    name: str                                              # 컨트롤러 이름
    state: HardwareState                                   # 현재 상태
    is_simulation: bool                                    # 시뮬레이션 모드 여부
    last_update: datetime = field(default_factory=datetime.now)  # 마지막 업데이트 시간
    error_message: Optional[str] = None                    # 오류 메시지 (없으면 None)
    details: Dict[str, Any] = field(default_factory=dict)  # 추가 상세 정보

    def to_dict(self) -> Dict[str, Any]:
        """
        딕셔너리로 변환 (Convert to Dictionary)

        [한국어 설명]
        이 메서드가 필요한 이유:
        - JSON으로 직렬화하기 위해 (API 응답용)
        - Enum과 datetime은 JSON으로 직접 변환 불가
        - state.value: Enum에서 실제 값 추출 (예: "ready")
        - isoformat(): datetime을 ISO 8601 문자열로 변환

        Returns:
            딕셔너리 형태의 상태 정보
        """
        return {
            "name": self.name,
            "state": self.state.value,              # Enum → 문자열 변환
            "is_simulation": self.is_simulation,
            "last_update": self.last_update.isoformat(),  # datetime → 문자열 변환
            "error_message": self.error_message,
            "details": self.details
        }


# ============================================================================
# 하드웨어 컨트롤러 베이스 클래스 (Hardware Controller Base Class)
# ============================================================================

class BaseHardwareController(ABC):
    """
    모든 하드웨어 컨트롤러의 추상 베이스 클래스
    (Abstract Base Class for All Hardware Controllers)

    [한국어 설명]
    ABC (Abstract Base Class)란?
    - 직접 인스턴스를 만들 수 없는 클래스
    - 자식 클래스가 반드시 구현해야 하는 메서드를 정의
    - 인터페이스 역할 + 공통 기능 제공

    이 클래스가 제공하는 기능:
    1. 초기화/정리 생명주기 관리
    2. 상태 추적 (READY, ERROR 등)
    3. 비동기 락으로 동시 접근 방지
    4. 상태 조회 인터페이스

    상속 패턴:
        class GPIOController(BaseHardwareController, SimulationMixin):
            # BaseHardwareController: 주요 기능 상속
            # SimulationMixin: 시뮬레이션 유틸리티 메서드 추가

    @abstractmethod 데코레이터:
    - 이 데코레이터가 붙은 메서드는 자식 클래스에서 반드시 구현해야 함
    - 구현하지 않으면 인스턴스 생성 시 TypeError 발생

    사용 예시:
        controller = GPIOController(simulation_mode=True)
        await controller.initialize()  # 초기화
        # ... 사용 ...
        await controller.cleanup()     # 정리
    """

    def __init__(self, name: str, simulation_mode: bool = False):
        """
        생성자 (Constructor)

        [한국어 설명]
        __init__: Python에서 객체가 생성될 때 자동으로 호출되는 특수 메서드
        self: 객체 자신을 가리키는 참조 (다른 언어의 this와 유사)

        언더스코어(_) 접두사 규칙:
        - self.name: 공개 속성 (외부에서 접근 가능)
        - self._state: 보호 속성 (클래스 내부용, 외부 접근 비권장)
        - self.__private: 비공개 속성 (이름 맹글링으로 외부 접근 어려움)

        Args:
            name: 컨트롤러 이름 (예: "GPIO Controller")
            simulation_mode: 시뮬레이션 모드 활성화 여부
        """
        self.name = name                              # 컨트롤러 이름 (공개)
        self.simulation_mode = simulation_mode        # 시뮬레이션 모드 여부 (공개)
        self._state = HardwareState.UNINITIALIZED     # 현재 상태 (보호)
        self._error_message: Optional[str] = None     # 오류 메시지 (보호)
        self._last_update = datetime.now()            # 마지막 업데이트 시간
        self._initialized = False                     # 초기화 완료 여부
        self._lock = asyncio.Lock()                   # 비동기 락 (동시 접근 방지)
        # asyncio.Lock():
        # - 여러 비동기 작업이 동시에 같은 리소스에 접근하는 것을 방지
        # - async with self._lock: 으로 사용
        # - 한 번에 하나의 작업만 critical section에 진입 가능

    @property
    def is_ready(self) -> bool:
        """
        하드웨어가 사용 준비되었는지 확인 (Check if Hardware is Ready)

        [한국어 설명]
        @property 데코레이터란?
        - 메서드를 속성처럼 사용할 수 있게 해줌
        - 괄호 없이 호출: controller.is_ready (O)
        - 괄호 사용 불가: controller.is_ready() (X)

        @property의 장점:
        1. 간결한 문법 (메서드보다 직관적)
        2. 읽기 전용 속성 만들기 (setter 없으면 수정 불가)
        3. 계산된 값을 속성처럼 접근

        Returns:
            True면 사용 가능, False면 사용 불가
        """
        return self._state == HardwareState.READY

    @property
    def status(self) -> HardwareStatus:
        """
        현재 하드웨어 상태 조회 (Get Current Hardware Status)

        [한국어 설명]
        HardwareStatus 객체를 생성하여 반환합니다.
        이 객체에는 이름, 상태, 시뮬레이션 여부, 마지막 업데이트 시간 등이 포함됩니다.

        Returns:
            HardwareStatus 객체 (현재 상태 정보)
        """
        return HardwareStatus(
            name=self.name,
            state=self._state,
            is_simulation=self.simulation_mode,
            last_update=self._last_update,
            error_message=self._error_message,
            details=self._get_status_details()  # 자식 클래스에서 오버라이드
        )

    def _get_status_details(self) -> Dict[str, Any]:
        """
        컴포넌트별 상세 상태 정보 (Component-specific Status Details)

        [한국어 설명]
        자식 클래스에서 오버라이드하여 추가 정보를 제공할 수 있습니다.
        기본 구현은 빈 딕셔너리를 반환합니다.

        오버라이드 예시 (GPIOController):
            def _get_status_details(self) -> Dict[str, Any]:
                return {
                    "led_pins": self._led_pins,
                    "button_pins": self._button_pins,
                    "led_states": self.get_led_states()
                }

        Returns:
            상세 정보 딕셔너리 (기본: 빈 딕셔너리)
        """
        return {}

    async def initialize(self) -> bool:
        """
        하드웨어 컨트롤러 초기화 (Initialize Hardware Controller)

        [한국어 설명]
        async/await 패턴:
        - async def: 비동기 함수 정의
        - await: 비동기 작업이 완료될 때까지 대기
        - 다른 작업이 기다리는 동안 다른 코루틴이 실행될 수 있음

        async with self._lock:
        - 비동기 컨텍스트 매니저
        - 락을 획득하고, 블록 끝에서 자동으로 해제
        - 동시에 여러 초기화가 실행되는 것을 방지

        Template Method 패턴:
        - initialize()가 전체 흐름을 정의
        - _do_initialize()는 자식 클래스에서 구현
        - 공통 로직(로깅, 상태 관리)은 여기서 처리

        Returns:
            True: 초기화 성공
            False: 초기화 실패
        """
        # 이미 초기화된 경우 바로 반환
        if self._initialized:
            return True

        # 비동기 락으로 동시 초기화 방지
        async with self._lock:
            try:
                # 상태를 "초기화 중"으로 변경
                self._state = HardwareState.INITIALIZING
                logger.info(f"Initializing {self.name} (simulation={self.simulation_mode})")

                # 실제 초기화 수행 (자식 클래스에서 구현)
                success = await self._do_initialize()

                if success:
                    # 성공 시 상태 업데이트
                    self._state = HardwareState.READY
                    self._initialized = True
                    self._error_message = None
                    logger.info(f"{self.name} initialized successfully")
                else:
                    # 실패 시 에러 상태로 변경
                    self._state = HardwareState.ERROR
                    logger.error(f"{self.name} initialization failed")

                return success

            except Exception as e:
                # 예외 발생 시 에러 상태로 변경
                self._state = HardwareState.ERROR
                self._error_message = str(e)
                logger.exception(f"{self.name} initialization error: {e}")
                # logger.exception(): 예외의 스택 트레이스도 함께 로깅
                return False

    async def cleanup(self) -> None:
        """
        하드웨어 리소스 정리 (Clean up Hardware Resources)

        [한국어 설명]
        정리(cleanup)가 중요한 이유:
        1. GPIO 핀을 해제하여 다른 프로세스가 사용할 수 있게 함
        2. 열린 파일/연결을 닫음
        3. 실행 중인 스레드/태스크를 종료
        4. 메모리 누수 방지

        예외 처리:
        - 정리 중 예외가 발생해도 로깅만 하고 계속 진행
        - 다른 리소스의 정리가 막히지 않도록 함
        """
        async with self._lock:
            try:
                logger.info(f"Cleaning up {self.name}")
                await self._do_cleanup()  # 자식 클래스에서 구현
                self._state = HardwareState.UNINITIALIZED
                self._initialized = False
            except Exception as e:
                # 정리 중 예외는 로깅만 하고 계속 진행
                logger.exception(f"{self.name} cleanup error: {e}")

    @abstractmethod
    async def _do_initialize(self) -> bool:
        """
        실제 초기화 수행 (Perform Actual Initialization)

        [한국어 설명]
        @abstractmethod 데코레이터:
        - 이 메서드는 자식 클래스에서 반드시 구현해야 함
        - 구현하지 않으면 클래스 인스턴스 생성 불가
        - "이 메서드는 자식 클래스마다 다르게 동작해야 한다"는 의미

        자식 클래스 구현 예시 (GPIOController):
            async def _do_initialize(self) -> bool:
                try:
                    import RPi.GPIO as GPIO
                    GPIO.setmode(GPIO.BCM)
                    # LED, 버튼, 릴레이 핀 설정
                    return True
                except:
                    return False

        Returns:
            True: 초기화 성공
            False: 초기화 실패
        """
        pass  # 자식 클래스에서 구현 필수

    @abstractmethod
    async def _do_cleanup(self) -> None:
        """
        실제 정리 수행 (Perform Actual Cleanup)

        [한국어 설명]
        자식 클래스에서 구현해야 하는 정리 로직입니다.
        GPIO 핀 해제, 연결 닫기, 버퍼 비우기 등의 작업을 수행합니다.

        자식 클래스 구현 예시 (GPIOController):
            async def _do_cleanup(self) -> None:
                if self._gpio:
                    self._gpio.cleanup()
                self._pins.clear()
        """
        pass  # 자식 클래스에서 구현 필수

    def _update_timestamp(self) -> None:
        """
        마지막 업데이트 시간 갱신 (Update Last Update Timestamp)

        [한국어 설명]
        하드웨어 상태가 변경될 때마다 호출하여
        마지막 업데이트 시간을 현재 시간으로 갱신합니다.

        사용 예시:
            async def set_led(self, index: int, state: bool) -> bool:
                # LED 상태 변경
                self._update_timestamp()  # 시간 갱신
                return True
        """
        self._last_update = datetime.now()


# ============================================================================
# 시뮬레이션 믹스인 클래스 (Simulation Mixin Class)
# ============================================================================

class SimulationMixin:
    """
    시뮬레이션 유틸리티를 제공하는 믹스인 클래스
    (Mixin Class Providing Simulation Utilities)

    [한국어 설명]
    Mixin 패턴이란?
    - 다중 상속을 통해 기능을 추가하는 패턴
    - 단독으로 사용하지 않고 다른 클래스와 함께 상속
    - "섞어서(mix in)" 사용하는 클래스

    일반 상속 vs Mixin:
    - 일반 상속: "is-a" 관계 (Dog is an Animal)
    - Mixin: "has-a" 또는 "can-do" 관계 (Controller has simulation capability)

    사용 예시:
        class GPIOController(BaseHardwareController, SimulationMixin):
            # BaseHardwareController의 기능 + SimulationMixin의 기능

    이 Mixin이 제공하는 기능:
    1. 현실적인 지연 시간 시뮬레이션
    2. 센서 노이즈 시뮬레이션
    3. 값의 점진적 변화(드리프트) 시뮬레이션
    """

    def _simulate_delay(self, min_ms: float = 1, max_ms: float = 10) -> float:
        """
        현실적인 지연 시간 생성 (Generate Realistic Delay)

        [한국어 설명]
        실제 하드웨어는 동작에 시간이 걸립니다.
        예: I2C 통신 5ms, 센서 읽기 50ms 등

        시뮬레이션에서도 이 지연을 모방하여:
        1. 실제 환경과 비슷한 타이밍 테스트 가능
        2. 타이밍 관련 버그 발견 가능
        3. UI 반응성 테스트 가능

        Args:
            min_ms: 최소 지연 시간 (밀리초)
            max_ms: 최대 지연 시간 (밀리초)

        Returns:
            지연 시간 (초 단위) - asyncio.sleep()에 사용
        """
        import random
        # random.uniform(a, b): a와 b 사이의 랜덤 실수 반환
        return random.uniform(min_ms, max_ms) / 1000  # ms → 초 변환

    def _simulate_noise(self, value: float, noise_percent: float = 2.0) -> float:
        """
        현실적인 노이즈 추가 (Add Realistic Noise to Simulated Value)

        [한국어 설명]
        실제 센서는 항상 약간의 노이즈(잡음)가 있습니다.
        예: 온도계가 25.0°C를 측정해도 24.9~25.1°C로 출력

        이 함수는 값에 랜덤 노이즈를 추가합니다:
        - noise_percent=2.0이면 ±2% 범위의 노이즈
        - 값이 클수록 노이즈의 절대값도 커짐

        계산 과정:
        1. 노이즈 범위 = value * (noise_percent / 100)
        2. 랜덤 값 = -1 ~ +1 사이의 값
        3. 최종 노이즈 = 노이즈 범위 * 랜덤 값

        Args:
            value: 기본 값
            noise_percent: 노이즈 백분율 (기본 2%)

        Returns:
            노이즈가 추가된 값

        예시:
            value = 25.0, noise_percent = 2.0
            → 25.0 ± 0.5 = 24.5 ~ 25.5 사이의 값
        """
        import random
        # 값의 noise_percent%를 최대 노이즈 범위로 설정
        noise = value * (noise_percent / 100) * random.uniform(-1, 1)
        return value + noise

    def _simulate_drift(self, value: float, target: float, rate: float = 0.1) -> float:
        """
        목표값으로 점진적 이동 (Simulate Gradual Drift Towards Target)

        [한국어 설명]
        드리프트(drift)란?
        - 값이 시간에 따라 천천히 변하는 현상
        - 온도가 서서히 올라가거나 내려가는 것처럼

        이 함수는 현재 값을 목표 값 방향으로 조금씩 이동시킵니다.
        - rate=0.1이면 목표와의 차이의 10%만큼 이동
        - rate가 클수록 빠르게 목표에 도달

        수학적 공식:
        new_value = value + (target - value) * rate
                  = value * (1 - rate) + target * rate

        이는 지수 이동 평균(EMA)과 같은 형태입니다.

        Args:
            value: 현재 값
            target: 목표 값
            rate: 드리프트 속도 (0-1, 클수록 빠름)

        Returns:
            드리프트가 적용된 새 값

        예시:
            value = 20, target = 30, rate = 0.1
            → 20 + (30 - 20) * 0.1 = 21
            다음 호출: 21 + (30 - 21) * 0.1 = 21.9
            ...점점 30에 가까워짐
        """
        return value + (target - value) * rate
