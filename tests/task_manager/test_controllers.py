#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Manager Controllers 测试模块

测试 TaskManager 控制器的所有方法，包括任务生命周期管理、并发安全等。
"""

import time
import threading
import pytest
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import Future

from task_manager.controllers import TaskManager, Task
from task_manager.interfaces import ITaskEventListener, TaskInfo, TaskStatus
from task_manager.exceptions import TaskNotFoundError, TaskStateError


class TestTaskManager:
    """测试 TaskManager 控制器"""

    def setup_method(self):
        """测试初始化"""
        self.task_manager = TaskManager(max_workers=5)

    def teardown_method(self):
        """测试清理"""
        self.task_manager.shutdown(wait=True)

    def test_task_manager_initialization(self):
        """测试 TaskManager 初始化"""
        assert isinstance(self.task_manager._tasks, dict)
        assert isinstance(self.task_manager._listeners, list)
        assert len(self.task_manager._tasks) == 0
        assert len(self.task_manager._listeners) == 0
        assert self.task_manager._executor is not None

    def test_create_task_with_valid_function(self):
        """测试创建有效任务"""
        def sample_task():
            return "task completed"

        task_id = self.task_manager.create_task("test_task", sample_task)
        assert task_id is not None
        assert isinstance(task_id, str)
        assert len(task_id) > 0

        # 验证任务已添加到内部字典
        assert task_id in self.task_manager._tasks
        task = self.task_manager._tasks[task_id]
        assert task.task_id == task_id
        assert task.name == "test_task"
        assert task.task_func == sample_task
        assert task.status == TaskStatus.PENDING

    def test_create_task_with_invalid_function(self):
        """测试创建无效任务"""
        with pytest.raises(ValueError, match="task_func must be callable"):
            self.task_manager.create_task("invalid_task", "not_a_function")

    def test_create_task_with_metadata(self):
        """测试创建带元数据的任务"""
        def sample_task():
            return "task completed"

        metadata = {"source": "test", "priority": "high"}
        task_id = self.task_manager.create_task("metadata_task", sample_task, metadata)

        task = self.task_manager._tasks[task_id]
        assert task.metadata == metadata

    def test_start_task_success(self):
        """测试成功启动任务"""
        def sample_task():
            time.sleep(0.01)  # 短暂延迟
            return "task completed"

        task_id = self.task_manager.create_task("start_test", sample_task)
        result = self.task_manager.start_task(task_id)
        assert result is True

        # 验证任务状态已更新
        task = self.task_manager._tasks[task_id]
        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None

    def test_start_task_not_found(self):
        """测试启动不存在的任务"""
        result = self.task_manager.start_task("non_existent_task")
        assert result is False

    def test_start_task_invalid_state(self):
        """测试启动无效状态的任务"""
        def sample_task():
            return "task completed"

        task_id = self.task_manager.create_task("invalid_state_test", sample_task)
        # 先启动任务
        self.task_manager.start_task(task_id)
        # 再次尝试启动应该失败
        result = self.task_manager.start_task(task_id)
        assert result is False

    def test_pause_task_success(self):
        """测试成功暂停任务"""
        def sample_task():
            time.sleep(0.1)
            return "task completed"

        task_id = self.task_manager.create_task("pause_test", sample_task)
        self.task_manager.start_task(task_id)
        result = self.task_manager.pause_task(task_id)
        assert result is True

        task = self.task_manager._tasks[task_id]
        assert task.status == TaskStatus.PAUSED

    def test_pause_task_not_found(self):
        """测试暂停不存在的任务"""
        result = self.task_manager.pause_task("non_existent_task")
        assert result is False

    def test_pause_task_invalid_state(self):
        """测试暂停无效状态的任务"""
        def sample_task():
            return "task completed"

        task_id = self.task_manager.create_task("invalid_pause_test", sample_task)
        # 尝试暂停未启动的任务应该失败
        result = self.task_manager.pause_task(task_id)
        assert result is False

    def test_resume_task_success(self):
        """测试成功恢复任务"""
        def sample_task():
            time.sleep(0.1)
            return "task completed"

        task_id = self.task_manager.create_task("resume_test", sample_task)
        self.task_manager.start_task(task_id)
        self.task_manager.pause_task(task_id)
        result = self.task_manager.resume_task(task_id)
        assert result is True

        task = self.task_manager._tasks[task_id]
        assert task.status == TaskStatus.RUNNING

    def test_resume_task_not_found(self):
        """测试恢复不存在的任务"""
        result = self.task_manager.resume_task("non_existent_task")
        assert result is False

    def test_resume_task_invalid_state(self):
        """测试恢复无效状态的任务"""
        def sample_task():
            return "task completed"

        task_id = self.task_manager.create_task("invalid_resume_test", sample_task)
        # 尝试恢复未暂停的任务应该失败
        result = self.task_manager.resume_task(task_id)
        assert result is False

    def test_stop_task_success(self):
        """测试成功停止任务"""
        def long_running_task():
            time.sleep(1)  # 长时间运行
            return "task completed"

        task_id = self.task_manager.create_task("stop_test", long_running_task)
        self.task_manager.start_task(task_id)
        result = self.task_manager.stop_task(task_id)
        assert result is True

        task = self.task_manager._tasks[task_id]
        assert task.status == TaskStatus.STOPPED
        assert task.completed_at is not None

    def test_stop_task_not_found(self):
        """测试停止不存在的任务"""
        result = self.task_manager.stop_task("non_existent_task")
        assert result is False

    def test_stop_task_already_completed(self):
        """测试停止已完成的任务"""
        def quick_task():
            return "quick task"

        task_id = self.task_manager.create_task("quick_test", quick_task)
        self.task_manager.start_task(task_id)
        # 等待任务完成
        time.sleep(0.05)

        result = self.task_manager.stop_task(task_id)
        assert result is False

    def test_get_task_info_success(self):
        """测试成功获取任务信息"""
        def sample_task():
            return "task completed"

        task_id = self.task_manager.create_task("info_test", sample_task)
        task_info = self.task_manager.get_task_info(task_id)
        assert task_info is not None
        assert isinstance(task_info, TaskInfo)
        assert task_info.task_id == task_id
        assert task_info.name == "info_test"
        assert task_info.status == TaskStatus.PENDING

    def test_get_task_info_not_found(self):
        """测试获取不存在的任务信息"""
        task_info = self.task_manager.get_task_info("non_existent_task")
        assert task_info is None

    def test_add_event_listener(self):
        """测试添加事件监听器"""
        listener = Mock(spec=ITaskEventListener)
        self.task_manager.add_event_listener(listener)
        assert listener in self.task_manager._listeners

    def test_add_duplicate_event_listener(self):
        """测试添加重复事件监听器"""
        listener = Mock(spec=ITaskEventListener)
        self.task_manager.add_event_listener(listener)
        # 再次添加相同的监听器
        self.task_manager.add_event_listener(listener)
        # 应该只存在一个实例
        assert self.task_manager._listeners.count(listener) == 1

    def test_remove_event_listener(self):
        """测试移除事件监听器"""
        listener = Mock(spec=ITaskEventListener)
        self.task_manager.add_event_listener(listener)
        assert listener in self.task_manager._listeners

        self.task_manager.remove_event_listener(listener)
        assert listener not in self.task_manager._listeners

    def test_remove_nonexistent_event_listener(self):
        """测试移除不存在的事件监听器"""
        listener = Mock(spec=ITaskEventListener)
        # 移除不存在的监听器不应该抛出异常
        self.task_manager.remove_event_listener(listener)

    def test_task_completion_notification(self):
        """测试任务完成通知"""
        def quick_task():
            return "quick task result"

        listener = Mock(spec=ITaskEventListener)
        self.task_manager.add_event_listener(listener)

        task_id = self.task_manager.create_task("completion_test", quick_task)
        self.task_manager.start_task(task_id)

        # 等待任务完成
        time.sleep(0.05)

        # 验证监听器被调用
        assert listener.on_task_created.called
        assert listener.on_task_started.called
        assert listener.on_task_completed.called

        # 验证传递的参数
        task_info = listener.on_task_completed.call_args[0][0]
        assert task_info.task_id == task_id
        assert task_info.status == TaskStatus.COMPLETED
        assert task_info.result == "quick task result"

    def test_task_failure_notification(self):
        """测试任务失败通知"""
        def failing_task():
            raise Exception("Task failed intentionally")

        listener = Mock(spec=ITaskEventListener)
        self.task_manager.add_event_listener(listener)

        task_id = self.task_manager.create_task("failure_test", failing_task)
        self.task_manager.start_task(task_id)

        # 等待任务失败
        time.sleep(0.05)

        # 验证监听器被调用
        assert listener.on_task_created.called
        assert listener.on_task_started.called
        assert listener.on_task_failed.called

        # 验证传递的参数
        call_args = listener.on_task_failed.call_args
        task_info = call_args[0][0]
        exception = call_args[0][1]
        assert task_info.task_id == task_id
        assert task_info.status == TaskStatus.FAILED
        assert "Task failed intentionally" in task_info.error
        assert isinstance(exception, Exception)

    def test_task_exception_handling_in_listener(self):
        """测试监听器异常处理"""
        def sample_task():
            return "task completed"

        # 创建一个会抛出异常的监听器
        bad_listener = Mock(spec=ITaskEventListener)
        bad_listener.on_task_created.side_effect = Exception("Listener error")

        # 创建一个正常的监听器
        good_listener = Mock(spec=ITaskEventListener)

        self.task_manager.add_event_listener(bad_listener)
        self.task_manager.add_event_listener(good_listener)

        # 创建任务应该不会因为监听器异常而失败
        task_id = self.task_manager.create_task("exception_test", sample_task)
        assert task_id is not None

        # 验证正常监听器被调用
        assert good_listener.on_task_created.called

    def test_shutdown_with_wait(self):
        """测试关闭任务管理器并等待任务完成"""
        def long_task():
            time.sleep(0.1)
            return "long task completed"

        task_id = self.task_manager.create_task("long_task", long_task)
        self.task_manager.start_task(task_id)

        # 关闭并等待所有任务完成
        self.task_manager.shutdown(wait=True)

        # 验证任务管理器已关闭
        # 尝试创建新任务应该失败
        with pytest.raises(RuntimeError):
            self.task_manager.create_task("new_task", long_task)


class TestTaskManagerConcurrency:
    """测试 TaskManager 并发安全"""

    def setup_method(self):
        """测试初始化"""
        self.task_manager = TaskManager(max_workers=10)

    def teardown_method(self):
        """测试清理"""
        self.task_manager.shutdown(wait=True)

    def test_concurrent_task_creation(self):
        """测试并发任务创建"""
        def sample_task():
            time.sleep(0.01)
            return "task completed"

        # 并发创建多个任务
        threads = []
        task_ids = []

        def create_task():
            task_id = self.task_manager.create_task("concurrent_task", sample_task)
            task_ids.append(task_id)

        # 创建10个线程并发创建任务
        for _ in range(10):
            thread = threading.Thread(target=create_task)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有任务都已创建
        assert len(task_ids) == 10
        for task_id in task_ids:
            assert task_id in self.task_manager._tasks

    def test_concurrent_task_execution(self):
        """测试并发任务执行"""
        results = []

        def sample_task(task_number):
            time.sleep(0.01)
            result = f"task_{task_number}_completed"
            results.append(result)
            return result

        # 创建多个任务
        task_ids = []
        for i in range(10):
            task_id = self.task_manager.create_task(f"concurrent_exec_{i}", 
                                                  lambda n=i: sample_task(n))
            task_ids.append(task_id)

        # 并发启动所有任务
        threads = []
        for task_id in task_ids:
            thread = threading.Thread(target=self.task_manager.start_task, args=(task_id,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 等待任务完成
        time.sleep(0.2)

        # 验证所有任务都已完成
        completed_count = 0
        for task_id in task_ids:
            task_info = self.task_manager.get_task_info(task_id)
            if task_info and task_info.status == TaskStatus.COMPLETED:
                completed_count += 1

        assert completed_count == 10
        assert len(results) == 10

    def test_concurrent_task_operations(self):
        """测试并发任务操作"""
        def long_running_task():
            time.sleep(0.1)
            return "long task completed"

        task_id = self.task_manager.create_task("concurrent_ops", long_running_task)
        self.task_manager.start_task(task_id)

        # 并发执行多个操作
        results = []

        def get_task_info():
            task_info = self.task_manager.get_task_info(task_id)
            results.append(task_info is not None)

        def pause_task():
            result = self.task_manager.pause_task(task_id)
            results.append(result)

        def resume_task():
            result = self.task_manager.resume_task(task_id)
            results.append(result)

        # 创建并发线程
        threads = []
        for _ in range(5):
            thread1 = threading.Thread(target=get_task_info)
            thread2 = threading.Thread(target=pause_task)
            thread3 = threading.Thread(target=resume_task)
            threads.extend([thread1, thread2, thread3])

        # 启动所有线程
        for thread in threads:
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证没有异常发生
        assert len(results) == 15  # 5次get_info + 5次pause + 5次resume


class TestTaskManagerPerformance:
    """测试 TaskManager 性能"""

    def setup_method(self):
        """测试初始化"""
        self.task_manager = TaskManager(max_workers=5)

    def teardown_method(self):
        """测试清理"""
        self.task_manager.shutdown(wait=True)

    def test_task_creation_performance(self):
        """测试任务创建性能"""
        def sample_task():
            return "task completed"

        iterations = 1000
        start_time = time.perf_counter()

        task_ids = []
        for _ in range(iterations):
            task_id = self.task_manager.create_task("perf_test", sample_task)
            task_ids.append(task_id)

        end_time = time.perf_counter()
        total_time = end_time - start_time
        avg_time = (total_time / iterations) * 1000  # 转换为毫秒

        print(f"任务创建平均时间: {avg_time:.6f}ms")
        assert avg_time < 1.0, "任务创建应该小于1ms"

        # 验证所有任务都已创建
        assert len(task_ids) == iterations

    def test_task_operation_performance(self):
        """测试任务操作性能"""
        def sample_task():
            return "task completed"

        task_id = self.task_manager.create_task("op_perf_test", sample_task)

        operations = [
            ("start", lambda: self.task_manager.start_task(task_id)),
            ("get_info", lambda: self.task_manager.get_task_info(task_id)),
        ]

        for op_name, op_func in operations:
            iterations = 1000
            start_time = time.perf_counter()

            for _ in range(iterations):
                result = op_func()

            end_time = time.perf_counter()
            total_time = end_time - start_time
            avg_time = (total_time / iterations) * 1000  # 转换为毫秒

            print(f"{op_name} 操作平均时间: {avg_time:.6f}ms")
            assert avg_time < 1.0, f"{op_name} 操作应该小于1ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
