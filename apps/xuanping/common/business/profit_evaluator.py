"""
利润评估器

负责集成Excel利润计算器进行利润计算和评估。
"""

import logging
from typing import Optional, Dict, Any

from ..models import ProductInfo, PriceCalculationResult
from ..config import GoodStoreSelectorConfig, get_config
from ..excel_processor import ExcelProfitProcessor
from .pricing_calculator import PricingCalculator


class ProfitEvaluator:
    """利润评估器"""
    
    def __init__(self, profit_calculator_path: str, config: Optional[GoodStoreSelectorConfig] = None):
        """
        初始化利润评估器
        
        Args:
            profit_calculator_path: Excel利润计算器文件路径
            config: 配置对象
        """
        self.config = config or get_config()
        self.logger = logging.getLogger(f"{__name__}.ProfitEvaluator")
        
        # 初始化组件
        self.pricing_calculator = PricingCalculator(config)
        self.excel_processor = ExcelProfitProcessor(profit_calculator_path, config)
    
    def evaluate_product_profit(self, product_info: ProductInfo, 
                              source_price: Optional[float] = None) -> Dict[str, Any]:
        """
        评估商品利润
        
        Args:
            product_info: 商品信息
            source_price: 货源价格（采购价格）
            
        Returns:
            Dict[str, Any]: 利润评估结果
        """
        try:
            # 1. 定价计算
            pricing_result = self.pricing_calculator.calculate_complete_pricing(
                green_price_rub=product_info.green_price,
                black_price_rub=product_info.black_price
            )
            
            # 2. 如果有货源价格，使用Excel计算器进行精确利润计算
            excel_result = None
            if source_price and self._has_required_data(product_info):
                try:
                    excel_result = self.excel_processor.calculate_product_profit(
                        black_price=pricing_result.real_selling_price,  # 使用计算后的真实售价
                        green_price=pricing_result.product_pricing,     # 使用计算后的商品定价
                        commission_rate=product_info.commission_rate or self.config.price_calculation.commission_rate_default,
                        weight=product_info.weight or 500.0  # 默认重量500克
                    )
                except Exception as e:
                    self.logger.warning(f"Excel利润计算失败: {e}")
            
            # 3. 综合评估结果
            evaluation_result = self._create_evaluation_result(
                product_info, pricing_result, excel_result, source_price
            )
            
            return evaluation_result
            
        except Exception as e:
            self.logger.error(f"评估商品利润失败: {e}")
            return self._create_error_result(str(e))
    
    def _has_required_data(self, product_info: ProductInfo) -> bool:
        """
        检查是否有进行Excel计算所需的数据
        
        Args:
            product_info: 商品信息
            
        Returns:
            bool: 是否有必要数据
        """
        return (
            product_info.green_price is not None and
            product_info.black_price is not None and
            (product_info.commission_rate is not None or 
             self.config.price_calculation.commission_rate_default is not None)
        )
    
    def _create_evaluation_result(self, product_info: ProductInfo,
                                pricing_result: PriceCalculationResult,
                                excel_result: Optional[Any] = None,
                                source_price: Optional[float] = None) -> Dict[str, Any]:
        """
        创建评估结果
        
        Args:
            product_info: 商品信息
            pricing_result: 定价计算结果
            excel_result: Excel计算结果
            source_price: 货源价格
            
        Returns:
            Dict[str, Any]: 评估结果
        """
        result = {
            'product_id': product_info.product_id,
            'pricing_calculation': pricing_result,
            'source_price': source_price,
            'has_excel_calculation': excel_result is not None
        }
        
        # 如果有Excel计算结果，使用更精确的利润数据
        if excel_result:
            result.update({
                'profit_amount': excel_result.profit_amount,
                'profit_rate': excel_result.profit_rate,
                'is_profitable': not excel_result.is_loss,
                'excel_calculation_time': excel_result.calculation_time,
                'calculation_source': 'excel'
            })
        else:
            # 使用定价计算的结果
            result.update({
                'profit_amount': pricing_result.profit_amount,
                'profit_rate': pricing_result.profit_rate,
                'is_profitable': pricing_result.is_profitable,
                'calculation_source': 'pricing_only'
            })
        
        # 判断是否符合利润阈值
        result['meets_profit_threshold'] = (
            result['profit_rate'] >= self.config.store_filter.profit_rate_threshold
        )
        
        # 添加评估摘要
        result['evaluation_summary'] = self._create_evaluation_summary(result)
        
        return result
    
    def _create_evaluation_summary(self, result: Dict[str, Any]) -> str:
        """
        创建评估摘要
        
        Args:
            result: 评估结果
            
        Returns:
            str: 评估摘要
        """
        try:
            profit_status = "有利润" if result['is_profitable'] else "无利润"
            threshold_status = "达标" if result['meets_profit_threshold'] else "不达标"
            calculation_source = "Excel精确计算" if result['calculation_source'] == 'excel' else "定价估算"
            
            return (
                f"商品{result['product_id']}: {profit_status}, "
                f"利润率{result['profit_rate']:.2f}% ({threshold_status}), "
                f"利润金额¥{result['profit_amount']:.2f}, "
                f"计算方式: {calculation_source}"
            )
        except Exception as e:
            self.logger.error(f"创建评估摘要失败: {e}")
            return "评估摘要生成失败"
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """
        创建错误结果
        
        Args:
            error_message: 错误信息
            
        Returns:
            Dict[str, Any]: 错误结果
        """
        return {
            'product_id': 'unknown',
            'profit_amount': 0.0,
            'profit_rate': 0.0,
            'is_profitable': False,
            'meets_profit_threshold': False,
            'calculation_source': 'error',
            'error_message': error_message,
            'evaluation_summary': f"利润评估失败: {error_message}"
        }
    
    def batch_evaluate_products(self, products: list[ProductInfo], 
                              source_prices: Optional[Dict[str, float]] = None) -> list[Dict[str, Any]]:
        """
        批量评估商品利润
        
        Args:
            products: 商品列表
            source_prices: 货源价格字典，key为product_id
            
        Returns:
            list[Dict[str, Any]]: 评估结果列表
        """
        results = []
        source_prices = source_prices or {}
        
        for product in products:
            try:
                source_price = source_prices.get(product.product_id)
                result = self.evaluate_product_profit(product, source_price)
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"批量评估商品{product.product_id}失败: {e}")
                results.append(self._create_error_result(str(e)))
        
        self.logger.info(f"批量评估完成，共{len(products)}个商品")
        return results
    
    def get_profitable_products(self, evaluation_results: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """
        筛选有利润的商品
        
        Args:
            evaluation_results: 评估结果列表
            
        Returns:
            list[Dict[str, Any]]: 有利润的商品列表
        """
        profitable_products = [
            result for result in evaluation_results 
            if result.get('meets_profit_threshold', False)
        ]
        
        self.logger.info(f"筛选出{len(profitable_products)}个有利润商品（总共{len(evaluation_results)}个）")
        return profitable_products
    
    def get_evaluation_statistics(self, evaluation_results: list[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取评估统计信息
        
        Args:
            evaluation_results: 评估结果列表
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            total_products = len(evaluation_results)
            profitable_products = len([r for r in evaluation_results if r.get('is_profitable', False)])
            threshold_products = len([r for r in evaluation_results if r.get('meets_profit_threshold', False)])
            
            # 计算平均利润率
            profit_rates = [r.get('profit_rate', 0) for r in evaluation_results if r.get('profit_rate') is not None]
            avg_profit_rate = sum(profit_rates) / len(profit_rates) if profit_rates else 0
            
            # 计算最高和最低利润率
            max_profit_rate = max(profit_rates) if profit_rates else 0
            min_profit_rate = min(profit_rates) if profit_rates else 0
            
            return {
                'total_products': total_products,
                'profitable_products': profitable_products,
                'threshold_products': threshold_products,
                'profitable_rate': (profitable_products / total_products * 100) if total_products > 0 else 0,
                'threshold_rate': (threshold_products / total_products * 100) if total_products > 0 else 0,
                'avg_profit_rate': avg_profit_rate,
                'max_profit_rate': max_profit_rate,
                'min_profit_rate': min_profit_rate,
                'profit_threshold': self.config.store_filter.profit_rate_threshold
            }
            
        except Exception as e:
            self.logger.error(f"获取评估统计信息失败: {e}")
            return {'error': str(e)}
    
    def close(self):
        """关闭评估器"""
        if self.excel_processor:
            self.excel_processor.close()