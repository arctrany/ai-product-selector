"""
Profit calculation models

This module contains data models for profit calculation functionality.
These models are shared across different calculation engines.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional


@dataclass
class ProfitCalculatorInput:
    """利润计算器输入参数数据模型"""
    # 价格信息
    black_price: float  # 黑标价格（人民币）
    green_price: float  # 绿标价格（人民币）
    list_price: float  # 定价（人民币）
    purchase_price: float  # 采购价（人民币）
    commission_rate: float  # 佣金率（如12表示12%）

    # 商品物理属性
    weight: float  # 重量（克）
    length: float  # 长度（厘米）
    width: float  # 宽度（厘米）
    height: float  # 高度（厘米）
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def validate(self) -> None:
        """Validate input parameters"""
        if self.black_price <= 0:
            raise ValueError("黑标价格必须为正数")
        if self.green_price <= 0:
            raise ValueError("绿标价格必须为正数")
        if self.list_price <= 0:
            raise ValueError("定价必须为正数")
        if self.purchase_price <= 0:
            raise ValueError("采购价必须为正数")
        if not (0 <= self.commission_rate <= 100):
            raise ValueError("佣金率必须在0-100之间")
        if self.weight <= 0:
            raise ValueError("重量必须为正数")
        if self.length <= 0 or self.width <= 0 or self.height <= 0:
            raise ValueError("尺寸必须为正数")


@dataclass
class ProfitCalculatorResult:
    """利润计算器结果数据模型"""
    profit_amount: float  # 利润金额（人民币）
    profit_rate: float  # 利润率（百分比）
    is_loss: bool  # 是否亏损
    input_summary: Dict[str, Any]  # 输入参数摘要
    calculation_time: float  # 计算耗时（秒）
    log_info: Dict[str, Any]  # 日志信息
    
    # Additional fields for engine information
    engine_used: Optional[str] = None  # Which engine was used
    shipping_cost: Optional[float] = None  # Calculated shipping cost
    commission_amount: Optional[float] = None  # Calculated commission
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def format_summary(self) -> str:
        """Format result summary"""
        status = "亏损" if self.is_loss else "盈利"
        return (f"{status}: 利润金额 ¥{self.profit_amount:.2f}, "
                f"利润率 {self.profit_rate:.2f}%, 耗时 {self.calculation_time:.3f}s")