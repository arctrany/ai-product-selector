#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OZON利润计算器
基于Excel物流计算表，提供商品利润和利润率计算功能
"""

import pandas as pd
import openpyxl
from openpyxl.utils import get_column_letter
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductCategory(Enum):
    """商品分类枚举"""
    EXTRA_SMALL = "超级轻小件"  # ≤0.5KG, ≤1500卢布
    SMALL = "轻小件"          # ≤2KG, 1501-7000卢布
    BUDGET = "低客单标准件"    # ≤25KG, ≤1500卢布
    STANDARD = "标准件"       # 其他情况


@dataclass
class ProductInfo:
    """商品信息数据结构"""
    sku: str                    # 商品SKU
    weight_kg: float           # 重量(KG)
    dimensions_cm: str         # 尺寸(长x宽x高)
    ozon_price_rub: float     # OZON销售价格(卢布)
    purchase_price_cny: float  # 采购价格(人民币)
    exchange_rate: float = 13.5  # 汇率(卢布/人民币)
    
    @property
    def purchase_price_rub(self) -> float:
        """采购价格(卢布)"""
        return self.purchase_price_cny * self.exchange_rate
    
    @property
    def dimensions_list(self) -> List[float]:
        """解析尺寸为列表"""
        try:
            return [float(x.strip()) for x in self.dimensions_cm.replace('×', 'x').split('x')]
        except:
            return [0, 0, 0]
    
    @property
    def total_dimensions(self) -> float:
        """三边之和"""
        return sum(self.dimensions_list)
    
    @property
    def max_dimension(self) -> float:
        """最长边"""
        return max(self.dimensions_list) if self.dimensions_list else 0


@dataclass
class LogisticsChannel:
    """物流渠道信息"""
    name: str                  # 渠道名称
    service_level: str         # 服务等级
    base_fee: float           # 基础费用(元)
    weight_fee: float         # 重量费用(元/克 或 元/KG)
    weight_unit: str          # 重量单位(g/kg)
    max_weight_kg: float      # 最大重量限制
    max_value_rub: float      # 最大货值限制
    max_dimensions: float     # 最大尺寸限制
    max_single_side: float    # 最长边限制
    delivery_days: str        # 时效
    
    def calculate_shipping_cost(self, product: ProductInfo) -> Optional[float]:
        """计算物流费用"""
        # 检查重量限制
        if product.weight_kg > self.max_weight_kg:
            return None
            
        # 检查货值限制
        if self.max_value_rub > 0 and product.ozon_price_rub > self.max_value_rub:
            return None
            
        # 检查尺寸限制
        if self.max_dimensions > 0 and product.total_dimensions > self.max_dimensions:
            return None
            
        if self.max_single_side > 0 and product.max_dimension > self.max_single_side:
            return None
        
        # 计算费用
        if self.weight_unit == 'g':
            weight_cost = product.weight_kg * 1000 * self.weight_fee
        else:  # kg
            weight_cost = product.weight_kg * self.weight_fee
            
        total_cost = self.base_fee + weight_cost
        return total_cost


@dataclass
class ProfitCalculation:
    """利润计算结果"""
    product_sku: str
    category: ProductCategory
    available_channels: List[str]
    best_channel: str
    shipping_cost_cny: float
    total_cost_cny: float
    revenue_cny: float
    profit_cny: float
    profit_margin: float
    warnings: List[str]


class OzonCalculator:
    """OZON利润计算器"""
    
    def __init__(self, excel_path: str = "../../../docs/122义乌仓资费测算3.17.xlsx"):
        """
        初始化计算器
        
        Args:
            excel_path: Excel文件路径
        """
        self.excel_path = excel_path
        self.channels: Dict[str, List[LogisticsChannel]] = {}
        self.exchange_rate = 13.5  # 默认汇率
        self._load_excel_data()
    
    def _load_excel_data(self):
        """加载Excel数据，解析物流渠道信息"""
        try:
            logger.info(f"正在加载Excel文件: {self.excel_path}")
            
            # 读取所有工作表
            excel_data = pd.read_excel(self.excel_path, sheet_name=None, header=None)
            
            for sheet_name, df in excel_data.items():
                logger.info(f"解析工作表: {sheet_name}")
                channels = self._parse_sheet_channels(sheet_name, df)
                if channels:
                    self.channels[sheet_name] = channels
                    
            logger.info(f"成功加载 {len(self.channels)} 个物流服务商的数据")
            
        except Exception as e:
            logger.error(f"加载Excel文件失败: {e}")
            raise
    
    def _parse_sheet_channels(self, sheet_name: str, df: pd.DataFrame) -> List[LogisticsChannel]:
        """解析工作表中的物流渠道信息"""
        channels = []
        
        try:
            # 查找表头行
            header_row = None
            for i, row in df.iterrows():
                if any('渠道名称' in str(cell) for cell in row if pd.notna(cell)):
                    header_row = i
                    break
            
            if header_row is None:
                logger.warning(f"工作表 {sheet_name} 未找到表头")
                return channels
            
            # 解析数据行
            for i in range(header_row + 1, len(df)):
                row = df.iloc[i]
                
                # 跳过空行
                if row.isna().all():
                    continue
                
                # 解析渠道信息
                channel = self._parse_channel_row(row, df.columns)
                if channel:
                    channels.append(channel)
                    
        except Exception as e:
            logger.error(f"解析工作表 {sheet_name} 失败: {e}")
        
        return channels
    
    def _parse_channel_row(self, row: pd.Series, columns) -> Optional[LogisticsChannel]:
        """解析单行渠道数据"""
        try:
            # 提取渠道名称
            channel_name = None
            for cell in row:
                if pd.notna(cell) and isinstance(cell, str) and ('Express' in cell or 'Standard' in cell or 'Economy' in cell):
                    channel_name = cell.strip()
                    break
            
            if not channel_name:
                return None
            
            # 解析资费信息
            fee_info = self._parse_fee_structure(row)
            if not fee_info:
                return None
            
            # 解析其他限制信息
            constraints = self._parse_constraints(row)
            
            return LogisticsChannel(
                name=channel_name,
                service_level=self._extract_service_level(channel_name),
                base_fee=fee_info['base_fee'],
                weight_fee=fee_info['weight_fee'],
                weight_unit=fee_info['weight_unit'],
                max_weight_kg=constraints.get('max_weight', 25),
                max_value_rub=constraints.get('max_value', 0),
                max_dimensions=constraints.get('max_dimensions', 200),
                max_single_side=constraints.get('max_single_side', 115),
                delivery_days=constraints.get('delivery_days', '5-10天')
            )
            
        except Exception as e:
            logger.error(f"解析渠道行失败: {e}")
            return None
    
    def _parse_fee_structure(self, row: pd.Series) -> Optional[Dict]:
        """解析资费结构"""
        for cell in row:
            if pd.notna(cell) and isinstance(cell, str):
                # 匹配不同的资费格式
                patterns = [
                    r'(\d+(?:\.\d+)?)元.*?(\d+(?:\.\d+)?)元/(?:千克|kg|KG)',  # XX元 + XX元/KG
                    r'(\d+(?:\.\d+)?)元.*?(\d+(?:\.\d+)?)元/(?:克|g)',        # XX元 + XX元/g
                    r'(\d+(?:\.\d+)?).*?(\d+(?:\.\d+)?)元/(?:千克|kg|KG)',    # XX + XX元/KG
                    r'(\d+(?:\.\d+)?).*?(\d+(?:\.\d+)?)元/(?:克|g)',         # XX + XX元/g
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, cell)
                    if match:
                        base_fee = float(match.group(1))
                        weight_fee = float(match.group(2))
                        weight_unit = 'kg' if ('千克' in cell or 'kg' in cell.lower()) else 'g'
                        
                        return {
                            'base_fee': base_fee,
                            'weight_fee': weight_fee,
                            'weight_unit': weight_unit
                        }
        
        return None
    
    def _parse_constraints(self, row: pd.Series) -> Dict:
        """解析约束条件"""
        constraints = {}
        
        for cell in row:
            if pd.notna(cell) and isinstance(cell, str):
                # 解析重量限制
                weight_match = re.search(r'(\d+(?:\.\d+)?)KG', cell, re.IGNORECASE)
                if weight_match:
                    constraints['max_weight'] = float(weight_match.group(1))
                
                # 解析货值限制
                value_match = re.search(r'(\d+)卢布', cell)
                if value_match:
                    constraints['max_value'] = float(value_match.group(1))
                
                # 解析尺寸限制
                dim_match = re.search(r'(\d+)CM', cell, re.IGNORECASE)
                if dim_match:
                    constraints['max_dimensions'] = float(dim_match.group(1))
                
                # 解析时效
                time_match = re.search(r'(\d+-\d+天)', cell)
                if time_match:
                    constraints['delivery_days'] = time_match.group(1)
        
        return constraints
    
    def _extract_service_level(self, channel_name: str) -> str:
        """提取服务等级"""
        if 'Express' in channel_name:
            return '超快速'
        elif 'Standard' in channel_name:
            return '快速'
        elif 'Economy' in channel_name:
            return '经济'
        else:
            return '标准'
    
    def classify_product(self, product: ProductInfo) -> ProductCategory:
        """商品分类"""
        if product.weight_kg <= 0.5 and product.ozon_price_rub <= 1500:
            return ProductCategory.EXTRA_SMALL
        elif product.weight_kg <= 2 and 1501 <= product.ozon_price_rub <= 7000:
            return ProductCategory.SMALL
        elif product.weight_kg <= 25 and product.ozon_price_rub <= 1500:
            return ProductCategory.BUDGET
        else:
            return ProductCategory.STANDARD
    
    def find_available_channels(self, product: ProductInfo) -> List[Tuple[str, LogisticsChannel, float]]:
        """查找可用的物流渠道"""
        available = []
        
        for provider, channels in self.channels.items():
            for channel in channels:
                cost = channel.calculate_shipping_cost(product)
                if cost is not None:
                    available.append((provider, channel, cost))
        
        # 按费用排序
        available.sort(key=lambda x: x[2])
        return available
    
    def calculate_profit(self, product: ProductInfo, 
                        ozon_commission_rate: float = 0.15,
                        other_fees_cny: float = 0) -> ProfitCalculation:
        """
        计算商品利润
        
        Args:
            product: 商品信息
            ozon_commission_rate: OZON佣金率(默认15%)
            other_fees_cny: 其他费用(人民币)
        """
        warnings = []
        
        # 商品分类
        category = self.classify_product(product)
        
        # 查找可用渠道
        available_channels = self.find_available_channels(product)
        
        if not available_channels:
            warnings.append("没有找到合适的物流渠道")
            return ProfitCalculation(
                product_sku=product.sku,
                category=category,
                available_channels=[],
                best_channel="无",
                shipping_cost_cny=0,
                total_cost_cny=product.purchase_price_cny,
                revenue_cny=product.ozon_price_rub / self.exchange_rate,
                profit_cny=0,
                profit_margin=0,
                warnings=warnings
            )
        
        # 选择最便宜的渠道
        best_provider, best_channel, shipping_cost_cny = available_channels[0]
        
        # 计算收入(卢布转人民币)
        revenue_cny = product.ozon_price_rub / self.exchange_rate
        
        # 计算OZON佣金
        ozon_commission_cny = revenue_cny * ozon_commission_rate
        
        # 计算总成本
        total_cost_cny = (
            product.purchase_price_cny +      # 采购成本
            shipping_cost_cny +               # 物流费用
            ozon_commission_cny +             # OZON佣金
            other_fees_cny                    # 其他费用
        )
        
        # 计算利润
        profit_cny = revenue_cny - total_cost_cny
        profit_margin = (profit_cny / revenue_cny) * 100 if revenue_cny > 0 else 0
        
        # 添加警告
        if profit_margin < 10:
            warnings.append(f"利润率过低: {profit_margin:.1f}%")
        
        if product.weight_kg > best_channel.max_weight_kg * 0.9:
            warnings.append("商品重量接近物流限制")
        
        return ProfitCalculation(
            product_sku=product.sku,
            category=category,
            available_channels=[f"{p}-{c.name}" for p, c, _ in available_channels[:3]],
            best_channel=f"{best_provider}-{best_channel.name}",
            shipping_cost_cny=shipping_cost_cny,
            total_cost_cny=total_cost_cny,
            revenue_cny=revenue_cny,
            profit_cny=profit_cny,
            profit_margin=profit_margin,
            warnings=warnings
        )
    
    def batch_calculate(self, products: List[ProductInfo]) -> List[ProfitCalculation]:
        """批量计算利润"""
        results = []
        for product in products:
            try:
                result = self.calculate_profit(product)
                results.append(result)
            except Exception as e:
                logger.error(f"计算商品 {product.sku} 利润失败: {e}")
                # 创建错误结果
                error_result = ProfitCalculation(
                    product_sku=product.sku,
                    category=ProductCategory.STANDARD,
                    available_channels=[],
                    best_channel="计算失败",
                    shipping_cost_cny=0,
                    total_cost_cny=0,
                    revenue_cny=0,
                    profit_cny=0,
                    profit_margin=0,
                    warnings=[f"计算失败: {str(e)}"]
                )
                results.append(error_result)
        
        return results
    
    def get_channel_summary(self) -> Dict[str, int]:
        """获取渠道汇总信息"""
        summary = {}
        for provider, channels in self.channels.items():
            summary[provider] = len(channels)
        return summary


# 使用示例和测试函数
def create_sample_product() -> ProductInfo:
    """创建示例商品"""
    return ProductInfo(
        sku="TEST001",
        weight_kg=0.6,
        dimensions_cm="20x15x10",
        ozon_price_rub=1200,
        purchase_price_cny=50,
        exchange_rate=13.5
    )


def main():
    """主函数 - 用于测试"""
    try:
        # 创建计算器实例
        calculator = OzonCalculator()
        
        # 显示加载的渠道信息
        print("=== 物流渠道汇总 ===")
        summary = calculator.get_channel_summary()
        for provider, count in summary.items():
            print(f"{provider}: {count} 个渠道")
        
        # 创建测试商品
        product = create_sample_product()
        print(f"\n=== 商品信息 ===")
        print(f"SKU: {product.sku}")
        print(f"重量: {product.weight_kg}KG")
        print(f"尺寸: {product.dimensions_cm}")
        print(f"OZON价格: {product.ozon_price_rub}卢布")
        print(f"采购价格: {product.purchase_price_cny}元")
        
        # 计算利润
        result = calculator.calculate_profit(product)
        
        print(f"\n=== 利润计算结果 ===")
        print(f"商品分类: {result.category.value}")
        print(f"最佳渠道: {result.best_channel}")
        print(f"物流费用: {result.shipping_cost_cny:.2f}元")
        print(f"总成本: {result.total_cost_cny:.2f}元")
        print(f"收入: {result.revenue_cny:.2f}元")
        print(f"利润: {result.profit_cny:.2f}元")
        print(f"利润率: {result.profit_margin:.1f}%")
        
        if result.warnings:
            print(f"\n⚠️ 警告:")
            for warning in result.warnings:
                print(f"  - {warning}")
        
        print(f"\n可用渠道: {', '.join(result.available_channels)}")
        
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == "__main__":
    main()