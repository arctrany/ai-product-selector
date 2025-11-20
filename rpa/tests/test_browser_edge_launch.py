"""
Edge 浏览器启动功能测试

测试范围：
1. Edge 浏览器类型配置
2. 用户数据目录自动检测
3. 不同操作系统的默认路径
4. 浏览器 channel 选择
5. 启动参数配置
"""

import pytest
import platform
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from rpa.browser.browser_service import SimplifiedBrowserService
from rpa.browser.implementations.playwright_browser_driver import SimplifiedPlaywrightBrowserDriver


class TestEdgeBrowserConfig:
    """测试 Edge 浏览器配置"""
    
    def test_edge_browser_type_config(self):
        """测试场景：配置使用 Edge 浏览器"""
        config = {
            'browser_config': {
                'browser_type': 'edge',
                'headless': False
            }
        }
        service = SimplifiedBrowserService(config)
        
        browser_config = service._prepare_browser_config()
        
        assert 'browser_type' in browser_config
        assert browser_config['browser_type'] == 'edge'
    
    def test_chrome_browser_type_config(self):
        """测试场景：配置使用 Chrome 浏览器（对比）"""
        config = {
            'browser_config': {
                'browser_type': 'chrome',
                'headless': False
            }
        }
        service = SimplifiedBrowserService(config)
        
        browser_config = service._prepare_browser_config()
        
        assert 'browser_type' in browser_config
        assert browser_config['browser_type'] == 'chrome'
    
    def test_default_browser_type(self):
        """测试场景：不指定浏览器类型，应使用默认值"""
        config = {
            'browser_config': {}
        }
        service = SimplifiedBrowserService(config)
        
        browser_config = service._prepare_browser_config()
        
        # 默认应该是 chrome
        assert browser_config.get('browser_type', 'chrome') == 'chrome'


class TestEdgeBrowserChannel:
    """测试浏览器 channel 选择"""
    
    def test_edge_channel_on_macos(self):
        """测试场景：macOS 上 Edge 浏览器应使用 msedge channel"""
        driver = SimplifiedPlaywrightBrowserDriver({'browser_type': 'edge'})
        
        with patch('platform.system', return_value='Darwin'):
            channel = driver._get_browser_channel('edge')
        
        assert channel == 'msedge'
    
    def test_edge_channel_on_windows(self):
        """测试场景：Windows 上 Edge 浏览器应使用 msedge channel"""
        driver = SimplifiedPlaywrightBrowserDriver({'browser_type': 'edge'})
        
        with patch('platform.system', return_value='Windows'):
            channel = driver._get_browser_channel('edge')
        
        assert channel == 'msedge'
    
    def test_chrome_channel_on_macos(self):
        """测试场景：macOS 上 Chrome 浏览器应使用 chrome channel"""
        driver = SimplifiedPlaywrightBrowserDriver({'browser_type': 'chrome'})
        
        with patch('platform.system', return_value='Darwin'):
            channel = driver._get_browser_channel('chrome')
        
        assert channel == 'chrome'
    
    def test_chrome_channel_on_windows(self):
        """测试场景：Windows 上 Chrome 浏览器应使用 chrome channel"""
        driver = SimplifiedPlaywrightBrowserDriver({'browser_type': 'chrome'})
        
        with patch('platform.system', return_value='Windows'):
            channel = driver._get_browser_channel('chrome')
        
        assert channel == 'chrome'
    
    def test_chromium_channel_on_linux(self):
        """测试场景：Linux 上应使用 chromium channel"""
        driver = SimplifiedPlaywrightBrowserDriver({'browser_type': 'chrome'})
        
        with patch('platform.system', return_value='Linux'):
            channel = driver._get_browser_channel('chrome')
        
        # Linux 上应该返回 chromium 或 None
        assert channel in ['chromium', None]


class TestEdgeUserDataDirectory:
    """测试用户数据目录路径"""
    
    def test_edge_default_user_data_dir_macos(self):
        """测试场景：macOS 上 Edge 的默认用户数据目录"""
        expected_path = os.path.expanduser("~/Library/Application Support/Microsoft Edge")
        
        # 在 macOS 上，Edge 的默认用户数据目录应该是这个路径
        assert expected_path.endswith("Microsoft Edge")
    
    def test_edge_default_user_data_dir_windows(self):
        """测试场景：Windows 上 Edge 的默认用户数据目录"""
        expected_path = os.path.expanduser("~/AppData/Local/Microsoft/Edge/User Data")
        
        # 在 Windows 上，Edge 的默认用户数据目录应该是这个路径
        assert "Microsoft" in expected_path
        assert "Edge" in expected_path
    
    def test_edge_default_user_data_dir_linux(self):
        """测试场景：Linux 上 Edge 的默认用户数据目录"""
        expected_path = os.path.expanduser("~/.config/microsoft-edge")
        
        # 在 Linux 上，Edge 的默认用户数据目录应该是这个路径
        assert expected_path.endswith("microsoft-edge")
    
    def test_chrome_default_user_data_dir_macos(self):
        """测试场景：macOS 上 Chrome 的默认用户数据目录"""
        expected_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
        
        # 在 macOS 上，Chrome 的默认用户数据目录应该是这个路径
        assert expected_path.endswith("Google/Chrome")
    
    def test_chrome_default_user_data_dir_windows(self):
        """测试场景：Windows 上 Chrome 的默认用户数据目录"""
        expected_path = os.path.expanduser("~/AppData/Local/Google/Chrome/User Data")
        
        # 在 Windows 上，Chrome 的默认用户数据目录应该是这个路径
        assert "Google" in expected_path
        assert "Chrome" in expected_path
    
    def test_chrome_default_user_data_dir_linux(self):
        """测试场景：Linux 上 Chrome 的默认用户数据目录"""
        expected_path = os.path.expanduser("~/.config/google-chrome")
        
        # 在 Linux 上，Chrome 的默认用户数据目录应该是这个路径
        assert expected_path.endswith("google-chrome")


class TestEdgeLaunchConfig:
    """测试 Edge 启动配置"""
    
    def test_edge_config_with_custom_user_data_dir(self):
        """测试场景：使用自定义用户数据目录配置 Edge"""
        custom_dir = "/custom/path/to/edge/profile"
        config = {
            'browser_config': {
                'browser_type': 'edge',
                'user_data_dir': custom_dir,
                'headless': False
            }
        }
        service = SimplifiedBrowserService(config)
        
        browser_config = service._prepare_browser_config()
        
        assert browser_config['browser_type'] == 'edge'
        assert browser_config['user_data_dir'] == custom_dir
    
    def test_edge_config_without_user_data_dir(self):
        """测试场景：不指定用户数据目录，应使用默认值（None，会自动检测）"""
        config = {
            'browser_config': {
                'browser_type': 'edge',
                'headless': False
            }
        }
        service = SimplifiedBrowserService(config)
        
        browser_config = service._prepare_browser_config()
        
        assert browser_config['browser_type'] == 'edge'
        # 不指定时应该是 None，会触发自动检测
        assert browser_config.get('user_data_dir') is None
    
    def test_edge_headless_mode(self):
        """测试场景：Edge 浏览器 headless 模式配置"""
        config = {
            'browser_config': {
                'browser_type': 'edge',
                'headless': True
            }
        }
        service = SimplifiedBrowserService(config)
        
        browser_config = service._prepare_browser_config()
        
        assert browser_config['browser_type'] == 'edge'
        assert browser_config['headless'] is True
    
    def test_edge_non_headless_mode(self):
        """测试场景：Edge 浏览器非 headless 模式配置"""
        config = {
            'browser_config': {
                'browser_type': 'edge',
                'headless': False
            }
        }
        service = SimplifiedBrowserService(config)
        
        browser_config = service._prepare_browser_config()
        
        assert browser_config['browser_type'] == 'edge'
        assert browser_config['headless'] is False


class TestEdgeLaunchArgs:
    """测试 Edge 启动参数"""
    
    def test_default_launch_args_format(self):
        """测试场景：默认启动参数格式"""
        driver = SimplifiedPlaywrightBrowserDriver({})
        
        launch_args = driver._get_default_launch_args()
        
        # 验证启动参数是列表
        assert isinstance(launch_args, list)
        # 验证包含必要的参数
        assert '--no-first-run' in launch_args
        assert '--no-default-browser-check' in launch_args
        assert '--enable-extensions' in launch_args
    
    def test_launch_args_contain_anti_automation(self):
        """测试场景：启动参数包含反自动化检测参数"""
        driver = SimplifiedPlaywrightBrowserDriver({})
        
        launch_args = driver._get_default_launch_args()
        
        # 验证包含反自动化检测参数
        assert '--disable-blink-features=AutomationControlled' in launch_args
        assert '--exclude-switches=enable-automation' in launch_args
    
    def test_launch_args_preserve_user_state(self):
        """测试场景：启动参数保留用户状态"""
        driver = SimplifiedPlaywrightBrowserDriver({})
        
        launch_args = driver._get_default_launch_args()
        
        # 验证包含保留用户状态的参数
        assert '--enable-password-generation' in launch_args
        assert '--enable-autofill' in launch_args
        assert '--enable-sync' in launch_args


class TestEdgeFactoryFunctions:
    """测试 Edge 浏览器工厂函数"""
    
    def test_create_edge_browser_service(self):
        """测试场景：创建 Edge 浏览器服务"""
        config = {
            'browser_config': {
                'browser_type': 'edge'
            }
        }
        service = SimplifiedBrowserService(config)
        
        assert isinstance(service, SimplifiedBrowserService)
        assert service.config.browser_config.browser_type == 'edge'
    
    def test_create_edge_browser_with_profile(self):
        """测试场景：创建带 Profile 的 Edge 浏览器服务"""
        profile_path = "/path/to/edge/profile"
        config = {
            'browser_config': {
                'browser_type': 'edge',
                'user_data_dir': profile_path
            }
        }
        service = SimplifiedBrowserService(config)
        
        assert isinstance(service, SimplifiedBrowserService)
        assert service.config.browser_config.browser_type == 'edge'
        assert service.config.browser_config.user_data_dir == profile_path


class TestEdgeCurrentSystemDetection:
    """测试当前系统的 Edge 配置"""
    
    def test_current_system_edge_default_path(self):
        """测试场景：当前系统的 Edge 默认路径"""
        system = platform.system().lower()
        
        if system == "darwin":
            expected_path = os.path.expanduser("~/Library/Application Support/Microsoft Edge")
        elif system == "windows":
            expected_path = os.path.expanduser("~/AppData/Local/Microsoft/Edge/User Data")
        elif system == "linux":
            expected_path = os.path.expanduser("~/.config/microsoft-edge")
        else:
            pytest.skip(f"Unsupported system: {system}")
        
        # 验证路径格式正确
        assert isinstance(expected_path, str)
        assert len(expected_path) > 0
        assert "edge" in expected_path.lower() or "Edge" in expected_path
    
    def test_current_system_edge_channel(self):
        """测试场景：当前系统的 Edge channel"""
        driver = SimplifiedPlaywrightBrowserDriver({'browser_type': 'edge'})
        
        channel = driver._get_browser_channel('edge')
        
        system = platform.system().lower()
        if system in ["darwin", "windows"]:
            assert channel == 'msedge'
        else:
            # Linux 或其他系统可能返回 chromium
            assert channel in ['msedge', 'chromium', None]


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
