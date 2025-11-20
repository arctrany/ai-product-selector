"""
Seerfar平台抓取器

负责从Seerfar平台抓取OZON店铺的销售数据和商品信息。
基于现代化的Playwright浏览器服务。
"""

import time
import re
from typing import Dict, Any, List, Optional, Callable

from .base_scraper import BaseScraper
from .global_browser_singleton import get_global_browser_service
from .scraper_utils import ScraperUtils
from ..models import ScrapingResult
from common.config import GoodStoreSelectorConfig
from common.config.seerfar_selectors import get_seerfar_selector


class SeerfarScraper(BaseScraper):
    """Seerfar平台抓取器"""

    def __init__(self, config: Optional[GoodStoreSelectorConfig] = None):
        """初始化Seerfar抓取器"""
        super().__init__()
        from common.config import get_config
        import logging

        self.config = config or get_config()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.base_url = self.config.scraping.seerfar_base_url
        self.store_detail_path = self.config.scraping.seerfar_store_detail_path

        # 使用全局浏览器服务
        self.browser_service = get_global_browser_service()

    def scrape_store_sales_data(self, store_id: str, store_filter_func=None) -> ScrapingResult:
        """
        抓取店铺销售数据

        Args:
            store_id: 店铺ID
            store_filter_func: 店铺过滤函数，用于筛选店铺（检查销售额和订单量）

        Returns:
            ScrapingResult: 抓取结果，包含销售数据
        """
        # 构建店铺详情页URL
        url = f"{self.base_url}{self.store_detail_path}?storeId={store_id}&platform=OZON"

        # dryrun模式下记录入参，但仍执行真实的抓取流程
        if self.config.dryrun:
            self.logger.info(f"🧪 试运行模式 - Seerfar店铺销售数据抓取入参: 店铺ID={store_id}, URL={url}")
            self.logger.info("🧪 试运行模式 - 执行真实的销售数据抓取流程（结果不会保存到文件）")

        # 使用继承的抓取方法
        result = self.scrape_page_data(url, self._extract_sales_data_async)

        # 如果提供了过滤函数，则应用过滤
        # 注意：需要将字段名转换为统一格式
        if result.success and store_filter_func and result.data:
            filter_data = {
                'store_sales_30days': result.data.get('sold_30days', 0),
                'store_orders_30days': result.data.get('sold_count_30days', 0)
            }
            if not store_filter_func(filter_data):
                self.logger.info(f"店铺{store_id}不符合筛选条件")
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message="店铺不符合筛选条件",
                    execution_time=result.execution_time
                )

        return result



    def scrape(
        self,
        store_id: str,
        include_products: bool = True,
        max_products: Optional[int] = None,
        product_filter_func: Optional[Callable[[Dict[str, Any]], bool]] = None,
        store_filter_func: Optional[Callable[[Dict[str, Any]], bool]] = None,
        **kwargs
    ) -> ScrapingResult:
        """
        统一的店铺抓取接口（整合销售数据和商品抓取）

        Args:
            store_id: 店铺ID
            include_products: 是否包含商品信息，默认 True
            max_products: 最大抓取商品数量，默认使用配置中的值
            product_filter_func: 商品过滤函数，接受商品数据字典，返回布尔值
            store_filter_func: 店铺过滤函数，接受销售数据字典，返回布尔值
            **kwargs: 其他参数

        Returns:
            ScrapingResult: 抓取结果，包含销售数据和商品列表

        使用场景：
            1. 只获取销售数据：scrape(store_id, include_products=False)
            2. 获取完整信息：scrape(store_id, include_products=True)
            3. 带过滤的抓取：scrape(store_id, store_filter_func=..., product_filter_func=...)
        """
        start_time = time.time()

        try:
            # 1. 抓取销售数据
            sales_result = self.scrape_store_sales_data(store_id)
            if not sales_result.success:
                return sales_result

            result_data = {
                'store_id': store_id,
                'sales_data': sales_result.data
            }

            # 2. 应用店铺过滤（如果提供）
            if store_filter_func:
                # 转换字段名以匹配过滤函数期望的格式
                filter_data = {
                    'store_sales_30days': sales_result.data.get('sold_30days', 0),
                    'store_orders_30days': sales_result.data.get('sold_count_30days', 0)
                }
                if not store_filter_func(filter_data):
                    self.logger.info(f"店铺{store_id}未通过店铺过滤条件，跳过商品抓取")
                    return ScrapingResult(
                        success=False,
                        data=result_data,
                        error_message="店铺未通过过滤条件",
                        execution_time=time.time() - start_time
                    )

            # 3. 如果需要，抓取商品信息
            if include_products:
                # 使用配置中的默认值或传入的值
                max_products = max_products or self.config.store_filter.max_products_to_check

                # 构建店铺详情页URL
                url = f"{self.base_url}{self.store_detail_path}?storeId={store_id}&platform=OZON"

                # dryrun模式下记录入参
                if self.config.dryrun:
                    self.logger.info(f"🧪 试运行模式 - Seerfar店铺商品抓取入参: 店铺ID={store_id}, "
                                     f"最大商品数={max_products}, URL={url}")
                    self.logger.info("🧪 试运行模式 - 执行真实的商品抓取流程（结果不会保存到文件）")

                # 创建提取函数
                async def extract_products(browser_service):
                    products = await self._extract_products_list_async(
                        browser_service,
                        max_products,
                        product_filter_func
                    )
                    return {'products': products, 'total_count': len(products)}

                # 使用继承的抓取方法
                products_result = self.scrape_page_data(url, extract_products)

                if products_result.success:
                    result_data['products'] = products_result.data['products']
                else:
                    self.logger.warning(f"抓取店铺{store_id}商品信息失败: {products_result.error_message}")
                    result_data['products'] = []

            return ScrapingResult(
                success=True,
                data=result_data,
                execution_time=time.time() - start_time
            )

        except Exception as e:
            self.logger.error(f"综合抓取店铺{store_id}信息失败: {e}")
            return ScrapingResult(
                success=False,
                data={},
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    async def _extract_sales_data_async(self, browser_service) -> Dict[str, Any]:
        """
        异步提取销售数据 - 使用配置文件中的选择器

        Args:
            browser_service: 浏览器服务实例

        Returns:
            Dict[str, Any]: 销售数据
        """
        sales_data = {}

        try:
            # 直接访问 page 对象
            page = browser_service.page

            # 验证 page 对象
            if not self._validate_page(page):
                return {}

            # 使用配置文件中的选择器提取销售额
            await self._extract_sales_amount(page, sales_data)

            # 使用配置文件中的选择器提取销量
            await self._extract_sales_volume(page, sales_data)

            # 使用配置文件中的选择器提取日均销量
            await self._extract_daily_avg_sales(page, sales_data)

            # 如果没有找到具体元素，尝试通用方法
            if not sales_data:
                sales_data = await self._extract_sales_data_generic_async(page)

            # 合并日志输出店铺数据摘要
            if sales_data:
                sales_amount = sales_data.get('sold_30days', 0)
                sales_volume = sales_data.get('sold_count_30days', 0)
                daily_avg = sales_data.get('daily_avg_sold', 0)
                self.logger.info(
                    f"📊 店铺数据提取完成 - 销售额: {sales_amount:.0f}₽, 销量: {sales_volume}, 日均: {daily_avg}")

            self.logger.debug(f"提取的销售数据: {sales_data}")
            return sales_data

        except Exception as e:
            self.logger.error(f"提取销售数据失败: {e}")
            return {}

    async def _extract_sales_amount(self, page, sales_data: Dict[str, Any]):
        """提取销售额 - 使用配置文件中的选择器"""
        try:
            # 从配置文件获取销售额选择器
            sales_amount_selector = get_seerfar_selector('store_sales_data', 'sales_amount')
            if not sales_amount_selector:
                self.logger.error("❌ 未能找到销售额选择器配置")
                return

            # 等待元素出现
            try:
                await page.wait_for_selector(sales_amount_selector, timeout=5000)
            except:
                self.logger.debug("销售额元素等待超时，继续尝试提取")

            element = await page.query_selector(sales_amount_selector)
            if element:
                text = await element.text_content()
                if text and text.strip():
                    # 提取数字并转换为销售额
                    number = ScraperUtils.extract_number_from_text(text.strip())
                    if number:
                        sales_data['sold_30days'] = number
                        return

            self.logger.warning("⚠️ 未能提取到销售额数据")

        except Exception as e:
            self.logger.error(f"❌ 销售额提取失败: {str(e)}")

    async def _extract_sales_volume(self, page, sales_data: Dict[str, Any]):
        """提取销量 - 使用配置文件中的选择器"""
        try:
            # 从配置文件获取销量选择器
            sales_volume_selector = get_seerfar_selector('store_sales_data', 'sales_volume')
            if not sales_volume_selector:
                self.logger.error("❌ 未能找到销量选择器配置")
                return

            # 等待元素出现
            try:
                await page.wait_for_selector(sales_volume_selector, timeout=5000)
            except:
                self.logger.debug("销量元素等待超时，继续尝试提取")

            element = await page.query_selector(sales_volume_selector)
            if element:
                text = await element.text_content()
                if text and text.strip():
                    # 提取数字并转换为销量
                    number = ScraperUtils.extract_number_from_text(text.strip())
                    if number:
                        sales_data['sold_count_30days'] = int(number)
                        return

            self.logger.warning("⚠️ 未能提取到销量数据")

        except Exception as e:
            self.logger.error(f"❌ 销量提取失败: {str(e)}")

    async def _extract_daily_avg_sales(self, page, sales_data: Dict[str, Any]):
        """提取日均销量 - 使用配置文件中的选择器"""
        try:
            # 从配置文件获取日均销量选择器
            daily_avg_selector = get_seerfar_selector('store_sales_data', 'daily_avg_sales')
            if not daily_avg_selector:
                self.logger.error("❌ 未能找到日均销量选择器配置")
                return

            # 等待元素出现
            try:
                await page.wait_for_selector(daily_avg_selector, timeout=5000)
            except:
                self.logger.debug("日均销量元素等待超时，继续尝试提取")

            element = await page.query_selector(daily_avg_selector)
            if element:
                text = await element.text_content()
                if text and text.strip():
                    # 提取数字并转换为日均销量
                    number = ScraperUtils.extract_number_from_text(text.strip())
                    if number:
                        sales_data['daily_avg_sold'] = number
                        return

            self.logger.warning("⚠️ 未能提取到日均销量数据")

        except Exception as e:
            self.logger.error(f"❌ 日均销量提取失败: {str(e)}")

    async def _extract_category_data(self, page, sales_data: Dict[str, Any]):
        """提取类目数据 - 使用配置文件中的选择器"""
        try:
            # 从配置文件获取类目数据选择器
            category_xpath = get_seerfar_selector('store_sales_data', 'category_data')
            if not category_xpath:
                self.logger.debug("未配置类目数据选择器，跳过类目数据提取")
                return

            # 等待元素出现
            try:
                await page.wait_for_selector(f'xpath={category_xpath}', timeout=5000)
            except:
                self.logger.debug("类目数据元素等待超时，继续尝试提取")

            element = await page.query_selector(f'xpath={category_xpath}')
            if element:
                text = await element.text_content()
                if text and text.strip():
                    sales_data['category_info'] = text.strip()
                    return

            self.logger.warning("⚠️ 未能提取到类目数据")

        except Exception as e:
            self.logger.error(f"❌ 类目数据提取失败: {str(e)}")

    async def _extract_sales_data_generic_async(self, page) -> Dict[str, Any]:
        """
        异步通用方法提取销售数据
        
        Args:
            page: Playwright页面对象
            
        Returns:
            Dict[str, Any]: 销售数据
        """
        sales_data = {}

        try:
            # 查找所有包含数字的元素
            number_elements = await page.query_selector_all(
                "//*[contains(text(), '₽') or contains(text(), '万') or contains(text(), '千')]")

            for element in number_elements[:10]:  # 限制检查前10个元素
                try:
                    text = await element.text_content()
                    if not text:
                        continue

                    # 判断是否为销售额
                    if any(keyword in text for keyword in ['销售额', '营业额', '收入', '₽']):
                        number = ScraperUtils.extract_number_from_text(text)
                        if number and number > 1000:  # 销售额通常较大
                            sales_data['sold_30days'] = number

                    # 判断是否为销量
                    elif any(keyword in text for keyword in ['销量', '订单', '件数']):
                        number = ScraperUtils.extract_number_from_text(text)
                        if number and 10 <= number <= 10000:  # 销量通常在合理范围内
                            sales_data['sold_count_30days'] = int(number)
                except Exception as e:
                    self.logger.debug(f"处理元素文本失败: {e}")
                    continue

            # 如果找到销售额和销量，计算日均销量
            if 'sold_30days' in sales_data and 'sold_count_30days' in sales_data:
                sales_data['daily_avg_sold'] = sales_data['sold_count_30days'] / 30

            return sales_data

        except Exception as e:
            self.logger.error(f"通用方法提取销售数据失败: {e}")
            return {}

    async def _extract_products_list_async(self, browser_service, max_products: int,
                                           product_filter_func: Optional[Callable[[Dict[str, Any]], bool]] = None) -> List[Dict[str, Any]]:
        """
        异步提取商品列表，支持前置过滤

        Args:
            browser_service: 浏览器服务实例
            max_products: 最大商品数量
            product_filter_func: 商品过滤函数，用于前置过滤（在提取 OZON 详情前）

        Returns:
            List[Dict[str, Any]]: 商品列表
        """
        products = []
        filtered_count = 0

        try:
            # 直接访问 page 对象
            page = browser_service.page

            # 验证 page 对象
            if not self._validate_page(page):
                return []

            # 从配置文件获取商品列表选择器
            product_rows_selector = get_seerfar_selector('product_list', 'product_rows')
            product_rows_alt_selector = get_seerfar_selector('product_list', 'product_rows_alt')

            if not product_rows_selector or not product_rows_alt_selector:
                self.logger.error("❌ 未能找到商品列表选择器配置")
                return []

            # 查找商品表格或列表
            product_rows = await page.query_selector_all(product_rows_selector)

            if not product_rows:
                # 尝试其他可能的选择器
                product_rows = await page.query_selector_all(product_rows_alt_selector)

            # 🔧 修复：去重，避免 CSS 和 XPath 选择器匹配到相同元素
            product_rows = await self._deduplicate_rows(product_rows)
            total_rows = len(product_rows)
            self.logger.info(f"📋 找到 {total_rows} 个商品行（去重后），开始处理（最多 {max_products} 个）")

            # 🔧 修复：每次循环重新获取商品行，避免页面导航后元素失效
            # 使用索引而不是直接遍历元素
            for i in range(min(total_rows, max_products)):
                try:
                    # 🔧 关键修复：每次循环重新获取商品行列表
                    current_rows = await page.query_selector_all(product_rows_selector)
                    if not current_rows:
                        current_rows = await page.query_selector_all(product_rows_alt_selector)

                    # 去重
                    unique_current_rows = await self._deduplicate_rows(current_rows)

                    # 检查索引是否有效
                    if i >= len(unique_current_rows):
                        self.logger.warning(f"⚠️  索引 {i} 超出范围，跳过")
                        break

                    row = unique_current_rows[i]

                    # 先提取基础字段（类目、上架时间、销量、重量）
                    category_data = await self._extract_category(row)
                    listing_date_data = await self._extract_listing_date(row)
                    sales_volume = await self._extract_product_sales_volume(row)
                    weight = await self._extract_weight(row)

                    # 构建基础商品数据用于前置过滤（使用统一字段名）
                    basic_product_data = {
                        'product_category_cn': category_data.get('category_cn'),
                        'product_category_ru': category_data.get('category_ru'),
                        'product_listing_date': listing_date_data.get('listing_date'),
                        'product_shelf_duration': listing_date_data.get('shelf_duration'),
                        'product_sales_volume': sales_volume,
                        'product_weight': weight
                    }

                    # 应用前置过滤
                    if product_filter_func:
                        if not product_filter_func(basic_product_data):
                            filtered_count += 1
                            self.logger.debug(f"⏭️  商品 #{i+1} 未通过前置过滤，跳过 OZON 详情页处理")
                            continue

                    # 通过过滤，继续提取完整商品信息（包括 OZON 详情页）
                    product_data = await self._extract_product_from_row_async(row)
                    if product_data:
                        products.append(product_data)
                        self.logger.info(f"✅ 商品 #{i+1} 提取成功")

                except Exception as e:
                    self.logger.warning(f"⚠️  提取第 {i + 1} 个商品信息失败: {e}")
                    continue

            if products:
                self.logger.info(f"🎉 成功提取 {len(products)} 个有效商品信息（前置过滤跳过 {filtered_count} 个）")
            else:
                self.logger.warning("⚠️  未提取到有效的商品信息")
            return products

        except Exception as e:
            self.logger.error(f"❌ 提取商品列表失败: {e}")
            return []

    async def _extract_product_from_row_async(self, row_element) -> Optional[Dict[str, Any]]:
        """
        异步从行元素中提取商品信息并点击进入OZON详情页

        主方法：协调整个商品信息提取流程

        Args:
            row_element: 行元素

        Returns:
            Dict[str, Any]: 完整的商品信息（包含OZON详情页数据）
        """
        try:
            # 1. 提取 Seerfar 表格基础数据
            product_data = await self._extract_basic_product_data(row_element)

            # 2. 获取 OZON URL
            ozon_url = await self._get_ozon_url_from_row(row_element)
            if not ozon_url:
                return None

            # 3. 抓取 OZON 详情页数据
            ozon_data = await self._fetch_ozon_details(ozon_url)
            if ozon_data:
                product_data.update(ozon_data)

            return product_data if product_data else None

        except Exception as e:
            self.logger.error(f"提取商品信息失败: {e}")
            return None

    async def _extract_basic_product_data(self, row_element) -> Dict[str, Any]:
        """
        提取 Seerfar 表格中的基础商品数据

        Args:
            row_element: 行元素

        Returns:
            Dict[str, Any]: 基础商品数据（类目、上架时间、销量、重量）
        """
        product_data = {}

        # 1. 提取类目信息
        category_data = await self._extract_category(row_element)
        product_data.update(category_data)

        # 2. 提取上架时间
        listing_date_data = await self._extract_listing_date(row_element)
        product_data.update(listing_date_data)

        # 3. 提取销量
        sales_volume = await self._extract_product_sales_volume(row_element)
        if sales_volume is not None:
            product_data['sales_volume'] = sales_volume

        # 4. 提取重量
        weight = await self._extract_weight(row_element)
        if weight is not None:
            product_data['weight'] = weight

        return product_data

    async def _get_ozon_url_from_row(self, row_element) -> Optional[str]:
        """
        从行元素中提取 OZON URL

        Args:
            row_element: 行元素

        Returns:
            Optional[str]: OZON URL，如果提取失败返回 None
        """
        try:
            # 验证 page 对象
            page = self.browser_service.page
            if not self._validate_page(page):
                return None

            # 从配置文件获取选择器
            third_column_selector = get_seerfar_selector('product_list', 'third_column')
            clickable_element_selector = get_seerfar_selector('product_list', 'clickable_element')
            clickable_element_alt_selector = get_seerfar_selector('product_list', 'clickable_element_alt')

            if not third_column_selector or not clickable_element_selector or not clickable_element_alt_selector:
                self.logger.error("❌ 未能找到商品行元素选择器配置")
                return None

            # 查找第三列中有onclick事件的元素
            td3_element = await row_element.query_selector(third_column_selector)
            if not td3_element:
                self.logger.warning("⚠️ 未找到第三列，跳过此商品")
                return None

            # 查找可点击元素
            clickable_element = await td3_element.query_selector(clickable_element_selector)
            if not clickable_element:
                clickable_element = await td3_element.query_selector(clickable_element_alt_selector)
                if not clickable_element:
                    self.logger.warning("⚠️ 未找到可点击的商品元素，跳过此商品")
                    return None

            # 记录找到的元素类型
            element_tag = await clickable_element.evaluate("el => el.tagName")
            element_class = await clickable_element.evaluate("el => el.className")
            self.logger.info(f"🔗 找到可点击元素: {element_tag}.{element_class}")

            # 提取 onclick 中的 URL
            onclick_attr = await clickable_element.get_attribute("onclick")
            if onclick_attr and "window.open" in onclick_attr:
                import re
                url_match = re.search(r"window\.open\('([^']+)'\)", onclick_attr)
                if url_match:
                    ozon_url = url_match.group(1)
                    self.logger.info(f"提取到 OZON URL: {ozon_url}")

                    # 获取最终 URL（处理重定向）
                    final_url = await self._resolve_ozon_url(ozon_url, page)
                    return final_url

            self.logger.warning("未找到有效的onclick事件")
            return None

        except Exception as e:
            self.logger.error(f"提取 OZON URL 失败: {e}")
            return None

    async def _resolve_ozon_url(self, ozon_url: str, page) -> str:
        """
        解析 OZON URL，处理可能的重定向

        Args:
            ozon_url: 原始 OZON URL
            page: 当前页面对象

        Returns:
            str: 最终的 OZON URL
        """
        new_page = None
        try:
            new_page = await page.context.new_page()
            await new_page.goto(ozon_url)
            await new_page.wait_for_load_state('domcontentloaded', timeout=5000)

            # 获取最终URL（可能有重定向）
            final_ozon_url = new_page.url
            self.logger.info(f"获取到最终 OZON URL: {final_ozon_url}")
            return final_ozon_url

        finally:
            # 立即关闭临时页面，释放浏览器资源
            if new_page:
                try:
                    await new_page.close()
                    self.logger.debug("✅ 临时页面已关闭")
                except Exception as close_error:
                    self.logger.warning(f"关闭临时页面时出错: {close_error}")

    async def _fetch_ozon_details(self, ozon_url: str) -> Optional[Dict[str, Any]]:
        """
        抓取 OZON 详情页数据

        Args:
            ozon_url: OZON 商品详情页 URL

        Returns:
            Optional[Dict[str, Any]]: OZON 详情页数据，包含价格、跟卖店铺、ERP 数据
        """
        self.logger.info("📊 调用 OzonScraper 处理 OZON 商品详情页...")
        try:
            from .ozon_scraper import OzonScraper

            # 创建 OzonScraper 实例并使用公共接口
            ozon_scraper = OzonScraper(self.config)
            ozon_result = ozon_scraper.scrape(ozon_url, include_competitors=True)

            # 处理抓取结果
            if ozon_result.success:
                ozon_data = {}

                # 提取价格数据
                if 'price_data' in ozon_result.data:
                    ozon_data.update(ozon_result.data['price_data'])
                    self.logger.debug(f"✅ 价格数据已提取: {len(ozon_result.data['price_data'])}项")

                # 提取跟卖店铺数据
                if 'competitors' in ozon_result.data:
                    ozon_data['competitors'] = ozon_result.data['competitors']
                    self.logger.debug(f"✅ 跟卖店铺数据已提取: {len(ozon_result.data['competitors'])}个")

                # 提取 ERP 数据
                if 'erp_data' in ozon_result.data:
                    ozon_data['erp_data'] = ozon_result.data['erp_data']
                    self.logger.debug("✅ ERP 数据已提取")

                self.logger.info(f"✅ OZON 数据提取完成: 执行时间={ozon_result.execution_time:.2f}秒")
                return ozon_data
            else:
                self.logger.warning(f"⚠️ OZON 数据提取失败: {ozon_result.error_message}")
                return None

        except Exception as scrape_error:
            self.logger.error(f"❌ 调用 OzonScraper 失败: {scrape_error}")
            return None

    def _validate_page(self, page) -> bool:
        """
        验证 page 对象是否有效

        Args:
            page: Playwright 页面对象

        Returns:
            bool: 页面是否有效
        """
        if page is None:
            self.logger.error("❌ page 对象为 None，浏览器可能未正确启动")
            return False
        return True

    async def _deduplicate_rows(self, rows: list) -> list:
        """
        去重商品行，避免 CSS 和 XPath 选择器匹配到相同元素

        使用 data-index 属性进行去重。如果元素没有 data-index 属性，
        则保留该元素。

        Args:
            rows: 商品行元素列表

        Returns:
            list: 去重后的商品行列表
        """
        seen_indices = set()
        unique_rows = []

        for row in rows:
            try:
                data_index = await row.get_attribute('data-index')
                if data_index and data_index not in seen_indices:
                    seen_indices.add(data_index)
                    unique_rows.append(row)
            except Exception:
                # 如果没有 data-index 属性，也加入列表
                unique_rows.append(row)

        return unique_rows

    async def _extract_category(self, row_element) -> Dict[str, Optional[str]]:
        """
        从行元素中提取类目信息

        Args:
            row_element: Playwright 行元素

        Returns:
            Dict[str, Optional[str]]: 包含 category_cn 和 category_ru 的字典
        """
        result = {'category_cn': None, 'category_ru': None}

        # 类目列索引（从0开始）
        # 第0列：复选框，第1列：序号，第2列：商品信息，第3列：类目
        CATEGORY_COLUMN_INDEX = 3

        try:
            # 查找第三个 td 元素（类目列）
            td_elements = await row_element.query_selector_all('td')
            if len(td_elements) <= CATEGORY_COLUMN_INDEX:
                self.logger.warning("⚠️ 未找到足够的 td 元素来提取类目")
                return result

            category_td = td_elements[CATEGORY_COLUMN_INDEX]

            # 提取中文类目
            category_cn_element = await category_td.query_selector('span.category-title')
            if category_cn_element:
                category_cn_text = await category_cn_element.text_content()
                if category_cn_text:
                    result['category_cn'] = category_cn_text.strip()

            # 提取俄文类目
            category_ru_element = await category_td.query_selector('span.text-muted')
            if category_ru_element:
                category_ru_text = await category_ru_element.text_content()
                if category_ru_text:
                    result['category_ru'] = category_ru_text.strip()

            if result['category_cn'] or result['category_ru']:
                self.logger.debug(f"✅ 类目提取成功: 中文={result['category_cn']}, 俄文={result['category_ru']}")
            else:
                self.logger.warning("⚠️ 未能提取到类目信息")

        except Exception as e:
            self.logger.error(f"❌ 类目提取失败: {e}")

        return result

    async def _extract_listing_date(self, row_element) -> Dict[str, Optional[str]]:
        """
        从行元素中提取上架时间信息

        Args:
            row_element: Playwright 行元素

        Returns:
            Dict[str, Optional[str]]: 包含 listing_date 和 shelf_duration 的字典
        """
        result = {'listing_date': None, 'shelf_duration': None}

        try:
            # 查找所有 td 元素，上架时间在最后一个 td
            td_elements = await row_element.query_selector_all('td')
            if not td_elements:
                self.logger.warning("⚠️ 未找到 td 元素来提取上架时间")
                return result

            # 最后一个 td 包含上架时间
            listing_date_td = td_elements[-1]

            # 获取完整的 HTML 内容以便解析
            inner_html = await listing_date_td.inner_html()

            # 提取日期（格式：2025-06-20）
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', inner_html)
            if date_match:
                result['listing_date'] = date_match.group(1)

            # 提取货架时长（格式：4 个月 或 < 1 个月）
            duration_match = re.search(r'<span[^>]*>([^<]+)</span>', inner_html)
            if duration_match:
                duration_text = duration_match.group(1).strip()
                if duration_text and duration_text != '':
                    result['shelf_duration'] = duration_text

            if result['listing_date'] or result['shelf_duration']:
                self.logger.debug(f"✅ 上架时间提取成功: 日期={result['listing_date']}, 时长={result['shelf_duration']}")
            else:
                self.logger.warning("⚠️ 未能提取到上架时间信息")

        except Exception as e:
            self.logger.error(f"❌ 上架时间提取失败: {e}")

        return result

    async def _extract_product_sales_volume(self, row_element) -> Optional[int]:
        """
        从行元素中提取商品销量信息

        Args:
            row_element: Playwright 行元素

        Returns:
            Optional[int]: 销量数值，如果提取失败返回 None
        """
        # 销量列索引（从0开始，第5列）
        SALES_VOLUME_COLUMN_INDEX = 4

        try:
            # 查找所有 td 元素
            td_elements = await row_element.query_selector_all('td')
            if len(td_elements) <= SALES_VOLUME_COLUMN_INDEX:
                self.logger.warning("⚠️ 未找到足够的 td 元素来提取销量")
                return None

            # 销量在第5个 td（索引4）
            sales_td = td_elements[SALES_VOLUME_COLUMN_INDEX]

            # 获取文本内容
            sales_text = await sales_td.text_content()
            if not sales_text:
                self.logger.warning("⚠️ 销量 td 元素为空")
                return None

            # 提取数字（只提取第一行的数字，忽略增长率）
            lines = sales_text.strip().split('\n')
            if lines:
                first_line = lines[0].strip()
                # 提取纯数字
                sales_match = re.search(r'^(\d+)', first_line)
                if sales_match:
                    sales_volume = int(sales_match.group(1))
                    self.logger.debug(f"✅ 销量提取成功: {sales_volume}")
                    return sales_volume

            self.logger.warning(f"⚠️ 未能从文本中提取销量: {sales_text}")
            return None

        except Exception as e:
            self.logger.error(f"❌ 销量提取失败: {e}")
            return None

    async def _extract_weight(self, row_element) -> Optional[float]:
        """
        从行元素中提取商品重量信息

        Args:
            row_element: Playwright 行元素

        Returns:
            Optional[float]: 重量数值（克），如果提取失败返回 None
        """
        try:
            # 查找所有 td 元素
            td_elements = await row_element.query_selector_all('td')

            # 重量在倒数第二列
            if len(td_elements) < 2:
                self.logger.warning("⚠️ 未找到足够的 td 元素来提取重量")
                return None

            # 倒数第二个 td
            weight_td = td_elements[-2]

            # 获取文本内容
            weight_text = await weight_td.text_content()
            if not weight_text:
                self.logger.warning("⚠️ 重量 td 元素为空")
                return None

            # 提取数字和单位（格式：161 g 或 1.5 kg）
            weight_text = weight_text.strip()
            weight_match = re.search(r'([\d.]+)\s*(g|kg)', weight_text, re.IGNORECASE)

            if weight_match:
                value = float(weight_match.group(1))
                unit = weight_match.group(2).lower()

                # 统一转换为克
                if unit == 'kg':
                    weight_grams = value * 1000
                else:  # g
                    weight_grams = value

                self.logger.debug(f"✅ 重量提取成功: {weight_grams}g (原始: {weight_text})")
                return weight_grams

            self.logger.warning(f"⚠️ 未能从文本中提取重量: {weight_text}")
            return None

        except Exception as e:
            self.logger.error(f"❌ 重量提取失败: {e}")
            return None

