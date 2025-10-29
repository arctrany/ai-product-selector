"""Bootstrap module for workflow engine environment setup.

This module provides a way to setup the environment before importing
other workflow engine modules, solving the circular import problem.
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Optional, Dict, Any


def _find_config_file() -> Optional[Path]:
    """Find server.yml configuration file."""
    current_path = Path(__file__).resolve()

    # Start from current file and go up the directory tree
    for parent in current_path.parents:
        # Look for config in workflow_engine/config/server.yml
        for config_dir in ["config", "workflow_engine/config"]:
            config_file = parent / config_dir / "server.yml"
            if config_file.exists():
                return config_file

        # Also check if there's a server.yml directly in any parent
        config_file = parent / "server.yml"
        if config_file.exists():
            return config_file

    return None


def _load_config() -> Dict[str, Any]:
    """Load configuration from server.yml."""
    config_file = _find_config_file()
    if not config_file:
        return {}

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _find_project_root() -> str:
    """Find project root by looking for server.yml configuration file."""
    config_file = _find_config_file()
    if config_file:
        # Try to get project root from config
        config = _load_config()
        project_config = config.get("project", {})

        # If root is specified in config, use it
        if project_config.get("root"):
            return str(Path(project_config["root"]).resolve())

        # Otherwise, infer from config file location
        config_parent = config_file.parent
        source_dir = project_config.get("source_dir", "src_new")

        # If config is in workflow_engine/config/, go up to find source dir
        while config_parent.name != source_dir and config_parent.parent != config_parent:
            config_parent = config_parent.parent

        if config_parent.name == source_dir:
            return str(config_parent.parent)

        # Fallback: assume config is in project root
        return str(config_file.parent)

    # Last resort: use relative path from current file
    fallback_root = Path(__file__).resolve().parents[4]
    return str(fallback_root)


def setup_environment() -> None:
    """Setup the workflow engine environment.
    
    This function should be called at the beginning of workflow definition files
    to ensure proper Python import paths are configured.
    """
    project_root = _find_project_root()
    config = _load_config()
    project_config = config.get("project", {})
    source_dir = project_config.get("source_dir", "src_new")

    source_path = os.path.join(project_root, source_dir)
    apps_path = os.path.join(project_root, "apps")

    # Add project root to Python path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Add source directory to Python path
    if source_path not in sys.path:
        sys.path.insert(0, source_path)

    # Add apps directory to Python path to enable direct import of app modules
    if apps_path not in sys.path:
        sys.path.insert(0, apps_path)


def get_project_root() -> str:
    """Get the project root directory."""
    return _find_project_root()