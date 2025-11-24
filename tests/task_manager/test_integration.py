#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Manager Integration 测试模块

测试模块间集成，包括完整的任务生命周期、配置集成、异常处理等。
"""

import time
import threading
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from task_manager.models import TaskStatus, TaskProgress, TaskConfig, TaskInfo
from task_manager.controllers import TaskManager
from task_manager.interfaces import ITaskEventListener
from task_manager.exceptions import (
    TaskCreationError,
    TaskExecutionError,
    TaskNotFoundError,
    TaskStateError,
    TaskTimeoutError
)
from task_manager.config import TaskManagerConfig, get_config, set_config
from task_manager.mixins import TaskControlMixin


class TestTaskManagerIntegration:
    """测试 TaskManager 完整集成"""

    def setup_method(self):
        """测试初始化"""
        self.task_manager = TaskManager(max_workers=5)

    def teardown_method(self):
        """测试清理"""
        self.task_manager.shutdown(wait=True)

    def test_complete_task_lifecycle(self):
        """测试完整的任务生命周期"""
        # 创建任务
        def sample_task():
            time.sleep(0.01)  # 短暂延迟模拟工作
            return "task completed successfully"

        task_id = self.task_manager.create_task("lifecycle_test", sample_task)
        assert task_id is not None

        # 验证初始状态
        task_info = self.task_manager.get_task_info(task_id)
        assert task_info.status == TaskStatus.PENDING

        # 启动任务
        assert self.task_manager.start_task(task_id) is True

        # 验证运行状态
        task_info = self.task_manager.get_task_info(task_id)
        assert task_info.status == TaskStatus.RUNNING

        # 等待任务完成
        time.sleep(0.05)

        # 验证完成状态
        task_info = self.task_manager.get_task_info(task_id)
        assert task_info.status == TaskStatus.COMPLETED
        assert task_info.result == "task completed successfully"
        assert task_info.progress == 100.0

    def test_task_with_config_integration(self):
        """测试带配置的任务集成"""
        def configurable_task():
            return "configured task result"

        # 创建带配置的任务
        task_config = TaskConfig(
            timeout=30,
            retry_count=2,
            priority=5,
            metadata={"source": "integration_test"}
        )

        # 注意：当前实现中 TaskManager.create_task 不直接接受 TaskConfig
        # 但可以通过 metadata 传递配置信息
        task_id = self.task_manager.create_task(
            "config_test",
            configurable_task,
            metadata={"config": task_config.to_dict()}
        )

        assert self.task_manager.start_task(task_id) is True

        # 等待任务完成
        time.sleep(0.05)

        task_info = self.task_manager.get_task_info(task_id)
        assert task_info.status == TaskStatus.COMPLETED
        assert task_info.metadata is not None

    def test_task_failure_integration(self):
        """测试任务失败集成"""
        def failing_task():
            raise ValueError("Intentional failure for testing")

        task_id = self.task_manager.create_task("failure_test", failing_task)
        assert self.task_manager.start_task(task_id) is True

        # 等待任务失败
        time.sleep(0.05)

        task_info = self.task_manager.get_task_info(task_id)
        assert task_info.status == TaskStatus.FAILED
        assert task_info.error is not None
        assert "Intentional failure" in task_info.error

    def test_task_pause_resume_integration(self):
        """测试任务暂停恢复集成"""
        def long_running_task():
            time.sleep(0.1)
            return "long running task completed"

        task_id = self.task_manager.create_task("pause_resume_test", long_running_task)
        assert self.task_manager.start_task(task_id) is True

        # 暂停任务
        assert self.task_manager.pause_task(task_id) is True

        task_info = self.task_manager.get_task_info(task_id)
        assert task_info.status == TaskStatus.PAUSED

        # 恢复任务
        assert self.task_manager.resume_task(task_id) is True

        task_info = self.task_manager.get_task_info(task_id)
        assert task_info.status == TaskStatus.RUNNING

        # 等待任务完成
        time.sleep(0.15)

        task_info = self.task_manager.get_task_info(task_id)
        assert task_info.status == TaskStatus.COMPLETED

    def test_event_listener_integration(self):
        """测试事件监听器集成"""
        events = []

        class TestEventListener(ITaskEventListener):
            def on_task_created(self, task_info: TaskInfo) -> None:
                events.append(("created", task_info.task_id))

            def on_task_started(self, task_info: TaskInfo) -> None:
                events.append(("started", task_info.task_id))

            def on_task_completed(self, task_info: TaskInfo) -> None:
                events.append(("completed", task_info.task_id))

            def on_task_failed(self, task_info: TaskInfo, error: Exception) -> None:
                events.append(("failed", task_info.task_id))

            def on_task_paused(self, task_info: TaskInfo) -> None:
                events.append(("paused", task_info.task_id))

            def on_task_resumed(self, task_info: TaskInfo) -> None:
                events.append(("resumed", task_info.task_id))

            def on_task_stopped(self, task_info: TaskInfo) -> None:
                events.append(("stopped", task_info.task_id))

            def on_task_progress(self, task_info: TaskInfo) -> None:
                events.append(("progress", task_info.task_id))

        listener = TestEventListener()
        self.task_manager.add_event_listener(listener)

        def sample_task():
            return "listener test completed"

        # 创建并启动任务
        task_id = self.task_manager.create_task("listener_test", sample_task)
        self.task_manager.start_task(task_id)

        # 等待任务完成
        time.sleep(0.05)

        # 验证事件被触发
        event_types = [event[0] for event in events]
        assert "created" in event_types
        assert "started" in event_types
        assert "completed" in event_types

        # 验证任务ID一致
        task_ids = [event[1] for event in events]
        assert all(task_id == tid for tid in task_ids)

    def test_multiple_tasks_integration(self):
        """测试多个任务集成"""
        results = []

        def create_task_func(task_number):
            def task_func():
                time.sleep(0.01 * task_number)  # 不同延迟
                result = f"task_{task_number}_result"
                results.append(result)
                return result
            return task_func

        # 创建多个任务
        task_ids = []
        for i in range(5):
            task_id = self.task_manager.create_task(
                f"multi_task_{i}",
                create_task_func(i)
            )
            task_ids.append(task_id)

        # 启动所有任务
        for task_id in task_ids:
            assert self.task_manager.start_task(task_id) is True

        # 等待所有任务完成
        time.sleep(0.1)

        # 验证所有任务都已完成
        for task_id in task_ids:
            task_info = self.task_manager.get_task_info(task_id)
            assert task_info.status == TaskStatus.COMPLETED

        # 验证所有结果都已收集
        assert len(results) == 5
        for i in range(5):
            assert f"task_{i}_result" in results


class TestTaskManagerWithConfigIntegration:
    """测试 TaskManager 与配置集成"""

    def setup_method(self):
        """测试初始化"""
        # 保存原始配置
        self.original_config = get_config()
        # 设置测试配置
        test_config = TaskManagerConfig(
            max_concurrent_tasks=3,
            max_task_queue_size=50,
            persist_tasks=False,
            log_level="DEBUG"
        )
        set_config(test_config)
        self.task_manager = TaskManager(max_workers=3)

    def teardown_method(self):
        """测试清理"""
        self.task_manager.shutdown(wait=True)
        # 恢复原始配置
        set_config(self.original_config)

    def test_config_integration(self):
        """测试配置集成"""
        # 验证配置已应用
        config = get_config()
        assert config.max_concurrent_tasks == 3
        assert config.log_level == "DEBUG"

        # 创建超过最大并发数的任务来测试限制
        def sample_task():
            time.sleep(0.05)
            return "config test result"

        task_ids = []
        for i in range(5):  # 超过最大并发数3
            task_id = self.task_manager.create_task(f"config_test_{i}", sample_task)
            task_ids.append(task_id)
            self.task_manager.start_task(task_id)

        # 等待任务完成
        time.sleep(0.2)

        # 验证所有任务都已完成
        completed_count = 0
        for task_id in task_ids:
            task_info = self.task_manager.get_task_info(task_id)
            if task_info and task_info.status == TaskStatus.COMPLETED:
                completed_count += 1

        assert completed_count == 5


class TestTaskManagerExceptionIntegration:
    """测试 TaskManager 异常处理集成"""

    def setup_method(self):
        """测试初始化"""
        self.task_manager = TaskManager(max_workers=2)

    def teardown_method(self):
        """测试清理"""
        self.task_manager.shutdown(wait=True)

    def test_task_not_found_exception(self):
        """测试任务未找到异常处理"""
        # 尝试操作不存在的任务
        assert self.task_manager.start_task("non_existent_task") is False
        assert self.task_manager.pause_task("non_existent_task") is False
        assert self.task_manager.resume_task("non_existent_task") is False
        assert self.task_manager.stop_task("non_existent_task") is False
        assert self.task_manager.get_task_info("non_existent_task") is None

    def test_invalid_task_creation(self):
        """测试无效任务创建"""
        # 尝试创建无效任务
        with pytest.raises(ValueError, match="task_func must be callable"):
            self.task_manager.create_task("invalid_task", "not_a_function")

    def test_task_state_exceptions(self):
        """测试任务状态异常"""
        def sample_task():
            return "state test result"

        task_id = self.task_manager.create_task("state_test", sample_task)

        # 尝试暂停未运行的任务应该失败
        assert self.task_manager.pause_task(task_id) is False

        # 启动任务
        assert self.task_manager.start_task(task_id) is True

        # 再次启动应该失败
        assert self.task_manager.start_task(task_id) is False


class TestTaskControlMixinIntegration:
    """测试 TaskControlMixin 集成"""

    def test_task_control_integration(self):
        """测试任务控制集成"""
        class ControlledTask(TaskControlMixin):
            def __init__(self):
                super().__init__()
                self.progress_reports = []

            def execute_long_task(self, task_id):
                """执行长时间任务，支持控制点检查"""
                for i in range(10):
                    # 检查控制点
                    if not self._check_task_control(task_id):
                        return "task stopped"
                    
                    # 模拟工作
                    time.sleep(0.001)
                    
                    # 报告进度
                    progress = (i + 1) * 10
                    self._report_task_progress(task_id, progress, f"Step {i+1}")
                    self.progress_reports.append(progress)
                
                return "task completed"

        controlled_task = ControlledTask()
        task_id = "controlled_task_123"

        # 执行任务
        result = controlled_task.execute_long_task(task_id)

        assert result == "task completed"
        assert len(controlled_task.progress_reports) == 10
        assert controlled_task.progress_reports[-1] == 100

    def test_task_control_stop_integration(self):
        """测试任务控制停止集成"""
        class ControlledTask(TaskControlMixin):
            def __init__(self):
                super().__init__()

            def execute_long_task(self, task_id):
                """执行长时间任务，支持控制点检查"""
                for i in range(100):  # 更多步骤
                    # 检查控制点
                    if not self._check_task_control(task_id):
                        return "task stopped"
                    
                    # 模拟工作
                    time.sleep(0.001)
                
                return "task completed"

        controlled_task = ControlledTask()
        task_id = "stop_controlled_task"

        # 在另一个线程中设置停止标志
        def stop_task():
            time.sleep(0.01)  # 短暂延迟后停止
            controlled_task._set_task_stop_flag(task_id)

        stop_thread = threading.Thread(target=stop_task)
        stop_thread.start()

        # 执行任务
        result = controlled_task.execute_long_task(task_id)

        stop_thread.join()

        assert result == "task stopped"


class TestCrossModuleIntegration:
    """测试跨模块集成"""

    def test_models_controllers_integration(self):
        """测试模型与控制器集成"""
        task_manager = TaskManager(max_workers=2)

        def sample_task():
            time.sleep(0.01)
            return {"result": "integration success", "value": 42}

        task_id = task_manager.create_task("model_controller_test", sample_task)

        # 验证创建的 TaskInfo 符合模型定义
        task_info = task_manager.get_task_info(task_id)
        assert isinstance(task_info, TaskInfo)
        assert isinstance(task_info.status, TaskStatus)
        assert isinstance(task_info.progress, float)

        # 启动并完成任务
        task_manager.start_task(task_id)
        time.sleep(0.05)

        # 验证完成的 TaskInfo
        task_info = task_manager.get_task_info(task_id)
        assert task_info.status == TaskStatus.COMPLETED
        assert task_info.result == {"result": "integration success", "value": 42}
        assert task_info.progress == 100.0

        task_manager.shutdown(wait=True)

    def test_interfaces_implementation_integration(self):
        """测试接口实现集成"""
        # 验证 TaskManager 实现了 ITaskManager 接口
        task_manager = TaskManager()
        
        # 检查所有必需的方法都存在且可调用
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
            assert hasattr(task_manager, method_name)
            assert callable(getattr(task_manager, method_name))

        task_manager.shutdown(wait=True)

    def test_exceptions_models_integration(self):
        """测试异常与模型集成"""
        # 验证异常消息包含正确的任务信息
        task_id = "exception_integration_test"
        
        try:
            raise TaskNotFoundError(task_id)
        except TaskNotFoundError as e:
            assert str(e) == f"Task with ID '{task_id}' not found"
            assert e.task_id == task_id

        # 验证超时异常消息
        try:
            raise TaskTimeoutError(task_id=task_id, timeout=30)
        except TaskTimeoutError as e:
            assert "timeout" in e.message.lower()
            assert "30 seconds" in e.message
            assert e.task_id == task_id


class TestPerformanceIntegration:
    """测试性能集成"""

    def test_task_creation_performance_integration(self):
        """测试任务创建性能集成"""
        task_manager = TaskManager(max_workers=10)

        def sample_task():
            return "perf test result"

        # 批量创建任务测试性能
        iterations = 100
        start_time = time.perf_counter()

        task_ids = []
        for i in range(iterations):
            task_id = task_manager.create_task(f"perf_test_{i}", sample_task)
            task_ids.append(task_id)

        end_time = time.perf_counter()
        avg_time = ((end_time - start_time) / iterations) * 1000  # 转换为毫秒

        print(f"集成任务创建平均时间: {avg_time:.6f}ms")
        assert avg_time < 2.0, "集成任务创建应该小于2ms"

        # 清理
        task_manager.shutdown(wait=True)

    def test_concurrent_task_execution_integration(self):
        """测试并发任务执行集成"""
        task_manager = TaskManager(max_workers=20)
        results = []

        def create_task_func(task_number):
            def task_func():
                time.sleep(0.01)  # 短暂延迟
                result = f"concurrent_{task_number}"
                results.append(result)
                return result
            return task_func

        # 创建并发任务
        start_time = time.perf_counter()
        
        task_ids = []
        for i in range(50):  # 50个并发任务
            task_id = task_manager.create_task(f"concurrent_test_{i}", create_task_func(i))
            task_ids.append(task_id)
            task_manager.start_task(task_id)

        # 等待所有任务完成
        time.sleep(0.2)

        end_time = time.perf_counter()
        total_time = end_time - start_time

        print(f"50个并发任务完成耗时: {total_time:.6f}秒")

        # 验证所有任务都已完成
        completed_count = 0
        for task_id in task_ids:
            task_info = task_manager.get_task_info(task_id)
            if task_info and task_info.status == TaskStatus.COMPLETED:
                completed_count += 1

        assert completed_count == 50
        assert len(results) == 50

        # 清理
        task_manager.shutdown(wait=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
