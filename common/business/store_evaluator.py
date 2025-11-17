"""
店铺评估器

负责店铺级别的评估和好店判定。
"""

import logging
from typing import List, Dict, Any, Optional

from ..models import StoreInfo, StoreAnalysisResult, ProductAnalysisResult, GoodStoreFlag, StoreStatus
from ..config import GoodStoreSelectorConfig, get_config


class StoreEvaluator:
    """店铺评估器"""
    
    def __init__(self, config: Optional[GoodStoreSelectorConfig] = None):
        """
        初始化店铺评估器
        
        Args:
            config: 配置对象
        """
        self.config = config or get_config()
        self.logger = logging.getLogger(f"{__name__}.StoreEvaluator")
    
    def evaluate_store(self, store_info: StoreInfo, 
                      product_evaluations: List[Dict[str, Any]]) -> StoreAnalysisResult:
        """
        评估店铺
        
        Args:
            store_info: 店铺信息
            product_evaluations: 商品评估结果列表
            
        Returns:
            StoreAnalysisResult: 店铺分析结果
        """
        try:
            # 1. 验证店铺初筛条件
            if not self.filter_store({
                'sold_30days': store_info.sold_30days,
                'sold_count_30days': store_info.sold_count_30days
            }):
                return self._create_failed_store_result(store_info, "不符合初筛条件")

            # 2. 转换商品评估结果
            product_results = self._convert_product_evaluations(product_evaluations)

            # 3. 创建店铺分析结果
            store_result = StoreAnalysisResult(
                store_info=store_info,
                products=product_results,
                profit_rate_threshold=self.config.store_filter.profit_rate_threshold,
                good_store_threshold=self.config.store_filter.good_store_ratio_threshold
            )

            # 4. 记录评估日志
            self._log_evaluation_result(store_result)

            return store_result

        except Exception as e:
            self.logger.error(f"评估店铺{store_info.store_id}失败: {e}")
            return self._create_failed_store_result(store_info, str(e))

    def _convert_product_evaluations(self, product_evaluations: List[Dict[str, Any]]) -> List[ProductAnalysisResult]:
        """
        转换商品评估结果为ProductAnalysisResult
        
        Args:
            product_evaluations: 商品评估结果列表
            
        Returns:
            List[ProductAnalysisResult]: 转换后的结果列表
        """
        product_results = []
        
        for evaluation in product_evaluations:
            try:
                # 从评估结果中提取商品信息
                product_info = self._extract_product_info_from_evaluation(evaluation)
                
                # 从评估结果中提取价格计算结果
                price_calculation = evaluation.get('pricing_calculation')
                
                # 创建ProductAnalysisResult
                product_result = ProductAnalysisResult(
                    product_info=product_info,
                    price_calculation=price_calculation,
                    competitor_stores=[]  # 这里可以后续扩展
                )
                
                product_results.append(product_result)
                
            except Exception as e:
                self.logger.warning(f"转换商品评估结果失败: {e}")
                continue
        
        return product_results
    
    def _extract_product_info_from_evaluation(self, evaluation: Dict[str, Any]):
        """
        从评估结果中提取商品信息
        
        Args:
            evaluation: 评估结果
            
        Returns:
            ProductInfo: 商品信息
        """
        from ..models import ProductInfo
        
        # 这里需要从evaluation中重建ProductInfo
        # 实际实现中可能需要传递原始的ProductInfo对象
        return ProductInfo(
            product_id=evaluation.get('product_id', 'unknown'),
            green_price=evaluation.get('pricing_calculation', {}).get('calculation_details', {}).get('green_price_cny'),
            black_price=evaluation.get('pricing_calculation', {}).get('calculation_details', {}).get('black_price_cny'),
            commission_rate=evaluation.get('commission_rate'),
            weight=evaluation.get('weight'),
            source_price=evaluation.get('source_price'),
            source_matched=evaluation.get('source_price') is not None
        )
    
    def _create_failed_store_result(self, store_info: StoreInfo, reason: str) -> StoreAnalysisResult:
        """
        创建失败的店铺结果
        
        Args:
            store_info: 店铺信息
            reason: 失败原因
            
        Returns:
            StoreAnalysisResult: 失败结果
        """
        # 更新店铺状态
        store_info.is_good_store = GoodStoreFlag.NO
        store_info.status = StoreStatus.PROCESSED
        
        return StoreAnalysisResult(
            store_info=store_info,
            products=[],
            profit_rate_threshold=self.config.store_filter.profit_rate_threshold,
            good_store_threshold=self.config.store_filter.good_store_ratio_threshold
        )
    
    def _log_evaluation_result(self, store_result: StoreAnalysisResult):
        """
        记录评估结果日志
        
        Args:
            store_result: 店铺分析结果
        """
        try:
            store_id = store_result.store_info.store_id
            total_products = store_result.total_products
            profitable_products = store_result.profitable_products
            is_good_store = store_result.store_info.is_good_store
            
            profit_ratio = (profitable_products / total_products * 100) if total_products > 0 else 0
            
            self.logger.info(
                f"店铺{store_id}评估完成: "
                f"总商品{total_products}个, 有利润商品{profitable_products}个 ({profit_ratio:.1f}%), "
                f"判定结果: {is_good_store.value}"
            )
            
        except Exception as e:
            self.logger.error(f"记录评估结果日志失败: {e}")
    
    def batch_evaluate_stores(self, stores_data: List[Dict[str, Any]]) -> List[StoreAnalysisResult]:
        """
        批量评估店铺
        
        Args:
            stores_data: 店铺数据列表，每个元素包含store_info和product_evaluations
            
        Returns:
            List[StoreAnalysisResult]: 店铺分析结果列表
        """
        results = []
        
        for store_data in stores_data:
            try:
                store_info = store_data['store_info']
                product_evaluations = store_data.get('product_evaluations', [])
                
                result = self.evaluate_store(store_info, product_evaluations)
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"批量评估店铺失败: {e}")
                continue
        
        self.logger.info(f"批量评估完成，共{len(stores_data)}个店铺")
        return results
    
    def get_good_stores(self, store_results: List[StoreAnalysisResult]) -> List[StoreAnalysisResult]:
        """
        筛选好店
        
        Args:
            store_results: 店铺分析结果列表
            
        Returns:
            List[StoreAnalysisResult]: 好店列表
        """
        good_stores = [
            result for result in store_results 
            if result.store_info.is_good_store == GoodStoreFlag.YES
        ]
        
        self.logger.info(f"筛选出{len(good_stores)}个好店（总共{len(store_results)}个店铺）")
        return good_stores
    
    def get_evaluation_statistics(self, store_results: List[StoreAnalysisResult]) -> Dict[str, Any]:
        """
        获取评估统计信息
        
        Args:
            store_results: 店铺分析结果列表
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            total_stores = len(store_results)
            good_stores = len([r for r in store_results if r.store_info.is_good_store == GoodStoreFlag.YES])
            processed_stores = len([r for r in store_results if r.store_info.status == StoreStatus.PROCESSED])
            
            # 计算总商品数和有利润商品数
            total_products = sum(r.total_products for r in store_results)
            total_profitable_products = sum(r.profitable_products for r in store_results)
            
            # 计算平均利润商品比例
            profit_ratios = []
            for result in store_results:
                if result.total_products > 0:
                    ratio = result.profitable_products / result.total_products * 100
                    profit_ratios.append(ratio)
            
            avg_profit_ratio = sum(profit_ratios) / len(profit_ratios) if profit_ratios else 0
            
            return {
                'total_stores': total_stores,
                'good_stores': good_stores,
                'processed_stores': processed_stores,
                'good_store_rate': (good_stores / total_stores * 100) if total_stores > 0 else 0,
                'total_products': total_products,
                'total_profitable_products': total_profitable_products,
                'overall_profit_rate': (total_profitable_products / total_products * 100) if total_products > 0 else 0,
                'avg_store_profit_ratio': avg_profit_ratio,
                'profit_threshold': self.config.store_filter.profit_rate_threshold,
                'good_store_threshold': self.config.store_filter.good_store_ratio_threshold
            }
            
        except Exception as e:
            self.logger.error(f"获取评估统计信息失败: {e}")
            return {'error': str(e)}
    
    def should_collect_competitors(self, product_evaluation: Dict[str, Any]) -> bool:
        """
        判断是否应该采集跟卖店铺信息
        
        Args:
            product_evaluation: 商品评估结果
            
        Returns:
            bool: 是否应该采集
        """
        try:
            # 根据规格要求，当商品利润率 >= 配置阈值时才采集跟卖店铺信息
            profit_rate = product_evaluation.get('profit_rate', 0)
            return profit_rate >= self.config.store_filter.profit_rate_threshold
            
        except Exception as e:
            self.logger.error(f"判断是否采集跟卖店铺信息失败: {e}")
            return False

    def get_product_filter_func(self):
        """
        获取商品过滤函数，用于过滤黑名单类目商品

        Returns:
            Callable: 商品过滤函数
        """
        def product_filter(product_data: Dict[str, Any]) -> bool:
            """
            过滤黑名单类目商品

            Args:
                product_data: 商品数据

            Returns:
                bool: True表示保留商品，False表示过滤掉商品
            """
            try:
                # 检查商品类目是否在黑名单中
                category_info = product_data.get('category_info', '')
                blacklisted_categories = self.config.store_filter.blacklisted_categories

                if category_info:
                    for blacklisted_cat in blacklisted_categories:
                        if blacklisted_cat in category_info:
                            product_id = product_data.get('product_id', '未知')
                            self.logger.info(f"过滤掉商品 {product_id}，原因：属于黑名单类目 '{blacklisted_cat}'，类目信息：{category_info}")
                            return False  # 过滤掉黑名单类目商品
                return True  # 保留其他商品
            except Exception as e:
                self.logger.error(f"商品过滤函数执行失败: {e}")
                return True  # 出错时默认保留商品

        return product_filter