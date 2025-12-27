"""
WebSocket API Routes (WebSocket API 라우트)
============================================

[한국어 설명]
실시간 양방향 통신을 위한 WebSocket 엔드포인트들을 정의합니다.

WebSocket이란?
- HTTP와 달리 클라이언트-서버 간 지속적인 연결을 유지
- 서버에서 클라이언트로 데이터를 즉시 푸시(push) 가능
- 실시간 데이터 업데이트에 적합 (센서 값, 시스템 상태 등)

HTTP vs WebSocket:
- HTTP: 요청-응답 방식, 클라이언트가 매번 요청해야 함
- WebSocket: 연결 유지, 서버가 원할 때 데이터 전송 가능

이 모듈에서 제공하는 기능:
1. 실시간 하드웨어 데이터 업데이트
2. 시스템 메트릭 실시간 전송
3. 로그 실시간 전송
4. 토픽 기반 구독 시스템

[English Description]
WebSocket endpoints for real-time bidirectional communication.
Provides live hardware data, system metrics, and log updates.
"""

# ============================================================================
# 라이브러리 임포트 (Import Libraries)
# ============================================================================

# typing: 타입 힌트용 모듈
from typing import Dict, Any

# FastAPI WebSocket 관련 클래스들
# APIRouter: 엔드포인트 그룹화
# WebSocket: WebSocket 연결 객체
# WebSocketDisconnect: WebSocket 연결 종료 예외
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

# ws_manager: WebSocket 연결들을 관리하는 매니저 (싱글톤)
from app.services.websocket_manager import ws_manager

# 로거 가져오기
from app.core.logging_config import get_logger

# 이 모듈용 로거 생성
logger = get_logger(__name__)

# 라우터 인스턴스 생성
# 이 router는 __init__.py에서 "/ws" 접두사와 함께 등록됨
router = APIRouter()


# ============================================================================
# WebSocket 엔드포인트 (WebSocket Endpoints)
# ============================================================================

@router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    """
    메인 WebSocket 엔드포인트 (Main WebSocket Endpoint for Real-time Data)

    [한국어 설명]
    @router.websocket(): WebSocket 연결을 처리하는 데코레이터
    - HTTP GET/POST와 다르게 지속적인 연결을 유지
    - 양방향 통신 가능 (서버 ↔ 클라이언트)

    연결 URL: ws://localhost:8000/api/ws/live
    (브라우저에서는 WebSocket API 또는 socket.io 등 사용)

    지원 기능:
    1. 실시간 하드웨어 데이터 수신
    2. 시스템 메트릭 수신
    3. 로그 업데이트 수신
    4. 토픽 기반 구독

    클라이언트 → 서버 메시지 예시:
    {
        "type": "subscribe",
        "topics": ["hardware", "system"]
    }

    서버 → 클라이언트 메시지 예시:
    {
        "type": "hardware_update",
        "data": {
            "temperature": 25.5,
            "humidity": 60.0,
            ...
        }
    }

    연결 흐름:
    1. 클라이언트가 WebSocket 연결 요청
    2. 서버가 연결 수락 (accept)
    3. 양방향 메시지 교환 시작
    4. 연결 종료 시 정리(cleanup) 수행
    """
    # 클라이언트 연결 처리
    # ws_manager.connect(): 연결을 수락하고 고유 클라이언트 ID 반환
    client_id = await ws_manager.connect(websocket)

    # 연결 실패 시 (예: 최대 연결 수 초과)
    if not client_id:
        return

    try:
        # 무한 루프: 연결이 유지되는 동안 클라이언트 메시지 수신
        while True:
            # 클라이언트로부터 텍스트 메시지 수신 대기
            # await: 메시지가 올 때까지 비동기 대기
            message = await websocket.receive_text()

            # 수신한 메시지 처리
            # 예: 구독 요청, 명령 등
            await ws_manager.handle_client_message(client_id, message)

    except WebSocketDisconnect:
        # WebSocketDisconnect: 클라이언트가 정상적으로 연결을 종료한 경우
        # 예: 브라우저 탭 닫기, 앱 종료
        await ws_manager.disconnect(client_id)

    except Exception as e:
        # 기타 예외: 네트워크 오류, 비정상 종료 등
        logger.error(f"WebSocket error for {client_id}: {e}")
        await ws_manager.disconnect(client_id)


# ============================================================================
# WebSocket 상태 조회 엔드포인트 (REST)
# ============================================================================
# [한국어 설명]
# 아래는 일반 HTTP 엔드포인트입니다.
# WebSocket 연결 상태를 조회하는 데 사용됩니다.

@router.get("/status")
async def get_websocket_status() -> Dict[str, Any]:
    """
    WebSocket 매니저 상태 조회 (Get WebSocket Manager Status)

    [한국어 설명]
    현재 WebSocket 매니저의 상태 정보를 반환합니다.

    반환 데이터:
    - running: 매니저 실행 중 여부
    - client_count: 현재 연결된 클라이언트 수
    - max_connections: 최대 허용 연결 수

    API 경로: GET /api/ws/status

    응답 예시:
    {
        "running": true,
        "client_count": 3,
        "max_connections": 10
    }
    """
    return ws_manager.get_status()


@router.get("/clients")
async def get_websocket_clients() -> Dict[str, Any]:
    """
    연결된 WebSocket 클라이언트 목록 조회 (Get List of Connected WebSocket Clients)

    [한국어 설명]
    현재 연결된 모든 WebSocket 클라이언트의 정보를 반환합니다.

    반환 데이터:
    - count: 연결된 클라이언트 수
    - clients: 클라이언트 정보 목록
        - client_id: 클라이언트 고유 ID
        - connected_at: 연결 시작 시간
        - subscriptions: 구독 중인 토픽 목록

    API 경로: GET /api/ws/clients

    응답 예시:
    {
        "count": 2,
        "clients": [
            {
                "client_id": "abc123",
                "connected_at": "2024-01-01T12:00:00",
                "subscriptions": ["hardware", "system"]
            },
            {
                "client_id": "def456",
                "connected_at": "2024-01-01T12:05:00",
                "subscriptions": ["logs"]
            }
        ]
    }
    """
    return {
        "count": ws_manager.client_count,  # 연결된 클라이언트 수
        "clients": ws_manager.clients       # 클라이언트 정보 목록
    }
