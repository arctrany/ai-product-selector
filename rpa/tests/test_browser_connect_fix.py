"""
简化版测试：验证浏览器连接现有实例失败时不降级的修复

🎯 核心测试目标：
验证当检测到现有浏览器但连接失败时，不应该降级到启动新实例，
而应该直接返回 False，避免不断打开 about:blank 标签页。
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rpa.browser.browser_service import SimplifiedBrowserService


class TestBrowserConnectFix:
    """测试浏览器连接修复的核心逻辑"""

    @pytest.mark.asyncio
    async def test_connect_failure_returns_false(self):
        """
        🔧 核心测试：连接现有浏览器失败时应该返回 False
        
        这是本次修复的关键测试用例
        """
        # 配置：标记需要连接现有浏览器
        config = {
            'browser_config': {
                'browser_type': 'edge',
                'connect_to_existing': True,
                'debug_port': 9222
            },
            'use_shared_browser': False  # 禁用共享浏览器
        }

        service = SimplifiedBrowserService(config=config)

        with patch('rpa.browser.browser_service.SimplifiedPlaywrightBrowserDriver') as MockDriver:
            # 模拟 CDP 连接失败
            mock_driver_instance = MagicMock()
            mock_driver_instance.connect_to_existing_browser = AsyncMock(return_value=False)
            mock_driver_instance.initialize = AsyncMock(return_value=True)  # 这个不应该被调用
            MockDriver.return_value = mock_driver_instance

            # 执行初始化
            result = await service.initialize()

            # 🔧 关键断言：应该返回 False
            assert result is False, "连接失败应该返回 False，而不是降级到启动新实例"

            # 🔧 关键断言：不应该调用 initialize（不应该降级）
            mock_driver_instance.initialize.assert_not_called()

            # 🔧 关键断言：browser_driver 应该被清理
            assert service.browser_driver is None

    @pytest.mark.asyncio
    async def test_connect_success_returns_true(self):
        """测试连接成功时返回 True"""
        config = {
            'browser_config': {
                'browser_type': 'edge',
                'connect_to_existing': True,
                'debug_port': 9222
            },
            'use_shared_browser': False
        }

        service = SimplifiedBrowserService(config=config)

        with patch('rpa.browser.browser_service.SimplifiedPlaywrightBrowserDriver') as MockDriver:
            # 模拟 CDP 连接成功
            mock_driver_instance = MagicMock()
            mock_driver_instance.connect_to_existing_browser = AsyncMock(return_value=True)
            mock_driver_instance.is_initialized = MagicMock(return_value=True)
            mock_driver_instance.get_page = MagicMock(return_value=MagicMock())
            MockDriver.return_value = mock_driver_instance

            # 执行初始化
            result = await service.initialize()

            # 断言：应该返回 True
            assert result is True

            # 断言：browser_driver 应该被设置
            assert service.browser_driver is not None

            # 断言：调用了 connect_to_existing_browser
            mock_driver_instance.connect_to_existing_browser.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_connect_flag_starts_new_instance(self):
        """测试没有 connect_to_existing 标志时正常启动新实例"""
        config = {
            'browser_config': {
                'browser_type': 'edge',
                'debug_port': 9222
                # 注意：没有 connect_to_existing
            },
            'use_shared_browser': False
        }

        # 清理共享实例池
        SimplifiedBrowserService._shared_instances.clear()

        service = SimplifiedBrowserService(config=config)

        with patch('rpa.browser.browser_service.SimplifiedPlaywrightBrowserDriver') as MockDriver:
            # 模拟正常初始化
            mock_driver_instance = MagicMock()
            mock_driver_instance.initialize = AsyncMock(return_value=True)
            mock_driver_instance.is_initialized = MagicMock(return_value=True)
            mock_driver_instance.get_page = MagicMock(return_value=MagicMock())
            MockDriver.return_value = mock_driver_instance

            # 执行初始化
            result = await service.initialize()

            # 断言：应该返回 True
            assert result is True, "没有 connect_to_existing 标志时应该正常启动新实例"

            # 断言：调用了 initialize（启动新实例）
            mock_driver_instance.initialize.assert_called_once()

            # 断言：browser_driver 应该被设置
            assert service.browser_driver is not None

            # 断言：没有调用 connect_to_existing_browser
            if hasattr(mock_driver_instance, 'connect_to_existing_browser'):
                mock_driver_instance.connect_to_existing_browser.assert_not_called()


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
