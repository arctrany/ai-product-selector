"""
Excel处理相关数据模型

定义与Excel文件处理、数据导入导出相关的数据结构
"""

from dataclasses import dataclass

from .enums import GoodStoreFlag, StoreStatus
from .business_models import StoreInfo


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
