"""Dependency injection for API routes."""

from typing import Any, Dict
from fastapi import Depends
from fastapi.templating import Jinja2Templates

from ..core.engine import WorkflowEngine
from ..apps.manager import AppManager
from ..storage.database import DatabaseManager
from ..sdk.control import WorkflowControl
from ..config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Global instances (initialized in server.py)
_engine: WorkflowEngine = None
_app_manager: AppManager = None
_templates: Jinja2Templates = None
_config = None
_workflow_control: WorkflowControl = None


def init_dependencies(engine: WorkflowEngine, app_manager: AppManager, templates: Jinja2Templates, config):
    """Initialize global dependencies."""
    global _engine, _app_manager, _templates, _config, _workflow_control
    _engine = engine
    _app_manager = app_manager
    _templates = templates
    _config = config
    # Initialize WorkflowControl with the engine's database manager
    _workflow_control = WorkflowControl(db_manager=engine.db_manager)
    logger.info("Dependencies initialized")


def get_workflow_engine() -> WorkflowEngine:
    """Get workflow engine instance."""
    if _engine is None:
        raise RuntimeError("Workflow engine not initialized")
    return _engine


def get_app_manager() -> AppManager:
    """Get app manager instance."""
    if _app_manager is None:
        raise RuntimeError("App manager not initialized")
    return _app_manager


def get_templates() -> Jinja2Templates:
    """Get templates instance."""
    if _templates is None:
        raise RuntimeError("Templates not initialized")
    return _templates


def get_app_config():
    """Get application config."""
    if _config is None:
        raise RuntimeError("Config not initialized")
    return _config


def get_database_manager() -> DatabaseManager:
    """Get database manager from workflow engine."""
    engine = get_workflow_engine()
    return engine.db_manager


def get_workflow_control() -> WorkflowControl:
    """Get workflow control instance."""
    if _workflow_control is None:
        raise RuntimeError("Workflow control not initialized")
    return _workflow_control


# Dependency functions for FastAPI
async def engine_dependency() -> WorkflowEngine:
    """FastAPI dependency for workflow engine."""
    return get_workflow_engine()


async def app_manager_dependency() -> AppManager:
    """FastAPI dependency for app manager."""
    return get_app_manager()


async def templates_dependency() -> Jinja2Templates:
    """FastAPI dependency for templates."""
    return get_templates()


async def config_dependency():
    """FastAPI dependency for config."""
    return get_app_config()


async def db_manager_dependency() -> DatabaseManager:
    """FastAPI dependency for database manager."""
    return get_database_manager()


async def workflow_control_dependency() -> WorkflowControl:
    """FastAPI dependency for workflow control."""
    return get_workflow_control()
