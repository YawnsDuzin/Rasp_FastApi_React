"""
Data Logger Service (데이터 로거 서비스)
===================

[한국어 설명]
센서 데이터를 SQLite 데이터베이스에 영구 저장하는 서비스입니다.
설정된 주기로 자동으로 데이터를 기록하고, 이력 조회 기능을 제공합니다.

[핵심 개념]
1. 데이터 영속화 (Data Persistence):
   - 센서 데이터를 휘발성 메모리가 아닌 DB에 저장
   - 시스템 재시작 후에도 데이터 유지
   - 장기 트렌드 분석 가능

2. 콜백 기반 로깅:
   - HardwareManager의 데이터 변경 콜백에 연결
   - 센서 데이터가 업데이트될 때마다 자동 저장
   - 비동기 처리로 하드웨어 성능에 영향 없음

3. 데이터 조회 패턴:
   - 시간 범위 기반 필터링
   - 센서 유형별 필터링
   - 통계 집계 (min, max, avg)

[SQLAlchemy 쿼리 빌더]
이 모듈에서 사용하는 SQLAlchemy 쿼리 패턴:
- select(): SELECT 쿼리 시작
- .where(): WHERE 조건 추가
- .order_by(): ORDER BY 추가
- .limit(): LIMIT 추가
- func.min/max/avg/count(): 집계 함수
"""

import asyncio  # 비동기 프로그래밍

# 타입 힌트
from typing import Dict, Any, Optional, List

# 날짜/시간 처리
from datetime import datetime, timedelta

# [SQLAlchemy 쿼리 함수들]
# select: SELECT 쿼리 생성
# func: SQL 함수 (COUNT, SUM, AVG 등) 접근
# desc: 내림차순 정렬
from sqlalchemy import select, func, desc

# 비동기 세션 타입
from sqlalchemy.ext.asyncio import AsyncSession

# 프로젝트 설정 및 로거
from app.core.config import settings
from app.core.logging_config import get_logger

# 데이터베이스 세션 팩토리
from app.models.database import async_session

# ORM 모델들
from app.models.sensor_data import SensorData
from app.models.system_log import SystemLog, LogLevel
from app.models.device_state import DeviceState

# 하드웨어 데이터 타입 (콜백에서 받는 데이터 형식)
from app.hardware.manager import HardwareData

# 이 모듈용 로거
logger = get_logger(__name__)


# ==================== 데이터 로거 클래스 ====================
class DataLogger:
    """
    Service for logging data to SQLite database.
    SQLite 데이터베이스에 데이터를 기록하는 서비스.

    [한국어 설명]
    센서 데이터, 시스템 이벤트, 장치 상태 변경을 DB에 기록하고
    이력 데이터를 조회하는 기능을 제공합니다.

    Features:
    - 주기적 자동 센서 데이터 로깅
    - 시스템 이벤트 로깅
    - 장치 상태 변경 이력
    - 트렌드 분석을 위한 데이터 조회

    [사용 패턴]
    1. 인스턴스 생성 (전역 싱글톤)
    2. start()로 로깅 시작
    3. HardwareManager 콜백에 log_hardware_data 등록
    4. stop()으로 로깅 중지
    """

    def __init__(self):
        """
        DataLogger 초기화.

        [속성 설명]
        - _log_interval: 로깅 간격 (초 단위)
        - _log_task: 백그라운드 로깅 태스크
        - _running: 서비스 실행 상태 플래그
        - _last_data: 마지막으로 받은 하드웨어 데이터
        """
        # 설정에서 로깅 간격 가져오기 (기본 5초)
        self._log_interval = settings.DATA_LOG_INTERVAL

        # [Optional[asyncio.Task]]
        # 백그라운드 로깅 작업의 핸들
        # None이면 태스크가 실행 중이 아님
        self._log_task: Optional[asyncio.Task] = None

        # 실행 상태 플래그 (시작/중지 제어)
        self._running = False

        # 마지막으로 로깅한 하드웨어 데이터 (중복 방지 등에 활용 가능)
        self._last_data: Optional[HardwareData] = None

    # ==================== 생명주기 메서드 ====================
    async def start(self) -> None:
        """
        Start the data logging loop.
        데이터 로깅 루프 시작.

        [한국어 설명]
        데이터 로거 서비스를 활성화합니다.
        이 메서드가 호출되어야 log_hardware_data()가 실제로 DB에 기록합니다.
        """
        # 이미 실행 중이면 무시 (중복 시작 방지)
        if self._running:
            return

        self._running = True
        logger.info(f"Data logger started (interval: {self._log_interval}s)")

    async def stop(self) -> None:
        """
        Stop the data logging loop.
        데이터 로깅 루프 중지.

        [한국어 설명]
        데이터 로거 서비스를 비활성화합니다.
        진행 중인 백그라운드 태스크가 있다면 정리합니다.
        """
        self._running = False

        # [백그라운드 태스크 정리]
        if self._log_task:
            # cancel(): 태스크에 취소 요청
            self._log_task.cancel()
            try:
                # 취소가 완료될 때까지 대기
                await self._log_task
            except asyncio.CancelledError:
                # CancelledError는 정상적인 취소 신호이므로 무시
                pass
            self._log_task = None

        logger.info("Data logger stopped")

    # ==================== 데이터 로깅 메서드 ====================
    async def log_hardware_data(self, data: HardwareData) -> None:
        """
        Log hardware data to database.
        하드웨어 데이터를 데이터베이스에 기록.

        [한국어 설명]
        HardwareManager의 콜백으로 등록되어 호출됩니다.
        센서 데이터를 SensorData 테이블에 저장합니다.

        Args:
            data: HardwareManager에서 수집한 HardwareData 객체

        [콜백 등록 예시]
        hardware_manager.register_callback(data_logger.log_hardware_data)
        """
        # 마지막 데이터 저장 (참조용)
        self._last_data = data

        # 서비스가 실행 중이 아니면 기록하지 않음
        if not self._running:
            return

        try:
            # [비동기 세션 컨텍스트]
            # async with로 세션 생성, 사용 후 자동 정리
            async with async_session() as session:
                # [SensorData 객체 생성]
                # HardwareData의 속성들을 SensorData 컬럼에 매핑
                sensor_data = SensorData(
                    sensor_type="all",  # 모든 센서 데이터 통합
                    temperature=data.temperature,
                    humidity=data.humidity,
                    pressure=data.pressure,
                    altitude=data.altitude,
                    distance=data.distance,
                    light_level=data.light_level,
                    soil_moisture=data.soil_moisture,
                    # bool을 int로 변환 (SQLite 호환)
                    motion=1 if data.motion else 0,
                    # I2C와 SPI ADC 값들을 JSON으로 저장
                    adc_values={
                        "i2c": data.adc_values,  # ADS1115에서 읽은 값
                        "spi": data.spi_adc_values  # MCP3008에서 읽은 값
                    }
                )

                # [session.add()]
                # 세션에 새 객체 추가 (INSERT 준비)
                session.add(sensor_data)

                # [session.commit()]
                # 변경사항을 DB에 영구 저장
                await session.commit()

        except Exception as e:
            # 로깅 실패는 치명적이지 않으므로 에러 로그만 남김
            logger.error(f"Failed to log sensor data: {e}")

    async def log_system_event(
        self,
        level: LogLevel,
        source: str,
        message: str,
        details: Dict[str, Any] = None,
        user_action: bool = False
    ) -> None:
        """
        Log a system event.
        시스템 이벤트 로깅.

        [한국어 설명]
        시스템에서 발생한 이벤트를 SystemLog 테이블에 기록합니다.
        에러, 경고, 정보성 이벤트 등을 추적할 수 있습니다.

        Args:
            level: 로그 레벨 (LogLevel 열거형)
            source: 이벤트 발생 소스 (모듈명)
            message: 로그 메시지
            details: 추가 상세 정보 (선택적)
            user_action: 사용자 행동 여부

        [사용 예시]
        await data_logger.log_system_event(
            level=LogLevel.ERROR,
            source="gpio_controller",
            message="GPIO 초기화 실패",
            details={"pin": 17, "error": "Permission denied"}
        )
        """
        try:
            async with async_session() as session:
                # SystemLog 팩토리 메서드 사용
                log_entry = SystemLog.create_log(
                    level=level,
                    source=source,
                    message=message,
                    details=details,
                    user_action=user_action
                )
                session.add(log_entry)
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to log system event: {e}")

    async def log_device_change(
        self,
        device_type: str,
        device_id: str,
        new_state: Dict[str, Any],
        previous_state: Dict[str, Any] = None,
        changed_by: str = "system"
    ) -> None:
        """
        Log a device state change.
        장치 상태 변경 기록.

        [한국어 설명]
        LED, 릴레이, 서보 등 장치의 상태 변경을 기록합니다.
        이전 상태와 새 상태를 함께 저장하여 변경 추적이 가능합니다.

        Args:
            device_type: 장치 유형 (예: "led", "relay")
            device_id: 장치 식별자 (예: "led_1")
            new_state: 새로운 상태 딕셔너리
            previous_state: 이전 상태 딕셔너리
            changed_by: 변경 주체 (user/system/schedule)

        [사용 예시]
        await data_logger.log_device_change(
            device_type="led",
            device_id="led_1",
            new_state={"on": True},
            previous_state={"on": False},
            changed_by="user"
        )
        """
        try:
            async with async_session() as session:
                # DeviceState 팩토리 메서드 사용
                state_record = DeviceState.record_change(
                    device_type=device_type,
                    device_id=device_id,
                    new_state=new_state,
                    previous_state=previous_state,
                    changed_by=changed_by
                )
                session.add(state_record)
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to log device change: {e}")

    # ==================== 데이터 조회 메서드 ====================
    async def get_sensor_history(
        self,
        sensor_type: str = "all",
        hours: int = 24,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get sensor data history.
        센서 데이터 이력 조회.

        [한국어 설명]
        지정된 시간 범위 내의 센서 데이터를 조회합니다.
        차트 표시나 데이터 분석에 사용됩니다.

        Args:
            sensor_type: 센서 유형 필터 (기본: "all")
            hours: 조회할 시간 범위 (기본: 24시간)
            limit: 최대 레코드 수 (기본: 1000)

        Returns:
            센서 데이터 딕셔너리 리스트

        [SQLAlchemy 쿼리 패턴]
        select(Model).where(조건).order_by(정렬).limit(제한)
        """
        try:
            async with async_session() as session:
                # [시간 범위 계산]
                # 현재 시간에서 hours시간 전까지
                cutoff = datetime.now() - timedelta(hours=hours)

                # [SELECT 쿼리 시작]
                # select(SensorData): SensorData 테이블 전체 조회
                # .where(...): WHERE 조건 추가
                query = select(SensorData).where(
                    SensorData.timestamp > cutoff
                )

                # [조건부 필터 추가]
                # sensor_type이 "all"이 아니면 추가 필터
                if sensor_type != "all":
                    query = query.where(SensorData.sensor_type == sensor_type)

                # [정렬 및 제한]
                # desc(): 내림차순 (최신 데이터 먼저)
                # limit(): 결과 수 제한
                query = query.order_by(desc(SensorData.timestamp)).limit(limit)

                # [쿼리 실행]
                result = await session.execute(query)

                # [결과 추출]
                # scalars(): Row 객체를 실제 모델 객체로 변환
                # all(): 모든 결과를 리스트로 반환
                records = result.scalars().all()

                # [딕셔너리 변환]
                # 각 ORM 객체를 to_dict()로 변환
                return [record.to_dict() for record in records]

        except Exception as e:
            logger.error(f"Failed to get sensor history: {e}")
            return []

    async def get_temperature_trend(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get temperature trend data.
        온도 트렌드 데이터 조회.

        [한국어 설명]
        온도 데이터만 추출하여 시계열 형태로 반환합니다.
        차트에서 온도 그래프를 그릴 때 사용합니다.

        Args:
            hours: 조회할 시간 범위

        Returns:
            [{"timestamp": "...", "value": 25.5}, ...]
        """
        try:
            async with async_session() as session:
                cutoff = datetime.now() - timedelta(hours=hours)

                # [특정 컬럼만 선택]
                # select(컬럼1, 컬럼2): 필요한 컬럼만 조회
                query = select(
                    SensorData.timestamp,
                    SensorData.temperature
                ).where(
                    SensorData.timestamp > cutoff,
                    # [.isnot(None)]
                    # IS NOT NULL 조건
                    # temperature가 NULL이 아닌 레코드만
                    SensorData.temperature.isnot(None)
                ).order_by(SensorData.timestamp)  # 시간순 정렬 (오래된 것부터)

                result = await session.execute(query)

                # [all()의 반환 타입]
                # 컬럼을 지정하면 Row 튜플 리스트 반환
                # 각 Row는 .timestamp, .temperature 속성 접근 가능
                records = result.all()

                # [시계열 데이터 형식으로 변환]
                return [
                    {"timestamp": r.timestamp.isoformat(), "value": r.temperature}
                    for r in records
                ]

        except Exception as e:
            logger.error(f"Failed to get temperature trend: {e}")
            return []

    async def get_system_logs(
        self,
        level: str = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get system logs.
        시스템 로그 조회.

        [한국어 설명]
        시스템 로그를 조회합니다.
        로그 레벨로 필터링할 수 있습니다.

        Args:
            level: 로그 레벨 필터 (선택적, 예: "ERROR")
            hours: 조회할 시간 범위
            limit: 최대 레코드 수

        Returns:
            로그 딕셔너리 리스트
        """
        try:
            async with async_session() as session:
                cutoff = datetime.now() - timedelta(hours=hours)

                query = select(SystemLog).where(
                    SystemLog.timestamp > cutoff
                )

                # 레벨 필터 (옵션)
                if level:
                    query = query.where(SystemLog.level == level)

                query = query.order_by(desc(SystemLog.timestamp)).limit(limit)

                result = await session.execute(query)
                records = result.scalars().all()

                return [record.to_dict() for record in records]

        except Exception as e:
            logger.error(f"Failed to get system logs: {e}")
            return []

    async def get_device_history(
        self,
        device_type: str = None,
        device_id: str = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get device state history.
        장치 상태 이력 조회.

        [한국어 설명]
        장치 상태 변경 이력을 조회합니다.
        특정 장치 유형이나 ID로 필터링할 수 있습니다.

        Args:
            device_type: 장치 유형 필터 (선택적)
            device_id: 장치 ID 필터 (선택적)
            hours: 조회할 시간 범위

        Returns:
            장치 상태 딕셔너리 리스트
        """
        try:
            async with async_session() as session:
                cutoff = datetime.now() - timedelta(hours=hours)

                query = select(DeviceState).where(
                    DeviceState.timestamp > cutoff
                )

                # [다중 조건 필터]
                if device_type:
                    query = query.where(DeviceState.device_type == device_type)
                if device_id:
                    query = query.where(DeviceState.device_id == device_id)

                query = query.order_by(desc(DeviceState.timestamp))

                result = await session.execute(query)
                records = result.scalars().all()

                return [record.to_dict() for record in records]

        except Exception as e:
            logger.error(f"Failed to get device history: {e}")
            return []

    async def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get data statistics for the specified period.
        지정된 기간의 데이터 통계 조회.

        [한국어 설명]
        센서 데이터의 통계 정보를 계산합니다.
        대시보드의 요약 정보에 사용됩니다.

        Args:
            hours: 통계 계산 기간

        Returns:
            통계 딕셔너리 (개수, 최소/최대/평균 등)

        [SQL 집계 함수]
        - func.count(): COUNT()
        - func.min(): MIN()
        - func.max(): MAX()
        - func.avg(): AVG()
        """
        try:
            async with async_session() as session:
                cutoff = datetime.now() - timedelta(hours=hours)

                # [센서 데이터 개수]
                # select(func.count(컬럼)): COUNT 쿼리
                sensor_count = await session.execute(
                    select(func.count(SensorData.id)).where(
                        SensorData.timestamp > cutoff
                    )
                )

                # [온도 통계]
                # 여러 집계 함수를 한 쿼리에서 실행
                temp_stats = await session.execute(
                    select(
                        func.min(SensorData.temperature),  # 최소 온도
                        func.max(SensorData.temperature),  # 최대 온도
                        func.avg(SensorData.temperature)   # 평균 온도
                    ).where(
                        SensorData.timestamp > cutoff,
                        SensorData.temperature.isnot(None)
                    )
                )

                # [.one()]
                # 정확히 하나의 행만 반환 (집계 함수 결과)
                # 여러 값을 튜플로 언패킹
                temp_min, temp_max, temp_avg = temp_stats.one()

                # [로그 레벨별 개수]
                # GROUP BY를 사용한 집계
                log_counts = await session.execute(
                    select(
                        SystemLog.level,
                        func.count(SystemLog.id)
                    ).where(
                        SystemLog.timestamp > cutoff
                    ).group_by(SystemLog.level)  # 레벨별로 그룹화
                )

                return {
                    "period_hours": hours,
                    # [.scalar()]
                    # 단일 값 반환 (COUNT 결과)
                    "sensor_readings": sensor_count.scalar() or 0,
                    "temperature": {
                        # round(): 소수점 자리수 제한
                        "min": round(temp_min, 1) if temp_min else None,
                        "max": round(temp_max, 1) if temp_max else None,
                        "avg": round(temp_avg, 1) if temp_avg else None
                    },
                    # [딕셔너리 컴프리헨션]
                    # {level: count for level, count in ...}
                    # 예: {"INFO": 50, "ERROR": 3}
                    "log_counts": {level: count for level, count in log_counts.all()}
                }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}


# ==================== 전역 인스턴스 ====================
# [싱글톤 패턴]
# 모듈 레벨에서 인스턴스 생성
# 다른 모듈에서 from ... import data_logger로 같은 인스턴스 사용
data_logger = DataLogger()
