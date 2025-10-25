"""
Unit tests for workflow engine configuration management and dependency injection.

Tests cover:
- WorkflowEngineConfig initialization and validation
- DependencyContainer registration and retrieval
- ConfigManager singleton behavior and thread safety
- Environment variable configuration loading
- Configuration persistence and defaults
"""

import os
import threading
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src_new.workflow_engine.core.config import (
    WorkflowEngineConfig,
    DependencyContainer,
    ConfigManager,
    get_config_manager,
    get_config,
    get_container
)


class TestWorkflowEngineConfig(unittest.TestCase):
    """Test WorkflowEngineConfig class."""

    def test_config_initialization_with_defaults(self):
        """Test config initialization with default values."""
        config = WorkflowEngineConfig()
        
        # Check default values
        self.assertEqual(config.db_pool_size, 5)
        self.assertEqual(config.db_max_overflow, 10)
        self.assertFalse(config.db_echo)
        self.assertEqual(config.thread_pool_workers, 4)
        self.assertEqual(config.batch_size, 100)
        self.assertEqual(config.query_timeout, 30)
        self.assertTrue(config.checkpoint_enabled)
        self.assertEqual(config.log_level, "INFO")
        self.assertTrue(config.validate_inputs)
        self.assertEqual(config.max_workflow_depth, 100)
        self.assertEqual(config.max_execution_time, 3600)
        self.assertTrue(config.enable_async_operations)
        self.assertTrue(config.enable_batch_operations)
        self.assertTrue(config.enable_metrics)

    def test_config_initialization_with_custom_values(self):
        """Test config initialization with custom values."""
        config = WorkflowEngineConfig(
            db_pool_size=10,
            thread_pool_workers=8,
            batch_size=200,
            checkpoint_enabled=False,
            log_level="DEBUG",
            validate_inputs=False,
            max_workflow_depth=50,
            enable_async_operations=False
        )
        
        self.assertEqual(config.db_pool_size, 10)
        self.assertEqual(config.thread_pool_workers, 8)
        self.assertEqual(config.batch_size, 200)
        self.assertFalse(config.checkpoint_enabled)
        self.assertEqual(config.log_level, "DEBUG")
        self.assertFalse(config.validate_inputs)
        self.assertEqual(config.max_workflow_depth, 50)
        self.assertFalse(config.enable_async_operations)

    def test_config_post_init_db_path_creation(self):
        """Test that default db_path is created correctly."""
        config = WorkflowEngineConfig()
        
        # Check that db_path is set
        self.assertIsNotNone(config.db_path)
        self.assertTrue(config.db_path.endswith("workflow.db"))
        
        # Check that checkpoint_db_path is derived from db_path
        self.assertIsNotNone(config.checkpoint_db_path)
        self.assertTrue(config.checkpoint_db_path.endswith("workflow_checkpoints.db"))

    def test_config_post_init_custom_db_path(self):
        """Test config with custom db_path."""
        custom_db_path = "/tmp/custom_workflow.db"
        config = WorkflowEngineConfig(db_path=custom_db_path)
        
        self.assertEqual(config.db_path, custom_db_path)
        self.assertEqual(config.checkpoint_db_path, "/tmp/custom_workflow_checkpoints.db")

    def test_config_checkpoint_disabled(self):
        """Test config with checkpoints disabled."""
        config = WorkflowEngineConfig(checkpoint_enabled=False)
        
        self.assertFalse(config.checkpoint_enabled)
        # checkpoint_db_path should still be None when disabled
        self.assertIsNone(config.checkpoint_db_path)


class TestDependencyContainer(unittest.TestCase):
    """Test DependencyContainer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.container = DependencyContainer()

    def test_register_and_get_singleton(self):
        """Test singleton registration and retrieval."""
        # Create a test service
        class TestService:
            def __init__(self, value):
                self.value = value

        service_instance = TestService("test_value")
        
        # Register singleton
        self.container.register_singleton(TestService, service_instance)
        
        # Retrieve and verify it's the same instance
        retrieved = self.container.get(TestService)
        self.assertIs(retrieved, service_instance)
        self.assertEqual(retrieved.value, "test_value")
        
        # Verify multiple calls return same instance
        retrieved2 = self.container.get(TestService)
        self.assertIs(retrieved, retrieved2)

    def test_register_and_get_factory(self):
        """Test factory registration and retrieval."""
        class TestService:
            def __init__(self, value):
                self.value = value

        # Register factory
        self.container.register_factory(TestService, lambda: TestService("factory_value"))
        
        # Retrieve and verify new instance each time
        retrieved1 = self.container.get(TestService)
        retrieved2 = self.container.get(TestService)
        
        self.assertIsNot(retrieved1, retrieved2)
        self.assertEqual(retrieved1.value, "factory_value")
        self.assertEqual(retrieved2.value, "factory_value")

    def test_register_and_get_instance(self):
        """Test instance registration and retrieval."""
        class TestService:
            def __init__(self, value):
                self.value = value

        service_instance = TestService("instance_value")
        
        # Register instance
        self.container.register_instance(TestService, service_instance)
        
        # Retrieve and verify
        retrieved = self.container.get(TestService)
        self.assertIs(retrieved, service_instance)

    def test_has_service(self):
        """Test service existence checking."""
        class TestService:
            pass

        # Initially not registered
        self.assertFalse(self.container.has(TestService))
        
        # Register and check
        self.container.register_singleton(TestService, TestService())
        self.assertTrue(self.container.has(TestService))

    def test_get_unregistered_service_raises_error(self):
        """Test that getting unregistered service raises ValueError."""
        class UnregisteredService:
            pass

        with self.assertRaises(ValueError) as context:
            self.container.get(UnregisteredService)
        
        self.assertIn("not registered", str(context.exception))

    def test_clear_services(self):
        """Test clearing all registered services."""
        class TestService1:
            pass
        
        class TestService2:
            pass

        # Register services
        self.container.register_singleton(TestService1, TestService1())
        self.container.register_factory(TestService2, lambda: TestService2())
        
        # Verify they exist
        self.assertTrue(self.container.has(TestService1))
        self.assertTrue(self.container.has(TestService2))
        
        # Clear and verify they're gone
        self.container.clear()
        self.assertFalse(self.container.has(TestService1))
        self.assertFalse(self.container.has(TestService2))

    def test_thread_safety(self):
        """Test that container is thread-safe."""
        class TestService:
            def __init__(self, value):
                self.value = value

        results = []
        errors = []

        def register_and_get(thread_id):
            try:
                # Register a service
                service = TestService(f"thread_{thread_id}")
                self.container.register_singleton(TestService, service)
                
                # Get the service
                retrieved = self.container.get(TestService)
                results.append((thread_id, retrieved.value))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=register_and_get, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check that no errors occurred
        self.assertEqual(len(errors), 0, f"Thread safety test failed with errors: {errors}")
        
        # All threads should have gotten some service (last one wins due to overwrite)
        self.assertEqual(len(results), 5)


class TestConfigManager(unittest.TestCase):
    """Test ConfigManager singleton class."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset singleton for each test
        ConfigManager._instance = None

    def test_singleton_behavior(self):
        """Test that ConfigManager is a singleton."""
        manager1 = ConfigManager()
        manager2 = ConfigManager()
        
        self.assertIs(manager1, manager2)

    def test_singleton_thread_safety(self):
        """Test that singleton creation is thread-safe."""
        instances = []
        
        def create_manager():
            instances.append(ConfigManager())

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_manager)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All instances should be the same
        self.assertEqual(len(instances), 10)
        for instance in instances:
            self.assertIs(instance, instances[0])

    def test_config_management(self):
        """Test config setting and getting."""
        manager = ConfigManager()
        
        # Initially should have default config
        config = manager.get_config()
        self.assertIsInstance(config, WorkflowEngineConfig)
        
        # Set custom config
        custom_config = WorkflowEngineConfig(db_pool_size=20)
        manager.set_config(custom_config)
        
        # Verify custom config is returned
        retrieved_config = manager.get_config()
        self.assertIs(retrieved_config, custom_config)
        self.assertEqual(retrieved_config.db_pool_size, 20)

    def test_container_access(self):
        """Test dependency container access."""
        manager = ConfigManager()
        
        container = manager.get_container()
        self.assertIsInstance(container, DependencyContainer)
        
        # Should return same container instance
        container2 = manager.get_container()
        self.assertIs(container, container2)

    def test_load_from_env_all_variables(self):
        """Test loading configuration from environment variables."""
        env_vars = {
            'WORKFLOW_DB_PATH': '/tmp/test_workflow.db',
            'WORKFLOW_DB_POOL_SIZE': '15',
            'WORKFLOW_DB_ECHO': 'true',
            'WORKFLOW_THREAD_WORKERS': '6',
            'WORKFLOW_BATCH_SIZE': '150',
            'WORKFLOW_CHECKPOINT_ENABLED': 'false',
            'WORKFLOW_CHECKPOINT_DB_PATH': '/tmp/test_checkpoints.db',
            'WORKFLOW_LOG_LEVEL': 'debug',
            'WORKFLOW_VALIDATE_INPUTS': 'false',
            'WORKFLOW_MAX_DEPTH': '75',
            'WORKFLOW_MAX_EXECUTION_TIME': '1800',
            'WORKFLOW_ENABLE_ASYNC': 'false',
            'WORKFLOW_ENABLE_BATCH': 'false',
            'WORKFLOW_ENABLE_METRICS': 'false'
        }

        with patch.dict(os.environ, env_vars):
            manager = ConfigManager()
            config = manager.load_from_env()

            self.assertEqual(config.db_path, '/tmp/test_workflow.db')
            self.assertEqual(config.db_pool_size, 15)
            self.assertTrue(config.db_echo)
            self.assertEqual(config.thread_pool_workers, 6)
            self.assertEqual(config.batch_size, 150)
            self.assertFalse(config.checkpoint_enabled)
            self.assertEqual(config.checkpoint_db_path, '/tmp/test_checkpoints.db')
            self.assertEqual(config.log_level, 'DEBUG')
            self.assertFalse(config.validate_inputs)
            self.assertEqual(config.max_workflow_depth, 75)
            self.assertEqual(config.max_execution_time, 1800)
            self.assertFalse(config.enable_async_operations)
            self.assertFalse(config.enable_batch_operations)
            self.assertFalse(config.enable_metrics)

    def test_load_from_env_partial_variables(self):
        """Test loading configuration with only some environment variables set."""
        env_vars = {
            'WORKFLOW_DB_POOL_SIZE': '25',
            'WORKFLOW_LOG_LEVEL': 'warning',
            'WORKFLOW_ENABLE_ASYNC': 'false'
        }

        with patch.dict(os.environ, env_vars, clear=False):
            manager = ConfigManager()
            config = manager.load_from_env()

            # Check that env vars were applied
            self.assertEqual(config.db_pool_size, 25)
            self.assertEqual(config.log_level, 'WARNING')
            self.assertFalse(config.enable_async_operations)
            
            # Check that defaults are still used for unset vars
            self.assertEqual(config.batch_size, 100)  # default
            self.assertTrue(config.checkpoint_enabled)  # default

    def test_load_from_env_boolean_parsing(self):
        """Test boolean environment variable parsing."""
        test_cases = [
            ('true', True),
            ('True', True),
            ('1', True),
            ('yes', True),
            ('false', False),
            ('False', False),
            ('0', False),
            ('no', False),
            ('invalid', False)  # Invalid values default to False
        ]

        for env_value, expected in test_cases:
            with patch.dict(os.environ, {'WORKFLOW_DB_ECHO': env_value}):
                manager = ConfigManager()
                config = manager.load_from_env()
                self.assertEqual(config.db_echo, expected, 
                               f"Failed for env_value: {env_value}")


class TestGlobalFunctions(unittest.TestCase):
    """Test global configuration functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset singleton for each test
        ConfigManager._instance = None

    def test_get_config_manager(self):
        """Test get_config_manager function."""
        manager = get_config_manager()
        self.assertIsInstance(manager, ConfigManager)
        
        # Should return same instance
        manager2 = get_config_manager()
        self.assertIs(manager, manager2)

    def test_get_config(self):
        """Test get_config function."""
        config = get_config()
        self.assertIsInstance(config, WorkflowEngineConfig)

    def test_get_container(self):
        """Test get_container function."""
        container = get_container()
        self.assertIsInstance(container, DependencyContainer)


class TestConfigIntegration(unittest.TestCase):
    """Integration tests for configuration system."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset singleton for each test
        ConfigManager._instance = None

    def test_config_persistence_across_calls(self):
        """Test that configuration persists across function calls."""
        # Set custom config
        custom_config = WorkflowEngineConfig(db_pool_size=99)
        manager = get_config_manager()
        manager.set_config(custom_config)
        
        # Verify it persists across different function calls
        config1 = get_config()
        config2 = get_config()
        
        self.assertIs(config1, custom_config)
        self.assertIs(config2, custom_config)
        self.assertEqual(config1.db_pool_size, 99)

    def test_container_service_persistence(self):
        """Test that container services persist across calls."""
        class TestService:
            def __init__(self, value):
                self.value = value

        # Register service through container
        container = get_container()
        service = TestService("persistent_value")
        container.register_singleton(TestService, service)
        
        # Verify service persists across different container calls
        container2 = get_container()
        retrieved_service = container2.get(TestService)
        
        self.assertIs(retrieved_service, service)
        self.assertEqual(retrieved_service.value, "persistent_value")

    def test_thread_safety_integration(self):
        """Test thread safety of the entire configuration system."""
        results = []
        errors = []

        def worker_thread(thread_id):
            try:
                # Each thread gets config and container
                config = get_config()
                container = get_container()
                
                # Register a service
                class ThreadService:
                    def __init__(self, tid):
                        self.thread_id = tid

                service = ThreadService(thread_id)
                container.register_instance(ThreadService, service)
                
                # Get the service back
                retrieved = container.get(ThreadService)
                results.append((thread_id, retrieved.thread_id, id(config), id(container)))
                
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        self.assertEqual(len(errors), 0, f"Integration test failed with errors: {errors}")
        self.assertEqual(len(results), 10)
        
        # All threads should get the same config and container instances
        config_ids = set(result[2] for result in results)
        container_ids = set(result[3] for result in results)
        
        self.assertEqual(len(config_ids), 1, "All threads should get same config instance")
        self.assertEqual(len(container_ids), 1, "All threads should get same container instance")


if __name__ == '__main__':
    unittest.main()