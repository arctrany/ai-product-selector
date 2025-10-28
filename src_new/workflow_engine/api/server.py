"""FastAPI server for workflow engine."""

from typing import Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .dependencies import init_dependencies
from .exceptions import setup_exception_handlers
from .system_routes import create_system_router
from .flow_routes import create_flow_router

from .thread_routes import create_thread_router
from .workflow_ws import create_websocket_router
from .console_routes import create_console_router
from .app_routes import create_app_router
from ..utils.logger import get_logger, setup_logging
from ..core.config import get_config

# Initialize logging first
from ..config.loader import CrossPlatformConfigLoader
config_loader = CrossPlatformConfigLoader()
raw_config = config_loader.load_config()
logging_config = raw_config.get("logging", {})
setup_logging(
    log_level=logging_config.get("level", "INFO"),
    log_dir=logging_config.get("directory"),
    enable_console=logging_config.get("console_output", True)
)

logger = get_logger(__name__)

def _bootstrap_workflows(engine, app_manager):
    """Bootstrap workflow definitions from apps into database."""
    try:
        logger.info("🚀 Starting workflow bootstrap process...")

        # Get all apps
        apps = app_manager.list_apps()
        loaded_count = 0

        for app in apps:
            logger.info(f"📦 Processing app: {app.app_id}")

            # Process each flow in the app
            for flow_name, flow_config in app.flows.items():
                try:
                    # Get flow_id from config
                    flow_id = getattr(flow_config, 'flow_id', flow_name)
                    version = getattr(flow_config, 'version', '1.0.0')

                    # Always load workflow definition to ensure functions are registered
                    # even if the flow already exists in database
                    logger.info(f"  🔄 Loading workflow definition for {app.app_id}.{flow_name}")
                    workflow_definition = app_manager.load_workflow_definition(app.app_id, flow_name)

                    # Check if flow already exists in database
                    existing_flow = engine.db_manager.get_flow_by_name(flow_id)
                    if existing_flow:
                        logger.info(f"  ⏭️  Flow {flow_id} already exists in database, but functions are now registered")
                        continue

                    # Workflow definition already loaded above for function registration

                    # Create flow in database
                    db_flow_id = engine.create_flow(
                        name=flow_id,
                        definition=workflow_definition,
                        version=version
                    )

                    logger.info(f"  ✅ Successfully loaded {flow_id} (DB ID: {db_flow_id})")
                    loaded_count += 1

                except Exception as e:
                    logger.error(f"  ❌ Failed to load {app.app_id}.{flow_name}: {e}")
                    continue

        logger.info(f"🎉 Workflow bootstrap completed! Loaded {loaded_count} workflows")

    except Exception as e:
        logger.error(f"❌ Workflow bootstrap failed: {e}")
        # Don't raise exception to avoid breaking server startup
        pass


def create_app(db_path: Optional[str] = None) -> FastAPI:
    """Create FastAPI application with modular route structure."""

    # Load configuration
    config = get_config()

    # Create FastAPI app
    app = FastAPI(
        title="Workflow Engine API",
        description="AI Product Selector Workflow Engine",
        version="1.0.0"
    )

    # Initialize workflow engine
    from ..core.engine import WorkflowEngine
    if db_path is not None:
        # If db_path is provided, create a custom config with that path
        from ..core.config import WorkflowEngineConfig
        custom_config = WorkflowEngineConfig()
        custom_config.db_path = db_path
        engine = WorkflowEngine(custom_config)
    else:
        # Use default config
        engine = WorkflowEngine(config)

    # Initialize app manager
    from ..apps.manager import AppManager
    # Use config to get apps directory path for consistency
    apps_dir = config.get_apps_directory_path()

    # Ensure the path is properly resolved and doesn't contain environment variable placeholders
    from ..config.loader import EnvironmentVariableExpander
    from pathlib import Path
    apps_dir_str = str(apps_dir)
    apps_dir_expanded = EnvironmentVariableExpander.expand_value(apps_dir_str)

    # Get project root directory
    project_root = Path.cwd()  # Use current working directory as project root
    if apps_dir_expanded.startswith('/'):
        # Absolute path
        final_apps_dir = Path(apps_dir_expanded)
    else:
        # Relative path
        final_apps_dir = project_root / apps_dir_expanded

    app_manager = AppManager(str(final_apps_dir))

    # Initialize templates
    # Use config to get templates directory path for consistency
    templates_dir = config.get_templates_directory_path()

    # Ensure the templates path is properly resolved and doesn't contain environment variable placeholders
    templates_dir_str = str(templates_dir)
    templates_dir_expanded = EnvironmentVariableExpander.expand_value(templates_dir_str)

    # Get project root directory for templates
    if templates_dir_expanded.startswith('/'):
        # Absolute path
        final_templates_dir = Path(templates_dir_expanded)
    else:
        # Relative path
        final_templates_dir = project_root / templates_dir_expanded

    templates = Jinja2Templates(directory=str(final_templates_dir))

    # Initialize dependencies
    init_dependencies(engine, app_manager, templates, config)

    # Auto-load workflow definitions from apps into database
    _bootstrap_workflows(engine, app_manager)

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

    app.include_router(create_thread_router(), prefix="/api", tags=["threads"])
    app.include_router(create_websocket_router(), prefix="/api", tags=["websocket"])
    app.include_router(create_console_router(), prefix="", tags=["console"])
    app.include_router(create_app_router(), prefix="", tags=["applications"])

    logger.info("FastAPI application created with modular route structure")
    return app


# Server startup script
if __name__ == "__main__":
    import uvicorn

    config = get_config()

    # Use import string for uvicorn to support reload and workers
    # Use default values since WorkflowEngineConfig doesn't have server config
    uvicorn.run(
        "src_new.workflow_engine.api.server:create_app",
        host="0.0.0.0",
        port=8889,
        reload=False,
        factory=True
    )