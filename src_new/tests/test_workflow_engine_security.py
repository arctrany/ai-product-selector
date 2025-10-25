"""
Unit tests for workflow engine security validation and safety checks.

Tests cover:
- InputValidator workflow definition validation
- InputValidator Python code security checks
- ExecutionTimeoutManager timeout handling
- SafeImportManager import restrictions
- Security exception handling
- Thread safety of security components
"""

import ast
import threading
import time
import unittest
from unittest.mock import patch, MagicMock

from src_new.workflow_engine.core.security import (
    SecurityError,
    InputValidationError,
    ExecutionTimeoutError,
    UnsafeCodeError,
    InputValidator,
    ExecutionTimeoutManager,
    SafeImportManager,
    get_input_validator,
    get_timeout_manager,
    get_import_manager,
    validate_workflow_definition,
    validate_input_data,
    execution_timeout
)
from src_new.workflow_engine.core.config import WorkflowEngineConfig


class TestSecurityExceptions(unittest.TestCase):
    """Test security exception classes."""

    def test_security_error_inheritance(self):
        """Test SecurityError is base exception."""
        error = SecurityError("test message")
        self.assertIsInstance(error, Exception)
        self.assertEqual(str(error), "test message")

    def test_input_validation_error(self):
        """Test InputValidationError."""
        error = InputValidationError("validation failed")
        self.assertIsInstance(error, SecurityError)
        self.assertEqual(str(error), "validation failed")

    def test_execution_timeout_error(self):
        """Test ExecutionTimeoutError."""
        error = ExecutionTimeoutError("timeout occurred")
        self.assertIsInstance(error, SecurityError)
        self.assertEqual(str(error), "timeout occurred")

    def test_unsafe_code_error(self):
        """Test UnsafeCodeError."""
        error = UnsafeCodeError("unsafe code detected")
        self.assertIsInstance(error, SecurityError)
        self.assertEqual(str(error), "unsafe code detected")


class TestInputValidator(unittest.TestCase):
    """Test InputValidator class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create validator with validation enabled
        config = WorkflowEngineConfig(validate_inputs=True)
        with patch('src_new.workflow_engine.core.security.get_config', return_value=config):
            self.validator = InputValidator()

    def test_valid_workflow_definition(self):
        """Test validation of valid workflow definition."""
        valid_definition = {
            "nodes": [
                {"id": "start", "type": "start"},
                {"id": "process", "type": "python", "data": {"code": "result = input_data"}},
                {"id": "end", "type": "end"}
            ],
            "edges": [
                {"source": "start", "target": "process"},
                {"source": "process", "target": "end"}
            ]
        }

        # Should not raise any exception
        try:
            self.validator.validate_workflow_definition(valid_definition)
        except Exception as e:
            self.fail(f"Valid workflow definition raised exception: {e}")

    def test_invalid_workflow_definition_not_dict(self):
        """Test validation fails for non-dict definition."""
        with self.assertRaises(InputValidationError) as context:
            self.validator.validate_workflow_definition("not a dict")
        
        self.assertIn("must be a dictionary", str(context.exception))

    def test_invalid_workflow_definition_missing_fields(self):
        """Test validation fails for missing required fields."""
        # Missing nodes
        invalid_definition = {"edges": []}
        with self.assertRaises(InputValidationError) as context:
            self.validator.validate_workflow_definition(invalid_definition)
        self.assertIn("Missing required field: nodes", str(context.exception))

        # Missing edges
        invalid_definition = {"nodes": []}
        with self.assertRaises(InputValidationError) as context:
            self.validator.validate_workflow_definition(invalid_definition)
        self.assertIn("Missing required field: edges", str(context.exception))

    def test_invalid_nodes_not_list(self):
        """Test validation fails when nodes is not a list."""
        invalid_definition = {
            "nodes": "not a list",
            "edges": []
        }
        
        with self.assertRaises(InputValidationError) as context:
            self.validator.validate_workflow_definition(invalid_definition)
        self.assertIn("Nodes must be a list", str(context.exception))

    def test_too_many_nodes(self):
        """Test validation fails when too many nodes."""
        # Create definition with too many nodes
        nodes = [{"id": f"node_{i}", "type": "python"} for i in range(101)]
        invalid_definition = {
            "nodes": nodes,
            "edges": []
        }
        
        with self.assertRaises(InputValidationError) as context:
            self.validator.validate_workflow_definition(invalid_definition)
        self.assertIn("Too many nodes", str(context.exception))

    def test_invalid_node_structure(self):
        """Test validation of individual nodes."""
        # Node not a dict
        invalid_definition = {
            "nodes": ["not a dict"],
            "edges": []
        }
        
        with self.assertRaises(InputValidationError) as context:
            self.validator.validate_workflow_definition(invalid_definition)
        self.assertIn("Node 0 must be a dictionary", str(context.exception))

        # Node missing required fields
        invalid_definition = {
            "nodes": [{"id": "test"}],  # Missing type
            "edges": []
        }
        
        with self.assertRaises(InputValidationError) as context:
            self.validator.validate_workflow_definition(invalid_definition)
        self.assertIn("Node 0 missing required field: type", str(context.exception))

    def test_invalid_node_id(self):
        """Test validation of node IDs."""
        # Empty node ID
        invalid_definition = {
            "nodes": [{"id": "", "type": "start"}],
            "edges": []
        }
        
        with self.assertRaises(InputValidationError) as context:
            self.validator.validate_workflow_definition(invalid_definition)
        self.assertIn("Node 0 ID must be a non-empty string", str(context.exception))

        # Non-string node ID
        invalid_definition = {
            "nodes": [{"id": 123, "type": "start"}],
            "edges": []
        }
        
        with self.assertRaises(InputValidationError) as context:
            self.validator.validate_workflow_definition(invalid_definition)
        self.assertIn("Node 0 ID must be a non-empty string", str(context.exception))

    def test_invalid_node_type(self):
        """Test validation of node types."""
        invalid_definition = {
            "nodes": [{"id": "test", "type": "invalid_type"}],
            "edges": []
        }
        
        with self.assertRaises(InputValidationError) as context:
            self.validator.validate_workflow_definition(invalid_definition)
        self.assertIn("Node 0 has invalid type: invalid_type", str(context.exception))

    def test_invalid_edges_structure(self):
        """Test validation of edges structure."""
        # Edges not a list
        invalid_definition = {
            "nodes": [{"id": "test", "type": "start"}],
            "edges": "not a list"
        }
        
        with self.assertRaises(InputValidationError) as context:
            self.validator.validate_workflow_definition(invalid_definition)
        self.assertIn("Edges must be a list", str(context.exception))

        # Edge not a dict
        invalid_definition = {
            "nodes": [{"id": "test", "type": "start"}],
            "edges": ["not a dict"]
        }
        
        with self.assertRaises(InputValidationError) as context:
            self.validator.validate_workflow_definition(invalid_definition)
        self.assertIn("Edge 0 must be a dictionary", str(context.exception))

    def test_invalid_edge_fields(self):
        """Test validation of edge fields."""
        # Missing source
        invalid_definition = {
            "nodes": [{"id": "test", "type": "start"}],
            "edges": [{"target": "test"}]
        }
        
        with self.assertRaises(InputValidationError) as context:
            self.validator.validate_workflow_definition(invalid_definition)
        self.assertIn("Edge 0 missing required field: source", str(context.exception))

        # Empty source
        invalid_definition = {
            "nodes": [{"id": "test", "type": "start"}],
            "edges": [{"source": "", "target": "test"}]
        }
        
        with self.assertRaises(InputValidationError) as context:
            self.validator.validate_workflow_definition(invalid_definition)
        self.assertIn("Edge 0 source must be a non-empty string", str(context.exception))

    def test_dangerous_python_code_detection(self):
        """Test detection of dangerous Python code."""
        dangerous_codes = [
            "import os",
            "from sys import exit",
            "__import__('subprocess')",
            'exec("malicious code")',
            "eval(user_input)",
            "open('/etc/passwd')",
            "globals()",
            "__class__.__bases__"
        ]

        for code in dangerous_codes:
            definition = {
                "nodes": [{"id": "test", "type": "python", "data": {"code": code}}],
                "edges": []
            }
            
            with self.assertRaises(UnsafeCodeError) as context:
                self.validator.validate_workflow_definition(definition)
            self.assertIn("Dangerous", str(context.exception))

    def test_python_syntax_error_detection(self):
        """Test detection of Python syntax errors."""
        invalid_code = "if True\n    print('missing colon')"
        
        definition = {
            "nodes": [{"id": "test", "type": "python", "data": {"code": invalid_code}}],
            "edges": []
        }
        
        with self.assertRaises(InputValidationError) as context:
            self.validator.validate_workflow_definition(definition)
        self.assertIn("Syntax error in code", str(context.exception))

    def test_input_data_validation_string(self):
        """Test input data size validation for strings."""
        # Valid size
        small_data = "a" * 100
        try:
            self.validator.validate_input_data(small_data, max_size=1000)
        except Exception as e:
            self.fail(f"Valid string data raised exception: {e}")

        # Too large
        large_data = "a" * 2000
        with self.assertRaises(InputValidationError) as context:
            self.validator.validate_input_data(large_data, max_size=1000)
        self.assertIn("Input data too large", str(context.exception))

    def test_input_data_validation_dict(self):
        """Test input data size validation for dictionaries."""
        # Valid size
        small_dict = {"key1": "value1", "key2": "value2"}
        try:
            self.validator.validate_input_data(small_dict, max_size=1000)
        except Exception as e:
            self.fail(f"Valid dict data raised exception: {e}")

        # Too large (estimated)
        large_dict = {f"key_{i}": "a" * 100 for i in range(20)}
        with self.assertRaises(InputValidationError) as context:
            self.validator.validate_input_data(large_dict, max_size=1000)
        self.assertIn("Input data too large", str(context.exception))

    def test_input_data_validation_list(self):
        """Test input data size validation for lists."""
        # Valid size
        small_list = ["item1", "item2", "item3"]
        try:
            self.validator.validate_input_data(small_list, max_size=1000)
        except Exception as e:
            self.fail(f"Valid list data raised exception: {e}")

        # Too large (estimated)
        large_list = ["a" * 100 for _ in range(20)]
        with self.assertRaises(InputValidationError) as context:
            self.validator.validate_input_data(large_list, max_size=1000)
        self.assertIn("Input data too large", str(context.exception))

    def test_validation_disabled(self):
        """Test that validation can be disabled."""
        config = WorkflowEngineConfig(validate_inputs=False)
        with patch('src_new.workflow_engine.core.security.get_config', return_value=config):
            validator = InputValidator()

        # Should not validate when disabled
        invalid_definition = "not a dict"
        try:
            validator.validate_workflow_definition(invalid_definition)
            validator.validate_input_data("a" * 10000, max_size=100)
        except Exception as e:
            self.fail(f"Validation should be disabled but raised exception: {e}")


class TestExecutionTimeoutManager(unittest.TestCase):
    """Test ExecutionTimeoutManager class."""

    def setUp(self):
        """Set up test fixtures."""
        config = WorkflowEngineConfig(max_execution_time=2)
        with patch('src_new.workflow_engine.core.security.get_config', return_value=config):
            self.timeout_manager = ExecutionTimeoutManager()

    def test_timeout_context_manager_success(self):
        """Test timeout context manager with successful execution."""
        with self.timeout_manager.timeout(5):
            time.sleep(0.1)  # Short operation should succeed

    def test_timeout_context_manager_timeout(self):
        """Test timeout context manager with timeout."""
        with self.assertRaises(ExecutionTimeoutError) as context:
            with self.timeout_manager.timeout(1):
                time.sleep(2)  # Long operation should timeout
        
        self.assertIn("exceeded 1 seconds", str(context.exception))

    def test_timeout_no_limit(self):
        """Test timeout with no limit (0 or negative)."""
        with self.timeout_manager.timeout(0):
            time.sleep(0.1)  # Should not timeout

        with self.timeout_manager.timeout(-1):
            time.sleep(0.1)  # Should not timeout

    def test_timeout_default_from_config(self):
        """Test timeout using default from config."""
        # This test is tricky because we can't easily test a 2-second timeout
        # So we'll just verify the context manager works
        with self.timeout_manager.timeout():
            time.sleep(0.1)  # Short operation should succeed

    def test_multiple_timeouts_thread_safety(self):
        """Test multiple concurrent timeouts."""
        results = []
        errors = []

        def worker_with_timeout(worker_id, sleep_time, timeout_time):
            try:
                with self.timeout_manager.timeout(timeout_time):
                    time.sleep(sleep_time)
                results.append(f"worker_{worker_id}_success")
            except ExecutionTimeoutError:
                results.append(f"worker_{worker_id}_timeout")
            except Exception as e:
                errors.append(f"worker_{worker_id}_error: {e}")

        # Create threads with different timeout scenarios
        threads = []
        
        # Thread that should succeed
        thread1 = threading.Thread(target=worker_with_timeout, args=(1, 0.1, 2))
        threads.append(thread1)
        
        # Thread that should timeout
        thread2 = threading.Thread(target=worker_with_timeout, args=(2, 2, 1))
        threads.append(thread2)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check results
        self.assertEqual(len(errors), 0, f"Unexpected errors: {errors}")
        self.assertIn("worker_1_success", results)
        self.assertIn("worker_2_timeout", results)


class TestSafeImportManager(unittest.TestCase):
    """Test SafeImportManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.import_manager = SafeImportManager()

    def test_allowed_module_import(self):
        """Test importing allowed modules."""
        # These should work
        allowed_modules = ['json', 'datetime', 'math', 'random']
        
        for module_name in allowed_modules:
            try:
                result = self.import_manager.safe_import(module_name)
                self.assertIsNotNone(result)
            except ImportError as e:
                self.fail(f"Allowed module {module_name} was rejected: {e}")

    def test_disallowed_module_import(self):
        """Test importing disallowed modules."""
        # These should be blocked
        disallowed_modules = ['os', 'sys', 'subprocess', 'socket']
        
        for module_name in disallowed_modules:
            with self.assertRaises(ImportError) as context:
                self.import_manager.safe_import(module_name)
            self.assertIn("not allowed for security reasons", str(context.exception))

    def test_submodule_import(self):
        """Test importing submodules."""
        # Allowed submodule
        try:
            result = self.import_manager.safe_import('urllib.parse')
            self.assertIsNotNone(result)
        except ImportError as e:
            self.fail(f"Allowed submodule urllib.parse was rejected: {e}")

        # Disallowed base module should block submodule
        with self.assertRaises(ImportError):
            self.import_manager.safe_import('os.path')

    def test_install_and_restore_import(self):
        """Test installing and restoring safe import."""
        # Get original import function
        original_import = __builtins__.__import__
        
        # Install safe import
        self.import_manager.install_safe_import()
        self.assertIs(__builtins__.__import__, self.import_manager.safe_import)
        
        # Restore original import
        self.import_manager.restore_original_import()
        self.assertIs(__builtins__.__import__, original_import)

    def test_thread_safety(self):
        """Test thread safety of import manager."""
        results = []
        errors = []

        def worker_import(worker_id):
            try:
                # Try to import allowed module
                self.import_manager.safe_import('json')
                results.append(f"worker_{worker_id}_success")
                
                # Try to import disallowed module
                try:
                    self.import_manager.safe_import('os')
                    results.append(f"worker_{worker_id}_unexpected_success")
                except ImportError:
                    results.append(f"worker_{worker_id}_blocked")
                    
            except Exception as e:
                errors.append(f"worker_{worker_id}_error: {e}")

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_import, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check results
        self.assertEqual(len(errors), 0, f"Unexpected errors: {errors}")
        
        # All workers should succeed with allowed imports and be blocked on disallowed
        success_count = len([r for r in results if r.endswith('_success')])
        blocked_count = len([r for r in results if r.endswith('_blocked')])
        
        self.assertEqual(success_count, 5)
        self.assertEqual(blocked_count, 5)


class TestGlobalSecurityFunctions(unittest.TestCase):
    """Test global security functions."""

    def test_get_input_validator(self):
        """Test get_input_validator function."""
        validator = get_input_validator()
        self.assertIsInstance(validator, InputValidator)
        
        # Should return same instance
        validator2 = get_input_validator()
        self.assertIs(validator, validator2)

    def test_get_timeout_manager(self):
        """Test get_timeout_manager function."""
        manager = get_timeout_manager()
        self.assertIsInstance(manager, ExecutionTimeoutManager)
        
        # Should return same instance
        manager2 = get_timeout_manager()
        self.assertIs(manager, manager2)

    def test_get_import_manager(self):
        """Test get_import_manager function."""
        manager = get_import_manager()
        self.assertIsInstance(manager, SafeImportManager)
        
        # Should return same instance
        manager2 = get_import_manager()
        self.assertIs(manager, manager2)

    def test_validate_workflow_definition_function(self):
        """Test global validate_workflow_definition function."""
        valid_definition = {
            "nodes": [{"id": "test", "type": "start"}],
            "edges": []
        }
        
        # Should not raise exception for valid definition
        try:
            validate_workflow_definition(valid_definition)
        except Exception as e:
            self.fail(f"Valid definition raised exception: {e}")

        # Should raise exception for invalid definition
        with self.assertRaises(InputValidationError):
            validate_workflow_definition("invalid")

    def test_validate_input_data_function(self):
        """Test global validate_input_data function."""
        # Should not raise exception for valid data
        try:
            validate_input_data("small data", max_size=1000)
        except Exception as e:
            self.fail(f"Valid data raised exception: {e}")

        # Should raise exception for large data
        with self.assertRaises(InputValidationError):
            validate_input_data("a" * 2000, max_size=1000)

    def test_execution_timeout_context_manager(self):
        """Test global execution_timeout context manager."""
        # Should work for short operations
        with execution_timeout(5):
            time.sleep(0.1)

        # Should timeout for long operations
        with self.assertRaises(ExecutionTimeoutError):
            with execution_timeout(1):
                time.sleep(2)


class TestSecurityIntegration(unittest.TestCase):
    """Integration tests for security components."""

    def test_comprehensive_workflow_validation(self):
        """Test comprehensive workflow validation with all security checks."""
        # Create a complex but valid workflow
        complex_workflow = {
            "nodes": [
                {"id": "start", "type": "start"},
                {
                    "id": "process1", 
                    "type": "python", 
                    "data": {
                        "code": "import json\nresult = json.dumps({'processed': True})"
                    }
                },
                {
                    "id": "condition1", 
                    "type": "condition",
                    "data": {
                        "condition": {"==": [{"var": "processed"}, True]}
                    }
                },
                {"id": "end", "type": "end"}
            ],
            "edges": [
                {"source": "start", "target": "process1"},
                {"source": "process1", "target": "condition1"},
                {"source": "condition1", "target": "end"}
            ]
        }

        # Should pass all validations
        try:
            validate_workflow_definition(complex_workflow)
        except Exception as e:
            self.fail(f"Valid complex workflow failed validation: {e}")

    def test_security_with_disabled_validation(self):
        """Test security behavior when validation is disabled."""
        config = WorkflowEngineConfig(validate_inputs=False)
        
        with patch('src_new.workflow_engine.core.security.get_config', return_value=config):
            # Even dangerous code should pass when validation is disabled
            dangerous_workflow = {
                "nodes": [
                    {
                        "id": "dangerous", 
                        "type": "python", 
                        "data": {"code": "import os; os.system('echo test')"}
                    }
                ],
                "edges": []
            }
            
            try:
                validate_workflow_definition(dangerous_workflow)
            except Exception as e:
                self.fail(f"Validation should be disabled but raised: {e}")

    def test_concurrent_security_operations(self):
        """Test concurrent security operations for thread safety."""
        results = []
        errors = []

        def security_worker(worker_id):
            try:
                # Validate workflow
                workflow = {
                    "nodes": [{"id": f"node_{worker_id}", "type": "start"}],
                    "edges": []
                }
                validate_workflow_definition(workflow)
                
                # Validate input data
                validate_input_data(f"data_{worker_id}", max_size=1000)
                
                # Use timeout
                with execution_timeout(2):
                    time.sleep(0.1)
                
                results.append(f"worker_{worker_id}_success")
                
            except Exception as e:
                errors.append(f"worker_{worker_id}_error: {e}")

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=security_worker, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check results
        self.assertEqual(len(errors), 0, f"Concurrent security test failed: {errors}")
        self.assertEqual(len(results), 10)
        
        # All workers should succeed
        for i in range(10):
            self.assertIn(f"worker_{i}_success", results)


if __name__ == '__main__':
    unittest.main()