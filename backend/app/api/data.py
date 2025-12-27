"""
Data API Routes (데이터 API 라우트)
====================================

[한국어 설명]
데이터 히스토리 조회와 로깅을 위한 REST API 엔드포인트들을 정의합니다.

이 모듈에서 제공하는 기능:
1. 센서 데이터 히스토리 조회
2. 온도 트렌드 데이터 조회 (차트용)
3. 시스템 로그 조회
4. 장치 상태 변경 이력 조회
5. 데이터 통계 조회
6. 오래된 데이터 정리

데이터베이스:
- SQLite + SQLAlchemy ORM 사용
- WAL 모드로 읽기/쓰기 성능 최적화
- 비동기(async) 쿼리 지원

[English Description]
REST API endpoints for data history and logging.
Provides sensor history, logs, device history, and statistics.
"""

# ============================================================================
# 라이브러리 임포트 (Import Libraries)
# ============================================================================

# typing: 타입 힌트용 모듈
from typing import Dict, Any, List, Optional

# FastAPI 관련 클래스들
# APIRouter: 엔드포인트 그룹화
# Query: URL 쿼리 파라미터 정의
from fastapi import APIRouter, Query

# data_logger: 데이터베이스에 데이터를 기록하고 조회하는 서비스
from app.services.data_logger import data_logger

# cleanup_old_data: 오래된 데이터를 정리하는 함수
from app.models.database import cleanup_old_data

# 로거 가져오기
from app.core.logging_config import get_logger

# 이 모듈용 로거 생성
logger = get_logger(__name__)

# 라우터 인스턴스 생성
# 이 router는 __init__.py에서 "/data" 접두사와 함께 등록됨
router = APIRouter()


# ============================================================================
# 센서 데이터 엔드포인트 (Sensor Data Endpoints)
# ============================================================================

@router.get("/sensors")
async def get_sensor_history(
    sensor_type: str = Query("all", description="Sensor type filter"),
    hours: int = Query(24, ge=1, le=168, description="Hours of history"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records")
) -> List[Dict[str, Any]]:
    """
    센서 데이터 히스토리 조회 (Get Sensor Data History)

    [한국어 설명]
    Query() 파라미터 설명:
    - sensor_type: 필터링할 센서 종류 ("all"이면 전체)
        - "temperature": 온도 데이터만
        - "humidity": 습도 데이터만
        - "distance": 거리 데이터만
        - "all": 모든 센서 데이터
    - hours: 조회할 시간 범위 (1~168시간, 기본 24시간)
        - ge=1: 최소 1시간
        - le=168: 최대 168시간 (7일)
    - limit: 최대 반환 레코드 수 (1~10000, 기본 1000)

    API 경로: GET /api/data/sensors?sensor_type=temperature&hours=24&limit=100

    응답 예시:
    [
        {
            "id": 1,
            "timestamp": "2024-01-01T12:00:00",
            "sensor_type": "temperature",
            "value": 25.5
        },
        {
            "id": 2,
            "timestamp": "2024-01-01T12:00:05",
            "sensor_type": "temperature",
            "value": 25.6
        },
        ...
    ]
    """
    return await data_logger.get_sensor_history(
        sensor_type=sensor_type,
        hours=hours,
        limit=limit
    )


@router.get("/temperature")
async def get_temperature_trend(
    hours: int = Query(24, ge=1, le=168, description="Hours of history")
) -> List[Dict[str, Any]]:
    """
    온도 트렌드 데이터 조회 (Get Temperature Trend Data for Charts)

    [한국어 설명]
    차트에 표시하기 적합한 형태로 온도 데이터를 반환합니다.
    시계열 그래프를 그리는 데 최적화된 형식입니다.

    API 경로: GET /api/data/temperature?hours=24

    응답 예시:
    [
        {"timestamp": "2024-01-01T12:00:00", "temperature": 25.5},
        {"timestamp": "2024-01-01T12:05:00", "temperature": 25.7},
        {"timestamp": "2024-01-01T12:10:00", "temperature": 25.4},
        ...
    ]

    프론트엔드에서 사용 예시 (Recharts):
    <LineChart data={temperatureData}>
        <XAxis dataKey="timestamp" />
        <YAxis />
        <Line dataKey="temperature" />
    </LineChart>
    """
    return await data_logger.get_temperature_trend(hours=hours)


# ============================================================================
# 로그 엔드포인트 (Log Endpoints)
# ============================================================================

@router.get("/logs")
async def get_system_logs(
    level: Optional[str] = Query(None, description="Log level filter"),
    hours: int = Query(24, ge=1, le=168, description="Hours of history"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records")
) -> List[Dict[str, Any]]:
    """
    시스템 로그 조회 (Get System Logs)

    [한국어 설명]
    시스템에서 발생한 이벤트 로그를 조회합니다.

    Query 파라미터:
    - level: 로그 레벨 필터 (선택사항)
        - None: 모든 레벨
        - "INFO": 정보 로그만
        - "WARNING": 경고 로그만
        - "ERROR": 에러 로그만
    - hours: 조회할 시간 범위
    - limit: 최대 반환 레코드 수 (기본 100)

    API 경로: GET /api/data/logs?level=ERROR&hours=24&limit=50

    응답 예시:
    [
        {
            "id": 1,
            "timestamp": "2024-01-01T12:00:00",
            "level": "ERROR",
            "component": "hardware.gpio",
            "message": "Failed to read GPIO pin 17",
            "user_action": false
        },
        {
            "id": 2,
            "timestamp": "2024-01-01T12:05:00",
            "level": "INFO",
            "component": "hardware.gpio",
            "message": "LED 0 set to ON",
            "user_action": true
        },
        ...
    ]
    """
    return await data_logger.get_system_logs(
        level=level,
        hours=hours,
        limit=limit
    )


# ============================================================================
# 장치 상태 이력 엔드포인트 (Device History Endpoints)
# ============================================================================

@router.get("/devices")
async def get_device_history(
    device_type: Optional[str] = Query(None, description="Device type filter"),
    device_id: Optional[str] = Query(None, description="Device ID filter"),
    hours: int = Query(24, ge=1, le=168, description="Hours of history")
) -> List[Dict[str, Any]]:
    """
    장치 상태 변경 이력 조회 (Get Device State History)

    [한국어 설명]
    LED, 릴레이, 모터 등 장치의 상태 변경 이력을 조회합니다.
    어떤 장치가 언제 어떻게 변경되었는지 추적할 수 있습니다.

    Query 파라미터:
    - device_type: 장치 종류 필터 (선택사항)
        - "led": LED 이력만
        - "relay": 릴레이 이력만
        - "motor": 모터 이력만
        - "servo": 서보 이력만
    - device_id: 특정 장치 ID 필터 (선택사항)
        - 예: "0", "1", "2" (LED 인덱스)
    - hours: 조회할 시간 범위

    API 경로: GET /api/data/devices?device_type=led&hours=24

    응답 예시:
    [
        {
            "id": 1,
            "timestamp": "2024-01-01T12:00:00",
            "device_type": "led",
            "device_id": "0",
            "previous_state": {"on": false},
            "new_state": {"on": true},
            "changed_by": "user"
        },
        {
            "id": 2,
            "timestamp": "2024-01-01T12:05:00",
            "device_type": "motor",
            "device_id": "0",
            "previous_state": {"speed": 0},
            "new_state": {"speed": 50},
            "changed_by": "user"
        },
        ...
    ]
    """
    return await data_logger.get_device_history(
        device_type=device_type,
        device_id=device_id,
        hours=hours
    )


# ============================================================================
# 통계 엔드포인트 (Statistics Endpoints)
# ============================================================================

@router.get("/statistics")
async def get_statistics(
    hours: int = Query(24, ge=1, le=168, description="Hours for statistics")
) -> Dict[str, Any]:
    """
    데이터 통계 조회 (Get Data Statistics)

    [한국어 설명]
    지정된 시간 범위 내의 데이터 통계를 반환합니다.
    대시보드에서 요약 정보를 표시하는 데 유용합니다.

    반환 데이터:
    - sensor_count: 센서 데이터 레코드 수
    - log_count: 로그 레코드 수
    - device_changes: 장치 상태 변경 횟수
    - temperature_avg: 평균 온도
    - temperature_min: 최저 온도
    - temperature_max: 최고 온도
    - humidity_avg: 평균 습도

    API 경로: GET /api/data/statistics?hours=24

    응답 예시:
    {
        "sensor_count": 1728,
        "log_count": 45,
        "device_changes": 120,
        "temperature": {
            "avg": 25.3,
            "min": 22.1,
            "max": 28.7
        },
        "humidity": {
            "avg": 55.2,
            "min": 45.0,
            "max": 65.8
        }
    }
    """
    return await data_logger.get_statistics(hours=hours)


# ============================================================================
# 데이터 정리 엔드포인트 (Data Cleanup Endpoints)
# ============================================================================

@router.post("/cleanup")
async def cleanup_data(
    retention_days: int = Query(30, ge=1, le=365, description="Retention period in days")
) -> Dict[str, Any]:
    """
    오래된 데이터 정리 (Clean Up Old Data)

    [한국어 설명]
    지정된 보관 기간보다 오래된 데이터를 삭제합니다.
    SD 카드 용량 관리와 성능 유지를 위해 주기적으로 실행하면 좋습니다.

    주의사항:
    - 이 작업은 되돌릴 수 없습니다!
    - 삭제된 데이터는 복구할 수 없습니다.
    - 프로덕션 환경에서는 권한 제어를 추가하는 것이 좋습니다.

    Query 파라미터:
    - retention_days: 보관 기간 (1~365일, 기본 30일)
        - 이 기간보다 오래된 데이터가 삭제됨

    API 경로: POST /api/data/cleanup?retention_days=30

    응답 예시:
    {
        "success": true,
        "deleted_records": 15000,
        "retention_days": 30
    }

    삭제되는 데이터:
    - 센서 데이터 (sensor_data 테이블)
    - 시스템 로그 (system_log 테이블)
    - 장치 상태 이력 (device_state 테이블)
    """
    # 오래된 데이터 삭제 실행
    deleted = await cleanup_old_data(retention_days=retention_days)

    return {
        "success": True,
        "deleted_records": deleted,    # 삭제된 레코드 수
        "retention_days": retention_days  # 적용된 보관 기간
    }
