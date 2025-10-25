"""Configuration management for workflow engine with dependency injection support."""

import os
import threading
from typing import Any, Dict, Optional, Type, TypeVar, Callable
from dataclasses import dataclass, field
from pathlib import Path

T = TypeVar('T')

@dataclass
class WorkflowEngineConfig:
    """Configuration class for workflow engine."""
    
    # Database configuration
    db_path: Optional[str] = None
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_echo: bool = False
    
    # Performance configuration
    thread_pool_workers: int = 4
    batch_size: int = 100
    query_timeout: int = 30
    
    # Checkpoint configuration
    checkpoint_enabled: bool = True
    checkpoint_db_path: Optional[str] = None
    
    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Security configuration
    validate_inputs: bool = True
    max_workflow_depth: int = 100
    max_execution_time: int = 3600  # seconds
    
    # Feature flags
    enable_async_operations: bool = True
    enable_batch_operations: bool = True
    enable_metrics: bool = True
    
    def __post_init__(self):
        """Initialize default paths if not provided."""
        if self.db_path is None:
            db_dir = Path.home() / ".ren"
            db_dir.mkdir(exist_ok=True)
            self.db_path = str(db_dir / "workflow.db")
        
        if self.checkpoint_db_path is None and self.checkpoint_enabled:
            self.checkpoint_db_path = self.db_path.replace('.db', '_checkpoints.db')

class DependencyContainer:
    """Thread-safe dependency injection container."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._singletons: Dict[str, Any] = {}
        self._lock = threading.RLock()
    
    def register_singleton(self, service_type: Type[T], instance: T) -> None:
        """Register a singleton instance."""
        with self._lock:
            key = self._get_key(service_type)
            self._singletons[key] = instance
    
    def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """Register a factory function for creating instances."""
        with self._lock:
            key = self._get_key(service_type)
            self._factories[key] = factory
    
    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """Register a specific instance (not singleton)."""
        with self._lock:
            key = self._get_key(service_type)
            self._services[key] = instance
    
    def get(self, service_type: Type[T]) -> T:
        """Get an instance of the requested service type."""
        with self._lock:
            key = self._get_key(service_type)
            
            # Check singletons first
            if key in self._singletons:
                return self._singletons[key]
            
            # Check registered instances
            if key in self._services:
                return self._services[key]
            
            # Check factories
            if key in self._factories:
                return self._factories[key]()
            
            raise ValueError(f"Service {service_type.__name__} not registered")
    
    def has(self, service_type: Type[T]) -> bool:
        """Check if a service type is registered."""
        with self._lock:
            key = self._get_key(service_type)
            return key in self._singletons or key in self._services or key in self._factories
    
    def clear(self) -> None:
        """Clear all registered services."""
        with self._lock:
            self._services.clear()
            self._factories.clear()
            self._singletons.clear()
    
    def _get_key(self, service_type: Type) -> str:
        """Get a string key for the service type."""
        return f"{service_type.__module__}.{service_type.__name__}"

class ConfigManager:
    """Thread-safe configuration manager."""
    
    _instance: Optional['ConfigManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'ConfigManager':
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._config: Optional[WorkflowEngineConfig] = None
            self._container = DependencyContainer()
            self._lock = threading.RLock()
            self._initialized = True
    
    def set_config(self, config: WorkflowEngineConfig) -> None:
        """Set the global configuration."""
        with self._lock:
            self._config = config
    
    def get_config(self) -> WorkflowEngineConfig:
        """Get the global configuration."""
        with self._lock:
            if self._config is None:
                self._config = WorkflowEngineConfig()
            return self._config
    
    def get_container(self) -> DependencyContainer:
        """Get the dependency injection container."""
        return self._container
    
    def load_from_env(self) -> WorkflowEngineConfig:
        """Load configuration from environment variables."""
        config = WorkflowEngineConfig()
        
        # Database configuration
        if db_path := os.getenv('WORKFLOW_DB_PATH'):
            config.db_path = db_path
        
        if db_pool_size := os.getenv('WORKFLOW_DB_POOL_SIZE'):
            config.db_pool_size = int(db_pool_size)
        
        if db_echo := os.getenv('WORKFLOW_DB_ECHO'):
            config.db_echo = db_echo.lower() in ('true', '1', 'yes')
        
        # Performance configuration
        if thread_workers := os.getenv('WORKFLOW_THREAD_WORKERS'):
            config.thread_pool_workers = int(thread_workers)
        
        if batch_size := os.getenv('WORKFLOW_BATCH_SIZE'):
            config.batch_size = int(batch_size)
        
        # Checkpoint configuration
        if checkpoint_enabled := os.getenv('WORKFLOW_CHECKPOINT_ENABLED'):
            config.checkpoint_enabled = checkpoint_enabled.lower() in ('true', '1', 'yes')
        
        if checkpoint_db_path := os.getenv('WORKFLOW_CHECKPOINT_DB_PATH'):
            config.checkpoint_db_path = checkpoint_db_path
        
        # Logging configuration
        if log_level := os.getenv('WORKFLOW_LOG_LEVEL'):
            config.log_level = log_level.upper()
        
        # Security configuration
        if validate_inputs := os.getenv('WORKFLOW_VALIDATE_INPUTS'):
            config.validate_inputs = validate_inputs.lower() in ('true', '1', 'yes')
        
        if max_workflow_depth := os.getenv('WORKFLOW_MAX_DEPTH'):
            config.max_workflow_depth = int(max_workflow_depth)
        
        if max_execution_time := os.getenv('WORKFLOW_MAX_EXECUTION_TIME'):
            config.max_execution_time = int(max_execution_time)
        
        # Feature flags
        if enable_async := os.getenv('WORKFLOW_ENABLE_ASYNC'):
            config.enable_async_operations = enable_async.lower() in ('true', '1', 'yes')
        
        if enable_batch := os.getenv('WORKFLOW_ENABLE_BATCH'):
            config.enable_batch_operations = enable_batch.lower() in ('true', '1', 'yes')
        
        if enable_metrics := os.getenv('WORKFLOW_ENABLE_METRICS'):
            config.enable_metrics = enable_metrics.lower() in ('true', '1', 'yes')
        
        self.set_config(config)
        return config

# Global configuration manager instance
_config_manager = ConfigManager()

def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    return _config_manager

def get_config() -> WorkflowEngineConfig:
    """Get the global configuration."""
    return _config_manager.get_config()

def get_container() -> DependencyContainer:
    """Get the global dependency injection container."""
    return _config_manager.get_container()