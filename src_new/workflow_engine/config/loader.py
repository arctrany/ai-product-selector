"""Cross-platform configuration loader with environment variable support."""

import os
import re
import yaml
import platform
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass


@dataclass
class PlatformPaths:
    """Platform-specific directory paths."""
    
    @staticmethod
    def get_user_data_dir(app_name: str = "workflow_engine") -> Path:
        """Get platform-specific user data directory."""
        system = platform.system().lower()
        
        if system == "windows":
            # Windows: %APPDATA%/app_name
            base_dir = os.getenv("APPDATA", str(Path.home() / "AppData" / "Roaming"))
            return Path(base_dir) / app_name
        elif system == "darwin":
            # macOS: ~/Library/Application Support/app_name
            return Path.home() / "Library" / "Application Support" / app_name
        else:
            # Linux/Unix: ~/.local/share/app_name
            base_dir = os.getenv("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
            return Path(base_dir) / app_name
    
    @staticmethod
    def get_user_cache_dir(app_name: str = "workflow_engine") -> Path:
        """Get platform-specific user cache directory."""
        system = platform.system().lower()
        
        if system == "windows":
            # Windows: %LOCALAPPDATA%/app_name/cache
            base_dir = os.getenv("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
            return Path(base_dir) / app_name / "cache"
        elif system == "darwin":
            # macOS: ~/Library/Caches/app_name
            return Path.home() / "Library" / "Caches" / app_name
        else:
            # Linux/Unix: ~/.cache/app_name
            base_dir = os.getenv("XDG_CACHE_HOME", str(Path.home() / ".cache"))
            return Path(base_dir) / app_name
    
    @staticmethod
    def get_temp_dir(app_name: str = "workflow_engine") -> Path:
        """Get platform-specific temporary directory."""
        import tempfile
        return Path(tempfile.gettempdir()) / app_name


class EnvironmentVariableExpander:
    """Handles environment variable expansion in configuration values."""
    
    # Pattern to match ${VAR_NAME:default_value} or ${VAR_NAME}
    ENV_VAR_PATTERN = re.compile(r'\$\{([^}:]+)(?::([^}]*))?\}')
    
    @classmethod
    def expand_value(cls, value: Any) -> Any:
        """Expand environment variables in a configuration value."""
        if isinstance(value, str):
            return cls._expand_string(value)
        elif isinstance(value, dict):
            return {k: cls.expand_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [cls.expand_value(item) for item in value]
        else:
            return value
    
    @classmethod
    def _expand_string(cls, text: str) -> str:
        """Expand environment variables in a string."""
        def replace_env_var(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ""
            
            # Get environment variable value
            env_value = os.getenv(var_name)
            
            if env_value is not None:
                return env_value
            else:
                return default_value
        
        return cls.ENV_VAR_PATTERN.sub(replace_env_var, text)


class CrossPlatformConfigLoader:
    """Cross-platform configuration loader with environment variable support."""
    
    def __init__(self, app_name: str = "workflow_engine"):
        self.app_name = app_name
        self.platform_paths = PlatformPaths()
        self.env_expander = EnvironmentVariableExpander()
    
    def load_config(self, config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """Load and process configuration from YAML file."""
        # Load raw configuration
        raw_config = self._load_raw_config(config_path)
        
        # Expand environment variables
        expanded_config = self.env_expander.expand_value(raw_config)
        
        # Resolve platform-specific paths
        resolved_config = self._resolve_platform_paths(expanded_config)
        
        return resolved_config
    
    def _load_raw_config(self, config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """Load raw configuration from YAML file."""
        if config_path is None:
            # Default config path
            config_path = Path(__file__).parent / "server.yml"
        else:
            config_path = Path(config_path)
        
        if not config_path.exists():
            # Return empty configuration if file doesn't exist
            return {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
                return config_data
        except Exception as e:
            print(f"Warning: Failed to load {config_path}: {e}")
            return {}
    
    def _resolve_platform_paths(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve platform-specific paths in configuration."""
        resolved_config = config.copy()
        
        # Resolve database path
        if "database" in resolved_config and "path" in resolved_config["database"]:
            db_path = resolved_config["database"]["path"]
            if not db_path:  # Empty path, use default
                data_dir = self.platform_paths.get_user_data_dir(self.app_name)
                resolved_config["database"]["path"] = str(data_dir / "workflow.db")
        
        # Resolve logging directory
        if "logging" in resolved_config and "directory" in resolved_config["logging"]:
            log_dir = resolved_config["logging"]["directory"]
            if not log_dir:  # Empty directory, use default
                data_dir = self.platform_paths.get_user_data_dir(self.app_name)
                resolved_config["logging"]["directory"] = str(data_dir / "logs")
        
        # Resolve data directories
        if "data_dirs" in resolved_config:
            data_dirs = resolved_config["data_dirs"]
            
            if "base" in data_dirs and not data_dirs["base"]:
                data_dirs["base"] = str(self.platform_paths.get_user_data_dir(self.app_name))
            
            if "cache" in data_dirs and not data_dirs["cache"]:
                data_dirs["cache"] = str(self.platform_paths.get_user_cache_dir(self.app_name))
            
            if "temp" in data_dirs and not data_dirs["temp"]:
                data_dirs["temp"] = str(self.platform_paths.get_temp_dir(self.app_name))
        
        # Ensure directories exist
        self._ensure_directories_exist(resolved_config)
        
        return resolved_config
    
    def _ensure_directories_exist(self, config: Dict[str, Any]) -> None:
        """Ensure required directories exist."""
        directories_to_create = []
        
        # Database directory
        if "database" in config and "path" in config["database"]:
            db_path = Path(config["database"]["path"])
            directories_to_create.append(db_path.parent)
        
        # Logging directory
        if "logging" in config and "directory" in config["logging"]:
            log_dir = Path(config["logging"]["directory"])
            directories_to_create.append(log_dir)
        
        # Data directories
        if "data_dirs" in config:
            data_dirs = config["data_dirs"]
            for dir_key in ["base", "cache", "temp"]:
                if dir_key in data_dirs:
                    directories_to_create.append(Path(data_dirs[dir_key]))
        
        # Create directories
        for directory in directories_to_create:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"Warning: Failed to create directory {directory}: {e}")
    
    def get_project_root(self, config: Dict[str, Any]) -> Path:
        """Get project root directory."""
        if "project" in config and "root" in config["project"] and config["project"]["root"]:
            return Path(config["project"]["root"]).resolve()
        
        # Auto-detect project root by looking for src_new directory
        current = Path(__file__).parent
        while current.parent != current:
            if (current / "src_new").exists():
                return current
            current = current.parent
        
        # Fallback to current working directory
        return Path.cwd()
    
    def resolve_relative_path(self, path: str, base_path: Path) -> Path:
        """Resolve relative path against base path."""
        path_obj = Path(path)
        if path_obj.is_absolute():
            return path_obj
        else:
            return base_path / path_obj


# Convenience functions for backward compatibility
def load_cross_platform_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Load cross-platform configuration."""
    loader = CrossPlatformConfigLoader()
    return loader.load_config(config_path)


def expand_environment_variables(config: Dict[str, Any]) -> Dict[str, Any]:
    """Expand environment variables in configuration."""
    expander = EnvironmentVariableExpander()
    return expander.expand_value(config)


def get_platform_data_dir(app_name: str = "workflow_engine") -> Path:
    """Get platform-specific user data directory."""
    return PlatformPaths.get_user_data_dir(app_name)


def get_platform_cache_dir(app_name: str = "workflow_engine") -> Path:
    """Get platform-specific user cache directory."""
    return PlatformPaths.get_user_cache_dir(app_name)


def get_platform_temp_dir(app_name: str = "workflow_engine") -> Path:
    """Get platform-specific temporary directory."""
    return PlatformPaths.get_temp_dir(app_name)