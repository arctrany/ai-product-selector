"""
毛子ERP插件抓取器

负责从毛子ERP插件渲染区域抓取商品的结构化数据。
支持共享browser_service实例，便于独立测试。
"""

import asyncio
import logging
import time
import re
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from .base_scraper import BaseScraper
from .global_browser_singleton import get_global_browser_service
from common.models.scraping_result import ScrapingResult as ScrapingResultImport
from common.models.scraping_result import ScrapingResult
from common.utils.wait_utils import WaitUtils
from common.utils.scraping_utils import ScrapingUtils
from common.config.erp_selectors_config import ERPSelectorsConfig, get_erp_selectors_config
from ..interfaces.scraper_interface import IERPScraper, ScrapingMode, StandardScrapingOptions
from ..exceptions.scraping_exceptions import ScrapingException, NavigationException, DataExtractionException

class ErpPluginScraper(BaseScraper, IERPScraper):
    """
    毛子ERP插件抓取器 - 使用全局浏览器单例

    实现IERPScraper接口，提供标准化的ERP数据抓取功能
    """

    def __init__(self, selectors_config: Optional[ERPSelectorsConfig] = None, browser_service = None):
        """
        初始化ERP插件抓取器

        Args:
            selectors_config: ERP选择器配置对象
            browser_service: 可选的共享浏览器服务实例（向后兼容，推荐使用全局单例）
        """
        super().__init__()
        self.selectors_config = selectors_config or get_erp_selectors_config()
        # 为了兼容测试，添加config属性（指向selectors_config）
        self.config = self.selectors_config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 使用全局浏览器单例
        if browser_service:
            self.browser_service = browser_service
            self._owns_browser_service = False  # 不拥有浏览器服务，不负责关闭
        else:
            self.browser_service = get_global_browser_service()
            self._owns_browser_service = False  # 使用全局单例，不负责关闭
        
        # 🔧 重构：初始化统一工具类
        self.wait_utils = WaitUtils(self.browser_service, self.logger)
        self.scraping_utils = ScrapingUtils(self.logger)
        
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

    def scrape_erp_data(self,
                       product_url: str,
                       include_attributes: bool = True,
                       options: Optional[Dict[str, Any]] = None) -> ScrapingResult:
        """
        抓取ERP数据（标准接口实现）

        Args:
            product_url: 商品URL
            include_attributes: 是否包含商品属性
            options: 抓取选项

        Returns:
            ScrapingResult: ERP数据抓取结果

        Raises:
            NavigationException: 页面导航失败
            DataExtractionException: 数据提取失败
        """
        try:
            # 解析选项
            scraping_options = StandardScrapingOptions(**(options or {}))

            # 使用内部方法进行抓取
            return self._scrape_comprehensive(
                product_url=product_url,
                include_attributes=include_attributes,
                **scraping_options.to_dict()
            )

        except Exception as e:
            raise DataExtractionException(
                field_name="erp_data",
                message=f"ERP数据抓取失败: {str(e)}",
                context={'product_url': product_url, 'options': options},
                original_exception=e
            )

    # 标准scrape接口实现
    def scrape(self,
               target: Optional[str] = None,
               mode: Optional[ScrapingMode] = None,
               options: Optional[Dict[str, Any]] = None,
               **kwargs) -> ScrapingResult:
        """
        统一的抓取接口（标准接口实现）

        Args:
            target: 抓取目标（商品URL）
            mode: 抓取模式
            options: 抓取选项配置
            **kwargs: 额外参数

        Returns:
            ScrapingResult: 标准化抓取结果

        Raises:
            ScrapingException: 抓取异常
        """
        try:
            # 解析选项
            scraping_options = StandardScrapingOptions(**(options or {}))

            # 根据模式选择抓取策略
            if mode == ScrapingMode.ERP_DATA:
                return self.scrape_erp_data(
                    product_url=target,
                    include_attributes=kwargs.get('include_attributes', True),
                    options=options
                )
            elif mode == ScrapingMode.PRODUCT_ATTRIBUTES:
                return self.scrape_product_attributes(
                    product_url=target,
                    green_price=kwargs.get('green_price', None)
                )
            else:
                # 默认使用ERP数据抓取
                return self._scrape_comprehensive(
                    product_url=target,
                    include_attributes=kwargs.get('include_attributes', True),
                    **kwargs
                )

        except Exception as e:
            raise ScrapingException(
                message=f"抓取失败: {str(e)}",
                error_code="SCRAPING_FAILED",
                context={'target': target, 'mode': mode, 'options': options},
                original_exception=e
            )

    def _scrape_comprehensive(self,
                             product_url: Optional[str] = None,
                             include_attributes: bool = True,
                             **kwargs) -> ScrapingResult:
        """
        综合ERP数据抓取（内部方法，保持向后兼容）

        Args:
            product_url: 可选的商品URL，如果提供则导航到该页面，否则从当前页面抓取
            include_attributes: 是否包含商品属性
            **kwargs: 其他参数
            
        Returns:
            ScrapingResult: 抓取结果，包含结构化的ERP数据
        """
        start_time = time.time()

        try:
            if product_url:
                # 如果提供了URL，导航并抓取页面数据
                success = self.navigate_to(product_url)
                if not success:
                    raise Exception("页面导航失败")

                # 等待页面加载
                self.wait(1)

            # 智能等待ERP插件加载完成
            self._wait_for_erp_plugin_loaded()

            # 获取页面内容 - 使用同步方法
            page_content = self.browser_service.evaluate_sync("() => document.documentElement.outerHTML")

            if not page_content:
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message="未能获取当前页面内容",
                    execution_time=time.time() - start_time
                )

            # 解析ERP信息
            erp_data = self._extract_erp_data()

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

    def _extract_erp_data(self, *args, **kwargs) -> Dict[str, Any]:
        """
        提取ERP数据的入口方法（测试接口兼容性）

        Returns:
            Dict[str, Any]: 提取的ERP数据
        """
        try:
            # 获取页面内容
            page_content = self.browser_service.evaluate_sync("() => document.documentElement.outerHTML")
            if not page_content:
                return {}

            # 调用实际的提取方法
            return self._extract_erp_data_from_content(page_content)
        except Exception as e:
            self.logger.error(f"提取ERP数据失败: {e}")
            return {}

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
        from common.config.erp_selectors_config import get_erp_selectors_config

        # 使用配置化的选择器，而不是硬编码
        erp_config = get_erp_selectors_config()
        selectors = erp_config.erp_container_selectors
        
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
            label_elements = container.find_all(string=re.compile(f'{re.escape(label_text)}：?\\s*'))
            
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

    def _wait_for_erp_plugin_loaded(self, max_wait_seconds: int = 10) -> bool:
        """
        智能等待ERP插件加载完成

        Args:
            max_wait_seconds: 最大等待时间（秒）

        Returns:
            bool: 是否成功加载
        """
        start_time = time.time()
        check_interval = 0.5  # 每0.5秒检查一次

        while time.time() - start_time < max_wait_seconds:
            try:
                # 获取页面内容 - 使用同步方法
                page_content = self.browser_service.evaluate_sync("() => document.documentElement.outerHTML")
                if not page_content:
                    self.wait(check_interval)
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
                self.wait(check_interval)

            except Exception as e:
                self.logger.debug(f"检查ERP插件状态时出错: {e}")
                self.wait(check_interval)

        # 超时
        self.logger.warning(f"⚠️ ERP插件加载超时（{max_wait_seconds}秒），继续尝试抓取")
        return False

    def close(self):
        """关闭资源 - 使用全局单例时不需要关闭"""
        # 使用全局单例时不需要主动关闭浏览器服务
        # 全局单例的生命周期由应用程序管理
        pass

    def __enter__(self):
        return self

    def scrape_product_attributes(self, product_url: str, green_price: Optional[float] = None) -> ScrapingResult:
        """
        抓取商品属性信息

        Args:
            product_url: 商品页面URL
            green_price: 商品绿标价格（用于佣金率计算）

        Returns:
            ScrapingResult: 抓取结果，包含商品属性信息
        """
        start_time = time.time()

        try:
            # 导航到商品页面
            success = self.navigate_to(product_url)
            if not success:
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message="页面导航失败",
                    execution_time=time.time() - start_time
                )

            # 等待页面加载
            self.wait(1)

            # 智能等待ERP插件加载完成
            self._wait_for_erp_plugin_loaded()

            # 获取页面内容
            page_content = self.browser_service.evaluate_sync("() => document.documentElement.outerHTML")
            if not page_content:
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message="未能获取页面内容",
                    execution_time=time.time() - start_time
                )

            # 解析ERP数据
            erp_data = self._extract_erp_data_from_content(page_content)

            # 提取需要的属性信息
            attributes = {}

            # 佣金率
            if 'rfbs_commission_rates' in erp_data and erp_data['rfbs_commission_rates']:
                # 使用第一个佣金率作为默认值
                attributes['commission_rate'] = erp_data['rfbs_commission_rates'][0]
            elif green_price:
                # 如果没有佣金率但有绿标价格，可以根据价格计算默认佣金率
                attributes['commission_rate'] = self._calculate_commission_rate_by_price(green_price)
            else:
                # 使用默认佣金率
                attributes['commission_rate'] = 12.0  # 默认12%

            # 重量
            if 'weight' in erp_data and erp_data['weight']:
                attributes['weight'] = float(erp_data['weight'])

            # 尺寸信息
            if 'length' in erp_data and erp_data['length']:
                attributes['length'] = float(erp_data['length'])
            if 'width' in erp_data and erp_data['width']:
                attributes['width'] = float(erp_data['width'])
            if 'height' in erp_data and erp_data['height']:
                attributes['height'] = float(erp_data['height'])

            # 上架天数
            if 'shelf_days' in erp_data and erp_data['shelf_days']:
                attributes['shelf_days'] = int(erp_data['shelf_days'])

            return ScrapingResult(
                success=True,
                data=attributes,
                execution_time=time.time() - start_time
            )

        except Exception as e:
            self.logger.error(f"抓取商品属性失败: {e}")
            return ScrapingResult(
                success=False,
                data={},
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    def _calculate_commission_rate_by_price(self, price: float) -> float:
        """
        根据价格计算佣金率

        Args:
            price: 商品价格（卢布）

        Returns:
            float: 佣金率（百分比）
        """
        try:
            # 🔧 重构：使用硬编码阈值，符合架构分离原则
            if price <= 500:  # 低价商品阈值500卢布
                return 15.0  # 低价商品佣金率15%
            elif price >= 2000:  # 高价商品阈值2000卢布
                return 8.0   # 高价商品佣金率8%
            else:
                return 12.0  # 中等价格商品佣金率12%
        except Exception as e:
            self.logger.warning(f"计算佣金率失败，使用默认值: {e}")
            return 12.0

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ========== 抽象方法实现 ==========

    def extract_data(self,
                    selectors: Optional[Dict[str, str]] = None,
                    options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        从当前页面提取数据（抽象方法实现）

        Args:
            selectors: 选择器映射
            options: 提取选项

        Returns:
            Dict[str, Any]: 提取的数据
        """
        try:
            # 获取页面内容
            page_content = self.browser_service.evaluate_sync("() => document.documentElement.outerHTML")
            if not page_content:
                return {}

            # 使用现有的ERP数据提取逻辑
            erp_data = self._extract_erp_data_from_content(page_content)

            return erp_data

        except Exception as e:
            self.logger.error(f"数据提取失败: {e}")
            return {}

    def validate_data(self, data: Dict[str, Any],
                     filters: Optional[List[Callable]] = None) -> bool:
        """
        验证提取的数据（抽象方法实现）

        Args:
            data: 待验证的数据
            filters: 验证过滤器列表

        Returns:
            bool: 数据是否有效
        """
        try:
            # 基本验证：数据不为空
            if not data:
                return False

            # 验证ERP数据的关键字段
            erp_fields = ['category', 'sku', 'brand_name', 'monthly_sales_volume', 'monthly_sales_amount']
            has_valid_field = False

            for field in erp_fields:
                if field in data and data[field] is not None:
                    has_valid_field = True
                    break

            if not has_valid_field:
                self.logger.warning("没有找到有效的ERP数据字段")
                return False

            # 验证数值字段的合理性
            numeric_fields = ['monthly_sales_volume', 'monthly_sales_amount', 'daily_sales_volume', 'daily_sales_amount']
            for field in numeric_fields:
                if field in data:
                    try:
                        value = float(data[field]) if data[field] is not None else 0
                        if value < 0:
                            self.logger.warning(f"字段 {field} 值为负数: {value}")
                            return False
                    except (ValueError, TypeError):
                        self.logger.warning(f"字段 {field} 值无法转换为数字: {data[field]}")

            # 应用自定义过滤器
            if filters:
                for filter_func in filters:
                    if not filter_func(data):
                        return False

            return True

        except Exception as e:
            self.logger.error(f"数据验证失败: {e}")
            return False

    def get_health_status(self) -> Dict[str, Any]:
        """
        获取Scraper健康状态（抽象方法实现）

        Returns:
            Dict[str, Any]: 健康状态信息
        """
        try:
            status = {
                'scraper_name': 'ErpPluginScraper',
                'status': 'healthy',
                'browser_service_available': self.browser_service is not None,
                'selectors_config_loaded': self.selectors_config is not None,
                'field_mappings_count': len(self.field_mappings)
            }

            # 检查浏览器服务状态
            if self.browser_service:
                try:
                    # 简单检查浏览器是否响应
                    page_url = self.browser_service.evaluate_sync("() => window.location.href")
                    status['browser_responsive'] = page_url is not None
                    status['current_url'] = page_url

                    # 检查ERP插件是否存在
                    status['erp_plugin_detected'] = self._wait_for_erp_plugin_loaded(max_wait_seconds=1)
                except:
                    status['browser_responsive'] = False
                    status['status'] = 'degraded'
                    status['erp_plugin_detected'] = False
            else:
                status['status'] = 'unavailable'
                status['browser_responsive'] = False
                status['erp_plugin_detected'] = False

            return status

        except Exception as e:
            return {
                'scraper_name': 'ErpPluginScraper',
                'status': 'error',
                'error': str(e)
            }

    def wait_for_erp_plugin(self, timeout: int = 30) -> bool:
        """
        等待ERP插件加载完成（抽象方法实现）

        Args:
            timeout: 超时时间（秒）

        Returns:
            bool: 插件是否加载成功
        """
        try:
            return self._wait_for_erp_plugin_loaded(max_wait_seconds=timeout)
        except Exception as e:
            self.logger.error(f"等待ERP插件加载失败: {e}")
            return False
