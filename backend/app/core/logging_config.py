"""
Logging Configuration (로깅 설정)
==================================

[한국어 설명]
HMI 애플리케이션의 구조화된 로깅 시스템을 설정합니다.
콘솔, 파일, JSON 형식의 다양한 로깅 출력을 지원합니다.

[핵심 개념]
1. Python Logging:
   - 표준 라이브러리의 로깅 모듈
   - 로거(Logger) → 핸들러(Handler) → 포매터(Formatter) 구조
   - 로그 레벨: DEBUG < INFO < WARNING < ERROR < CRITICAL

2. 로깅 아키텍처:
                    ┌──────────────┐
                    │    Logger    │  ← 로그 메시지 생성
                    │   ("hmi")    │
                    └──────┬───────┘
                           │
       ┌──────────┬────────┼────────┬──────────┐
       ▼          ▼        ▼        ▼          ▼
   ┌───────┐  ┌───────┐ ┌──────┐ ┌───────┐ ┌───────┐
   │Console│  │ File  │ │ JSON │ │ Error │ │ ...   │
   │Handler│  │Handler│ │Handler│ │Handler│ │       │
   └───────┘  └───────┘ └──────┘ └───────┘ └───────┘

3. 로그 레벨 사용 가이드:
   - DEBUG: 개발 중 디버깅 정보
   - INFO: 정상 동작 정보 (시작, 종료 등)
   - WARNING: 경고 (복구 가능한 문제)
   - ERROR: 오류 (기능 실패)
   - CRITICAL: 심각한 오류 (시스템 중단)

4. 로그 파일 종류:
   - hmi.log: 모든 로그 (텍스트 형식)
   - hmi_json.log: 구조화된 로그 (JSON 형식, 모니터링 도구 연동용)
   - hmi_error.log: 에러 로그만 (ERROR 이상)
"""

# ============================================================================
# 라이브러리 임포트 (Import Libraries)
# ============================================================================

# [logging 모듈]
# Python 표준 로깅 라이브러리
# 로거, 핸들러, 포매터 등 로깅 관련 클래스 제공
import logging

# [sys 모듈]
# 시스템 관련 유틸리티
# sys.stdout: 표준 출력 (콘솔)
import sys

# [Path 클래스]
# 파일 경로 처리 (OS 독립적)
from pathlib import Path

# [RotatingFileHandler]
# 파일 크기에 따라 자동으로 로그 파일을 교체하는 핸들러
# 예: hmi.log → hmi.log.1 → hmi.log.2 (백업)
from logging.handlers import RotatingFileHandler

# [datetime]
# 타임스탬프 생성용
from datetime import datetime

# [python-json-logger]
# JSON 형식의 구조화된 로그 출력
# pip install python-json-logger
from pythonjsonlogger import jsonlogger

# [프로젝트 설정]
from .config import settings


# ============================================================================
# 커스텀 JSON 포매터 (Custom JSON Formatter)
# ============================================================================

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter with additional fields.
    추가 필드가 포함된 커스텀 JSON 포매터.

    [한국어 설명]
    기본 JsonFormatter를 확장하여 추가적인 메타데이터 필드를 포함합니다.
    ELK Stack, Grafana Loki 등 로그 분석 도구와 연동하기 좋습니다.

    [상속]
    jsonlogger.JsonFormatter를 상속받아 add_fields 메서드를 오버라이드

    [추가 필드]
    - timestamp: ISO 형식 타임스탬프 (예: "2024-01-15T12:30:45.123456")
    - level: 로그 레벨 (예: "INFO", "ERROR")
    - logger: 로거 이름 (예: "hmi.hardware.gpio")
    - module: 모듈 이름 (예: "gpio_controller")
    - function: 함수 이름 (예: "set_led")
    - line: 소스 코드 줄 번호 (예: 42)

    [출력 예시]
    {
        "timestamp": "2024-01-15T12:30:45.123456",
        "level": "INFO",
        "logger": "hmi.hardware.gpio",
        "module": "gpio_controller",
        "function": "set_led",
        "line": 42,
        "message": "LED 0 turned on"
    }
    """

    def add_fields(self, log_record, record, message_dict):
        """
        로그 레코드에 추가 필드를 삽입합니다.
        Add additional fields to the log record.

        [매개변수]
        - log_record (dict): 최종 출력될 JSON 딕셔너리
        - record (logging.LogRecord): 원본 로그 레코드 객체
        - message_dict (dict): 메시지에서 추출된 딕셔너리 (사용자 정의 필드)

        [LogRecord 속성]
        - record.levelname: 로그 레벨 문자열 ("DEBUG", "INFO" 등)
        - record.name: 로거 이름
        - record.module: 모듈 이름 (확장자 제외)
        - record.funcName: 호출 함수 이름
        - record.lineno: 호출 위치 줄 번호

        [super() 호출]
        부모 클래스의 기본 필드 추가 로직을 먼저 실행
        """
        # [부모 클래스 메서드 호출]
        # 기본 필드들(message 등)을 먼저 추가
        super().add_fields(log_record, record, message_dict)

        # ==================== 타임스탬프 추가 ====================
        # [UTC 시간으로 통일]
        # utcnow(): 시간대 독립적인 UTC 시간
        # isoformat(): ISO 8601 형식 문자열 변환
        log_record["timestamp"] = datetime.utcnow().isoformat()

        # ==================== 로그 레벨 ====================
        # [levelname]
        # 레벨을 문자열로: DEBUG, INFO, WARNING, ERROR, CRITICAL
        log_record["level"] = record.levelname

        # ==================== 로거 이름 ====================
        # [name]
        # 계층적 로거 이름 (예: "hmi.hardware.gpio_controller")
        log_record["logger"] = record.name

        # ==================== 모듈 이름 ====================
        # [module]
        # 파일 이름에서 .py 확장자를 제외한 부분
        log_record["module"] = record.module

        # ==================== 함수 이름 ====================
        # [funcName]
        # 로그가 호출된 함수의 이름
        log_record["function"] = record.funcName

        # ==================== 줄 번호 ====================
        # [lineno]
        # 로그가 호출된 소스 코드의 줄 번호
        log_record["line"] = record.lineno


# ============================================================================
# 로깅 설정 함수 (Setup Logging Function)
# ============================================================================

def setup_logging() -> logging.Logger:
    """
    Set up application logging.
    애플리케이션 로깅 설정.

    [한국어 설명]
    다양한 핸들러(콘솔, 파일, JSON, 에러)를 설정하여
    로그 메시지를 여러 출력으로 라우팅합니다.

    [핸들러 구성]
    1. Console Handler: 콘솔 출력 (개발 시 실시간 확인)
    2. File Handler: 일반 로그 파일 (hmi.log)
    3. JSON Handler: 구조화된 로그 (hmi_json.log, 분석 도구 연동)
    4. Error Handler: 에러 전용 파일 (hmi_error.log)

    [Rotating 파일]
    파일 크기가 설정된 값을 초과하면 자동으로 백업 파일 생성
    예: hmi.log → hmi.log.1 → hmi.log.2 (최대 backupCount개)

    Returns:
        logging.Logger: 설정된 루트 로거 인스턴스
    """

    # ==================== 로그 디렉토리 생성 ====================
    # [설정에서 경로 가져오기]
    # settings.LOG_DIR: Path 객체
    log_dir = settings.LOG_DIR

    # [mkdir()]
    # 디렉토리가 없으면 생성
    # parents=True: 상위 디렉토리도 함께 생성
    # exist_ok=True: 이미 존재해도 에러 없음
    log_dir.mkdir(parents=True, exist_ok=True)

    # ==================== 루트 로거 설정 ====================
    # [getLogger("hmi")]
    # "hmi"라는 이름의 루트 로거 가져오기
    # 하위 로거들은 "hmi.hardware", "hmi.api" 등의 이름을 가짐
    logger = logging.getLogger("hmi")

    # [setLevel()]
    # 로거의 최소 로그 레벨 설정
    # 이 레벨 미만의 로그는 처리하지 않음
    # getattr(logging, "INFO") → logging.INFO (20)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # [handlers 초기화]
    # 기존 핸들러 제거 (중복 방지)
    # 앱 재시작 시 핸들러가 누적되는 것을 방지
    logger.handlers = []

    # ==================== 콘솔 핸들러 설정 ====================
    # [Console Handler]
    # 터미널/콘솔에 로그 출력
    # 개발 중 실시간 디버깅에 유용

    # [StreamHandler(sys.stdout)]
    # 표준 출력(stdout)으로 로그 전송
    # stderr 대신 stdout 사용 (일부 IDE 호환성)
    console_handler = logging.StreamHandler(sys.stdout)

    # [DEBUG 모드 분기]
    # 디버그 모드: DEBUG 레벨부터 출력
    # 프로덕션 모드: INFO 레벨부터 출력
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # [Formatter 설정]
    # 로그 메시지 형식 정의
    # %(asctime)s: 시간
    # %(levelname)-8s: 레벨 (8자 왼쪽 정렬)
    # %(name)s: 로거 이름
    # %(funcName)s: 함수 이름
    # %(lineno)d: 줄 번호
    # %(message)s: 로그 메시지
    console_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"  # 날짜 형식: 2024-01-15 12:30:45
    )
    console_handler.setFormatter(console_format)

    # [핸들러 등록]
    logger.addHandler(console_handler)

    # ==================== 파일 핸들러 설정 (일반 로그) ====================
    # [File Handler - Rotating]
    # 로그를 파일에 기록
    # 파일 크기가 커지면 자동으로 로테이션

    # [RotatingFileHandler 매개변수]
    # filename: 로그 파일 경로
    # maxBytes: 최대 파일 크기 (바이트 단위)
    # backupCount: 보관할 백업 파일 수
    # encoding: 파일 인코딩 (UTF-8 권장)
    file_handler = RotatingFileHandler(
        log_dir / "hmi.log",                    # logs/hmi.log
        maxBytes=settings.LOG_MAX_SIZE,         # 기본: 10MB
        backupCount=settings.LOG_BACKUP_COUNT,  # 기본: 5개 백업
        encoding="utf-8"
    )

    # [DEBUG 레벨]
    # 파일에는 모든 레벨의 로그 저장
    file_handler.setLevel(logging.DEBUG)

    # [콘솔과 동일한 포맷]
    file_handler.setFormatter(console_format)

    # [핸들러 등록]
    logger.addHandler(file_handler)

    # ==================== JSON 파일 핸들러 설정 ====================
    # [JSON Handler]
    # 구조화된 로그 (JSON 형식)
    # ELK Stack, Grafana Loki 등 로그 분석 도구 연동에 적합

    json_handler = RotatingFileHandler(
        log_dir / "hmi_json.log",               # logs/hmi_json.log
        maxBytes=settings.LOG_MAX_SIZE,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8"
    )

    # [INFO 레벨]
    # JSON 로그는 INFO 이상만 (용량 절약)
    json_handler.setLevel(logging.INFO)

    # [커스텀 JSON 포매터 사용]
    json_handler.setFormatter(CustomJsonFormatter())

    # [핸들러 등록]
    logger.addHandler(json_handler)

    # ==================== 에러 파일 핸들러 설정 ====================
    # [Error Handler]
    # 에러 로그만 별도 파일에 저장
    # 문제 추적/모니터링에 유용

    error_handler = RotatingFileHandler(
        log_dir / "hmi_error.log",              # logs/hmi_error.log
        maxBytes=settings.LOG_MAX_SIZE,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8"
    )

    # [ERROR 레벨]
    # ERROR와 CRITICAL만 기록
    error_handler.setLevel(logging.ERROR)

    # [콘솔과 동일한 포맷]
    error_handler.setFormatter(console_format)

    # [핸들러 등록]
    logger.addHandler(error_handler)

    # ==================== 초기화 완료 로그 ====================
    # [설정 완료 확인 메시지]
    logger.info(f"Logging initialized. Level: {settings.LOG_LEVEL}, Dir: {log_dir}")

    return logger


# ============================================================================
# 로거 가져오기 함수 (Get Logger Function)
# ============================================================================

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    지정된 이름의 로거를 가져옵니다.

    [한국어 설명]
    모듈별로 개별 로거를 생성하여 로그 출처를 구분합니다.
    "hmi" 루트 로거의 하위 로거로 생성됩니다.

    [로거 계층 구조]
    - "hmi" (루트)
      ├── "hmi.hardware" (하드웨어 모듈)
      │   ├── "hmi.hardware.gpio_controller"
      │   └── "hmi.hardware.sensor_controller"
      ├── "hmi.api" (API 모듈)
      └── "hmi.services" (서비스 모듈)

    [사용 예시]
    from app.core.logging_config import get_logger
    logger = get_logger(__name__)  # __name__ = "app.hardware.gpio"
    logger.info("LED turned on")

    Args:
        name: 로거 이름 (일반적으로 __name__ 사용)

    Returns:
        logging.Logger: 해당 이름의 로거 인스턴스

    [장점]
    - 로그 메시지에 모듈 이름 포함
    - 모듈별 로그 레벨 개별 설정 가능
    - 로그 필터링 용이
    """
    # [하위 로거 생성]
    # "hmi." + name 형식으로 로거 이름 구성
    # 예: "hmi.app.hardware.gpio_controller"
    return logging.getLogger(f"hmi.{name}")
