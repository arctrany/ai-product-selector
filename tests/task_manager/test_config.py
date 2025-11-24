#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task Manager Config 测试模块

测试跨平台配置管理功能，包括配置加载、验证和持久化。
"""

import os
import json
import tempfile
import platform
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from task_manager.config import (
    TaskManagerConfig,
    get_config,
    set_config,
    load_config,
    create_default_config_file
)


class TestTaskManagerConfig:
    """测试 TaskManagerConfig 数据类"""

    def test_default_initialization(self):
        """测试默认初始化"""
        config = TaskManagerConfig()
        
        # 验证默认值
        assert config.max_concurrent_tasks == 5
        assert config.max_task_queue_size == 100
        assert config.persist_tasks is True
        assert config.enable_logging is True
        assert config.log_level == "INFO"
        assert config.default_retry_count == 0
        assert config.retry_delay == 1.0
        assert isinstance(config.platform_specific, dict)
        
        # 验证路径已设置
        assert config.task_storage_path != ""
        assert config.log_file_path != ""

    def test_custom_initialization(self):
        """测试自定义初始化"""
        custom_config = TaskManagerConfig(
            max_concurrent_tasks=10,
            max_task_queue_size=200,
            persist_tasks=False,
            enable_logging=False,
            log_level="DEBUG",
            default_task_timeout=60,
            default_retry_count=3,
            retry_delay=2.0
        )
        
        assert custom_config.max_concurrent_tasks == 10
        assert custom_config.max_task_queue_size == 200
        assert custom_config.persist_tasks is False
        assert custom_config.enable_logging is False
        assert custom_config.log_level == "DEBUG"
        assert custom_config.default_task_timeout == 60
        assert custom_config.default_retry_count == 3
        assert custom_config.retry_delay == 2.0

    def test_from_dict(self):
        """测试从字典创建配置"""
        config_dict = {
            "max_concurrent_tasks": 15,
            "max_task_queue_size": 300,
            "persist_tasks": False,
            "log_level": "WARNING",
            "default_retry_count": 5
        }
        
        config = TaskManagerConfig.from_dict(config_dict)
        
        assert config.max_concurrent_tasks == 15
        assert config.max_task_queue_size == 300
        assert config.persist_tasks is False
        assert config.log_level == "WARNING"
        assert config.default_retry_count == 5

    def test_from_dict_with_extra_fields(self):
        """测试从包含额外字段的字典创建配置"""
        config_dict = {
            "max_concurrent_tasks": 8,
            "extra_field": "should_be_ignored",
            "another_extra": 123
        }
        
        config = TaskManagerConfig.from_dict(config_dict)
        
        assert config.max_concurrent_tasks == 8
        # 额外字段应该被忽略
        assert not hasattr(config, 'extra_field')
        assert not hasattr(config, 'another_extra')

    def test_to_dict(self):
        """测试转换为字典"""
        config = TaskManagerConfig(
            max_concurrent_tasks=7,
            log_level="ERROR"
        )
        
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict["max_concurrent_tasks"] == 7
        assert config_dict["log_level"] == "ERROR"
        assert "task_storage_path" in config_dict
        assert "log_file_path" in config_dict

    def test_post_init_storage_path(self):
        """测试初始化后存储路径设置"""
        # 不设置存储路径，应该使用默认值
        config = TaskManagerConfig()
        assert config.task_storage_path != ""

    def test_post_init_log_path(self):
        """测试初始化后日志路径设置"""
        # 不设置日志路径，应该使用默认值
        config = TaskManagerConfig()
        assert config.log_file_path != ""


class TestTaskManagerConfigPlatformPaths:
    """测试跨平台路径配置"""

    @patch("os.name", "nt")  # Windows
    def test_windows_paths(self):
        """测试 Windows 路径"""
        with patch.dict(os.environ, {"APPDATA": "C:\\Users\\Test\\AppData\\Roaming"}, clear=True):
            config = TaskManagerConfig()
            
            # 验证路径包含 Windows 特定目录
            assert "AppData" in config.task_storage_path
            assert "AppData" in config.log_file_path
            assert "xuanping" in config.task_storage_path
            assert "xuanping" in config.log_file_path

    @patch("os.name", "posix")  # Unix-like
    def test_unix_paths(self):
        """测试 Unix-like 系统路径"""
        with patch.dict(os.environ, {"XDG_DATA_HOME": "/home/test/.local/share"}, clear=True):
            config = TaskManagerConfig()
            
            # 验证路径包含 Unix 特定目录
            assert ".local/share" in config.task_storage_path
            assert ".cache" in config.log_file_path
            assert "xuanping" in config.task_storage_path
            assert "xuanping" in config.log_file_path

    @patch("os.name", "unknown")
    def test_unknown_platform_paths(self):
        """测试未知平台路径"""
        config = TaskManagerConfig()
        
        # 应该回退到用户主目录
        assert str(Path.home()) in config.task_storage_path
        assert str(Path.home()) in config.log_file_path


class TestTaskManagerConfigFileOperations:
    """测试配置文件操作"""

    def test_save_to_json_file(self):
        """测试保存配置到JSON文件"""
        config = TaskManagerConfig(max_concurrent_tasks=12, log_level="DEBUG")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file_path = f.name
        
        try:
            config.save_to_json_file(temp_file_path)
            
            # 验证文件已创建并包含正确内容
            assert os.path.exists(temp_file_path)
            
            with open(temp_file_path, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
            
            assert saved_config["max_concurrent_tasks"] == 12
            assert saved_config["log_level"] == "DEBUG"
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_from_json_file_success(self):
        """测试从JSON文件加载配置成功"""
        config_data = {
            "max_concurrent_tasks": 20,
            "log_level": "CRITICAL",
            "default_retry_count": 2
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(config_data, f)
            temp_file_path = f.name
        
        try:
            config = TaskManagerConfig.from_json_file(temp_file_path)
            
            assert config.max_concurrent_tasks == 20
            assert config.log_level == "CRITICAL"
            assert config.default_retry_count == 2
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_from_json_file_not_found(self):
        """测试从不存在的JSON文件加载配置"""
        config = TaskManagerConfig.from_json_file("/non/existent/config.json")
        
        # 应该返回默认配置
        assert isinstance(config, TaskManagerConfig)
        assert config.max_concurrent_tasks == 5  # 默认值

    def test_from_json_file_invalid_json(self):
        """测试从无效JSON文件加载配置"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write("invalid json content")
            temp_file_path = f.name
        
        try:
            config = TaskManagerConfig.from_json_file(temp_file_path)
            
            # 应该返回默认配置
            assert isinstance(config, TaskManagerConfig)
            assert config.max_concurrent_tasks == 5  # 默认值
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)


class TestTaskManagerConfigEnvironment:
    """测试环境变量配置"""

    def test_from_env_with_variables(self):
        """测试从环境变量加载配置"""
        env_vars = {
            "TASK_MANAGER_MAX_CONCURRENT": "25",
            "TASK_MANAGER_MAX_QUEUE_SIZE": "500",
            "TASK_MANAGER_PERSIST_TASKS": "false",
            "TASK_MANAGER_ENABLE_LOGGING": "false",
            "TASK_MANAGER_LOG_LEVEL": "ERROR",
            "TASK_MANAGER_DEFAULT_TIMEOUT": "120",
            "TASK_MANAGER_DEFAULT_RETRY": "5",
            "TASK_MANAGER_RETRY_DELAY": "3.5"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = TaskManagerConfig.from_env()
            
            assert config.max_concurrent_tasks == 25
            assert config.max_task_queue_size == 500
            assert config.persist_tasks is False
            assert config.enable_logging is False
            assert config.log_level == "ERROR"
            assert config.default_task_timeout == 120
            assert config.default_retry_count == 5
            assert config.retry_delay == 3.5

    def test_from_env_without_variables(self):
        """测试在没有环境变量时从环境加载配置"""
        with patch.dict(os.environ, {}, clear=True):
            config = TaskManagerConfig.from_env()
            
            # 应该返回默认配置
            assert isinstance(config, TaskManagerConfig)
            assert config.max_concurrent_tasks == 5  # 默认值

    def test_from_env_with_invalid_values(self):
        """测试从包含无效值的环境变量加载配置"""
        env_vars = {
            "TASK_MANAGER_MAX_CONCURRENT": "invalid",
            "TASK_MANAGER_DEFAULT_RETRY": "not_a_number"
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            # 应该抛出异常或使用默认值
            with pytest.raises(ValueError):
                TaskManagerConfig.from_env()


class TestTaskManagerConfigValidation:
    """测试配置验证"""

    def test_valid_config(self):
        """测试有效配置验证"""
        config = TaskManagerConfig(
            max_concurrent_tasks=10,
            max_task_queue_size=100,
            default_retry_count=3
        )
        
        # 验证应该通过
        assert config.validate() is True

    def test_invalid_concurrent_tasks(self):
        """测试无效并发任务数验证"""
        config = TaskManagerConfig(max_concurrent_tasks=0)
        
        # 验证应该失败
        assert config.validate() is False

    def test_invalid_retry_count(self):
        """测试无效重试次数验证"""
        config = TaskManagerConfig(default_retry_count=-1)
        
        # 验证应该失败
        assert config.validate() is False

    def test_invalid_retry_delay(self):
        """测试无效重试延迟验证"""
        config = TaskManagerConfig(retry_delay=-0.5)
        
        # 验证应该失败
        assert config.validate() is False

    def test_storage_path_validation(self):
        """测试存储路径验证"""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = os.path.join(temp_dir, "tasks.json")
            config = TaskManagerConfig(
                persist_tasks=True,
                task_storage_path=storage_path
            )
            
            # 验证应该通过
            assert config.validate() is True

    def test_invalid_storage_path(self):
        """测试无效存储路径验证"""
        config = TaskManagerConfig(
            persist_tasks=True,
            task_storage_path="/invalid/path/that/cannot/be/written"
        )
        
        # 验证应该失败
        assert config.validate() is False


class TestConfigGlobalFunctions:
    """测试全局配置函数"""

    def setup_method(self):
        """测试初始化"""
        # 重置全局配置
        global _global_config
        _global_config = None

    def teardown_method(self):
        """测试清理"""
        # 重置全局配置
        global _global_config
        _global_config = None

    def test_get_config_default(self):
        """测试获取默认配置"""
        config = get_config()
        
        assert isinstance(config, TaskManagerConfig)
        assert config.max_concurrent_tasks == 5  # 默认值

    def test_get_config_cached(self):
        """测试获取缓存配置"""
        # 第一次获取
        config1 = get_config()
        # 第二次获取
        config2 = get_config()
        
        # 应该是同一个实例
        assert config1 is config2

    def test_set_config(self):
        """测试设置配置"""
        new_config = TaskManagerConfig(max_concurrent_tasks=50)
        set_config(new_config)
        
        retrieved_config = get_config()
        assert retrieved_config is new_config
        assert retrieved_config.max_concurrent_tasks == 50

    def test_load_config_with_file(self):
        """测试从文件加载配置"""
        config_data = {
            "max_concurrent_tasks": 30,
            "log_level": "DEBUG"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(config_data, f)
            temp_file_path = f.name
        
        try:
            config = load_config(temp_file_path)
            
            assert config.max_concurrent_tasks == 30
            assert config.log_level == "DEBUG"
        finally:
            # 清理临时文件
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_load_config_without_file(self):
        """测试在没有文件时加载配置"""
        config = load_config("/non/existent/config.json")
        
        # 应该返回默认配置
        assert isinstance(config, TaskManagerConfig)

    def test_create_default_config_file(self):
        """测试创建默认配置文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file_path = os.path.join(temp_dir, "default_config.json")
            created_path = create_default_config_file(config_file_path)
            
            assert created_path == config_file_path
            assert os.path.exists(config_file_path)
            
            # 验证文件包含有效的JSON
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            assert "max_concurrent_tasks" in config_data
            assert "log_level" in config_data


class TestConfigCrossPlatformCompatibility:
    """测试跨平台兼容性"""

    def test_path_creation_on_different_platforms(self):
        """测试在不同平台上的路径创建"""
        # 测试当前平台
        config = TaskManagerConfig()
        
        # 验证路径是有效的
        storage_path = Path(config.task_storage_path)
        log_path = Path(config.log_file_path)
        
        # 父目录应该存在或可以创建
        assert storage_path.parent.exists() or storage_path.parent.parent.exists()
        assert log_path.parent.exists() or log_path.parent.parent.exists()

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-specific test")
    def test_unix_permissions(self):
        """测试 Unix 系统权限"""
        config = TaskManagerConfig()
        
        # 在 Unix 系统上，目录应该可以创建
        storage_dir = Path(config.task_storage_path).parent
        log_dir = Path(config.log_file_path).parent
        
        # 尝试创建目录
        storage_dir.mkdir(parents=True, exist_ok=True)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        assert storage_dir.exists()
        assert log_dir.exists()

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
    def test_windows_paths(self):
        """测试 Windows 路径"""
        config = TaskManagerConfig()
        
        # 验证路径不包含非法字符
        assert ":" in config.task_storage_path  # Windows 驱动器标识
        assert ":" in config.log_file_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
