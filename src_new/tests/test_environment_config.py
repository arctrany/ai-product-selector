#!/usr/bin/env python3
"""
Test Environment Configuration
=============================

This module provides configuration and utilities for running tests
in different environments (development, testing, production).
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to Python path for imports
project_root = Path(__file__).resolve().parents[2]
src_path = project_root / "src_new"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

class TestEnvironment:
    """Test environment configuration and management."""
    
    def __init__(self, environment: str = "test"):
        """Initialize test environment.
        
        Args:
            environment: Environment type (test, development, integration)
        """
        self.environment = environment
        self.temp_files = []
        self.config = self._create_config()
    
    def _create_config(self) -> Dict[str, Any]:
        """Create configuration for test environment."""
        if self.environment == "test":
            return self._create_test_config()
        elif self.environment == "integration":
            return self._create_integration_config()
        elif self.environment == "performance":
            return self._create_performance_config()
        else:
            return self._create_default_config()
    
    def _create_test_config(self) -> Dict[str, Any]:
        """Create configuration for unit tests."""
        temp_db = self._create_temp_db()
        return {
            "db_path": temp_db,
            "checkpoint_enabled": False,
            "thread_pool_workers": 1,
            "batch_size": 5,
            "log_level": "WARNING",
            "timeout": 10,
            "environment": "test"
        }
    
    def _create_integration_config(self) -> Dict[str, Any]:
        """Create configuration for integration tests."""
        temp_db = self._create_temp_db()
        return {
            "db_path": temp_db,
            "checkpoint_enabled": True,
            "thread_pool_workers": 2,
            "batch_size": 10,
            "log_level": "INFO",
            "timeout": 30,
            "environment": "integration"
        }
    
    def _create_performance_config(self) -> Dict[str, Any]:
        """Create configuration for performance tests."""
        temp_db = self._create_temp_db()
        return {
            "db_path": temp_db,
            "checkpoint_enabled": True,
            "thread_pool_workers": 4,
            "batch_size": 50,
            "log_level": "ERROR",
            "timeout": 60,
            "environment": "performance"
        }
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration."""
        return {
            "db_path": ":memory:",
            "checkpoint_enabled": False,
            "thread_pool_workers": 1,
            "batch_size": 10,
            "log_level": "INFO",
            "timeout": 30,
            "environment": "default"
        }
    
    def _create_temp_db(self) -> str:
        """Create temporary database file."""
        temp_file = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        self.temp_files.append(temp_path)
        return temp_path
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config.copy()
    
    def cleanup(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            try:
                Path(temp_file).unlink(missing_ok=True)
            except Exception:
                pass
        self.temp_files.clear()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()

class MockImportManager:
    """Manager for handling missing imports in test environment."""
    
    @staticmethod
    def create_mock_workflow_engine_config(**kwargs):
        """Create mock WorkflowEngineConfig."""
        class MockConfig:
            def __init__(self, **config_kwargs):
                # Default values
                self.db_path = ":memory:"
                self.checkpoint_enabled = False
                self.thread_pool_workers = 1
                self.batch_size = 10
                self.log_level = "INFO"
                self.timeout = 30
                
                # Override with provided values
                for k, v in config_kwargs.items():
                    setattr(self, k, v)
        
        return MockConfig(**kwargs)
    
    @staticmethod
    def create_mock_database_manager(db_path: str = ":memory:"):
        """Create mock DatabaseManager."""
        from unittest.mock import Mock
        
        mock = Mock()
        mock.db_path = db_path
        
        # Mock common methods
        mock.create_flow_by_name.return_value = 1
        mock.get_flow_by_name.return_value = {"flow_id": 1, "name": "test-flow"}
        mock.get_latest_flow_version.return_value = {"flow_version_id": 1, "version": "1.0.0"}
        mock.get_flow_version_by_version.return_value = {"flow_version_id": 2, "version": "2.0.0"}
        mock.create_run.return_value = None
        mock.get_run.return_value = {"thread_id": "test-123", "status": "pending", "flow_version_id": 1}
        mock.atomic_update_run_status.return_value = True
        
        return mock
    
    @staticmethod
    def create_mock_workflow_engine(config=None):
        """Create mock WorkflowEngine."""
        from unittest.mock import Mock
        
        mock = Mock()
        mock.config = config or MockImportManager.create_mock_workflow_engine_config()
        mock.db_manager = MockImportManager.create_mock_database_manager()
        
        # Mock common methods
        mock.create_flow.return_value = 1
        mock.start_workflow.return_value = "test-thread-123"
        mock.compile_workflow.return_value = Mock()
        
        return mock

def setup_test_environment(environment: str = "test") -> TestEnvironment:
    """Setup test environment with proper configuration.
    
    Args:
        environment: Environment type (test, integration, performance)
        
    Returns:
        TestEnvironment instance
    """
    return TestEnvironment(environment)

def get_test_config(environment: str = "test") -> Dict[str, Any]:
    """Get test configuration for specified environment.
    
    Args:
        environment: Environment type
        
    Returns:
        Configuration dictionary
    """
    with setup_test_environment(environment) as env:
        return env.get_config()

# Environment detection
def is_ci_environment() -> bool:
    """Check if running in CI environment."""
    ci_indicators = ['CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS', 'GITLAB_CI']
    return any(os.getenv(indicator) for indicator in ci_indicators)

def is_local_development() -> bool:
    """Check if running in local development environment."""
    return not is_ci_environment() and os.getenv('ENVIRONMENT') != 'production'

# Auto-configure based on environment
def auto_configure_test_environment() -> str:
    """Automatically configure test environment based on context."""
    if is_ci_environment():
        return "integration"
    elif is_local_development():
        return "test"
    else:
        return "test"

if __name__ == "__main__":
    # Test the configuration
    print("🔧 Testing Environment Configuration")
    print("=" * 50)
    
    environments = ["test", "integration", "performance"]
    
    for env_type in environments:
        print(f"\n📋 {env_type.upper()} Environment:")
        with setup_test_environment(env_type) as env:
            config = env.get_config()
            for key, value in config.items():
                print(f"  • {key}: {value}")
    
    print(f"\n🎯 Auto-detected environment: {auto_configure_test_environment()}")
    print("✅ Environment configuration test completed!")