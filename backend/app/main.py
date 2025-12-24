"""
Raspberry Pi HMI - FastAPI Application
======================================

Main application entry point.

This is a Human-Machine Interface (HMI) system designed for Raspberry Pi.
It provides:
- Real-time hardware monitoring and control
- WebSocket-based data push
- System resource monitoring
- SQLite data logging

Usage:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import settings
from app.core.logging_config import setup_logging, get_logger
from app.models.database import init_db
from app.hardware.manager import hardware_manager
from app.services.system_monitor import system_monitor
from app.services.data_logger import data_logger
from app.services.websocket_manager import ws_manager
from app.api import api_router

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # ==================== Startup ====================
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Simulation mode: {settings.SIMULATION_MODE}")

    # Initialize database
    await init_db()

    # Initialize hardware
    await hardware_manager.initialize()

    # Start services
    await system_monitor.start()
    await data_logger.start()
    await ws_manager.start()

    # Register callbacks for real-time updates
    async def on_hardware_update(data):
        """Callback for hardware data updates."""
        # Broadcast to WebSocket clients
        await ws_manager.broadcast_hardware_data(data.to_dict())
        # Log to database (with throttling)
        # Note: actual logging is done at intervals, not every update

    hardware_manager.register_callback(on_hardware_update)

    # Start hardware update loop
    await hardware_manager.start_update_loop()

    # Create periodic data logging task
    async def periodic_data_log():
        while True:
            await asyncio.sleep(settings.DATA_LOG_INTERVAL)
            if hardware_manager.current_data:
                await data_logger.log_hardware_data(hardware_manager.current_data)

    log_task = asyncio.create_task(periodic_data_log())

    # Create periodic system metrics broadcast
    async def periodic_system_broadcast():
        while True:
            await asyncio.sleep(1.0)  # 1 second interval
            if system_monitor.current:
                await ws_manager.broadcast_system_metrics(
                    system_monitor.current.to_dict()
                )

    system_task = asyncio.create_task(periodic_system_broadcast())

    logger.info("Application started successfully")

    yield

    # ==================== Shutdown ====================
    logger.info("Shutting down application...")

    # Cancel tasks
    log_task.cancel()
    system_task.cancel()

    try:
        await log_task
        await system_task
    except asyncio.CancelledError:
        pass

    # Stop services
    await ws_manager.stop()
    await data_logger.stop()
    await system_monitor.stop()
    await hardware_manager.stop_update_loop()
    await hardware_manager.cleanup()

    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## Raspberry Pi HMI System

    A real-time Human-Machine Interface for Raspberry Pi.

    ### Features:
    - **Hardware Control**: GPIO, PWM, I2C, SPI, Sensors, Displays
    - **Real-time Updates**: WebSocket-based data push
    - **System Monitoring**: CPU, Memory, Disk, Temperature
    - **Data Logging**: SQLite with WAL mode
    - **Simulation Mode**: For development without hardware

    ### WebSocket:
    Connect to `/api/ws/live` for real-time updates.
    """,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


# Include API router
app.include_router(api_router, prefix="/api")


# Serve static files (React build)
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Serve React app for all other routes
@app.get("/")
async def serve_react_app():
    """Serve the React application."""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Welcome to Raspberry Pi HMI API", "docs": "/api/docs"}


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve SPA for client-side routing."""
    # Check if it's a static file
    file_path = static_dir / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))

    # Otherwise serve index.html for SPA routing
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))

    # If no React build, return API info
    return {"message": "API endpoint not found", "docs": "/api/docs"}


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "simulation": settings.SIMULATION_MODE
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )
