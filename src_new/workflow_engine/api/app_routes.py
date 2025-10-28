"""Application-specific API routes for workflow engine."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .dependencies import app_manager_dependency, db_manager_dependency, engine_dependency, workflow_control_dependency, \
    config_dependency
from ..apps import AppManager
from ..storage.database import DatabaseManager
from ..core.engine import WorkflowEngine
from ..utils.logger import get_logger
from ..config import get_config
from ..sdk.control import WorkflowControl

# Import Windows compatibility utilities
try:
    from ...utils.windows_compat import normalize_path, is_windows
except ImportError:
    # Fallback implementations if windows_compat is not available
    from pathlib import Path


    def normalize_path(path):
        return Path(path).resolve()


    def is_windows():
        import platform
        return platform.system().lower() == "windows"

logger = get_logger(__name__)


def create_app_router() -> APIRouter:
    """Create application-specific routes."""

    router = APIRouter()

    def parse_flow_version_id(flow_version_param: str) -> tuple[str, Optional[str]]:
        """Parse flow_id-version parameter into flow_id and version."""
        # Check if this looks like a version pattern (contains dots or is numeric)
        if '-' in flow_version_param:
            # Try to find version pattern from the end
            # Version patterns: 1.0.0, 2.1, 1.0.0-beta, etc.
            parts = flow_version_param.split('-')

            # Look for version-like patterns from the end
            for i in range(len(parts) - 1, 0, -1):
                potential_version = '-'.join(parts[i:])
                # Check if this looks like a version (starts with digit and contains dots)
                if potential_version and potential_version[0].isdigit() and ('.' in potential_version):
                    flow_id = '-'.join(parts[:i])
                    return flow_id, potential_version

            # Fallback: check if last part is numeric
            if parts[-1].isdigit():
                return '-'.join(parts[:-1]), parts[-1]

        return flow_version_param, None

    def get_flow_version_by_id_and_version(
            flow_id: str,
            version: Optional[str] = None,
            db_manager: DatabaseManager = None
    ):
        """Get flow version by flow_id and version. If version is None, get latest."""
        try:
            # Get flow from database using flow_id
            flow = db_manager.get_flow_by_name(flow_id)
            if not flow:
                return None, None

            flow_db_id = flow["flow_id"]

            if version:
                # Get specific version
                flow_version = db_manager.get_flow_version_by_version(flow_db_id, version)
            else:
                # Get latest version
                flow_version = db_manager.get_latest_flow_version(flow_db_id)

            return flow, flow_version
        except Exception as e:
            logger.error(f"Failed to get flow version for {flow_id}-{version}: {e}")
            return None, None

    def get_app_by_name_flexible(app_name: str, app_manager: AppManager):
        """Get app by name, supporting both underscore and hyphen formats."""
        # Try exact match first
        app = app_manager.get_app(app_name)
        if app:
            return app

        # Try converting hyphens to underscores
        if '-' in app_name:
            app_name_underscore = app_name.replace('-', '_')
            app = app_manager.get_app(app_name_underscore)
            if app:
                return app

        # Try converting underscores to hyphens
        if '_' in app_name:
            app_name_hyphen = app_name.replace('_', '-')
            app = app_manager.get_app(app_name_hyphen)
            if app:
                return app

        return None

    def parse_flow_identifier(app, flow_identifier: str):
        """Parse flow identifier, supporting flow_name, flow_id, or flow_id-version."""
        # First check if it's a direct flow_name
        if flow_identifier in app.flows:
            flow_config = app.flows[flow_identifier]
            return flow_identifier, flow_config, getattr(flow_config, "flow_id", None), None

        # Check if it's a direct flow_id
        for fname, fconfig in app.flows.items():
            if getattr(fconfig, "flow_id", None) == flow_identifier:
                return fname, fconfig, flow_identifier, None

        # Check if it's flow_id-version format
        flow_id, version = parse_flow_version_id(flow_identifier)
        if version:  # Has version
            for fname, fconfig in app.flows.items():
                if getattr(fconfig, "flow_id", None) == flow_id:
                    return fname, fconfig, flow_id, version

        return None, None, None, None

    # Page routes - supporting both flow_name and flow_id access
    # Note: .htm route must come before the general route to avoid conflicts
    @router.get("/{app_name}/{flow_identifier}.htm", response_class=HTMLResponse, tags=["applications"])
    async def get_flow_custom_page(
            request: Request,
            app_name: str,
            flow_identifier: str,
            app_manager: AppManager = Depends(app_manager_dependency),
            db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """Get flow-specific custom page from web/templates/index.htm."""
        # Validate app exists (flexible matching)
        app = get_app_by_name_flexible(app_name, app_manager)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")

        # Remove .htm suffix if present (FastAPI doesn't strip it automatically)
        if flow_identifier.endswith('.htm'):
            flow_identifier = flow_identifier[:-4]

        # Parse flow identifier
        flow_name, flow_config, flow_id, version = parse_flow_identifier(app, flow_identifier)

        if not flow_config:
            raise HTTPException(status_code=404,
                                detail=f"Flow '{flow_identifier}' not found in application '{app_name}'")

        # Get configuration for apps directory
        config = get_config()
        # Use config to get apps directory path for consistency
        apps_dir = config.get_apps_directory_path()

        # Ensure the path is properly resolved and doesn't contain environment variable placeholders
        from ..config.loader import EnvironmentVariableExpander
        from pathlib import Path
        apps_dir_str = str(apps_dir)
        apps_dir_expanded = EnvironmentVariableExpander.expand_value(apps_dir_str)

        # Get project root directory - use cross-platform path handling
        project_root = normalize_path(Path.cwd())  # Use current working directory as project root
        if Path(apps_dir_expanded).is_absolute():
            # Absolute path
            apps_dir = normalize_path(apps_dir_expanded)
        else:
            # Relative path
            apps_dir = normalize_path(project_root / apps_dir_expanded)

        # Create flow context for template - use cross-platform paths
        flow_context = {
            "flow_path": str(normalize_path(apps_dir / app_name / flow_name)),
            "templates_path": str(normalize_path(apps_dir / app_name / flow_name / "web" / "templates")),
            "scripts_path": str(normalize_path(apps_dir / app_name / flow_name / "web" / "scripts"))
        }

        # Try to load custom template from app's web/templates directory
        import os
        custom_template_path = normalize_path(apps_dir / app_name / flow_name / "web" / "templates" / "index.htm")

        if custom_template_path.exists():
            # Use custom template from app directory
            from fastapi.templating import Jinja2Templates
            app_templates = Jinja2Templates(
                directory=str(normalize_path(apps_dir / app_name / flow_name / "web" / "templates")))

            # Get latest flow version for submit URL
            if not flow_id:
                flow_id = getattr(flow_config, "flow_id", flow_identifier)

            _, flow_version = get_flow_version_by_id_and_version(flow_id, db_manager=db_manager)
            version_id = flow_version["version"] if flow_version else "latest"

            return app_templates.TemplateResponse(
                "index.htm",
                {
                    "request": request,
                    "app_name": app.app_id,
                    "flow_id": flow_id,
                    "flow_name": flow_name,
                    "app_config": app,
                    "flow_config": flow_config,
                    "flow_context": flow_context,
                    "flow_title": getattr(flow_config, "title", flow_name),
                    "flow_description": getattr(flow_config, "description", ""),
                    "title": f"{app.console_title} - {getattr(flow_config, 'title', flow_name)}",
                    "subtitle": getattr(flow_config, "description", f"Flow: {flow_id}"),
                    "console_url": f"/{app.app_id}/{flow_id}",
                    "submit_url": f"/api/flows/{flow_id}-{version_id}/submit"
                }
            )
        else:
            raise HTTPException(status_code=404, detail=f"Custom template not found: {custom_template_path}")

    @router.get("/{app_name}/{flow_identifier}", response_class=HTMLResponse, tags=["applications"])
    async def get_flow_console_page_simplified(
            request: Request,
            app_name: str,
            flow_identifier: str,
            app_manager: AppManager = Depends(app_manager_dependency),
            db_manager: DatabaseManager = Depends(db_manager_dependency),
            config=Depends(config_dependency)
    ):
        """Get flow-specific console page using flow_name, flow_id, or flow_id-version."""
        # Validate app exists (flexible matching)
        app = get_app_by_name_flexible(app_name, app_manager)
        if not app:
            raise HTTPException(status_code=404, detail="Application not found")

        # Parse flow identifier
        flow_name, flow_config, flow_id, version = parse_flow_identifier(app, flow_identifier)

        if not flow_config:
            raise HTTPException(status_code=404,
                                detail=f"Flow '{flow_identifier}' not found in application '{app_name}'")

        # Get configuration for apps directory
        config = get_config()
        # Use config to get apps directory path for consistency
        apps_dir = config.get_apps_directory_path()

        # Ensure the path is properly resolved and doesn't contain environment variable placeholders
        from ..config.loader import EnvironmentVariableExpander
        from pathlib import Path
        apps_dir_str = str(apps_dir)
        apps_dir_expanded = EnvironmentVariableExpander.expand_value(apps_dir_str)

        # Get project root directory - use cross-platform path handling
        project_root = normalize_path(Path.cwd())  # Use current working directory as project root
        if Path(apps_dir_expanded).is_absolute():
            # Absolute path
            apps_dir = normalize_path(apps_dir_expanded)
        else:
            # Relative path
            apps_dir = normalize_path(project_root / apps_dir_expanded)

        # Create flow context for template - use cross-platform paths
        flow_context = {
            "flow_path": str(normalize_path(apps_dir / app_name / flow_name)),
            "templates_path": str(normalize_path(apps_dir / app_name / "templates")),
            "scripts_path": str(normalize_path(apps_dir / app_name / "scripts"))
        }

        # Get recent runs for this flow
        runs = []
        try:
            all_runs = db_manager.list_runs()
            # Filter runs by flow_id
            runs = [run for run in all_runs if hasattr(run, 'flow_id') and run.flow_id == flow_id]
            # Sort by created_at descending, limit to 10 most recent
            runs = sorted(runs, key=lambda r: getattr(r, 'created_at', ''), reverse=True)[:10]
        except Exception as e:
            logger.warning(f"Failed to get runs for {flow_id}: {e}")

        # Get latest flow version for submit URL
        if not flow_id:
            flow_id = getattr(flow_config, "flow_id", flow_identifier)

        _, flow_version = get_flow_version_by_id_and_version(flow_id, db_manager=db_manager)
        version_id = flow_version["version"] if flow_version else "latest"

        # Initialize templates with config-based directory - use cross-platform paths
        templates_dir = normalize_path(Path(__file__).parent.parent / "templates")
        templates = Jinja2Templates(directory=str(templates_dir))

        return templates.TemplateResponse(
            "flow_console.html",
            {
                "request": request,
                "app_id": app.app_id,
                "app_name": app.app_id,
                "flow_id": flow_id,
                "flow_name": flow_name,
                "app_config": app,
                "flow_config": flow_config,
                "flow_context": flow_context,
                "flow_title": getattr(flow_config, "title", flow_name),
                "flow_description": getattr(flow_config, "description", ""),
                "title": f"{app.console_title} - {getattr(flow_config, 'title', flow_name)}",
                "subtitle": getattr(flow_config, "description", f"Flow: {flow_id}"),
                "runs": runs,
                "extensions": app.extensions,
                "api_base": f"/{app.app_id}/{flow_id}",
                "submit_url": f"/api/flows/{flow_id}-{version_id}/submit"
            }
        )

    # New API routes based on flow_id-version format
    @router.post("/api/flows/{flow_version_param}/submit", tags=["flows"])
    async def submit_flow_form(
            request: Request,
            flow_version_param: str,
            app_manager: AppManager = Depends(app_manager_dependency),
            db_manager: DatabaseManager = Depends(db_manager_dependency),
            control: WorkflowControl = Depends(workflow_control_dependency)
    ):
        """Submit form data: validate and create a pending run, then redirect to console without starting execution."""
        flow_id, version = parse_flow_version_id(flow_version_param)

        # Validate flow exists and get version
        flow, flow_version = get_flow_version_by_id_and_version(flow_id, version, db_manager)
        if not flow or not flow_version:
            raise HTTPException(status_code=404, detail=f"Flow '{flow_id}' version '{version or 'latest'}' not found")

        try:
            # Parse form data
            form_data = await request.form()
            form_dict = {}

            # Get configuration for file upload directory - use environment variable or default
            config = get_config()
            upload_dir = normalize_path(config.get_upload_directory_path())
            upload_dir.mkdir(parents=True, exist_ok=True)

            for key, value in form_data.items():
                if hasattr(value, "filename"):  # File upload
                    if value.filename:
                        import uuid
                        from pathlib import Path

                        file_extension = Path(value.filename).suffix
                        unique_filename = f"{uuid.uuid4()}{file_extension}"
                        file_path = normalize_path(upload_dir / unique_filename)

                        file_content = await value.read()
                        with open(file_path, "wb") as f:
                            f.write(file_content)

                        form_dict[key] = {
                            "filename": value.filename,
                            "content_type": value.content_type,
                            "size": len(file_content),
                            "file_path": str(file_path),
                        }

                        logger.info(f"Saved uploaded file: {value.filename} -> {file_path}")
                    else:
                        form_dict[key] = None
                else:
                    form_dict[key] = value

            # Create a pending run (do not start execution here)
            import uuid as _uuid
            pending_thread_id = f"thr_{_uuid.uuid4().hex[:16]}"
            db_manager.create_run(
                thread_id=pending_thread_id,
                flow_version_id=flow_version["flow_version_id"],
                status="pending",
                metadata={"inputs": form_dict},
            )

            logger.info(
                f"Form submitted for {flow_id}-{version}: {list(form_dict.keys())}; pending thread: {pending_thread_id}")

            # Find app_name and flow_name for redirect (reverse lookup)
            app_name = None
            flow_name = None
            for app in app_manager.list_apps():
                for fname, fconfig in app.flows.items():
                    if getattr(fconfig, "flow_id", None) == flow_id:
                        app_name = app.app_id
                        flow_name = fname
                        break
                if app_name:
                    break

            # Encode form data for URL transmission
            import urllib.parse
            import json
            form_data_json = json.dumps(form_dict)
            form_data_encoded = urllib.parse.quote(form_data_json)

            if not app_name or not flow_name:
                redirect_url = f"/console?id={flow_id}&tab=logs&thread_id={pending_thread_id}&form_data=submitted&form_values={form_data_encoded}"
            else:
                redirect_url = f"/{app_name}/{flow_name}?tab=logs&thread_id={pending_thread_id}&form_data=submitted&form_values={form_data_encoded}"

            return RedirectResponse(url=redirect_url, status_code=302)

        except Exception as e:
            logger.error(f"Failed to submit form for {flow_id}-{version}: {e}")
            raise HTTPException(status_code=500, detail=f"Form submission failed: {str(e)}")

    return router
