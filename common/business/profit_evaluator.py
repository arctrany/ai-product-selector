"""
利润评估器

负责集成Excel利润计算器进行利润计算和评估。
"""

import logging
from typing import Optional, Dict, Any

# 延迟导入，避免循环导入
# from ..excel_processor import ExcelProfitProcessor
from ..models import ProductInfo, PriceCalculationResult
from ..config import GoodStoreSelectorConfig, get_config
# 延迟导入，避免循环导入
# # 延迟导入，避免循环导入
# from ..excel_processor import ExcelProfitProcessor
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
        # 延迟导入，避免循环导入
        # self.excel_processor = ExcelProfitProcessor(profit_calculator_path, config)

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
            # 1. 检查上架时间是否符合要求
            if not self._validate_shelf_time(product_info):
                return self._create_shelf_time_rejected_result(product_info)

            # 2. 定价计算
            pricing_result = self.pricing_calculator.calculate_complete_pricing(
                green_price_rub=product_info.green_price,
                black_price_rub=product_info.black_price
            )

            # 3. 如果有货源价格，使用Excel计算器进行精确利润计算
            excel_result = None
            # 如果有货源价格，使用Excel计算器进行精确利润计算
            excel_result = None
            # if source_price and self._has_required_data(product_info):
            #     try:
            #         excel_result = self.excel_processor.calculate_product_profit(
            #             black_price=pricing_result.real_selling_price,  # 使用计算后的真实售价
            #             green_price=pricing_result.product_pricing,     # 使用计算后的商品定价
            #             commission_rate=product_info.commission_rate or self.config.price_calculation.commission_rate_default,
            #             weight=product_info.weight or 500.0  # 默认重量500克
            #         )
            #     except Exception as e:
            #         self.logger.warning(f"Excel利润计算失败: {e}")

            # 4. 综合评估结果
            evaluation_result = self._create_evaluation_result(
                product_info, pricing_result, excel_result, source_price
            )

            return evaluation_result

        except Exception as e:
            self.logger.error(f"评估商品利润失败: {e}")
            return self._create_error_result(str(e))

    def _validate_shelf_time(self, product_info: ProductInfo) -> bool:
        """
        验证商品上架时间是否符合要求

        Args:
            product_info: 商品信息

        Returns:
            bool: 是否符合要求
        """
        try:
            # 如果没有上架时间信息，直接通过验证
            if product_info.shelf_days is None:
                return True

            # 检查上架时间是否超过配置的阈值
            max_shelf_days = getattr(self.config, 'item_shelf_days', 150)
            if product_info.shelf_days > max_shelf_days:
                self.logger.info(
                    f"商品{product_info.product_id}上架时间过长: {product_info.shelf_days}天 > {max_shelf_days}天")
                return False

            return True

        except Exception as e:
            self.logger.error(f"验证商品上架时间失败: {e}")
            return True  # 出错时默认通过验证

    def _create_shelf_time_rejected_result(self, product_info: ProductInfo) -> Dict[str, Any]:
        """
        创建因上架时间不符合要求而被拒绝的结果

        Args:
            product_info: 商品信息

        Returns:
            Dict[str, Any]: 拒绝结果
        """
        return {
            'product_id': product_info.product_id,
            'pricing_calculation': None,
            'source_price': None,
            'has_excel_calculation': False,
            'profit_amount': 0.0,
            'profit_rate': 0.0,
            'is_profitable': False,
            'meets_profit_threshold': False,
            'calculation_source': 'shelf_time_rejected',
            'shelf_days': product_info.shelf_days,
            'error_message': f'商品上架时间过长: {product_info.shelf_days}天',
            'evaluation_summary': f"商品{product_info.product_id}: 上架时间过长({product_info.shelf_days}天)，不符合要求"
        }

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
                result['profit_rate'] >= self.config.selector_filter.profit_rate_threshold
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
        results: list[Dict[str, Any]] = []
        source_prices_dict: Dict[str, float] = source_prices or {}

        for product in products:
            try:
                source_price = source_prices_dict.get(product.product_id)
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

    def has_better_competitor_price(self, result_data: Dict[str, Any]) -> bool:
        """
        判断跟卖价格是否比主价格更优

        Args:
            result_data: 包含价格数据的结果字典

        Returns:
            bool: 如果跟卖价格更优返回True，否则返回False
        """
        try:
            # 确保价格字段存在（即使为空）
            price_data = result_data.get('price_data', {})
            if 'green_price' not in price_data:
                price_data['green_price'] = None
            if 'black_price' not in price_data:
                price_data['black_price'] = None

            # 获取价格数据
            green_price = price_data.get('green_price')
            black_price = price_data.get('black_price')
            competitor_price = price_data.get('competitor_price')

            # 跟卖价格无效时返回 False
            if not competitor_price or competitor_price <= 0:
                self.logger.info("跟卖价格为空或无效，has_better_price 设置为 False")
                return False

            # 没有主价格时返回 False
            if not black_price:
                self.logger.info("未检测到主价格，跳过价格比较")
                return False

            # 优先比较绿标价格，其次比较黑标价格
            compare_price = green_price if green_price else black_price

            if competitor_price < compare_price:
                self.logger.info(f"跟卖价格({competitor_price}₽)比主价格({compare_price}₽)更低")
                return True
            else:
                self.logger.info(f"跟卖价格({competitor_price}₽)不比主价格({compare_price}₽)更低")
                return False

        except Exception as e:
            self.logger.error(f"判断跟卖价格优势失败: {e}")
            return False

    def close(self):
        """关闭评估器"""
        # if self.excel_processor:
        #     self.excel_processor.close()
