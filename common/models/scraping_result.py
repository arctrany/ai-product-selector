"""
标准抓取结果数据模型

提供统一的数据传输对象，适用于所有Scraper。
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ScrapingStatus(str, Enum):
    """抓取状态枚举"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class ScrapingResult:
    """
    统一抓取结果数据类
    
    适用于所有Scraper的标准返回格式
    """
    success: bool
    data: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    status: ScrapingStatus = ScrapingStatus.SUCCESS
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """自动设置状态"""
        if self.success:
            self.status = ScrapingStatus.SUCCESS
        elif self.error_message:
            if "timeout" in self.error_message.lower():
                self.status = ScrapingStatus.TIMEOUT
            else:
                self.status = ScrapingStatus.ERROR
        else:
            self.status = ScrapingStatus.FAILED
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'success': self.success,
            'data': self.data,
            'error_message': self.error_message,
            'execution_time': self.execution_time,
            'status': self.status.value,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def create_success(cls, data: Dict[str, Any], execution_time: Optional[float] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> 'ScrapingResult':
        """创建成功结果"""
        return cls(
            success=True,
            data=data,
            execution_time=execution_time,
            metadata=metadata or {},
            status=ScrapingStatus.SUCCESS
        )
    
    @classmethod
    def create_failure(cls, error_message: str, execution_time: Optional[float] = None,
                      data: Optional[Dict[str, Any]] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> 'ScrapingResult':
        """创建失败结果"""
        return cls(
            success=False,
            data=data or {},
            error_message=error_message,
            execution_time=execution_time,
            metadata=metadata or {},
            status=ScrapingStatus.FAILED
        )


@dataclass
class CompetitorInfo:
    """跟卖店铺信息"""
    store_name: str
    store_url: Optional[str] = None
    price: Optional[float] = None
    rating: Optional[float] = None
    sales_count: Optional[int] = None
    delivery_info: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'store_name': self.store_name,
            'store_url': self.store_url,
            'price': self.price,
            'rating': self.rating,
            'sales_count': self.sales_count,
            'delivery_info': self.delivery_info,
            'metadata': self.metadata
        }


@dataclass
class CompetitorDetectionResult:
    """跟卖检测结果"""
    has_competitors: bool
    competitor_count: int
    competitors: List[CompetitorInfo] = field(default_factory=list)
    detection_method: Optional[str] = None
    confidence: float = 1.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'has_competitors': self.has_competitors,
            'competitor_count': self.competitor_count,
            'competitors': [c.to_dict() for c in self.competitors],
            'detection_method': self.detection_method,
            'confidence': self.confidence,
            'error_message': self.error_message,
            'metadata': self.metadata
        }
    
    @classmethod
    def create_no_competitors(cls, detection_method: Optional[str] = None) -> 'CompetitorDetectionResult':
        """创建无跟卖结果"""
        return cls(
            has_competitors=False,
            competitor_count=0,
            competitors=[],
            detection_method=detection_method,
            confidence=1.0
        )
    
    @classmethod
    def create_with_competitors(cls, competitors: List[CompetitorInfo],
                               detection_method: Optional[str] = None) -> 'CompetitorDetectionResult':
        """创建有跟卖结果"""
        return cls(
            has_competitors=True,
            competitor_count=len(competitors),
            competitors=competitors,
            detection_method=detection_method,
            confidence=1.0
        )


@dataclass
class ProductScrapingResult(ScrapingResult):
    """
    商品抓取结果（扩展ScrapingResult）
    
    专门用于商品信息抓取
    """
    product_url: Optional[str] = None
    product_id: Optional[str] = None
    
    def __post_init__(self):
        """扩展初始化"""
        super().__post_init__()
        if self.product_url and not self.product_id:
            self.product_id = self._extract_id_from_url(self.product_url)
    
    @staticmethod
    def _extract_id_from_url(url: str) -> Optional[str]:
        """从URL提取商品ID"""
        try:
            parts = url.rstrip('/').split('/')
            return parts[-1] if parts else None
        except Exception:
            return None
