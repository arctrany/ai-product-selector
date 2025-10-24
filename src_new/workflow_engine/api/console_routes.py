"""Console UI routes for workflow engine."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .dependencies import app_manager_dependency, db_manager_dependency, config_dependency
from ..apps import AppManager
from ..storage.database import DatabaseManager
from ..utils.logger import get_logger

logger = get_logger(__name__)

def create_console_router() -> APIRouter:
    """Create console UI routes."""
    router = APIRouter(tags=["console"])

    @router.get("/console", response_class=HTMLResponse)
    async def app_console(
            request: Request,
            id: Optional[str] = Query(None, description="Console ID in format: app_id-flow_id"),
            app_manager: AppManager = Depends(app_manager_dependency),
            db_manager: DatabaseManager = Depends(db_manager_dependency),
            config = Depends(config_dependency)
    ):
        """Application console view with optional app-specific context."""

        # Initialize templates with config-based directory
        templates = Jinja2Templates(directory=str(config.get_templates_directory_path()))

        if not id:
            # Return global console view
            return templates.TemplateResponse(
                "console.html",
                {
                    "request": request,
                    "console_type": "global",
                    "title": "Workflow Engine Console",
                    "subtitle": "Ren工作流引擎管理控制台"
                }
            )

        # Parse and validate console ID
        context = app_manager.create_run_context(id)
        if not context:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid console ID format or app/flow not found: {id}"
            )

        # Get current runs for this app/flow combination
        runs = []
        try:
            all_runs = db_manager.list_runs()
            # Filter runs by flow_id (simplified - in real implementation might need more sophisticated filtering)
            runs = [run for run in all_runs if hasattr(run, 'flow_id') and run.flow_id == context.flow_id]
        except Exception as e:
            logger.warning(f"Failed to get runs for {id}: {e}")

        return templates.TemplateResponse(
            "app_console.html",
            {
                "request": request,
                "console_type": "application",
                "console_id": id,
                "app_config": context.app_config,
                "flow_id": context.flow_id,
                "title": context.app_config.console_title,
                "subtitle": context.app_config.console_subtitle or f"Flow: {context.flow_id}",
                "runs": runs,
                "extensions": context.app_config.extensions
            }
        )

    @router.get("/console/stats")
    async def console_stats(
            app_manager: AppManager = Depends(app_manager_dependency),
            db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """Get console statistics."""
        try:
            apps = app_manager.list_apps()
            all_runs = db_manager.list_runs()

            # Calculate statistics
            stats = {
                "apps": {
                    "total": len(apps),
                    "active": len([app for app in apps if getattr(app, 'enabled', True)])
                },
                "flows": {
                    "total": sum(len(app.flow_ids) for app in apps)
                },
                "runs": {
                    "total": len(all_runs),
                    "running": len([run for run in all_runs if getattr(run, 'status', '') == 'running']),
                    "completed": len([run for run in all_runs if getattr(run, 'status', '') == 'completed']),
                    "failed": len([run for run in all_runs if getattr(run, 'status', '') == 'failed'])
                }
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get console statistics: {e}")
            return {
                "apps": {"total": 0, "active": 0},
                "flows": {"total": 0},
                "runs": {"total": 0, "running": 0, "completed": 0, "failed": 0}
            }

    @router.get("/console/health")
    async def console_health(config = Depends(config_dependency)):
        """Console health check endpoint."""
        return {
            "status": "healthy",
            "console_type": "workflow_engine",
            "timestamp": datetime.utcnow().isoformat(),
            "version": config.server.version
        }

    return router