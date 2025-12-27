"""
System Monitor Service (시스템 모니터 서비스)
======================

[한국어 설명]
시스템 리소스(CPU, 메모리, 디스크, 온도)를 모니터링하는 서비스입니다.
Raspberry Pi의 상태를 실시간으로 추적하여 과열이나 리소스 부족을 감지합니다.

[핵심 개념]
1. psutil 라이브러리:
   - Python의 시스템 모니터링 라이브러리
   - CPU, 메모리, 디스크, 네트워크 정보 수집
   - 크로스 플랫폼 지원 (Windows, Linux, macOS)

2. 시스템 메트릭 (System Metrics):
   - CPU 사용률, 주파수, 온도
   - 메모리 사용량 (전체, 사용 중, 가용)
   - 디스크 사용량
   - 네트워크 I/O

3. 헬스 체크 (Health Check):
   - 임계값 기반 경고 시스템
   - CPU 온도 70°C 이상: 경고
   - CPU 사용률 90% 이상: 경고
   - 메모리/디스크 여유 10% 미만: 경고

[Raspberry Pi 특화]
- CPU 온도는 /sys/class/thermal/thermal_zone0/temp에서 읽음
- 과열 방지를 위한 모니터링이 특히 중요
"""

import asyncio  # 비동기 프로그래밍
import platform  # 플랫폼 정보 (OS, 아키텍처 등)

# 타입 힌트
from typing import Dict, Any, Optional, List

# 날짜/시간 처리
from datetime import datetime

# 데이터 클래스 데코레이터
from dataclasses import dataclass, field

# [psutil]
# Process and System Utilities
# 시스템 모니터링을 위한 크로스 플랫폼 라이브러리
# CPU, 메모리, 디스크, 네트워크, 프로세스 정보 제공
import psutil

# 프로젝트 설정 및 로거
from app.core.config import settings
from app.core.logging_config import get_logger

# 이 모듈용 로거
logger = get_logger(__name__)


# ==================== 시스템 메트릭 데이터 클래스 ====================
@dataclass
class SystemMetrics:
    """
    System metrics snapshot.
    시스템 메트릭 스냅샷.

    [한국어 설명]
    특정 시점의 시스템 상태를 저장하는 데이터 클래스입니다.
    모든 주요 시스템 지표를 하나의 객체로 묶어서 관리합니다.

    [필드 기본값]
    field(default_factory=...)를 사용하면
    인스턴스 생성 시마다 새 객체가 생성됩니다.
    """

    # [타임스탬프]
    # 메트릭이 수집된 시간
    # default_factory: 객체 생성 시 datetime.now() 호출
    timestamp: datetime = field(default_factory=datetime.now)

    # ==================== CPU 관련 필드 ====================

    # CPU 사용률 (0-100%)
    cpu_percent: float = 0.0

    # CPU 코어 수 (논리적 코어)
    cpu_count: int = 0

    # 현재 CPU 주파수 (MHz)
    cpu_freq_current: float = 0.0

    # 최대 CPU 주파수 (MHz)
    cpu_freq_max: float = 0.0

    # CPU 온도 (섭씨) - Raspberry Pi에서 특히 중요
    # Optional: 온도 센서가 없는 시스템에서는 None
    cpu_temp: Optional[float] = None

    # ==================== 메모리 관련 필드 ====================

    # 전체 메모리 (바이트)
    memory_total: int = 0

    # 가용 메모리 (바이트) - 실제 사용 가능한 양
    memory_available: int = 0

    # 사용 중인 메모리 (바이트)
    memory_used: int = 0

    # 메모리 사용률 (0-100%)
    memory_percent: float = 0.0

    # ==================== 디스크 관련 필드 ====================

    # 전체 디스크 공간 (바이트)
    disk_total: int = 0

    # 사용 중인 디스크 공간 (바이트)
    disk_used: int = 0

    # 남은 디스크 공간 (바이트)
    disk_free: int = 0

    # 디스크 사용률 (0-100%)
    disk_percent: float = 0.0

    # ==================== 네트워크 관련 필드 ====================

    # 총 송신 바이트
    net_bytes_sent: int = 0

    # 총 수신 바이트
    net_bytes_recv: int = 0

    # ==================== 시스템 관련 필드 ====================

    # 부팅 시간
    boot_time: datetime = None

    # 가동 시간 (초)
    uptime_seconds: float = 0.0

    # ==================== 메서드 ====================
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.
        JSON 직렬화를 위한 딕셔너리 변환.

        [한국어 설명]
        시스템 메트릭을 API 응답이나 WebSocket 전송에
        적합한 구조화된 딕셔너리로 변환합니다.
        단위 변환(바이트->GB, 초->시간)도 포함합니다.
        """
        return {
            # ISO 8601 형식 타임스탬프
            "timestamp": self.timestamp.isoformat(),

            # [CPU 정보]
            "cpu": {
                "percent": round(self.cpu_percent, 1),  # 소수점 1자리
                "count": self.cpu_count,
                "frequency": {
                    "current": round(self.cpu_freq_current, 0),  # 정수
                    "max": round(self.cpu_freq_max, 0)
                },
                # 온도가 있으면 반올림, 없으면 None
                "temperature": round(self.cpu_temp, 1) if self.cpu_temp else None
            },

            # [메모리 정보]
            "memory": {
                "total": self.memory_total,
                "available": self.memory_available,
                "used": self.memory_used,
                "percent": round(self.memory_percent, 1),
                # [단위 변환: 바이트 -> GB]
                # 1024^3 = 1,073,741,824 (1GB)
                "total_gb": round(self.memory_total / (1024**3), 2),
                "used_gb": round(self.memory_used / (1024**3), 2)
            },

            # [디스크 정보]
            "disk": {
                "total": self.disk_total,
                "used": self.disk_used,
                "free": self.disk_free,
                "percent": round(self.disk_percent, 1),
                "total_gb": round(self.disk_total / (1024**3), 2),
                "free_gb": round(self.disk_free / (1024**3), 2)
            },

            # [네트워크 정보]
            "network": {
                "bytes_sent": self.net_bytes_sent,
                "bytes_recv": self.net_bytes_recv,
                # [단위 변환: 바이트 -> MB]
                "sent_mb": round(self.net_bytes_sent / (1024**2), 2),
                "recv_mb": round(self.net_bytes_recv / (1024**2), 2)
            },

            # [시스템 정보]
            "system": {
                "boot_time": self.boot_time.isoformat() if self.boot_time else None,
                "uptime_seconds": round(self.uptime_seconds, 0),
                # [단위 변환: 초 -> 시간]
                "uptime_hours": round(self.uptime_seconds / 3600, 2)
            }
        }


# ==================== 시스템 모니터 클래스 ====================
class SystemMonitor:
    """
    System resource monitoring service.
    시스템 리소스 모니터링 서비스.

    [한국어 설명]
    실시간 및 히스토리 시스템 메트릭을 제공합니다.
    Raspberry Pi의 과열 방지를 위해 특히 중요합니다.

    [주요 기능]
    - 1초 간격 자동 메트릭 수집
    - 최근 1000개 샘플 이력 유지
    - CPU 온도, 사용률 모니터링
    - 헬스 체크 및 경고 생성
    """

    def __init__(self):
        """
        SystemMonitor 초기화.

        [속성 설명]
        - _current_metrics: 가장 최근 수집된 메트릭
        - _history: 메트릭 이력 (최대 1000개)
        - _max_history: 이력 최대 크기
        - _update_task: 백그라운드 모니터링 태스크
        - _running: 실행 상태 플래그
        """
        # 현재 메트릭 (None이면 아직 수집 안됨)
        self._current_metrics: Optional[SystemMetrics] = None

        # 메트릭 이력 리스트
        self._history: List[SystemMetrics] = []

        # 이력 최대 크기 (메모리 사용량 제한)
        self._max_history = 1000  # 1000개 샘플 = 약 16분 (1초 간격)

        # 백그라운드 모니터링 태스크 핸들
        self._update_task: Optional[asyncio.Task] = None

        # 실행 상태 플래그
        self._running = False

    # ==================== 프로퍼티 ====================
    @property
    def current(self) -> Optional[SystemMetrics]:
        """
        Get current system metrics.
        현재 시스템 메트릭 반환.

        [한국어 설명]
        가장 최근에 수집된 시스템 메트릭을 반환합니다.
        아직 수집된 적이 없으면 None을 반환합니다.
        """
        return self._current_metrics

    @property
    def history(self) -> List[SystemMetrics]:
        """
        Get metrics history.
        메트릭 이력 반환.

        [한국어 설명]
        수집된 메트릭의 이력 리스트를 반환합니다.
        트렌드 분석이나 그래프 표시에 사용됩니다.
        """
        return self._history

    # ==================== 생명주기 메서드 ====================
    async def start(self) -> None:
        """
        Start the monitoring loop.
        모니터링 루프 시작.

        [한국어 설명]
        백그라운드에서 1초마다 시스템 메트릭을 수집합니다.
        FastAPI 시작 시 lifespan에서 호출됩니다.
        """
        # 이미 실행 중이면 무시
        if self._running:
            return

        self._running = True

        # [asyncio.create_task()]
        # 코루틴을 백그라운드 태스크로 실행
        # 현재 함수는 바로 반환되고, 루프는 별도로 실행됨
        self._update_task = asyncio.create_task(self._monitor_loop())

        logger.info("System monitor started")

    async def stop(self) -> None:
        """
        Stop the monitoring loop.
        모니터링 루프 중지.

        [한국어 설명]
        백그라운드 모니터링을 중지합니다.
        FastAPI 종료 시 lifespan에서 호출됩니다.
        """
        self._running = False

        if self._update_task:
            # 태스크 취소 요청
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                # 정상적인 취소
                pass
            self._update_task = None

        logger.info("System monitor stopped")

    async def _monitor_loop(self) -> None:
        """
        Background monitoring loop.
        백그라운드 모니터링 루프.

        [한국어 설명]
        1초마다 시스템 메트릭을 수집하는 무한 루프입니다.
        에러가 발생해도 루프를 계속 유지합니다 (안정성).
        """
        while self._running:
            try:
                # 메트릭 수집
                await self.collect_metrics()

            except asyncio.CancelledError:
                # 취소 요청 시 루프 종료
                break

            except Exception as e:
                # 개별 수집 실패는 로그만 남기고 계속
                logger.error(f"Monitor loop error: {e}")

            # [asyncio.sleep()]
            # 비동기 대기 (다른 태스크 실행 허용)
            # 1초 간격으로 메트릭 수집
            await asyncio.sleep(1.0)

    # ==================== 메트릭 수집 ====================
    async def collect_metrics(self) -> SystemMetrics:
        """
        Collect current system metrics.
        현재 시스템 메트릭 수집.

        [한국어 설명]
        psutil 라이브러리를 사용하여 시스템 정보를 수집합니다.
        수집된 데이터는 현재 메트릭과 이력에 저장됩니다.

        Returns:
            SystemMetrics: 수집된 메트릭 객체
        """
        # 새 메트릭 객체 생성
        metrics = SystemMetrics()

        try:
            # ==================== CPU 정보 수집 ====================

            # [psutil.cpu_percent()]
            # CPU 사용률 반환 (0-100%)
            # interval=None: 이전 호출 이후의 평균값 반환
            # interval=1.0: 1초간 측정 후 반환 (블로킹)
            metrics.cpu_percent = psutil.cpu_percent(interval=None)

            # [psutil.cpu_count()]
            # 논리적 CPU 코어 수
            # Raspberry Pi 4: 4코어
            metrics.cpu_count = psutil.cpu_count()

            # [psutil.cpu_freq()]
            # CPU 주파수 정보 (current, min, max)
            # 일부 시스템에서는 None 반환
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                metrics.cpu_freq_current = cpu_freq.current
                metrics.cpu_freq_max = cpu_freq.max

            # [CPU 온도]
            # Raspberry Pi 특화 함수 호출
            metrics.cpu_temp = self._get_cpu_temperature()

            # ==================== 메모리 정보 수집 ====================

            # [psutil.virtual_memory()]
            # 시스템 메모리 정보 반환
            # total, available, used, percent, free 등
            memory = psutil.virtual_memory()
            metrics.memory_total = memory.total       # 전체 RAM
            metrics.memory_available = memory.available  # 실제 사용 가능
            metrics.memory_used = memory.used         # 사용 중
            metrics.memory_percent = memory.percent   # 사용률

            # ==================== 디스크 정보 수집 ====================

            # [psutil.disk_usage('/')]
            # 루트 파티션의 디스크 사용량
            # Windows에서는 'C:' 등으로 변경 필요
            disk = psutil.disk_usage('/')
            metrics.disk_total = disk.total
            metrics.disk_used = disk.used
            metrics.disk_free = disk.free
            metrics.disk_percent = disk.percent

            # ==================== 네트워크 정보 수집 ====================

            # [psutil.net_io_counters()]
            # 네트워크 I/O 통계
            # bytes_sent, bytes_recv: 누적 바이트 수
            net_io = psutil.net_io_counters()
            metrics.net_bytes_sent = net_io.bytes_sent
            metrics.net_bytes_recv = net_io.bytes_recv

            # ==================== 시스템 정보 수집 ====================

            # [psutil.boot_time()]
            # 시스템 부팅 시간 (Unix 타임스탬프)
            boot_timestamp = psutil.boot_time()
            metrics.boot_time = datetime.fromtimestamp(boot_timestamp)

            # [가동 시간 계산]
            # 현재 시간 - 부팅 시간 = 가동 시간
            # .total_seconds(): timedelta를 초 단위 float로 변환
            metrics.uptime_seconds = (datetime.now() - metrics.boot_time).total_seconds()

            # ==================== 메트릭 저장 ====================

            # 현재 메트릭 업데이트
            self._current_metrics = metrics

            # 이력에 추가
            self._history.append(metrics)

            # [이력 크기 제한]
            # 메모리 사용량을 제한하기 위해 오래된 데이터 삭제
            # 슬라이싱으로 최근 N개만 유지
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

        except Exception as e:
            logger.error(f"Metrics collection error: {e}")

        return metrics

    def _get_cpu_temperature(self) -> Optional[float]:
        """
        Get CPU temperature.
        CPU 온도 조회.

        [한국어 설명]
        Raspberry Pi 및 일부 Linux 시스템에서 CPU 온도를 읽습니다.
        여러 방법을 시도하여 가능한 경우 온도를 반환합니다.

        Returns:
            float: CPU 온도 (섭씨), 읽기 실패 시 None

        [Raspberry Pi 온도 파일]
        /sys/class/thermal/thermal_zone0/temp 파일에
        밀리섭씨(1/1000 °C) 단위로 온도가 저장됨
        예: 45000 -> 45.0°C
        """
        try:
            # [방법 1: Raspberry Pi thermal zone 파일]
            # Linux sysfs를 통한 온도 읽기
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                # 밀리섭씨를 섭씨로 변환 (1000으로 나눔)
                temp = float(f.read().strip()) / 1000.0
                return temp

        except FileNotFoundError:
            # 파일이 없으면 (Windows 등) 다음 방법 시도
            pass

        try:
            # [방법 2: psutil sensors_temperatures()]
            # 더 일반적인 방법 (일부 Linux 시스템)
            temps = psutil.sensors_temperatures()

            if temps:
                # 여러 센서 중 첫 번째 유효한 값 반환
                for name, entries in temps.items():
                    for entry in entries:
                        if entry.current:
                            return entry.current

        except Exception:
            # sensors_temperatures()가 지원되지 않는 시스템
            pass

        # 온도를 읽을 수 없음
        return None

    # ==================== 정보 조회 메서드 ====================
    def get_platform_info(self) -> Dict[str, Any]:
        """
        Get platform information.
        플랫폼 정보 조회.

        [한국어 설명]
        운영체제, 아키텍처, Python 버전 등의 정보를 반환합니다.
        시스템 정보 페이지에 표시됩니다.

        Returns:
            플랫폼 정보 딕셔너리
        """
        return {
            # [platform 모듈]
            # 시스템 정보를 반환하는 표준 라이브러리

            # OS 이름: "Windows", "Linux", "Darwin" (macOS)
            "system": platform.system(),

            # OS 릴리스: "10", "5.15.0-generic"
            "release": platform.release(),

            # OS 버전 (상세)
            "version": platform.version(),

            # 하드웨어 아키텍처: "x86_64", "aarch64" (ARM64)
            "machine": platform.machine(),

            # 프로세서 정보
            "processor": platform.processor(),

            # Python 버전: "3.11.0"
            "python_version": platform.python_version(),

            # Raspberry Pi 여부 (settings에서 판단)
            "is_raspberry_pi": settings.is_raspberry_pi
        }

    def get_process_info(self) -> Dict[str, Any]:
        """
        Get current process information.
        현재 프로세스 정보 조회.

        [한국어 설명]
        이 애플리케이션 프로세스의 리소스 사용 정보를 반환합니다.
        메모리 누수 감지 등에 유용합니다.

        Returns:
            프로세스 정보 딕셔너리
        """
        # [psutil.Process()]
        # 현재 프로세스 객체 (인자 없으면 현재 프로세스)
        process = psutil.Process()

        return {
            # 프로세스 ID
            "pid": process.pid,

            # 프로세스 이름: "python", "uvicorn"
            "name": process.name(),

            # 상태: "running", "sleeping", "zombie"
            "status": process.status(),

            # 이 프로세스의 CPU 사용률
            "cpu_percent": process.cpu_percent(),

            # 이 프로세스의 메모리 사용률
            "memory_percent": round(process.memory_percent(), 2),

            # 메모리 사용량 (MB)
            # rss: Resident Set Size (실제 물리 메모리 사용량)
            "memory_mb": round(process.memory_info().rss / (1024**2), 2),

            # 스레드 수
            "threads": process.num_threads(),

            # 프로세스 시작 시간
            "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
        }

    def check_health(self) -> Dict[str, Any]:
        """
        Check system health and return status.
        시스템 건강 상태 확인.

        [한국어 설명]
        시스템 리소스 상태를 점검하고 경고를 생성합니다.
        임계값을 초과하면 warning 또는 critical 상태를 반환합니다.

        Returns:
            {"status": "healthy|warning|critical", "warnings": [...]}

        [임계값]
        - CPU 온도 > 70°C: 경고
        - CPU 온도 > 80°C: 위험
        - CPU 사용률 > 90%: 경고
        - 메모리 여유 < 10%: 경고
        - 디스크 여유 < 10%: 경고
        """
        # 메트릭이 없으면 unknown 상태
        if not self._current_metrics:
            return {"status": "unknown", "warnings": ["No metrics available"]}

        # 경고 메시지 리스트
        warnings = []

        # 편의를 위한 별칭
        m = self._current_metrics

        # ==================== CPU 온도 체크 ====================
        if m.cpu_temp and m.cpu_temp > 70:
            warnings.append(f"High CPU temperature: {m.cpu_temp:.1f}°C")

        if m.cpu_temp and m.cpu_temp > 80:
            # 80도 이상은 위험 수준 (스로틀링 시작)
            warnings.append("CRITICAL: CPU temperature exceeds 80°C!")

        # ==================== CPU 사용률 체크 ====================
        if m.cpu_percent > 90:
            warnings.append(f"High CPU usage: {m.cpu_percent:.1f}%")

        # ==================== 메모리 체크 ====================
        # 가용 메모리 비율 계산
        memory_available_percent = (m.memory_available / m.memory_total) * 100

        if memory_available_percent < 10:
            warnings.append(f"Low memory: {memory_available_percent:.1f}% available")

        # ==================== 디스크 체크 ====================
        # 남은 공간 비율 계산
        disk_free_percent = (m.disk_free / m.disk_total) * 100

        if disk_free_percent < 10:
            warnings.append(f"Low disk space: {disk_free_percent:.1f}% free")

        # ==================== 상태 결정 ====================
        # 경고가 없으면 healthy
        status = "healthy" if not warnings else "warning"

        # CRITICAL 경고가 있으면 critical 상태
        # any(): 하나라도 True면 True 반환
        if any("CRITICAL" in w for w in warnings):
            status = "critical"

        return {
            "status": status,
            "warnings": warnings,
            "timestamp": datetime.now().isoformat()
        }

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of system status.
        시스템 상태 요약 조회.

        [한국어 설명]
        대시보드에 표시할 주요 시스템 지표를 반환합니다.
        상세 정보 대신 핵심 수치만 포함합니다.

        Returns:
            시스템 상태 요약 딕셔너리
        """
        # 메트릭이 없으면 에러 반환
        if not self._current_metrics:
            return {"error": "No metrics available"}

        m = self._current_metrics
        health = self.check_health()

        return {
            # 핵심 수치들
            "cpu_percent": round(m.cpu_percent, 1),
            "cpu_temp": round(m.cpu_temp, 1) if m.cpu_temp else None,
            "memory_percent": round(m.memory_percent, 1),
            "disk_percent": round(m.disk_percent, 1),
            "uptime_hours": round(m.uptime_seconds / 3600, 1),

            # 헬스 체크 결과
            "health_status": health["status"],
            "warnings": health["warnings"]
        }


# ==================== 전역 인스턴스 ====================
# [싱글톤 패턴]
# 모듈 레벨에서 인스턴스 생성하여 애플리케이션 전체에서 공유
system_monitor = SystemMonitor()
