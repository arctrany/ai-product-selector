"""Security validation and safety checks for workflow engine."""

import re
import ast
import time
import signal
import threading
from typing import Any, Dict, List, Optional, Set, Union
from contextlib import contextmanager

from .config import get_config


class SecurityError(Exception):
    """Base exception for security-related errors."""
    pass


class InputValidationError(SecurityError):
    """Exception raised when input validation fails."""
    pass


class ExecutionTimeoutError(SecurityError):
    """Exception raised when execution exceeds time limit."""
    pass


class UnsafeCodeError(SecurityError):
    """Exception raised when unsafe code is detected."""
    pass


class InputValidator:
    """Input validation for workflow engine."""

    # Dangerous built-in functions and modules
    DANGEROUS_BUILTINS = {
        'eval', 'exec', 'compile', '__import__', 'open', 'file',
        'input', 'raw_input', 'reload', 'vars', 'locals', 'globals',
        'dir', 'hasattr', 'getattr', 'setattr', 'delattr',
        'isinstance', 'issubclass', 'callable'
    }

    # Dangerous modules
    DANGEROUS_MODULES = {
        'os', 'sys', 'subprocess', 'shutil', 'tempfile', 'pickle',
        'marshal', 'shelve', 'dbm', 'sqlite3', 'socket', 'urllib',
        'http', 'ftplib', 'smtplib', 'telnetlib', 'webbrowser',
        'ctypes', 'multiprocessing', 'threading', 'asyncio'
    }

    # Dangerous attributes and methods
    DANGEROUS_ATTRIBUTES = {
        '__class__', '__bases__', '__subclasses__', '__mro__',
        '__dict__', '__globals__', '__locals__', '__code__',
        '__func__', '__self__', '__module__', '__name__',
        '__file__', '__path__', '__package__'
    }

    def __init__(self):
        self.config = get_config()

    def validate_workflow_definition(self, definition: Dict[str, Any]) -> None:
        """Validate workflow definition for security issues."""
        if not self.config.validate_inputs:
            return

        if not isinstance(definition, dict):
            raise InputValidationError("Workflow definition must be a dictionary")

        # Check required fields
        required_fields = ['nodes', 'edges']
        for field in required_fields:
            if field not in definition:
                raise InputValidationError(f"Missing required field: {field}")

        # Validate nodes
        nodes = definition.get('nodes', [])
        if not isinstance(nodes, list):
            raise InputValidationError("Nodes must be a list")

        if len(nodes) > self.config.max_workflow_depth:
            raise InputValidationError(f"Too many nodes: {len(nodes)} > {self.config.max_workflow_depth}")

        for i, node in enumerate(nodes):
            self._validate_node(node, i)

        # Validate edges
        edges = definition.get('edges', [])
        if not isinstance(edges, list):
            raise InputValidationError("Edges must be a list")

        for i, edge in enumerate(edges):
            self._validate_edge(edge, i)

    def _validate_node(self, node: Dict[str, Any], index: int) -> None:
        """Validate a single node."""
        if not isinstance(node, dict):
            raise InputValidationError(f"Node {index} must be a dictionary")

        # Check required fields
        required_fields = ['id', 'type']
        for field in required_fields:
            if field not in node:
                raise InputValidationError(f"Node {index} missing required field: {field}")

        # Validate node ID
        node_id = node.get('id')
        if not isinstance(node_id, str) or not node_id.strip():
            raise InputValidationError(f"Node {index} ID must be a non-empty string")

        # Validate node type
        node_type = node.get('type')
        valid_types = ['start', 'end', 'python', 'condition']
        if node_type not in valid_types:
            raise InputValidationError(f"Node {index} has invalid type: {node_type}")

        # Validate node data if present
        # START and END nodes may not have data, which is acceptable
        if 'data' in node and node['data'] is not None:
            self._validate_node_data(node['data'], index)

    def _validate_node_data(self, data: Dict[str, Any], node_index: int) -> None:
        """Validate node data for security issues."""
        if not isinstance(data, dict):
            raise InputValidationError(f"Node {node_index} data must be a dictionary")

        # Check for dangerous code in Python nodes
        if 'code' in data:
            code = data['code']
            if isinstance(code, str):
                self._validate_python_code(code, f"Node {node_index}")

    def _validate_edge(self, edge: Dict[str, Any], index: int) -> None:
        """Validate a single edge."""
        if not isinstance(edge, dict):
            raise InputValidationError(f"Edge {index} must be a dictionary")

        # Check required fields
        required_fields = ['source', 'target']
        for field in required_fields:
            if field not in edge:
                raise InputValidationError(f"Edge {index} missing required field: {field}")

        # Validate source and target
        source = edge.get('source')
        target = edge.get('target')

        if not isinstance(source, str) or not source.strip():
            raise InputValidationError(f"Edge {index} source must be a non-empty string")

        if not isinstance(target, str) or not target.strip():
            raise InputValidationError(f"Edge {index} target must be a non-empty string")

    def _validate_python_code(self, code: str, context: str) -> None:
        """Validate Python code for security issues."""
        if not isinstance(code, str):
            raise InputValidationError(f"{context}: Code must be a string")

        # Check for dangerous imports
        for module in self.DANGEROUS_MODULES:
            patterns = [
                f"import {module}",
                f"from {module}",
                f"__import__('{module}')",
                f'__import__("{module}")'
            ]
            for pattern in patterns:
                if pattern in code:
                    raise UnsafeCodeError(f"{context}: Dangerous import detected: {module}")

        # Check for dangerous built-ins
        for builtin in self.DANGEROUS_BUILTINS:
            if re.search(rf'\b{re.escape(builtin)}\b', code):
                raise UnsafeCodeError(f"{context}: Dangerous built-in detected: {builtin}")

        # Check for dangerous attributes
        for attr in self.DANGEROUS_ATTRIBUTES:
            if attr in code:
                raise UnsafeCodeError(f"{context}: Dangerous attribute detected: {attr}")

        # Try to parse the code to check for syntax errors
        try:
            ast.parse(code)
        except SyntaxError as e:
            raise InputValidationError(f"{context}: Syntax error in code: {e}")

    def validate_input_data(self, data: Any, max_size: int = 1024 * 1024) -> None:
        """Validate input data size and type."""
        if not self.config.validate_inputs:
            return

        # Check data size (rough estimation)
        if isinstance(data, (str, bytes)):
            if len(data) > max_size:
                raise InputValidationError(f"Input data too large: {len(data)} > {max_size}")
        elif isinstance(data, dict):
            # Estimate dict size
            estimated_size = sum(len(str(k)) + len(str(v)) for k, v in data.items())
            if estimated_size > max_size:
                raise InputValidationError(f"Input data too large: {estimated_size} > {max_size}")
        elif isinstance(data, list):
            # Estimate list size
            estimated_size = sum(len(str(item)) for item in data)
            if estimated_size > max_size:
                raise InputValidationError(f"Input data too large: {estimated_size} > {max_size}")


class ExecutionTimeoutManager:
    """Manages execution timeouts for workflow operations."""

    def __init__(self):
        self.config = get_config()
        self._active_timeouts = {}
        self._lock = threading.Lock()

    @contextmanager
    def timeout(self, seconds: Optional[int] = None):
        """Context manager for execution timeout."""
        timeout_seconds = seconds or self.config.max_execution_time

        if timeout_seconds <= 0:
            # No timeout
            yield
            return

        thread_id = threading.get_ident()
        timer = None

        def timeout_handler():
            with self._lock:
                if thread_id in self._active_timeouts:
                    del self._active_timeouts[thread_id]
            raise ExecutionTimeoutError(f"Execution exceeded {timeout_seconds} seconds")

        try:
            with self._lock:
                timer = threading.Timer(timeout_seconds, timeout_handler)
                self._active_timeouts[thread_id] = timer
                timer.start()

            yield

        finally:
            with self._lock:
                if thread_id in self._active_timeouts:
                    timer = self._active_timeouts.pop(thread_id)
                    if timer:
                        timer.cancel()


class SafeImportManager:
    """Manages safe imports for workflow execution."""

    # Allowed modules for workflow execution
    ALLOWED_MODULES = {
        'json', 'datetime', 'time', 'math', 'random', 'uuid',
        'base64', 'hashlib', 'hmac', 'secrets', 'string',
        'collections', 'itertools', 'functools', 'operator',
        're', 'urllib.parse', 'decimal', 'fractions'
    }

    def __init__(self):
        self.config = get_config()
        # Handle both dict and module forms of __builtins__
        if isinstance(__builtins__, dict):
            self._original_import = __builtins__['__import__']
        else:
            self._original_import = __builtins__.__import__
        self._import_lock = threading.Lock()

    def safe_import(self, name: str, globals=None, locals=None, fromlist=(), level=0):
        """Safe import function that only allows whitelisted modules."""
        with self._import_lock:
            # Check if module is allowed
            base_module = name.split('.')[0]
            if base_module not in self.ALLOWED_MODULES:
                raise ImportError(f"Module '{name}' is not allowed for security reasons")

            # Use original import
            return self._original_import(name, globals, locals, fromlist, level)

    def install_safe_import(self):
        """Install the safe import function."""
        __builtins__.__import__ = self.safe_import

    def restore_original_import(self):
        """Restore the original import function."""
        __builtins__.__import__ = self._original_import


# Global instances
_input_validator = InputValidator()
_timeout_manager = ExecutionTimeoutManager()
_import_manager = SafeImportManager()


def get_input_validator() -> InputValidator:
    """Get the global input validator instance."""
    return _input_validator


def get_timeout_manager() -> ExecutionTimeoutManager:
    """Get the global timeout manager instance."""
    return _timeout_manager


def get_import_manager() -> SafeImportManager:
    """Get the global import manager instance."""
    return _import_manager


def validate_workflow_definition(definition: Dict[str, Any]) -> None:
    """Validate workflow definition for security issues."""
    _input_validator.validate_workflow_definition(definition)


def validate_input_data(data: Any, max_size: int = 1024 * 1024) -> None:
    """Validate input data size and type."""
    _input_validator.validate_input_data(data, max_size)


@contextmanager
def execution_timeout(seconds: Optional[int] = None):
    """Context manager for execution timeout."""
    with _timeout_manager.timeout(seconds):
        yield
