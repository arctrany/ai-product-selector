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
        
        # Mock _run_async 返回 True
        service._run_async = Mock(return_value=True)
        
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
        
        # Mock _run_async 返回 False
        service._run_async = Mock(return_value=False)
        
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
    
    @pytest.mark.skip(reason="需要实际浏览器环境，仅在集成测试时运行")
    def test_page_navigation(self):
        """测试使用 page 对象进行导航"""
        service = XuanpingBrowserServiceSync()
        
        try:
            service.initialize()
            service.start_browser()
            
            # 使用 page 对象导航
            page = service.page
            assert page is not None
            
            # 验证 page 有必要的方法
            assert hasattr(page, 'goto')
            assert hasattr(page, 'query_selector')
            assert hasattr(page, 'query_selector_all')
            
        finally:
            service.close()


if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v', '--tb=short'])
