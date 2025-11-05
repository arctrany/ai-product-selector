"""
货源匹配器

负责模拟1688货源匹配功能。
"""

import logging
import random
from typing import Optional, Dict, Any

from ..models import ProductInfo
from ..config import GoodStoreSelectorConfig, get_config


class SourceMatcher:
    """货源匹配器"""
    
    def __init__(self, config: Optional[GoodStoreSelectorConfig] = None):
        """
        初始化货源匹配器
        
        Args:
            config: 配置对象
        """
        self.config = config or get_config()
        self.logger = logging.getLogger(f"{__name__}.SourceMatcher")
    
    def match_source(self, product_info: ProductInfo) -> Dict[str, Any]:
        """
        匹配货源
        
        Args:
            product_info: 商品信息
            
        Returns:
            Dict[str, Any]: 匹配结果
        """
        try:
            # 模拟货源匹配过程
            match_result = self._simulate_source_matching(product_info)
            
            self.logger.debug(f"商品{product_info.product_id}货源匹配结果: {match_result}")
            return match_result
            
        except Exception as e:
            self.logger.error(f"货源匹配失败: {e}")
            return self._create_failed_match_result(str(e))
    
    def _simulate_source_matching(self, product_info: ProductInfo) -> Dict[str, Any]:
        """
        模拟货源匹配
        
        Args:
            product_info: 商品信息
            
        Returns:
            Dict[str, Any]: 模拟匹配结果
        """
        # 模拟匹配成功率（70%）
        is_matched = random.random() < 0.7
        
        if not is_matched:
            return {
                'success': False,
                'matched': False,
                'reason': '未找到匹配的货源',
                'source_price': None,
                'source_info': None
            }
        
        # 模拟生成采购价格
        # 通常采购价格是售价的30%-60%
        base_price = product_info.green_price or product_info.black_price or 100.0
        
        # 转换为人民币（如果是卢布）
        if product_info.green_price:
            base_price_cny = base_price * self.config.price_calculation.rub_to_cny_rate
        else:
            base_price_cny = base_price
        
        # 生成采购价格（30%-60%的售价）
        cost_ratio = random.uniform(0.3, 0.6)
        source_price = base_price_cny * cost_ratio
        
        # 模拟货源信息
        source_info = {
            'supplier_id': f"supplier_{random.randint(1000, 9999)}",
            'supplier_name': f"供应商{random.randint(1, 100)}",
            'location': random.choice(['广州', '深圳', '义乌', '杭州', '上海']),
            'min_order_quantity': random.choice([1, 5, 10, 20, 50]),
            'delivery_time': random.choice(['1-3天', '3-7天', '7-15天']),
            'quality_score': random.uniform(4.0, 5.0),
            'price_trend': random.choice(['stable', 'rising', 'falling'])
        }
        
        return {
            'success': True,
            'matched': True,
            'source_price': round(source_price, 2),
            'source_info': source_info,
            'cost_ratio': round(cost_ratio * 100, 1),
            'match_confidence': random.uniform(0.7, 0.95)
        }
    
    def _create_failed_match_result(self, error_message: str) -> Dict[str, Any]:
        """
        创建失败的匹配结果
        
        Args:
            error_message: 错误信息
            
        Returns:
            Dict[str, Any]: 失败结果
        """
        return {
            'success': False,
            'matched': False,
            'reason': f'匹配过程出错: {error_message}',
            'source_price': None,
            'source_info': None,
            'error': error_message
        }
    
    def batch_match_sources(self, products: list[ProductInfo]) -> Dict[str, Dict[str, Any]]:
        """
        批量匹配货源
        
        Args:
            products: 商品列表
            
        Returns:
            Dict[str, Dict[str, Any]]: 匹配结果字典，key为product_id
        """
        results = {}
        
        for product in products:
            try:
                result = self.match_source(product)
                results[product.product_id] = result
                
            except Exception as e:
                self.logger.error(f"批量匹配商品{product.product_id}货源失败: {e}")
                results[product.product_id] = self._create_failed_match_result(str(e))
        
        # 统计匹配结果
        total_products = len(products)
        matched_products = len([r for r in results.values() if r.get('matched', False)])
        match_rate = (matched_products / total_products * 100) if total_products > 0 else 0
        
        self.logger.info(f"批量货源匹配完成: {matched_products}/{total_products} ({match_rate:.1f}%)")
        
        return results
    
    def get_source_prices(self, match_results: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """
        提取货源价格
        
        Args:
            match_results: 匹配结果字典
            
        Returns:
            Dict[str, float]: 货源价格字典，key为product_id
        """
        source_prices = {}
        
        for product_id, result in match_results.items():
            if result.get('matched', False) and result.get('source_price'):
                source_prices[product_id] = result['source_price']
        
        self.logger.debug(f"提取到{len(source_prices)}个商品的货源价格")
        return source_prices
    
    def get_match_statistics(self, match_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取匹配统计信息
        
        Args:
            match_results: 匹配结果字典
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            total_products = len(match_results)
            matched_products = len([r for r in match_results.values() if r.get('matched', False)])
            failed_products = len([r for r in match_results.values() if not r.get('success', True)])
            
            # 计算平均采购价格
            source_prices = [r.get('source_price', 0) for r in match_results.values() if r.get('source_price')]
            avg_source_price = sum(source_prices) / len(source_prices) if source_prices else 0
            
            # 计算平均成本比例
            cost_ratios = [r.get('cost_ratio', 0) for r in match_results.values() if r.get('cost_ratio')]
            avg_cost_ratio = sum(cost_ratios) / len(cost_ratios) if cost_ratios else 0
            
            # 计算平均匹配置信度
            confidences = [r.get('match_confidence', 0) for r in match_results.values() if r.get('match_confidence')]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                'total_products': total_products,
                'matched_products': matched_products,
                'failed_products': failed_products,
                'match_rate': (matched_products / total_products * 100) if total_products > 0 else 0,
                'avg_source_price': round(avg_source_price, 2),
                'avg_cost_ratio': round(avg_cost_ratio, 1),
                'avg_confidence': round(avg_confidence, 3),
                'price_range': {
                    'min': min(source_prices) if source_prices else 0,
                    'max': max(source_prices) if source_prices else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"获取匹配统计信息失败: {e}")
            return {'error': str(e)}
    
    def validate_source_price(self, source_price: float, selling_price: float) -> bool:
        """
        验证货源价格的合理性
        
        Args:
            source_price: 货源价格
            selling_price: 销售价格
            
        Returns:
            bool: 价格是否合理
        """
        try:
            if source_price <= 0 or selling_price <= 0:
                return False
            
            # 采购价格不应该超过销售价格的80%
            cost_ratio = source_price / selling_price
            if cost_ratio > 0.8:
                self.logger.warning(f"货源价格过高: {source_price}/{selling_price} = {cost_ratio:.2f}")
                return False
            
            # 采购价格不应该低于销售价格的10%（可能是异常数据）
            if cost_ratio < 0.1:
                self.logger.warning(f"货源价格过低: {source_price}/{selling_price} = {cost_ratio:.2f}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"验证货源价格失败: {e}")
            return False