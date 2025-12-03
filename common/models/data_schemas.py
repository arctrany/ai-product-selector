"""
标准化数据模式定义

定义所有 Scraper 的标准输出格式，确保数据一致性
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class DataSchemaVersion(str, Enum):
    """数据模式版本"""
    V1_0 = "1.0"
    V2_0 = "2.0"  # 当前版本


@dataclass
class StandardProductData:
    """标准化商品数据格式"""
    # 基础信息
    product_id: Optional[str] = None
    product_url: Optional[str] = None
    title: Optional[str] = None
    brand_name: Optional[str] = None
    category: Optional[str] = None
    sku: Optional[str] = None
    
    # 价格信息
    green_price: Optional[float] = None  # 绿标价格（促销价）
    black_price: Optional[float] = None  # 黑标价格（原价）
    list_price: Optional[float] = None   # 定价（计算得出）
    
    # 媒体信息
    product_image: Optional[str] = None
    images: List[str] = field(default_factory=list)
    
    # ERP 数据
    source_price: Optional[float] = None      # 采购价格
    commission_rate: Optional[float] = None   # 佣金率
    weight: Optional[float] = None            # 重量(克)
    length: Optional[float] = None            # 长度
    width: Optional[float] = None             # 宽度
    height: Optional[float] = None            # 高度
    shelf_days: Optional[int] = None          # 已上架天数
    
    # 状态标识
    source_matched: bool = False              # 是否匹配到货源
    is_competitor_selected: bool = False      # 是否选择了跟卖商品
    
    # 元数据
    scraping_timestamp: Optional[str] = None
    data_completeness: Optional[float] = None  # 数据完整度 0.0-1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'product_id': self.product_id,
            'product_url': self.product_url,
            'title': self.title,
            'brand_name': self.brand_name,
            'category': self.category,
            'sku': self.sku,
            'green_price': self.green_price,
            'black_price': self.black_price,
            'list_price': self.list_price,
            'product_image': self.product_image,
            'images': self.images,
            'source_price': self.source_price,
            'commission_rate': self.commission_rate,
            'weight': self.weight,
            'length': self.length,
            'width': self.width,
            'height': self.height,
            'shelf_days': self.shelf_days,
            'source_matched': self.source_matched,
            'is_competitor_selected': self.is_competitor_selected,
            'scraping_timestamp': self.scraping_timestamp,
            'data_completeness': self.data_completeness
        }


@dataclass
class StandardStoreData:
    """标准化店铺数据格式"""
    store_id: str
    store_name: Optional[str] = None
    store_url: Optional[str] = None
    
    # 销售数据
    sold_30days: Optional[float] = None       # 30天销售额
    sold_count_30days: Optional[int] = None   # 30天销量
    daily_avg_sold: Optional[float] = None    # 日均销量
    
    # 评价信息
    rating: Optional[float] = None
    review_count: Optional[int] = None
    
    # 商品列表
    products: List[Dict[str, Any]] = field(default_factory=list)
    
    # 元数据
    scraping_timestamp: Optional[str] = None
    data_source: Optional[str] = None  # 数据来源（seerfar, ozon等）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'store_id': self.store_id,
            'store_name': self.store_name,
            'store_url': self.store_url,
            'sold_30days': self.sold_30days,
            'sold_count_30days': self.sold_count_30days,
            'daily_avg_sold': self.daily_avg_sold,
            'rating': self.rating,
            'review_count': self.review_count,
            'products': self.products,
            'scraping_timestamp': self.scraping_timestamp,
            'data_source': self.data_source
        }


@dataclass
class StandardCompetitorData:
    """标准化跟卖数据格式"""
    store_id: str
    store_name: Optional[str] = None
    price: Optional[float] = None
    ranking: Optional[int] = None  # 在跟卖列表中的排名
    
    # 店铺信息
    rating: Optional[float] = None
    sales_count: Optional[int] = None
    delivery_info: Optional[str] = None
    
    # 元数据
    detection_method: Optional[str] = None
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'store_id': self.store_id,
            'store_name': self.store_name,
            'price': self.price,
            'ranking': self.ranking,
            'rating': self.rating,
            'sales_count': self.sales_count,
            'delivery_info': self.delivery_info,
            'detection_method': self.detection_method,
            'confidence': self.confidence
        }


@dataclass
class StandardScrapingResultData:
    """标准化抓取结果数据格式"""
    schema_version: DataSchemaVersion = DataSchemaVersion.V2_0
    
    # 核心数据（根据抓取类型选择性填充）
    product_data: Optional[StandardProductData] = None
    store_data: Optional[StandardStoreData] = None
    competitors_data: List[StandardCompetitorData] = field(default_factory=list)
    
    # 分析结果
    analysis_type: Optional[str] = None  # 'product_only', 'store_only', 'full_analysis'
    selection_decision: Optional[str] = None  # 'primary', 'competitor', 'none'
    selection_reason: Optional[str] = None
    
    # 性能指标
    data_quality_score: Optional[float] = None  # 0.0-1.0
    processing_steps: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'schema_version': self.schema_version.value,
            'product_data': self.product_data.to_dict() if self.product_data else None,
            'store_data': self.store_data.to_dict() if self.store_data else None,
            'competitors_data': [c.to_dict() for c in self.competitors_data],
            'analysis_type': self.analysis_type,
            'selection_decision': self.selection_decision,
            'selection_reason': self.selection_reason,
            'data_quality_score': self.data_quality_score,
            'processing_steps': self.processing_steps
        }
    
    @classmethod
    def create_product_result(cls, product_data: StandardProductData,
                            analysis_type: str = 'product_only') -> 'StandardScrapingResultData':
        """创建商品抓取结果"""
        return cls(
            product_data=product_data,
            analysis_type=analysis_type,
            processing_steps=['product_extraction']
        )
    
    @classmethod
    def create_store_result(cls, store_data: StandardStoreData,
                          analysis_type: str = 'store_only') -> 'StandardScrapingResultData':
        """创建店铺抓取结果"""
        return cls(
            store_data=store_data,
            analysis_type=analysis_type,
            processing_steps=['store_extraction']
        )
    
    @classmethod
    def create_full_analysis_result(cls, product_data: StandardProductData,
                                  competitors_data: List[StandardCompetitorData],
                                  selection_decision: str,
                                  selection_reason: str) -> 'StandardScrapingResultData':
        """创建完整分析结果"""
        return cls(
            product_data=product_data,
            competitors_data=competitors_data,
            analysis_type='full_analysis',
            selection_decision=selection_decision,
            selection_reason=selection_reason,
            processing_steps=['product_extraction', 'competitor_detection', 'selection_analysis']
        )


def migrate_legacy_data(legacy_data: Dict[str, Any]) -> StandardScrapingResultData:
    """
    将旧格式数据迁移到新的标准格式
    
    Args:
        legacy_data: 旧格式的数据字典
        
    Returns:
        StandardScrapingResultData: 标准格式的数据
    """
    # 提取商品数据
    product_data = None
    if any(key in legacy_data for key in ['product_id', 'green_price', 'black_price']):
        product_data = StandardProductData(
            product_id=legacy_data.get('product_id'),
            product_url=legacy_data.get('product_url'),
            title=legacy_data.get('title'),
            brand_name=legacy_data.get('brand_name'),
            green_price=legacy_data.get('green_price'),
            black_price=legacy_data.get('black_price'),
            product_image=legacy_data.get('product_image'),
            source_price=legacy_data.get('source_price'),
            commission_rate=legacy_data.get('commission_rate'),
            weight=legacy_data.get('weight'),
            length=legacy_data.get('length'),
            width=legacy_data.get('width'),
            height=legacy_data.get('height'),
            source_matched=legacy_data.get('source_matched', False)
        )
    
    # 提取店铺数据
    store_data = None
    if any(key in legacy_data for key in ['store_id', 'sold_30days']):
        store_data = StandardStoreData(
            store_id=legacy_data.get('store_id', ''),
            store_name=legacy_data.get('store_name'),
            sold_30days=legacy_data.get('sold_30days'),
            sold_count_30days=legacy_data.get('sold_count_30days'),
            daily_avg_sold=legacy_data.get('daily_avg_sold'),
            products=legacy_data.get('products', [])
        )
    
    # 提取跟卖数据
    competitors_data = []
    if 'competitors' in legacy_data:
        for comp in legacy_data['competitors']:
            competitors_data.append(StandardCompetitorData(
                store_id=comp.get('store_id', ''),
                store_name=comp.get('store_name'),
                price=comp.get('price'),
                ranking=comp.get('ranking')
            ))
    
    return StandardScrapingResultData(
        product_data=product_data,
        store_data=store_data,
        competitors_data=competitors_data,
        analysis_type=legacy_data.get('analysis_type', 'unknown'),
        selection_decision=legacy_data.get('selection_decision'),
        selection_reason=legacy_data.get('selection_reason')
    )