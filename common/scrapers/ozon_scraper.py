"""
OZON平台抓取器

负责从OZON平台抓取商品价格信息和跟卖店铺数据。
基于新的browser_service架构。
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Tuple

from .base_scraper import BaseScraper
from .global_browser_singleton import get_global_browser_service
from .competitor_scraper import CompetitorScraper
from ..models import ProductInfo, CompetitorStore, clean_price_string, ScrapingResult
from ..config import GoodStoreSelectorConfig
from ..config.ozon_selectors import get_ozon_selectors_config, OzonSelectorsConfig
from ..business.profit_evaluator import ProfitEvaluator
from .erp_plugin_scraper import ErpPluginScraper


class OzonScraper(BaseScraper):
    """OZON平台抓取器 - 基于browser_service架构"""

    def __init__(self, config: Optional[GoodStoreSelectorConfig] = None,
                 selectors_config: Optional[OzonSelectorsConfig] = None):
        """初始化OZON抓取器"""
        super().__init__()
        self.config = config or GoodStoreSelectorConfig()
        self.selectors_config = selectors_config or get_ozon_selectors_config()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.base_url = self.config.scraping.ozon_base_url

        # 🔧 性能优化：使用共享的全局浏览器服务，避免重复创建
        self.browser_service = get_global_browser_service()

        # 创建跟卖抓取器
        self.competitor_scraper = CompetitorScraper(selectors_config=self.selectors_config)

        # 创建利润评估器
        self.profit_evaluator = ProfitEvaluator(
            profit_calculator_path=self.config.excel.profit_calculator_path,
            config=self.config
        )

        # 初始化ERP插件抓取器（共享browser_service实例）
        self.erp_scraper = ErpPluginScraper(self.config, self.browser_service)

    def scrape_product_prices(self, product_url: str) -> ScrapingResult:
        """
        抓取商品价格信息
        
        Args:
            product_url: 商品URL
            
        Returns:
            ScrapingResult: 抓取结果，包含价格信息
        """
        start_time = time.time()

        try:
            # 使用浏览器服务抓取数据
            def extract_price_data(browser_service):
                """同步提取价格数据"""
                try:
                    # 🔧 性能优化：减少不必要的等待时间
                    time.sleep(0.5)

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

    def scrape_competitor_stores(self, product_url: str, max_competitors: int = 10) -> ScrapingResult:
        """
        抓取跟卖店铺信息

        Args:
            product_url: 商品URL
            max_competitors: 最大跟卖店铺数量，默认10个

        Returns:
            ScrapingResult: 抓取结果，包含跟卖店铺信息
        """
        start_time = time.time()

        try:
            def extract_competitor_data(browser_service):
                """同步提取跟卖店铺数据"""
                try:
                    # 🔧 性能优化：减少不必要的等待时间
                    time.sleep(0.5)

                    # 🔧 修复：使用CompetitorScraper的严格跟卖检测方法
                    page = browser_service.browser_driver.page
                    popup_result = self.competitor_scraper.open_competitor_popup(page)

                    # 🎯 根据严格检测结果决定后续处理
                    if not popup_result['success']:
                        self.logger.error(f"跟卖检测失败: {popup_result['error_message']}")
                        return {'competitors': [], 'total_count': 0}

                    if not popup_result['has_competitors']:
                        self.logger.info("✅ 确认无跟卖，跳过跟卖信息提取")
                        return {'competitors': [], 'total_count': 0}

                    if not popup_result['popup_opened']:
                        self.logger.warning("⚠️ 有跟卖但浮层未打开，跳过跟卖信息提取")
                        return {'competitors': [], 'total_count': 0}

                    # 🔧 修复：获取检测到的总跟卖数量（而不是实际提取的数量）
                    page = browser_service.get_page()
                    detected_total_count = self.competitor_scraper._get_competitor_count(page)

                    # 获取页面内容 - 使用同步方法
                    page_content = browser_service.evaluate_sync("() => document.documentElement.outerHTML")

                    # 解析跟卖店铺信息 - 修复：使用CompetitorScraper
                    competitors = self.competitor_scraper.extract_competitors_from_content(page_content,
                                                                                                 max_competitors)

                    # 🔧 修复：返回检测到的总数量，而不是实际提取的数量
                    return {
                        'competitors': competitors,
                        'total_count': detected_total_count if detected_total_count is not None else len(competitors)
                    }

                except Exception as e:
                    self.logger.error(f"提取跟卖店铺数据失败: {e}")
                    return {'competitors': [], 'total_count': 0}

            # 使用继承的抓取方法
            result = self.scrape_page_data(product_url, extract_competitor_data)

            if result.success:
                return ScrapingResult(
                    success=True,
                    data=result.data,
                    execution_time=time.time() - start_time
                )
            else:
                return ScrapingResult(
                    success=False,
                    data={'competitors': [], 'total_count': 0},
                    error_message=result.error_message or "无法抓取跟卖店铺信息",
                    execution_time=time.time() - start_time
                )

        except Exception as e:
            self.logger.error(f"抓取跟卖店铺信息失败: {e}")
            return ScrapingResult(
                success=False,
                data={'competitors': [], 'total_count': 0},
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    # 抓取商品信息的主入口
    def scrape(self,
               product_url: str,
               include_competitors: bool = False,
               _recursion_depth: int = 0,
               _fetch_competitor_details: bool = True,
               **kwargs) -> ScrapingResult:
        """
        综合抓取商品信息

        Args:
            product_url: 商品URL
            include_competitors: 是否包含跟卖店铺信息
            _recursion_depth: 递归深度（内部参数，防止无限递归）
            _fetch_competitor_details: 是否抓取跟卖商品详情（内部参数）
            **kwargs: 其他参数

        Returns:
            ScrapingResult: 抓取结果，包含 product_id 和可选的 first_competitor_details 字段
        """
        start_time = time.time()

        try:
            # 🔒 递归深度限制（硬性保护）
            if _recursion_depth > 1:
                self.logger.error("递归深度超限，终止抓取")
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message="递归深度超限",
                    execution_time=time.time() - start_time
                )
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
                'price_data': price_result.data,
                'include_competitors': include_competitors
            }


            # 判断跟卖价格比黑标价格、绿标价格是否更低,绿标价格如果不存在则比价黑标价格即可；
            has_better_price = self.profit_evaluator.has_better_competitor_price(result_data)

            # 抓取ERP区域信息
            erp_result = self.scrape_erp_info()
            if erp_result.success:
                result_data['erp_data'] = erp_result.data
            else:
                self.logger.warning(f"抓取ERP信息失败: {erp_result.error_message}")
                result_data['erp_data'] = {}


            # 如果需要，抓取跟卖店铺信息
            if include_competitors and has_better_price:
                competitors_result = self.scrape_competitor_stores(product_url)
                if competitors_result.success:
                    result_data['competitors'] = competitors_result.data['competitors']
                    # 🔧 修复：使用检测到的总跟卖数量，而不是实际提取的店铺数量
                    result_data['competitor_count'] = competitors_result.data.get('total_count', len(
                        competitors_result.data['competitors']))


                else:
                    self.logger.warning(f"抓取跟卖店铺信息失败: {competitors_result.error_message}")
                    result_data['competitors'] = []
                    result_data['competitor_count'] = 0

                # 🔄 递归抓取第一个跟卖商品详情
                if _fetch_competitor_details and _recursion_depth == 0:
                    try:
                        self.logger.info("🎯 开始抓取第一个跟卖商品详情")

                        # 点击第一个跟卖店铺并获取新URL和商品ID
                        first_url, first_product_id = self._click_first_competitor()
                        self.logger.info(f"✅ 跳转到跟卖商品: {first_url} (ID: {first_product_id})")

                        # 递归调用 scrape()，禁止再次递归
                        competitor_result = self.scrape(
                            first_url,
                            include_competitors=False,
                            _fetch_competitor_details=False,
                            _recursion_depth=1
                        )

                        if competitor_result.success:
                            result_data['first_competitor_details'] = competitor_result.data
                            self.logger.info("✅ 成功抓取跟卖商品详情")
                        else:
                            self.logger.warning(f"⚠️ 递归抓取失败，但不影响主流程: {competitor_result.error_message}")

                    except Exception as e:
                        self.logger.warning(f"⚠️ 抓取跟卖商品详情失败: {e}")
                        # 不影响主流程，继续返回原商品数据

            else:
                # 即使不抓取跟卖店铺，也要设置 competitor_count
                result_data['competitors'] = []
                result_data['competitor_count'] = 0

            # 如果include_competitors = False, 并且include_competitors = True，并且result_data里存在itemUrl，则抓取scrape当前商品的信息
            # competitor_product_url = result_data.get('competitor_product_url')
            # competitor_item_result = None
            # if not include_competitors and competitor_product_url:
            #     competitor_item_result = self.scrape(competitor_product_url, include_competitors=False)
            #
            # # 编写一个函数chooseGoodItem根据competitor item result和原始的result_data
            # # 进行加工和验证，返回一个新的result_data，包含一个当前商品以及competitor商品，先不实现逻辑打印即可。
            # if competitor_item_result and competitor_item_result.success:
            #     self.combine_item(competitor_item_result.data, result_data)

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
        核心价格提取逻辑 - 简化版本

        Args:
            soup: BeautifulSoup对象
            is_async: 是否异步调用

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

            # 🔧 修复：直接在主流程中检测跟卖关键词并提取价格
            page_text = soup.get_text()

            # 检测跟卖关键词
            for keyword in self.selectors_config.competitor_keywords:
                if keyword.lower() in page_text.lower():
                    self.logger.info(f"🔍 检测到跟卖关键词: {keyword}")
                    price_data.update({
                        'has_competitors': True,
                        'competitor_keyword': keyword
                    })

                    # 提取跟卖价格
                    competitor_price = self._extract_competitor_price_value(soup)
                    if competitor_price:
                        price_data['competitor_price'] = competitor_price
                        currency_symbol = self.currency_config.get_default_symbol()
                        self.logger.info(f"💰 跟卖价格: {competitor_price}{currency_symbol}")
                    break

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

            # 使用clean_price_string函数提取价格
            price = clean_price_string(text, self.selectors_config)
            return price

        except Exception as e:
            self._handle_extraction_error(e, "从元素提取价格")
            return None

    def _extract_competitor_price_value(self, soup) -> Optional[float]:
        """提取具体的跟卖价格数值 - 使用配置的精确选择器"""
        try:
            # 🎯 使用配置的精确跟卖价格选择器
            competitor_price_selector = self.selectors_config.competitor_price_selector

            self.logger.debug(f"🔍 使用精确跟卖价格选择器: {competitor_price_selector}")

            # 查找跟卖价格元素
            competitor_elements = soup.select(competitor_price_selector)

            for element in competitor_elements:
                text = element.get_text(strip=True)
                self.logger.debug(f"🔍 找到跟卖价格元素文本: '{text}'")

                # 🔧 修复：只处理包含价格符号的元素，过滤掉配送时间等非价格信息
                # 使用配置化的货币符号检查
                has_currency = self.currency_config.is_currency_symbol(text)
                if not has_currency:
                    self.logger.debug(f"⚠️ 跳过非价格元素: '{text}'")
                    continue

                # 提取价格数值 - 处理 "From 3 800 ₽" 格式
                price = self._extract_price_from_element(element)
                if self._validate_price(price, "跟卖"):
                    self.logger.debug(f"🎯 成功提取跟卖价格: {price}₽")
                    return price

            self.logger.debug("⚠️ 未找到包含价格符号的跟卖价格元素")
            return None

        except Exception as e:
            self._handle_extraction_error(e, "提取跟卖价格")
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

    def _click_first_competitor(self) -> Tuple[str, Optional[str]]:
        """
        点击第一个跟卖店铺卡片的安全区域（避免店铺名称/Logo）
        返回跳转后的商品详情页URL和商品ID
        
        Returns:
            Tuple[str, Optional[str]]: (新URL, 商品ID)
                - 新URL: 跳转后的商品详情页URL
                - 商品ID: 从URL中提取的product_id，提取失败时为None
                
        Raises:
            Exception: 点击失败、跳转失败等
        """
        try:
            page = self.browser_service.get_page()
            
            # 1. 定位第一个跟卖卡片（支持新旧选择器）
            card_selectors = ["div.pdp_bk3", "div.pdp_kb2"]
            first_card = None
            
            for selector in card_selectors:
                # 使用同步方法替代异步的 Locator.count()
                elements = self.browser_service.query_selector_all_sync(selector)
                count = len(elements) if elements else 0
                if count > 0:
                    first_card = page.locator(selector).first
                    self.logger.info(f"✅ 找到第一个跟卖卡片: {selector}")
                    break
            
            if not first_card:
                raise Exception("未找到跟卖店铺卡片")
            
            # 2. 优先点击的安全区域选择器（避开店铺名称/Logo）
            # 注意：整个卡片有JS事件监听，点击非店铺链接区域会跳转到商品页
            safe_click_selectors = [
                # 🥇 最高优先级：价格区域（用户已验证）
                "div.pdp_bk0",              # 价格容器
                "div.pdp_b1k",              # 价格文本
                
                # 🥈 高优先级：其他信息区域
                "div.pdp_kb1",              # Ozon卡片价格
                "div.pdp_b3j",              # 配送信息区域
                "div.pdp_jb3",              # 配送文本区域
                
                # 🥉 中优先级：按钮区域
                "div.pdp_j6b",              # 按钮容器
            ]
            
            # 3. 查找可点击的安全区域
            clickable_element = None
            used_selector = None
            
            for selector in safe_click_selectors:
                # 使用同步方法替代异步的 Locator.count()
                elements = self.browser_service.query_selector_all_sync(selector)
                count = len(elements) if elements else 0
                if count > 0:
                    clickable_element = first_card.locator(selector).first
                    used_selector = selector
                    self.logger.info(f"✅ 找到安全点击区域: {selector}")
                    break
            
            if not clickable_element:
                raise Exception("未找到安全的可点击区域")
            
            # 4. 记录原URL
            original_url = page.url
            self.logger.info(f"原始URL: {original_url}")
            
            # 5. 滚动到元素可见位置
            clickable_element.scroll_into_view_if_needed()
            time.sleep(0.2)
            
            # 6. 点击元素
            clickable_element.click()
            self.logger.info(f"✅ 已点击跟卖卡片的 {used_selector} 区域")
            
            # 7. 等待页面跳转
            time.sleep(2)
            
            # 8. 获取跳转后的URL
            new_url = page.url
            self.logger.info(f"跳转后URL: {new_url}")
            
            # 9. 验证跳转
            if new_url == original_url:
                raise Exception("页面未跳转，点击可能失败")
            
            # 10. 验证跳转到商品页（而非店铺首页）
            if '/product/' not in new_url:
                self.logger.warning(f"⚠️ 可能跳转到了店铺首页: {new_url}")
                # 不抛异常，因为可能是预期行为
            
            # 11. 立即从新URL提取product_id
            product_id = self._extract_product_id(new_url)
            if product_id:
                self.logger.info(f"✅ 提取到跟卖商品ID: {product_id}")
            else:
                self.logger.warning(f"⚠️ 无法从URL提取商品ID: {new_url}")
            
            return new_url, product_id
            
        except Exception as e:
            self.logger.error(f"点击第一个跟卖店铺失败: {e}")
            raise
    #     pass
