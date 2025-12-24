"""
System Monitor Service
======================

Monitors system resources (CPU, Memory, Disk, Temperature).
Essential for HMI to track Raspberry Pi health.
"""

import asyncio
import platform
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field

import psutil

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class SystemMetrics:
    """System metrics snapshot."""
    timestamp: datetime = field(default_factory=datetime.now)

    # CPU
    cpu_percent: float = 0.0
    cpu_count: int = 0
    cpu_freq_current: float = 0.0
    cpu_freq_max: float = 0.0
    cpu_temp: Optional[float] = None

    # Memory
    memory_total: int = 0
    memory_available: int = 0
    memory_used: int = 0
    memory_percent: float = 0.0

    # Disk
    disk_total: int = 0
    disk_used: int = 0
    disk_free: int = 0
    disk_percent: float = 0.0

    # Network
    net_bytes_sent: int = 0
    net_bytes_recv: int = 0

    # System
    boot_time: datetime = None
    uptime_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu": {
                "percent": round(self.cpu_percent, 1),
                "count": self.cpu_count,
                "frequency": {
                    "current": round(self.cpu_freq_current, 0),
                    "max": round(self.cpu_freq_max, 0)
                },
                "temperature": round(self.cpu_temp, 1) if self.cpu_temp else None
            },
            "memory": {
                "total": self.memory_total,
                "available": self.memory_available,
                "used": self.memory_used,
                "percent": round(self.memory_percent, 1),
                "total_gb": round(self.memory_total / (1024**3), 2),
                "used_gb": round(self.memory_used / (1024**3), 2)
            },
            "disk": {
                "total": self.disk_total,
                "used": self.disk_used,
                "free": self.disk_free,
                "percent": round(self.disk_percent, 1),
                "total_gb": round(self.disk_total / (1024**3), 2),
                "free_gb": round(self.disk_free / (1024**3), 2)
            },
            "network": {
                "bytes_sent": self.net_bytes_sent,
                "bytes_recv": self.net_bytes_recv,
                "sent_mb": round(self.net_bytes_sent / (1024**2), 2),
                "recv_mb": round(self.net_bytes_recv / (1024**2), 2)
            },
            "system": {
                "boot_time": self.boot_time.isoformat() if self.boot_time else None,
                "uptime_seconds": round(self.uptime_seconds, 0),
                "uptime_hours": round(self.uptime_seconds / 3600, 2)
            }
        }


class SystemMonitor:
    """
    System resource monitoring service.

    Provides real-time and historical system metrics.
    Especially important for Raspberry Pi to prevent overheating.
    """

    def __init__(self):
        self._current_metrics: Optional[SystemMetrics] = None
        self._history: List[SystemMetrics] = []
        self._max_history = 1000  # Keep last 1000 samples
        self._update_task: Optional[asyncio.Task] = None
        self._running = False

    @property
    def current(self) -> Optional[SystemMetrics]:
        """Get current system metrics."""
        return self._current_metrics

    @property
    def history(self) -> List[SystemMetrics]:
        """Get metrics history."""
        return self._history

    async def start(self) -> None:
        """Start the monitoring loop."""
        if self._running:
            return

        self._running = True
        self._update_task = asyncio.create_task(self._monitor_loop())
        logger.info("System monitor started")

    async def stop(self) -> None:
        """Stop the monitoring loop."""
        self._running = False

        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
            self._update_task = None

        logger.info("System monitor stopped")

    async def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        while self._running:
            try:
                await self.collect_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")

            await asyncio.sleep(1.0)  # 1 second interval

    async def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        metrics = SystemMetrics()

        try:
            # CPU
            metrics.cpu_percent = psutil.cpu_percent(interval=None)
            metrics.cpu_count = psutil.cpu_count()

            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                metrics.cpu_freq_current = cpu_freq.current
                metrics.cpu_freq_max = cpu_freq.max

            # CPU Temperature (Raspberry Pi specific)
            metrics.cpu_temp = self._get_cpu_temperature()

            # Memory
            memory = psutil.virtual_memory()
            metrics.memory_total = memory.total
            metrics.memory_available = memory.available
            metrics.memory_used = memory.used
            metrics.memory_percent = memory.percent

            # Disk
            disk = psutil.disk_usage('/')
            metrics.disk_total = disk.total
            metrics.disk_used = disk.used
            metrics.disk_free = disk.free
            metrics.disk_percent = disk.percent

            # Network
            net_io = psutil.net_io_counters()
            metrics.net_bytes_sent = net_io.bytes_sent
            metrics.net_bytes_recv = net_io.bytes_recv

            # System
            boot_timestamp = psutil.boot_time()
            metrics.boot_time = datetime.fromtimestamp(boot_timestamp)
            metrics.uptime_seconds = (datetime.now() - metrics.boot_time).total_seconds()

            # Store metrics
            self._current_metrics = metrics

            # Add to history
            self._history.append(metrics)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

        except Exception as e:
            logger.error(f"Metrics collection error: {e}")

        return metrics

    def _get_cpu_temperature(self) -> Optional[float]:
        """
        Get CPU temperature.

        Works on Raspberry Pi and some other Linux systems.
        """
        try:
            # Try Raspberry Pi thermal zone
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = float(f.read().strip()) / 1000.0
                return temp
        except FileNotFoundError:
            pass

        try:
            # Try psutil sensors
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        if entry.current:
                            return entry.current
        except Exception:
            pass

        return None

    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform information."""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "is_raspberry_pi": settings.is_raspberry_pi
        }

    def get_process_info(self) -> Dict[str, Any]:
        """Get current process information."""
        process = psutil.Process()
        return {
            "pid": process.pid,
            "name": process.name(),
            "status": process.status(),
            "cpu_percent": process.cpu_percent(),
            "memory_percent": round(process.memory_percent(), 2),
            "memory_mb": round(process.memory_info().rss / (1024**2), 2),
            "threads": process.num_threads(),
            "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
        }

    def check_health(self) -> Dict[str, Any]:
        """
        Check system health and return status.

        Returns warnings for:
        - High CPU temperature (>70°C)
        - High CPU usage (>90%)
        - Low memory (<10% available)
        - Low disk space (<10% free)
        """
        if not self._current_metrics:
            return {"status": "unknown", "warnings": ["No metrics available"]}

        warnings = []
        m = self._current_metrics

        # CPU temperature check
        if m.cpu_temp and m.cpu_temp > 70:
            warnings.append(f"High CPU temperature: {m.cpu_temp:.1f}°C")

        if m.cpu_temp and m.cpu_temp > 80:
            warnings.append("CRITICAL: CPU temperature exceeds 80°C!")

        # CPU usage check
        if m.cpu_percent > 90:
            warnings.append(f"High CPU usage: {m.cpu_percent:.1f}%")

        # Memory check
        memory_available_percent = (m.memory_available / m.memory_total) * 100
        if memory_available_percent < 10:
            warnings.append(f"Low memory: {memory_available_percent:.1f}% available")

        # Disk check
        disk_free_percent = (m.disk_free / m.disk_total) * 100
        if disk_free_percent < 10:
            warnings.append(f"Low disk space: {disk_free_percent:.1f}% free")

        status = "healthy" if not warnings else "warning"
        if any("CRITICAL" in w for w in warnings):
            status = "critical"

        return {
            "status": status,
            "warnings": warnings,
            "timestamp": datetime.now().isoformat()
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of system status."""
        if not self._current_metrics:
            return {"error": "No metrics available"}

        m = self._current_metrics
        health = self.check_health()

        return {
            "cpu_percent": round(m.cpu_percent, 1),
            "cpu_temp": round(m.cpu_temp, 1) if m.cpu_temp else None,
            "memory_percent": round(m.memory_percent, 1),
            "disk_percent": round(m.disk_percent, 1),
            "uptime_hours": round(m.uptime_seconds / 3600, 1),
            "health_status": health["status"],
            "warnings": health["warnings"]
        }


# Global instance
system_monitor = SystemMonitor()
