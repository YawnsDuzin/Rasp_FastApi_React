"""
Sensor Data Model (센서 데이터 모델)
=================

[한국어 설명]
센서 측정값의 이력을 저장하는 ORM 모델입니다.
온도, 습도, 기압, 거리 등 다양한 센서 데이터를 통합 저장합니다.

[핵심 개념]
1. ORM 모델 (Object-Relational Mapping):
   - Python 클래스를 데이터베이스 테이블에 매핑
   - 클래스의 속성이 테이블의 컬럼이 됨
   - SQL 없이 Python 객체로 DB 조작 가능

2. SQLAlchemy Column 타입:
   - Integer: 정수 (SQLite INTEGER)
   - Float: 실수 (SQLite REAL)
   - String(n): 문자열, 최대 n자 (SQLite TEXT)
   - DateTime: 날짜/시간 (SQLite TEXT ISO8601 형식)
   - JSON: JSON 데이터 (SQLite TEXT로 직렬화)

3. 데이터베이스 인덱스:
   - 검색 속도를 높이기 위한 데이터 구조
   - 자주 검색하는 컬럼에 생성
   - 저장 공간은 늘어나지만 조회 성능 향상
"""

# datetime: 날짜/시간 처리를 위한 표준 라이브러리
from datetime import datetime

# 타입 힌트 관련 모듈
# Optional: None일 수 있는 타입 표시 (Optional[int] = int 또는 None)
# Dict: 딕셔너리 타입 (Dict[str, Any] = 키가 str인 딕셔너리)
# Any: 어떤 타입이든 가능
from typing import Optional, Dict, Any

# [SQLAlchemy 컬럼 및 타입]
# Column: 테이블 컬럼을 정의하는 클래스
# Integer, Float, String, DateTime: 데이터 타입 클래스
# JSON: JSON 데이터를 저장하는 타입 (직렬화/역직렬화 자동 처리)
# Index: 데이터베이스 인덱스를 정의하는 클래스
from sqlalchemy import Column, Integer, Float, String, DateTime, JSON, Index

# Mapped: SQLAlchemy 2.0 스타일 타입 힌트
# 컬럼의 Python 타입을 명시적으로 표시
from sqlalchemy.orm import Mapped

# 모든 모델의 기반이 되는 Base 클래스
from .database import Base


# ==================== 센서 데이터 모델 ====================
class SensorData(Base):
    """
    Model for storing sensor data readings.
    센서 데이터 측정값을 저장하는 모델.

    [한국어 설명]
    모든 종류의 센서 데이터를 하나의 테이블에 저장합니다.
    Nullable 컬럼을 사용하여 유연하게 다양한 센서를 지원합니다.

    Attributes:
        id: 기본 키 (자동 증가)
        timestamp: 측정 시간
        sensor_type: 센서 유형 (dht, bmp280, ultrasonic 등)
        temperature: 온도 (섭씨)
        humidity: 상대습도 (%)
        pressure: 기압 (hPa)
        altitude: 고도 (미터)
        distance: 거리 (센티미터)
        light_level: 조도 (0-1023)
        soil_moisture: 토양 습도 (0-1023)
        motion: 움직임 감지 여부
        adc_values: ADC 채널별 값 (JSON)
        extra_data: 추가 센서 데이터 (JSON)

    [테이블 구조]
    - 유연한 스키마: 각 센서에 해당하는 컬럼만 값이 있고 나머지는 NULL
    - JSON 컬럼으로 확장성 확보 (새 센서 추가 시 스키마 변경 불필요)
    """

    # [테이블 이름 지정]
    # __tablename__: SQLAlchemy가 생성할 테이블 이름
    # 지정하지 않으면 클래스 이름을 소문자로 변환하여 사용
    __tablename__ = "sensor_data"

    # ==================== 기본 컬럼들 ====================

    # [기본 키 컬럼]
    # id: 각 레코드의 고유 식별자
    # Mapped[int]: Python int 타입으로 매핑됨을 표시
    # Column(...): 컬럼 정의
    # Integer: 정수 타입
    # primary_key=True: 기본 키로 지정 (유일하고 NOT NULL)
    # autoincrement=True: 자동 증가 (INSERT 시 자동으로 값 할당)
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)

    # [타임스탬프 컬럼]
    # timestamp: 데이터가 기록된 시간
    # DateTime: 날짜/시간 타입
    # default=datetime.now: INSERT 시 현재 시간 자동 입력
    # nullable=False: NULL 불허 (필수 값)
    # index=True: 이 컬럼에 인덱스 생성 (시간 기반 검색 최적화)
    timestamp: Mapped[datetime] = Column(DateTime, default=datetime.now, nullable=False, index=True)

    # [센서 타입 컬럼]
    # sensor_type: 어떤 센서의 데이터인지 구분
    # String(50): 최대 50자 문자열
    # 예: "dht", "bmp280", "ultrasonic", "pir", "all"
    sensor_type: Mapped[str] = Column(String(50), nullable=False, index=True)

    # ==================== 환경 센서 컬럼들 ====================
    # 온도, 습도, 기압, 고도 - 모두 Optional (NULL 가능)

    # [온도]
    # Float: 부동소수점 타입
    # Optional[float]: Python에서 float 또는 None
    # nullable=True: NULL 허용 (해당 센서가 없으면 값이 없음)
    temperature: Mapped[Optional[float]] = Column(Float, nullable=True)

    # [습도] - 상대습도 0-100%
    humidity: Mapped[Optional[float]] = Column(Float, nullable=True)

    # [기압] - hPa (헥토파스칼) 단위, 해수면 기준 약 1013hPa
    pressure: Mapped[Optional[float]] = Column(Float, nullable=True)

    # [고도] - 미터 단위, 기압으로부터 계산됨
    altitude: Mapped[Optional[float]] = Column(Float, nullable=True)

    # ==================== 거리 센서 컬럼 ====================

    # [거리] - 센티미터 단위, 초음파 센서로 측정
    distance: Mapped[Optional[float]] = Column(Float, nullable=True)

    # ==================== 아날로그 센서 컬럼들 ====================

    # [조도] - 0-1023 (10비트 ADC 값)
    # Integer 사용 (아날로그 값은 정수로 변환됨)
    light_level: Mapped[Optional[int]] = Column(Integer, nullable=True)

    # [토양 습도] - 0-1023 (10비트 ADC 값)
    soil_moisture: Mapped[Optional[int]] = Column(Integer, nullable=True)

    # ==================== 움직임 감지 컬럼 ====================

    # [움직임 감지]
    # motion: PIR 센서의 움직임 감지 결과
    # SQLite는 Boolean 타입이 없어 Integer 사용 (0=False, 1=True)
    # Python에서는 bool로 취급하지만 DB에는 정수로 저장
    motion: Mapped[Optional[bool]] = Column(Integer, nullable=True)

    # ==================== JSON 컬럼들 ====================

    # [ADC 값들]
    # adc_values: 여러 ADC 채널의 값을 JSON으로 저장
    # JSON 타입: Python dict를 자동으로 직렬화/역직렬화
    # 예: {"ch0": 512, "ch1": 768, "ch2": 256}
    adc_values: Mapped[Optional[Dict]] = Column(JSON, nullable=True)

    # [추가 데이터]
    # extra_data: 확장성을 위한 추가 데이터 필드
    # 새로운 센서 추가 시 스키마 변경 없이 여기에 저장 가능
    extra_data: Mapped[Optional[Dict]] = Column(JSON, nullable=True)

    # ==================== 복합 인덱스 ====================
    # [__table_args__]
    # 테이블 레벨 옵션을 설정하는 특수 속성
    # 여러 컬럼에 걸친 복합 인덱스 등을 정의

    __table_args__ = (
        # [복합 인덱스 1: 센서타입 + 시간]
        # Index('인덱스이름', '컬럼1', '컬럼2'): 복합 인덱스 생성
        # 특정 센서의 특정 시간대 데이터 조회 시 유용
        # 예: SELECT * FROM sensor_data WHERE sensor_type='dht' AND timestamp > '2024-01-01'
        Index('idx_sensor_timestamp', 'sensor_type', 'timestamp'),

        # [복합 인덱스 2: 온도 + 시간]
        # 온도 기준 검색 시 유용 (온도 트렌드 분석 등)
        # 예: SELECT * FROM sensor_data WHERE temperature > 30 ORDER BY timestamp
        Index('idx_temperature_time', 'temperature', 'timestamp'),
    )

    # ==================== 인스턴스 메서드 ====================
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        딕셔너리로 변환.

        [한국어 설명]
        ORM 객체를 JSON 직렬화 가능한 딕셔너리로 변환합니다.
        API 응답을 생성할 때 사용됩니다.

        Returns:
            Dict[str, Any]: 센서 데이터를 담은 딕셔너리

        [datetime 처리]
        datetime 객체는 JSON으로 직접 변환할 수 없으므로
        isoformat()을 사용해 ISO 8601 문자열로 변환합니다.
        예: "2024-01-15T14:30:00"
        """
        return {
            "id": self.id,
            # [조건부 표현식]
            # self.timestamp.isoformat() if self.timestamp else None
            # = self.timestamp가 있으면 ISO 문자열로, 없으면 None
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "sensor_type": self.sensor_type,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "altitude": self.altitude,
            "distance": self.distance,
            "light_level": self.light_level,
            "soil_moisture": self.soil_moisture,
            # [bool 변환]
            # motion은 DB에 Integer로 저장되므로 bool()로 변환
            # 0 -> False, 1 -> True, None -> None
            "motion": bool(self.motion) if self.motion is not None else None,
            "adc_values": self.adc_values,
            "extra_data": self.extra_data
        }

    # ==================== 클래스 메서드 ====================
    @classmethod
    def from_hardware_data(cls, data: Dict[str, Any]) -> "SensorData":
        """
        Create SensorData from hardware data dict.
        하드웨어 데이터 딕셔너리로부터 SensorData 생성.

        [한국어 설명]
        HardwareManager에서 수집한 데이터 딕셔너리를 ORM 객체로 변환합니다.
        팩토리 메서드 패턴의 구현입니다.

        Args:
            data: 하드웨어에서 수집한 데이터 딕셔너리

        Returns:
            SensorData: 새로 생성된 센서 데이터 객체

        [클래스 메서드 (@classmethod)]
        - cls: 클래스 자체를 첫 번째 인자로 받음 (self 대신)
        - 인스턴스 없이 클래스에서 직접 호출 가능
        - 예: SensorData.from_hardware_data({...})

        [반환 타입 힌트 "SensorData"]
        클래스 정의 내부에서 자기 자신을 타입으로 사용할 때
        문자열로 감싸야 함 (Forward Reference)
        """
        # cls(...): 클래스의 생성자 호출 (SensorData(...) 와 동일)
        return cls(
            # 모든 센서 데이터를 통합 저장하므로 "all" 타입
            sensor_type="all",

            # [dict.get() 메서드]
            # data.get("key"): 키가 있으면 값을, 없으면 None 반환
            # data["key"]와 달리 KeyError가 발생하지 않음
            temperature=data.get("temperature"),
            humidity=data.get("humidity"),
            pressure=data.get("pressure"),
            altitude=data.get("altitude"),
            distance=data.get("distance"),
            light_level=data.get("light_level"),
            soil_moisture=data.get("soil_moisture"),

            # [조건부 표현식으로 bool -> int 변환]
            # True -> 1, False/None -> 0
            motion=1 if data.get("motion") else 0,
            adc_values=data.get("adc_values"),
            extra_data=data.get("extra_data")
        )
