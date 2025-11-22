"""
过滤器管理模块

提供店铺和商品的过滤功能，明确区分不同的数据字段
"""

from typing import Dict, Any, Optional, Callable
import re
import logging


class FilterManager:
    """
    过滤器管理类
    
    提供店铺级别和商品级别的过滤功能，明确区分不同的数据字段：
    
    店铺级别字段：
    - store_sales_30days: 店铺30天销售额（卢布）
    - store_orders_30days: 店铺30天订单量
    
    商品级别字段：
    - product_sales_volume: 商品销量
    - product_category_cn: 商品中文类目
    - product_category_ru: 商品俄文类目
    - product_shelf_duration: 商品货架时长
    - product_weight: 商品重量（克）
    """
    
    def __init__(self, config):
        """
        初始化过滤器管理器
        
        Args:
            config: 配置对象（GoodStoreSelectorConfig）
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.UnifiedFilter")

        # 从系统配置读取类目黑名单
        self.blacklisted_categories = getattr(
            config.selector_filter,
            'item_category_blacklist',
            []
        )

    def filter_store(self, store_data: Dict[str, Any]) -> bool:
        """
        店铺级别过滤函数
        
        Args:
            store_data: 店铺数据，包含：
                - store_sales_30days: 店铺30天销售额（卢布）
                - store_orders_30days: 店铺30天订单量
                
        Returns:
            bool: True 表示通过过滤，False 表示被过滤掉
        """
        try:
            # 提取店铺销售数据（使用明确的字段名避免冲突）
            store_sales_30days = store_data.get('store_sales_30days', 0)
            store_orders_30days = store_data.get('store_orders_30days', 0)
            store_id = store_data.get('store_id', '未知')

            # 检测是否为 dryrun 模式
            is_dryrun = getattr(self.config, 'dryrun', False)

            # 执行过滤条件检查
            failed_conditions = []
            passed_conditions = []

            # 检查销售额条件
            sales_threshold = self.config.selector_filter.store_min_sales_30days
            if store_sales_30days < sales_threshold:
                failed_conditions.append(
                    f"销售额: {store_sales_30days:,.0f}₽ < {sales_threshold:,.0f}₽ (阈值)"
                )
            else:
                passed_conditions.append(
                    f"销售额: {store_sales_30days:,.0f}₽ >= {sales_threshold:,.0f}₽ (阈值)"
                )

            # 检查订单量条件
            orders_threshold = self.config.selector_filter.store_min_orders_30days
            if store_orders_30days < orders_threshold:
                failed_conditions.append(
                    f"订单量: {store_orders_30days} < {orders_threshold} (阈值)"
                )
            else:
                passed_conditions.append(
                    f"订单量: {store_orders_30days} >= {orders_threshold} (阈值)"
                )

            # 判断最终结果
            would_be_filtered = len(failed_conditions) > 0

            # Dryrun 模式：输出详细报告但不实际过滤
            if is_dryrun:
                self.logger.info(f"🧪 [DRYRUN] 店铺过滤报告")
                self.logger.info(f"  店铺ID: {store_id}")

                for condition in passed_conditions:
                    self.logger.info(f"  ✅ {condition}")

                for condition in failed_conditions:
                    self.logger.info(f"  ❌ {condition}")

                if would_be_filtered:
                    self.logger.info(f"  总体结果: FILTERED (会被过滤)")
                    self.logger.info(f"  原因: {'; '.join(failed_conditions)}")
                else:
                    self.logger.info(f"  总体结果: PASS (通过过滤)")

                # Dryrun 模式下始终返回 True（不实际过滤）
                return True

            # 正常模式：实际执行过滤
            if would_be_filtered:
                self.logger.info(
                    f"店铺{store_id}不符合筛选条件: {'; '.join(failed_conditions)}"
                )
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"店铺过滤失败: {e}")
            return False
    
    def filter_product(self, product_data: Dict[str, Any]) -> bool:
        """
        商品级别过滤函数
        
        Args:
            product_data: 商品数据，包含：
                - product_category_cn: 商品中文类目
                - product_category_ru: 商品俄文类目
                - product_listing_date: 商品上架日期
                - product_shelf_duration: 商品货架时长文本（如 "4 个月"）
                - product_sales_volume: 商品销量
                - product_weight: 商品重量（克）
                
        Returns:
            bool: True 表示通过过滤，False 表示被过滤掉
        """
        try:
            # 检查是否有用户配置
            if not hasattr(self.config, 'ui_config') or not self.config.ui_config:
                # 没有用户配置，默认通过
                return True
            
            ui_config = self.config.ui_config
            
            # 检测是否为 dryrun 模式
            is_dryrun = getattr(self.config, 'dryrun', False)

            # 执行过滤条件检查
            failed_conditions = []
            passed_conditions = []
            product_id = product_data.get('product_id', product_data.get('product_index', '未知'))

            # 1. 类目黑名单过滤（从系统配置读取）
            if self.blacklisted_categories:
                product_category_cn = product_data.get('product_category_cn', '')
                product_category_ru = product_data.get('product_category_ru', '')

                blacklist_matched = False
                matched_keyword = None

                for blacklist_keyword in self.blacklisted_categories:
                    if blacklist_keyword:
                        # 检查中文或俄文类目是否包含黑名单关键词
                        if (product_category_cn and blacklist_keyword in product_category_cn) or \
                           (product_category_ru and blacklist_keyword in product_category_ru):
                            blacklist_matched = True
                            matched_keyword = blacklist_keyword
                            break

                if blacklist_matched:
                    failed_conditions.append(
                        f"类目黑名单: '{matched_keyword}' 在 [{product_category_cn}, {product_category_ru}]"
                    )
                else:
                    passed_conditions.append(
                        f"类目黑名单: 不在黑名单 [{product_category_cn}, {product_category_ru}]"
                    )

            # 2. 上架时间过滤（shelf_duration）
            if ui_config.item_shelf_days > 0:
                product_shelf_duration = product_data.get('product_shelf_duration', '')
                if product_shelf_duration:
                    # 解析货架时长（如 "4 个月" 或 "< 1 个月"）
                    days = self._parse_shelf_duration(product_shelf_duration)

                    # 如果超过阈值，过滤掉
                    if days > ui_config.item_shelf_days:
                        failed_conditions.append(
                            f"上架时间: {days}天 > {ui_config.item_shelf_days}天 (阈值)"
                        )
                    else:
                        passed_conditions.append(
                            f"上架时间: {days}天 <= {ui_config.item_shelf_days}天 (阈值)"
                        )

            # 3. 销量范围过滤
            product_sales_volume = product_data.get('product_sales_volume')
            if product_sales_volume is not None:
                # 最小销量过滤
                if ui_config.monthly_sold_min > 0:
                    if product_sales_volume < ui_config.monthly_sold_min:
                        failed_conditions.append(
                            f"销量: {product_sales_volume} < {ui_config.monthly_sold_min} (最小阈值)"
                        )
                    else:
                        passed_conditions.append(
                            f"销量: {product_sales_volume} >= {ui_config.monthly_sold_min} (最小阈值)"
                        )

                # 最大销量过滤（0表示不限制）
                if ui_config.max_monthly_sold > 0:
                    if product_sales_volume > ui_config.max_monthly_sold:
                        failed_conditions.append(
                            f"销量: {product_sales_volume} > {ui_config.max_monthly_sold} (最大阈值)"
                        )
                    else:
                        passed_conditions.append(
                            f"销量: {product_sales_volume} <= {ui_config.max_monthly_sold} (最大阈值)"
                        )

            # 4. 重量范围过滤
            product_weight = product_data.get('product_weight')
            if product_weight is not None:
                # 最小重量过滤
                if ui_config.item_min_weight > 0:
                    if product_weight < ui_config.item_min_weight:
                        failed_conditions.append(
                            f"重量: {product_weight}g < {ui_config.item_min_weight}g (最小阈值)"
                        )
                    else:
                        passed_conditions.append(
                            f"重量: {product_weight}g >= {ui_config.item_min_weight}g (最小阈值)"
                        )

                # 最大重量过滤
                if ui_config.item_max_weight > 0:
                    if product_weight > ui_config.item_max_weight:
                        failed_conditions.append(
                            f"重量: {product_weight}g > {ui_config.item_max_weight}g (最大阈值)"
                        )
                    else:
                        passed_conditions.append(
                            f"重量: {product_weight}g <= {ui_config.item_max_weight}g (最大阈值)"
                        )

            # 判断最终结果
            would_be_filtered = len(failed_conditions) > 0

            # Dryrun 模式：输出详细报告但不实际过滤
            if is_dryrun:
                self.logger.info(f"🧪 [DRYRUN] 商品过滤报告")
                self.logger.info(f"  商品: {product_id}")

                for condition in passed_conditions:
                    self.logger.info(f"  ✅ {condition}")

                for condition in failed_conditions:
                    self.logger.info(f"  ❌ {condition}")

                if would_be_filtered:
                    self.logger.info(f"  总体结果: FILTERED (会被过滤)")
                    self.logger.info(f"  原因: {failed_conditions[0]}")  # 显示第一个失败原因
                else:
                    self.logger.info(f"  总体结果: PASS (通过过滤)")

                # Dryrun 模式下始终返回 True（不实际过滤）
                return True

            # 正常模式：实际执行过滤
            if would_be_filtered:
                self.logger.debug(
                    f"商品{product_id}被过滤: {failed_conditions[0]}"
                )
                return False
            
            # 所有条件都通过
            return True
            
        except Exception as e:
            self.logger.error(f"商品过滤失败: {e}")
            return True  # 出错时默认保留商品
    
    def _parse_shelf_duration(self, shelf_duration: str) -> int:
        """
        解析货架时长文本为天数
        
        Args:
            shelf_duration: 货架时长文本（如 "4 个月" 或 "< 1 个月"）
            
        Returns:
            int: 天数
        """
        try:
            # "< 1 个月" 表示不到1个月，约30天
            if '< 1' in shelf_duration or '<1' in shelf_duration:
                return 30
            
            # 提取月数并转换为天数
            if '个月' in shelf_duration or 'месяц' in shelf_duration:
                month_match = re.search(r'(\d+)', shelf_duration)
                if month_match:
                    months = int(month_match.group(1))
                    return months * 30  # 简化：1个月=30天
            
            return 0
            
        except Exception as e:
            self.logger.error(f"解析货架时长失败: {e}")
            return 0
    
    def get_store_filter_func(self) -> Callable[[Dict[str, Any]], bool]:
        """
        获取店铺过滤函数（用于传递给抓取器）
        
        Returns:
            Callable: 店铺过滤函数
        """
        return self.filter_store
    
    def get_product_filter_func(self) -> Callable[[Dict[str, Any]], bool]:
        """
        获取商品过滤函数（用于传递给抓取器）
        
        Returns:
            Callable: 商品过滤函数
        """
        return self.filter_product
