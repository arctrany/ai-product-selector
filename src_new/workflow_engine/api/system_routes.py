"""System-level API routes for workflow engine health monitoring and status reporting."""

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from .dependencies import config_dependency
from ..utils.logger import get_logger

logger = get_logger(__name__)

def create_system_router() -> APIRouter:
    """Create system-level API routes for health monitoring and status reporting.

    Returns:
        APIRouter: Configured router with system endpoints
    """
    router = APIRouter(tags=["system"])

    @router.get("/health")
    async def get_system_health_status():
        """Get system health status for monitoring and load balancer health checks.

        This endpoint provides a simple health check that can be used by:
        - Load balancers for health monitoring
        - Monitoring systems for uptime tracking
        - DevOps tools for service discovery

        Returns:
            dict: Health status information
                - status (str): "healthy" if system is operational
                - service (str): Service identifier "workflow-engine"

        Example Response:
            {
                "status": "healthy",
                "service": "workflow-engine"
            }
        """
        return {"status": "healthy", "service": "workflow-engine"}

    @router.get("/")
    async def get_api_root():
        """Get API root endpoint with basic service information.

        This endpoint serves as the API entry point and provides basic
        confirmation that the service is running and accessible.

        Returns:
            dict: Basic service information
                - message (str): Confirmation message

        Example Response:
            {
                "message": "It works!"
            }
        """
        return {"message": "It works!"}

    @router.get("/status")
    async def get_detailed_system_status(config=Depends(config_dependency)):
        """Get comprehensive system status and configuration information.

        This endpoint provides detailed system information including:
        - Service status and version
        - Database configuration
        - Directory paths
        - System configuration details

        Args:
            config: Injected system configuration dependency

        Returns:
            dict: Comprehensive system status
                - status (str): Current system status
                - service (str): Service identifier
                - version (str): Service version
                - database_path (str): Database file path
                - logging_directory (str): Log files directory
                - apps_directory (str): Applications directory
                - templates_directory (str): Templates directory

        Example Response:
            {
                "status": "running",
                "service": "workflow-engine",
                "version": "1.0.0",
                "database_path": "/path/to/database.db",
                "logging_directory": "/path/to/logs",
                "apps_directory": "/path/to/apps",
                "templates_directory": "/path/to/templates"
            }
        """
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