"""
System API Routes (시스템 API 라우트)
=====================================

[한국어 설명]
시스템 모니터링을 위한 REST API 엔드포인트들을 정의합니다.

이 모듈에서 제공하는 기능:
1. 시스템 메트릭 조회 (CPU, 메모리, 디스크 사용량)
2. 시스템 상태 요약
3. 헬스 체크 (경고 상태 포함)
4. 플랫폼 정보
5. 프로세스 정보
6. 애플리케이션 설정 정보

[English Description]
REST API endpoints for system monitoring.
Provides CPU, memory, disk metrics and health information.
"""

# ============================================================================
# 라이브러리 임포트 (Import Libraries)
# ============================================================================

# typing: 타입 힌트용 모듈
from typing import Dict, Any

# FastAPI 라우터 클래스
from fastapi import APIRouter

# system_monitor: 시스템 메트릭을 수집하는 서비스 (싱글톤)
# psutil 라이브러리를 사용하여 CPU, 메모리, 디스크 사용량 등을 측정
from app.services.system_monitor import system_monitor

# settings: 애플리케이션 설정 객체
from app.core.config import settings

# 로거 가져오기
from app.core.logging_config import get_logger

# 이 모듈용 로거 생성
logger = get_logger(__name__)

# 라우터 인스턴스 생성
# 이 router는 __init__.py에서 "/system" 접두사와 함께 등록됨
router = APIRouter()


# ============================================================================
# 시스템 메트릭 엔드포인트 (System Metrics Endpoints)
# ============================================================================

@router.get("/metrics")
async def get_system_metrics() -> Dict[str, Any]:
    """
    현재 시스템 메트릭 조회 (Get Current System Metrics)

    [한국어 설명]
    현재 시스템의 상세 성능 지표를 반환합니다.

    반환 데이터:
    - cpu_percent: CPU 사용률 (%)
    - memory_percent: 메모리 사용률 (%)
    - memory_used: 사용 중인 메모리 (바이트)
    - memory_total: 전체 메모리 (바이트)
    - disk_percent: 디스크 사용률 (%)
    - disk_used: 사용 중인 디스크 (바이트)
    - disk_total: 전체 디스크 (바이트)
    - cpu_temp: CPU 온도 (라즈베리 파이만)
    - uptime: 시스템 가동 시간

    API 경로: GET /api/system/metrics

    응답 예시:
    {
        "cpu_percent": 15.2,
        "memory_percent": 45.8,
        "memory_used": 1932804096,
        "memory_total": 4218507264,
        "disk_percent": 32.1,
        "cpu_temp": 52.5,
        "uptime": 86400
    }
    """
    # system_monitor.current: 가장 최근에 수집된 시스템 메트릭
    metrics = system_monitor.current

    if metrics:
        # to_dict(): 메트릭 객체를 딕셔너리로 변환
        return metrics.to_dict()

    # 메트릭이 아직 수집되지 않은 경우
    return {"error": "No metrics available"}


@router.get("/summary")
async def get_system_summary() -> Dict[str, Any]:
    """
    시스템 상태 요약 조회 (Get System Status Summary)

    [한국어 설명]
    시스템 상태의 간단한 요약 정보를 반환합니다.
    대시보드에서 빠르게 시스템 상태를 표시할 때 유용합니다.

    API 경로: GET /api/system/summary

    응답 예시:
    {
        "status": "healthy",
        "cpu": "15%",
        "memory": "45%",
        "disk": "32%",
        "temperature": "52°C"
    }
    """
    return system_monitor.get_summary()


@router.get("/health")
async def get_system_health() -> Dict[str, Any]:
    """
    시스템 헬스 상태 조회 (Get System Health Status with Warnings)

    [한국어 설명]
    시스템 상태와 함께 경고 정보를 반환합니다.

    경고 발생 조건 예시:
    - CPU 사용률 > 80%
    - 메모리 사용률 > 85%
    - 디스크 사용률 > 90%
    - CPU 온도 > 70°C (라즈베리 파이)

    API 경로: GET /api/system/health

    응답 예시:
    {
        "status": "warning",
        "warnings": [
            "High memory usage: 87%",
            "CPU temperature high: 72°C"
        ],
        "metrics": {...}
    }
    """
    return system_monitor.check_health()


@router.get("/platform")
async def get_platform_info() -> Dict[str, Any]:
    """
    플랫폼 정보 조회 (Get Platform Information)

    [한국어 설명]
    현재 실행 중인 시스템의 플랫폼 정보를 반환합니다.
    운영체제, 아키텍처, 파이썬 버전 등의 정보를 포함합니다.

    API 경로: GET /api/system/platform

    응답 예시:
    {
        "system": "Linux",
        "release": "5.10.0-rpi",
        "machine": "armv7l",
        "processor": "ARMv7 Processor rev 4",
        "python_version": "3.9.2",
        "is_raspberry_pi": true
    }
    """
    return system_monitor.get_platform_info()


@router.get("/process")
async def get_process_info() -> Dict[str, Any]:
    """
    현재 프로세스 정보 조회 (Get Current Process Information)

    [한국어 설명]
    현재 실행 중인 FastAPI 애플리케이션 프로세스의 정보를 반환합니다.

    반환 데이터:
    - pid: 프로세스 ID
    - cpu_percent: 이 프로세스의 CPU 사용률
    - memory_percent: 이 프로세스의 메모리 사용률
    - memory_rss: 실제 사용 중인 메모리 (Resident Set Size)
    - threads: 스레드 수
    - open_files: 열린 파일 수
    - connections: 네트워크 연결 수

    API 경로: GET /api/system/process

    응답 예시:
    {
        "pid": 1234,
        "cpu_percent": 2.5,
        "memory_percent": 1.8,
        "memory_rss": 52428800,
        "threads": 4,
        "open_files": 15,
        "connections": 3
    }
    """
    return system_monitor.get_process_info()


@router.get("/config")
async def get_config_info() -> Dict[str, Any]:
    """
    애플리케이션 설정 정보 조회 (Get Application Configuration - Non-sensitive)

    [한국어 설명]
    현재 애플리케이션의 설정 정보 중 민감하지 않은 정보만 반환합니다.
    보안상 민감한 정보(비밀번호, API 키 등)는 포함하지 않습니다.

    반환 데이터:
    - app_name: 앱 이름
    - app_version: 앱 버전
    - debug: 디버그 모드 여부
    - simulation_mode: 시뮬레이션 모드 여부
    - hardware_update_interval: 하드웨어 업데이트 간격
    - data_log_interval: 데이터 로깅 간격
    - data_retention_days: 데이터 보관 기간
    - platform: 플랫폼 정보

    API 경로: GET /api/system/config

    응답 예시:
    {
        "app_name": "Raspberry Pi HMI",
        "app_version": "1.0.0",
        "debug": false,
        "simulation_mode": true,
        "hardware_update_interval": 0.5,
        "data_log_interval": 5.0,
        "data_retention_days": 30,
        "platform": {
            "system": "Windows",
            "is_raspberry_pi": false,
            ...
        }
    }
    """
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "simulation_mode": settings.SIMULATION_MODE,
        "hardware_update_interval": settings.HARDWARE_UPDATE_INTERVAL,
        "data_log_interval": settings.DATA_LOG_INTERVAL,
        "data_retention_days": settings.DATA_RETENTION_DAYS,
        "platform": settings.platform_info
    }
