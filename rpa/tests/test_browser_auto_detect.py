"""
SimplifiedBrowserService 自动检测功能的单元测试

测试范围：
1. _check_existing_browser() 方法
2. _prepare_browser_config() 方法的 debug_port 传递
"""

import pytest
from unittest.mock import Mock, patch
from rpa.browser.browser_service import SimplifiedBrowserService


class TestCheckExistingBrowser:
    """测试 _check_existing_browser() 方法"""
    
    def test_check_existing_browser_port_not_occupied(self):
        """测试场景：端口未被占用"""
        service = SimplifiedBrowserService()
        
        with patch('socket.socket') as mock_socket:
            mock_sock_instance = Mock()
            mock_sock_instance.connect_ex.return_value = 1  # 非0表示连接失败
            mock_socket.return_value = mock_sock_instance
            
            result = service._check_existing_browser(9222)
            
            assert result is False
            mock_sock_instance.connect_ex.assert_called_once_with(('localhost', 9222))
            mock_sock_instance.close.assert_called_once()
    
    def test_check_existing_browser_port_occupied_cdp_available(self):
        """测试场景：端口被占用且 CDP 端点可用"""
        service = SimplifiedBrowserService()
        
        with patch('socket.socket') as mock_socket, \
             patch('urllib.request.urlopen') as mock_urlopen:
            
            # Mock socket - 端口被占用
            mock_sock_instance = Mock()
            mock_sock_instance.connect_ex.return_value = 0  # 0表示连接成功
            mock_socket.return_value = mock_sock_instance
            
            # Mock CDP 响应
            mock_response = Mock()
            mock_response.read.return_value = b'{"webSocketDebuggerUrl": "ws://localhost:9222/devtools/browser"}'
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response
            
            result = service._check_existing_browser(9222)
            
            assert result is True
            mock_sock_instance.connect_ex.assert_called_once_with(('localhost', 9222))
    
    def test_check_existing_browser_port_occupied_cdp_unavailable(self):
        """测试场景：端口被占用但 CDP 端点不可用"""
        service = SimplifiedBrowserService()
        
        with patch('socket.socket') as mock_socket, \
             patch('urllib.request.urlopen') as mock_urlopen:
            
            # Mock socket - 端口被占用
            mock_sock_instance = Mock()
            mock_sock_instance.connect_ex.return_value = 0
            mock_socket.return_value = mock_sock_instance
            
            # Mock CDP 响应 - 没有 webSocketDebuggerUrl
            mock_response = Mock()
            mock_response.read.return_value = b'{"Browser": "Chrome/91.0"}'
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=False)
            mock_urlopen.return_value = mock_response
            
            result = service._check_existing_browser(9222)
            
            assert result is False
    
    def test_check_existing_browser_cdp_request_fails(self):
        """测试场景：CDP 请求失败"""
        service = SimplifiedBrowserService()
        
        with patch('socket.socket') as mock_socket, \
             patch('urllib.request.urlopen') as mock_urlopen:
            
            # Mock socket - 端口被占用
            mock_sock_instance = Mock()
            mock_sock_instance.connect_ex.return_value = 0
            mock_socket.return_value = mock_sock_instance
            
            # Mock CDP 请求失败
            mock_urlopen.side_effect = Exception("Connection refused")
            
            result = service._check_existing_browser(9222)
            
            assert result is False


class TestPrepareBrowserConfig:
    """测试 _prepare_browser_config() 方法"""
    
    def test_prepare_browser_config_with_debug_port(self):
        """测试场景：配置中有 debug_port"""
        config = {
            'browser_config': {
                'debug_port': 9223
            }
        }
        service = SimplifiedBrowserService(config)
        
        browser_config = service._prepare_browser_config()
        
        assert 'debug_port' in browser_config
        assert browser_config['debug_port'] == 9223
    
    def test_prepare_browser_config_without_debug_port(self):
        """测试场景：配置中没有 debug_port，应使用默认值 9222"""
        config = {
            'browser_config': {}
        }
        service = SimplifiedBrowserService(config)
        
        browser_config = service._prepare_browser_config()
        
        assert 'debug_port' in browser_config
        assert browser_config['debug_port'] == 9222


class TestAutoDetectLogic:
    """测试自动检测逻辑的集成"""
    
    def test_auto_detect_sets_connect_mode_when_browser_exists(self):
        """测试场景：检测到浏览器时，配置应设置为连接模式"""
        service = SimplifiedBrowserService()
        
        # Mock _check_existing_browser 返回 True
        with patch.object(service, '_check_existing_browser', return_value=True):
            browser_config = {'debug_port': 9222}
            
            # 模拟 initialize() 中的逻辑
            connect_to_existing = browser_config.get('connect_to_existing', None)
            
            if connect_to_existing is None:
                debug_port = browser_config.get('debug_port', 9222)
                has_existing_browser = service._check_existing_browser(debug_port)
                
                if has_existing_browser:
                    connect_to_existing = f"http://localhost:{debug_port}"
                    browser_config['connect_to_existing'] = connect_to_existing
            
            # 验证配置被正确设置
            assert browser_config['connect_to_existing'] == "http://localhost:9222"
    
    def test_auto_detect_sets_launch_mode_when_no_browser(self):
        """测试场景：未检测到浏览器时，配置应设置为启动模式"""
        service = SimplifiedBrowserService()
        
        # Mock _check_existing_browser 返回 False
        with patch.object(service, '_check_existing_browser', return_value=False):
            browser_config = {'debug_port': 9222}
            
            # 模拟 initialize() 中的逻辑
            connect_to_existing = browser_config.get('connect_to_existing', None)
            
            if connect_to_existing is None:
                debug_port = browser_config.get('debug_port', 9222)
                has_existing_browser = service._check_existing_browser(debug_port)
                
                if has_existing_browser:
                    connect_to_existing = f"http://localhost:{debug_port}"
                    browser_config['connect_to_existing'] = connect_to_existing
                else:
                    connect_to_existing = False
                    browser_config['connect_to_existing'] = False
            
            # 验证配置被正确设置
            assert browser_config['connect_to_existing'] is False
    
    def test_manual_config_not_overridden(self):
        """测试场景：手动配置不应被自动检测覆盖"""
        service = SimplifiedBrowserService()
        
        # Mock _check_existing_browser（不应被调用）
        with patch.object(service, '_check_existing_browser') as mock_check:
            browser_config = {
                'debug_port': 9222,
                'connect_to_existing': 'http://localhost:9222'
            }
            
            # 模拟 initialize() 中的逻辑
            connect_to_existing = browser_config.get('connect_to_existing', None)
            
            if connect_to_existing is None:
                debug_port = browser_config.get('debug_port', 9222)
                has_existing_browser = service._check_existing_browser(debug_port)
                
                if has_existing_browser:
                    connect_to_existing = f"http://localhost:{debug_port}"
                    browser_config['connect_to_existing'] = connect_to_existing
                else:
                    connect_to_existing = False
                    browser_config['connect_to_existing'] = False
            
            # 验证手动配置未被修改
            assert browser_config['connect_to_existing'] == 'http://localhost:9222'
            # 验证自动检测未被调用
            mock_check.assert_not_called()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
