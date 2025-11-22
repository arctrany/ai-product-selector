"""
定价计算器

负责根据规格要求计算商品的真实售价和定价。
"""

import logging
from typing import Optional, Tuple, Dict, Any

from ..models import PriceCalculationResult
from ..config import GoodStoreSelectorConfig, get_config


class PricingCalculator:
    """定价计算器"""
    
    def __init__(self, config: Optional[GoodStoreSelectorConfig] = None):
        """
        初始化定价计算器
        
        Args:
            config: 配置对象
        """
        self.config = config or get_config()
        self.logger = logging.getLogger(f"{__name__}.PricingCalculator")
    
    def calculate_real_selling_price(self, green_price: Optional[float], 
                                   black_price: Optional[float]) -> float:
        """
        计算真实售价
        
        Args:
            green_price: 绿标价格（人民币）
            black_price: 黑标价格（人民币）
            
        Returns:
            float: 真实售价（人民币）
        """
        try:
            # 如果只有黑标价格，直接使用黑标价格
            if not green_price and black_price:
                self.logger.debug(f"只有黑标价格，真实售价 = {black_price}")
                return black_price
            
            # 如果没有价格信息，返回0
            if not green_price and not black_price:
                self.logger.warning("没有价格信息")
                return 0.0
            
            # 使用绿标价格作为基准
            base_price = green_price or black_price
            
            # 根据规格要求的价格计算规则
            if base_price <= self.config.price_calculation.price_adjustment_threshold_1:
                # 黑标价格 <= 90人民币：真实售价 = 黑标价格
                real_price = black_price or base_price
                self.logger.debug(f"价格 <= {self.config.price_calculation.price_adjustment_threshold_1}，真实售价 = {real_price}")
                
            elif base_price <= self.config.price_calculation.price_adjustment_threshold_2:
                # 90人民币 < 黑标价格 <= 120人民币：真实售价 = 黑标价格 + 5
                real_price = (black_price or base_price) + self.config.price_calculation.price_adjustment_amount
                self.logger.debug(f"{self.config.price_calculation.price_adjustment_threshold_1} < 价格 <= {self.config.price_calculation.price_adjustment_threshold_2}，真实售价 = {real_price}")
                
            else:
                # 黑标价格 > 120人民币：真实售价 = (黑标 - 绿标) × 2.2 + 黑标
                if green_price and black_price:
                    real_price = (black_price - green_price) * self.config.price_calculation.price_multiplier + black_price
                else:
                    real_price = base_price
                self.logger.debug(f"价格 > {self.config.price_calculation.price_adjustment_threshold_2}，真实售价 = {real_price}")
            
            return max(real_price, 0.0)  # 确保价格不为负数
            
        except Exception as e:
            self.logger.error(f"计算真实售价失败: {e}")
            return black_price or green_price or 0.0
    
    def calculate_product_pricing(self, real_selling_price: float) -> float:
        """
        计算商品定价（95折）
        
        Args:
            real_selling_price: 真实售价
            
        Returns:
            float: 商品定价
        """
        try:
            product_pricing = real_selling_price * self.config.price_calculation.pricing_discount_rate
            self.logger.debug(f"商品定价 = {real_selling_price} × {self.config.price_calculation.pricing_discount_rate} = {product_pricing}")
            return product_pricing
            
        except Exception as e:
            self.logger.error(f"计算商品定价失败: {e}")
            return real_selling_price
    
    def convert_rub_to_cny(self, rub_amount: float) -> float:
        """
        卢布转人民币
        
        Args:
            rub_amount: 卢布金额
            
        Returns:
            float: 人民币金额
        """
        try:
            cny_amount = rub_amount * self.config.price_calculation.rub_to_cny_rate
            self.logger.debug(f"汇率转换: {rub_amount} RUB = {cny_amount} CNY")
            return cny_amount
            
        except Exception as e:
            self.logger.error(f"汇率转换失败: {e}")
            return rub_amount
    
    def calculate_complete_pricing(self, green_price_rub: Optional[float], 
                                 black_price_rub: Optional[float]) -> PriceCalculationResult:
        """
        完整的定价计算流程
        
        Args:
            green_price_rub: 绿标价格（卢布）
            black_price_rub: 黑标价格（卢布）
            
        Returns:
            PriceCalculationResult: 价格计算结果
        """
        try:
            calculation_details = {
                'input_green_price_rub': green_price_rub,
                'input_black_price_rub': black_price_rub,
                'exchange_rate': self.config.price_calculation.rub_to_cny_rate,
                'discount_rate': self.config.price_calculation.pricing_discount_rate
            }
            
            # 1. 汇率转换
            green_price_cny = self.convert_rub_to_cny(green_price_rub) if green_price_rub else None
            black_price_cny = self.convert_rub_to_cny(black_price_rub) if black_price_rub else None
            
            calculation_details.update({
                'green_price_cny': green_price_cny,
                'black_price_cny': black_price_cny
            })
            
            # 2. 计算真实售价
            real_selling_price = self.calculate_real_selling_price(green_price_cny, black_price_cny)
            calculation_details['real_selling_price'] = real_selling_price
            
            # 3. 计算商品定价
            product_pricing = self.calculate_product_pricing(real_selling_price)
            calculation_details['product_pricing'] = product_pricing
            
            # 4. 计算利润（这里只是价格差，实际利润需要减去成本）
            profit_amount = real_selling_price - product_pricing
            profit_rate = (profit_amount / real_selling_price * 100) if real_selling_price > 0 else 0.0
            
            calculation_details.update({
                'profit_amount': profit_amount,
                'profit_rate': profit_rate
            })
            
            # 创建结果对象
            result = PriceCalculationResult(
                real_selling_price=real_selling_price,
                product_pricing=product_pricing,
                profit_amount=profit_amount,
                profit_rate=profit_rate,
                is_profitable=profit_rate >= self.config.selector_filter.profit_rate_threshold,
                calculation_details=calculation_details
            )
            
            # 🔧 修复：只有在有效价格时才输出日志
            if real_selling_price > 0:
                self.logger.info(f"定价计算完成: 真实售价={real_selling_price:.2f}, 商品定价={product_pricing:.2f}, 利润率={profit_rate:.2f}%")
            else:
                self.logger.debug(f"价格计算结果为0，跳过日志输出")
            return result
            
        except Exception as e:
            self.logger.error(f"完整定价计算失败: {e}")
            return PriceCalculationResult(
                real_selling_price=0.0,
                product_pricing=0.0,
                profit_amount=0.0,
                profit_rate=0.0,
                is_profitable=False,
                calculation_details={'error': str(e)}
            )
    
    def validate_prices(self, green_price: Optional[float], 
                       black_price: Optional[float]) -> bool:
        """
        验证价格数据的有效性
        
        Args:
            green_price: 绿标价格
            black_price: 黑标价格
            
        Returns:
            bool: 价格是否有效
        """
        try:
            # 至少要有一个价格
            if not green_price and not black_price:
                return False
            
            # 价格必须为正数
            if green_price is not None and green_price <= 0:
                return False
            
            if black_price is not None and black_price <= 0:
                return False
            
            # 如果两个价格都存在，绿标价格应该小于等于黑标价格
            if green_price and black_price and green_price > black_price:
                self.logger.warning(f"绿标价格({green_price})大于黑标价格({black_price})，可能存在异常")
                # 不直接返回False，因为可能是促销等特殊情况
            
            return True
            
        except Exception as e:
            self.logger.error(f"验证价格失败: {e}")
            return False
    
    def get_pricing_summary(self, result: PriceCalculationResult) -> str:
        """
        获取定价计算摘要
        
        Args:
            result: 价格计算结果
            
        Returns:
            str: 摘要字符串
        """
        try:
            return (
                f"定价摘要: 真实售价 ¥{result.real_selling_price:.2f}, "
                f"商品定价 ¥{result.product_pricing:.2f}, "
                f"利润率 {result.profit_rate:.2f}%, "
                f"{'有利润' if result.is_profitable else '无利润'}"
            )
        except Exception as e:
            self.logger.error(f"生成定价摘要失败: {e}")
            return "定价摘要生成失败"