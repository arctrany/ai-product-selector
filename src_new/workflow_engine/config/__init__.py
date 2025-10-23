"""Configuration management for workflow engine."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ServerConfig:
    """Server configuration."""
    host: str = "0.0.0.0"
    port: int = 8888
    title: str = "Workflow Engine API"
    description: str = "轻量级本地工作流引擎 API"
    version: str = "1.0.0"


@dataclass
class AppsConfig:
    """Applications configuration."""
    directory: str = "src_new/apps"
    auto_reload: bool = True


@dataclass
class DatabaseConfig:
    """Database configuration."""
    path: str = "~/.ren/workflow.db"


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    directory: str = "~/.ren/runs"


@dataclass
class TemplatesConfig:
    """Templates configuration."""
    directory: str = "templates"


@dataclass
class DevelopmentConfig:
    """Development configuration."""
    debug: bool = False
    reload: bool = False


@dataclass
class WorkflowEngineConfig:
    """Complete workflow engine configuration."""
    server: ServerConfig
    apps: AppsConfig
    database: DatabaseConfig
    logging: LoggingConfig
    templates: TemplatesConfig
    development: DevelopmentConfig

    def get_apps_directory_path(self, project_root: Optional[Path] = None) -> Path:
        """Get absolute path to apps directory."""
        if project_root is None:
            # Try to find project root by looking for src_new directory
            current = Path(__file__).parent
            while current.parent != current:
                if (current / "src_new").exists():
                    project_root = current
                    break
                current = current.parent
            else:
                # Fallback to current working directory
                project_root = Path.cwd()

        apps_path = Path(self.apps.directory)
        if apps_path.is_absolute():
            return apps_path
        else:
            return project_root / apps_path

    def get_database_path(self) -> Path:
        """Get absolute path to database file."""
        db_path = Path(self.database.path).expanduser()
        return db_path

    def get_logging_directory_path(self) -> Path:
        """Get absolute path to logging directory."""
        log_path = Path(self.logging.directory).expanduser()
        return log_path

    def get_templates_directory_path(self) -> Path:
        """Get absolute path to templates directory."""
        templates_path = Path(self.templates.directory)
        if templates_path.is_absolute():
            return templates_path
        else:
            # Relative to workflow_engine package
            package_root = Path(__file__).parent.parent
            return package_root / templates_path


def load_config(config_path: Optional[str] = None) -> WorkflowEngineConfig:
    """Load configuration from YAML file."""
    if config_path is None:
        # Default config path
        config_path = Path(__file__).parent / "server.yml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        # Return default configuration if file doesn't exist
        return WorkflowEngineConfig(
            server=ServerConfig(),
            apps=AppsConfig(),
            database=DatabaseConfig(),
            logging=LoggingConfig(),
            templates=TemplatesConfig(),
            development=DevelopmentConfig()
        )

    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)

    # Parse configuration sections
    server_config = ServerConfig(**config_data.get('server', {}))
    apps_config = AppsConfig(**config_data.get('apps', {}))
    database_config = DatabaseConfig(**config_data.get('database', {}))
    logging_config = LoggingConfig(**config_data.get('logging', {}))
    templates_config = TemplatesConfig(**config_data.get('templates', {}))
    development_config = DevelopmentConfig(**config_data.get('development', {}))

    return WorkflowEngineConfig(
        server=server_config,
        apps=apps_config,
        database=database_config,
        logging=logging_config,
        templates=templates_config,
        development=development_config
    )


# Global configuration instance
_config: Optional[WorkflowEngineConfig] = None


def get_config() -> WorkflowEngineConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config(config_path: Optional[str] = None) -> WorkflowEngineConfig:
    """Reload configuration from file."""
    global _config
    _config = load_config(config_path)
    return _config
