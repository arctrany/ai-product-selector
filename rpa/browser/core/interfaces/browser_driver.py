"""
浏览器驱动接口定义

本模块定义了浏览器驱动的抽象接口，
遵循依赖倒置原则，让上层模块依赖抽象而不是具体实现。
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from playwright.sync_api import Browser, BrowserContext, Page


class IBrowserDriver(ABC):
    """
    浏览器驱动抽象接口
    
    定义了浏览器驱动必须实现的核心方法，
    支持依赖注入和多种浏览器引擎实现。
    """

    # ========================================
    # 🚀 生命周期管理接口
    # ========================================

    @abstractmethod
    def initialize(self) -> bool:
        """
        同步初始化浏览器驱动
        
        Returns:
            bool: 初始化是否成功
        """
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """
        同步关闭浏览器驱动
        
        Returns:
            bool: 关闭是否成功
        """
        pass

    @abstractmethod
    def is_initialized(self) -> bool:
        """
        检查驱动是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        pass

    # ========================================
    # 🌐 页面导航接口
    # ========================================

    @abstractmethod
    def open_page(self, url: str, wait_until: str = 'networkidle') -> bool:
        """
        打开指定URL的页面
        
        Args:
            url: 要打开的URL
            wait_until: 等待条件
            
        Returns:
            bool: 操作是否成功
        """
        pass

    @abstractmethod
    def get_page_url(self) -> Optional[str]:
        """
        获取当前页面URL
        
        Returns:
            Optional[str]: 页面URL
        """
        pass

    @abstractmethod
    def get_page_title_sync(self) -> Optional[str]:
        """
        同步获取当前页面标题
        
        Returns:
            Optional[str]: 页面标题，失败时返回 None
        """
        pass

    # ========================================
    # 📸 页面操作接口
    # ========================================

    @abstractmethod
    def screenshot_sync(self, file_path: Union[str, Path]) -> Optional[Path]:
        """
        同步截取当前页面的截图
        
        Args:
            file_path: 截图保存路径
            
        Returns:
            Optional[Path]: 截图文件路径，失败时返回 None
        """
        pass

    @abstractmethod
    def execute_script(self, script: str) -> Any:
        """
        同步执行JavaScript脚本
        
        Args:
            script: JavaScript代码
            
        Returns:
            Any: 脚本执行结果
        """
        pass

    # ========================================
    # 🎯 元素交互接口
    # ========================================

    @abstractmethod
    def wait_for_element(self, selector: str, timeout: int = 30000) -> bool:
        """
        等待元素出现
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            
        Returns:
            bool: 元素是否出现
        """
        pass

    @abstractmethod
    def click_element(self, selector: str) -> bool:
        """
        点击指定元素
        
        Args:
            selector: 元素选择器
            
        Returns:
            bool: 操作是否成功
        """
        pass

    @abstractmethod
    def fill_input(self, selector: str, text: str) -> bool:
        """
        填充输入框
        
        Args:
            selector: 输入框选择器
            text: 要填充的文本
            
        Returns:
            bool: 操作是否成功
        """
        pass

    @abstractmethod
    def get_element_text(self, selector: str) -> Optional[str]:
        """
        同步获取元素文本内容
        
        Args:
            selector: 元素选择器
            
        Returns:
            Optional[str]: 元素文本内容，失败时返回 None
        """
        pass

    # ========================================
    # 🔍 访问器接口
    # ========================================

    @abstractmethod
    def get_page(self) -> Optional[Page]:
        """
        获取页面对象
        
        Returns:
            Optional[Page]: 页面对象
        """
        pass

    @abstractmethod
    def get_context(self) -> Optional[BrowserContext]:
        """
        获取浏览器上下文
        
        Returns:
            Optional[BrowserContext]: 浏览器上下文
        """
        pass

    @abstractmethod
    def get_browser(self) -> Optional[Browser]:
        """
        获取浏览器实例
        
        Returns:
            Optional[Browser]: 浏览器实例
        """
        pass

    # ========================================
    # 🔐 会话管理接口
    # ========================================

    @abstractmethod
    def verify_login_state(self, domain: str) -> Dict[str, Any]:
        """
        验证指定域名的登录状态

        Args:
            domain: 要验证的域名

        Returns:
            Dict[str, Any]: 验证结果
        """
        pass

    @abstractmethod
    def save_storage_state(self, file_path: str) -> bool:
        """
        保存浏览器存储状态到文件

        Args:
            file_path: 保存路径

        Returns:
            bool: 保存是否成功
        """
        pass

    @abstractmethod
    def load_storage_state(self, file_path: str) -> bool:
        """
        从文件加载浏览器存储状态

        Args:
            file_path: 文件路径

        Returns:
            bool: 加载是否成功
        """
        pass

    # ========================================
    # 🔄 同步兼容接口
    # ========================================

    @abstractmethod
    def screenshot(self, file_path: Union[str, Path]) -> Optional[Path]:
        """
        同步截图方法（向后兼容）
        
        Args:
            file_path: 截图保存路径
            
        Returns:
            Optional[Path]: 截图文件路径
        """
        pass

    @abstractmethod
    def get_page_title(self) -> Optional[str]:
        """
        同步获取页面标题方法（向后兼容）
        
        Returns:
            Optional[str]: 页面标题
        """
        pass

    # ========================================
    # 🔄 上下文管理器接口
    # ========================================

    @abstractmethod
    def __enter__(self):
        """同步上下文管理器入口"""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """同步上下文管理器出口"""
        pass