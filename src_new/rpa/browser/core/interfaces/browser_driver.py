"""
浏览器驱动接口定义

定义了浏览器驱动的标准接口，支持不同浏览器引擎的统一操作
遵循接口隔离原则，提供清晰的抽象层
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.browser_config import BrowserConfig
    from ..models.page_element import PageElement
    from ..exceptions.browser_exceptions import BrowserError
else:
    # 运行时使用字符串类型注解避免循环导入
    BrowserConfig = 'BrowserConfig'
    PageElement = 'PageElement'
    BrowserError = Exception


class IBrowserDriver(ABC):
    """浏览器驱动接口 - 定义浏览器操作的标准接口"""

    @abstractmethod
    async def initialize(self, config: BrowserConfig) -> bool:
        """
        初始化浏览器驱动
        
        Args:
            config: 浏览器配置
            
        Returns:
            bool: 初始化是否成功
            
        Raises:
            BrowserError: 初始化失败时抛出
        """
        pass

    @abstractmethod
    async def navigate_to(self, url: str, wait_until: str = 'networkidle') -> bool:
        """
        导航到指定URL
        
        Args:
            url: 目标URL
            wait_until: 等待条件
            
        Returns:
            bool: 导航是否成功
        """
        pass

    @abstractmethod
    async def find_element(self, selector: str, timeout: int = 10000) -> Optional[PageElement]:
        """
        查找页面元素
        
        Args:
            selector: 元素选择器
            timeout: 超时时间(毫秒)
            
        Returns:
            Optional[PageElement]: 找到的元素，未找到返回None
        """
        pass

    @abstractmethod
    async def find_elements(self, selector: str, timeout: int = 10000) -> List[PageElement]:
        """
        查找多个页面元素
        
        Args:
            selector: 元素选择器
            timeout: 超时时间(毫秒)
            
        Returns:
            List[PageElement]: 找到的元素列表
        """
        pass

    @abstractmethod
    async def click_element(self, selector: str, timeout: int = 10000) -> bool:
        """
        点击页面元素
        
        Args:
            selector: 元素选择器
            timeout: 超时时间(毫秒)
            
        Returns:
            bool: 点击是否成功
        """
        pass

    @abstractmethod
    async def input_text(self, selector: str, text: str, timeout: int = 10000) -> bool:
        """
        向元素输入文本
        
        Args:
            selector: 元素选择器
            text: 要输入的文本
            timeout: 超时时间(毫秒)
            
        Returns:
            bool: 输入是否成功
        """
        pass

    @abstractmethod
    async def take_screenshot(self, full_page: bool = False) -> Optional[bytes]:
        """
        截取页面截图
        
        Args:
            full_page: 是否截取整个页面
            
        Returns:
            Optional[bytes]: 截图数据，失败返回None
        """
        pass

    @abstractmethod
    async def execute_script(self, script: str, *args) -> Any:
        """
        执行JavaScript脚本
        
        Args:
            script: JavaScript代码
            *args: 脚本参数
            
        Returns:
            Any: 脚本执行结果
        """
        pass

    @abstractmethod
    async def wait_for_element(self, selector: str, timeout: int = 10000) -> bool:
        """
        等待元素出现
        
        Args:
            selector: 元素选择器
            timeout: 超时时间(毫秒)
            
        Returns:
            bool: 元素是否出现
        """
        pass

    @abstractmethod
    async def get_page_title(self) -> str:
        """
        获取页面标题
        
        Returns:
            str: 页面标题
        """
        pass

    @abstractmethod
    async def get_current_url(self) -> str:
        """
        获取当前页面URL
        
        Returns:
            str: 当前URL
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """关闭浏览器驱动，释放资源"""
        pass

    @abstractmethod
    def is_initialized(self) -> bool:
        """
        检查驱动是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        pass


class IPageManager(ABC):
    """页面管理器接口 - 管理多个页面/标签页"""

    @abstractmethod
    async def new_page(self) -> str:
        """
        创建新页面
        
        Returns:
            str: 页面ID
        """
        pass

    @abstractmethod
    async def switch_to_page(self, page_id: str) -> bool:
        """
        切换到指定页面
        
        Args:
            page_id: 页面ID
            
        Returns:
            bool: 切换是否成功
        """
        pass

    @abstractmethod
    async def close_page(self, page_id: str) -> bool:
        """
        关闭指定页面
        
        Args:
            page_id: 页面ID
            
        Returns:
            bool: 关闭是否成功
        """
        pass

    @abstractmethod
    async def get_all_pages(self) -> List[str]:
        """
        获取所有页面ID
        
        Returns:
            List[str]: 页面ID列表
        """
        pass


class IResourceManager(ABC):
    """资源管理器接口 - 管理浏览器资源生命周期"""

    @abstractmethod
    async def acquire_resource(self, resource_type: str, config: Dict[str, Any]) -> Any:
        """
        获取资源
        
        Args:
            resource_type: 资源类型
            config: 资源配置
            
        Returns:
            Any: 资源对象
        """
        pass

    @abstractmethod
    async def release_resource(self, resource: Any) -> None:
        """
        释放资源
        
        Args:
            resource: 要释放的资源
        """
        pass

    @abstractmethod
    async def cleanup_all(self) -> None:
        """清理所有资源"""
        pass