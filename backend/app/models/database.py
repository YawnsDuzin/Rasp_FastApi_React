"""
Database Configuration (데이터베이스 설정)
======================

[한국어 설명]
SQLite 데이터베이스 설정 및 비동기 지원 모듈입니다.
WAL (Write-Ahead Logging) 모드를 사용하여 SD 카드 수명을 보호합니다.

[핵심 개념]
1. SQLAlchemy: Python의 대표적인 ORM(Object-Relational Mapping) 라이브러리
   - ORM: 데이터베이스 테이블을 Python 클래스로 매핑하는 기술
   - SQL 쿼리를 직접 작성하지 않고 Python 객체로 DB 조작 가능

2. 비동기 SQLAlchemy (Async SQLAlchemy):
   - SQLAlchemy 1.4+부터 지원하는 비동기 DB 접근
   - FastAPI와 함께 사용하면 높은 동시성 처리 가능
   - 블로킹 없이 여러 DB 요청을 동시에 처리

3. WAL (Write-Ahead Logging) 모드:
   - SQLite의 저널링 모드 중 하나
   - 쓰기 작업을 별도의 WAL 파일에 먼저 기록
   - 장점: 읽기/쓰기 동시성 향상, 안전한 트랜잭션
   - Raspberry Pi SD 카드 수명 보호에 효과적
"""

import asyncio  # 비동기 프로그래밍 지원 (Python 표준 라이브러리)
from pathlib import Path  # 파일 경로 처리를 위한 클래스 (OS 독립적)
from typing import AsyncGenerator  # 비동기 제너레이터 타입 힌트

# [SQLAlchemy 비동기 모듈들]
# create_async_engine: 비동기 DB 엔진 생성 함수
# AsyncSession: 비동기 DB 세션 클래스 (DB 연결을 감싸는 객체)
# async_sessionmaker: 비동기 세션 팩토리 생성 함수
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# declarative_base: ORM 모델의 기반 클래스를 생성하는 함수
# 모든 DB 모델 클래스가 이 Base를 상속받음
from sqlalchemy.orm import declarative_base

# event: SQLAlchemy 이벤트 리스너 등록 모듈
from sqlalchemy import event

# 프로젝트 설정 불러오기
from app.core.config import settings
from app.core.logging_config import get_logger

# 이 모듈용 로거 생성 (__name__ = "app.models.database")
logger = get_logger(__name__)

# ==================== 데이터 디렉토리 생성 ====================
# [파일 시스템 설정]

# Path("data"): 현재 작업 디렉토리 기준 "data" 폴더 경로
data_dir = Path("data")

# mkdir(): 디렉토리 생성
# - parents=True: 부모 디렉토리가 없으면 함께 생성 (mkdir -p와 유사)
# - exist_ok=True: 이미 존재해도 에러 발생하지 않음
data_dir.mkdir(parents=True, exist_ok=True)


# ==================== 비동기 엔진 생성 ====================
# [SQLAlchemy 비동기 엔진]

# create_async_engine(): 비동기 DB 연결 엔진 생성
# 엔진(Engine)은 DB 연결 풀(pool)을 관리하는 객체
engine = create_async_engine(
    # settings.DATABASE_URL: "sqlite+aiosqlite:///data/hmi_data.db" 형태
    # sqlite+aiosqlite: 비동기 SQLite 드라이버 (aiosqlite 라이브러리 사용)
    settings.DATABASE_URL,

    # echo: True면 실행되는 SQL 쿼리를 콘솔에 출력 (디버깅용)
    echo=settings.DEBUG,

    # future=True: SQLAlchemy 2.0 스타일 API 사용
    # 1.x와 2.0 버전의 API 차이가 있어, 최신 스타일을 명시적으로 활성화
    future=True,

    # connect_args: DB 드라이버에 전달할 추가 인자
    # check_same_thread=False: SQLite 멀티스레드 접근 허용
    # SQLite는 기본적으로 단일 스레드용이지만, 이 옵션으로 해제
    connect_args={"check_same_thread": False}
)


# ==================== 세션 팩토리 생성 ====================
# [세션 팩토리 설정]

# async_sessionmaker(): 비동기 세션을 생성하는 팩토리 함수 생성
# 세션(Session): DB와의 대화 단위, 트랜잭션을 관리
async_session = async_sessionmaker(
    # 사용할 엔진 지정
    engine,

    # class_=AsyncSession: 생성할 세션의 클래스 타입
    class_=AsyncSession,

    # expire_on_commit=False: 커밋 후에도 객체 속성이 만료되지 않음
    # True(기본값)면 커밋 후 객체 속성에 접근할 때 새 쿼리가 필요
    # False면 커밋 후에도 메모리의 값을 그대로 사용 (성능 향상)
    expire_on_commit=False
)


# ==================== 모델 기반 클래스 ====================
# [ORM Base 클래스]

# declarative_base(): 모든 ORM 모델의 부모 클래스 생성
# 이 Base를 상속받은 클래스들이 DB 테이블과 매핑됨
# 예: class User(Base): -> users 테이블
Base = declarative_base()


# ==================== WAL 모드 활성화 함수 ====================
def enable_wal_mode(dbapi_connection, connection_record):
    """
    Enable WAL mode for SQLite.
    SQLite WAL(Write-Ahead Logging) 모드 활성화.

    [한국어 설명]
    SQLite의 성능과 안정성을 높이는 PRAGMA 설정들을 적용합니다.

    [매개변수]
    - dbapi_connection: 저수준 DB API 연결 객체 (sqlite3.Connection)
    - connection_record: SQLAlchemy 연결 풀 기록 객체

    [PRAGMA 설명]
    SQLite에서 PRAGMA는 데이터베이스 설정을 조정하는 명령어입니다.
    런타임에 DB 동작 방식을 변경할 수 있습니다.
    """

    # cursor(): SQL 명령을 실행하기 위한 커서 객체 생성
    cursor = dbapi_connection.cursor()

    # [PRAGMA journal_mode=WAL]
    # 저널 모드를 WAL(Write-Ahead Logging)으로 설정
    # - DELETE(기본값): 트랜잭션마다 롤백 저널 생성/삭제
    # - WAL: 변경사항을 별도 WAL 파일에 기록
    # WAL 장점:
    #   1. 읽기와 쓰기가 서로를 블로킹하지 않음
    #   2. 쓰기 중에도 읽기 가능
    #   3. 체크포인트로 데이터를 메인 DB에 병합
    cursor.execute("PRAGMA journal_mode=WAL")

    # [PRAGMA synchronous=NORMAL]
    # 디스크 동기화 수준 설정 (안전성 vs 성능)
    # - FULL(기본값): 모든 쓰기 작업에서 fsync() 호출 (가장 안전)
    # - NORMAL: WAL 모드에서 적절한 안전성 제공 (빠름)
    # - OFF: fsync() 호출 안함 (가장 빠르지만 위험)
    cursor.execute("PRAGMA synchronous=NORMAL")

    # [PRAGMA cache_size=10000]
    # 메모리 캐시 페이지 수 설정 (기본값: 2000)
    # 각 페이지는 4KB (기본값), 10000페이지 = 약 40MB
    # 캐시가 크면 디스크 I/O가 줄어들어 성능 향상
    cursor.execute("PRAGMA cache_size=10000")

    # [PRAGMA temp_store=MEMORY]
    # 임시 테이블 저장 위치 설정
    # - FILE(기본값): 디스크에 임시 파일 생성
    # - MEMORY: 메모리에만 저장 (빠르지만 메모리 사용 증가)
    # 정렬, GROUP BY 등의 임시 데이터를 메모리에 저장
    cursor.execute("PRAGMA temp_store=MEMORY")

    # 커서 닫기 (리소스 해제)
    cursor.close()


# ==================== 데이터베이스 초기화 ====================
async def init_db() -> None:
    """
    Initialize the database and create tables.
    데이터베이스 초기화 및 테이블 생성.

    [한국어 설명]
    애플리케이션 시작 시 호출되어:
    1. WAL 모드 이벤트 리스너를 등록하고
    2. 모든 ORM 모델에 해당하는 테이블을 생성합니다.

    [호출 시점]
    FastAPI의 lifespan 이벤트(startup)에서 호출됨
    """
    logger.info("Initializing database...")

    # [WAL 모드 이벤트 등록]
    # settings.DATABASE_WAL_MODE가 True일 때만 WAL 설정 적용
    if settings.DATABASE_WAL_MODE:
        # 이 import들은 위에서 이미 했지만, 조건부 실행을 위해 여기서 다시 import
        from sqlalchemy import event
        from sqlalchemy.engine import Engine

        # [이벤트 리스너 데코레이터]
        # @event.listens_for(Engine, "connect"):
        # 모든 Engine 객체에서 "connect" 이벤트 발생 시 실행할 함수 등록
        # "connect" 이벤트: 새 DB 연결이 생성될 때마다 발생
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            # 연결될 때마다 WAL 모드 설정 적용
            enable_wal_mode(dbapi_connection, connection_record)

    # [테이블 생성]
    # engine.begin(): 트랜잭션을 시작하고 연결을 반환
    # async with: 비동기 컨텍스트 매니저, 자동으로 커밋/롤백 처리
    async with engine.begin() as conn:
        # [모델 Import]
        # 여기서 모델들을 import해야 Base.metadata에 등록됨
        # SQLAlchemy는 import된 모델들의 메타데이터를 자동 수집
        from . import sensor_data, system_log, device_state

        # [run_sync(): 동기 함수를 비동기로 실행]
        # Base.metadata.create_all(): 모든 모델의 테이블을 생성하는 동기 함수
        # 비동기 환경에서 동기 함수 호출 시 run_sync() 사용
        # 이미 존재하는 테이블은 건너뜀 (CREATE TABLE IF NOT EXISTS)
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized successfully")


# ==================== 세션 의존성 주입 ====================
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session for dependency injection.
    의존성 주입을 위한 데이터베이스 세션 제공.

    [한국어 설명]
    FastAPI의 Depends()와 함께 사용하는 의존성 주입 함수입니다.
    각 API 요청에 대해 새 DB 세션을 생성하고, 요청 완료 시 정리합니다.

    [AsyncGenerator 설명]
    - AsyncGenerator[YieldType, SendType]: 비동기 제너레이터 타입 힌트
    - YieldType: yield하는 값의 타입 (AsyncSession)
    - SendType: send()로 받는 값의 타입 (None = 받지 않음)

    [사용 예시]
    @app.get("/items")
    async def get_items(session: AsyncSession = Depends(get_session)):
        result = await session.execute(select(Item))
        return result.scalars().all()

    [트랜잭션 흐름]
    1. async with로 세션 생성
    2. yield로 세션을 호출자에게 전달 (API 핸들러 실행)
    3. API 핸들러가 완료되면 yield 이후 코드 실행
    4. 성공 시 commit(), 실패 시 rollback()
    5. finally에서 세션 닫기
    """

    # async_session(): 세션 팩토리를 호출하여 새 세션 생성
    # async with: 세션을 컨텍스트 매니저로 사용
    async with async_session() as session:
        try:
            # [yield]
            # yield를 만나면 함수 실행이 일시 중단되고,
            # session 객체가 호출자(API 핸들러)에게 전달됨
            # 호출자가 작업을 마치면 yield 이후 코드가 실행됨
            yield session

            # [commit(): 트랜잭션 커밋]
            # API 핸들러가 정상적으로 완료되면 변경사항을 DB에 저장
            await session.commit()

        except Exception:
            # [rollback(): 트랜잭션 롤백]
            # 예외 발생 시 모든 변경사항을 취소
            await session.rollback()
            # 예외를 다시 발생시켜 상위 핸들러에서 처리하도록 함
            raise

        finally:
            # [close(): 세션 닫기]
            # 성공/실패와 관계없이 항상 세션을 닫아 리소스 해제
            await session.close()


# ==================== 오래된 데이터 정리 ====================
async def cleanup_old_data(retention_days: int = None) -> int:
    """
    Clean up data older than retention period.
    보관 기간이 지난 오래된 데이터 정리.

    [한국어 설명]
    SD 카드 용량 관리를 위해 오래된 센서 데이터와 로그를 삭제합니다.
    Raspberry Pi의 제한된 저장 공간을 효율적으로 사용하기 위함입니다.

    Args:
        retention_days: 보관할 일수 (기본값: settings에서 가져옴)

    Returns:
        삭제된 레코드 수

    [사용 예시]
    # 7일 이전 데이터 삭제
    deleted = await cleanup_old_data(retention_days=7)
    print(f"{deleted}개 레코드 삭제됨")
    """

    # datetime: 날짜/시간 처리 표준 라이브러리
    from datetime import datetime, timedelta
    # delete: SQLAlchemy DELETE 쿼리 생성 함수
    from sqlalchemy import delete
    # 삭제할 테이블의 모델 클래스들
    from .sensor_data import SensorData
    from .system_log import SystemLog

    # [보관 기간 설정]
    # 인자로 전달된 값이 없으면(None) 설정에서 가져옴
    # or 연산자: 왼쪽이 falsy(None, 0, False 등)면 오른쪽 값 사용
    retention_days = retention_days or settings.DATA_RETENTION_DAYS

    # [기준 날짜 계산]
    # datetime.now(): 현재 시간
    # timedelta(days=n): n일의 시간 차이를 나타내는 객체
    # 현재 시간에서 보관 기간을 빼면 삭제 기준 날짜가 됨
    cutoff_date = datetime.now() - timedelta(days=retention_days)

    # 삭제된 레코드 수 카운터
    deleted_count = 0

    # [비동기 세션 사용]
    async with async_session() as session:
        # [센서 데이터 삭제]
        # delete(SensorData): SensorData 테이블에서 DELETE 쿼리 시작
        # .where(...): WHERE 조건절 추가
        # SensorData.timestamp < cutoff_date: 기준일 이전 데이터만 대상
        result = await session.execute(
            delete(SensorData).where(SensorData.timestamp < cutoff_date)
        )
        # result.rowcount: 영향받은 (삭제된) 행 수
        deleted_count += result.rowcount

        # [시스템 로그 삭제]
        result = await session.execute(
            delete(SystemLog).where(SystemLog.timestamp < cutoff_date)
        )
        deleted_count += result.rowcount

        # [변경사항 커밋]
        # DELETE는 데이터 변경이므로 반드시 커밋 필요
        await session.commit()

    # 삭제 결과 로깅
    logger.info(f"Cleaned up {deleted_count} old records (older than {retention_days} days)")

    return deleted_count
