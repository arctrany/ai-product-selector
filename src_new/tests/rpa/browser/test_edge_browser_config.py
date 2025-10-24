"""
Microsoft Edge 浏览器配置测试

测试新架构中 Microsoft Edge 浏览器的配置功能，包括：
1. 有头模式配置
2. 复用默认用户目录
3. 启用浏览器插件
4. 验证配置的正确性
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, Mock

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src_new.rpa.browser.browser_service import BrowserService
from src_new.rpa.browser.config import RPAConfig
from src_new.rpa.browser.core.models.browser_config import (
    BrowserConfig, 
    BrowserType, 
    ExtensionConfig,
    ViewportConfig,
    create_default_config
)
from src_new.rpa.browser.implementations.playwright_browser_driver import PlaywrightBrowserDriver


class TestEdgeBrowserConfiguration:
    """Microsoft Edge 浏览器配置测试类"""
    
    def setup_method(self):
        """测试前的设置"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.mock_edge_path = "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
        self.mock_user_data_dir = str(Path.home() / "Library/Application Support/Microsoft Edge")
        
        # 创建模拟的扩展目录
        self.extension_dir = self.temp_dir / "test_extension"
        self.extension_dir.mkdir(parents=True)
        
        # 创建模拟的扩展清单文件
        manifest_content = '''
        {
            "manifest_version": 3,
            "name": "Test Extension",
            "version": "1.0",
            "description": "A test extension for Edge browser"
        }
        '''
        (self.extension_dir / "manifest.json").write_text(manifest_content.strip())
    
    def teardown_method(self):
        """测试后的清理"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_create_edge_browser_config(self):
        """测试创建 Microsoft Edge 浏览器配置"""
        # 创建 Edge 浏览器配置
        config = BrowserConfig(
            browser_type=BrowserType.EDGE,
            headless=False,  # 有头模式
            user_data_dir=self.mock_user_data_dir,  # 复用默认用户目录
            extensions=[
                ExtensionConfig(
                    path=self.extension_dir,
                    enabled=True,
                    options={"auto_load": True}
                )
            ],
            viewport=ViewportConfig(width=1920, height=1080),
            debug_port=9222,
            devtools=False,
            launch_args=[
                "--disable-web-security",
                "--allow-running-insecure-content",
                "--disable-features=VizDisplayCompositor"
            ]
        )
        
        # 验证配置
        assert config.browser_type == BrowserType.EDGE
        assert config.headless == False
        assert str(config.user_data_dir) == self.mock_user_data_dir
        assert len(config.extensions) == 1
        assert config.extensions[0].enabled == True
        assert config.viewport.width == 1920
        assert config.viewport.height == 1080
        
        print("✅ Edge 浏览器配置创建成功")
    
    def test_edge_config_validation(self):
        """测试 Edge 配置验证"""
        # 创建有效配置
        valid_config = BrowserConfig(
            browser_type=BrowserType.EDGE,
            headless=False,
            user_data_dir=self.temp_dir / "edge_data",
            extensions=[
                ExtensionConfig(path=self.extension_dir, enabled=True)
            ]
        )
        
        # 创建用户数据目录的父目录
        (self.temp_dir / "edge_data").parent.mkdir(parents=True, exist_ok=True)
        
        # 验证配置
        errors = valid_config.validate()
        assert len(errors) == 0, f"配置验证失败: {errors}"
        
        print("✅ Edge 配置验证通过")
    
    def test_edge_config_with_invalid_extension(self):
        """测试包含无效扩展的 Edge 配置"""
        invalid_extension_path = self.temp_dir / "nonexistent_extension"
        
        config = BrowserConfig(
            browser_type=BrowserType.EDGE,
            headless=False,
            extensions=[
                ExtensionConfig(path=invalid_extension_path, enabled=True)
            ]
        )
        
        # 验证应该失败
        errors = config.validate()
        assert len(errors) > 0
        assert any("Extension path does not exist" in error for error in errors)
        
        print("✅ 无效扩展配置验证正确失败")
    
    def test_edge_config_serialization(self):
        """测试 Edge 配置的序列化和反序列化"""
        original_config = BrowserConfig(
            browser_type=BrowserType.EDGE,
            headless=False,
            user_data_dir=self.mock_user_data_dir,
            extensions=[
                ExtensionConfig(
                    path=self.extension_dir,
                    enabled=True,
                    options={"theme": "dark"}
                )
            ],
            launch_args=["--disable-web-security"]
        )
        
        # 序列化为字典
        config_dict = original_config.to_dict()
        
        # 验证序列化结果
        assert config_dict['browser_type'] == 'edge'
        assert config_dict['headless'] == False
        assert config_dict['user_data_dir'] == self.mock_user_data_dir
        assert len(config_dict['extensions']) == 1
        
        # 反序列化
        restored_config = BrowserConfig.from_dict(config_dict)
        
        # 验证反序列化结果
        assert restored_config.browser_type == BrowserType.EDGE
        assert restored_config.headless == False
        assert str(restored_config.user_data_dir) == self.mock_user_data_dir
        assert len(restored_config.extensions) == 1
        assert restored_config.extensions[0].enabled == True
        
        print("✅ Edge 配置序列化和反序列化成功")
    
    @patch('os.path.exists')
    def test_browser_service_with_edge_config(self, mock_exists):
        """测试使用 Edge 配置的浏览器服务"""
        # 模拟文件存在
        mock_exists.return_value = True
        
        # 创建 RPA 配置
        rpa_config = RPAConfig(overrides={
            "backend": "playwright",
            "browser_type": "edge",
            "headless": False,
            "user_data_dir": self.mock_user_data_dir
        })
        
        # 创建浏览器服务
        service = BrowserService(rpa_config)
        
        # 验证服务创建成功
        assert service is not None
        assert not service.is_initialized()
        
        print("✅ 使用 Edge 配置的浏览器服务创建成功")
    
    @patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver._get_edge_executable_path')
    @patch('src_new.rpa.browser.implementations.playwright_browser_driver.PlaywrightBrowserDriver._get_edge_user_data_dir')
    @patch('os.path.exists')
    def test_playwright_driver_edge_detection(self, mock_exists, mock_user_data_dir, mock_edge_path):
        """测试 Playwright 驱动的 Edge 检测"""
        # 设置模拟返回值
        mock_edge_path.return_value = self.mock_edge_path
        mock_user_data_dir.return_value = self.mock_user_data_dir
        mock_exists.return_value = True
        
        # 创建驱动
        driver = PlaywrightBrowserDriver()
        
        # 测试浏览器路径检测
        executable_path, user_data_dir, browser_type = driver._get_browser_paths()
        
        # 验证检测结果
        assert executable_path == self.mock_edge_path
        assert user_data_dir == self.mock_user_data_dir
        assert browser_type == "edge"
        
        print("✅ Playwright 驱动 Edge 检测成功")
    
    def test_edge_config_merge(self):
        """测试 Edge 配置合并"""
        # 基础配置
        base_config = BrowserConfig(
            browser_type=BrowserType.EDGE,
            headless=False,
            viewport=ViewportConfig(width=1920, height=1080)
        )
        
        # 扩展配置
        extension_config = BrowserConfig(
            browser_type=BrowserType.EDGE,
            extensions=[
                ExtensionConfig(path=self.extension_dir, enabled=True)
            ],
            launch_args=["--disable-web-security"],
            extra_http_headers={"User-Agent": "Custom Edge Agent"}
        )
        
        # 合并配置
        merged_config = base_config.merge(extension_config)
        
        # 验证合并结果
        assert merged_config.browser_type == BrowserType.EDGE
        assert merged_config.headless == False
        assert merged_config.viewport.width == 1920
        assert len(merged_config.extensions) == 1
        assert len(merged_config.launch_args) == 1
        assert "User-Agent" in merged_config.extra_http_headers
        
        print("✅ Edge 配置合并成功")
    
    def test_create_edge_config_with_multiple_extensions(self):
        """测试创建包含多个扩展的 Edge 配置"""
        # 创建第二个扩展目录
        extension_dir_2 = self.temp_dir / "test_extension_2"
        extension_dir_2.mkdir(parents=True)
        (extension_dir_2 / "manifest.json").write_text('{"manifest_version": 3, "name": "Test Extension 2", "version": "1.0"}')
        
        config = BrowserConfig(
            browser_type=BrowserType.EDGE,
            headless=False,
            user_data_dir=self.mock_user_data_dir,
            extensions=[
                ExtensionConfig(
                    path=self.extension_dir,
                    enabled=True,
                    options={"priority": "high"}
                ),
                ExtensionConfig(
                    path=extension_dir_2,
                    enabled=True,
                    options={"priority": "normal"}
                )
            ],
            launch_args=[
                "--load-extension=" + str(self.extension_dir),
                "--load-extension=" + str(extension_dir_2),
                "--disable-extensions-except=" + str(self.extension_dir) + "," + str(extension_dir_2)
            ]
        )
        
        # 验证配置
        assert len(config.extensions) == 2
        assert all(ext.enabled for ext in config.extensions)
        assert len(config.launch_args) == 3
        
        # 验证扩展路径
        extension_paths = [str(ext.path) for ext in config.extensions]
        assert str(self.extension_dir) in extension_paths
        assert str(extension_dir_2) in extension_paths
        
        print("✅ 多扩展 Edge 配置创建成功")
    
    def test_edge_config_with_custom_user_agent(self):
        """测试带自定义 User-Agent 的 Edge 配置"""
        custom_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        
        config = BrowserConfig(
            browser_type=BrowserType.EDGE,
            headless=False,
            user_agent=custom_user_agent,
            extra_http_headers={
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br"
            }
        )
        
        # 验证配置
        assert config.user_agent == custom_user_agent
        assert "Accept-Language" in config.extra_http_headers
        assert "Accept-Encoding" in config.extra_http_headers
        
        print("✅ 自定义 User-Agent Edge 配置成功")
    
    def test_edge_config_performance_settings(self):
        """测试 Edge 性能相关配置"""
        config = BrowserConfig(
            browser_type=BrowserType.EDGE,
            headless=False,
            launch_args=[
                "--max_old_space_size=4096",  # 增加内存限制
                "--disable-background-timer-throttling",  # 禁用后台定时器节流
                "--disable-backgrounding-occluded-windows",  # 禁用被遮挡窗口的后台处理
                "--disable-renderer-backgrounding",  # 禁用渲染器后台处理
                "--disable-features=TranslateUI",  # 禁用翻译UI
                "--disable-ipc-flooding-protection",  # 禁用IPC洪水保护
            ],
            default_timeout=60000,  # 60秒超时
            navigation_timeout=60000,
            slow_mo=100  # 100ms 操作延迟
        )
        
        # 验证性能配置
        assert config.default_timeout == 60000
        assert config.navigation_timeout == 60000
        assert config.slow_mo == 100
        assert len(config.launch_args) == 6
        
        # 验证特定的性能参数
        performance_args = [
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding"
        ]
        
        for arg in performance_args:
            assert arg in config.launch_args
        
        print("✅ Edge 性能配置设置成功")


def test_comprehensive_edge_browser_setup():
    """综合测试：完整的 Edge 浏览器设置"""
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        # 创建扩展目录
        extension_dir = temp_dir / "ad_blocker_extension"
        extension_dir.mkdir(parents=True)
        
        # 创建扩展清单
        manifest = {
            "manifest_version": 3,
            "name": "Ad Blocker Plus",
            "version": "1.0.0",
            "description": "Block advertisements on web pages",
            "permissions": ["activeTab", "storage"],
            "action": {
                "default_popup": "popup.html",
                "default_title": "Ad Blocker Plus"
            }
        }
        
        import json
        (extension_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
        
        # 创建用户数据目录
        user_data_dir = temp_dir / "edge_profile"
        user_data_dir.mkdir(parents=True)
        
        # 创建完整的 Edge 配置
        edge_config = BrowserConfig(
            browser_type=BrowserType.EDGE,
            headless=False,  # 有头模式
            user_data_dir=user_data_dir,  # 自定义用户目录
            extensions=[
                ExtensionConfig(
                    path=extension_dir,
                    enabled=True,
                    options={
                        "block_ads": True,
                        "block_trackers": True,
                        "whitelist_domains": ["example.com", "test.com"]
                    }
                )
            ],
            viewport=ViewportConfig(
                width=1920,
                height=1080,
                device_scale_factor=1.0
            ),
            launch_args=[
                f"--load-extension={extension_dir}",
                "--disable-web-security",
                "--allow-running-insecure-content",
                "--disable-features=VizDisplayCompositor",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-background-timer-throttling"
            ],
            extra_http_headers={
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
            },
            default_timeout=30000,
            navigation_timeout=30000,
            debug_port=9222,
            devtools=False,
            slow_mo=50  # 50ms 延迟，便于观察
        )
        
        # 验证配置完整性
        assert edge_config.browser_type == BrowserType.EDGE
        assert edge_config.headless == False
        assert edge_config.user_data_dir == user_data_dir
        assert len(edge_config.extensions) == 1
        assert edge_config.extensions[0].enabled == True
        assert edge_config.viewport.width == 1920
        assert edge_config.debug_port == 9222
        
        # 验证扩展配置
        extension = edge_config.extensions[0]
        assert extension.options["block_ads"] == True
        assert "example.com" in extension.options["whitelist_domains"]
        
        # 验证启动参数
        assert f"--load-extension={extension_dir}" in edge_config.launch_args
        assert "--disable-web-security" in edge_config.launch_args
        
        # 测试配置序列化
        config_dict = edge_config.to_dict()
        restored_config = BrowserConfig.from_dict(config_dict)
        
        assert restored_config.browser_type == BrowserType.EDGE
        assert restored_config.headless == False
        
        print("✅ 综合 Edge 浏览器设置测试通过")
        print(f"   - 浏览器类型: {edge_config.browser_type.value}")
        print(f"   - 有头模式: {not edge_config.headless}")
        print(f"   - 用户目录: {edge_config.user_data_dir}")
        print(f"   - 扩展数量: {len(edge_config.extensions)}")
        print(f"   - 启动参数: {len(edge_config.launch_args)} 个")
        print(f"   - 调试端口: {edge_config.debug_port}")
        
    finally:
        # 清理临时目录
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # 运行综合测试
    test_comprehensive_edge_browser_setup()
    
    # 运行所有测试
    pytest.main([__file__, "-v"])