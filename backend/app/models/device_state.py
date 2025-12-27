"""
Device State Model (장치 상태 모델)
==================

[한국어 설명]
장치 상태 이력을 저장하는 ORM 모델입니다.
LED, 릴레이, 서보 모터 등의 상태 변경 기록을 추적합니다.

[사용 목적]
1. 감사(Auditing): 누가 언제 장치를 변경했는지 기록
2. 복구(Recovery): 시스템 재시작 시 마지막 상태 복원
3. 분석: 장치 사용 패턴 분석

[핵심 개념]
1. 상태 기록 패턴:
   - 현재 상태와 이전 상태를 함께 저장
   - 변경 주체(user/system/schedule) 추적
   - 시간순 이력 관리

2. JSON 컬럼 활용:
   - 다양한 장치의 상태를 유연하게 저장
   - LED: {"on": true, "brightness": 100}
   - Servo: {"angle": 90}
   - Motor: {"speed": 50, "direction": "forward"}
"""

# 날짜/시간 처리
from datetime import datetime

# 타입 힌트
from typing import Optional, Dict, Any

# SQLAlchemy 컬럼 및 타입
from sqlalchemy import Column, Integer, String, DateTime, JSON, Index

# SQLAlchemy 2.0 스타일 타입 매핑
from sqlalchemy.orm import Mapped

# 모델 기반 클래스
from .database import Base


# ==================== 장치 상태 모델 ====================
class DeviceState(Base):
    """
    Model for storing device state history.
    장치 상태 이력을 저장하는 모델.

    [한국어 설명]
    장치의 상태 변경 이력을 저장합니다.
    상태 변경 시 현재 상태와 이전 상태를 모두 기록하여
    변경 추적과 롤백이 가능합니다.

    Attributes:
        id: 기본 키
        timestamp: 상태가 기록된 시간
        device_type: 장치 유형 (led, relay, servo 등)
        device_id: 특정 장치 식별자 (예: "led_1", "relay_0")
        state: 현재 상태 (JSON)
        previous_state: 이전 상태 (JSON)
        changed_by: 변경 주체 (user, system, schedule)

    [사용 예시]
    LED 1이 켜졌을 때:
    {
        "device_type": "led",
        "device_id": "led_1",
        "state": {"on": true, "brightness": 100},
        "previous_state": {"on": false, "brightness": 0},
        "changed_by": "user"
    }
    """

    # 테이블 이름
    __tablename__ = "device_states"

    # ==================== 기본 컬럼들 ====================

    # [기본 키]
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)

    # [타임스탬프]
    # 상태가 변경된 시간
    timestamp: Mapped[datetime] = Column(DateTime, default=datetime.now, nullable=False, index=True)

    # [장치 유형]
    # 예: "led", "relay", "servo", "motor", "neopixel", "display"
    device_type: Mapped[str] = Column(String(50), nullable=False, index=True)

    # [장치 식별자]
    # 같은 유형의 여러 장치를 구분
    # 예: "led_0", "led_1", "relay_main", "servo_arm"
    device_id: Mapped[str] = Column(String(50), nullable=False, index=True)

    # ==================== 상태 컬럼들 ====================

    # [현재 상태]
    # JSON 형태로 다양한 장치 상태 저장
    # LED: {"on": true, "brightness": 80}
    # Servo: {"angle": 45}
    # Relay: {"on": false, "mode": "manual"}
    state: Mapped[Dict] = Column(JSON, nullable=False)

    # [이전 상태]
    # 롤백이나 비교를 위해 이전 상태도 저장
    # 첫 상태 기록 시에는 None일 수 있음
    previous_state: Mapped[Optional[Dict]] = Column(JSON, nullable=True)

    # [변경 주체]
    # 누가/무엇이 상태를 변경했는지 기록
    # - "user": 사용자가 UI를 통해 변경
    # - "system": 시스템 자동 변경 (초기화, 안전 모드 등)
    # - "schedule": 예약된 작업에 의한 변경
    # - "api": 외부 API 호출에 의한 변경
    # default="system": 기본값은 시스템
    changed_by: Mapped[str] = Column(String(50), default="system")

    # ==================== 복합 인덱스 ====================
    __table_args__ = (
        # [장치 유형 + 식별자 복합 인덱스]
        # 특정 장치의 이력 조회 시 유용
        # 예: SELECT * FROM device_states WHERE device_type='led' AND device_id='led_1'
        Index('idx_device_type_id', 'device_type', 'device_id'),

        # [장치 유형 + 시간 복합 인덱스]
        # 특정 유형의 최근 변경 조회 시 유용
        # 예: SELECT * FROM device_states WHERE device_type='relay' ORDER BY timestamp DESC
        Index('idx_device_time', 'device_type', 'timestamp'),
    )

    # ==================== 인스턴스 메서드 ====================
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        딕셔너리로 변환.

        [한국어 설명]
        ORM 객체를 API 응답용 딕셔너리로 변환합니다.
        JSON 직렬화가 가능한 형태로 반환됩니다.
        """
        return {
            "id": self.id,
            # datetime을 ISO 8601 문자열로 변환
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "device_type": self.device_type,
            "device_id": self.device_id,
            "state": self.state,  # JSON 컬럼은 이미 dict
            "previous_state": self.previous_state,
            "changed_by": self.changed_by
        }

    # ==================== 클래스 메서드 ====================
    @classmethod
    def record_change(
        cls,
        device_type: str,
        device_id: str,
        new_state: Dict[str, Any],
        previous_state: Dict[str, Any] = None,
        changed_by: str = "system"
    ) -> "DeviceState":
        """
        Record a device state change.
        장치 상태 변경 기록 생성.

        [한국어 설명]
        장치 상태 변경을 기록하는 팩토리 메서드입니다.
        명확한 인터페이스로 상태 기록 객체를 생성합니다.

        Args:
            device_type: 장치 유형 (예: "led", "relay")
            device_id: 장치 식별자 (예: "led_1")
            new_state: 새로운 상태 딕셔너리
            previous_state: 이전 상태 딕셔너리 (선택적)
            changed_by: 변경 주체 (기본값: "system")

        Returns:
            DeviceState: 새로 생성된 상태 기록 객체

        [사용 예시]
        # LED 상태 변경 기록
        record = DeviceState.record_change(
            device_type="led",
            device_id="led_1",
            new_state={"on": True, "brightness": 100},
            previous_state={"on": False, "brightness": 0},
            changed_by="user"
        )

        # DB에 저장
        session.add(record)
        await session.commit()

        [팩토리 메서드 패턴]
        - 객체 생성 로직을 캡슐화
        - 생성자보다 의미 있는 이름 제공
        - 유효성 검사나 전처리 추가 가능
        """
        return cls(
            device_type=device_type,
            device_id=device_id,
            state=new_state,
            previous_state=previous_state,
            changed_by=changed_by
        )
