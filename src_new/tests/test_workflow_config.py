"""Test workflow configuration functionality."""

import unittest
import tempfile
import os
import sys
import shutil
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflow_engine.core.config import (
    WorkflowEngineConfig, ConfigManager, DependencyContainer,
    get_config_manager, get_config, get_container
)

class TestWorkflowEngineConfig(unittest.TestCase):
    """Test WorkflowEngineConfig class."""

    def test_default_config_creation(self):
        """Test creation of config with default values."""
        config = WorkflowEngineConfig()
        
        # Check default values
        self.assertEqual(config.db_pool_size, 5)
        self.assertEqual(config.thread_pool_workers, 4)
        self.assertEqual(config.batch_size, 100)
        self.assertTrue(config.checkpoint_enabled)
        self.assertEqual(config.log_level, "INFO")
        self.assertTrue(config.validate_inputs)
        self.assertEqual(config.max_workflow_depth, 100)
        self.assertTrue(config.enable_async_operations)

    def test_config_with_custom_values(self):
        """Test creation of config with custom values."""
        config = WorkflowEngineConfig(
            db_pool_size=10,
            thread_pool_workers=8,
            batch_size=200,
            checkpoint_enabled=False,
            log_level="DEBUG",
            validate_inputs=False,
            max_workflow_depth=50
        )
        
        self.assertEqual(config.db_pool_size, 10)
        self.assertEqual(config.thread_pool_workers, 8)
        self.assertEqual(config.batch_size, 200)
        self.assertFalse(config.checkpoint_enabled)
        self.assertEqual(config.log_level, "DEBUG")
        self.assertFalse(config.validate_inputs)
        self.assertEqual(config.max_workflow_depth, 50)

    def test_config_post_init_db_path(self):
        """Test that db_path is set in __post_init__ if None."""
        config = WorkflowEngineConfig()
        
        # Should have set a default db_path
        self.assertIsNotNone(config.db_path)
        self.assertTrue(config.db_path.endswith("workflow.db"))

    def test_config_post_init_checkpoint_path(self):
        """Test that checkpoint_db_path is set when checkpoint is enabled."""
        config = WorkflowEngineConfig(
            db_path="/tmp/test.db",
            checkpoint_enabled=True
        )
        
        # Should have set checkpoint path based on db_path
        self.assertIsNotNone(config.checkpoint_db_path)
        self.assertTrue(config.checkpoint_db_path.endswith("_checkpoints.db"))

    def test_config_no_checkpoint_path_when_disabled(self):
        """Test that checkpoint_db_path is not set when checkpoint is disabled."""
        config = WorkflowEngineConfig(
            checkpoint_enabled=False
        )
        
        # Should not have set checkpoint path
        self.assertIsNone(config.checkpoint_db_path)


class TestDependencyContainer(unittest.TestCase):
    """Test DependencyContainer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.container = DependencyContainer()

    def test_register_and_get_singleton(self):
        """Test registering and getting singleton instances."""
        # Create a test service
        test_service = "test_singleton"
        
        # Register as singleton
        self.container.register_singleton(str, test_service)
        
        # Get the service
        retrieved = self.container.get(str)
        self.assertEqual(retrieved, test_service)
        
        # Should return the same instance
        retrieved2 = self.container.get(str)
        self.assertIs(retrieved, retrieved2)

    def test_register_and_get_factory(self):
        """Test registering and getting factory instances."""
        # Create a factory function
        call_count = 0
        def factory():
            nonlocal call_count
            call_count += 1
            return f"instance_{call_count}"
        
        # Register factory
        self.container.register_factory(str, factory)
        
        # Get instances - should create new ones each time
        instance1 = self.container.get(str)
        instance2 = self.container.get(str)
        
        self.assertEqual(instance1, "instance_1")
        self.assertEqual(instance2, "instance_2")
        self.assertNotEqual(instance1, instance2)

    def test_register_and_get_instance(self):
        """Test registering and getting regular instances."""
        test_service = "test_instance"
        
        # Register instance
        self.container.register_instance(str, test_service)
        
        # Get the service
        retrieved = self.container.get(str)
        self.assertEqual(retrieved, test_service)

    def test_has_service(self):
        """Test checking if service is registered."""
        # Should not have service initially
        self.assertFalse(self.container.has(str))
        
        # Register service
        self.container.register_singleton(str, "test")
        
        # Should have service now
        self.assertTrue(self.container.has(str))

    def test_get_unregistered_service_raises_error(self):
        """Test that getting unregistered service raises ValueError."""
        with self.assertRaises(ValueError) as context:
            self.container.get(str)
        
        self.assertIn("Service str not registered", str(context.exception))

    def test_clear_services(self):
        """Test clearing all registered services."""
        # Register some services
        self.container.register_singleton(str, "test1")
        self.container.register_instance(int, 42)
        
        # Should have services
        self.assertTrue(self.container.has(str))
        self.assertTrue(self.container.has(int))
        
        # Clear services
        self.container.clear()
        
        # Should not have services anymore
        self.assertFalse(self.container.has(str))
        self.assertFalse(self.container.has(int))


class TestConfigManager(unittest.TestCase):
    """Test ConfigManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Get a fresh config manager for each test
        self.config_manager = ConfigManager()

    def test_singleton_pattern(self):
        """Test that ConfigManager follows singleton pattern."""
        manager1 = ConfigManager()
        manager2 = ConfigManager()
        
        # Should be the same instance
        self.assertIs(manager1, manager2)

    def test_set_and_get_config(self):
        """Test setting and getting configuration."""
        config = WorkflowEngineConfig(
            db_pool_size=15,
            log_level="ERROR"
        )
        
        # Set config
        self.config_manager.set_config(config)
        
        # Get config
        retrieved = self.config_manager.get_config()
        self.assertIs(retrieved, config)
        self.assertEqual(retrieved.db_pool_size, 15)
        self.assertEqual(retrieved.log_level, "ERROR")

    def test_get_config_creates_default_if_none(self):
        """Test that get_config creates default config if none set."""
        # Clear any existing config
        self.config_manager._config = None
        
        # Get config should create default
        config = self.config_manager.get_config()
        
        self.assertIsInstance(config, WorkflowEngineConfig)
        self.assertEqual(config.db_pool_size, 5)  # Default value

    def test_get_container(self):
        """Test getting dependency container."""
        container = self.config_manager.get_container()
        
        self.assertIsInstance(container, DependencyContainer)

    @patch.dict(os.environ, {
        'WORKFLOW_DB_PATH': '/custom/path/db.sqlite',
        'WORKFLOW_DB_POOL_SIZE': '20',
        'WORKFLOW_DB_ECHO': 'true',
        'WORKFLOW_THREAD_WORKERS': '12',
        'WORKFLOW_BATCH_SIZE': '500',
        'WORKFLOW_CHECKPOINT_ENABLED': 'false',
        'WORKFLOW_LOG_LEVEL': 'debug',
        'WORKFLOW_VALIDATE_INPUTS': 'false',
        'WORKFLOW_MAX_DEPTH': '200',
        'WORKFLOW_ENABLE_ASYNC': 'false'
    })
    def test_load_from_env(self):
        """Test loading configuration from environment variables."""
        config = self.config_manager.load_from_env()
        
        # Check that environment values were loaded
        self.assertEqual(config.db_path, '/custom/path/db.sqlite')
        self.assertEqual(config.db_pool_size, 20)
        self.assertTrue(config.db_echo)
        self.assertEqual(config.thread_pool_workers, 12)
        self.assertEqual(config.batch_size, 500)
        self.assertFalse(config.checkpoint_enabled)
        self.assertEqual(config.log_level, 'DEBUG')
        self.assertFalse(config.validate_inputs)
        self.assertEqual(config.max_workflow_depth, 200)
        self.assertFalse(config.enable_async_operations)

    @patch.dict(os.environ, {}, clear=True)
    def test_load_from_env_with_defaults(self):
        """Test loading from environment with no env vars set."""
        config = self.config_manager.load_from_env()
        
        # Should have default values
        self.assertEqual(config.db_pool_size, 5)
        self.assertEqual(config.thread_pool_workers, 4)
        self.assertTrue(config.checkpoint_enabled)
        self.assertEqual(config.log_level, 'INFO')
        self.assertTrue(config.validate_inputs)


class TestGlobalFunctions(unittest.TestCase):
    """Test global configuration functions."""

    def test_get_config_manager(self):
        """Test get_config_manager function."""
        manager = get_config_manager()
        
        self.assertIsInstance(manager, ConfigManager)

    def test_get_config(self):
        """Test get_config function."""
        config = get_config()
        
        self.assertIsInstance(config, WorkflowEngineConfig)

    def test_get_container(self):
        """Test get_container function."""
        container = get_container()
        
        self.assertIsInstance(container, DependencyContainer)

    def test_global_functions_consistency(self):
        """Test that global functions return consistent instances."""
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        
        # Should be same manager instance
        self.assertIs(manager1, manager2)
        
        # Config from manager should match global config
        config1 = manager1.get_config()
        config2 = get_config()
        self.assertIs(config1, config2)
        
        # Container from manager should match global container
        container1 = manager1.get_container()
        container2 = get_container()
        self.assertIs(container1, container2)


if __name__ == '__main__':
    unittest.main()