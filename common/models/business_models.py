"""
业务领域数据模型

定义与业务逻辑相关的核心数据结构，包括店铺、商品、价格计算等
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

from .enums import StoreStatus, GoodStoreFlag


@dataclass
class StoreInfo:
    """店铺基础信息"""
    store_id: str
    is_good_store: GoodStoreFlag = GoodStoreFlag.EMPTY
    status: StoreStatus = StoreStatus.EMPTY
    
    # Seerfar抓取的销售数据
    sold_30days: Optional[float] = None  # 30天销售额
    sold_count_30days: Optional[int] = None  # 30天销量
    daily_avg_sold: Optional[float] = None  # 日均销量
    
    # 处理结果
    profitable_products_count: int = 0  # 有利润商品数量
    total_products_checked: int = 0  # 检查的商品总数
    needs_split: bool = False  # 是否需要裂变
    
    def __post_init__(self):
        """数据验证"""
        if not self.store_id or not self.store_id.strip():
            raise ValueError("店铺ID不能为空")


@dataclass
class ProductInfo:
    """商品基础信息"""
    product_id: Optional[str] = None  # 商品ID（从URL提取）
    product_url: Optional[str] = None  # 商品页面URL（直接存储，无需转换）
    image_url: Optional[str] = None
    brand_name: Optional[str] = None
    sku: Optional[str] = None

    # OZON价格信息
    green_price: Optional[float] = None  # 绿标价格（促销价）
    black_price: Optional[float] = None  # 黑标价格（原价）
    list_price: Optional[float] = None  # 定价（绿标价格*0.95）
    competitor_price: Optional[float] = None  # 跟卖价格

    # ERP插件数据
    commission_rate: Optional[float] = None  # 佣金率
    weight: Optional[float] = None  # 重量(克)
    length: Optional[float] = None  # 长度
    width: Optional[float] = None  # 宽度
    height: Optional[float] = None  # 高度

    # 货源匹配
    source_price: Optional[float] = None  # 采购价格
    source_matched: bool = False  # 是否匹配到货源

    # 上架时间信息
    shelf_days: Optional[int] = None  # 已上架时间（天）
    
    # 合并决策标识
    is_competitor_selected: bool = False  # 是否选择了跟卖商品

    def __post_init__(self):
        """数据验证"""
        # product_id 现在是可选的，允许为 None
        pass


@dataclass
class PriceCalculationResult:
    """价格计算结果"""
    real_selling_price: float  # 真实售价
    product_pricing: float  # 商品定价（95折）
    profit_amount: float  # 利润金额
    profit_rate: float  # 利润率（百分比）
    is_profitable: bool  # 是否有利润
    
    # 计算过程记录
    calculation_details: Dict[str, Any]
    
    def __post_init__(self):
        """数据验证"""
        if self.profit_rate < 0:
            self.is_profitable = False
        else:
            self.is_profitable = self.profit_rate >= 20.0  # 默认20%阈值


@dataclass
class CompetitorStore:
    """跟卖店铺信息"""
    store_id: str
    store_name: Optional[str] = None
    price: Optional[float] = None
    ranking: Optional[int] = None  # 在跟卖列表中的排名


@dataclass
class ProductAnalysisResult:
    """商品分析结果"""
    product_info: ProductInfo
    price_calculation: Optional[PriceCalculationResult] = None
    competitor_stores: List[CompetitorStore] = None
    
    def __post_init__(self):
        if self.competitor_stores is None:
            self.competitor_stores = []


@dataclass
class StoreAnalysisResult:
    """店铺分析结果"""
    store_info: StoreInfo
    products: List[ProductAnalysisResult]
    
    # 汇总统计
    total_products: int = 0
    profitable_products: int = 0
    profit_rate_threshold: float = 20.0  # 利润率阈值
    good_store_threshold: float = 20.0  # 好店判定阈值（有利润商品比例）
    
    def __post_init__(self):
        """计算汇总统计"""
        self.total_products = len(self.products)
        self.profitable_products = sum(
            1 for p in self.products 
            if p.price_calculation and p.price_calculation.is_profitable
        )
        
        # 更新店铺信息
        self.store_info.total_products_checked = self.total_products
        self.store_info.profitable_products_count = self.profitable_products
        
        # 判断是否为好店
        if self.total_products > 0:
            profit_ratio = (self.profitable_products / self.total_products) * 100
            self.store_info.needs_split = profit_ratio >= self.good_store_threshold
            self.store_info.is_good_store = (
                GoodStoreFlag.YES if self.store_info.needs_split else GoodStoreFlag.NO
            )
            self.store_info.status = StoreStatus.PROCESSED
        else:
            # 🔧 关键修复：没有商品时明确标记为非好店，且状态为失败
            self.store_info.is_good_store = GoodStoreFlag.NO
            self.store_info.needs_split = False
            # 如果状态还是EMPTY或PENDING，设置为失败；如果已经是PROCESSED，保持不变
            if self.store_info.status in [StoreStatus.EMPTY, StoreStatus.PENDING]:
                self.store_info.status = StoreStatus.PROCESSED  # 改为PROCESSED，但明确标记为NO


@dataclass
class BatchProcessingResult:
    """批量处理结果"""
    total_stores: int
    processed_stores: int
    good_stores: int
    failed_stores: int
    
    processing_time: float  # 处理耗时（秒）
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # 详细结果
    store_results: List[StoreAnalysisResult] = None
    error_logs: List[str] = None
    
    def __post_init__(self):
        if self.store_results is None:
            self.store_results = []
        if self.error_logs is None:
            self.error_logs = []
