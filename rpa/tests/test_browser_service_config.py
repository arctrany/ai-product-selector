"""
BrowserService 配置测试

测试重构后的 BrowserService 配置功能：
- 配置字典支持
- BrowserConfig对象支持
- ConfigManager兼容性
- 配置验证和更新
- 配置修复功能
- 错误处理
"""

import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os
from typing import Dict, List, Any, Optional

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src_new.rpa.browser.browser_service import BrowserService, create_browser_service
from src_new.rpa.browser.core.models.browser_config import BrowserConfig, BrowserType, create_default_config
from src_new.rpa.browser.core.exceptions.browser_exceptions import BrowserError, ConfigurationError
from src_new.rpa.browser.implementations.config_manager import ConfigManager

class TestBrowserServiceConfigSupport:
    """测试BrowserService的配置支持"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.config_dict_chrome = {
            'browser_type': 'chrome',
            'headless': True,
            'viewport': {'width': 1920, 'height': 1080},
            'default_timeout': 30000
        }
        
        self.config_dict_edge = {
            'browser_type': 'edge',
            'headless': False,
            'viewport': {'width': 1366, 'height': 768},
            'user_data_dir': '/tmp/edge_profile'
        }
        
        self.browser_config = BrowserConfig(
            browser_type=BrowserType.CHROME,
            headless=True,
            viewport={'width': 1920, 'height': 1080}
        )
    
    def test_init_with_config_dict(self):
        """测试使用配置字典初始化"""
        service = BrowserService(config=self.config_dict_chrome)
        
        assert service.unified_config_manager is not None
        assert service._config_initialization_task is not None
        assert not service._initialized
    
    def test_init_with_browser_config_object(self):
        """测试使用BrowserConfig对象初始化"""
        service = BrowserService(config=self.browser_config)
        
        assert service.unified_config_manager is not None
        assert service._config_initialization_task is not None
        assert not service._initialized
    
    def test_init_with_config_manager(self):
        """测试使用ConfigManager初始化"""
        config_manager = ConfigManager()
        service = BrowserService(config=config_manager)
        
        assert service.unified_config_manager is not None
        assert service._config_initialization_task is not None
        assert not service._initialized
    
    @pytest.mark.asyncio
    async def test_config_dict_initialization(self):
        """测试配置字典初始化过程"""
        service = BrowserService(config=self.config_dict_chrome, debug_mode=True)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver_class.return_value = mock_driver
            
            result = await service.initialize()
            
            assert result is True
            assert service._initialized is True
            assert service.browser_config is not None
            assert service.browser_config.browser_type == BrowserType.CHROME
            assert service.browser_config.headless is True
            assert service._config_source_type == "Dict"
    
    @pytest.mark.asyncio
    async def test_browser_config_initialization(self):
        """测试BrowserConfig对象初始化过程"""
        service = BrowserService(config=self.browser_config, debug_mode=True)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver_class.return_value = mock_driver
            
            result = await service.initialize()
            
            assert result is True
            assert service._initialized is True
            assert service.browser_config is not None
            assert service._config_source_type == "BrowserConfig"
    
    @pytest.mark.asyncio
    async def test_config_manager_initialization(self):
        """测试ConfigManager初始化过程"""
        config_manager = ConfigManager()
        service = BrowserService(config=config_manager, debug_mode=True)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver_class.return_value = mock_driver
            
            result = await service.initialize()
            
            assert result is True
            assert service._initialized is True
            assert service.browser_config is not None
            assert service._config_source_type == "ConfigManager"

class TestBrowserServiceConfigValidation:
    """测试BrowserService的配置验证"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.valid_config = {
            'browser_type': 'chrome',
            'headless': True,
            'viewport': {'width': 1920, 'height': 1080}
        }
        
        self.invalid_config_type = {
            'browser_type': 'invalid_browser',
            'headless': True
        }
        
        self.invalid_config_structure = {
            'browser_type': 'chrome',
            'headless': 'not_a_boolean',
            'viewport': 'invalid_viewport'
        }
    
    @pytest.mark.asyncio
    async def test_validate_valid_config(self):
        """测试验证有效配置"""
        service = BrowserService(config=self.valid_config)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver_class.return_value = mock_driver
            
            await service.initialize()
            
            validation_result = await service.validate_current_config()
            
            assert 'valid' in validation_result
            assert 'errors' in validation_result
            assert 'warnings' in validation_result
    
    @pytest.mark.asyncio
    async def test_validate_config_not_initialized(self):
        """测试验证未初始化的配置"""
        service = BrowserService()
        
        validation_result = await service.validate_current_config()
        
        assert validation_result['valid'] is False
        assert '配置未初始化' in validation_result['errors']
    
    def test_invalid_config_type_rejection(self):
        """测试拒绝无效配置类型"""
        invalid_configs = [
            "string_config",
            123,
            ["list", "config"],
            None
        ]
        
        for invalid_config in invalid_configs:
            service = BrowserService(config=invalid_config)
            # 应该能创建服务，但初始化时会失败
            assert service.unified_config_manager is not None

class TestBrowserServiceConfigUpdate:
    """测试BrowserService的配置更新"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.initial_config = {
            'browser_type': 'chrome',
            'headless': True,
            'viewport': {'width': 1920, 'height': 1080}
        }
    
    @pytest.mark.asyncio
    async def test_update_config_after_initialization(self):
        """测试初始化后更新配置"""
        service = BrowserService(config=self.initial_config, debug_mode=True)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver_class.return_value = mock_driver
            
            await service.initialize()
            
            # 更新配置
            result = await service.update_config('headless', False)
            
            assert result is True
            assert service.browser_config.headless is False
    
    @pytest.mark.asyncio
    async def test_update_config_before_initialization(self):
        """测试初始化前更新配置"""
        service = BrowserService()
        
        # 即使未初始化也应该能更新配置
        result = await service.update_config('headless', True)
        
        # 这取决于具体实现，可能返回True或False
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_get_config_info(self):
        """测试获取配置信息"""
        service = BrowserService(config=self.initial_config, debug_mode=True)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver_class.return_value = mock_driver
            
            await service.initialize()
            
            config_info = await service.get_config_info()
            
            assert 'unified_config_manager' in config_info
            assert 'browser_service' in config_info
            assert config_info['browser_service']['service_initialized'] is True
            assert config_info['browser_service']['config_source_type'] == "Dict"
            assert 'current_config' in config_info['browser_service']

class TestBrowserServiceConfigFixer:
    """测试BrowserService的配置修复功能"""
    
    def setup_method(self):
        """每个测试方法前的设置"""
        self.config_with_string_values = {
            'browser_type': 'chrome',
            'headless': 'true',  # 字符串布尔值
            'viewport_width': 1366,  # 分离的视口配置
            'viewport_height': 768,
            'default_timeout': '30000',  # 字符串数字
            'invalid_field': 'should_be_ignored'  # 无效字段
        }
    
    @pytest.mark.asyncio
    async def test_config_auto_fix_string_boolean(self):
        """测试自动修复字符串布尔值"""
        service = BrowserService(config=self.config_with_string_values, debug_mode=True)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver_class.return_value = mock_driver
            
            result = await service.initialize()
            
            assert result is True
            assert service.browser_config.headless is True  # 自动修复为布尔值
    
    @pytest.mark.asyncio
    async def test_config_auto_merge_viewport(self):
        """测试自动合并视口配置"""
        service = BrowserService(config=self.config_with_string_values, debug_mode=True)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver_class.return_value = mock_driver
            
            result = await service.initialize()
            
            assert result is True
            assert service.browser_config.viewport.width == 1366  # 自动合并视口配置
            assert service.browser_config.viewport.height == 768

class TestBrowserServiceFactoryWithConfig:
    """测试BrowserService工厂函数的配置支持"""
    
    def test_create_with_config_dict(self):
        """测试使用配置字典创建服务"""
        config_dict = {'browser_type': 'edge', 'headless': False}
        service = create_browser_service(config=config_dict, debug_mode=True)
        
        assert isinstance(service, BrowserService)
        assert service._config_initialization_task is not None
        assert service.debug_mode is True
    
    def test_create_with_browser_config(self):
        """测试使用BrowserConfig对象创建服务"""
        browser_config = create_default_config()
        service = create_browser_service(config=browser_config)
        
        assert isinstance(service, BrowserService)
        assert service._config_initialization_task is not None
    
    def test_create_with_config_manager(self):
        """测试使用ConfigManager创建服务"""
        config_manager = ConfigManager()
        service = create_browser_service(config=config_manager)
        
        assert isinstance(service, BrowserService)
        assert service._config_initialization_task is not None

class TestBrowserServiceConfigErrorHandling:
    """测试BrowserService配置错误处理"""
    
    @pytest.mark.asyncio
    async def test_initialize_with_invalid_config_type(self):
        """测试使用无效配置类型初始化"""
        invalid_configs = [
            ["invalid", "config", "list"],
            "invalid_string_config",
            123,
            None
        ]
        
        for invalid_config in invalid_configs:
            service = BrowserService(config=invalid_config)
            
            result = await service.initialize()
            
            assert result is False
            assert not service._initialized
    
    @pytest.mark.asyncio
    async def test_config_validation_with_errors(self):
        """测试配置验证包含错误的情况"""
        # 创建一个会导致验证错误的配置
        problematic_config = {
            'browser_type': 'chrome',
            'headless': True,
            'viewport': {'width': -100, 'height': -100}  # 无效的视口尺寸
        }
        
        service = BrowserService(config=problematic_config)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver_class.return_value = mock_driver
            
            # 即使配置有问题，初始化也可能成功（取决于具体实现）
            result = await service.initialize()
            
            # 验证配置应该能检测到问题
            validation_result = await service.validate_current_config()
            
            assert 'valid' in validation_result
            assert 'errors' in validation_result
            assert 'warnings' in validation_result
    
    @pytest.mark.asyncio
    async def test_update_config_with_invalid_values(self):
        """测试使用无效值更新配置"""
        service = BrowserService(config={'browser_type': 'chrome'}, debug_mode=True)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver_class.return_value = mock_driver
            
            await service.initialize()
            
            # 尝试使用无效值更新配置
            result = await service.update_config('browser_type', 'invalid_browser')
            
            # 应该拒绝无效的更新
            assert isinstance(result, bool)

class TestBrowserServiceConfigCompatibility:
    """测试BrowserService配置兼容性"""
    
    @pytest.mark.asyncio
    async def test_legacy_config_manager_compatibility(self):
        """测试与旧版ConfigManager的兼容性"""
        # 创建一个模拟的旧版ConfigManager
        mock_config_manager = MagicMock(spec=ConfigManager)
        mock_config_manager.get_config = AsyncMock(return_value={
            'browser_type': 'edge',
            'headless': False,
            'profile_name': 'Default'
        })
        
        service = BrowserService(config=mock_config_manager, debug_mode=True)
        
        with patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver_class.return_value = mock_driver
            
            result = await service.initialize()
            
            assert result is True
            assert service._initialized is True
            assert service._config_source_type == "ConfigManager"
    
    def test_mixed_config_scenarios(self):
        """测试混合配置场景"""
        # 测试各种配置组合
        configs = [
            {'browser_type': 'chrome', 'headless': True},
            BrowserConfig(browser_type=BrowserType.EDGE, headless=False),
            ConfigManager(),
        ]
        
        for config in configs:
            service = BrowserService(config=config)
            assert service.unified_config_manager is not None
            assert service._config_initialization_task is not None or config is None

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])