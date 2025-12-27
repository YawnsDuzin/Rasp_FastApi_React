"""
API Routes (API 라우트 모듈)
============================

[한국어 설명]
FastAPI 라우터 정의를 담당하는 모듈입니다.

FastAPI의 라우터 시스템:
- APIRouter: 관련된 엔드포인트들을 그룹화하는 클래스
- 라우터를 사용하면 대규모 앱을 여러 파일로 분리하여 관리할 수 있음
- 각 라우터는 prefix(접두사)와 tags(태그)를 가질 수 있음

이 프로젝트의 API 구조:
/api/
├── /hardware/   → 하드웨어 제어 (GPIO, PWM, 센서 등)
├── /system/     → 시스템 모니터링 (CPU, 메모리, 디스크)
├── /data/       → 데이터 히스토리 조회
└── /ws/         → WebSocket 실시간 통신

[English Description]
FastAPI router definitions for the HMI API.
Organizes API endpoints into logical groups with prefixes and tags.
"""

# ============================================================================
# 라이브러리 임포트 (Import Libraries)
# ============================================================================

# APIRouter: FastAPI의 라우터 클래스
# 엔드포인트들을 그룹화하고 나중에 메인 앱에 포함시킬 수 있음
from fastapi import APIRouter

# 각 도메인별 라우터 임포트
# [한국어 설명]
# Python의 상대 임포트(relative import) 사용:
# "." : 현재 패키지 (app.api)
# ".hardware" : 현재 패키지의 hardware 모듈
# "from .hardware import router as hardware_router"
#   → hardware.py의 router를 hardware_router라는 이름으로 가져옴
from .hardware import router as hardware_router    # 하드웨어 제어 라우터
from .system import router as system_router        # 시스템 모니터링 라우터
from .data import router as data_router            # 데이터 히스토리 라우터
from .websocket import router as websocket_router  # WebSocket 라우터


# ============================================================================
# 메인 API 라우터 생성 (Create Main API Router)
# ============================================================================

# 모든 서브 라우터를 포함할 최상위 라우터 생성
# [한국어 설명]
# 이 api_router는 main.py에서 app.include_router(api_router, prefix="/api")로 등록됨
# 결과적으로 모든 엔드포인트는 /api 아래에 위치하게 됨
api_router = APIRouter()


# ============================================================================
# 서브 라우터 포함 (Include Sub-routers)
# ============================================================================

# include_router() 메서드로 서브 라우터들을 메인 라우터에 추가
# [한국어 설명]
# 매개변수:
# - 첫 번째 인자: 포함할 라우터 객체
# - prefix: URL 경로 접두사 (예: "/hardware" → /api/hardware/...)
# - tags: Swagger 문서에서 그룹화할 태그 이름

# 하드웨어 라우터 포함
# 결과 경로: /api/hardware/...
# 예: /api/hardware/gpio, /api/hardware/sensors
api_router.include_router(hardware_router, prefix="/hardware", tags=["Hardware"])

# 시스템 라우터 포함
# 결과 경로: /api/system/...
# 예: /api/system/metrics, /api/system/health
api_router.include_router(system_router, prefix="/system", tags=["System"])

# 데이터 라우터 포함
# 결과 경로: /api/data/...
# 예: /api/data/sensors, /api/data/logs
api_router.include_router(data_router, prefix="/data", tags=["Data"])

# WebSocket 라우터 포함
# 결과 경로: /api/ws/...
# 예: /api/ws/live (WebSocket 연결 엔드포인트)
api_router.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])


# ============================================================================
# 모듈 내보내기 (Module Exports)
# ============================================================================

# __all__: 이 모듈에서 "from api import *" 할 때 내보낼 이름들
# [한국어 설명]
# Python의 모듈 시스템에서 공개 API를 명시적으로 정의
# 다른 모듈에서 "from app.api import api_router"로 사용
__all__ = ["api_router"]
