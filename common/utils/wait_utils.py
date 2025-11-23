"""
统一时序控制工具类

提供标准化的等待和时序控制功能，用于所有Scraper的时序管理。
"""

import time
import logging
from typing import Optional, Callable, Any


class WaitUtils:
    """
    统一时序控制工具类
    
    提供标准化的等待和时序控制功能
    """
    
    def __init__(self, browser_service=None, logger: Optional[logging.Logger] = None):
        """
        初始化时序控制工具
        
        Args:
            browser_service: 浏览器服务实例
            logger: 日志记录器
        """
        self.browser_service = browser_service
        self.logger = logger or logging.getLogger(__name__)
        
        # 默认超时配置
        self.default_timeouts = {
            'element_visible': 15.0,
            'element_clickable': 15.0,
            'url_change': 30.0,
            'page_load': 45.0
        }
    
    def smart_wait(self, seconds: float):
        """
        智能等待
        
        Args:
            seconds: 等待秒数
        """
        if seconds > 0:
            self.logger.debug(f"⏳ 智能等待 {seconds} 秒")
            time.sleep(seconds)
    
    def wait_for_element_visible(self, selector: str, timeout: Optional[float] = None) -> bool:
        """
        等待元素可见
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（秒）
            
        Returns:
            bool: 元素是否可见
        """
        if timeout is None:
            timeout = self.default_timeouts['element_visible']
        
        try:
            if not self.browser_service:
                self.logger.error("Browser service not initialized")
                return False
            
            # 使用浏览器服务等待元素可见
            result = self.browser_service.wait_for_selector_sync(
                selector, 
                state='visible', 
                timeout=int(timeout * 1000)
            )
            return result
        except Exception as e:
            self.logger.warning(f"等待元素可见失败: {e}")
            return False
    
    def wait_for_element_clickable(self, selector: str, timeout: Optional[float] = None) -> bool:
        """
        等待元素可点击
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（秒）
            
        Returns:
            bool: 元素是否可点击
        """
        if timeout is None:
            timeout = self.default_timeouts['element_clickable']
        
        try:
            if not self.browser_service:
                self.logger.error("Browser service not initialized")
                return False
            
            # 使用浏览器服务等待元素可点击
            result = self.browser_service.wait_for_selector_sync(
                selector, 
                state='visible', 
                timeout=int(timeout * 1000)
            )
            return result
        except Exception as e:
            self.logger.warning(f"等待元素可点击失败: {e}")
            return False
    
    def wait_for_url_change(self, expected_url: str = None, timeout: Optional[float] = None) -> bool:
        """
        等待URL变化
        
        Args:
            expected_url: 期望的URL（可选）
            timeout: 超时时间（秒）
            
        Returns:
            bool: URL是否变化到期望值
        """
        if timeout is None:
            timeout = self.default_timeouts['url_change']
        
        try:
            if not self.browser_service:
                self.logger.error("Browser service not initialized")
                return False
            
            start_time = time.time()
            initial_url = self.browser_service.get_page_url_sync()
            
            while time.time() - start_time < timeout:
                current_url = self.browser_service.get_page_url_sync()
                if current_url != initial_url:
                    if expected_url is None or expected_url in current_url:
                        return True
                time.sleep(0.5)
            
            return False
        except Exception as e:
            self.logger.warning(f"等待URL变化失败: {e}")
            return False
    
    def wait_for_page_load(self, timeout: Optional[float] = None) -> bool:
        """
        等待页面加载完成
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            bool: 页面是否加载完成
        """
        if timeout is None:
            timeout = self.default_timeouts['page_load']
        
        try:
            if not self.browser_service:
                self.logger.error("Browser service not initialized")
                return False
            
            # 等待页面加载状态变为complete
            self.browser_service.wait_for_load_state_sync('networkidle', int(timeout * 1000))
            return True
        except Exception as e:
            self.logger.warning(f"等待页面加载完成失败: {e}")
            return False
    
    def execute_with_timeout(self, func: Callable, timeout: float, operation_name: str = "操作") -> Any:
        """
        带超时控制的执行函数
        
        Args:
            func: 要执行的函数
            timeout: 超时时间（秒）
            operation_name: 操作名称
            
        Returns:
            函数执行结果
            
        Raises:
            TimeoutError: 超时异常
        """
        start_time = time.time()
        
        try:
            result = func()
            elapsed = time.time() - start_time
            self.logger.debug(f"✅ {operation_name} 完成，耗时 {elapsed:.2f} 秒")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                self.logger.error(f"⏱️ {operation_name} 超时 ({elapsed:.2f}s >= {timeout}s)")
                raise TimeoutError(f"{operation_name} 超时")
            else:
                self.logger.error(f"❌ {operation_name} 执行失败: {e}")
                raise


# 全局实例管理
_wait_utils_instance = None


def get_global_wait_utils(browser_service=None, logger=None) -> WaitUtils:
    """
    获取全局WaitUtils实例
    
    Args:
        browser_service: 浏览器服务实例
        logger: 日志记录器
        
    Returns:
        WaitUtils: 全局WaitUtils实例
    """
    global _wait_utils_instance
    
    if _wait_utils_instance is None:
        _wait_utils_instance = WaitUtils(browser_service, logger)
    
    return _wait_utils_instance


def reset_global_wait_utils():
    """重置全局WaitUtils实例"""
    global _wait_utils_instance
    _wait_utils_instance = None
