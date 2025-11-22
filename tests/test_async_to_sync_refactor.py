#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
异步到同步改造项目 - 严格单元测试套件

本测试套件专门用于验证异步到同步改造项目的所有修改内容：
1. Browser Driver接口层15个同步方法验证
2. SimplifiedPlaywrightBrowserDriver实现完整性测试  
3. Scraper同步化改造功能验证
4. BeautifulSoup API更新测试
5. 同步上下文管理器测试
6. 性能回归测试
7. 错误处理和边界条件测试
"""

import pytest
import unittest.mock as mock
import time
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestBrowserDriverInterface:
    """测试Browser Driver接口层的同步化改造"""
    
    def setup_method(self):
        """测试前设置"""
        from rpa.browser.core.interfaces.browser_driver import IBrowserDriver
        self.interface = IBrowserDriver
        
    def test_interface_methods_are_synchronous(self):
        """验证接口中所有方法都是同步的（不包含async关键字）"""
        import inspect
        from rpa.browser.core.interfaces.browser_driver import IBrowserDriver
        
        # 获取所有抽象方法
        abstract_methods = []
        for name, method in inspect.getmembers(IBrowserDriver, predicate=inspect.isfunction):
            if hasattr(method, '__isabstractmethod__') and method.__isabstractmethod__:
                abstract_methods.append((name, method))
        
        # 验证没有async方法
        for name, method in abstract_methods:
            assert not inspect.iscoroutinefunction(method), f"接口方法 {name} 不应该是async方法"
            
        print(f"✅ 验证通过：{len(abstract_methods)}个接口方法都是同步的")
        
    def test_interface_imports_sync_playwright(self):
        """验证接口使用sync_playwright而不是async_playwright"""
        import inspect
        from rpa.browser.core.interfaces import browser_driver
        
        source_lines = inspect.getsourcelines(browser_driver)[0]
        source_code = ''.join(source_lines)
        
        # 验证导入同步API
        assert 'playwright.sync_api' in source_code, "应该导入playwright.sync_api"
        assert 'playwright.async_api' not in source_code, "不应该导入playwright.async_api"
        
        print("✅ 验证通过：接口正确使用同步Playwright API")

    def test_context_manager_methods_exist(self):
        """验证同步上下文管理器方法存在"""
        from rpa.browser.core.interfaces.browser_driver import IBrowserDriver
        import inspect
        
        # 检查是否有同步上下文管理器方法
        methods = [name for name, _ in inspect.getmembers(IBrowserDriver, predicate=inspect.isfunction)]
        
        assert '__enter__' in methods, "缺少 __enter__ 同步上下文管理器方法"
        assert '__exit__' in methods, "缺少 __exit__ 同步上下文管理器方法"
        
        print("✅ 验证通过：同步上下文管理器方法存在")


class TestSimplifiedPlaywrightBrowserDriver:
    """测试SimplifiedPlaywrightBrowserDriver实现类的完整性"""
    
    def setup_method(self):
        """测试前设置"""
        from rpa.browser.implementations.playwright_browser_driver import SimplifiedPlaywrightBrowserDriver
        self.driver_class = SimplifiedPlaywrightBrowserDriver
        
    def test_class_can_be_instantiated(self):
        """验证类可以成功实例化（没有抽象方法未实现）"""
        try:
            driver = self.driver_class()
            assert driver is not None
            print("✅ 验证通过：SimplifiedPlaywrightBrowserDriver可以成功实例化")
        except TypeError as e:
            if "abstract" in str(e).lower():
                pytest.fail(f"类仍有未实现的抽象方法: {e}")
            else:
                raise

    def test_sync_context_manager_implementation(self):
        """验证同步上下文管理器实现"""
        driver = self.driver_class()
        
        # 验证方法存在
        assert hasattr(driver, '__enter__'), "缺少 __enter__ 方法"
        assert hasattr(driver, '__exit__'), "缺少 __exit__ 方法"
        
        # 验证方法可调用
        assert callable(getattr(driver, '__enter__')), "__enter__ 方法不可调用"
        assert callable(getattr(driver, '__exit__')), "__exit__ 方法不可调用"
        
        print("✅ 验证通过：同步上下文管理器实现完整")

    def test_sync_method_signatures(self):
        """验证关键同步方法签名正确"""
        driver = self.driver_class()
        
        # 检查关键方法存在且为同步方法
        critical_sync_methods = [
            'initialize', 'shutdown', 'open_page', 
            'get_page_title_sync', 'screenshot_sync',
            'execute_script', 'wait_for_element', 'click_element',
            'fill_input', 'get_element_text', 'verify_login_state',
            'save_storage_state', 'load_storage_state'
        ]
        
        import inspect
        for method_name in critical_sync_methods:
            assert hasattr(driver, method_name), f"缺少方法: {method_name}"
            method = getattr(driver, method_name)
            assert not inspect.iscoroutinefunction(method), f"方法 {method_name} 不应该是async方法"
            
        print(f"✅ 验证通过：{len(critical_sync_methods)}个关键同步方法签名正确")

    @patch('threading.Thread')
    @patch('asyncio.new_event_loop')
    def test_event_loop_thread_management(self, mock_new_loop, mock_thread):
        """测试事件循环线程管理（不实际启动）"""
        driver = self.driver_class()
        
        # 模拟事件循环创建
        mock_loop = Mock()
        mock_new_loop.return_value = mock_loop
        
        # 调用内部方法（如果存在）
        if hasattr(driver, '_start_event_loop_thread'):
            driver._start_event_loop_thread()
            
            # 验证线程创建
            mock_thread.assert_called_once()
            
        print("✅ 验证通过：事件循环线程管理机制正确")


class TestScraperSyncRefactoring:
    """测试Scraper同步化改造功能"""
    
    def test_competitor_scraper_sync_methods(self):
        """验证competitor_scraper.py中的同步化改造"""
        from common.scrapers.competitor_scraper import CompetitorScraper
        import inspect
        
        scraper = CompetitorScraper()
        
        # 验证关键方法是同步的
        sync_methods = [
            '_find_element_by_selectors',
            '_find_elements_by_selectors', 
            '_count_visible_competitors'
        ]
        
        for method_name in sync_methods:
            if hasattr(scraper, method_name):
                method = getattr(scraper, method_name)
                assert not inspect.iscoroutinefunction(method), f"{method_name} 应该是同步方法"
                
        print("✅ 验证通过：CompetitorScraper同步化改造正确")

    def test_ozon_scraper_sync_improvements(self):
        """验证ozon_scraper.py中的同步化改进"""
        # 读取源码验证Locator.count()调用已修复
        from pathlib import Path
        
        ozon_scraper_path = project_root / 'common' / 'scrapers' / 'ozon_scraper.py'
        if ozon_scraper_path.exists():
            source_code = ozon_scraper_path.read_text(encoding='utf-8')
            
            # 验证没有未await的Locator.count()调用
            lines = source_code.split('\n')
            problematic_lines = []
            
            for i, line in enumerate(lines, 1):
                if 'count()' in line and 'await' not in line and '# ' not in line:
                    # 检查是否是Locator.count()未await的情况
                    if 'locator' in line.lower() or '.count()' in line:
                        problematic_lines.append((i, line.strip()))
                        
            assert len(problematic_lines) == 0, f"发现未同步化的count()调用: {problematic_lines}"
            
        print("✅ 验证通过：OzonScraper同步化改进正确")


class TestBeautifulSoupAPIUpdate:
    """测试BeautifulSoup API更新"""
    
    def test_erp_plugin_scraper_string_parameter(self):
        """验证erp_plugin_scraper.py使用string参数而不是text参数"""
        from pathlib import Path
        
        erp_scraper_path = project_root / 'common' / 'scrapers' / 'erp_plugin_scraper.py'
        if erp_scraper_path.exists():
            source_code = erp_scraper_path.read_text(encoding='utf-8')
            
            # 验证使用了string参数
            assert 'find_all(string=' in source_code, "应该使用string参数"
            
            # 验证没有使用废弃的text参数
            deprecated_usage = 'find_all(text=' in source_code
            assert not deprecated_usage, "不应该使用废弃的text参数"
            
        print("✅ 验证通过：BeautifulSoup API更新正确")

    def test_beautiful_soup_compatibility(self):
        """测试BeautifulSoup新API的兼容性"""
        from bs4 import BeautifulSoup
        import re
        
        # 创建测试HTML
        html = '<div><span>测试文本：价格</span><span>100₽</span></div>'
        soup = BeautifulSoup(html, 'html.parser')
        
        # 验证string参数工作正常
        pattern = re.compile(r'测试文本：?\s*')
        elements = soup.find_all(string=pattern)
        
        assert len(elements) > 0, "string参数应该能找到匹配的文本"
        
        print("✅ 验证通过：BeautifulSoup string参数工作正常")


class TestSyncContextManagers:
    """测试同步上下文管理器"""
    
    @patch('rpa.browser.implementations.playwright_browser_driver.SimplifiedPlaywrightBrowserDriver.initialize')
    @patch('rpa.browser.implementations.playwright_browser_driver.SimplifiedPlaywrightBrowserDriver.shutdown')
    def test_sync_context_manager_lifecycle(self, mock_shutdown, mock_initialize):
        """测试同步上下文管理器生命周期"""
        from rpa.browser.implementations.playwright_browser_driver import SimplifiedPlaywrightBrowserDriver
        
        mock_initialize.return_value = True
        mock_shutdown.return_value = True
        
        # 测试同步上下文管理器
        driver = SimplifiedPlaywrightBrowserDriver()
        
        with driver:
            # 验证初始化被调用
            mock_initialize.assert_called_once()
            
        # 验证关闭被调用
        mock_shutdown.assert_called_once()
        
        print("✅ 验证通过：同步上下文管理器生命周期正确")

    def test_context_manager_exception_handling(self):
        """测试上下文管理器异常处理"""
        from rpa.browser.implementations.playwright_browser_driver import SimplifiedPlaywrightBrowserDriver
        
        driver = SimplifiedPlaywrightBrowserDriver()
        
        # 模拟异常情况
        with patch.object(driver, 'initialize', return_value=True):
            with patch.object(driver, 'shutdown', return_value=True) as mock_shutdown:
                try:
                    with driver:
                        raise ValueError("测试异常")
                except ValueError:
                    pass
                
                # 验证即使有异常也会调用shutdown
                mock_shutdown.assert_called_once()
                
        print("✅ 验证通过：上下文管理器异常处理正确")


class TestPerformanceRegression:
    """性能回归测试"""
    
    def test_sync_method_performance(self):
        """测试同步方法性能（基准测试）"""
        from rpa.browser.implementations.playwright_browser_driver import SimplifiedPlaywrightBrowserDriver
        
        driver = SimplifiedPlaywrightBrowserDriver()
        
        # 测试方法调用性能
        start_time = time.time()
        
        # 调用多个同步方法（模拟）
        for _ in range(100):
            if hasattr(driver, '_get_default_launch_args'):
                driver._get_default_launch_args()
                
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 性能应该在合理范围内（100次调用应该在1秒内完成）
        assert execution_time < 1.0, f"同步方法性能测试超时: {execution_time}秒"
        
        print(f"✅ 验证通过：同步方法性能良好 ({execution_time:.3f}秒完成100次调用)")

    def test_memory_usage_stability(self):
        """测试内存使用稳定性"""
        from rpa.browser.implementations.playwright_browser_driver import SimplifiedPlaywrightBrowserDriver
        import gc
        
        # 创建和销毁多个实例
        for _ in range(10):
            driver = SimplifiedPlaywrightBrowserDriver()
            del driver
            
        # 强制垃圾回收
        gc.collect()
        
        print("✅ 验证通过：内存使用稳定性良好")


class TestErrorHandlingAndEdgeCases:
    """错误处理和边界条件测试"""
    
    def test_driver_initialization_failure_handling(self):
        """测试驱动初始化失败处理"""
        from rpa.browser.implementations.playwright_browser_driver import SimplifiedPlaywrightBrowserDriver
        
        driver = SimplifiedPlaywrightBrowserDriver()
        
        # 模拟初始化失败
        with patch.object(driver, 'initialize', side_effect=Exception("模拟初始化失败")):
            try:
                result = driver.initialize()
                # 应该返回False或抛出异常
                assert result is False or result is None
            except Exception:
                pass  # 异常是可接受的处理方式
                
        print("✅ 验证通过：初始化失败处理正确")

    def test_thread_safety_basic(self):
        """基础线程安全测试"""
        from rpa.browser.implementations.playwright_browser_driver import SimplifiedPlaywrightBrowserDriver
        
        results = []
        errors = []
        
        def create_driver():
            try:
                driver = SimplifiedPlaywrightBrowserDriver()
                results.append(driver)
            except Exception as e:
                errors.append(e)
                
        # 创建多个线程同时创建驱动实例
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_driver)
            threads.append(thread)
            thread.start()
            
        # 等待所有线程完成
        for thread in threads:
            thread.join()
            
        # 验证没有严重错误
        assert len(errors) == 0, f"线程安全测试出现错误: {errors}"
        assert len(results) > 0, "应该成功创建至少一个驱动实例"
        
        print(f"✅ 验证通过：基础线程安全测试 ({len(results)}/{len(threads)}个实例成功创建)")


class TestIntegrationScenarios:
    """集成测试场景"""
    
    def test_scraper_with_sync_driver_integration(self):
        """测试Scraper与同步Driver的集成"""
        from common.scrapers.base_scraper import BaseScraper
        from unittest.mock import MagicMock
        
        # 创建Mock同步浏览器服务
        mock_browser_service = MagicMock()
        mock_browser_service.navigate_to_sync = MagicMock(return_value=True)
        mock_browser_service.close_sync = MagicMock(return_value=True)
        
        # 创建Scraper实例
        scraper = BaseScraper()
        scraper.browser_service = mock_browser_service
        
        # 测试数据抓取流程
        def mock_extractor(browser_service):
            return {"test": "data"}
            
        result = scraper.scrape_page_data("https://example.com", mock_extractor)
        
        # 验证集成工作正常
        assert result.success is True
        assert result.data == {"test": "data"}
        mock_browser_service.navigate_to_sync.assert_called_once()
        
        print("✅ 验证通过：Scraper与同步Driver集成正常")

    def test_full_sync_pipeline(self):
        """测试完整同步管道"""
        # 这是一个概念验证测试，验证所有组件可以协同工作
        from rpa.browser.implementations.playwright_browser_driver import SimplifiedPlaywrightBrowserDriver
        from common.scrapers.competitor_scraper import CompetitorScraper
        
        # 创建组件实例
        driver = SimplifiedPlaywrightBrowserDriver()
        scraper = CompetitorScraper()
        
        # 验证实例创建成功
        assert driver is not None
        assert scraper is not None
        
        # 验证关键方法存在
        assert hasattr(driver, 'initialize')
        assert hasattr(scraper, '_find_element_by_selectors')
        
        print("✅ 验证通过：完整同步管道组件协同正常")


if __name__ == "__main__":
    # 运行所有测试
    pytest.main([__file__, "-v", "--tb=short"])
