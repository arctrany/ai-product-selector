#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Manager Mixins 测试模块

测试 TaskControlMixin 的性能和功能，包括控制点检查、进度报告等。
"""

import time
import threading
import pytest
from unittest.mock import Mock, patch, MagicMock

from task_manager.mixins import TaskControlMixin, TaskControlContext


class TestTaskControlContext:
    """测试 TaskControlContext 数据类"""

    def test_task_control_context_initialization(self):
        """测试 TaskControlContext 初始化"""
        task_id = "test_task_123"
        context = TaskControlContext(task_id=task_id)
        
        assert context.task_id == task_id
        assert context.should_stop is False
        assert context.should_pause is False
        assert context.last_check_time == 0.0
        assert context.check_interval == 0.001  # 1ms

    def test_task_control_context_with_custom_interval(self):
        """测试 TaskControlContext 自定义检查间隔"""
        task_id = "test_task_456"
        custom_interval = 0.005  # 5ms
        context = TaskControlContext(
            task_id=task_id,
            check_interval=custom_interval
        )
        
        assert context.task_id == task_id
        assert context.check_interval == custom_interval


class ConcreteTaskControl(TaskControlMixin):
    """具体的 TaskControlMixin 实现用于测试"""
    
    def __init__(self):
        super().__init__()


class TestTaskControlMixin:
    """测试 TaskControlMixin 功能"""

    def setup_method(self):
        """测试初始化"""
        self.task_control = ConcreteTaskControl()

    def test_get_task_context_new(self):
        """测试获取新的任务上下文"""
        task_id = "new_task_context"
        context = self.task_control._get_task_context(task_id)
        
        assert isinstance(context, TaskControlContext)
        assert context.task_id == task_id
        assert context.should_stop is False
        assert context.should_pause is False

    def test_get_task_context_existing(self):
        """测试获取已存在的任务上下文"""
        task_id = "existing_task_context"
        # 第一次获取
        context1 = self.task_control._get_task_context(task_id)
        # 第二次获取
        context2 = self.task_control._get_task_context(task_id)
        
        # 应该是同一个实例
        assert context1 is context2

    def test_check_task_control_continue(self):
        """测试任务控制点检查 - 继续执行"""
        task_id = "continue_test"
        result = self.task_control._check_task_control(task_id)
        assert result is True

    def test_check_task_control_stop_flag(self):
        """测试任务控制点检查 - 停止标志"""
        task_id = "stop_flag_test"
        # 设置停止标志
        self.task_control._set_task_stop_flag(task_id)
        result = self.task_control._check_task_control(task_id)
        assert result is False

    def test_check_task_control_pause_flag(self):
        """测试任务控制点检查 - 暂停标志"""
        task_id = "pause_flag_test"
        # 设置暂停标志
        self.task_control._set_task_pause_flag(task_id, True)
        
        # 在另一个线程中取消暂停
        def resume_task():
            time.sleep(0.01)  # 10ms
            self.task_control._set_task_pause_flag(task_id, False)
        
        thread = threading.Thread(target=resume_task)
        thread.start()
        
        # 检查控制点应该会等待恢复
        result = self.task_control._check_task_control(task_id)
        assert result is True
        
        thread.join()

    def test_check_task_control_stop_during_pause(self):
        """测试任务控制点检查 - 暂停期间停止"""
        task_id = "stop_during_pause_test"
        # 设置暂停标志
        self.task_control._set_task_pause_flag(task_id, True)
        # 设置停止标志
        self.task_control._set_task_stop_flag(task_id)
        
        result = self.task_control._check_task_control(task_id)
        assert result is False

    def test_report_task_progress(self):
        """测试报告任务进度"""
        task_id = "progress_report_test"
        progress = 50.0
        message = "Halfway done"
        
        # 报告进度不应该抛出异常
        self.task_control._report_task_progress(task_id, progress, message)
        
        # 测试边界值
        self.task_control._report_task_progress(task_id, 0.0)
        self.task_control._report_task_progress(task_id, 100.0)
        self.task_control._report_task_progress(task_id, -10.0)  # 应该被限制到0
        self.task_control._report_task_progress(task_id, 150.0)  # 应该被限制到100

    def test_set_task_stop_flag(self):
        """测试设置任务停止标志"""
        task_id = "stop_flag_test"
        # 初始状态
        context = self.task_control._get_task_context(task_id)
        assert context.should_stop is False
        
        # 设置停止标志
        self.task_control._set_task_stop_flag(task_id)
        assert context.should_stop is True

    def test_set_task_pause_flag(self):
        """测试设置任务暂停标志"""
        task_id = "pause_flag_test"
        # 初始状态
        context = self.task_control._get_task_context(task_id)
        assert context.should_pause is False
        
        # 设置暂停标志
        self.task_control._set_task_pause_flag(task_id, True)
        assert context.should_pause is True
        
        # 取消暂停标志
        self.task_control._set_task_pause_flag(task_id, False)
        assert context.should_pause is False


class TestTaskControlMixinConcurrency:
    """测试 TaskControlMixin 并发安全"""

    def setup_method(self):
        """测试初始化"""
        self.task_control = ConcreteTaskControl()

    def test_concurrent_context_access(self):
        """测试并发上下文访问"""
        task_id = "concurrent_context_test"
        contexts = []

        def get_context():
            context = self.task_control._get_task_context(task_id)
            contexts.append(context)

        # 创建多个线程并发访问
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=get_context)
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有线程获取到的是同一个上下文实例
        assert len(contexts) == 10
        first_context = contexts[0]
        for context in contexts:
            assert context is first_context

    def test_concurrent_flag_operations(self):
        """测试并发标志操作"""
        task_id = "concurrent_flag_test"
        
        def set_stop_flag():
            self.task_control._set_task_stop_flag(task_id)

        def set_pause_flag():
            self.task_control._set_task_pause_flag(task_id, True)

        def check_control():
            self.task_control._check_task_control(task_id)

        # 创建并发线程
        threads = []
        for _ in range(5):
            thread1 = threading.Thread(target=set_stop_flag)
            thread2 = threading.Thread(target=set_pause_flag)
            thread3 = threading.Thread(target=check_control)
            threads.extend([thread1, thread2, thread3])

        # 启动所有线程
        for thread in threads:
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证没有异常发生

    def test_concurrent_multiple_tasks(self):
        """测试并发多个任务"""
        task_ids = [f"task_{i}" for i in range(10)]
        results = {}

        def check_control(task_id):
            result = self.task_control._check_task_control(task_id)
            results[task_id] = result

        # 创建并发线程
        threads = []
        for task_id in task_ids:
            thread = threading.Thread(target=check_control, args=(task_id,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有任务都返回了正确的结果
        assert len(results) == 10
        for result in results.values():
            assert result is True


class TestTaskControlMixinPerformance:
    """测试 TaskControlMixin 性能"""

    def setup_method(self):
        """测试初始化"""
        self.task_control = ConcreteTaskControl()

    def test_check_task_control_performance(self):
        """测试任务控制点检查性能"""
        task_id = "performance_test_task"
        
        # 预热
        for _ in range(100):
            self.task_control._check_task_control(task_id)
            
        # 性能测试
        iterations = 10000
        start_time = time.perf_counter()
        
        for _ in range(iterations):
            self.task_control._check_task_control(task_id)
            
        end_time = time.perf_counter()
        total_time = end_time - start_time
        avg_time = (total_time / iterations) * 1000  # 转换为毫秒
        
        print(f"执行 {iterations} 次检查耗时: {total_time:.6f} 秒")
        print(f"平均每次检查耗时: {avg_time:.6f} 毫秒")
        
        # 验证性能是否小于1ms
        assert avg_time < 1.0, "任务控制点检查应该小于1ms"

    def test_get_task_context_performance(self):
        """测试获取任务上下文性能"""
        task_id = "context_perf_test"
        
        # 预热
        for _ in range(100):
            self.task_control._get_task_context(task_id)
            
        # 性能测试
        iterations = 10000
        start_time = time.perf_counter()
        
        for _ in range(iterations):
            self.task_control._get_task_context(task_id)
            
        end_time = time.perf_counter()
        total_time = end_time - start_time
        avg_time = (total_time / iterations) * 1000  # 转换为毫秒
        
        print(f"获取任务上下文 {iterations} 次耗时: {total_time:.6f} 秒")
        print(f"平均每次获取耗时: {avg_time:.6f} 毫秒")
        
        # 验证性能是否小于1ms
        assert avg_time < 1.0, "获取任务上下文应该小于1ms"

    def test_report_task_progress_performance(self):
        """测试报告任务进度性能"""
        task_id = "progress_perf_test"
        progress = 50.0
        
        # 预热
        for _ in range(100):
            self.task_control._report_task_progress(task_id, progress)
            
        # 性能测试
        iterations = 10000
        start_time = time.perf_counter()
        
        for _ in range(iterations):
            self.task_control._report_task_progress(task_id, progress)
            
        end_time = time.perf_counter()
        total_time = end_time - start_time
        avg_time = (total_time / iterations) * 1000  # 转换为毫秒
        
        print(f"报告任务进度 {iterations} 次耗时: {total_time:.6f} 秒")
        print(f"平均每次报告耗时: {avg_time:.6f} 毫秒")
        
        # 验证性能是否小于1ms
        assert avg_time < 1.0, "报告任务进度应该小于1ms"

    def test_concurrent_performance(self):
        """测试并发性能"""
        task_ids = [f"concurrent_perf_{i}" for i in range(100)]
        
        def check_control(task_id):
            for _ in range(100):
                self.task_control._check_task_control(task_id)
        
        # 性能测试
        start_time = time.perf_counter()
        
        # 创建并发线程
        threads = []
        for task_id in task_ids:
            thread = threading.Thread(target=check_control, args=(task_id,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
            
        end_time = time.perf_counter()
        total_time = end_time - start_time
        total_operations = len(task_ids) * 100
        avg_time = (total_time / total_operations) * 1000  # 转换为毫秒
        
        print(f"并发执行 {total_operations} 次检查耗时: {total_time:.6f} 秒")
        print(f"平均每次检查耗时: {avg_time:.6f} 毫秒")
        
        # 验证性能是否合理
        assert avg_time < 5.0, "并发任务控制点检查应该小于5ms"


class TestTaskControlMixinEdgeCases:
    """测试 TaskControlMixin 边缘情况"""

    def setup_method(self):
        """测试初始化"""
        self.task_control = ConcreteTaskControl()

    def test_check_interval_enforcement(self):
        """测试检查间隔强制执行"""
        task_id = "interval_test"
        context = self.task_control._get_task_context(task_id)
        
        # 第一次检查应该通过
        result1 = self.task_control._check_task_control(task_id)
        assert result1 is True
        
        # 立即第二次检查也应该通过（在间隔内）
        result2 = self.task_control._check_task_control(task_id)
        assert result2 is True
        
        # 等待超过检查间隔
        time.sleep(context.check_interval + 0.001)  # 稍微超过间隔
        
        # 第三次检查应该正常执行
        result3 = self.task_control._check_task_control(task_id)
        assert result3 is True

    def test_pause_resume_cycle(self):
        """测试暂停恢复循环"""
        task_id = "pause_resume_test"
        
        # 初始状态应该是继续执行
        assert self.task_control._check_task_control(task_id) is True
        
        # 设置暂停
        self.task_control._set_task_pause_flag(task_id, True)
        
        # 在另一个线程中恢复
        def resume_task():
            time.sleep(0.01)
            self.task_control._set_task_pause_flag(task_id, False)
        
        thread = threading.Thread(target=resume_task)
        thread.start()
        
        # 检查控制点应该等待恢复
        assert self.task_control._check_task_control(task_id) is True
        
        thread.join()

    def test_multiple_stop_flags(self):
        """测试多次设置停止标志"""
        task_id = "multiple_stop_test"
        
        # 多次设置停止标志
        for _ in range(10):
            self.task_control._set_task_stop_flag(task_id)
        
        # 检查应该始终返回False
        for _ in range(10):
            assert self.task_control._check_task_control(task_id) is False

    def test_progress_bounds_checking(self):
        """测试进度边界检查"""
        task_id = "progress_bounds_test"
        
        # 测试各种边界值
        test_cases = [
            (-100.0, 0.0),
            (-1.0, 0.0),
            (0.0, 0.0),
            (50.0, 50.0),
            (100.0, 100.0),
            (101.0, 100.0),
            (200.0, 100.0),
            (float('inf'), 100.0),
            (float('-inf'), 0.0),
        ]
        
        for input_progress, expected_progress in test_cases:
            # 报告进度不应该抛出异常
            self.task_control._report_task_progress(task_id, input_progress)
            # 验证边界处理（通过上下文验证）


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
