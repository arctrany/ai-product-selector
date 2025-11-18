"""
OZON平台抓取器

负责从OZON平台抓取商品价格信息和跟卖店铺数据。
基于新的browser_service架构。
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Tuple

from .xuanping_browser_service import XuanpingBrowserServiceSync
from .competitor_scraper import CompetitorScraper
from ..models import ProductInfo, CompetitorStore, clean_price_string, ScrapingResult
from ..config import GoodStoreSelectorConfig
from ..config.ozon_selectors import get_ozon_selectors_config, OzonSelectorsConfig
from ..business.profit_evaluator import ProfitEvaluator
from .erp_plugin_scraper import ErpPluginScraper


class OzonScraper:
    """OZON平台抓取器 - 基于browser_service架构"""

    def __init__(self, config: Optional[GoodStoreSelectorConfig] = None,
                 selectors_config: Optional[OzonSelectorsConfig] = None):
        """初始化OZON抓取器"""
        self.config = config or GoodStoreSelectorConfig()
        self.selectors_config = selectors_config or get_ozon_selectors_config()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.base_url = self.config.scraping.ozon_base_url

        # 🔧 性能优化：使用共享的浏览器服务，避免重复创建
        self.browser_service = XuanpingBrowserServiceSync()

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
            async def extract_price_data(browser_service):
                """异步提取价格数据"""
                try:
                    # 🔧 性能优化：减少不必要的等待时间
                    await asyncio.sleep(0.5)

                    # 获取页面内容
                    page_content = await browser_service.get_page_content()
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

            # 使用浏览器服务抓取页面数据
            result = self.browser_service.scrape_page_data(product_url, extract_price_data)

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
            async def extract_competitor_data(browser_service):
                """异步提取跟卖店铺数据"""
                try:
                    # 🔧 性能优化：减少不必要的等待时间
                    await asyncio.sleep(0.5)

                    # 🔧 修复：使用CompetitorScraper的严格跟卖检测方法
                    page = browser_service.browser_driver.page
                    popup_result = await self.competitor_scraper.open_competitor_popup(page)

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
                    page = browser_service.browser_driver.page
                    detected_total_count = await self.competitor_scraper._get_competitor_count(page)

                    # 获取页面内容
                    page_content = await browser_service.get_page_content()

                    # 解析跟卖店铺信息 - 修复：使用CompetitorScraper
                    competitors = await self.competitor_scraper.extract_competitors_from_content(page_content,
                                                                                                 max_competitors)

                    # 🔧 修复：返回检测到的总数量，而不是实际提取的数量
                    return {
                        'competitors': competitors,
                        'total_count': detected_total_count if detected_total_count is not None else len(competitors)
                    }

                except Exception as e:
                    self.logger.error(f"提取跟卖店铺数据失败: {e}")
                    return {'competitors': [], 'total_count': 0}

            # 使用浏览器服务抓取页面数据
            result = self.browser_service.scrape_page_data(product_url, extract_competitor_data)

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
    def scrape(self, product_url: str, include_competitors: bool = False, **kwargs) -> ScrapingResult:
        """
        综合抓取商品信息
        
        Args:
            product_url: 商品URL
            include_competitors: 是否包含跟卖店铺信息
            **kwargs: 其他参数
            
        Returns:
            ScrapingResult: 抓取结果
        """
        start_time = time.time()

        try:
            # 抓取价格信息
            price_result = self.scrape_product_prices(product_url)
            if not price_result.success:
                return price_result

            result_data = {
                'product_url': product_url,
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
            for keyword in self.selectors_config.COMPETITOR_KEYWORDS:
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
                        self.logger.info(f"💰 跟卖价格: {competitor_price}₽")
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
        for selector, price_type in self.selectors_config.PRICE_SELECTORS:
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
                        self.logger.info(f"✅ 绿标价格: {green_price}₽")
                        break  # 找到绿标价格后立即跳出内层循环
                    elif price_type == "black" and black_price is None:
                        black_price = price
                        self.logger.info(f"✅ 黑标价格: {black_price}₽")
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
            competitor_price_selector = self.selectors_config.COMPETITOR_PRICE_SELECTOR

            self.logger.debug(f"🔍 使用精确跟卖价格选择器: {competitor_price_selector}")

            # 查找跟卖价格元素
            competitor_elements = soup.select(competitor_price_selector)

            for element in competitor_elements:
                text = element.get_text(strip=True)
                self.logger.debug(f"🔍 找到跟卖价格元素文本: '{text}'")

                # 🔧 修复：只处理包含价格符号的元素，过滤掉配送时间等非价格信息
                # 使用配置化的货币符号检查
                has_currency = any(symbol.lower() in text.lower() for symbol in self.selectors_config.CURRENCY_SYMBOLS)
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
        核心图片提取逻辑 - 统一实现避免重复

        Args:
            soup: BeautifulSoup对象

        Returns:
            str: 商品图片URL，如果提取失败返回None
        """
        try:
            for selector in self.selectors_config.IMAGE_SELECTORS:
                img_element = soup.select_one(selector)
                if img_element:
                    src = img_element.get('src')
                    if src:
                        high_res_url = self._convert_to_high_res_image(src)
                        self.logger.info(f"✅ 成功提取商品图片: {high_res_url}")
                        return high_res_url

            self.logger.warning("⚠️ 未找到商品图片")
            return None

        except Exception as e:
            self._handle_extraction_error(e, "提取商品图片")
            return None

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

    def close(self):
        """
        关闭抓取器，清理资源
        """
        try:
            if hasattr(self, 'browser_service') and self.browser_service:
                self.browser_service.close()
                self.logger.info("🔒 OzonScraper 已关闭")
            if hasattr(self, 'erp_scraper') and self.erp_scraper:
                self.erp_scraper.close()
        except Exception as e:
            self.logger.error(f"关闭 OzonScraper 时发生错误: {e}")

    def __del__(self):
        """
        析构函数，确保资源被正确释放
        """
        try:
            self.close()
        except:
            pass

    # def combine_item(self, data, result_data):
    #     pass
