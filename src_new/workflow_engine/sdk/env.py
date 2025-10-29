"""Environment configuration module for workflow engine SDK.

This module provides utilities to configure the Python environment
by reading configuration from various sources and setting up proper import paths.
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class EnvironmentConfig:
    """Configuration for the workflow environment."""

    # Path configuration
    config_filename: str = "server.yml"
    source_directory: str = "src_new"
    apps_directory: str = "apps"
    config_directories: List[str] = field(default_factory=lambda: ["config", "workflow_engine/config", "."])

    # Database configuration
    default_database_path: str = "~/.ren/workflow.db"

    # Server configuration
    default_server_host: str = "0.0.0.0"
    default_server_port: int = 8889
    default_server_title: str = "Workflow Engine API"

    # Environment variables
    project_root_env_var: str = "WORKFLOW_PROJECT_ROOT"
    config_path_env_var: str = "WORKFLOW_CONFIG_PATH"
    apps_dir_env_var: str = "WORKFLOW_APPS_DIR"


class WorkflowEnvironment:
    """Manages workflow engine environment configuration."""

    _instance: Optional['WorkflowEnvironment'] = None
    _initialized: bool = False

    def __new__(cls, config: Optional[EnvironmentConfig] = None) -> 'WorkflowEnvironment':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[EnvironmentConfig] = None):
        if not self._initialized:
            self._env_config = config or EnvironmentConfig()
            self._config: Optional[Dict[str, Any]] = None
            self._project_root: Optional[str] = None
            self._config_file_path: Optional[Path] = None
            self._initialized = True

    def _find_config_file(self) -> Optional[Path]:
        """Find configuration file using multiple strategies."""
        if self._config_file_path is not None:
            return self._config_file_path

        # Strategy 1: Check environment variable
        env_config_path = os.getenv(self._env_config.config_path_env_var)
        if env_config_path:
            config_path = Path(env_config_path)
            if config_path.exists():
                self._config_file_path = config_path
                return self._config_file_path

        # Strategy 2: Search from current file location
        current_path = Path(__file__).resolve()

        for parent in current_path.parents:
            for config_dir in self._env_config.config_directories:
                config_file = parent / config_dir / self._env_config.config_filename
                if config_file.exists():
                    self._config_file_path = config_file
                    return self._config_file_path

        # Strategy 3: Look for config file in common locations
        common_locations = [
            Path.cwd() / self._env_config.config_filename,
            Path.home() / f".{self._env_config.config_filename}",
            Path("/etc") / self._env_config.config_filename,
        ]

        for location in common_locations:
            if location.exists():
                self._config_file_path = location
                return self._config_file_path

        return None

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or environment."""
        if self._config is not None:
            return self._config

        config = {}

        # Load from file
        config_file = self._find_config_file()
        if config_file:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f) or {}
                    config.update(file_config)
            except Exception as e:
                print(f"Warning: Failed to load {config_file}: {e}")

        # Override with environment variables
        self._apply_env_overrides(config)

        self._config = config
        return self._config

    def _apply_env_overrides(self, config: Dict[str, Any]) -> None:
        """Apply environment variable overrides to configuration."""
        # Project root override
        env_root = os.getenv(self._env_config.project_root_env_var)
        if env_root:
            config.setdefault("project", {})["root"] = env_root

        # Apps directory override
        env_apps_dir = os.getenv(self._env_config.apps_dir_env_var)
        if env_apps_dir:
            config.setdefault("apps", {})["directory"] = env_apps_dir

        # Server configuration from environment
        server_config = config.setdefault("server", {})

        if host := os.getenv("WORKFLOW_SERVER_HOST"):
            server_config["host"] = host

        if port := os.getenv("WORKFLOW_SERVER_PORT"):
            try:
                server_config["port"] = int(port)
            except ValueError:
                print(f"Warning: Invalid port value in WORKFLOW_SERVER_PORT: {port}")

        if title := os.getenv("WORKFLOW_SERVER_TITLE"):
            server_config["title"] = title

        # Database configuration from environment
        if db_path := os.getenv("WORKFLOW_DATABASE_PATH"):
            config.setdefault("database", {})["path"] = db_path

    def _find_project_root(self) -> str:
        """Find project root using multiple strategies."""
        if self._project_root is not None:
            return self._project_root

        # Strategy 1: Environment variable
        env_root = os.getenv(self._env_config.project_root_env_var)
        if env_root and Path(env_root).exists():
            self._project_root = str(Path(env_root).resolve())
            return self._project_root

        # Strategy 2: Configuration file
        config = self.get_config()
        config_root = config.get("project", {}).get("root")
        if config_root:
            root_path = Path(config_root).resolve()
            if root_path.exists():
                self._project_root = str(root_path)
                return self._project_root

        # Strategy 3: Infer from config file location
        config_file = self._find_config_file()
        if config_file:
            config_parent = config_file.parent
            source_dir = config.get("project", {}).get("source_dir", self._env_config.source_directory)

            # Navigate up to find source directory
            while config_parent.name != source_dir and config_parent.parent != config_parent:
                config_parent = config_parent.parent

            if config_parent.name == source_dir:
                self._project_root = str(config_parent.parent)
                return self._project_root

            # Fallback: use config file directory
            self._project_root = str(config_file.parent)
            return self._project_root

        # Strategy 4: Current working directory
        cwd = Path.cwd()
        if (cwd / self._env_config.source_directory).exists():
            self._project_root = str(cwd)
            return self._project_root

        # Strategy 5: Navigate up from current file
        current_path = Path(__file__).resolve()
        for parent in current_path.parents:
            if (parent / self._env_config.source_directory).exists():
                self._project_root = str(parent)
                return self._project_root

        # Last resort: current working directory
        self._project_root = str(Path.cwd())
        return self._project_root

    def get_project_root(self) -> str:
        """Get the project root directory."""
        return self._find_project_root()

    def get_config(self) -> Dict[str, Any]:
        """Get the full configuration dictionary."""
        return self._load_config()

    def get_apps_directory(self) -> str:
        """Get the applications directory path."""
        config = self.get_config()
        apps_config = config.get("apps", {})
        apps_dir = apps_config.get("directory", self._env_config.apps_directory)

        # Handle absolute vs relative paths
        if os.path.isabs(apps_dir):
            return apps_dir

        return os.path.join(self.get_project_root(), apps_dir)

    def setup_python_path(self) -> None:
        """Setup Python import paths based on project configuration."""
        project_root = self.get_project_root()
        config = self.get_config()

        # Get source directory from config
        source_dir = config.get("project", {}).get("source_dir", self._env_config.source_directory)
        source_path = os.path.join(project_root, source_dir)

        # Get apps directory path
        apps_path = self.get_apps_directory()

        # Add paths to sys.path if they exist and aren't already there
        paths_to_add = [project_root, source_path, apps_path]

        for path in paths_to_add:
            if os.path.exists(path) and path not in sys.path:
                sys.path.insert(0, path)

    def get_database_path(self) -> str:
        """Get the database file path."""
        config = self.get_config()
        db_path = config.get("database", {}).get("path", self._env_config.default_database_path)
        return os.path.expanduser(db_path)

    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration with defaults."""
        config = self.get_config()
        server_config = config.get("server", {})

        return {
            "host": server_config.get("host", self._env_config.default_server_host),
            "port": server_config.get("port", self._env_config.default_server_port),
            "title": server_config.get("title", self._env_config.default_server_title),
            **{k: v for k, v in server_config.items() if k not in ["host", "port", "title"]}
        }

    def get_logging_directory(self) -> str:
        """Get the logging directory path."""
        config = self.get_config()
        logging_config = config.get("logging", {})
        log_dir = logging_config.get("directory", "logs")

        if os.path.isabs(log_dir):
            return log_dir

        return os.path.join(self.get_project_root(), log_dir)


# Global environment instance
_env: Optional[WorkflowEnvironment] = None


def get_environment(config: Optional[EnvironmentConfig] = None) -> WorkflowEnvironment:
    """Get or create the global environment instance."""
    global _env
    if _env is None:
        _env = WorkflowEnvironment(config)
    return _env


def setup_environment(config: Optional[EnvironmentConfig] = None) -> None:
    """Setup the workflow engine environment.

    This function should be called at the beginning of workflow definition files
    to ensure proper Python import paths are configured.
    """
    env = get_environment(config)
    env.setup_python_path()


def get_project_root() -> str:
    """Get the project root directory."""
    return get_environment().get_project_root()


def get_config() -> Dict[str, Any]:
    """Get the workflow engine configuration."""
    return get_environment().get_config()


def get_apps_directory() -> str:
    """Get the applications directory path."""
    return get_environment().get_apps_directory()


def get_database_path() -> str:
    """Get the database file path."""
    return get_environment().get_database_path()


def get_server_config() -> Dict[str, Any]:
    """Get server configuration."""
    return get_environment().get_server_config()


def get_logging_directory() -> str:
    """Get the logging directory path."""
    return get_environment().get_logging_directory()
