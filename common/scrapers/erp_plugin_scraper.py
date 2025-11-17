"""
毛子ERP插件抓取器

负责从毛子ERP插件渲染区域抓取商品的结构化数据。
支持共享browser_service实例，便于独立测试。
"""

import asyncio
import logging
import time
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from .xuanping_browser_service import XuanpingBrowserServiceSync
from ..models import ProductInfo, ScrapingResult
from ..config import GoodStoreSelectorConfig

class ErpPluginScraper:
    """毛子ERP插件抓取器 - 支持共享browser_service实例"""
    
    def __init__(self, config: Optional[GoodStoreSelectorConfig] = None, browser_service: Optional[XuanpingBrowserServiceSync] = None):
        """
        初始化ERP插件抓取器
        
        Args:
            config: 配置对象
            browser_service: 可选的共享浏览器服务实例
        """
        self.config = config or GoodStoreSelectorConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 支持共享browser_service实例
        if browser_service:
            self.browser_service = browser_service
            self._owns_browser_service = False  # 不拥有浏览器服务，不负责关闭
        else:
            self.browser_service = XuanpingBrowserServiceSync()
            self._owns_browser_service = True  # 拥有浏览器服务，负责关闭
        
        # ERP区域数据字段映射
        self.field_mappings = {
            '类目': 'category',
            'rFBS佣金': 'rfbs_commission',
            'SKU': 'sku',
            '品牌': 'brand_name',
            '月销量': 'monthly_sales_volume',
            '月销售额': 'monthly_sales_amount',
            '月周转动态': 'monthly_turnover_trend',
            '日销量': 'daily_sales_volume',
            '日销售额': 'daily_sales_amount',
            '广告费占比': 'ad_cost_ratio',
            '参与促销天数': 'promotion_days',
            '参与促销的折扣': 'promotion_discount',
            '促销活动的转化率': 'promotion_conversion_rate',
            '付费推广天数': 'paid_promotion_days',
            '商品卡浏览量': 'product_card_views',
            '商品卡加购率': 'product_card_add_rate',
            '搜索目录浏览量': 'search_catalog_views',
            '搜索目录加购率': 'search_catalog_add_rate',
            '展示转化率': 'display_conversion_rate',
            '商品点击率': 'product_click_rate',
            '发货模式': 'shipping_mode',
            '退货取消率': 'return_cancel_rate',
            '长 宽 高': 'dimensions',
            '重 量': 'weight',
            '上架时间': 'listing_date',
            '跟卖列表': 'competitor_list',
            '跟卖最低价': 'competitor_min_price',
            '跟卖最高价': 'competitor_max_price'
        }

    def scrape(self, product_url: Optional[str] = None) -> ScrapingResult:
        """
        抓取ERP区域的结构化数据
        
        Args:
            product_url: 可选的商品URL，如果提供则导航到该页面，否则从当前页面抓取
            
        Returns:
            ScrapingResult: 抓取结果，包含结构化的ERP数据
        """
        start_time = time.time()

        try:
            if product_url:
                # 如果提供了URL，使用浏览器服务抓取页面数据
                async def extract_erp_data(browser_service):
                    """异步提取ERP数据"""
                    try:
                        # 智能等待ERP插件加载完成
                        await self._wait_for_erp_plugin_loaded(browser_service)

                        # 获取页面内容
                        page_content = await browser_service.get_page_content()
                        
                        # 解析ERP信息
                        erp_data = self._extract_erp_data_from_content(page_content)
                        
                        return erp_data
                        
                    except Exception as e:
                        self.logger.error(f"提取ERP数据失败: {e}")
                        return {}
                
                # 使用浏览器服务抓取页面数据
                result = self.browser_service.scrape_page_data(product_url, extract_erp_data)
                
                if result.success:
                    return ScrapingResult(
                        success=True,
                        data=result.data,
                        execution_time=time.time() - start_time
                    )
                else:
                    return ScrapingResult(
                        success=False,
                        data={},
                        error_message=result.error_message or "未能提取到ERP信息",
                        execution_time=time.time() - start_time
                    )
            else:
                # 从当前页面直接抓取
                async def get_current_page_content():
                    # 智能等待ERP插件加载完成
                    await self._wait_for_erp_plugin_loaded(self.browser_service)
                    return await self.browser_service.get_page_content()
                
                # 获取当前页面内容
                page_content = asyncio.run(get_current_page_content())
                
                if not page_content:
                    return ScrapingResult(
                        success=False,
                        data={},
                        error_message="未能获取当前页面内容",
                        execution_time=time.time() - start_time
                    )
                
                # 解析ERP信息
                erp_data = self._extract_erp_data_from_content(page_content)
                
                return ScrapingResult(
                    success=True,
                    data=erp_data,
                    execution_time=time.time() - start_time
                )
            
        except Exception as e:
            self.logger.error(f"抓取ERP信息失败: {e}")
            return ScrapingResult(
                success=False,
                data={},
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    def _extract_erp_data_from_content(self, page_content: str) -> Dict[str, Any]:
        """
        从页面内容中提取ERP数据
        
        Args:
            page_content: 页面HTML内容
            
        Returns:
            Dict[str, Any]: 提取的ERP数据
        """
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_content, 'html.parser')
            
            erp_data = {}
            
            # 查找ERP插件区域
            erp_container = self._find_erp_container(soup)
            if not erp_container:
                self.logger.warning("未找到ERP插件区域")
                return {}
            
            # 提取所有数据字段
            for label_text, field_key in self.field_mappings.items():
                value = self._extract_field_value(erp_container, label_text)
                if value is not None:
                    erp_data[field_key] = value
            
            # 特殊处理：解析尺寸信息
            if 'dimensions' in erp_data:
                dimensions = self._parse_dimensions(erp_data['dimensions'])
                erp_data.update(dimensions)
            
            # 特殊处理：解析上架时间
            if 'listing_date' in erp_data:
                parsed_date = self._parse_listing_date(erp_data['listing_date'])
                erp_data.update(parsed_date)
            
            # 特殊处理：解析重量
            if 'weight' in erp_data:
                weight_value = self._parse_weight(erp_data['weight'])
                if weight_value is not None:
                    erp_data['weight'] = weight_value
            
            # 特殊处理：解析rFBS佣金
            if 'rfbs_commission' in erp_data:
                commission_rates = self._parse_rfbs_commission(erp_data['rfbs_commission'])
                erp_data['rfbs_commission_rates'] = commission_rates
            
            return erp_data
            
        except Exception as e:
            self.logger.error(f"解析ERP数据失败: {e}")
            return {}

    def _find_erp_container(self, soup) -> Optional[Any]:
        """查找ERP插件容器"""
        # 尝试多种选择器查找ERP区域
        selectors = [
            '[data-v-efec3aa9]',  # 从HTML中观察到的特征属性
            '.erp-plugin',
            '[class*="erp"]',
            '[id*="erp"]'
        ]
        
        for selector in selectors:
            container = soup.select_one(selector)
            if container:
                return container
        
        return None

    def _extract_field_value(self, container: Any, label_text: str) -> Optional[str]:
        """
        从容器中提取指定标签的值
        
        Args:
            container: BeautifulSoup容器对象
            label_text: 标签文本
            
        Returns:
            Optional[str]: 提取的值，如果未找到返回None
        """
        try:
            # 查找包含标签文本的元素
            label_elements = container.find_all(text=re.compile(f'{re.escape(label_text)}：?\\s*'))
            
            for label_element in label_elements:
                # 获取父元素
                parent = label_element.parent
                if not parent:
                    continue
                
                # 查找同级或子级的值元素
                value_element = None
                
                # 方法1：查找同级span元素
                next_span = parent.find_next_sibling('span')
                if next_span:
                    value_element = next_span
                
                # 方法2：查找父元素内的其他span
                if not value_element:
                    spans = parent.find_all('span')
                    for span in spans:
                        if span.get_text(strip=True) != label_text.rstrip('：'):
                            value_element = span
                            break
                
                # 方法3：查找父元素的下一个div中的span
                if not value_element:
                    parent_div = parent.find_parent('div')
                    if parent_div:
                        next_div = parent_div.find_next_sibling('div')
                        if next_div:
                            value_span = next_div.find('span')
                            if value_span:
                                value_element = value_span
                
                if value_element:
                    value_text = value_element.get_text(strip=True)
                    # 过滤无效值
                    if value_text and value_text not in ['-', '无数据', 'N/A', '']:
                        return value_text
            
            return None
            
        except Exception as e:
            self.logger.error(f"提取字段 {label_text} 失败: {e}")
            return None

    def _parse_dimensions(self, dimensions_str: str) -> Dict[str, Optional[float]]:
        """
        解析尺寸字符串
        
        Args:
            dimensions_str: 尺寸字符串，如 "50 x 37 x 43mm"
            
        Returns:
            Dict[str, Optional[float]]: 包含length, width, height的字典
        """
        result = {'length': None, 'width': None, 'height': None}
        
        try:
            if not dimensions_str:
                return result
            
            # 移除单位并分割
            clean_str = re.sub(r'[a-zA-Z]+$', '', dimensions_str.strip())
            parts = re.split(r'\s*[x×]\s*', clean_str)
            
            if len(parts) >= 3:
                result['length'] = float(parts[0])
                result['width'] = float(parts[1])
                result['height'] = float(parts[2])
            
        except (ValueError, IndexError) as e:
            self.logger.warning(f"解析尺寸失败: {dimensions_str}, 错误: {e}")
        
        return result

    def _parse_listing_date(self, date_str: str) -> Dict[str, Optional[Any]]:
        """
        解析上架时间
        
        Args:
            date_str: 时间字符串，如 "2024-09-23(415天)"
            
        Returns:
            Dict[str, Optional[Any]]: 包含listing_date_parsed和shelf_days的字典
        """
        result = {'listing_date_parsed': None, 'shelf_days': None}

        try:
            if not date_str:
                return result

            # 提取日期部分
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
            if date_match:
                date_part = date_match.group(1)
                result['listing_date_parsed'] = date_part  # 直接返回字符串而不是date对象
            
            # 提取天数部分
            days_match = re.search(r'\((\d+)天\)', date_str)
            if days_match:
                result['shelf_days'] = int(days_match.group(1))
            
        except (ValueError, AttributeError) as e:
            self.logger.warning(f"解析上架时间失败: {date_str}, 错误: {e}")
        
        return result

    def _parse_weight(self, weight_str: str) -> Optional[float]:
        """
        解析重量字符串
        
        Args:
            weight_str: 重量字符串，如 "40g"
            
        Returns:
            Optional[float]: 重量值（克），失败返回None
        """
        try:
            if not weight_str:
                return None
            
            # 提取数字部分
            weight_match = re.search(r'(\d+(?:\.\d+)?)', weight_str)
            if weight_match:
                return float(weight_match.group(1))
            
        except (ValueError, AttributeError) as e:
            self.logger.warning(f"解析重量失败: {weight_str}, 错误: {e}")
        
        return None

    def _parse_rfbs_commission(self, commission_str: str) -> Optional[List[float]]:
        """
        解析rFBS佣金字符串

        Args:
            commission_str: 佣金字符串

        Returns:
            Optional[List[float]]: 佣金率列表，如果无法提取则返回None
        """
        try:
            if not commission_str:
                return None

            # 尝试从字符串中提取数字
            rates = re.findall(r'(\d+(?:\.\d+)?)%?', commission_str)
            if rates:
                return [float(rate) for rate in rates]

            # 如果无法提取到数字，返回None而不是默认值
            return None

        except Exception as e:
            self.logger.warning(f"解析佣金率失败: {commission_str}, 错误: {e}")
            return None

    async def _wait_for_erp_plugin_loaded(self, browser_service, max_wait_seconds: int = 10) -> bool:
        """
        智能等待ERP插件加载完成

        Args:
            browser_service: 浏览器服务实例
            max_wait_seconds: 最大等待时间（秒）

        Returns:
            bool: 是否成功加载
        """
        start_time = time.time()
        check_interval = 0.5  # 每0.5秒检查一次

        while time.time() - start_time < max_wait_seconds:
            try:
                # 获取页面内容
                page_content = await browser_service.get_page_content()
                if not page_content:
                    await asyncio.sleep(check_interval)
                    continue

                # 检查ERP插件区域是否存在
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(page_content, 'html.parser')

                # 使用多种选择器检查ERP区域
                erp_selectors = [
                    '[data-v-efec3aa9]',  # 从HTML中观察到的特征属性
                    '.erp-plugin',
                    '[class*="erp"]',
                    '[id*="erp"]'
                ]

                for selector in erp_selectors:
                    erp_elements = soup.select(selector)
                    if erp_elements:
                        # 检查是否有实际的数据内容（不只是空的容器）
                        for element in erp_elements:
                            text_content = element.get_text(strip=True)
                            if text_content and len(text_content) > 50:  # 有足够的文本内容
                                self.logger.info(f"✅ ERP插件加载完成，耗时: {time.time() - start_time:.2f}秒")
                                return True

                # 如果没找到，继续等待
                await asyncio.sleep(check_interval)

            except Exception as e:
                self.logger.debug(f"检查ERP插件状态时出错: {e}")
                await asyncio.sleep(check_interval)

        # 超时
        self.logger.warning(f"⚠️ ERP插件加载超时（{max_wait_seconds}秒），继续尝试抓取")
        return False

    def close(self):
        """关闭资源"""
        if self._owns_browser_service and self.browser_service:
            self.browser_service.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
