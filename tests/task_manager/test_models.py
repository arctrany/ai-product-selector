#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Manager Models 测试模块

测试 TaskStatus、TaskProgress、TaskConfig、TaskInfo 等数据模型的功能和性能。
"""

import time
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from task_manager.models import TaskStatus, TaskProgress, TaskConfig, TaskInfo


class TestTaskStatus:
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


class TestTaskProgress:
    """测试 TaskProgress 数据模型"""

    def test_task_progress_initialization(self):
        """测试 TaskProgress 初始化"""
        progress = TaskProgress()
        assert progress.percentage == 0.0
        assert progress.current_step == ""
        assert progress.total_steps == 0
        assert progress.completed_steps == 0
        assert progress.processed_items == 0
        assert progress.total_items == 0
        assert progress.step_start_time is None
        assert progress.step_duration == 0.0

    def test_task_progress_update_step(self):
        """测试 TaskProgress 更新步骤"""
        progress = TaskProgress()
        
        # 第一次更新步骤
        progress.update_step("step1")
        assert progress.current_step == "step1"
        assert progress.step_start_time is not None
        
        # 记录第一次更新的时间
        first_update_time = progress.step_start_time
        
        # 等待一小段时间后再次更新
        time.sleep(0.001)  # 等待1ms
        progress.update_step("step2")
        assert progress.current_step == "step2"
        assert progress.step_start_time is not None
        assert progress.step_start_time > first_update_time
        # 验证前一步骤的持续时间已计算
        assert progress.step_duration > 0

    def test_task_progress_calculate_percentage_with_items(self):
        """测试基于项目数的百分比计算"""
        progress = TaskProgress()
        progress.processed_items = 50
        progress.total_items = 100
        percentage = progress.calculate_percentage()
        assert percentage == 50.0
        assert progress.percentage == 50.0

    def test_task_progress_calculate_percentage_with_steps(self):
        """测试基于步骤数的百分比计算"""
        progress = TaskProgress()
        progress.completed_steps = 3
        progress.total_steps = 10
        percentage = progress.calculate_percentage()
        assert percentage == 30.0
        assert progress.percentage == 30.0

    def test_task_progress_calculate_percentage_no_data(self):
        """测试无数据时的百分比计算"""
        progress = TaskProgress()
        percentage = progress.calculate_percentage()
        assert percentage == 0.0
        assert progress.percentage == 0.0

    def test_task_progress_calculate_percentage_zero_division(self):
        """测试零除错误处理"""
        progress = TaskProgress()
        progress.total_items = 0
        progress.total_steps = 0
        percentage = progress.calculate_percentage()
        assert percentage == 0.0
        assert progress.percentage == 0.0


class TestTaskConfig:
    """测试 TaskConfig 数据模型"""

    def test_task_config_initialization(self):
        """测试 TaskConfig 初始化"""
        config = TaskConfig()
        assert config.timeout is None
        assert config.retry_count == 0
        assert config.priority == 0
        assert config.max_concurrent == 1
        assert config.thread_safe is True
        assert config.allow_pause is True
        assert config.auto_cleanup is True
        assert config.metadata == {}

    def test_task_config_with_parameters(self):
        """测试 TaskConfig 带参数初始化"""
        metadata = {"key": "value", "priority": "high"}
        config = TaskConfig(
            timeout=30,
            retry_count=3,
            priority=5,
            max_concurrent=10,
            thread_safe=False,
            allow_pause=False,
            auto_cleanup=False,
            metadata=metadata
        )
        assert config.timeout == 30
        assert config.retry_count == 3
        assert config.priority == 5
        assert config.max_concurrent == 10
        assert config.thread_safe is False
        assert config.allow_pause is False
        assert config.auto_cleanup is False
        assert config.metadata == metadata

    def test_task_config_default_factory(self):
        """测试 TaskConfig 默认工厂函数"""
        config1 = TaskConfig()
        config2 = TaskConfig()
        # 确保每个实例都有独立的 metadata 字典
        assert config1.metadata is not config2.metadata


class TestTaskInfo:
    """测试 TaskInfo 数据模型"""

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
        # 验证默认值
        assert isinstance(task_info.progress, TaskProgress)
        assert isinstance(task_info.config, TaskConfig)
        assert task_info.metadata is None
        assert task_info.error is None
        assert task_info.result is None

    def test_task_info_with_all_parameters(self):
        """测试 TaskInfo 带所有参数初始化"""
        task_id = "test_task_456"
        name = "Complete Test Task"
        status = TaskStatus.RUNNING
        created_at = datetime.now()
        started_at = datetime.now()
        completed_at = None
        progress = TaskProgress(percentage=50.0, current_step="processing")
        config = TaskConfig(timeout=60, retry_count=2)
        metadata = {"source": "test", "category": "unit"}
        error = None
        result = {"data": "test_result"}
        
        task_info = TaskInfo(
            task_id=task_id,
            name=name,
            status=status,
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at,
            progress=progress,
            config=config,
            metadata=metadata,
            error=error,
            result=result
        )
        
        assert task_info.task_id == task_id
        assert task_info.name == name
        assert task_info.status == status
        assert task_info.created_at == created_at
        assert task_info.started_at == started_at
        assert task_info.completed_at == completed_at
        assert task_info.progress == progress
        assert task_info.config == config
        assert task_info.metadata == metadata
        assert task_info.error == error
        assert task_info.result == result


# 性能测试
class TestTaskModelsPerformance:
    """测试任务模型性能"""

    def test_task_status_performance(self):
        """测试 TaskStatus 性能"""
        iterations = 100000
        
        start_time = time.perf_counter()
        for _ in range(iterations):
            status = TaskStatus.PENDING
            _ = status.value
        end_time = time.perf_counter()
        
        avg_time = (end_time - start_time) / iterations * 1000  # 转换为毫秒
        print(f"TaskStatus 平均访问时间: {avg_time:.6f}ms")
        # 验证性能是否小于1ms
        assert avg_time < 1.0, "TaskStatus 访问应该小于1ms"

    def test_task_progress_update_performance(self):
        """测试 TaskProgress 更新性能"""
        progress = TaskProgress()
        iterations = 10000
        
        start_time = time.perf_counter()
        for i in range(iterations):
            progress.update_step(f"step_{i}")
        end_time = time.perf_counter()
        
        avg_time = (end_time - start_time) / iterations * 1000  # 转换为毫秒
        print(f"TaskProgress 更新平均时间: {avg_time:.6f}ms")
        # 验证性能是否小于1ms
        assert avg_time < 1.0, "TaskProgress 更新应该小于1ms"

    def test_task_config_creation_performance(self):
        """测试 TaskConfig 创建性能"""
        iterations = 10000
        
        start_time = time.perf_counter()
        for _ in range(iterations):
            config = TaskConfig(timeout=30, retry_count=3, priority=5)
            _ = config.timeout
        end_time = time.perf_counter()
        
        avg_time = (end_time - start_time) / iterations * 1000  # 转换为毫秒
        print(f"TaskConfig 创建平均时间: {avg_time:.6f}ms")
        # 验证性能是否小于1ms
        assert avg_time < 1.0, "TaskConfig 创建应该小于1ms"

    def test_task_info_creation_performance(self):
        """测试 TaskInfo 创建性能"""
        iterations = 10000
        created_at = datetime.now()
        
        start_time = time.perf_counter()
        for i in range(iterations):
            task_info = TaskInfo(
                task_id=f"task_{i}",
                name=f"Task {i}",
                status=TaskStatus.PENDING,
                created_at=created_at
            )
            _ = task_info.task_id
        end_time = time.perf_counter()
        
        avg_time = (end_time - start_time) / iterations * 1000  # 转换为毫秒
        print(f"TaskInfo 创建平均时间: {avg_time:.6f}ms")
        # 验证性能是否小于1ms
        assert avg_time < 1.0, "TaskInfo 创建应该小于1ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
