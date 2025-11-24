#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Manager Interfaces 测试模块

测试接口定义和契约，确保接口的正确实现和抽象。
"""

import pytest
from abc import ABC, abstractmethod
from unittest.mock import Mock, MagicMock
from datetime import datetime
from typing import Optional

from task_manager.interfaces import ITaskEventListener, ITaskManager, TaskInfo, TaskStatus


class TestTaskStatusEnum:
    """测试 TaskStatus 枚举"""

    def test_task_status_values(self):
        """测试 TaskStatus 枚举值"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.PAUSED.value == "paused"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.STOPPED.value == "stopped"

    def test_task_status_equality(self):
        """测试 TaskStatus 相等性"""
        assert TaskStatus.PENDING == TaskStatus("pending")
        assert TaskStatus.RUNNING == TaskStatus("running")
        assert TaskStatus.PAUSED == TaskStatus("paused")
        assert TaskStatus.COMPLETED == TaskStatus("completed")
        assert TaskStatus.FAILED == TaskStatus("failed")
        assert TaskStatus.STOPPED == TaskStatus("stopped")


class TestTaskInfoDataclass:
    """测试 TaskInfo 数据类"""

    def test_task_info_initialization(self):
        """测试 TaskInfo 初始化"""
        task_id = "test_task_123"
        name = "Test Task"
        status = TaskStatus.PENDING
        created_at = datetime.now()
        
        task_info = TaskInfo(
            task_id=task_id,
            name=name,
            status=status,
            created_at=created_at
        )
        
        assert task_info.task_id == task_id
        assert task_info.name == name
        assert task_info.status == status
        assert task_info.created_at == created_at
        assert task_info.started_at is None
        assert task_info.completed_at is None
        assert task_info.progress == 0.0
        assert task_info.metadata is None
        assert task_info.error is None

    def test_task_info_with_all_parameters(self):
        """测试 TaskInfo 带所有参数初始化"""
        task_id = "test_task_456"
        name = "Complete Test Task"
        status = TaskStatus.RUNNING
        created_at = datetime.now()
        started_at = datetime.now()
        completed_at = None
        progress = 50.0
        metadata = {"source": "test", "category": "unit"}
        error = None
        
        task_info = TaskInfo(
            task_id=task_id,
            name=name,
            status=status,
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at,
            progress=progress,
            metadata=metadata,
            error=error
        )
        
        assert task_info.task_id == task_id
        assert task_info.name == name
        assert task_info.status == status
        assert task_info.created_at == created_at
        assert task_info.started_at == started_at
        assert task_info.completed_at == completed_at
        assert task_info.progress == progress
        assert task_info.metadata == metadata
        assert task_info.error == error


class TestITaskEventListenerInterface:
    """测试 ITaskEventListener 接口"""

    def test_interface_is_abstract(self):
        """测试接口是抽象的"""
        # 尝试实例化抽象类应该失败
        with pytest.raises(TypeError):
            ITaskEventListener()

    def test_interface_methods_are_abstract(self):
        """测试接口方法是抽象的"""
        # 检查所有方法都是抽象的
        assert hasattr(ITaskEventListener.on_task_created, '__isabstractmethod__')
        assert hasattr(ITaskEventListener.on_task_started, '__isabstractmethod__')
        assert hasattr(ITaskEventListener.on_task_paused, '__isabstractmethod__')
        assert hasattr(ITaskEventListener.on_task_resumed, '__isabstractmethod__')
        assert hasattr(ITaskEventListener.on_task_stopped, '__isabstractmethod__')
        assert hasattr(ITaskEventListener.on_task_completed, '__isabstractmethod__')
        assert hasattr(ITaskEventListener.on_task_failed, '__isabstractmethod__')
        assert hasattr(ITaskEventListener.on_task_progress, '__isabstractmethod__')

        # 验证所有方法都是抽象的
        assert ITaskEventListener.on_task_created.__isabstractmethod__
        assert ITaskEventListener.on_task_started.__isabstractmethod__
        assert ITaskEventListener.on_task_paused.__isabstractmethod__
        assert ITaskEventListener.on_task_resumed.__isabstractmethod__
        assert ITaskEventListener.on_task_stopped.__isabstractmethod__
        assert ITaskEventListener.on_task_completed.__isabstractmethod__
        assert ITaskEventListener.on_task_failed.__isabstractmethod__
        assert ITaskEventListener.on_task_progress.__isabstractmethod__

    def test_concrete_implementation(self):
        """测试具体实现"""
        # 创建具体实现类
        class ConcreteTaskEventListener(ITaskEventListener):
            def on_task_created(self, task_info: TaskInfo) -> None:
                pass

            def on_task_started(self, task_info: TaskInfo) -> None:
                pass

            def on_task_paused(self, task_info: TaskInfo) -> None:
                pass

            def on_task_resumed(self, task_info: TaskInfo) -> None:
                pass

            def on_task_stopped(self, task_info: TaskInfo) -> None:
                pass

            def on_task_completed(self, task_info: TaskInfo) -> None:
                pass

            def on_task_failed(self, task_info: TaskInfo, error: Exception) -> None:
                pass

            def on_task_progress(self, task_info: TaskInfo) -> None:
                pass

        # 实例化应该成功
        listener = ConcreteTaskEventListener()
        assert isinstance(listener, ITaskEventListener)
        assert isinstance(listener, ABC)


class TestITaskManagerInterface:
    """测试 ITaskManager 接口"""

    def test_interface_is_abstract(self):
        """测试接口是抽象的"""
        # 尝试实例化抽象类应该失败
        with pytest.raises(TypeError):
            ITaskManager()

    def test_interface_methods_are_abstract(self):
        """测试接口方法是抽象的"""
        # 检查所有方法都是抽象的
        methods = [
            'create_task',
            'start_task',
            'pause_task',
            'resume_task',
            'stop_task',
            'get_task_info',
            'add_event_listener',
            'remove_event_listener'
        ]
        
        for method_name in methods:
            method = getattr(ITaskManager, method_name)
            assert hasattr(method, '__isabstractmethod__')
            assert method.__isabstractmethod__

    def test_concrete_implementation(self):
        """测试具体实现"""
        # 创建具体实现类
        class ConcreteTaskManager(ITaskManager):
            def create_task(self, name: str, task_func, metadata: Optional[dict] = None) -> str:
                return "task_id"

            def start_task(self, task_id: str) -> bool:
                return True

            def pause_task(self, task_id: str) -> bool:
                return True

            def resume_task(self, task_id: str) -> bool:
                return True

            def stop_task(self, task_id: str) -> bool:
                return True

            def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
                return None

            def add_event_listener(self, listener: ITaskEventListener) -> None:
                pass

            def remove_event_listener(self, listener: ITaskEventListener) -> None:
                pass

        # 实例化应该成功
        manager = ConcreteTaskManager()
        assert isinstance(manager, ITaskManager)
        assert isinstance(manager, ABC)

    def test_interface_method_signatures(self):
        """测试接口方法签名"""
        # 创建具体实现类来验证方法签名
        class SignatureTestTaskManager(ITaskManager):
            def create_task(self, name: str, task_func, metadata: Optional[dict] = None) -> str:
                # 验证参数类型
                assert isinstance(name, str)
                assert callable(task_func)
                if metadata is not None:
                    assert isinstance(metadata, dict)
                return "task_id"

            def start_task(self, task_id: str) -> bool:
                assert isinstance(task_id, str)
                return True

            def pause_task(self, task_id: str) -> bool:
                assert isinstance(task_id, str)
                return True

            def resume_task(self, task_id: str) -> bool:
                assert isinstance(task_id, str)
                return True

            def stop_task(self, task_id: str) -> bool:
                assert isinstance(task_id, str)
                return True

            def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
                assert isinstance(task_id, str)
                return None

            def add_event_listener(self, listener: ITaskEventListener) -> None:
                assert isinstance(listener, ITaskEventListener)

            def remove_event_listener(self, listener: ITaskEventListener) -> None:
                assert isinstance(listener, ITaskEventListener)

        manager = SignatureTestTaskManager()
        
        # 测试方法调用
        task_id = manager.create_task("test", lambda: None, {"key": "value"})
        assert task_id == "task_id"
        
        assert manager.start_task("test_id") is True
        assert manager.pause_task("test_id") is True
        assert manager.resume_task("test_id") is True
        assert manager.stop_task("test_id") is True
        assert manager.get_task_info("test_id") is None
        
        listener = Mock(spec=ITaskEventListener)
        manager.add_event_listener(listener)
        manager.remove_event_listener(listener)


class TestInterfaceContractVerification:
    """测试接口契约验证"""

    def test_task_event_listener_contract(self):
        """测试任务事件监听器契约"""
        # 创建一个实现所有方法的监听器
        mock_listener = Mock(spec=ITaskEventListener)
        
        # 验证所有必需的方法都存在
        required_methods = [
            'on_task_created',
            'on_task_started',
            'on_task_paused',
            'on_task_resumed',
            'on_task_stopped',
            'on_task_completed',
            'on_task_failed',
            'on_task_progress'
        ]
        
        for method_name in required_methods:
            assert hasattr(mock_listener, method_name)
            assert callable(getattr(mock_listener, method_name))

    def test_task_manager_contract(self):
        """测试任务管理器契约"""
        # 创建一个模拟的任务管理器
        mock_manager = Mock(spec=ITaskManager)
        
        # 验证所有必需的方法都存在
        required_methods = [
            'create_task',
            'start_task',
            'pause_task',
            'resume_task',
            'stop_task',
            'get_task_info',
            'add_event_listener',
            'remove_event_listener'
        ]
        
        for method_name in required_methods:
            assert hasattr(mock_manager, method_name)
            assert callable(getattr(mock_manager, method_name))

    def test_interface_inheritance_chain(self):
        """测试接口继承链"""
        # 验证接口继承自ABC
        assert issubclass(ITaskEventListener, ABC)
        assert issubclass(ITaskManager, ABC)

        # 验证接口方法的抽象属性
        for cls in [ITaskEventListener, ITaskManager]:
            assert hasattr(cls, '__abstractmethods__')
            assert len(cls.__abstractmethods__) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
