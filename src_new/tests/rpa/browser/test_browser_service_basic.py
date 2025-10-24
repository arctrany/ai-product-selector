import sys
import os
from pathlib import Path
import pytest

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src_new.rpa.browser.browser_service import BrowserService
from src_new.rpa.browser.config import RPAConfig

def test_init_and_shutdown():
    """测试基本的初始化和关闭功能"""
    cfg = RPAConfig(overrides={"backend": "playwright", "headless": True})
    service = BrowserService(cfg)
    assert not service.is_initialized()
    
    # 测试初始化
    success = service.initialize()
    assert success == True
    assert service.is_initialized()
    
    # 测试关闭
    success = service.shutdown()
    assert success == True
    assert not service.is_initialized()

def test_screenshot_creates_nonempty_file(tmp_path: Path):
    """测试截图功能"""
    cfg = RPAConfig(overrides={"backend": "playwright", "headless": True})
    service = BrowserService(cfg)
    service.initialize()
    
    # 先打开一个非 about:blank 的页面，确保旧引擎能选择到活动页进行截图
    service.open_page("https://example.com")
    
    target = tmp_path / "shot.png"
    out = service.screenshot(target)
    assert out.exists()
    assert out.stat().st_size > 0
    
    # 清理
    service.shutdown()

def test_config_validation():
    """测试配置验证"""
    # 测试有效配置
    valid_config = RPAConfig(overrides={
        "backend": "playwright", 
        "headless": True,
        "browser_type": "chromium"
    })
    assert valid_config.validate() == True
    
    # 测试无效配置
    invalid_config = RPAConfig(overrides={
        "backend": "invalid_backend", 
        "headless": True
    })
    assert invalid_config.validate() == False

def test_browser_service_methods():
    """测试浏览器服务的各种方法"""
    cfg = RPAConfig(overrides={"backend": "playwright", "headless": True})
    service = BrowserService(cfg)
    
    # 测试未初始化状态
    assert service.get_page_title() is None
    assert service.get_page_url() is None
    assert service.get_driver() is None
    
    # 初始化后测试
    service.initialize()
    
    # 测试获取组件
    assert service.get_driver() is not None
    assert service.get_browser() is not None
    assert service.get_context() is not None
    assert service.get_page() is not None
    
    # 测试页面操作
    success = service.open_page("https://example.com")
    assert success == True
    
    title = service.get_page_title()
    assert title is not None
    
    url = service.get_page_url()
    assert url is not None
    assert "example.com" in url
    
    # 清理
    service.shutdown()

def test_element_operations():
    """测试元素操作功能"""
    cfg = RPAConfig(overrides={"backend": "playwright", "headless": True})
    service = BrowserService(cfg)
    service.initialize()
    
    # 打开测试页面
    service.open_page("https://example.com")
    
    # 测试等待元素（这个元素应该存在）
    exists = service.wait_for_element("h1", timeout=5000)
    assert exists == True
    
    # 测试获取元素文本
    text = service.get_element_text("h1")
    assert text is not None
    assert len(text) > 0
    
    # 测试不存在的元素
    exists = service.wait_for_element("nonexistent-element", timeout=1000)
    assert exists == False
    
    # 清理
    service.shutdown()

def test_javascript_execution():
    """测试JavaScript执行功能"""
    cfg = RPAConfig(overrides={"backend": "playwright", "headless": True})
    service = BrowserService(cfg)
    service.initialize()
    
    # 打开测试页面
    service.open_page("https://example.com")
    
    # 测试简单的JavaScript执行
    result = service.execute_script("return document.title")
    assert result is not None
    
    # 测试返回数值的JavaScript
    result = service.execute_script("return 1 + 1")
    assert result == 2
    
    # 测试返回对象的JavaScript
    result = service.execute_script("return {test: 'value'}")
    assert isinstance(result, dict)
    assert result.get('test') == 'value'
    
    # 清理
    service.shutdown()

def test_multiple_initialization():
    """测试多次初始化的处理"""
    cfg = RPAConfig(overrides={"backend": "playwright", "headless": True})
    service = BrowserService(cfg)
    
    # 第一次初始化
    success1 = service.initialize()
    assert success1 == True
    assert service.is_initialized()
    
    # 第二次初始化（应该不会重复初始化）
    success2 = service.initialize()
    assert success2 == True
    assert service.is_initialized()
    
    # 清理
    service.shutdown()

def test_error_handling():
    """测试错误处理"""
    cfg = RPAConfig(overrides={"backend": "playwright", "headless": True})
    service = BrowserService(cfg)
    
    # 测试未初始化时的操作
    assert service.open_page("https://example.com") == False
    assert service.click_element("button") == False
    assert service.fill_input("input", "text") == False
    
    # 初始化后测试无效操作
    service.initialize()
    
    # 测试无效URL
    success = service.open_page("invalid-url")
    assert success == False
    
    # 测试无效选择器
    success = service.click_element("invalid::selector")
    assert success == False
    
    # 清理
    service.shutdown()