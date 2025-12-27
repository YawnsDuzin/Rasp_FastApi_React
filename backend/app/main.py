"""
Raspberry Pi HMI - FastAPI Application (라즈베리 파이 HMI 시스템 메인 파일)
=====================================================================

[한국어 설명]
이 파일은 FastAPI 백엔드 애플리케이션의 메인 진입점(Entry Point)입니다.
FastAPI는 Python으로 작성된 현대적인 고성능 웹 프레임워크로,
자동 API 문서화, 타입 힌팅, 비동기(async) 지원 등의 특징이 있습니다.

이 HMI(Human-Machine Interface) 시스템의 주요 기능:
- 실시간 하드웨어 모니터링 및 제어 (GPIO, PWM, I2C, SPI)
- WebSocket을 통한 실시간 데이터 푸시
- 시스템 리소스 모니터링 (CPU, 메모리, 디스크)
- SQLite 데이터베이스를 사용한 데이터 로깅

실행 방법:
    uvicorn app.main:app --host 0.0.0.0 --port 8000

[English Description]
This file is the main entry point for the FastAPI backend application.
FastAPI is a modern, high-performance web framework for Python, featuring
automatic API documentation, type hints, and async support.
"""

# ============================================================================
# 필수 라이브러리 임포트 (Import Required Libraries)
# ============================================================================

# asyncio: Python의 비동기 프로그래밍 라이브러리
# 비동기(async/await)를 사용하면 여러 작업을 동시에 처리할 수 있어 성능이 향상됨
import asyncio

# contextlib.asynccontextmanager: 비동기 컨텍스트 매니저를 만들기 위한 데코레이터
# FastAPI의 lifespan 이벤트 핸들링에 사용됨
from contextlib import asynccontextmanager

# pathlib.Path: 파일 시스템 경로를 다루는 객체지향적 방법
# 문자열 대신 Path 객체를 사용하면 운영체제 독립적인 경로 처리가 가능
from pathlib import Path

# FastAPI 핵심 클래스들 임포트
# FastAPI: 메인 애플리케이션 클래스 - 앱의 모든 설정과 라우트를 관리
# Request: HTTP 요청 객체 - 클라이언트가 보낸 요청 정보를 담고 있음
from fastapi import FastAPI, Request

# CORS(Cross-Origin Resource Sharing) 미들웨어
# 브라우저의 보안 정책 때문에 다른 도메인에서 API를 호출하려면 CORS 설정이 필요
# 예: React 개발 서버(localhost:3000)에서 FastAPI(localhost:8000)로 요청할 때
from fastapi.middleware.cors import CORSMiddleware

# StaticFiles: 정적 파일(HTML, CSS, JS, 이미지 등)을 서빙하기 위한 클래스
from fastapi.staticfiles import StaticFiles

# FileResponse: 파일을 HTTP 응답으로 반환할 때 사용
# JSONResponse: JSON 형태로 HTTP 응답을 반환할 때 사용
from fastapi.responses import FileResponse, JSONResponse

# 프로젝트 내부 모듈 임포트
# settings: 환경 설정값들을 담고 있는 객체 (포트, DB URL, GPIO 핀 번호 등)
from app.core.config import settings

# setup_logging: 로깅 시스템 초기화, get_logger: 로거 인스턴스 가져오기
from app.core.logging_config import setup_logging, get_logger

# init_db: 데이터베이스 초기화 함수 (테이블 생성 등)
from app.models.database import init_db

# hardware_manager: 모든 하드웨어(GPIO, I2C, SPI 등)를 통합 관리하는 매니저
from app.hardware.manager import hardware_manager

# system_monitor: CPU, 메모리, 디스크 등 시스템 리소스 모니터링 서비스
from app.services.system_monitor import system_monitor

# data_logger: 센서 데이터를 DB에 주기적으로 저장하는 서비스
from app.services.data_logger import data_logger

# ws_manager: WebSocket 연결들을 관리하고 데이터를 브로드캐스트하는 매니저
from app.services.websocket_manager import ws_manager

# api_router: 모든 API 엔드포인트를 하나로 묶은 라우터
from app.api import api_router

# ============================================================================
# 로깅 설정 (Logging Setup)
# ============================================================================

# 로깅 시스템 초기화 - 로그 파일 생성, 포맷 설정 등
setup_logging()

# 이 모듈용 로거 인스턴스 생성
# __name__은 현재 모듈 이름('app.main')으로, 로그 출력 시 어디서 발생했는지 알 수 있음
logger = get_logger(__name__)


# ============================================================================
# 애플리케이션 수명주기 관리 (Application Lifespan Management)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 수명주기 관리자 (Application Lifespan Manager)

    [한국어 설명]
    FastAPI 앱이 시작될 때와 종료될 때 실행되어야 하는 코드를 정의합니다.

    @asynccontextmanager 데코레이터:
    - 이 데코레이터는 비동기 컨텍스트 매니저를 쉽게 만들 수 있게 해줍니다.
    - 'yield' 키워드 전: 앱 시작 시 실행되는 코드 (Startup)
    - 'yield' 키워드 후: 앱 종료 시 실행되는 코드 (Shutdown)

    async/await 키워드:
    - async def: 이 함수가 비동기 함수임을 선언 (코루틴)
    - await: 비동기 작업이 완료될 때까지 기다림

    [English Description]
    Defines code that should run when the FastAPI app starts and shuts down.
    The @asynccontextmanager decorator creates an async context manager.
    Code before 'yield' runs on startup, code after 'yield' runs on shutdown.
    """

    # ==================== 시작 단계 (Startup Phase) ====================

    # 앱 시작 정보 로그 출력
    # f-string: Python의 포맷 문자열, 변수값을 {} 안에 넣어서 문자열 생성
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # 시뮬레이션 모드 여부 로그 출력
    # 시뮬레이션 모드: 실제 라즈베리 파이 하드웨어 없이 개발/테스트할 때 사용
    logger.info(f"Simulation mode: {settings.SIMULATION_MODE}")

    # 데이터베이스 초기화 - 테이블이 없으면 생성
    # await: init_db()가 완료될 때까지 기다림 (비동기 함수이므로)
    await init_db()

    # 하드웨어 매니저 초기화
    # GPIO, I2C, SPI 등 모든 하드웨어 컨트롤러들을 초기화
    await hardware_manager.initialize()

    # 각종 백그라운드 서비스 시작
    await system_monitor.start()  # 시스템 모니터링 시작 (CPU, 메모리 등)
    await data_logger.start()     # 데이터 로깅 서비스 시작
    await ws_manager.start()      # WebSocket 매니저 시작

    # 하드웨어 데이터 업데이트 콜백 함수 등록
    # 콜백(Callback): 특정 이벤트가 발생했을 때 자동으로 호출되는 함수
    async def on_hardware_update(data):
        """
        하드웨어 데이터 업데이트 콜백 (Hardware Data Update Callback)

        [한국어 설명]
        하드웨어 데이터가 갱신될 때마다 호출되는 함수입니다.
        WebSocket을 통해 연결된 모든 클라이언트에게 새로운 데이터를 전송합니다.

        매개변수:
            data: 하드웨어 상태 데이터 객체 (GPIO 상태, 센서 값 등)
        """
        # WebSocket 클라이언트들에게 데이터 브로드캐스트 (전체 전송)
        # to_dict(): 객체를 딕셔너리로 변환 (JSON 직렬화를 위해)
        await ws_manager.broadcast_hardware_data(data.to_dict())

        # 참고: 실제 DB 로깅은 아래 periodic_data_log에서 주기적으로 수행됨
        # 매번 업데이트마다 DB에 쓰면 I/O 부하가 높아져서 주기적으로 저장

    # 하드웨어 매니저에 콜백 함수 등록
    hardware_manager.register_callback(on_hardware_update)

    # 하드웨어 상태 업데이트 루프 시작
    # 주기적으로 센서값을 읽고 콜백을 호출하는 무한 루프
    await hardware_manager.start_update_loop()

    # ==================== 주기적 작업 태스크 생성 (Periodic Tasks) ====================

    async def periodic_data_log():
        """
        주기적 데이터 로깅 태스크 (Periodic Data Logging Task)

        [한국어 설명]
        설정된 간격(DATA_LOG_INTERVAL)마다 하드웨어 데이터를 DB에 저장합니다.
        무한 루프(while True)로 계속 실행되며, 앱 종료 시 취소(cancel)됩니다.
        """
        while True:
            # 설정된 간격만큼 대기 (기본값: 5초)
            # asyncio.sleep은 비동기 sleep으로, 대기 중에도 다른 작업 가능
            await asyncio.sleep(settings.DATA_LOG_INTERVAL)

            # 현재 하드웨어 데이터가 있으면 DB에 저장
            if hardware_manager.current_data:
                await data_logger.log_hardware_data(hardware_manager.current_data)

    # 비동기 태스크 생성 및 백그라운드 실행
    # asyncio.create_task(): 코루틴을 태스크로 변환하여 동시 실행
    log_task = asyncio.create_task(periodic_data_log())

    async def periodic_system_broadcast():
        """
        주기적 시스템 메트릭 브로드캐스트 태스크 (Periodic System Metrics Broadcast Task)

        [한국어 설명]
        1초마다 시스템 정보(CPU, 메모리, 디스크 등)를 WebSocket 클라이언트에게 전송합니다.
        """
        while True:
            # 1초 대기
            await asyncio.sleep(1.0)

            # 현재 시스템 메트릭이 있으면 브로드캐스트
            if system_monitor.current:
                await ws_manager.broadcast_system_metrics(
                    system_monitor.current.to_dict()
                )

    # 시스템 브로드캐스트 태스크 생성
    system_task = asyncio.create_task(periodic_system_broadcast())

    logger.info("Application started successfully")

    # yield 키워드: 여기서 앱이 실행 중인 상태
    # yield 이전: 시작(startup) 코드
    # yield 이후: 종료(shutdown) 코드
    yield

    # ==================== 종료 단계 (Shutdown Phase) ====================

    logger.info("Shutting down application...")

    # 백그라운드 태스크 취소
    # cancel(): 태스크에 CancelledError를 발생시켜 중단
    log_task.cancel()
    system_task.cancel()

    # 태스크 취소 완료 대기
    try:
        await log_task
        await system_task
    except asyncio.CancelledError:
        # CancelledError는 정상적인 취소 과정이므로 무시
        pass

    # 각종 서비스 정리(cleanup) 및 종료
    await ws_manager.stop()              # WebSocket 연결 종료
    await data_logger.stop()             # 데이터 로거 종료
    await system_monitor.stop()          # 시스템 모니터 종료
    await hardware_manager.stop_update_loop()  # 하드웨어 업데이트 루프 종료
    await hardware_manager.cleanup()     # 하드웨어 리소스 정리 (GPIO 해제 등)

    logger.info("Application shutdown complete")


# ============================================================================
# FastAPI 애플리케이션 인스턴스 생성 (Create FastAPI Application Instance)
# ============================================================================

# FastAPI 클래스의 인스턴스를 생성
# 이 'app' 변수가 uvicorn 서버가 실행할 애플리케이션 객체
app = FastAPI(
    # title: API 문서에 표시될 제목
    title=settings.APP_NAME,

    # version: API 버전 정보
    version=settings.APP_VERSION,

    # description: API 문서에 표시될 설명 (Markdown 형식 지원)
    # 삼중 따옴표("""): 여러 줄 문자열을 정의할 때 사용
    description="""
    ## Raspberry Pi HMI System (라즈베리 파이 HMI 시스템)

    A real-time Human-Machine Interface for Raspberry Pi.
    (라즈베리 파이를 위한 실시간 사람-기계 인터페이스)

    ### Features (기능):
    - **Hardware Control (하드웨어 제어)**: GPIO, PWM, I2C, SPI, 센서, 디스플레이
    - **Real-time Updates (실시간 업데이트)**: WebSocket 기반 데이터 푸시
    - **System Monitoring (시스템 모니터링)**: CPU, 메모리, 디스크, 온도
    - **Data Logging (데이터 로깅)**: WAL 모드 SQLite
    - **Simulation Mode (시뮬레이션 모드)**: 하드웨어 없이 개발 가능

    ### WebSocket:
    실시간 업데이트를 위해 `/api/ws/live`에 연결하세요.
    Connect to `/api/ws/live` for real-time updates.
    """,

    # lifespan: 위에서 정의한 수명주기 관리자 연결
    lifespan=lifespan,

    # Swagger UI 문서 경로 (기본값: /docs)
    docs_url="/api/docs",

    # ReDoc 문서 경로 (기본값: /redoc)
    redoc_url="/api/redoc",

    # OpenAPI JSON 스키마 경로
    openapi_url="/api/openapi.json"
)


# ============================================================================
# CORS 미들웨어 설정 (CORS Middleware Configuration)
# ============================================================================

# CORS (Cross-Origin Resource Sharing) 미들웨어 추가
# [한국어 설명]
# 웹 브라우저는 보안상 이유로 다른 도메인(origin)으로의 요청을 기본적으로 차단합니다.
# 예: React 개발 서버(http://localhost:3000)에서
#     FastAPI 서버(http://localhost:8000)로 요청하면 CORS 에러 발생
# 이 미들웨어를 추가하면 지정된 도메인에서의 요청을 허용합니다.
app.add_middleware(
    CORSMiddleware,

    # allow_origins: 허용할 출처(origin) 목록
    # settings.CORS_ORIGINS에 정의된 도메인들만 API 접근 가능
    allow_origins=settings.CORS_ORIGINS,

    # allow_credentials: 쿠키, Authorization 헤더 등 자격 증명 포함 허용
    allow_credentials=True,

    # allow_methods: 허용할 HTTP 메서드 ("*"는 모든 메서드 허용)
    # GET, POST, PUT, DELETE, PATCH, OPTIONS 등
    allow_methods=["*"],

    # allow_headers: 허용할 HTTP 헤더 ("*"는 모든 헤더 허용)
    allow_headers=["*"],
)


# ============================================================================
# 전역 예외 처리기 (Global Exception Handler)
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    전역 예외 처리기 (Global Exception Handler)

    [한국어 설명]
    @app.exception_handler 데코레이터:
    - 지정된 예외 타입(여기서는 모든 Exception)이 발생했을 때 이 함수가 호출됨
    - 처리되지 않은 예외를 잡아서 사용자에게 적절한 에러 응답을 반환

    매개변수:
        request (Request): 예외가 발생한 HTTP 요청 객체
        exc (Exception): 발생한 예외 객체

    반환값:
        JSONResponse: JSON 형태의 에러 응답 (HTTP 500 상태 코드)

    [English Description]
    Catches any unhandled exceptions and returns a proper JSON error response.
    This prevents the server from crashing and provides useful error info.
    """
    # 예외 정보를 로그에 기록 (스택 트레이스 포함)
    logger.exception(f"Unhandled exception: {exc}")

    # 클라이언트에게 JSON 에러 응답 반환
    return JSONResponse(
        status_code=500,  # 500 Internal Server Error
        content={
            "error": "Internal server error",
            "detail": str(exc)  # 예외 메시지 (개발 중에만 표시 권장)
        }
    )


# ============================================================================
# API 라우터 등록 (Register API Router)
# ============================================================================

# API 라우터 포함
# include_router(): 별도 파일에 정의된 라우트들을 메인 앱에 추가
# prefix="/api": 모든 라우트 경로 앞에 /api가 붙음
# 예: hardware 라우터의 /gpio 경로는 /api/gpio가 됨
app.include_router(api_router, prefix="/api")


# ============================================================================
# 정적 파일 서빙 설정 (Static Files Serving)
# ============================================================================

# static 디렉토리 경로 계산
# Path(__file__): 현재 파일(main.py)의 경로
# .parent: 상위 디렉토리 (/app)
# .parent: 한 번 더 상위 (/backend)
# / "static": static 폴더 경로
static_dir = Path(__file__).parent.parent / "static"

# static 디렉토리가 존재하면 정적 파일 서빙 설정
if static_dir.exists():
    # StaticFiles: 정적 파일(HTML, CSS, JS, 이미지 등)을 서빙
    # /static 경로로 접근하면 static_dir의 파일을 반환
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ============================================================================
# React SPA(Single Page Application) 라우팅 (React SPA Routing)
# ============================================================================

@app.get("/")
async def serve_react_app():
    """
    루트 경로에서 React 앱 서빙 (Serve React App at Root Path)

    [한국어 설명]
    @app.get("/") 데코레이터:
    - HTTP GET 요청이 "/" 경로로 오면 이 함수가 실행됨

    React 앱이 빌드되어 static 폴더에 있으면 index.html을 반환하고,
    없으면 API 정보를 JSON으로 반환합니다.

    [English Description]
    Serves the React application's index.html if it exists,
    otherwise returns API information as JSON.
    """
    index_file = static_dir / "index.html"

    if index_file.exists():
        # React 빌드 파일이 있으면 index.html 반환
        return FileResponse(str(index_file))

    # React 빌드가 없으면 API 정보 반환
    return {"message": "Welcome to Raspberry Pi HMI API", "docs": "/api/docs"}


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """
    SPA 클라이언트 사이드 라우팅 지원 (Support SPA Client-Side Routing)

    [한국어 설명]
    경로 매개변수 {full_path:path}:
    - :path 타입은 슬래시(/)를 포함한 모든 경로를 캡처
    - 예: /dashboard, /settings/gpio, /hardware/sensors 등

    SPA(Single Page Application) 작동 방식:
    1. React 앱은 클라이언트에서 라우팅을 처리 (React Router)
    2. 사용자가 /dashboard 같은 경로를 직접 입력하거나 새로고침하면
       서버에 해당 경로로 요청이 옴
    3. 서버는 해당 경로의 정적 파일이 있으면 반환하고,
       없으면 index.html을 반환하여 React Router가 처리하도록 함

    [English Description]
    Handles client-side routing for Single Page Applications.
    Returns actual files if they exist, otherwise returns index.html
    so the React Router can handle the route.
    """
    # 요청된 경로에 실제 파일이 있는지 확인
    file_path = static_dir / full_path

    if file_path.exists() and file_path.is_file():
        # 파일이 존재하면 해당 파일 반환 (CSS, JS, 이미지 등)
        return FileResponse(str(file_path))

    # 파일이 없으면 index.html 반환 (SPA 라우팅)
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))

    # React 빌드가 없으면 API 안내 메시지 반환
    return {"message": "API endpoint not found", "docs": "/api/docs"}


# ============================================================================
# 헬스 체크 엔드포인트 (Health Check Endpoint)
# ============================================================================

@app.get("/health")
async def health_check():
    """
    헬스 체크 엔드포인트 (Health Check Endpoint)

    [한국어 설명]
    로드 밸런서나 모니터링 시스템이 서버 상태를 확인할 때 사용합니다.

    헬스 체크의 용도:
    1. 로드 밸런서: 정상적인 서버로만 트래픽을 보내기 위해 사용
    2. 쿠버네티스(K8s): Pod의 상태를 확인하고 재시작 여부 결정
    3. 모니터링: 서비스 가용성 모니터링 및 알림

    반환값:
        dict: 서버 상태 정보 (이름, 버전, 시뮬레이션 모드 여부)

    [English Description]
    Used by load balancers and monitoring systems to check server health.
    Returns basic info about the application status.
    """
    return {
        "status": "healthy",              # 서버 상태
        "app": settings.APP_NAME,         # 앱 이름
        "version": settings.APP_VERSION,  # 버전
        "simulation": settings.SIMULATION_MODE  # 시뮬레이션 모드 여부
    }


# ============================================================================
# 직접 실행 시 서버 시작 (Run Server When Executed Directly)
# ============================================================================

# __name__ == "__main__" 체크:
# 이 파일이 직접 실행될 때만 아래 코드가 실행됨
# 다른 파일에서 import할 때는 실행되지 않음
if __name__ == "__main__":
    # uvicorn: ASGI 서버, FastAPI 앱을 실행하는 웹 서버
    import uvicorn

    # uvicorn.run(): 서버 시작
    # "app.main:app": app 모듈의 main 파일에 있는 app 객체를 실행
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,              # 바인딩할 호스트 (0.0.0.0 = 모든 인터페이스)
        port=settings.PORT,              # 포트 번호 (기본 8000)
        reload=settings.RELOAD,          # 코드 변경 시 자동 재시작
        log_level=settings.LOG_LEVEL.lower()  # 로그 레벨 (info, debug 등)
    )
