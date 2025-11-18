"""
测试浏览器服务连接现有浏览器的逻辑

🎯 测试目标：
验证修复后的行为：当检测到现有浏览器但连接失败时，不应该降级到启动新实例，
而应该直接返回错误，避免不断打开 about:blank 标签页。

修复前的问题：
- 检测到现有浏览器 → 尝试 CDP 连接 → 连接失败 → 降级启动新实例 → 
  由于用户数据目录被占用 → 只能打开新标签页 → 不断重复

修复后的行为：
- 检测到现有浏览器 → 尝试 CDP 连接 → 连接失败 → 直接返回 False，
  提示用户解决方案
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rpa.browser.browser_service import SimplifiedBrowserService
from rpa.browser.core.exceptions.browser_exceptions import BrowserError


class TestConnectExistingBrowserLogic:
    """测试连接现有浏览器的逻辑"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.test_config = {
            'browser_config': {
                'browser_type': 'edge',
                'headless': False,
                'debug_port': 9222,
                'connect_to_existing': True  # 标记需要连接现有浏览器
            },
            'debug_mode': True,
            'use_shared_browser': False  # 🔧 禁用共享浏览器以避免测试干扰
        }

        # 🔧 清理共享实例池
        SimplifiedBrowserService._shared_instances.clear()

    @pytest.mark.asyncio
    async def test_connect_existing_browser_success(self):
        """测试成功连接到现有浏览器"""
        service = SimplifiedBrowserService(config=self.test_config)

        with patch('rpa.browser.browser_service.SimplifiedPlaywrightBrowserDriver') as mock_driver_class:
            # 模拟成功的 CDP 连接
            mock_driver = MagicMock()
            mock_driver.connect_to_existing_browser = AsyncMock(return_value=True)
            mock_driver.is_initialized = MagicMock(return_value=True)
            mock_driver.get_page = MagicMock(return_value=MagicMock())
            mock_driver_class.return_value = mock_driver

            # 执行初始化
            result = await service.initialize()

            # 验证结果
            assert result is True, "连接成功应该返回 True"
            assert service._initialized is True, "服务应该标记为已初始化"
            assert service.browser_driver is not None, "浏览器驱动应该被设置"

            # 验证调用了 connect_to_existing_browser
            mock_driver.connect_to_existing_browser.assert_called_once()

            # 验证没有调用 initialize（因为是连接而不是启动新实例）
            assert not hasattr(mock_driver, 'initialize') or not mock_driver.initialize.called

    @pytest.mark.asyncio
    async def test_connect_existing_browser_failure_no_fallback(self):
        """
        🔧 关键测试：连接现有浏览器失败时，不应该降级到启动新实例
        
        这是本次修复的核心测试用例
        """
        service = SimplifiedBrowserService(config=self.test_config)

        with patch('rpa.browser.browser_service.SimplifiedPlaywrightBrowserDriver') as mock_driver_class:
            # 模拟 CDP 连接失败
            mock_driver = MagicMock()
            mock_driver.connect_to_existing_browser = AsyncMock(return_value=False)
            mock_driver.initialize = AsyncMock(return_value=True)  # 这个不应该被调用
            mock_driver_class.return_value = mock_driver

            # 执行初始化
            result = await service.initialize()

            # 🔧 关键验证：应该返回 False，而不是降级到启动新实例
            assert result is False, "连接失败应该返回 False"
            assert service._initialized is False, "服务不应该标记为已初始化"
            assert service.browser_driver is None, "浏览器驱动应该被清理"

            # 🔧 关键验证：不应该调用 initialize（不应该降级到启动新实例）
            mock_driver.initialize.assert_not_called()

    @pytest.mark.asyncio
    async def test_connect_existing_browser_failure_logs_error(self):
        """测试连接失败时是否输出了正确的错误日志"""
        service = SimplifiedBrowserService(config=self.test_config)

        with patch('rpa.browser.browser_service.SimplifiedPlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.connect_to_existing_browser = AsyncMock(return_value=False)
            mock_driver_class.return_value = mock_driver

            # 捕获日志输出
            with patch.object(service.logger, 'error') as mock_logger_error:
                result = await service.initialize()

                # 验证返回值
                assert result is False

                # 验证错误日志被调用
                assert mock_logger_error.call_count >= 2, "应该输出错误信息和解决方案"

                # 验证日志内容包含关键信息
                log_calls = [str(call) for call in mock_logger_error.call_args_list]
                log_text = ' '.join(log_calls)

                assert '连接现有浏览器失败' in log_text or 'Failed' in log_text
                assert '解决方案' in log_text or '调试端口' in log_text or 'debug_port' in log_text

    @pytest.mark.asyncio
    async def test_no_existing_browser_starts_new_instance(self):
        """测试当没有现有浏览器时，正常启动新实例"""
        # 配置中不设置 connect_to_existing
        config_without_existing = {
            'browser_config': {
                'browser_type': 'edge',
                'headless': False,
                'debug_port': 9222
                # 注意：没有 connect_to_existing
            },
            'debug_mode': True
        }

        service = SimplifiedBrowserService(config=config_without_existing)

        with patch('rpa.browser.browser_service.SimplifiedPlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.initialize = AsyncMock(return_value=True)
            mock_driver.is_initialized = MagicMock(return_value=True)
            mock_driver.get_page = MagicMock(return_value=MagicMock())
            mock_driver_class.return_value = mock_driver

            result = await service.initialize()

            # 验证结果
            assert result is True
            assert service._initialized is True

            # 验证调用了 initialize（启动新实例）
            mock_driver.initialize.assert_called_once()

            # 验证没有调用 connect_to_existing_browser
            if hasattr(mock_driver, 'connect_to_existing_browser'):
                mock_driver.connect_to_existing_browser.assert_not_called()

    @pytest.mark.asyncio
    async def test_connect_existing_browser_exception_handling(self):
        """测试连接现有浏览器时抛出异常的处理"""
        service = SimplifiedBrowserService(config=self.test_config)

        with patch('rpa.browser.browser_service.SimplifiedPlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            # 模拟连接时抛出异常
            mock_driver.connect_to_existing_browser = AsyncMock(
                side_effect=Exception("CDP connection error")
            )
            mock_driver_class.return_value = mock_driver

            # 执行初始化，应该捕获异常并返回 False
            result = await service.initialize()

            # 验证结果
            assert result is False
            assert service._initialized is False
            assert service.browser_driver is None

    @pytest.mark.asyncio
    async def test_start_browser_after_connect_success(self):
        """测试连接成功后启动浏览器"""
        service = SimplifiedBrowserService(config=self.test_config)

        with patch('rpa.browser.browser_service.SimplifiedPlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.connect_to_existing_browser = AsyncMock(return_value=True)
            mock_driver.is_initialized = MagicMock(return_value=True)
            mock_page = MagicMock()
            mock_driver.get_page = MagicMock(return_value=mock_page)
            mock_driver_class.return_value = mock_driver

            # 初始化
            init_result = await service.initialize()
            assert init_result is True

            # 启动浏览器
            start_result = await service.start_browser()

            # 验证结果
            assert start_result is True
            assert service._browser_started is True

            # 验证调用了 get_page 来检查页面对象
            mock_driver.get_page.assert_called()

    @pytest.mark.asyncio
    async def test_start_browser_after_connect_failure(self):
        """测试连接失败后尝试启动浏览器应该失败"""
        service = SimplifiedBrowserService(config=self.test_config)

        with patch('rpa.browser.browser_service.SimplifiedPlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.connect_to_existing_browser = AsyncMock(return_value=False)
            mock_driver_class.return_value = mock_driver

            # 初始化失败
            init_result = await service.initialize()
            assert init_result is False

            # 尝试启动浏览器应该失败（因为初始化失败）
            with pytest.raises(BrowserError):
                await service.start_browser()


class TestConnectExistingBrowserIntegration:
    """集成测试：测试完整的连接流程"""

    @pytest.mark.asyncio
    async def test_full_workflow_connect_and_navigate(self):
        """测试完整工作流：连接现有浏览器并导航"""
        config = {
            'browser_config': {
                'browser_type': 'edge',
                'headless': False,
                'debug_port': 9222,
                'connect_to_existing': True
            },
            'debug_mode': True
        }

        service = SimplifiedBrowserService(config=config)

        with patch('rpa.browser.browser_service.SimplifiedPlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.connect_to_existing_browser = AsyncMock(return_value=True)
            mock_driver.is_initialized = MagicMock(return_value=True)
            mock_page = MagicMock()
            mock_driver.get_page = MagicMock(return_value=mock_page)
            mock_driver.open_page = AsyncMock(return_value=True)
            mock_driver_class.return_value = mock_driver

            # 1. 初始化
            init_result = await service.initialize()
            assert init_result is True

            # 2. 启动浏览器
            start_result = await service.start_browser()
            assert start_result is True

            # 3. 导航到页面
            navigate_result = await service.navigate_to("https://example.com")
            assert navigate_result is True

            # 验证调用顺序
            mock_driver.connect_to_existing_browser.assert_called_once()
            mock_driver.open_page.assert_called_once_with("https://example.com", "load")

    @pytest.mark.asyncio
    async def test_full_workflow_connect_failure_stops_early(self):
        """测试完整工作流：连接失败时应该提前停止"""
        config = {
            'browser_config': {
                'browser_type': 'edge',
                'headless': False,
                'debug_port': 9222,
                'connect_to_existing': True
            },
            'debug_mode': True
        }

        service = SimplifiedBrowserService(config=config)

        with patch('rpa.browser.browser_service.SimplifiedPlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.connect_to_existing_browser = AsyncMock(return_value=False)
            mock_driver.open_page = AsyncMock(return_value=True)
            mock_driver_class.return_value = mock_driver

            # 1. 初始化失败
            init_result = await service.initialize()
            assert init_result is False

            # 2. 不应该能够启动浏览器
            with pytest.raises(BrowserError):
                await service.start_browser()

            # 3. 不应该能够导航
            # （因为启动浏览器已经失败）

            # 验证 open_page 从未被调用
            mock_driver.open_page.assert_not_called()


class TestBrowserDriverCleanup:
    """测试浏览器驱动的清理逻辑"""

    @pytest.mark.asyncio
    async def test_driver_cleanup_on_connect_failure(self):
        """测试连接失败时是否正确清理了浏览器驱动"""
        config = {
            'browser_config': {
                'browser_type': 'edge',
                'connect_to_existing': True
            }
        }

        service = SimplifiedBrowserService(config=config)

        with patch('rpa.browser.browser_service.SimplifiedPlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.connect_to_existing_browser = AsyncMock(return_value=False)
            mock_driver_class.return_value = mock_driver

            # 初始化失败
            result = await service.initialize()

            # 验证清理
            assert result is False
            assert service.browser_driver is None, "浏览器驱动应该被清理为 None"
            assert service._initialized is False, "初始化标志应该为 False"

    @pytest.mark.asyncio
    async def test_driver_not_cleaned_on_connect_success(self):
        """测试连接成功时浏览器驱动不应该被清理"""
        config = {
            'browser_config': {
                'browser_type': 'edge',
                'connect_to_existing': True
            }
        }

        service = SimplifiedBrowserService(config=config)

        with patch('rpa.browser.browser_service.SimplifiedPlaywrightBrowserDriver') as mock_driver_class:
            mock_driver = MagicMock()
            mock_driver.connect_to_existing_browser = AsyncMock(return_value=True)
            mock_driver.is_initialized = MagicMock(return_value=True)
            mock_driver.get_page = MagicMock(return_value=MagicMock())
            mock_driver_class.return_value = mock_driver

            # 初始化成功
            result = await service.initialize()

            # 验证驱动保留
            assert result is True
            assert service.browser_driver is not None, "浏览器驱动应该被保留"
            assert service._initialized is True, "初始化标志应该为 True"


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
