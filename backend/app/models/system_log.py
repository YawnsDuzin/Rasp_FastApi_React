"""
System Log Model (시스템 로그 모델)
================

[한국어 설명]
시스템 이벤트와 에러 로그를 저장하는 ORM 모델입니다.
디버깅, 모니터링, 문제 추적을 위한 로그 기록을 관리합니다.

[핵심 개념]
1. 로그 레벨 (Log Level):
   - DEBUG: 디버깅용 상세 정보 (개발 환경)
   - INFO: 정상 동작 정보 (일반 이벤트)
   - WARNING: 잠재적 문제 경고
   - ERROR: 에러 발생 (복구 가능)
   - CRITICAL: 심각한 에러 (시스템 위험)

2. 구조화된 로깅 (Structured Logging):
   - 메시지와 함께 JSON 형태의 상세 정보 저장
   - 로그 검색 및 분석이 용이
   - 예: {"sensor_id": "dht_1", "error_code": 101}

3. 로그 소스 추적:
   - 어떤 모듈/컴포넌트에서 발생했는지 기록
   - 문제 발생 위치를 빠르게 파악 가능
"""

# 날짜/시간 처리
from datetime import datetime

# 타입 힌트
from typing import Optional, Dict, Any

# [Enum]
# 열거형 클래스를 정의하기 위한 모듈
# 고정된 값의 집합을 정의할 때 사용
from enum import Enum

# SQLAlchemy 컬럼 및 타입
# Text: 긴 문자열 (String보다 길이 제한 없음)
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Index

# SQLAlchemy 2.0 스타일 타입 매핑
from sqlalchemy.orm import Mapped

# 모델 기반 클래스
from .database import Base


# ==================== 로그 레벨 열거형 ====================
class LogLevel(str, Enum):
    """
    Log severity levels.
    로그 심각도 레벨.

    [한국어 설명]
    표준 로그 레벨을 정의하는 열거형입니다.
    Python 표준 logging 모듈과 동일한 레벨 체계를 따릅니다.

    [str, Enum 상속]
    str과 Enum을 함께 상속하면:
    - LogLevel.INFO.value 대신 LogLevel.INFO 자체를 문자열로 사용 가능
    - JSON 직렬화 시 자동으로 문자열 값 사용
    - 예: LogLevel.INFO == "INFO" -> True

    [레벨 설명]
    - DEBUG: 상세한 디버깅 정보 (보통 프로덕션에서 비활성화)
    - INFO: 일반적인 정보성 메시지 (정상 동작 확인)
    - WARNING: 경고 메시지 (잠재적 문제, 즉각 조치 불필요)
    - ERROR: 에러 발생 (기능 동작 실패, 복구 가능)
    - CRITICAL: 심각한 에러 (시스템 장애, 즉각 조치 필요)
    """

    # 각 레벨 정의 (값은 문자열)
    DEBUG = "DEBUG"        # 디버그 레벨 (가장 낮음)
    INFO = "INFO"          # 정보 레벨
    WARNING = "WARNING"    # 경고 레벨
    ERROR = "ERROR"        # 에러 레벨
    CRITICAL = "CRITICAL"  # 치명적 레벨 (가장 높음)


# ==================== 시스템 로그 모델 ====================
class SystemLog(Base):
    """
    Model for storing system logs and events.
    시스템 로그와 이벤트를 저장하는 모델.

    [한국어 설명]
    애플리케이션의 모든 중요 이벤트를 기록합니다.
    에러 추적, 사용자 활동 감사, 시스템 모니터링에 활용됩니다.

    Attributes:
        id: 기본 키
        timestamp: 이벤트 발생 시간
        level: 로그 심각도 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        source: 로그 발생 소스 (모듈/컴포넌트 이름)
        message: 로그 메시지
        details: 추가 상세 정보 (JSON)
        user_action: 사용자 행동에 의한 것인지 여부

    [로그 예시]
    센서 읽기 실패:
    {
        "level": "ERROR",
        "source": "sensor_controller",
        "message": "DHT22 센서 읽기 실패",
        "details": {"sensor_id": "dht_1", "retry_count": 3, "error": "timeout"},
        "user_action": false
    }

    사용자 설정 변경:
    {
        "level": "INFO",
        "source": "settings_api",
        "message": "사용자가 LED 설정 변경",
        "details": {"led_id": 1, "new_state": "on"},
        "user_action": true
    }
    """

    # 테이블 이름
    __tablename__ = "system_logs"

    # ==================== 기본 컬럼들 ====================

    # [기본 키]
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)

    # [타임스탬프]
    # 로그가 생성된 시간
    timestamp: Mapped[datetime] = Column(DateTime, default=datetime.now, nullable=False, index=True)

    # [로그 레벨]
    # DEBUG, INFO, WARNING, ERROR, CRITICAL 중 하나
    # String(20): 가장 긴 레벨명 "CRITICAL"도 충분히 저장
    level: Mapped[str] = Column(String(20), nullable=False, index=True)

    # [소스]
    # 로그를 생성한 모듈/컴포넌트 이름
    # 예: "gpio_controller", "websocket_manager", "sensor_api"
    # 문제 발생 위치를 빠르게 파악하는 데 유용
    source: Mapped[str] = Column(String(100), nullable=False, index=True)

    # [메시지]
    # 로그 내용 (사람이 읽을 수 있는 설명)
    # Text: 긴 메시지도 저장 가능 (String은 길이 제한 있음)
    message: Mapped[str] = Column(Text, nullable=False)

    # ==================== 추가 정보 컬럼들 ====================

    # [상세 정보]
    # 구조화된 추가 데이터 (JSON)
    # 예: {"error_code": 404, "url": "/api/sensor", "user_id": 123}
    details: Mapped[Optional[Dict]] = Column(JSON, nullable=True)

    # [사용자 행동 여부]
    # True: 사용자가 트리거한 이벤트
    # False: 시스템 자동 이벤트
    # SQLite는 Boolean이 없어 Integer 사용 (0 또는 1)
    user_action: Mapped[bool] = Column(Integer, default=0)

    # ==================== 복합 인덱스 ====================
    __table_args__ = (
        # [레벨 + 시간 복합 인덱스]
        # 특정 레벨의 최근 로그 조회 시 유용
        # 예: SELECT * FROM system_logs WHERE level='ERROR' ORDER BY timestamp DESC
        Index('idx_log_level_time', 'level', 'timestamp'),

        # [소스 + 시간 복합 인덱스]
        # 특정 모듈의 로그 조회 시 유용
        # 예: SELECT * FROM system_logs WHERE source='gpio_controller' AND timestamp > '...'
        Index('idx_log_source_time', 'source', 'timestamp'),
    )

    # ==================== 인스턴스 메서드 ====================
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        딕셔너리로 변환.

        [한국어 설명]
        ORM 객체를 API 응답용 딕셔너리로 변환합니다.
        프론트엔드의 로그 뷰어에서 사용됩니다.
        """
        return {
            "id": self.id,
            # datetime을 ISO 8601 문자열로 변환
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "level": self.level,
            "source": self.source,
            "message": self.message,
            "details": self.details,  # JSON 컬럼은 이미 dict
            # Integer를 bool로 변환 (0 -> False, 1 -> True)
            "user_action": bool(self.user_action)
        }

    # ==================== 클래스 메서드 ====================
    @classmethod
    def create_log(
        cls,
        level: LogLevel,
        source: str,
        message: str,
        details: Dict[str, Any] = None,
        user_action: bool = False
    ) -> "SystemLog":
        """
        Create a new log entry.
        새 로그 엔트리 생성.

        [한국어 설명]
        시스템 로그를 생성하는 팩토리 메서드입니다.
        LogLevel 열거형을 사용하여 타입 안전성을 보장합니다.

        Args:
            level: 로그 레벨 (LogLevel 열거형)
            source: 로그 소스 (모듈명)
            message: 로그 메시지
            details: 추가 상세 정보 (선택적)
            user_action: 사용자 행동 여부

        Returns:
            SystemLog: 새로 생성된 로그 객체

        [사용 예시]
        # 에러 로그 생성
        log = SystemLog.create_log(
            level=LogLevel.ERROR,
            source="sensor_controller",
            message="온도 센서 읽기 실패",
            details={"sensor": "DHT22", "error": "CRC 불일치"},
            user_action=False
        )

        # DB에 저장
        session.add(log)
        await session.commit()

        [LogLevel.value]
        LogLevel 열거형의 실제 문자열 값을 가져옴
        LogLevel.ERROR.value -> "ERROR"
        """
        return cls(
            # level.value: Enum의 실제 값(문자열) 추출
            level=level.value,
            source=source,
            message=message,
            details=details,
            # bool을 int로 변환 (True -> 1, False -> 0)
            user_action=1 if user_action else 0
        )
