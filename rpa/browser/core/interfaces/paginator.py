"""
分页器接口定义

定义分页处理的标准接口，支持不同类型的分页方式
包括数字分页、滚动分页、加载更多等模式
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable, AsyncGenerator
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.page_element import PageElement
    from ..exceptions.browser_exceptions import BrowserError
else:
    PageElement = 'PageElement'
    BrowserError = Exception


class PaginationType(Enum):
    """分页类型枚举"""
    NUMERIC = "numeric"  # 数字分页
    SCROLL = "scroll"    # 滚动分页
    LOAD_MORE = "load_more"  # 加载更多按钮
    INFINITE = "infinite"    # 无限滚动
    CURSOR = "cursor"        # 游标分页


class PaginationDirection(Enum):
    """分页方向枚举"""
    FORWARD = "forward"   # 向前翻页
    BACKWARD = "backward" # 向后翻页
    BOTH = "both"        # 双向翻页


class IPaginator(ABC):
    """分页器接口 - 定义分页处理的标准接口"""

    @abstractmethod
    async def initialize(self, root_selector: str, config: Dict[str, Any]) -> bool:
        """
        初始化分页器
        
        Args:
            root_selector: 分页容器选择器
            config: 分页配置
            
        Returns:
            bool: 初始化是否成功
        """
        pass

    @abstractmethod
    async def detect_pagination_type(self) -> PaginationType:
        """
        检测分页类型
        
        Returns:
            PaginationType: 检测到的分页类型
        """
        pass

    @abstractmethod
    async def get_current_page(self) -> int:
        """
        获取当前页码
        
        Returns:
            int: 当前页码，如果无法确定返回-1
        """
        pass

    @abstractmethod
    async def get_total_pages(self) -> Optional[int]:
        """
        获取总页数
        
        Returns:
            Optional[int]: 总页数，如果无法确定返回None
        """
        pass

    @abstractmethod
    async def has_next_page(self) -> bool:
        """
        检查是否有下一页
        
        Returns:
            bool: 是否有下一页
        """
        pass

    @abstractmethod
    async def has_previous_page(self) -> bool:
        """
        检查是否有上一页
        
        Returns:
            bool: 是否有上一页
        """
        pass

    @abstractmethod
    async def go_to_next_page(self, wait_for_load: bool = True) -> bool:
        """
        跳转到下一页
        
        Args:
            wait_for_load: 是否等待页面加载完成
            
        Returns:
            bool: 跳转是否成功
        """
        pass

    @abstractmethod
    async def go_to_previous_page(self, wait_for_load: bool = True) -> bool:
        """
        跳转到上一页
        
        Args:
            wait_for_load: 是否等待页面加载完成
            
        Returns:
            bool: 跳转是否成功
        """
        pass

    @abstractmethod
    async def go_to_page(self, page_number: int, wait_for_load: bool = True) -> bool:
        """
        跳转到指定页
        
        Args:
            page_number: 目标页码
            wait_for_load: 是否等待页面加载完成
            
        Returns:
            bool: 跳转是否成功
        """
        pass

    @abstractmethod
    async def iterate_pages(self, 
                          max_pages: Optional[int] = None,
                          direction: PaginationDirection = PaginationDirection.FORWARD) -> AsyncGenerator[int, None]:
        """
        迭代所有页面
        
        Args:
            max_pages: 最大页数限制
            direction: 分页方向
            
        Yields:
            int: 当前页码
        """
        pass


class IDataExtractor(ABC):
    """数据提取器接口 - 配合分页器使用的数据提取接口"""

    @abstractmethod
    async def extract_page_data(self, page_number: int) -> List[Dict[str, Any]]:
        """
        提取当前页数据
        
        Args:
            page_number: 页码
            
        Returns:
            List[Dict[str, Any]]: 页面数据列表
        """
        pass

    @abstractmethod
    async def extract_item_data(self, item_selector: str, item_index: int) -> Dict[str, Any]:
        """
        提取单个项目数据
        
        Args:
            item_selector: 项目选择器
            item_index: 项目索引
            
        Returns:
            Dict[str, Any]: 项目数据
        """
        pass

    @abstractmethod
    async def validate_data_completeness(self, data: List[Dict[str, Any]]) -> bool:
        """
        验证数据完整性
        
        Args:
            data: 要验证的数据
            
        Returns:
            bool: 数据是否完整
        """
        pass


class IPaginationStrategy(ABC):
    """分页策略接口 - 定义不同分页策略的实现"""

    @abstractmethod
    async def execute_pagination(self, 
                               paginator: IPaginator,
                               data_extractor: IDataExtractor,
                               config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        执行分页策略
        
        Args:
            paginator: 分页器实例
            data_extractor: 数据提取器实例
            config: 配置参数
            
        Returns:
            List[Dict[str, Any]]: 所有页面的数据
        """
        pass

    @abstractmethod
    async def handle_pagination_error(self, error: Exception, context: Dict[str, Any]) -> bool:
        """
        处理分页错误
        
        Args:
            error: 发生的错误
            context: 错误上下文
            
        Returns:
            bool: 是否应该继续分页
        """
        pass


class IScrollPaginator(IPaginator):
    """滚动分页器接口 - 专门处理滚动分页的接口"""

    @abstractmethod
    async def scroll_to_bottom(self, smooth: bool = True) -> bool:
        """
        滚动到页面底部
        
        Args:
            smooth: 是否平滑滚动
            
        Returns:
            bool: 滚动是否成功
        """
        pass

    @abstractmethod
    async def scroll_by_pixels(self, pixels: int, direction: str = "down") -> bool:
        """
        按像素滚动
        
        Args:
            pixels: 滚动像素数
            direction: 滚动方向 ("up", "down", "left", "right")
            
        Returns:
            bool: 滚动是否成功
        """
        pass

    @abstractmethod
    async def wait_for_new_content(self, timeout: int = 10000) -> bool:
        """
        等待新内容加载
        
        Args:
            timeout: 超时时间(毫秒)
            
        Returns:
            bool: 是否有新内容加载
        """
        pass

    @abstractmethod
    async def detect_scroll_end(self) -> bool:
        """
        检测是否滚动到底部
        
        Returns:
            bool: 是否已滚动到底部
        """
        pass


class ILoadMorePaginator(IPaginator):
    """加载更多分页器接口 - 专门处理"加载更多"按钮的接口"""

    @abstractmethod
    async def find_load_more_button(self) -> Optional['PageElement']:
        """
        查找"加载更多"按钮
        
        Returns:
            Optional[PageElement]: 找到的按钮元素，未找到返回None
        """
        pass

    @abstractmethod
    async def click_load_more(self, wait_for_content: bool = True) -> bool:
        """
        点击"加载更多"按钮
        
        Args:
            wait_for_content: 是否等待内容加载
            
        Returns:
            bool: 点击是否成功
        """
        pass

    @abstractmethod
    async def is_load_more_available(self) -> bool:
        """
        检查"加载更多"按钮是否可用
        
        Returns:
            bool: 按钮是否可用
        """
        pass