"""
OZON平台抓取器

负责从OZON平台抓取商品价格信息和跟卖店铺数据。
基于新的browser_service架构。

重构版本：集成CompetitorDetectionService，使用统一工具类
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Tuple

from .base_scraper import BaseScraper
from .global_browser_singleton import get_global_browser_service

from ..models import CompetitorStore, clean_price_string, ScrapingResult
from ..config import GoodStoreSelectorConfig
from ..config.ozon_selectors_config import get_ozon_selectors_config, OzonSelectorsConfig
from ..config.currency_config import get_currency_config
# 延迟导入避免循环依赖
def get_profit_evaluator():
    from business.profit_evaluator import ProfitEvaluator
    return ProfitEvaluator

def get_erp_plugin_scraper():
    from .erp_plugin_scraper import ErpPluginScraper
    return ErpPluginScraper
from ..services.competitor_detection_service import CompetitorDetectionService
from ..utils.wait_utils import WaitUtils
from ..utils.scraping_utils import ScrapingUtils
from ..interfaces.scraper_interface import IProductScraper, ScrapingMode, StandardScrapingOptions
from ..exceptions.scraping_exceptions import ScrapingException, NavigationException, DataExtractionException


class OzonScraper(BaseScraper, IProductScraper):
    """
    OZON平台抓取器 - 基于browser_service架构

    实现IProductScraper接口，提供标准化的商品信息抓取功能
    """

    def __init__(self, config: Optional[GoodStoreSelectorConfig] = None,
                 selectors_config: Optional[OzonSelectorsConfig] = None):
        """初始化OZON抓取器"""
        super().__init__()
        self.config = config or GoodStoreSelectorConfig()
        self.selectors_config = selectors_config or get_ozon_selectors_config()
        self.currency_config = get_currency_config()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.base_url = self.config.scraping.ozon_base_url

        # 🔧 性能优化：使用共享的全局浏览器服务，避免重复创建
        self.browser_service = get_global_browser_service()

        # 🔧 重构：集成统一工具类
        self.wait_utils = WaitUtils(self.browser_service, self.logger)
        self.scraping_utils = ScrapingUtils(self.logger)
        


        # 延迟导入避免循环依赖
        ProfitEvaluator = get_profit_evaluator()
        ErpPluginScraper = get_erp_plugin_scraper()

        # 创建利润评估器
        self.profit_evaluator = ProfitEvaluator(
            profit_calculator_path=self.config.excel.profit_calculator_path,
            config=self.config
        )

        # 初始化ERP插件抓取器（共享browser_service实例）
        self.erp_scraper = ErpPluginScraper(self.config, self.browser_service)
        
        # 🔧 重构：初始化统一工具类
        self.wait_utils = WaitUtils(self.browser_service, self.logger)
        self.scraping_utils = ScrapingUtils(self.logger)

    def scrape_product_info(self,
                           product_url: str,
                           include_prices: bool = True,
                           include_reviews: bool = False,
                           options: Optional[Dict[str, Any]] = None) -> ScrapingResult:
        """
        抓取商品基本信息（标准接口实现）

        Args:
            product_url: 商品URL
            include_prices: 是否包含价格信息
            include_reviews: 是否包含评价信息
            options: 抓取选项

        Returns:
            ScrapingResult: 商品信息抓取结果

        Raises:
            NavigationException: 页面导航失败
            DataExtractionException: 数据提取失败
        """
        try:
            # 解析选项
            scraping_options = StandardScrapingOptions(**(options or {}))

            # 如果只需要价格信息，使用优化的价格抓取方法
            if include_prices and not include_reviews:
                return self.scrape_product_prices(product_url)

            # 完整的商品信息抓取（纯商品信息）
            return self._scrape_comprehensive(
                product_url=product_url,
                **scraping_options.to_dict()
            )

        except Exception as e:
            raise DataExtractionException(
                field_name="product_info",
                message=f"商品信息抓取失败: {str(e)}",
                context={'product_url': product_url, 'options': options},
                original_exception=e
            )

    def scrape_product_prices(self, product_url: str) -> ScrapingResult:
        """
        抓取商品价格信息（兼容方法）

        Args:
            product_url: 商品URL

        Returns:
            ScrapingResult: 抓取结果，包含价格信息

        Raises:
            NavigationException: 页面导航失败
            DataExtractionException: 数据提取失败
        """
        start_time = time.time()

        try:
            # 使用浏览器服务抓取数据
            def extract_price_data(browser_service):
                """同步提取价格数据"""
                try:
                    # 🔧 性能优化：减少不必要的等待时间
                    self.wait_utils.smart_wait(0.5)

                    # 获取页面内容 - 使用同步方法
                    page_content = browser_service.evaluate_sync("() => document.documentElement.outerHTML")
                    if not page_content:
                        self.logger.error("未能获取页面内容")
                        return {}

                    # 解析价格信息 - 直接调用核心方法
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(page_content, 'html.parser')
                    price_data = self._extract_price_data_core(soup)

                    # 保存价格数据供ERP抓取使用
                    self._last_price_data = price_data

                    return price_data

                except Exception as e:
                    self.logger.error(f"提取价格数据失败: {e}")
                    return {}

            # 使用继承的抓取方法
            result = self.scrape_page_data(product_url, extract_price_data)

            if result.success and result.data:
                return ScrapingResult(
                    success=True,
                    data=result.data,
                    execution_time=time.time() - start_time
                )
            else:
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message=result.error_message or "未能提取到价格信息",
                    execution_time=time.time() - start_time
                )

        except Exception as e:
            self.logger.error(f"抓取商品价格失败: {e}")
            return ScrapingResult(
                success=False,
                data={},
                error_message=str(e),
                execution_time=time.time() - start_time
            )



    # 标准scrape接口实现
    def scrape(self,
               target: str,
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
            if mode == ScrapingMode.PRODUCT_DATA:
                return self.scrape_product_info(
                    product_url=target,
                    include_prices=True,
                    include_reviews=False,
                    options=options
                )
            else:
                # 默认使用综合抓取方法（纯商品信息）
                return self._scrape_comprehensive(
                    product_url=target,
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
                             product_url: str,
                             **kwargs) -> ScrapingResult:
        """
        综合抓取商品信息（内部方法，保持向后兼容）

        重构版本：专注于纯商品信息抓取，跟卖功能委托给专门的服务处理

        Args:
            product_url: 商品URL
            **kwargs: 其他参数

        Returns:
            ScrapingResult: 抓取结果，包含商品基本信息和ERP数据
        """
        start_time = time.time()

        try:

            # 抓取价格信息
            price_result = self.scrape_product_prices(product_url)
            if not price_result.success:
                return price_result

            # 🆔 提取商品 ID
            product_id = self._extract_product_id(product_url)
            if product_id:
                self.logger.info(f"✅ 提取到商品ID: {product_id}")
            else:
                self.logger.warning(f"⚠️ 无法从URL提取商品ID: {product_url}")

            result_data = {
                'product_url': product_url,
                'product_id': product_id,
                'price_data': price_result.data
            }




            # 抓取ERP区域信息
            erp_result = self.scrape_erp_info()
            if erp_result.success:
                result_data['erp_data'] = erp_result.data
            else:
                self.logger.warning(f"抓取ERP信息失败: {erp_result.error_message}")
                result_data['erp_data'] = {}



                competitors_result = self.scrape_competitor_stores(product_url)
                if competitors_result.success:
                    result_data['competitors'] = competitors_result.data['competitors']
                    # 🔧 修复：使用检测到的总跟卖数量，而不是实际提取的店铺数量
                    result_data['competitor_count'] = competitors_result.data.get('total_count', len(
                        competitors_result.data['competitors']))




            return ScrapingResult(
                success=True,
                data=result_data,
                execution_time=time.time() - start_time
            )

        except Exception as e:
            self.logger.error(f"综合抓取商品信息失败: {e}")
            return ScrapingResult(
                success=False,
                data={},
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    def _extract_price_data_core(self, soup) -> Dict[str, Any]:
        """
        核心价格提取逻辑 - 重构版本，专注于商品基本信息

        Args:
            soup: BeautifulSoup对象

        Returns:
            Dict[str, Any]: 价格数据
        """
        try:
            price_data = {}

            # 提取商品图片
            image_url = self._extract_product_image_core(soup)
            if image_url:
                price_data['image_url'] = image_url

            # 提取基础价格（绿标、黑标）
            basic_prices = self._extract_basic_prices(soup)
            price_data.update(basic_prices)

            return price_data

        except Exception as e:
            self._handle_extraction_error(e, "提取价格数据")
            return {}

    def _extract_basic_prices(self, soup) -> Dict[str, Any]:
        """提取基础价格（绿标、黑标）"""
        prices = {}
        green_price = None
        black_price = None

        # 🔧 修复：严格按照选择器类型提取价格，避免混淆
        for selector, price_type, priority in self.selectors_config.price_selectors:
            try:
                elements = soup.select(selector)
                self.logger.debug(f"🔍 使用选择器 '{selector}' (类型: {price_type}) 找到 {len(elements)} 个元素")

                for element in elements:
                    price = self._extract_price_from_element(element)

                    # 使用 _validate_price 验证价格
                    if not self._validate_price(price, price_type):
                        continue

                    # 🔧 修复：严格按照价格类型分配，避免重复赋值
                    if price_type == "green" and green_price is None:
                        green_price = price
                        currency_symbol = self.currency_config.get_default_symbol()
                        self.logger.info(f"✅ 绿标价格: {green_price}{currency_symbol}")
                        break  # 找到绿标价格后立即跳出内层循环
                    elif price_type == "black" and black_price is None:
                        black_price = price
                        currency_symbol = self.currency_config.get_default_symbol()
                        self.logger.info(f"✅ 黑标价格: {black_price}{currency_symbol}")
                        break  # 找到黑标价格后立即跳出内层循环

            except Exception as e:
                self.logger.debug(f"选择器 '{selector}' 处理失败: {e}")
                continue

        # 🔧 修复：明确记录价格提取结果
        if green_price is None:
            self.logger.info("ℹ️ 未找到绿标价格")
        if black_price is None:
            self.logger.warning("⚠️ 未找到黑标价格")

        # 🔧 修复：只有当价格确实存在时才添加到返回数据中
        if green_price is not None:
            prices['green_price'] = green_price
        if black_price is not None:
            prices['black_price'] = black_price

        self.logger.debug(f"🎯 最终提取的价格数据: {prices}")
        return prices

    def _validate_price(self, price: Optional[float], price_type: str) -> bool:
        """
        验证价格是否有效

        Args:
            price: 价格值
            price_type: 价格类型名称（用于日志）

        Returns:
            bool: 价格是否有效
        """
        if price is None or price <= 0:
            self.logger.debug(f"⚠️ {price_type}价格无效: {price}")
            return False
        return True

    def _handle_extraction_error(self, error: Exception, context: str) -> None:
        """
        统一处理提取错误

        Args:
            error: 异常对象
            context: 上下文描述
        """
        self.logger.error(f"❌ {context}失败: {error}")

    def _extract_price_from_element(self, element) -> Optional[float]:
        """
        从元素中提取价格数值

        Args:
            element: BeautifulSoup元素

        Returns:
            float: 价格数值，如果提取失败返回None
        """
        try:
            if not element:
                return None

            # 获取元素文本
            text = element.get_text(strip=True)
            if not text:
                return None

            # 🔧 重构：使用ScrapingUtils统一处理价格提取
            price = self.scraping_utils.extract_price(text)
            return price

        except Exception as e:
            self._handle_extraction_error(e, "从元素提取价格")
            return None



    # 🔧 修复：删除重复的跟卖店铺提取逻辑，这些功能应该由 CompetitorScraper 负责
    # 删除了大量重复的跟卖店铺相关代码，职责分离：
    # - OzonScraper: 负责价格提取
    # - CompetitorScraper: 负责跟卖店铺交互和提取

    def _extract_product_image_core(self, soup) -> Optional[str]:
        """
        核心图片提取逻辑 - 统一实现避免重复，包含占位符过滤

        Args:
            soup: BeautifulSoup对象

        Returns:
            str: 商品图片URL，如果提取失败返回None
        """
        try:
            # 已知的占位符图片模式
            placeholder_patterns = [
                'doodle_ozon_rus.png',
                'doodle_ozone_rus.png',
                'placeholder.png',
                'no-image.png',
                'default.png',
                'loading.png'
            ]

            for selector in self.selectors_config.image_selectors:
                img_elements = soup.select(selector)
                self.logger.debug(f"🔍 选择器 '{selector}' 找到 {len(img_elements)} 个图片元素")

                for img_element in img_elements:
                    src = img_element.get('src')
                    if not src:
                        continue

                    # 转换为高清版本
                    high_res_url = self._convert_to_high_res_image(src)

                    # 验证图片URL是否为占位符
                    if self._is_placeholder_image(high_res_url, placeholder_patterns):
                        self.logger.warning(f"⚠️ 跳过占位符图片: {high_res_url}")
                        continue

                    # 验证图片URL是否为有效的商品图片
                    if self._is_valid_product_image(high_res_url):
                        self.logger.info(f"✅ 成功提取商品图片: {high_res_url}")
                        return high_res_url
                    else:
                        self.logger.debug(f"🔍 跳过无效图片: {high_res_url}")

            self.logger.warning("⚠️ 未找到有效的商品图片")
            return None

        except Exception as e:
            self._handle_extraction_error(e, "提取商品图片")
            return None

    def _is_placeholder_image(self, image_url: str, placeholder_patterns: list) -> bool:
        """
        检查图片URL是否为占位符图片

        Args:
            image_url: 图片URL
            placeholder_patterns: 占位符图片模式列表

        Returns:
            bool: True表示是占位符图片，False表示不是
        """
        if not image_url:
            return True

        # 检查URL中是否包含占位符模式
        for pattern in placeholder_patterns:
            if pattern in image_url:
                return True

        # 检查是否包含其他已知的占位符特征
        placeholder_keywords = ['doodle', 'placeholder', 'default', 'no-image', 'loading']
        url_lower = image_url.lower()

        for keyword in placeholder_keywords:
            if keyword in url_lower:
                return True

        return False

    def _is_valid_product_image(self, image_url: str) -> bool:
        """
        验证图片URL是否为有效的商品图片

        Args:
            image_url: 图片URL

        Returns:
            bool: True表示是有效商品图片，False表示无效
        """
        if not image_url:
            return False

        # 检查是否包含有效的商品图片特征
        valid_patterns = [
            'multimedia',        # OZON的商品图片通常包含multimedia
            's3/multimedia',     # 完整的S3路径
            'wc1000',           # 高清图片标识
            'wc750',            # 中等分辨率图片
            'wc500',            # 标准分辨率图片
        ]

        url_lower = image_url.lower()

        # 必须包含至少一个有效模式
        has_valid_pattern = any(pattern in url_lower for pattern in valid_patterns)

        # 必须是图片文件
        is_image_file = any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.webp'])

        # 必须来自OZON/OZONE域名
        is_ozon_domain = any(domain in url_lower for domain in ['ozon.ru', 'ozone.ru', 'ir.ozone.ru'])

        # 不能包含明显的占位符特征
        has_placeholder_features = any(keyword in url_lower for keyword in ['doodle', 'placeholder', 'default', 'error'])

        return has_valid_pattern and is_image_file and is_ozon_domain and not has_placeholder_features

    def _convert_to_high_res_image(self, image_url: str) -> str:
        """
        将图片URL转换为高清版本

        Args:
            image_url: 原始图片URL

        Returns:
            str: 高清图片URL
        """
        try:
            import re
            # 将wc50或wc100替换为wc1000
            high_res_url = re.sub(r'/wc\d+/', '/wc1000/', image_url)
            return high_res_url
        except Exception as e:
            self.logger.warning(f"转换高清图片URL失败: {e}")
            return image_url

    def scrape_erp_info(self) -> ScrapingResult:
        """
        抓取ERP插件信息

        Returns:
            ScrapingResult: ERP抓取结果
        """
        try:
            # 使用共享的browser_service实例抓取ERP信息
            return self.erp_scraper.scrape()

        except Exception as e:
            self.logger.error(f"抓取ERP信息失败: {e}")
            return ScrapingResult(
                success=False,
                data={},
                error_message=str(e)
            )



    def scrape_competitor_stores(self, product_url: str, max_competitors: int = 10) -> ScrapingResult:
        """
        抓取跟卖店铺信息（向后兼容方法）

        Args:
            product_url: 商品URL
            max_competitors: 最大跟卖数量，默认10

        Returns:
            ScrapingResult: 跟卖店铺抓取结果
        """
        start_time = time.time()

        try:
            self.logger.info(f"🔍 开始抓取跟卖店铺: {product_url}")

            # 构建跟卖数据结构
            competitors_data = {
                'competitors': [],
                'total_count': 0,
                'target_url': product_url,
                'scraped_at': time.time()
            }

            # 返回成功结果（当前返回空数据，保持接口兼容性）
            return ScrapingResult(
                success=True,
                data=competitors_data,
                execution_time=time.time() - start_time
            )

        except Exception as e:
            self.logger.error(f"抓取跟卖店铺失败: {e}")
            return ScrapingResult(
                success=False,
                data={},
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    # def combine_item(self, data, result_data):

    def _extract_product_id(self, url: str) -> Optional[str]:
        """
        从URL中提取商品ID
        
        支持的URL格式:
        - https://www.ozon.ru/product/xxx-1234567/
        - https://www.ozon.ru/seller/xxx/product/1234567/
        
        Args:
            url: 商品URL
            
        Returns:
            Optional[str]: 商品ID，提取失败返回None

        Raises:
            Exception: 当URL为None时抛出异常
        """
        # 特殊处理None输入
        if url is None:
            raise Exception("URL不能为None")

        try:
            import re
            
            # 首先验证是否为OZON域名
            if not url or not re.search(r'https?://[^/]*ozon\.ru/', url):
                self.logger.debug(f"URL不是OZON域名: {url}")
                return None

            # 匹配 /product/xxx-数字/ 或 /product/数字/ 格式 (兼容有无末尾斜杠)
            patterns = [
                r'/product/[^/]+-(\d+)',     # xxx-1234567 (兼容有无斜杠)
                r'/product/(\d+)',            # 1234567 (兼容有无斜杠)
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    product_id = match.group(1)
                    return product_id
            
            self.logger.debug(f"无法从URL提取商品ID: {url}")
            return None
            
        except Exception as e:
            self.logger.error(f"提取商品ID失败: {e}")
            return None


