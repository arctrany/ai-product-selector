"""
用户配置测试

测试面向用户的配置功能，包括配置加载、环境变量、文件配置等
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
from common.config.base_config import (
    GoodStoreSelectorConfig,
    get_config,
    set_config,
    load_config,
    create_default_config_file
)


class TestUserConfigLoading:
    """用户配置加载测试"""
    
    def test_config_from_dict_basic(self):
        """测试从字典创建配置"""
        config_dict = {
            "selector_filter": {
                "store_min_sales_30days": 2000,
                "store_min_orders_30days": 50,
                "profit_rate_threshold": 25.0,
                "good_store_ratio_threshold": 80.0,
                "max_products_to_check": 150
            },
            "price_calculation": {
                "price_adjustment_threshold_1": 100,
                "price_adjustment_threshold_2": 500,
                "price_multiplier": 1.1,
                "pricing_discount_rate": 0.95,
                "rub_to_cny_rate": 0.12
            },
            "debug_mode": True,
            "dryrun": False,
            "selection_mode": "select-goods"
        }
        
        config = GoodStoreSelectorConfig.from_dict(config_dict)
        
        assert config.selector_filter.store_min_sales_30days == 2000
        assert config.selector_filter.store_min_orders_30days == 50
        assert config.price_calculation.price_multiplier == 1.1
        assert config.debug_mode is True
        assert config.dryrun is False
        assert config.selection_mode == "select-goods"
    
    def test_config_from_json_file_success(self):
        """测试从JSON文件成功加载配置"""
        config_data = {
            "selector_filter": {
                "store_min_sales_30days": 3000,
                "store_min_orders_30days": 75,
                "profit_rate_threshold": 30.0
            },
            "browser": {
                "page_load_timeout_ms": 45000,
                "element_wait_timeout_ms": 12000,
                "max_retries": 5
            },
            "debug_mode": False
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name
        
        try:
            config = GoodStoreSelectorConfig.from_json_file(temp_file)
            
            assert config.selector_filter.store_min_sales_30days == 3000
            assert config.browser.page_load_timeout_ms == 45000
            assert config.debug_mode is False
        finally:
            os.unlink(temp_file)
    
    def test_config_from_json_file_not_found(self):
        """测试JSON文件不存在时的处理"""
        non_existent_file = "/path/that/does/not/exist.json"
        
        with patch('logging.warning') as mock_warning:
            config = GoodStoreSelectorConfig.from_json_file(non_existent_file)
            
            # 应该返回默认配置
            assert isinstance(config, GoodStoreSelectorConfig)
            assert config.debug_mode is False  # 默认值
            
            # 应该记录警告
            mock_warning.assert_called_once()
            assert "不存在" in str(mock_warning.call_args[0][0])
    
    def test_config_from_json_file_invalid_json(self):
        """测试无效JSON文件的处理"""
        invalid_json = "{ invalid json content }"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(invalid_json)
            temp_file = f.name
        
        try:
            with patch('logging.error') as mock_error:
                config = GoodStoreSelectorConfig.from_json_file(temp_file)
                
                # 应该返回默认配置
                assert isinstance(config, GoodStoreSelectorConfig)
                assert config.debug_mode is False  # 默认值
                
                # 应该记录错误
                mock_error.assert_called_once()
                assert "格式错误" in str(mock_error.call_args[0][0])
        finally:
            os.unlink(temp_file)


class TestEnvironmentVariableConfig:
    """环境变量配置测试"""
    
    def test_config_from_env_basic(self):
        """测试基本环境变量配置"""
        env_vars = {
            'MIN_SALES_30DAYS': '5000',
            'MIN_ORDERS_30DAYS': '100',
            'PROFIT_RATE_THRESHOLD': '35.5'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = GoodStoreSelectorConfig.from_env()
            
            assert config.selector_filter.store_min_sales_30days == 5000.0
            assert config.selector_filter.store_min_orders_30days == 100
            assert config.selector_filter.profit_rate_threshold == 35.5
    
    def test_config_from_env_partial(self):
        """测试部分环境变量配置"""
        env_vars = {
            'MIN_SALES_30DAYS': '2500'
            # 其他变量不设置
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = GoodStoreSelectorConfig.from_env()
            
            # 设置的环境变量应该生效
            assert config.selector_filter.store_min_sales_30days == 2500.0
            
            # 未设置的应该使用默认值
            assert config.selector_filter.store_min_orders_30days == 10  # 默认值
            assert config.selector_filter.profit_rate_threshold == 20.0  # 默认值
    
    def test_config_from_env_invalid_values(self):
        """测试无效环境变量值的处理"""
        env_vars = {
            'MIN_SALES_30DAYS': 'not_a_number',
            'MIN_ORDERS_30DAYS': 'invalid_int'
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            # 应该不抛出异常，使用默认值
            config = GoodStoreSelectorConfig.from_env()
            
            # 应该使用默认值
            assert config.selector_filter.store_min_sales_30days == 1000  # 默认值
            assert config.selector_filter.store_min_orders_30days == 10  # 默认值
    
    def test_config_from_env_empty_values(self):
        """测试空环境变量值的处理"""
        env_vars = {
            'MIN_SALES_30DAYS': '',
            'MIN_ORDERS_30DAYS': '   ',  # 空白字符
            'PROFIT_RATE_THRESHOLD': '15.0'  # 有效值
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = GoodStoreSelectorConfig.from_env()
            
            # 空值应该使用默认值
            assert config.selector_filter.store_min_sales_30days == 1000  # 默认值
            assert config.selector_filter.store_min_orders_30days == 10  # 默认值
            
            # 有效值应该生效
            assert config.selector_filter.profit_rate_threshold == 15.0


class TestGlobalConfigManagement:
    """全局配置管理测试"""
    
    def teardown_method(self):
        """测试后清理全局配置"""
        # 重置全局配置
        from common.config.base_config import _global_config
        import common.config.base_config as config_module
        config_module._global_config = None
    
    def test_get_config_default(self):
        """测试获取默认全局配置"""
        config = get_config()
        
        assert isinstance(config, GoodStoreSelectorConfig)
        assert config.debug_mode is False
        assert config.selection_mode == 'select-shops'
    
    def test_set_and_get_config(self):
        """测试设置和获取全局配置"""
        custom_config = GoodStoreSelectorConfig()
        custom_config.debug_mode = True
        custom_config.selection_mode = 'select-goods'
        
        set_config(custom_config)
        retrieved_config = get_config()
        
        assert retrieved_config is custom_config
        assert retrieved_config.debug_mode is True
        assert retrieved_config.selection_mode == 'select-goods'
    
    def test_get_config_singleton_behavior(self):
        """测试全局配置单例行为"""
        config1 = get_config()
        config2 = get_config()
        
        assert config1 is config2  # 应该是同一个对象
    
    def test_load_config_with_file(self):
        """测试使用文件路径加载配置"""
        config_data = {
            "debug_mode": True,
            "selection_mode": "select-goods"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name
        
        try:
            config = load_config(temp_file)
            
            assert config.debug_mode is True
            assert config.selection_mode == "select-goods"
        finally:
            os.unlink(temp_file)
    
    def test_load_config_without_file(self):
        """测试不指定文件时加载配置"""
        with patch.dict(os.environ, {'MIN_SALES_30DAYS': '6000'}, clear=False):
            config = load_config()
            
            # 应该从环境变量加载
            assert config.selector_filter.store_min_sales_30days == 6000.0
    
    def test_load_config_validation_failure(self):
        """测试配置验证失败时的处理"""
        # 创建无效配置
        invalid_config_data = {
            "selector_filter": {
                "store_min_sales_30days": -1000  # 无效值（负数）
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_config_data, f)
            temp_file = f.name
        
        try:
            with patch('logging.warning') as mock_warning:
                config = load_config(temp_file)
                
                # 应该使用默认配置
                assert config.selector_filter.store_min_sales_30days == 1000  # 默认值
                
                # 应该记录警告
                mock_warning.assert_called_once()
                assert "配置验证失败" in str(mock_warning.call_args[0][0])
        finally:
            os.unlink(temp_file)


class TestDefaultConfigFileCreation:
    """默认配置文件创建测试"""
    
    def test_create_default_config_file_basic(self):
        """测试创建默认配置文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "test_config.json")
            
            created_file = create_default_config_file(config_file)
            
            assert created_file == config_file
            assert os.path.exists(config_file)
            
            # 验证文件内容
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            assert "selector_filter" in config_data
            assert "browser" in config_data
            assert "debug_mode" in config_data
    
    def test_create_default_config_file_directory_creation(self):
        """测试创建配置文件时自动创建目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, "config", "nested", "test.json")
            
            # 目录不存在时应该自动创建
            created_file = create_default_config_file(nested_path)
            
            assert created_file == nested_path
            assert os.path.exists(nested_path)
            assert os.path.exists(os.path.dirname(nested_path))


class TestUserConfigurationScenarios:
    """用户配置场景测试"""
    
    def test_development_environment_config(self):
        """测试开发环境配置"""
        dev_config = {
            "debug_mode": True,
            "dryrun": True,
            "browser": {
                "page_load_timeout_ms": 60000,  # 开发环境更长的超时
                "element_wait_timeout_ms": 15000
            },
            "logging": {
                "level": "DEBUG",
                "console_output": True,
                "file_output": False
            }
        }
        
        config = GoodStoreSelectorConfig.from_dict(dev_config)
        
        assert config.debug_mode is True
        assert config.dryrun is True
        assert config.browser.page_load_timeout_ms == 60000
        assert config.logging.level == "DEBUG"
    
    def test_production_environment_config(self):
        """测试生产环境配置"""
        prod_config = {
            "debug_mode": False,
            "dryrun": False,
            "browser": {
                "page_load_timeout_ms": 30000,
                "element_wait_timeout_ms": 8000,
                "max_retries": 3
            },
            "logging": {
                "level": "INFO",
                "console_output": False,
                "file_output": True
            },
            "performance": {
                "max_concurrent_stores": 5,
                "max_concurrent_products": 10
            }
        }
        
        config = GoodStoreSelectorConfig.from_dict(prod_config)
        
        assert config.debug_mode is False
        assert config.dryrun is False
        assert config.browser.max_retries == 3
        assert config.logging.level == "INFO"
        assert config.performance.max_concurrent_stores == 5
    
    def test_minimal_user_config(self):
        """测试最小用户配置"""
        minimal_config = {
            "selector_filter": {
                "store_min_sales_30days": 500
            }
        }
        
        config = GoodStoreSelectorConfig.from_dict(minimal_config)
        
        # 指定的配置应该生效
        assert config.selector_filter.store_min_sales_30days == 500
        
        # 未指定的应该使用默认值
        assert config.selector_filter.store_min_orders_30days == 10
        assert config.debug_mode is False
        assert config.selection_mode == 'select-shops'
    
    def test_comprehensive_user_config(self):
        """测试全面的用户配置"""
        comprehensive_config = {
            "selector_filter": {
                "store_min_sales_30days": 3000,
                "store_min_orders_30days": 80,
                "profit_rate_threshold": 28.0,
                "good_store_ratio_threshold": 85.0,
                "max_products_to_check": 200
            },
            "price_calculation": {
                "price_adjustment_threshold_1": 150,
                "price_adjustment_threshold_2": 800,
                "price_multiplier": 1.15,
                "pricing_discount_rate": 0.92,
                "rub_to_cny_rate": 0.13
            },
            "browser": {
                "page_load_timeout_ms": 40000,
                "element_wait_timeout_ms": 10000,
                "max_retries": 4,
                "retry_delay_ms": 2000
            },
            "excel": {
                "max_rows_to_process": 5000
            },
            "logging": {
                "level": "INFO",
                "console_output": True,
                "file_output": True
            },
            "performance": {
                "max_concurrent_stores": 8,
                "max_concurrent_products": 15,
                "cache_ttl": 1800,
                "batch_size": 20
            },
            "debug_mode": True,
            "dryrun": False,
            "selection_mode": "select-goods"
        }
        
        config = GoodStoreSelectorConfig.from_dict(comprehensive_config)
        
        # 验证所有配置项
        assert config.selector_filter.store_min_sales_30days == 3000
        assert config.price_calculation.price_multiplier == 1.15
        assert config.browser.page_load_timeout_ms == 40000
        assert config.excel.max_rows_to_process == 5000
        assert config.logging.level == "INFO"
        assert config.performance.max_concurrent_stores == 8
        assert config.debug_mode is True
        assert config.selection_mode == "select-goods"


class TestConfigurationPersistence:
    """配置持久化测试"""
    
    def test_save_and_load_roundtrip(self):
        """测试保存和加载配置的往返一致性"""
        # 创建自定义配置
        original_config = GoodStoreSelectorConfig()
        original_config.debug_mode = True
        original_config.selection_mode = "select-goods"
        original_config.selector_filter.store_min_sales_30days = 4000
        original_config.browser.page_load_timeout_ms = 50000
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            # 保存配置
            original_config.save_to_json_file(temp_file)
            
            # 加载配置
            loaded_config = GoodStoreSelectorConfig.from_json_file(temp_file)
            
            # 验证一致性
            assert loaded_config.debug_mode == original_config.debug_mode
            assert loaded_config.selection_mode == original_config.selection_mode
            assert loaded_config.selector_filter.store_min_sales_30days == original_config.selector_filter.store_min_sales_30days
            assert loaded_config.browser.page_load_timeout_ms == original_config.browser.page_load_timeout_ms
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_config_serialization_format(self):
        """测试配置序列化格式"""
        config = GoodStoreSelectorConfig()
        config.debug_mode = True
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            config.save_to_json_file(temp_file)
            
            # 验证JSON格式
            with open(temp_file, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            # 应该包含主要配置区块
            expected_sections = [
                "selector_filter", "price_calculation", "browser", 
                "excel", "logging", "performance"
            ]
            
            for section in expected_sections:
                assert section in saved_data
            
            assert saved_data["debug_mode"] is True
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
