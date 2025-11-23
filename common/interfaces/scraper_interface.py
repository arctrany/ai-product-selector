"""
标准Scraper接口规范

定义统一的Scraper接口标准，确保所有Scraper实现的一致性。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Callable
from enum import Enum

from ..models.scraping_result import ScrapingResult


class ScrapingMode(Enum):
    """抓取模式枚举"""
    PRODUCT_DATA = "product_data"  # 商品数据抓取
    STORE_DATA = "store_data"  # 店铺数据抓取
    COMPETITOR_DATA = "competitor_data"  # 跟卖数据抓取
    ERP_DATA = "erp_data"  # ERP数据抓取


class ScrapingErrorCode(Enum):
    """标准错误码枚举"""
    SUCCESS = "SUCCESS"
    NAVIGATION_FAILED = "NAVIGATION_FAILED"
    ELEMENT_NOT_FOUND = "ELEMENT_NOT_FOUND"
    DATA_EXTRACTION_FAILED = "DATA_EXTRACTION_FAILED"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    BROWSER_ERROR = "BROWSER_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RATE_LIMITED = "RATE_LIMITED"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


class IScraperInterface(ABC):
    """
    Scraper标准接口
    
    定义所有Scraper必须实现的统一接口规范
    """
    
    @abstractmethod
    def scrape(self, 
               target: str,
               mode: Optional[ScrapingMode] = None,
               options: Optional[Dict[str, Any]] = None,
               **kwargs) -> ScrapingResult:
        """
        统一的抓取接口
        
        Args:
            target: 抓取目标（URL、店铺ID等）
            mode: 抓取模式
            options: 抓取选项配置
            **kwargs: 额外参数
            
        Returns:
            ScrapingResult: 标准化抓取结果
            
        Raises:
            ScrapingException: 抓取异常
        """
        pass
    
    @abstractmethod
    def navigate_to(self, target: str, timeout: Optional[int] = None) -> bool:
        """
        导航到目标页面
        
        Args:
            target: 目标URL或标识符
            timeout: 超时时间（秒）
            
        Returns:
            bool: 导航是否成功
            
        Raises:
            NavigationException: 导航异常
        """
        pass
    
    @abstractmethod
    def extract_data(self, 
                    selectors: Optional[Dict[str, str]] = None,
                    options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        从当前页面提取数据
        
        Args:
            selectors: 选择器映射
            options: 提取选项
            
        Returns:
            Dict[str, Any]: 提取的数据
            
        Raises:
            DataExtractionException: 数据提取异常
        """
        pass
    
    @abstractmethod
    def validate_data(self, data: Dict[str, Any], 
                     filters: Optional[List[Callable]] = None) -> bool:
        """
        验证提取的数据
        
        Args:
            data: 待验证的数据
            filters: 验证过滤器列表
            
        Returns:
            bool: 数据是否有效
            
        Raises:
            ValidationException: 验证异常
        """
        pass
    
    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """
        获取Scraper健康状态
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """
        关闭Scraper并清理资源
        
        Raises:
            CleanupException: 清理异常
        """
        pass


class IProductScraper(IScraperInterface):
    """商品数据抓取器接口"""
    
    @abstractmethod
    def scrape_product_info(self, 
                           product_url: str,
                           include_prices: bool = True,
                           include_reviews: bool = False,
                           options: Optional[Dict[str, Any]] = None) -> ScrapingResult:
        """
        抓取商品基本信息
        
        Args:
            product_url: 商品URL
            include_prices: 是否包含价格信息
            include_reviews: 是否包含评价信息
            options: 抓取选项
            
        Returns:
            ScrapingResult: 商品信息抓取结果
        """
        pass


class IStoreScraper(IScraperInterface):
    """店铺数据抓取器接口"""
    
    @abstractmethod
    def scrape_store_info(self,
                         store_id: str,
                         include_products: bool = False,
                         max_products: Optional[int] = None,
                         options: Optional[Dict[str, Any]] = None) -> ScrapingResult:
        """
        抓取店铺基本信息
        
        Args:
            store_id: 店铺ID
            include_products: 是否包含商品列表
            max_products: 最大商品数量
            options: 抓取选项
            
        Returns:
            ScrapingResult: 店铺信息抓取结果
        """
        pass
    
    @abstractmethod
    def scrape_store_sales_data(self,
                               store_id: str,
                               period_days: int = 30,
                               options: Optional[Dict[str, Any]] = None) -> ScrapingResult:
        """
        抓取店铺销售数据
        
        Args:
            store_id: 店铺ID
            period_days: 统计天数
            options: 抓取选项
            
        Returns:
            ScrapingResult: 销售数据抓取结果
        """
        pass


class ICompetitorScraper(IScraperInterface):
    """跟卖数据抓取器接口"""
    
    @abstractmethod
    def detect_competitors(self,
                          product_url: str,
                          options: Optional[Dict[str, Any]] = None) -> ScrapingResult:
        """
        检测商品跟卖情况
        
        Args:
            product_url: 商品URL
            options: 检测选项
            
        Returns:
            ScrapingResult: 跟卖检测结果
        """
        pass
    
    @abstractmethod
    def extract_competitor_info(self,
                               competitors: List[Dict[str, Any]],
                               options: Optional[Dict[str, Any]] = None) -> ScrapingResult:
        """
        提取跟卖商家详细信息
        
        Args:
            competitors: 跟卖商家列表
            options: 提取选项
            
        Returns:
            ScrapingResult: 跟卖信息抓取结果
        """
        pass


class IERPScraper(IScraperInterface):
    """ERP数据抓取器接口"""
    
    @abstractmethod
    def scrape_erp_data(self,
                       product_url: Optional[str] = None,
                       fields: Optional[List[str]] = None,
                       options: Optional[Dict[str, Any]] = None) -> ScrapingResult:
        """
        抓取ERP插件数据
        
        Args:
            product_url: 商品URL（可选，如为空则从当前页面抓取）
            fields: 需要抓取的字段列表
            options: 抓取选项
            
        Returns:
            ScrapingResult: ERP数据抓取结果
        """
        pass
    
    @abstractmethod
    def wait_for_erp_plugin(self, timeout: int = 30) -> bool:
        """
        等待ERP插件加载完成
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            bool: 插件是否加载成功
        """
        pass


class StandardScrapingOptions:
    """标准抓取选项"""
    
    def __init__(self,
                 timeout: int = 30,
                 retry_count: int = 3,
                 retry_delay: float = 2.0,
                 enable_screenshots: bool = False,
                 custom_headers: Optional[Dict[str, str]] = None,
                 proxy_config: Optional[Dict[str, Any]] = None):
        """
        初始化标准抓取选项
        
        Args:
            timeout: 超时时间（秒）
            retry_count: 重试次数
            retry_delay: 重试延迟（秒）
            enable_screenshots: 是否启用截图
            custom_headers: 自定义请求头
            proxy_config: 代理配置
        """
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.enable_screenshots = enable_screenshots
        self.custom_headers = custom_headers or {}
        self.proxy_config = proxy_config
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'timeout': self.timeout,
            'retry_count': self.retry_count,
            'retry_delay': self.retry_delay,
            'enable_screenshots': self.enable_screenshots,
            'custom_headers': self.custom_headers,
            'proxy_config': self.proxy_config
        }
