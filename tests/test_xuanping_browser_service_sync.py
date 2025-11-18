"""
XuanpingBrowserServiceSync 单元测试

测试浏览器服务的同步包装器，特别是简化后的 API 访问方式
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch
from common.scrapers.xuanping_browser_service import XuanpingBrowserServiceSync


class TestXuanpingBrowserServiceSync:
    """XuanpingBrowserServiceSync 单元测试"""
    
    def test_initial_state(self):
        """测试初始状态：page、browser、context 应为 None"""
        service = XuanpingBrowserServiceSync()
        
        assert service.page is None, "初始 page 应为 None"
        assert service.browser is None, "初始 browser 应为 None"
        assert service.context is None, "初始 context 应为 None"
        assert service.async_service is not None, "async_service 应该被创建"
    
    def test_has_required_attributes(self):
        """测试必需的属性存在"""
        service = XuanpingBrowserServiceSync()
        
        assert hasattr(service, 'page'), "应该有 page 属性"
        assert hasattr(service, 'browser'), "应该有 browser 属性"
        assert hasattr(service, 'context'), "应该有 context 属性"
        assert hasattr(service, 'async_service'), "应该有 async_service 属性"
        assert hasattr(service, 'logger'), "应该有 logger 属性"
    
    def test_has_update_method(self):
        """测试 _update_browser_objects 方法存在"""
        service = XuanpingBrowserServiceSync()
        
        assert hasattr(service, '_update_browser_objects'), "应该有 _update_browser_objects 方法"
        assert callable(service._update_browser_objects), "_update_browser_objects 应该是可调用的"
    
    @patch('common.scrapers.xuanping_browser_service.XuanpingBrowserService')
    def test_update_browser_objects_success(self, mock_async_service_class):
        """测试成功更新浏览器对象"""
        # 创建 mock 对象
        mock_page = Mock(name='MockPage')
        mock_browser = Mock(name='MockBrowser')
        mock_context = Mock(name='MockContext')
        
        mock_driver = Mock()
        mock_driver.page = mock_page
        mock_driver.browser = mock_browser
        mock_driver.context = mock_context
        
        mock_browser_service = Mock()
        mock_browser_service.browser_driver = mock_driver
        
        mock_async_service = Mock()
        mock_async_service.browser_service = mock_browser_service
        
        mock_async_service_class.return_value = mock_async_service
        
        # 创建服务并更新对象
        service = XuanpingBrowserServiceSync()
        service._update_browser_objects()
        
        # 验证属性已更新
        assert service.page is mock_page, "page 应该被更新"
        assert service.browser is mock_browser, "browser 应该被更新"
        assert service.context is mock_context, "context 应该被更新"
    
    @patch('common.scrapers.xuanping_browser_service.XuanpingBrowserService')
    def test_update_browser_objects_attribute_error(self, mock_async_service_class):
        """测试更新浏览器对象时的 AttributeError 处理"""
        # 创建一个会抛出 AttributeError 的 mock
        mock_async_service = Mock()
        mock_async_service.browser_service.browser_driver = None  # 会导致 AttributeError
        
        mock_async_service_class.return_value = mock_async_service
        
        service = XuanpingBrowserServiceSync()
        
        # 应该不抛出异常，而是记录警告
        service._update_browser_objects()
        
        # 属性应该保持为 None
        assert service.page is None
        assert service.browser is None
        assert service.context is None
    
    def test_start_browser_calls_update(self):
        """测试 start_browser 成功时会调用 _update_browser_objects"""
        service = XuanpingBrowserServiceSync()
        
        # 创建一个返回协程的 mock
        async def mock_start_browser():
            return True

        # Mock async_service.start_browser 返回协程
        service.async_service.start_browser = Mock(return_value=mock_start_browser())
        
        # Mock _update_browser_objects
        service._update_browser_objects = Mock()
        
        # 调用 start_browser
        result = service.start_browser()
        
        # 验证
        assert result is True, "start_browser 应该返回 True"
        service._update_browser_objects.assert_called_once(), "_update_browser_objects 应该被调用一次"
    
    def test_start_browser_no_update_on_failure(self):
        """测试 start_browser 失败时不调用 _update_browser_objects"""
        service = XuanpingBrowserServiceSync()
        
        # 创建一个返回协程的 mock
        async def mock_start_browser():
            return False

        # Mock async_service.start_browser 返回协程
        service.async_service.start_browser = Mock(return_value=mock_start_browser())
        
        # Mock _update_browser_objects
        service._update_browser_objects = Mock()
        
        # 调用 start_browser
        result = service.start_browser()
        
        # 验证
        assert result is False, "start_browser 应该返回 False"
        service._update_browser_objects.assert_not_called(), "_update_browser_objects 不应该被调用"
    
    def test_shared_event_loop_initialization(self):
        """测试共享事件循环被正确初始化"""
        service = XuanpingBrowserServiceSync()
        
        # 验证类级别的共享事件循环相关属性存在
        assert hasattr(XuanpingBrowserServiceSync, '_shared_loop')
        assert hasattr(XuanpingBrowserServiceSync, '_shared_thread')
        assert hasattr(XuanpingBrowserServiceSync, '_loop_lock')
        
        # 验证锁已被初始化
        assert XuanpingBrowserServiceSync._loop_lock is not None
    
    def test_multiple_instances_share_loop(self):
        """测试多个实例共享同一个事件循环"""
        service1 = XuanpingBrowserServiceSync()
        service2 = XuanpingBrowserServiceSync()
        
        # 两个实例应该使用相同的类级别共享循环
        assert XuanpingBrowserServiceSync._shared_loop is not None
        
        # 验证两个实例的 async_service 都是 XuanpingBrowserService 的实例
        assert service1.async_service is not None
        assert service2.async_service is not None


class TestXuanpingBrowserServiceSyncIntegration:
    """XuanpingBrowserServiceSync 集成测试（需要实际浏览器环境）"""
    
    @pytest.mark.skip(reason="需要实际浏览器环境，仅在集成测试时运行")
    def test_full_workflow(self):
        """测试完整的工作流程：初始化 -> 启动 -> 访问 page"""
        service = XuanpingBrowserServiceSync()
        
        try:
            # 初始化
            assert service.initialize() is True
            
            # 启动浏览器
            assert service.start_browser() is True
            
            # 验证 page 对象可用
            assert service.page is not None
            assert service.browser is not None
            assert service.context is not None
            
            # 验证 page 对象的类型
            from playwright.async_api import Page
            assert isinstance(service.page, Page)
            
        finally:
            # 清理
            service.close()
    
    @pytest.mark.skip(reason="需要关闭所有 Edge 浏览器实例后手动运行。运行前请：1) 关闭所有 Edge 窗口 2) 运行: pytest tests/test_xuanping_browser_service_sync.py::TestXuanpingBrowserServiceSyncIntegration::test_page_navigation -v -s")
    def test_page_navigation(self):
        """测试使用 page 对象进行实际页面导航

        ⚠️ 运行此测试前的准备工作：
        1. 关闭所有 Microsoft Edge 浏览器窗口
        2. 确保端口 9222 未被占用
        3. 运行命令：pytest tests/test_xuanping_browser_service_sync.py::TestXuanpingBrowserServiceSyncIntegration::test_page_navigation -v -s

        测试内容：
        1. page 对象可以成功导航到 URL
        2. 可以使用简化的 API (browser_service.page) 进行操作
        3. 页面加载成功并能查询元素
        4. 访问真实的 Ozon 商品页面：https://www.ozon.ru/product/2369901364
        """
        import time

        # 使用项目默认配置创建服务
        service = XuanpingBrowserServiceSync()

        try:
            # 初始化浏览器服务
            init_success = service.initialize()
            assert init_success is True, "浏览器服务初始化失败"

            # 启动浏览器
            start_success = service.start_browser()
            assert start_success is True, "浏览器启动失败"

            # 验证 page 对象已通过简化 API 暴露
            page = service.page
            assert page is not None, "page 对象应该通过 service.page 直接访问"
            assert service.browser is not None, "browser 对象应该可用"
            assert service.context is not None, "context 对象应该可用"

            # 测试页面导航 - 访问 Ozon 商品页面
            test_url = "https://www.ozon.ru/product/2369901364"
            service.logger.info(f"🌐 导航到测试页面: {test_url}")

            # 使用简化的 API 进行导航
            goto_result = service.goto(test_url, wait_until='domcontentloaded', timeout=30000)
            assert goto_result is True, f"页面导航失败: {test_url}"

            # 等待页面稳定
            time.sleep(2)

            # 验证页面加载成功 - 检查 URL
            current_url = service.get_current_url()
            assert current_url is not None, "无法获取当前 URL"
            assert "ozon.ru" in current_url, f"URL 不正确: {current_url}"

            # 验证可以使用 page 对象查询元素
            # 尝试查找页面标题或商品信息
            title_selector = "h1"
            title_element = service.query_selector(title_selector)

            if title_element:
                service.logger.info("✅ 成功找到页面标题元素")
            else:
                service.logger.warning("⚠️ 未找到标题元素，可能页面结构已变化")

            # 验证 page 对象的核心方法可用
            assert hasattr(page, 'goto'), "page 应该有 goto 方法"
            assert hasattr(page, 'query_selector'), "page 应该有 query_selector 方法"
            assert hasattr(page, 'query_selector_all'), "page 应该有 query_selector_all 方法"
            assert hasattr(page, 'url'), "page 应该有 url 属性"

            service.logger.info("✅ 页面导航测试通过")

        except Exception as e:
            service.logger.error(f"❌ 页面导航测试失败: {e}")
            raise
        finally:
            # 清理资源
            try:
                service.close()
                service.logger.info("🧹 浏览器服务已关闭")
            except Exception as e:
                service.logger.warning(f"关闭浏览器时出错: {e}")


if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v', '--tb=short'])
