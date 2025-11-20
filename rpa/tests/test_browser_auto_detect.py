"""
SimplifiedBrowserService 浏览器配置的单元测试

测试范围：
1. _prepare_browser_config() 方法的 debug_port 传递
"""

import pytest
from unittest.mock import Mock, patch
from rpa.browser.browser_service import SimplifiedBrowserService



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



if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
