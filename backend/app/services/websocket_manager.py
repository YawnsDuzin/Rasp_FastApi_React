"""
WebSocket Manager (웹소켓 매니저)
=================

[한국어 설명]
실시간 데이터 푸시를 위한 WebSocket 연결 관리 서비스입니다.
다수의 클라이언트 연결과 메시지 브로드캐스트를 처리합니다.

[핵심 개념]
1. WebSocket:
   - HTTP와 달리 양방향 실시간 통신 지원
   - 한 번 연결되면 서버→클라이언트 푸시 가능
   - 센서 데이터 실시간 업데이트에 적합

2. 토픽 기반 구독 (Topic-based Subscription):
   - 클라이언트가 관심 있는 토픽만 구독
   - "hardware": 하드웨어 상태 업데이트
   - "system": 시스템 메트릭 업데이트
   - "logs": 시스템 로그 업데이트
   - "all": 모든 업데이트

3. Heartbeat (하트비트):
   - 주기적인 ping/pong으로 연결 상태 확인
   - 응답 없는 클라이언트 자동 연결 해제

[FastAPI WebSocket]
FastAPI는 Starlette 기반의 WebSocket 지원 내장
- 비동기 send/receive
- JSON 자동 직렬화
- 연결 상태 관리
"""

import asyncio  # 비동기 프로그래밍
import json     # JSON 파싱/직렬화

# 타입 힌트
from typing import Dict, Any, List, Set, Optional, Callable

# 날짜/시간 처리
from datetime import datetime

# 데이터 클래스 데코레이터
from dataclasses import dataclass, field

# [FastAPI WebSocket]
# FastAPI의 WebSocket 요청 객체
# HTTP Request와 유사하지만 양방향 통신 지원
from fastapi import WebSocket, WebSocketDisconnect

# [WebSocketState]
# WebSocket 연결 상태를 나타내는 열거형
# CONNECTING, CONNECTED, DISCONNECTED
from starlette.websockets import WebSocketState

# 프로젝트 설정 및 로거
from app.core.config import settings
from app.core.logging_config import get_logger

# 이 모듈용 로거
logger = get_logger(__name__)


# ==================== 클라이언트 정보 데이터 클래스 ====================
@dataclass
class ClientInfo:
    """
    Information about a connected WebSocket client.
    연결된 WebSocket 클라이언트 정보.

    [한국어 설명]
    각 WebSocket 클라이언트의 연결 정보와 상태를 저장합니다.
    구독 중인 토픽, 마지막 활동 시간 등을 추적합니다.
    """

    # [클라이언트 ID]
    # 고유 식별자 (예: "client_1", "client_2")
    id: str

    # [WebSocket 객체]
    # FastAPI의 WebSocket 연결 객체
    # 이 객체를 통해 메시지 송수신
    websocket: WebSocket

    # [연결 시간]
    # 클라이언트가 연결된 시간
    connected_at: datetime = field(default_factory=datetime.now)

    # [마지막 하트비트]
    # 마지막으로 응답받은 시간 (연결 상태 확인용)
    last_heartbeat: datetime = field(default_factory=datetime.now)

    # [구독 토픽]
    # 클라이언트가 구독 중인 토픽 집합
    # Set[str]: 중복 없는 문자열 집합
    # default_factory: 새 인스턴스마다 새 set() 생성
    subscriptions: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """
        딕셔너리로 변환.

        [한국어 설명]
        클라이언트 정보를 JSON 직렬화 가능한 형태로 변환합니다.
        관리 API에서 연결된 클라이언트 목록을 조회할 때 사용됩니다.
        """
        return {
            "id": self.id,
            "connected_at": self.connected_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            # set은 JSON 직렬화 불가하므로 list로 변환
            "subscriptions": list(self.subscriptions)
        }


# ==================== 웹소켓 매니저 클래스 ====================
class WebSocketManager:
    """
    Manager for WebSocket connections.
    WebSocket 연결 관리자.

    [한국어 설명]
    다수의 WebSocket 클라이언트 연결을 관리합니다.
    토픽 기반 구독과 메시지 브로드캐스트를 지원합니다.

    [주요 기능]
    - 다중 클라이언트 연결 관리
    - 토픽 기반 구독 시스템
    - 자동 하트비트/ping 전송
    - 메시지 브로드캐스팅
    - 연결 상태 모니터링
    """

    def __init__(self):
        """
        WebSocketManager 초기화.

        [속성 설명]
        - _clients: 연결된 클라이언트들 (ID -> ClientInfo)
        - _client_counter: 클라이언트 ID 생성용 카운터
        - _max_connections: 최대 동시 연결 수
        - _heartbeat_interval: 하트비트 전송 간격
        - _topics: 사용 가능한 구독 토픽
        """
        # [클라이언트 저장소]
        # Dict[str, ClientInfo]: 클라이언트 ID를 키로 사용
        self._clients: Dict[str, ClientInfo] = {}

        # [클라이언트 ID 카운터]
        # 새 클라이언트 연결 시 1씩 증가
        self._client_counter = 0

        # [최대 연결 수]
        # 설정에서 가져옴 (기본 50)
        # 리소스 보호를 위한 제한
        self._max_connections = settings.WS_MAX_CONNECTIONS

        # [하트비트 간격]
        # 설정에서 가져옴 (기본 30초)
        self._heartbeat_interval = settings.WS_HEARTBEAT_INTERVAL

        # [백그라운드 하트비트 태스크]
        self._heartbeat_task: Optional[asyncio.Task] = None

        # [실행 상태 플래그]
        self._running = False

        # [사용 가능한 토픽]
        # 클라이언트가 구독할 수 있는 토픽 목록
        # True: 해당 토픽이 활성화됨
        self._topics = {
            "hardware": True,  # 하드웨어 데이터 (GPIO, 센서 등)
            "system": True,    # 시스템 메트릭 (CPU, 메모리 등)
            "logs": True,      # 시스템 로그
            "all": True        # 모든 업데이트 (기본 구독)
        }

    # ==================== 프로퍼티 ====================
    @property
    def client_count(self) -> int:
        """
        Get number of connected clients.
        연결된 클라이언트 수 반환.
        """
        return len(self._clients)

    @property
    def clients(self) -> List[Dict[str, Any]]:
        """
        Get list of connected clients.
        연결된 클라이언트 목록 반환.

        [한국어 설명]
        현재 연결된 모든 클라이언트의 정보를 리스트로 반환합니다.
        관리 API에서 연결 상태를 확인할 때 사용합니다.
        """
        return [client.to_dict() for client in self._clients.values()]

    # ==================== 생명주기 메서드 ====================
    async def start(self) -> None:
        """
        Start the WebSocket manager.
        WebSocket 매니저 시작.

        [한국어 설명]
        하트비트 루프를 시작하여 연결 상태를 모니터링합니다.
        FastAPI 시작 시 lifespan에서 호출됩니다.
        """
        if self._running:
            return

        self._running = True

        # [하트비트 태스크 시작]
        # 백그라운드에서 주기적으로 ping 전송
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        logger.info("WebSocket manager started")

    async def stop(self) -> None:
        """
        Stop the WebSocket manager.
        WebSocket 매니저 중지.

        [한국어 설명]
        모든 클라이언트 연결을 종료하고 하트비트 루프를 중지합니다.
        FastAPI 종료 시 lifespan에서 호출됩니다.
        """
        self._running = False

        # 하트비트 태스크 취소
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # [모든 클라이언트 연결 종료]
        # list()로 복사본 생성 (반복 중 dict 수정 방지)
        for client_id in list(self._clients.keys()):
            await self.disconnect(client_id)

        logger.info("WebSocket manager stopped")

    # ==================== 연결 관리 메서드 ====================
    async def connect(self, websocket: WebSocket) -> Optional[str]:
        """
        Accept a new WebSocket connection.
        새 WebSocket 연결 수락.

        [한국어 설명]
        새 클라이언트의 WebSocket 연결을 수락하고 관리 목록에 추가합니다.
        최대 연결 수를 초과하면 연결을 거부합니다.

        Args:
            websocket: FastAPI WebSocket 객체

        Returns:
            str: 연결 성공 시 클라이언트 ID
            None: 연결 거부 시

        [WebSocket 연결 과정]
        1. 클라이언트가 ws:// URL로 연결 요청
        2. 서버가 accept()로 연결 수락
        3. 양방향 통신 가능 상태
        """
        # [최대 연결 수 체크]
        if len(self._clients) >= self._max_connections:
            logger.warning("WebSocket connection rejected: max connections reached")
            # [close()]
            # 연결 거부: HTTP 상태 코드와 이유 전송
            # 1013: "Try Again Later" (서버 과부하)
            await websocket.close(code=1013, reason="Max connections reached")
            return None

        # [연결 수락]
        # WebSocket 핸드셰이크 완료
        await websocket.accept()

        # [클라이언트 ID 생성]
        self._client_counter += 1
        client_id = f"client_{self._client_counter}"

        # [클라이언트 정보 저장]
        self._clients[client_id] = ClientInfo(
            id=client_id,
            websocket=websocket,
            # 기본적으로 "all" 토픽 구독
            subscriptions={"all"}
        )

        logger.info(f"WebSocket client connected: {client_id}")

        # [환영 메시지 전송]
        # 클라이언트에게 연결 성공과 할당된 ID 알림
        await self.send_to_client(client_id, {
            "type": "connected",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        })

        return client_id

    async def disconnect(self, client_id: str) -> None:
        """
        Disconnect a client.
        클라이언트 연결 해제.

        [한국어 설명]
        특정 클라이언트의 WebSocket 연결을 종료합니다.
        클라이언트 목록에서 제거하고 리소스를 정리합니다.

        Args:
            client_id: 연결 해제할 클라이언트 ID
        """
        # 존재하지 않는 클라이언트면 무시
        if client_id not in self._clients:
            return

        # [dict.pop()]
        # 키를 제거하고 값을 반환
        client = self._clients.pop(client_id)

        try:
            # [연결 상태 확인 후 종료]
            # 이미 닫힌 연결을 다시 닫으면 에러 발생
            if client.websocket.client_state == WebSocketState.CONNECTED:
                await client.websocket.close()
        except Exception as e:
            # 연결 종료 실패는 치명적이지 않음
            logger.debug(f"Error closing websocket: {e}")

        logger.info(f"WebSocket client disconnected: {client_id}")

    # ==================== 메시지 전송 메서드 ====================
    async def send_to_client(self, client_id: str, data: Dict[str, Any]) -> bool:
        """
        Send data to a specific client.
        특정 클라이언트에게 데이터 전송.

        [한국어 설명]
        특정 클라이언트에게 JSON 메시지를 전송합니다.
        전송 실패 시 해당 클라이언트 연결을 해제합니다.

        Args:
            client_id: 대상 클라이언트 ID
            data: 전송할 데이터 딕셔너리

        Returns:
            bool: 전송 성공 여부
        """
        if client_id not in self._clients:
            return False

        client = self._clients[client_id]

        try:
            # [send_json()]
            # Python dict를 JSON으로 직렬화하여 전송
            # FastAPI WebSocket의 편의 메서드
            await client.websocket.send_json(data)
            return True

        except Exception as e:
            logger.error(f"Failed to send to client {client_id}: {e}")
            # 전송 실패 시 연결 문제로 간주하여 연결 해제
            await self.disconnect(client_id)
            return False

    async def broadcast(self, data: Dict[str, Any], topic: str = "all") -> int:
        """
        Broadcast data to all subscribed clients.
        구독한 모든 클라이언트에게 데이터 브로드캐스트.

        [한국어 설명]
        특정 토픽을 구독한 모든 클라이언트에게 메시지를 전송합니다.
        "all" 토픽을 구독한 클라이언트는 모든 메시지를 받습니다.

        Args:
            data: 브로드캐스트할 데이터
            topic: 메시지 토픽 (기본: "all")

        Returns:
            int: 메시지를 받은 클라이언트 수
        """
        sent_count = 0

        # [메타데이터 추가]
        # 메시지에 토픽과 전송 시간 추가
        data["topic"] = topic
        data["broadcast_time"] = datetime.now().isoformat()

        # [모든 클라이언트에게 전송 시도]
        # list()로 복사본 순회 (전송 중 연결 해제 가능)
        for client_id, client in list(self._clients.items()):
            # [구독 확인]
            # 해당 토픽 또는 "all" 토픽을 구독 중이면 전송
            if topic in client.subscriptions or "all" in client.subscriptions:
                if await self.send_to_client(client_id, data):
                    sent_count += 1

        return sent_count

    # ==================== 특화된 브로드캐스트 메서드 ====================
    async def broadcast_hardware_data(self, data: Dict[str, Any]) -> int:
        """
        Broadcast hardware data update.
        하드웨어 데이터 업데이트 브로드캐스트.

        [한국어 설명]
        센서, GPIO, PWM 등의 하드웨어 데이터를
        "hardware" 토픽 구독자에게 전송합니다.
        """
        return await self.broadcast({
            "type": "hardware_update",
            "data": data
        }, topic="hardware")

    async def broadcast_system_metrics(self, metrics: Dict[str, Any]) -> int:
        """
        Broadcast system metrics update.
        시스템 메트릭 업데이트 브로드캐스트.

        [한국어 설명]
        CPU, 메모리, 디스크 등의 시스템 정보를
        "system" 토픽 구독자에게 전송합니다.
        """
        return await self.broadcast({
            "type": "system_update",
            "data": metrics
        }, topic="system")

    async def broadcast_log(self, log_entry: Dict[str, Any]) -> int:
        """
        Broadcast log entry.
        로그 엔트리 브로드캐스트.

        [한국어 설명]
        새 시스템 로그를 "logs" 토픽 구독자에게 전송합니다.
        실시간 로그 모니터링에 사용됩니다.
        """
        return await self.broadcast({
            "type": "log_update",
            "data": log_entry
        }, topic="logs")

    # ==================== 메시지 처리 메서드 ====================
    async def handle_client_message(self, client_id: str, message: str) -> None:
        """
        Handle incoming message from a client.
        클라이언트로부터 온 메시지 처리.

        [한국어 설명]
        클라이언트가 보낸 메시지를 파싱하고 적절한 동작을 수행합니다.
        구독 관리, ping/pong 등의 제어 메시지를 처리합니다.

        Args:
            client_id: 메시지를 보낸 클라이언트 ID
            message: 수신한 메시지 (JSON 문자열)

        [지원하는 메시지 타입]
        - subscribe: 토픽 구독
          {"type": "subscribe", "topics": ["hardware", "system"]}

        - unsubscribe: 토픽 구독 해제
          {"type": "unsubscribe", "topics": ["logs"]}

        - ping: 하트비트 응답 요청
          {"type": "ping"}
        """
        if client_id not in self._clients:
            return

        client = self._clients[client_id]

        try:
            # [JSON 파싱]
            data = json.loads(message)
            msg_type = data.get("type", "")

            # ==================== 구독 처리 ====================
            if msg_type == "subscribe":
                # 구독할 토픽 목록
                topics = data.get("topics", [])
                for topic in topics:
                    # 유효한 토픽만 추가
                    if topic in self._topics:
                        # [set.add()]
                        # 집합에 요소 추가 (중복 자동 무시)
                        client.subscriptions.add(topic)

                # 구독 확인 응답
                await self.send_to_client(client_id, {
                    "type": "subscribed",
                    "topics": list(client.subscriptions)
                })

            # ==================== 구독 해제 처리 ====================
            elif msg_type == "unsubscribe":
                topics = data.get("topics", [])
                for topic in topics:
                    # [set.discard()]
                    # 집합에서 요소 제거 (없어도 에러 없음)
                    # remove()는 없으면 KeyError 발생
                    client.subscriptions.discard(topic)

                await self.send_to_client(client_id, {
                    "type": "unsubscribed",
                    "topics": list(client.subscriptions)
                })

            # ==================== Ping/Pong 처리 ====================
            elif msg_type == "ping":
                # 마지막 하트비트 시간 업데이트
                client.last_heartbeat = datetime.now()

                # pong 응답 전송
                await self.send_to_client(client_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

            else:
                # 알 수 없는 메시지 타입
                logger.debug(f"Unknown message type from {client_id}: {msg_type}")

        except json.JSONDecodeError:
            # JSON 파싱 실패 (잘못된 형식의 메시지)
            logger.warning(f"Invalid JSON from client {client_id}")

        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")

    # ==================== 하트비트 루프 ====================
    async def _heartbeat_loop(self) -> None:
        """
        Background loop for sending heartbeat pings.
        하트비트 ping 전송 백그라운드 루프.

        [한국어 설명]
        주기적으로 모든 클라이언트에게 ping을 보내고
        응답하지 않는 클라이언트는 연결을 해제합니다.

        [하트비트 동작]
        1. 모든 클라이언트에게 ping 전송
        2. 클라이언트는 pong 응답 (last_heartbeat 업데이트)
        3. 2 * interval 동안 응답 없으면 연결 해제
        """
        while self._running:
            try:
                now = datetime.now()

                for client_id, client in list(self._clients.items()):
                    # [응답 시간 계산]
                    # 마지막 하트비트 이후 경과 시간
                    time_since_heartbeat = (now - client.last_heartbeat).total_seconds()

                    # [타임아웃 체크]
                    # 하트비트 간격의 2배 동안 응답 없으면 연결 해제
                    if time_since_heartbeat > self._heartbeat_interval * 2:
                        logger.warning(f"Client {client_id} timed out")
                        await self.disconnect(client_id)
                    else:
                        # 정상 클라이언트에게 ping 전송
                        await self.send_to_client(client_id, {
                            "type": "ping",
                            "timestamp": now.isoformat()
                        })

            except asyncio.CancelledError:
                # 태스크 취소 시 루프 종료
                break

            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")

            # [하트비트 간격만큼 대기]
            await asyncio.sleep(self._heartbeat_interval)

    # ==================== 상태 조회 메서드 ====================
    def get_status(self) -> Dict[str, Any]:
        """
        Get WebSocket manager status.
        WebSocket 매니저 상태 조회.

        [한국어 설명]
        WebSocket 서비스의 현재 상태 정보를 반환합니다.
        관리 API에서 상태를 모니터링할 때 사용합니다.

        Returns:
            상태 정보 딕셔너리
        """
        return {
            # 실행 상태
            "running": self._running,
            # 현재 연결된 클라이언트 수
            "client_count": len(self._clients),
            # 최대 허용 연결 수
            "max_connections": self._max_connections,
            # 연결된 클라이언트 목록
            "clients": self.clients,
            # 사용 가능한 토픽
            "topics": list(self._topics.keys())
        }


# ==================== 전역 인스턴스 ====================
# [싱글톤 패턴]
# 모듈 레벨에서 인스턴스 생성
# 애플리케이션 전체에서 동일한 매니저 사용
ws_manager = WebSocketManager()
