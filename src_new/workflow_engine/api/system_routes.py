"""System-level API routes."""

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from .dependencies import config_dependency
from ..utils.logger import get_logger

logger = get_logger(__name__)

def create_system_router() -> APIRouter:
    """Create system routes."""
    router = APIRouter(tags=["system"])

    @router.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "workflow-engine"}

    @router.get("/")
    async def root():
        """Root endpoint - simple status message."""
        return {"message": "It works!"}

    @router.get("/status")
    async def system_status(config=Depends(config_dependency)):
        """Get system status information."""
        return {
            "status": "running",
            "service": "workflow-engine",
            "version": config.server.version,
            "database_path": str(config.get_database_path()),
            "logging_directory": str(config.get_logging_directory_path()),
            "apps_directory": str(config.get_apps_directory_path()),
            "templates_directory": str(config.get_templates_directory_path())
        }

    return router