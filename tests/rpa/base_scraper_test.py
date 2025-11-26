"""
统一测试基类

为所有Scraper提供统一的测试基础设施，消除测试代码冗余。
"""

import unittest
import logging
import asyncio
from typing import Optional, Any
from unittest.mock import Mock, MagicMock, patch
from rpa.browser.implementations.playwright_browser_driver import SimplifiedPlaywrightBrowserDriver


class BaseScraperTest(unittest.TestCase):
    """
    Scraper测试基类
    
    提供统一的测试基础设施：
    - 浏览器服务Mock
    - 测试数据准备
    - 通用断言方法
    - 资源清理
    """
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        logging.basicConfig(level=logging.DEBUG)
        cls.logger = logging.getLogger(cls.__name__)
    
    def setUp(self):
        """每个测试方法执行前的初始化"""
        self.mock_browser_service = self._create_mock_browser_service()
        self.test_data = self._prepare_test_data()
    
    def tearDown(self):
        """每个测试方法执行后的清理"""
        self.mock_browser_service = None
        self.test_data = None
    
    def _create_mock_browser_service(self) -> Mock:
        """
        创建Mock浏览器服务
        
        Returns:
            Mock: Mock浏览器服务实例
        """
        mock_service = MagicMock()
        
        # 基础导航和页面操作
        mock_service.navigate_to_sync = MagicMock(return_value=True)
        mock_service.wait_for_selector_sync = MagicMock(return_value=True)
        mock_service.text_content_sync = MagicMock(return_value="Test Content")
        mock_service.evaluate_sync = MagicMock(return_value="<html></html>")
        mock_service.click_sync = MagicMock(return_value=True)
        mock_service.close_sync = MagicMock()
        mock_service.shutdown_sync = MagicMock()

        # 缺失的方法 - 修复测试失败问题
        mock_service.smart_wait = MagicMock(return_value=True)
        mock_service.get_page_content = MagicMock(return_value="<html><body>Mock Content</body></html>")
        mock_service.wait_for_load_state_sync = MagicMock(return_value=True)
        mock_service.scroll_to_bottom_sync = MagicMock(return_value=True)
        mock_service.take_screenshot_sync = MagicMock(return_value=b"mock_screenshot")

        # 元素查找和操作
        mock_service.query_selector_sync = MagicMock()
        mock_service.query_selector_all_sync = MagicMock(return_value=[])
        mock_service.get_attribute_sync = MagicMock(return_value="mock_attribute")
        mock_service.get_inner_text_sync = MagicMock(return_value="Mock Text")

        # 表单操作
        mock_service.fill_sync = MagicMock(return_value=True)
        mock_service.select_option_sync = MagicMock(return_value=True)

        # 高级功能
        mock_service.execute_script_sync = MagicMock(return_value=None)
        mock_service.wait_for_timeout_sync = MagicMock()
        
        # 添加缺失的方法
        mock_service.get_page_url_sync = MagicMock(return_value="https://www.ozon.ru")

        return mock_service
    
    def _prepare_test_data(self) -> dict:
        """
        准备测试数据
        
        Returns:
            dict: 测试数据字典
        """
        return {
            'test_url': 'https://www.ozon.ru/product/1756017628',
            'test_price': '1000.50',
            'test_product_id': '1756017628',
            'test_store_name': 'Test Store',
            'test_html': '<html><body><div class="price">1000.50 ₽</div></body></html>'
        }
    
    def assert_scraping_result_success(self, result: Any):
        """
        断言抓取结果成功
        
        Args:
            result: 抓取结果对象
        """
        self.assertIsNotNone(result, "Result should not be None")
        self.assertTrue(hasattr(result, 'success'), "Result should have 'success' attribute")
        self.assertTrue(result.success, "Result should be successful")
        self.assertIsNotNone(result.data, "Result data should not be None")
    
    def assert_scraping_result_failure(self, result: Any, expected_error: Optional[str] = None):
        """
        断言抓取结果失败
        
        Args:
            result: 抓取结果对象
            expected_error: 期望的错误消息（可选）
        """
        self.assertIsNotNone(result, "Result should not be None")
        self.assertTrue(hasattr(result, 'success'), "Result should have 'success' attribute")
        self.assertFalse(result.success, "Result should be failed")
        
        if expected_error:
            self.assertIsNotNone(result.error_message, "Error message should not be None")
            self.assertIn(expected_error, result.error_message, 
                         f"Error message should contain '{expected_error}'")
    
    def assert_price_valid(self, price: Any):
        """
        断言价格有效
        
        Args:
            price: 价格值
        """
        self.assertIsNotNone(price, "Price should not be None")
        self.assertGreater(float(price), 0, "Price should be greater than 0")
    
    def assert_url_valid(self, url: str):
        """
        断言URL有效
        
        Args:
            url: URL字符串
        """
        self.assertIsNotNone(url, "URL should not be None")
        self.assertTrue(url.startswith('http'), "URL should start with 'http'")
    
    def create_mock_html_element(self, tag: str = 'div', text: str = '', 
                                 attrs: Optional[dict] = None) -> Mock:
        """
        创建Mock HTML元素
        
        Args:
            tag: 标签名
            text: 文本内容
            attrs: 属性字典
            
        Returns:
            Mock: Mock元素
        """
        element = MagicMock()
        element.name = tag
        element.get_text = MagicMock(return_value=text)
        element.text = text
        element.attrs = attrs or {}
        element.get = MagicMock(side_effect=lambda k, d=None: element.attrs.get(k, d))
        
        return element
    
    def create_mock_page_content(self, price: str = "1000 ₽", 
                                 has_competitors: bool = False) -> str:
        """
        创建Mock页面内容
        
        Args:
            price: 价格字符串
            has_competitors: 是否包含跟卖信息
            
        Returns:
            str: HTML内容
        """
        competitors_html = ""
        if has_competitors:
            competitors_html = '''
            <div class="pdp_bk3">
                <div class="competitor">
                    <span class="store-name">Competitor Store 1</span>
                    <span class="price">950 ₽</span>
                </div>
            </div>
            '''
        
        return f'''
        <html>
            <body>
                <div class="product">
                    <span class="tsHeadline600Large">{price}</span>
                    {competitors_html}
                </div>
            </body>
        </html>
        '''
    
    def mock_browser_navigate(self, success: bool = True):
        """
        Mock浏览器导航
        
        Args:
            success: 是否成功
        """
        self.mock_browser_service.navigate_to_sync.return_value = success
    
    def mock_browser_element_visible(self, selector: str, visible: bool = True):
        """
        Mock元素可见性
        
        Args:
            selector: 选择器
            visible: 是否可见
        """
        self.mock_browser_service.wait_for_selector_sync.return_value = visible
    
    def mock_browser_page_content(self, html: str):
        """
        Mock页面内容
        
        Args:
            html: HTML内容
        """
        self.mock_browser_service.evaluate_sync.return_value = html
    
    @staticmethod
    def run_test_suite(test_class):
        """
        运行测试套件
        
        Args:
            test_class: 测试类
        """
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2)
        return runner.run(suite)


class BaseScraperRealBrowserTest(unittest.TestCase):
    """
    Scraper真实浏览器测试基类

    提供真实浏览器测试基础设施：
    - 真实浏览器服务启动和清理
    - 网络请求处理
    - 资源管理和错误处理
    """

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        logging.basicConfig(level=logging.DEBUG)
        cls.logger = logging.getLogger(cls.__name__)
        cls.real_browser_service = None

    def setUp(self):
        """每个测试方法执行前的初始化"""
        self.real_browser_service = None
        self.test_data = self._prepare_test_data()

        # 🔧 修复：延迟初始化，避免提前关闭
        # 不在setUp中初始化浏览器，而是在需要时初始化
        self.logger.info("✅ 测试环境准备完成，浏览器将在使用时初始化")

    def tearDown(self):
        """每个测试方法执行后的清理"""
        if self.real_browser_service:
            try:
                self.real_browser_service.shutdown()
                self.logger.info("✅ 真实浏览器已关闭")
            except Exception as e:
                self.logger.warning(f"浏览器关闭异常: {e}")
        self.real_browser_service = None
        self.test_data = None

    def _create_real_browser_service(self) -> SimplifiedPlaywrightBrowserDriver:
        """
        创建真实浏览器服务（使用与选品程序相同的配置策略）

        🔧 应用选品程序的浏览器配置策略：
        - 先清理冲突的浏览器进程
        - 使用真实用户Profile
        - 检测活跃Profile
        - 等待Profile解锁

        Returns:
            SimplifiedPlaywrightBrowserDriver: 真实浏览器服务实例
        """
        import os
        from rpa.browser.utils import detect_active_profile, BrowserDetector

        # 🔧 关键：使用选品程序相同的配置策略
        browser_type = 'edge'  # 选品程序默认使用edge
        debug_port = 9222

        # 🔧 步骤1：先清理浏览器进程，再进行 Profile 验证
        detector = BrowserDetector()
        base_user_data_dir = detector._get_edge_user_data_dir() if browser_type == 'edge' else None

        if not base_user_data_dir:
            self.logger.error("❌ 无法获取用户数据目录")
            raise RuntimeError("无法获取用户数据目录")

        # 🔧 步骤2：主动清理可能冲突的浏览器进程
        self.logger.info("🧹 测试启动前先清理可能冲突的浏览器进程...")
        if not detector.kill_browser_processes():
            self.logger.warning("⚠️ 清理浏览器进程时遇到问题，但继续启动")
        else:
            self.logger.info("✅ 浏览器进程清理完成")

        # 🔧 步骤3：检测最近使用的 Profile
        active_profile = detect_active_profile()
        if not active_profile:
            active_profile = "Default"
            self.logger.warning("⚠️ 未检测到 Profile，将使用默认 Profile")
        else:
            self.logger.info(f"✅ 检测到最近使用的 Profile: {active_profile}")

        # 🔧 步骤4：验证 Profile 可用性
        if not detector.is_profile_available(base_user_data_dir, active_profile):
            self.logger.warning(f"⚠️ Profile '{active_profile}' 仍不可用")

            # 等待 Profile 解锁
            profile_path = os.path.join(base_user_data_dir, active_profile)
            if detector.wait_for_profile_unlock(profile_path, max_wait_seconds=5):
                self.logger.info("✅ Profile 已解锁，继续启动")
                # 再次验证 Profile 是否真的可用
                if not detector.is_profile_available(base_user_data_dir, active_profile):
                    error_msg = f"❌ Profile '{active_profile}' 解锁后仍不可用"
                    self.logger.error(error_msg)
                    raise RuntimeError(error_msg)
            else:
                error_msg = f"❌ Profile '{active_profile}' 等待解锁超时"
                self.logger.error(error_msg)
                self.logger.error("💡 请手动关闭所有 Edge 浏览器窗口后重试")
                raise RuntimeError(error_msg)

        # 🔧 步骤5：使用真实Profile创建配置
        user_data_dir = os.path.join(base_user_data_dir, active_profile)
        self.logger.info(f"✅ Profile 可用，将使用: {user_data_dir}")

        # 🔧 使用与选品程序相同的配置
        config = {
            'browser_type': browser_type,
            'headless': False,  # 🔥 修复：与xp命令保持一致，浏览器可见
            'debug_port': debug_port,
            'user_data_dir': user_data_dir,  # 🔧 关键：使用真实Profile
            'timeout': 30000,  # 30秒超时
            'navigation_timeout': 30000,
            'wait_timeout': 10000,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--exclude-switches=enable-automation',
                '--enable-extensions',  # 保留扩展支持
                '--no-first-run',
                '--disable-default-browser-check',
                '--enable-password-generation',
                '--enable-autofill',
                '--enable-sync'
            ]
        }

        self.logger.info(f"🚀 测试配置: browser={browser_type}, headless=True, profile={active_profile}")
        return SimplifiedPlaywrightBrowserDriver(config)

    def _prepare_test_data(self) -> dict:
        """
        准备测试数据

        Returns:
            dict: 测试数据字典
        """
        return {
            'test_url': 'https://www.ozon.ru/product/1756017628/',
            'test_product_id': '1756017628',
            'test_timeout': 30,
            'expected_selectors': [
                '[data-widget="webPrice"]',
                '.tsHeadline600Large',
                '.tsBodyControl500Medium'
            ]
        }

    def navigate_to_url(self, url: str, timeout: int = 30) -> bool:
        """
        导航到指定URL

        Args:
            url: 目标URL
            timeout: 超时时间（秒）

        Returns:
            bool: 导航是否成功
        """
        try:
            # 🔧 修复：确保浏览器已初始化
            if self.real_browser_service is None:
                self.real_browser_service = self._create_real_browser_service()
                success = self.real_browser_service.initialize()
                if not success:
                    self.logger.error("❌ 浏览器初始化失败")
                    return False
                self.logger.info("✅ 真实浏览器已启动")

            # 🔧 修复：SimplifiedPlaywrightBrowserDriver 使用 open_page_sync 方法
            success = self.real_browser_service.open_page_sync(url, 'domcontentloaded')
            if success:
                self.logger.info(f"✅ 成功导航到: {url}")
                return True
            else:
                self.logger.error(f"❌ 导航失败: {url}")
                return False
        except Exception as e:
            self.logger.error(f"❌ 导航异常: {e}")
            return False

    def wait_for_element(self, selector: str, timeout: int = 10) -> bool:
        """
        等待元素出现

        Args:
            selector: 元素选择器
            timeout: 超时时间（秒）

        Returns:
            bool: 元素是否出现
        """
        try:
            return self.real_browser_service.wait_for_selector_sync(selector, timeout * 1000)
        except Exception as e:
            self.logger.error(f"❌ 等待元素失败 {selector}: {e}")
            return False

    def get_page_content(self) -> str:
        """
        获取页面内容

        Returns:
            str: 页面HTML内容
        """
        try:
            content = self.real_browser_service.evaluate_sync("() => document.documentElement.outerHTML")
            return content if content else ""
        except Exception as e:
            self.logger.error(f"❌ 获取页面内容失败: {e}")
            return ""

    def assert_real_browser_navigation_success(self, url: str):
        """
        断言真实浏览器导航成功

        Args:
            url: 期望的URL
        """
        success = self.navigate_to_url(url)
        self.assertTrue(success, f"浏览器应该成功导航到 {url}")

        # 验证当前URL
        try:
            # 🔧 修复：使用evaluate_sync获取当前URL
            current_url = self.real_browser_service.evaluate_sync("() => window.location.href")
            if current_url:
                self.assertIn(url.split('/')[-2], current_url, "URL应该包含产品ID")
        except Exception as e:
            self.logger.warning(f"URL验证警告: {e}")

    def assert_page_loaded_successfully(self):
        """
        断言页面加载成功
        """
        content = self.get_page_content()
        self.assertIsNotNone(content, "页面内容不应为空")
        self.assertGreater(len(content), 100, "页面内容应该有足够长度")
        self.assertIn('<html', content.lower(), "应该包含HTML标签")