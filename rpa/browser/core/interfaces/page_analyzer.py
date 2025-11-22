"""
页面分析器接口定义

定义页面分析和元素提取的标准接口
支持DOM分析、元素识别、内容提取等功能
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models.page_element import PageElement, ElementCollection
    from ..exceptions.browser_exceptions import BrowserError
else:
    PageElement = 'PageElement'
    ElementCollection = 'ElementCollection'
    BrowserError = Exception


class IPageAnalyzer(ABC):
    """页面分析器接口 - 定义页面分析的标准接口"""

    @abstractmethod
    async def analyze_page(self, url: Optional[str] = None) -> Dict[str, Any]:
        """
        分析整个页面结构
        
        Args:
            url: 页面URL，如果为None则分析当前页面
            
        Returns:
            Dict[str, Any]: 页面分析结果
        """
        pass

    @abstractmethod
    async def extract_elements(self, selector: str, element_type: Optional[str] = None) -> 'ElementCollection':
        """
        提取页面元素
        
        Args:
            selector: 元素选择器
            element_type: 元素类型过滤
            
        Returns:
            ElementCollection: 元素集合
        """
        pass

    @abstractmethod
    async def extract_links(self, filter_pattern: Optional[str] = None) -> List['PageElement']:
        """
        提取页面链接
        
        Args:
            filter_pattern: 链接过滤模式
            
        Returns:
            List[PageElement]: 链接元素列表
        """
        pass

    @abstractmethod
    async def extract_text_content(self, selector: Optional[str] = None) -> List[str]:
        """
        提取文本内容
        
        Args:
            selector: 选择器，如果为None则提取所有文本
            
        Returns:
            List[str]: 文本内容列表
        """
        pass

    @abstractmethod
    async def extract_images(self, include_data_urls: bool = False) -> List['PageElement']:
        """
        提取页面图片
        
        Args:
            include_data_urls: 是否包含data URL图片
            
        Returns:
            List[PageElement]: 图片元素列表
        """
        pass

    @abstractmethod
    async def extract_forms(self) -> List['PageElement']:
        """
        提取页面表单
        
        Returns:
            List[PageElement]: 表单元素列表
        """
        pass

    @abstractmethod
    async def analyze_element_hierarchy(self, root_selector: str) -> Dict[str, Any]:
        """
        分析元素层级结构
        
        Args:
            root_selector: 根元素选择器
            
        Returns:
            Dict[str, Any]: 层级结构信息
        """
        pass


class IContentExtractor(ABC):
    """内容提取器接口 - 定义内容提取的标准接口"""

    @abstractmethod
    async def extract_structured_data(self, schema_type: str) -> Dict[str, Any]:
        """
        提取结构化数据
        
        Args:
            schema_type: 数据模式类型 (json-ld, microdata, rdfa等)
            
        Returns:
            Dict[str, Any]: 结构化数据
        """
        pass

    @abstractmethod
    async def extract_table_data(self, table_selector: str) -> List[Dict[str, str]]:
        """
        提取表格数据
        
        Args:
            table_selector: 表格选择器
            
        Returns:
            List[Dict[str, str]]: 表格数据，每行为一个字典
        """
        pass

    @abstractmethod
    async def extract_list_data(self, list_selector: str, item_selector: str) -> List[Dict[str, Any]]:
        """
        提取列表数据
        
        Args:
            list_selector: 列表容器选择器
            item_selector: 列表项选择器
            
        Returns:
            List[Dict[str, Any]]: 列表数据
        """
        pass

    @abstractmethod
    async def extract_metadata(self) -> Dict[str, str]:
        """
        提取页面元数据
        
        Returns:
            Dict[str, str]: 元数据字典
        """
        pass

    @abstractmethod
    async def extract_dynamic_content(self, wait_selector: Optional[str] = None, timeout: int = 10000) -> Dict[str, Any]:
        """
        提取动态加载的内容
        
        Args:
            wait_selector: 等待出现的选择器
            timeout: 超时时间(毫秒)
            
        Returns:
            Dict[str, Any]: 动态内容
        """
        pass


class IElementMatcher(ABC):
    """元素匹配器接口 - 定义元素匹配和识别的标准接口"""

    @abstractmethod
    async def find_similar_elements(self, reference_element: 'PageElement', similarity_threshold: float = 0.8) -> List['PageElement']:
        """
        查找相似元素
        
        Args:
            reference_element: 参考元素
            similarity_threshold: 相似度阈值
            
        Returns:
            List[PageElement]: 相似元素列表
        """
        pass

    @abstractmethod
    async def match_by_pattern(self, pattern: Dict[str, Any]) -> List['PageElement']:
        """
        根据模式匹配元素
        
        Args:
            pattern: 匹配模式
            
        Returns:
            List[PageElement]: 匹配的元素列表
        """
        pass

    @abstractmethod
    async def classify_elements(self, elements: List['PageElement']) -> Dict[str, List['PageElement']]:
        """
        对元素进行分类
        
        Args:
            elements: 要分类的元素列表
            
        Returns:
            Dict[str, List[PageElement]]: 分类结果
        """
        pass

    @abstractmethod
    async def detect_interactive_elements(self) -> List['PageElement']:
        """
        检测可交互元素
        
        Returns:
            List[PageElement]: 可交互元素列表
        """
        pass


class IPageValidator(ABC):
    """页面验证器接口 - 定义页面验证的标准接口"""

    @abstractmethod
    async def validate_page_load(self, expected_elements: List[str]) -> bool:
        """
        验证页面是否完全加载
        
        Args:
            expected_elements: 期望存在的元素选择器列表
            
        Returns:
            bool: 页面是否完全加载
        """
        pass

    @abstractmethod
    async def validate_element_state(self, element: 'PageElement', expected_states: List[str]) -> bool:
        """
        验证元素状态
        
        Args:
            element: 要验证的元素
            expected_states: 期望的状态列表
            
        Returns:
            bool: 元素状态是否符合期望
        """
        pass

    @abstractmethod
    async def validate_content(self, validation_rules: Dict[str, Any]) -> Dict[str, bool]:
        """
        验证页面内容
        
        Args:
            validation_rules: 验证规则
            
        Returns:
            Dict[str, bool]: 验证结果
        """
        pass

    @abstractmethod
    async def check_accessibility(self) -> Dict[str, Any]:
        """
        检查页面可访问性
        
        Returns:
            Dict[str, Any]: 可访问性检查结果
        """
        pass