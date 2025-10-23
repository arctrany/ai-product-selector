"""FastAPI server for workflow engine."""

from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .dependencies import init_dependencies
from .exceptions import setup_exception_handlers
from .system_routes import create_system_router
from .flow_routes import create_flow_router
from .workflow_routes import create_workflow_router
from .workflow_ws import create_websocket_router
from .console_routes import create_console_router
from .app_routes import create_app_router
from ..utils.logger import get_logger
from ..config import get_config

logger = get_logger(__name__)

def create_app(db_path: Optional[str] = None) -> FastAPI:
    """Create FastAPI application with modular route structure."""
    
    # Load configuration
    config = get_config()

    # Create FastAPI app
    app = FastAPI(
        title=config.server.title,
        description=config.server.description,
        version=config.server.version
    )

    # Initialize workflow engine
    from ..core.engine import WorkflowEngine
    if db_path is None:
        db_path = str(config.get_database_path())
    engine = WorkflowEngine(db_path)

    # Initialize app manager
    from ..apps.manager import AppManager
    apps_dir = config.get_apps_directory_path()
    app_manager = AppManager(str(apps_dir))

    # Initialize templates
    templates_dir = config.get_templates_directory_path()
    templates = Jinja2Templates(directory=str(templates_dir))

    # Initialize dependencies
    init_dependencies(engine, app_manager, templates, config)

    # Setup exception handlers
    setup_exception_handlers(app)

    # Root endpoint - simple status message
    @app.get("/")
    async def root():
        """Root endpoint - simple status message."""
        return {"message": "It works!"}

    # Apps list page
    @app.get("/apps", response_class=HTMLResponse)
    async def app_list_page(request: Request):
        """Application list page."""
        from .dependencies import app_manager_dependency
        app_manager = await app_manager_dependency()
        apps = app_manager.list_apps()
        total_flows = sum(len(app.flow_ids) for app in apps)

        return templates.TemplateResponse("app_list.html", {
            "request": request,
            "apps": apps,
            "total_flows": total_flows
        })

    # Include all route modules
    app.include_router(create_system_router(), prefix="", tags=["system"])
    app.include_router(create_flow_router(), prefix="/api", tags=["flows"])
    app.include_router(create_workflow_router(), prefix="/api", tags=["workflows"])
    app.include_router(create_websocket_router(), prefix="/api", tags=["websocket"])
    app.include_router(create_console_router(), prefix="", tags=["console"])
    app.include_router(create_app_router(), prefix="", tags=["applications"])

    logger.info("FastAPI application created with modular route structure")
    return app

# Server startup script
if __name__ == "__main__":
    import uvicorn

    config = get_config()
    app = create_app()

    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.port,
        reload=config.development.reload
    )