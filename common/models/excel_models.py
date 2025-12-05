"""
Excel处理相关数据模型

定义与Excel文件处理、数据导入导出相关的数据结构
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

from .enums import GoodStoreFlag, StoreStatus
from .business_models import StoreInfo, ProductInfo


@dataclass
class ExcelStoreData:
    """Excel中的店铺数据"""
    row_index: int  # Excel中的行号
    store_id: str
    is_good_store: GoodStoreFlag
    status: StoreStatus
    
    def to_store_info(self) -> StoreInfo:
        """转换为StoreInfo对象"""
        return StoreInfo(
            store_id=self.store_id,
            is_good_store=self.is_good_store,
            status=self.status
        )


@dataclass
class ExcelProductData:
    """商品Excel数据模型"""
    store_id: str  # 店铺ID
    product_id: str  # 商品ID
    product_name: Optional[str] = None  # 商品名称
    image_url: Optional[str] = None  # 商品图片URL
    green_price: Optional[float] = None  # 绿标价格（卢布）
    black_price: Optional[float] = None  # 黑标价格（卢布）
    commission_rate: Optional[float] = None  # 佣金率
    weight: Optional[float] = None  # 重量（克）
    length: Optional[float] = None  # 长度（厘米）
    width: Optional[float] = None  # 宽度（厘米）
    height: Optional[float] = None  # 高度（厘米）
    source_price: Optional[float] = None  # 货源价格（人民币）
    profit_rate: Optional[float] = None  # 利润率
    profit_amount: Optional[float] = None  # 预计利润（人民币）
    
    @classmethod
    def from_product_info(cls, product_info: ProductInfo, profit_data: Optional[Dict[str, Any]] = None) -> 'ExcelProductData':
        """从ProductInfo和利润计算结果创建Excel数据
        
        Args:
            product_info: 商品信息
            profit_data: 利润计算结果，包含 profit_rate 和 profit_amount
        """
        return cls(
            store_id=product_info.store_id or "",
            product_id=product_info.product_id or "",
            product_name=None,  # 暂时没有商品名称字段
            image_url=product_info.image_url,
            green_price=product_info.green_price,
            black_price=product_info.black_price,
            commission_rate=product_info.commission_rate,
            weight=product_info.weight,
            length=product_info.length,
            width=product_info.width,
            height=product_info.height,
            source_price=product_info.source_price,
            profit_rate=profit_data.get('profit_rate') if profit_data else None,
            profit_amount=profit_data.get('profit_amount') if profit_data else None
        )
