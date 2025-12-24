"""
Database Configuration
======================

SQLite database setup with async support and WAL mode.
"""

import asyncio
from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Create data directory
data_dir = Path("data")
data_dir.mkdir(parents=True, exist_ok=True)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    connect_args={"check_same_thread": False}
)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()


def enable_wal_mode(dbapi_connection, connection_record):
    """Enable WAL mode for SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=10000")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.close()


async def init_db() -> None:
    """Initialize the database and create tables."""
    logger.info("Initializing database...")

    # Register WAL mode event
    if settings.DATABASE_WAL_MODE:
        from sqlalchemy import event
        from sqlalchemy.engine import Engine

        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            enable_wal_mode(dbapi_connection, connection_record)

    async with engine.begin() as conn:
        # Import all models to ensure they're registered
        from . import sensor_data, system_log, device_state

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized successfully")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def cleanup_old_data(retention_days: int = None) -> int:
    """
    Clean up data older than retention period.

    Args:
        retention_days: Number of days to retain (default from settings)

    Returns:
        Number of deleted records
    """
    from datetime import datetime, timedelta
    from sqlalchemy import delete
    from .sensor_data import SensorData
    from .system_log import SystemLog

    retention_days = retention_days or settings.DATA_RETENTION_DAYS
    cutoff_date = datetime.now() - timedelta(days=retention_days)

    deleted_count = 0

    async with async_session() as session:
        # Delete old sensor data
        result = await session.execute(
            delete(SensorData).where(SensorData.timestamp < cutoff_date)
        )
        deleted_count += result.rowcount

        # Delete old system logs
        result = await session.execute(
            delete(SystemLog).where(SystemLog.timestamp < cutoff_date)
        )
        deleted_count += result.rowcount

        await session.commit()

    logger.info(f"Cleaned up {deleted_count} old records (older than {retention_days} days)")
    return deleted_count
