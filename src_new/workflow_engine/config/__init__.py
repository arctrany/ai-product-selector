"""Configuration management for workflow engine."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Import cross-platform configuration loader
from .loader import (
    CrossPlatformConfigLoader,
    load_cross_platform_config,
    expand_environment_variables,
    get_platform_data_dir,
    get_platform_cache_dir,
    get_platform_temp_dir
)


@dataclass
class ServerConfig:
    """Server configuration."""
    host: str = "localhost"
    port: int = 8888
    title: str = "Ren Engine"
    description: str = "Ren引擎"
    version: str = "1.0.0"


@dataclass
class AppsConfig:
    """Applications configuration."""
    directory: str = "apps"
    auto_reload: bool = True


@dataclass
class DatabaseConfig:
    """Database configuration."""
    path: str = ""  # Empty string will use platform-specific default


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    directory: str = ""  # Empty string will use platform-specific default
    console_output: bool = True  # Enable console output by default
    console_format: str = "detailed"  # Console log format

@dataclass
class DataDirsConfig:
    """Data directories configuration."""
    base: str = ""  # Base data directory
    cache: str = ""  # Cache directory
    temp: str = ""  # Temporary directory
    upload: str = ""  # Upload directory
    logs: str = ""  # Logs directory


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
    data_dirs: DataDirsConfig

    def get_apps_directory_path(self, project_root: Optional[Path] = None) -> Path:
        """Get absolute path to apps directory."""
        if project_root is None:
            # Use cross-platform loader to get project root
            from .loader import CrossPlatformConfigLoader
            loader = CrossPlatformConfigLoader()
            project_root = loader.get_project_root({})

        apps_path = Path(self.apps.directory)
        if apps_path.is_absolute():
            return apps_path
        else:
            return project_root / apps_path

    def get_database_path(self) -> Path:
        """Get absolute path to database file."""
        if not self.database.path:
            # Use platform-specific default
            from .loader import get_platform_data_dir
            data_dir = get_platform_data_dir()
            return data_dir / "workflow.db"

        db_path = Path(self.database.path)
        if db_path.is_absolute():
            return db_path
        else:
            # Expand user path for cross-platform compatibility
            return db_path.expanduser()

    def get_logging_directory_path(self) -> Path:
        """Get absolute path to logging directory."""
        # First check data_dirs.logs, then logging.directory, then default
        log_dir = self.data_dirs.logs or self.logging.directory

        if not log_dir:
            # Use platform-specific default
            from .loader import get_platform_data_dir
            data_dir = get_platform_data_dir()
            return data_dir / "logs"

        log_path = Path(log_dir)
        if log_path.is_absolute():
            return log_path
        else:
            # Expand user path for cross-platform compatibility
            return log_path.expanduser()

    def get_upload_directory_path(self) -> Path:
        """Get absolute path to upload directory."""
        upload_dir = self.data_dirs.upload

        if not upload_dir:
            # Use platform-specific default
            from .loader import get_platform_data_dir
            data_dir = get_platform_data_dir()
            return data_dir / "uploads"

        upload_path = Path(upload_dir)
        if upload_path.is_absolute():
            return upload_path
        else:
            # Expand user path for cross-platform compatibility
            return upload_path.expanduser()

    def get_cache_directory_path(self) -> Path:
        """Get absolute path to cache directory."""
        cache_dir = self.data_dirs.cache

        if not cache_dir:
            # Use platform-specific default
            from .loader import get_platform_cache_dir
            return get_platform_cache_dir()

        cache_path = Path(cache_dir)
        if cache_path.is_absolute():
            return cache_path
        else:
            # Expand user path for cross-platform compatibility
            return cache_path.expanduser()

    def get_temp_directory_path(self) -> Path:
        """Get absolute path to temporary directory."""
        temp_dir = self.data_dirs.temp

        if not temp_dir:
            # Use platform-specific default
            from .loader import get_platform_temp_dir
            return get_platform_temp_dir()

        temp_path = Path(temp_dir)
        if temp_path.is_absolute():
            return temp_path
        else:
            # Expand user path for cross-platform compatibility
            return temp_path.expanduser()

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
            development=DevelopmentConfig(),
            data_dirs=DataDirsConfig()
        )

    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)

    # Parse configuration sections with safe handling of unknown fields
    server_data = config_data.get('server', {})
    apps_data = config_data.get('apps', {})
    database_data = config_data.get('database', {})
    logging_data = config_data.get('logging', {})
    templates_data = config_data.get('templates', {})
    development_data = config_data.get('development', {})
    data_dirs_data = config_data.get('data_dirs', {})

    # Filter out unknown fields to prevent TypeError
    def filter_known_fields(data_dict, dataclass_type):
        """Filter out fields that are not defined in the dataclass."""
        if not data_dict:
            return {}

        # Get field names from dataclass
        import dataclasses
        field_names = {field.name for field in dataclasses.fields(dataclass_type)}

        # Filter data to only include known fields
        return {k: v for k, v in data_dict.items() if k in field_names}

    server_config = ServerConfig(**filter_known_fields(server_data, ServerConfig))
    apps_config = AppsConfig(**filter_known_fields(apps_data, AppsConfig))
    database_config = DatabaseConfig(**filter_known_fields(database_data, DatabaseConfig))
    logging_config = LoggingConfig(**filter_known_fields(logging_data, LoggingConfig))
    templates_config = TemplatesConfig(**filter_known_fields(templates_data, TemplatesConfig))
    development_config = DevelopmentConfig(**filter_known_fields(development_data, DevelopmentConfig))
    data_dirs_config = DataDirsConfig(**filter_known_fields(data_dirs_data, DataDirsConfig))

    return WorkflowEngineConfig(
        server=server_config,
        apps=apps_config,
        database=database_config,
        logging=logging_config,
        templates=templates_config,
        development=development_config,
        data_dirs=data_dirs_config
    )


# Global configuration instance
_config: Optional[WorkflowEngineConfig] = None


def get_config() -> WorkflowEngineConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = load_cross_platform_workflow_config()
    return _config


def reload_config(config_path: Optional[str] = None) -> WorkflowEngineConfig:
    """Reload configuration from file."""
    global _config
    _config = load_config(config_path)
    return _config


def load_cross_platform_workflow_config(config_path: Optional[str] = None) -> WorkflowEngineConfig:
    """Load workflow configuration with cross-platform support and environment variable expansion."""
    # Load configuration using cross-platform loader
    raw_config = load_cross_platform_config(config_path)

    # Parse configuration sections with safe handling of unknown fields
    server_data = raw_config.get('server', {})
    apps_data = raw_config.get('apps', {})
    database_data = raw_config.get('database', {})
    logging_data = raw_config.get('logging', {})
    templates_data = raw_config.get('templates', {})
    development_data = raw_config.get('development', {})
    data_dirs_data = raw_config.get('data_dirs', {})

    # Filter out unknown fields to prevent TypeError
    def filter_known_fields(data_dict, dataclass_type):
        """Filter out fields that are not defined in the dataclass."""
        if not data_dict:
            return {}

        # Get field names from dataclass
        import dataclasses
        field_names = {field.name for field in dataclasses.fields(dataclass_type)}

        # Filter data to only include known fields
        return {k: v for k, v in data_dict.items() if k in field_names}

    # Convert to WorkflowEngineConfig objects
    server_config = ServerConfig(**filter_known_fields(server_data, ServerConfig))
    apps_config = AppsConfig(**filter_known_fields(apps_data, AppsConfig))
    database_config = DatabaseConfig(**filter_known_fields(database_data, DatabaseConfig))
    logging_config = LoggingConfig(**filter_known_fields(logging_data, LoggingConfig))
    templates_config = TemplatesConfig(**filter_known_fields(templates_data, TemplatesConfig))
    development_config = DevelopmentConfig(**filter_known_fields(development_data, DevelopmentConfig))
    data_dirs_config = DataDirsConfig(**filter_known_fields(data_dirs_data, DataDirsConfig))

    return WorkflowEngineConfig(
        server=server_config,
        apps=apps_config,
        database=database_config,
        logging=logging_config,
        templates=templates_config,
        development=development_config,
        data_dirs=data_dirs_config
    )


def get_cross_platform_config() -> WorkflowEngineConfig:
    """Get global cross-platform configuration instance."""
    global _config
    if _config is None:
        _config = load_cross_platform_workflow_config()
    return _config


# Export cross-platform functions
__all__ = [
    'ServerConfig',
    'AppsConfig',
    'DatabaseConfig',
    'LoggingConfig',
    'TemplatesConfig',
    'DevelopmentConfig',
    'WorkflowEngineConfig',
    'load_config',
    'get_config',
    'reload_config',
    'load_cross_platform_workflow_config',
    'get_cross_platform_config',
    'CrossPlatformConfigLoader',
    'load_cross_platform_config',
    'expand_environment_variables',
    'get_platform_data_dir',
    'get_platform_cache_dir',
    'get_platform_temp_dir'
]
