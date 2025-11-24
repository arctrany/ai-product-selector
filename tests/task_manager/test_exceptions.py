#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Manager Exceptions 测试模块

测试所有异常类型的功能和继承关系。
"""

import pytest
from unittest.mock import Mock, MagicMock

from task_manager.exceptions import (
    TaskManagerError,
    TaskCreationError,
    TaskExecutionError,
    TaskNotFoundError,
    TaskStateError,
    TaskTimeoutError
)


class TestTaskManagerError:
    """测试 TaskManagerError 基础异常"""

    def test_initialization_with_message(self):
        """测试仅带消息的初始化"""
        message = "Test error message"
        error = TaskManagerError(message)
        
        assert str(error) == message
        assert error.message == message
        assert error.task_id is None
        assert error.cause is None

    def test_initialization_with_task_id(self):
        """测试带任务ID的初始化"""
        message = "Test error with task ID"
        task_id = "task_123"
        error = TaskManagerError(message, task_id=task_id)
        
        assert error.message == message
        assert error.task_id == task_id
        assert error.cause is None
        # 验证字符串表示包含任务ID
        assert f"Task {task_id}: {message}" == str(error)

    def test_initialization_with_cause(self):
        """测试带原因的初始化"""
        message = "Test error with cause"
        cause = Exception("Root cause")
        error = TaskManagerError(message, cause=cause)
        
        assert error.message == message
        assert error.task_id is None
        assert error.cause is cause

    def test_initialization_with_all_parameters(self):
        """测试带所有参数的初始化"""
        message = "Test error with all parameters"
        task_id = "task_456"
        cause = Exception("Root cause")
        error = TaskManagerError(message, task_id=task_id, cause=cause)
        
        assert error.message == message
        assert error.task_id == task_id
        assert error.cause is cause
        # 验证字符串表示包含任务ID
        assert f"Task {task_id}: {message}" == str(error)

    def test_inheritance_from_exception(self):
        """测试继承自 Exception"""
        error = TaskManagerError("Test")
        assert isinstance(error, Exception)


class TestTaskCreationError:
    """测试 TaskCreationError 异常"""

    def test_initialization(self):
        """测试初始化"""
        message = "Task creation failed"
        task_id = "create_task_123"
        cause = ValueError("Invalid parameters")
        
        error = TaskCreationError(message, task_id=task_id, cause=cause)
        
        assert isinstance(error, TaskManagerError)
        assert error.message == message
        assert error.task_id == task_id
        assert error.cause is cause

    def test_default_parameters(self):
        """测试默认参数"""
        message = "Simple creation error"
        error = TaskCreationError(message)
        
        assert error.message == message
        assert error.task_id is None
        assert error.cause is None


class TestTaskExecutionError:
    """测试 TaskExecutionError 异常"""

    def test_initialization(self):
        """测试初始化"""
        message = "Task execution failed"
        task_id = "exec_task_123"
        cause = RuntimeError("Execution error")
        
        error = TaskExecutionError(message, task_id=task_id, cause=cause)
        
        assert isinstance(error, TaskManagerError)
        assert error.message == message
        assert error.task_id == task_id
        assert error.cause is cause

    def test_default_parameters(self):
        """测试默认参数"""
        message = "Simple execution error"
        error = TaskExecutionError(message)
        
        assert error.message == message
        assert error.task_id is None
        assert error.cause is None


class TestTaskNotFoundError:
    """测试 TaskNotFoundError 异常"""

    def test_initialization(self):
        """测试初始化"""
        task_id = "non_existent_task"
        error = TaskNotFoundError(task_id)
        
        expected_message = f"Task with ID '{task_id}' not found"
        assert error.message == expected_message
        assert error.task_id == task_id
        assert error.cause is None
        assert str(error) == expected_message

    def test_inheritance(self):
        """测试继承关系"""
        error = TaskNotFoundError("test_task")
        assert isinstance(error, TaskManagerError)


class TestTaskStateError:
    """测试 TaskStateError 异常"""

    def test_initialization(self):
        """测试初始化"""
        message = "Invalid task state transition"
        task_id = "state_task_123"
        cause = ValueError("Wrong state")
        
        error = TaskStateError(message, task_id=task_id, cause=cause)
        
        assert isinstance(error, TaskManagerError)
        assert error.message == message
        assert error.task_id == task_id
        assert error.cause is cause

    def test_default_parameters(self):
        """测试默认参数"""
        message = "Simple state error"
        error = TaskStateError(message)
        
        assert error.message == message
        assert error.task_id is None
        assert error.cause is None


class TestTaskTimeoutError:
    """测试 TaskTimeoutError 异常"""

    def test_initialization_with_task_id_and_timeout(self):
        """测试带任务ID和超时时间的初始化"""
        task_id = "timeout_task_123"
        timeout = 30
        error = TaskTimeoutError(task_id=task_id, timeout=timeout)
        
        expected_message = f"Task execution timeout after {timeout} seconds"
        assert error.message == expected_message
        assert error.task_id == task_id
        assert error.cause is None
        assert str(error) == expected_message

    def test_initialization_with_task_id_only(self):
        """测试仅带任务ID的初始化"""
        task_id = "timeout_task_456"
        error = TaskTimeoutError(task_id=task_id)
        
        expected_message = "Task execution timeout"
        assert error.message == expected_message
        assert error.task_id == task_id
        assert str(error) == expected_message

    def test_initialization_without_parameters(self):
        """测试不带参数的初始化"""
        error = TaskTimeoutError()
        
        expected_message = "Task execution timeout"
        assert error.message == expected_message
        assert error.task_id is None
        assert str(error) == expected_message

    def test_inheritance(self):
        """测试继承关系"""
        error = TaskTimeoutError()
        assert isinstance(error, TaskExecutionError)
        assert isinstance(error, TaskManagerError)


class TestExceptionInheritanceHierarchy:
    """测试异常继承层次结构"""

    def test_inheritance_chain(self):
        """测试继承链"""
        # TaskManagerError 继承自 Exception
        assert issubclass(TaskManagerError, Exception)
        
        # 其他异常继承自 TaskManagerError
        assert issubclass(TaskCreationError, TaskManagerError)
        assert issubclass(TaskExecutionError, TaskManagerError)
        assert issubclass(TaskNotFoundError, TaskManagerError)
        assert issubclass(TaskStateError, TaskManagerError)
        assert issubclass(TaskTimeoutError, TaskExecutionError)  # 特殊继承关系

    def test_instance_checks(self):
        """测试实例检查"""
        base_error = TaskManagerError("Base error")
        creation_error = TaskCreationError("Creation error")
        execution_error = TaskExecutionError("Execution error")
        not_found_error = TaskNotFoundError("test_task")
        state_error = TaskStateError("State error")
        timeout_error = TaskTimeoutError()
        
        # 所有异常都是 TaskManagerError 的实例
        assert isinstance(base_error, TaskManagerError)
        assert isinstance(creation_error, TaskManagerError)
        assert isinstance(execution_error, TaskManagerError)
        assert isinstance(not_found_error, TaskManagerError)
        assert isinstance(state_error, TaskManagerError)
        assert isinstance(timeout_error, TaskManagerError)
        
        # TaskTimeoutError 也是 TaskExecutionError 的实例
        assert isinstance(timeout_error, TaskExecutionError)


class TestExceptionUsage:
    """测试异常使用场景"""

    def test_exception_raising(self):
        """测试异常抛出"""
        def function_that_raises():
            raise TaskCreationError("Failed to create task", task_id="test_task")
        
        with pytest.raises(TaskCreationError) as exc_info:
            function_that_raises()
        
        assert exc_info.value.message == "Failed to create task"
        assert exc_info.value.task_id == "test_task"

    def test_exception_catching(self):
        """测试异常捕获"""
        def function_that_raises_base():
            raise TaskManagerError("Base error", task_id="test_task")
        
        def function_that_catches():
            try:
                function_that_raises_base()
            except TaskManagerError as e:
                # 重新抛出为更具体的异常
                raise TaskCreationError(f"Creation failed: {e.message}", task_id=e.task_id) from e
        
        with pytest.raises(TaskCreationError) as exc_info:
            function_that_catches()
        
        assert "Creation failed" in exc_info.value.message
        assert exc_info.value.task_id == "test_task"
        assert isinstance(exc_info.value.cause, TaskManagerError)

    def test_exception_chaining(self):
        """测试异常链"""
        root_cause = ValueError("Invalid input")
        task_error = TaskExecutionError("Task failed", task_id="test_task", cause=root_cause)
        
        assert task_error.cause is root_cause
        assert str(task_error.cause) == "Invalid input"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
