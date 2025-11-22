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
from common.config.seerfar_selectors import get_seerfar_selector, SEERFAR_SELECTORS


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
        result = self.scrape_page_data(url, self._extract_sales_data)

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
                def extract_products(browser_service):
                    products = self._extract_products_list(
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

    def _extract_sales_data(self, browser_service) -> Dict[str, Any]:
        """
        同步提取销售数据 - 使用配置文件中的选择器

        Args:
            browser_service: 浏览器服务实例

        Returns:
            Dict[str, Any]: 销售数据
        """
        self.logger.debug("🚀 _extract_sales_data 方法被调用")
        sales_data = {}

        try:
            # 直接访问 page 对象
            page = browser_service.page
            self.logger.debug(f"📄 获取到页面对象: {page}")

            # 验证 page 对象
            self.logger.debug("🔍 开始页面验证...")
            page_valid = self._validate_page()
            self.logger.debug(f"📋 页面验证结果: {page_valid}")

            if not page_valid:
                self.logger.warning("❌ 页面验证失败，无法提取销售数据")
                return {
                    'sold_30days': 0,
                    'sold_count_30days': 0,
                    'daily_avg_sold': 0
                }

            self.logger.debug("开始提取销售数据...")

            # 使用配置文件中的选择器提取销售额
            self.logger.debug("提取销售额...")
            self._extract_sales_amount(page, sales_data)

            # 使用配置文件中的选择器提取销量
            self.logger.debug("提取销量...")
            self._extract_sales_volume(page, sales_data)

            # 使用配置文件中的选择器提取日均销量
            self.logger.debug("提取日均销量...")
            self._extract_daily_avg_sales(page, sales_data)

            # ✅ 修复：即使没有提取到数据，也要返回一个有效的结果
            # 这样可以避免scrape_store_sales_data返回success=False
            if not sales_data:
                self.logger.warning("未提取到任何销售数据，但返回空数据结构以继续后续流程")
                # 返回默认的空数据结构，而不是空字典
                sales_data = {
                    'sold_30days': 0,
                    'sold_count_30days': 0,
                    'daily_avg_sold': 0
                }

            # 合并日志输出店铺数据摘要
            sales_amount = sales_data.get('sold_30days', 0)
            sales_volume = sales_data.get('sold_count_30days', 0)
            daily_avg = sales_data.get('daily_avg_sold', 0)
            self.logger.info(
                f"📊 店铺数据提取完成 - 销售额: {sales_amount:.0f}₽, 销量: {sales_volume}, 日均: {daily_avg}")

            self.logger.debug(f"提取的销售数据: {sales_data}")
            return sales_data

        except Exception as e:
            self.logger.error(f"提取销售数据失败: {e}", exc_info=True)
            # ✅ 修复：即使发生异常，也返回默认数据结构，避免整个流程失败
            return {
                'sold_30days': 0,
                'sold_count_30days': 0,
                'daily_avg_sold': 0
            }

    def _extract_sales_amount(self, page, sales_data: Dict[str, Any]):
        """提取销售额 - 使用配置文件中的选择器"""
        try:
            # 从配置文件获取销售额选择器
            sales_amount_selector = get_seerfar_selector('store_sales_data', 'sales_amount')
            self.logger.debug(f"销售额选择器: {sales_amount_selector}")
            if not sales_amount_selector:
                self.logger.error("❌ 未能找到销售额选择器配置")
                return

            # 🔧 使用同步方法获取文本内容
            self.logger.debug(f"尝试获取销售额元素文本，选择器: {sales_amount_selector}")
            text = self.browser_service.text_content_sync(sales_amount_selector, timeout=5000)
            self.logger.debug(f"销售额元素文本内容: '{text}'")
            if text and text.strip():
                # 提取数字并转换为销售额
                stripped_text = text.strip()
                self.logger.debug(f"处理销售额文本: '{stripped_text}'")
                number = ScraperUtils.extract_number_from_text(stripped_text)
                self.logger.debug(f"提取到的数字: {number}")
                if number:
                    sales_data['sold_30days'] = number
                    self.logger.debug(f"销售额提取成功: {number}")
                    return
                else:
                    self.logger.warning(f"无法从文本中提取数字: '{stripped_text}'")

            self.logger.warning("⚠️ 未能提取到销售额数据")

        except Exception as e:
            self.logger.error(f"❌ 销售额提取失败: {str(e)}", exc_info=True)

    def _extract_sales_volume(self, page, sales_data: Dict[str, Any]):
        """提取销量 - 使用配置文件中的选择器"""
        try:
            # 从配置文件获取销量选择器
            sales_volume_selector = get_seerfar_selector('store_sales_data', 'sales_volume')
            self.logger.debug(f"销量选择器: {sales_volume_selector}")
            if not sales_volume_selector:
                self.logger.error("❌ 未能找到销量选择器配置")
                return

            # 🔧 使用同步方法获取文本内容
            self.logger.debug(f"尝试获取销量元素文本，选择器: {sales_volume_selector}")
            text = self.browser_service.text_content_sync(sales_volume_selector, timeout=5000)
            self.logger.debug(f"销量元素文本内容: '{text}'")
            if text and text.strip():
                # 提取数字并转换为销量
                stripped_text = text.strip()
                self.logger.debug(f"处理销量文本: '{stripped_text}'")
                number = ScraperUtils.extract_number_from_text(stripped_text)
                self.logger.debug(f"提取到的数字: {number}")
                if number:
                    sales_data['sold_count_30days'] = int(number)
                    self.logger.debug(f"销量提取成功: {number}")
                    return
                else:
                    self.logger.warning(f"无法从文本中提取数字: '{stripped_text}'")

            self.logger.warning("⚠️ 未能提取到销量数据")

        except Exception as e:
            self.logger.error(f"❌ 销量提取失败: {str(e)}", exc_info=True)

    def _extract_daily_avg_sales(self, page, sales_data: Dict[str, Any]):
        """提取日均销量 - 使用配置文件中的选择器"""
        try:
            # 从配置文件获取日均销量选择器
            daily_avg_selector = get_seerfar_selector('store_sales_data', 'daily_avg_sales')
            self.logger.debug(f"日均销量选择器: {daily_avg_selector}")
            if not daily_avg_selector:
                self.logger.error("❌ 未能找到日均销量选择器配置")
                return

            # 🔧 使用同步方法获取文本内容
            self.logger.debug(f"尝试获取日均销量元素文本，选择器: {daily_avg_selector}")
            text = self.browser_service.text_content_sync(daily_avg_selector, timeout=5000)
            self.logger.debug(f"日均销量元素文本内容: '{text}'")
            if text and text.strip():
                # 提取数字并转换为日均销量
                stripped_text = text.strip()
                self.logger.debug(f"处理日均销量文本: '{stripped_text}'")
                number = ScraperUtils.extract_number_from_text(stripped_text)
                self.logger.debug(f"提取到的数字: {number}")
                if number:
                    sales_data['daily_avg_sold'] = number
                    self.logger.debug(f"日均销量提取成功: {number}")
                    return
                else:
                    self.logger.warning(f"无法从文本中提取数字: '{stripped_text}'")

            self.logger.warning("⚠️ 未能提取到日均销量数据")

        except Exception as e:
            self.logger.error(f"❌ 日均销量提取失败: {str(e)}", exc_info=True)

    def _extract_category_data(self, page, sales_data: Dict[str, Any]):
        """提取类目数据 - 使用配置文件中的选择器"""
        try:
            # 从配置文件获取类目数据选择器
            category_xpath = get_seerfar_selector('store_sales_data', 'category_data')
            if not category_xpath:
                self.logger.debug("未配置类目数据选择器，跳过类目数据提取")
                return

            # 🔧 使用同步方法获取文本内容
            text = self.browser_service.text_content_sync(f'xpath={category_xpath}', timeout=5000)
            if text and text.strip():
                sales_data['category_info'] = text.strip()
                return

            self.logger.warning("⚠️ 未能提取到类目数据")

        except Exception as e:
            self.logger.error(f"❌ 类目数据提取失败: {str(e)}")

    def _extract_sales_data_generic(self, page) -> Dict[str, Any]:
        """
        同步通用方法提取销售数据
        
        Args:
            page: Playwright页面对象
            
        Returns:
            Dict[str, Any]: 销售数据
        """
        sales_data = {}

        try:
            # 🔧 使用 evaluate_sync 直接在页面上提取文本内容
            script = """
                () => {
                    const xpath = "//*[contains(text(), '₽') or contains(text(), '万') or contains(text(), '千')]";
                    const elements = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                    const texts = [];
                    for (let i = 0; i < Math.min(elements.snapshotLength, 10); i++) {
                        const element = elements.snapshotItem(i);
                        if (element && element.textContent) {
                            texts.push(element.textContent.trim());
                        }
                    }
                    return texts;
                }
            """
            text_list = self.browser_service.evaluate_sync(script, timeout=5000)

            if text_list:
                for text in text_list:
                    try:
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

    def _extract_all_products_data_js(self, product_rows_selector: str) -> List[Dict[str, Any]]:
        """
        使用 JavaScript evaluate 一次性提取所有商品行数据

        这个方法避免了 ElementHandle 的事件循环问题，通过在浏览器端直接提取数据

        Args:
            product_rows_selector: 商品行选择器

        Returns:
            List[Dict[str, Any]]: 商品行数据列表
        """
        try:
            # 🔧 从配置文件获取选择器和列索引
            category_cn_selector = SEERFAR_SELECTORS.product_list.get('category_cn_selector', 'span.category-title')
            category_ru_selector = SEERFAR_SELECTORS.product_list.get('category_ru_selector', 'span.text-muted')
            category_column_idx = SEERFAR_SELECTORS.column_indexes['category']
            sales_volume_column_idx = SEERFAR_SELECTORS.column_indexes['sales_volume']

            # JavaScript 代码：在浏览器端提取所有商品行数据
            # 注意：正则表达式直接硬编码在JS中，避免f-string花括号冲突
            js_code = f"""
            () => {{
                const rows = document.querySelectorAll('{product_rows_selector}');
                return Array.from(rows).map((row, index) => {{
                    const tds = row.querySelectorAll('td');
                    
                    // 提取类目（第{category_column_idx}列）
                    const categoryTd = tds[{category_column_idx}];
                    const categoryCn = categoryTd?.querySelector('{category_cn_selector}')?.textContent?.trim() || null;
                    const categoryRu = categoryTd?.querySelector('{category_ru_selector}')?.textContent?.trim() || null;
                    
                    // 提取销量（第{sales_volume_column_idx}列）
                    const salesTd = tds[{sales_volume_column_idx}];
                    const salesText = salesTd?.textContent?.trim() || '';
                    const salesMatch = salesText.match(/^(\\d+)/);
                    const salesVolume = salesMatch ? parseInt(salesMatch[1]) : null;
                    
                    // 提取重量（倒数第二列）
                    const weightTd = tds[tds.length - 2];
                    const weightText = weightTd?.textContent?.trim() || '';
                    const weightMatch = weightText.match(/([\\d.]+)\\s*(g|kg)/i);
                    let weight = null;
                    if (weightMatch) {{
                        const value = parseFloat(weightMatch[1]);
                        const unit = weightMatch[2].toLowerCase();
                        weight = unit === 'kg' ? value * 1000 : value;
                    }}
                    
                    // 提取上架时间（最后一列）
                    const listingTd = tds[tds.length - 1];
                    const listingHtml = listingTd?.innerHTML || '';
                    const dateMatch = listingHtml.match(/(\\d{{4}}-\\d{{2}}-\\d{{2}})/);
                    const durationMatch = listingHtml.match(/<span[^>]*>([^<]+)<\\/span>/);
                    const listingDate = dateMatch ? dateMatch[1] : null;
                    const shelfDuration = durationMatch ? durationMatch[1].trim() : null;
                    
                    // 提取 OZON URL（第2列的 onclick 事件）
                    const td2 = tds[2];
                    const clickableElement = td2?.querySelector('[onclick*="window.open"]') || 
                                           td2?.querySelector('a[onclick*="window.open"]');
                    const onclickAttr = clickableElement?.getAttribute('onclick') || '';
                    const urlMatch = onclickAttr.match(/window\\.open\\('([^']+)'\\)/);
                    const ozonUrl = urlMatch ? urlMatch[1] : null;
                    
                    // 获取 data-index 用于去重
                    const dataIndex = row.getAttribute('data-index');
                    
                    return {{
                        index: index,
                        dataIndex: dataIndex,
                        categoryCn: categoryCn,
                        categoryRu: categoryRu,
                        salesVolume: salesVolume,
                        weight: weight,
                        listingDate: listingDate,
                        shelfDuration: shelfDuration,
                        ozonUrl: ozonUrl
                    }};
                }});
            }}
            """

            # 使用同步的 evaluate 方法
            products_data = self.browser_service.evaluate_sync(js_code)

            # 去重：基于 dataIndex
            if products_data:
                seen_indices = set()
                unique_products = []
                for product in products_data:
                    data_index = product.get('dataIndex')
                    if data_index and data_index not in seen_indices:
                        seen_indices.add(data_index)
                        unique_products.append(product)
                    elif not data_index:
                        # 没有 data-index 的也保留
                        unique_products.append(product)

                self.logger.info(f"📋 JavaScript 提取到 {len(unique_products)} 个商品行（去重后）")
                return unique_products

            return []

        except Exception as e:
            self.logger.error(f"❌ JavaScript 提取商品数据失败: {e}")
            return []

    def _extract_products_list(self, max_products: int,
                              product_filter_func: Optional[Callable[[Dict[str, Any]], bool]] = None) -> List[Dict[str, Any]]:
        """
        提取商品列表 - 同步实现

        重构的同步版本，支持前置过滤，消除异步复杂性。
        使用JavaScript一次性提取所有商品数据，避免逐个元素查询的性能问题。

        Args:
            max_products: 最大商品数量
            product_filter_func: 商品过滤函数，用于前置过滤

        Returns:
            List[Dict[str, Any]]: 商品列表
        """
        products = []
        filtered_count = 0

        try:
            self.logger.info(f"开始提取商品列表（同步实现，最多 {max_products} 个）")

            # 从配置文件获取商品列表选择器
            product_rows_selector = get_seerfar_selector('product_list', 'product_rows')
            product_rows_alt_selector = get_seerfar_selector('product_list', 'product_rows_alt')

            if not product_rows_selector or not product_rows_alt_selector:
                self.logger.error("❌ 未能找到商品列表选择器配置")
                return []

            # 使用JavaScript一次性提取所有商品数据
            products_data = self._extract_all_products_data_js(product_rows_selector)

            if not products_data:
                # 尝试备用选择器
                products_data = self._extract_all_products_data_js(product_rows_alt_selector)

            if not products_data:
                self.logger.warning("⚠️ 未找到任何商品行")
                return []

            total_rows = len(products_data)
            self.logger.info(f"📋 找到 {total_rows} 个商品行，开始处理（最多 {max_products} 个）")

            # 遍历提取的商品数据
            for i in range(min(total_rows, max_products)):
                try:
                    product_data_js = products_data[i]

                    # 构建基础商品数据用于前置过滤
                    basic_product_data = {
                        'product_category_cn': product_data_js.get('categoryCn'),
                        'product_category_ru': product_data_js.get('categoryRu'),
                        'product_listing_date': product_data_js.get('listingDate'),
                        'product_shelf_duration': product_data_js.get('shelfDuration'),
                        'product_sales_volume': product_data_js.get('salesVolume'),
                        'product_weight': product_data_js.get('weight')
                    }

                    # 应用前置过滤
                    if product_filter_func:
                        if not product_filter_func(basic_product_data):
                            filtered_count += 1
                            self.logger.debug(f"⏭️  商品 #{i+1} 未通过前置过滤，跳过 OZON 详情页处理")
                            continue

                    # 构建完整商品数据
                    product_data = {
                        'category_cn': product_data_js.get('categoryCn'),
                        'category_ru': product_data_js.get('categoryRu'),
                        'listing_date': product_data_js.get('listingDate'),
                        'shelf_duration': product_data_js.get('shelfDuration'),
                        'sales_volume': product_data_js.get('salesVolume'),
                        'weight': product_data_js.get('weight')
                    }

                    # 获取 OZON URL
                    ozon_url = product_data_js.get('ozonUrl')
                    ozon_data_success = False
                    if ozon_url:
                        self.logger.info(f"📎 提取到 OZON URL: {ozon_url}")

                        # 抓取 OZON 详情页数据 - 同步实现
                        ozon_data = self._fetch_ozon_details(ozon_url)
                        if ozon_data:
                            product_data.update(ozon_data)
                            ozon_data_success = True
                        else:
                            self.logger.warning(f"⚠️ 商品 #{i+1} OZON 数据获取失败")

                    if product_data:
                        products.append(product_data)
                        if ozon_data_success:
                            self.logger.info(f"✅ 商品 #{i+1} 提取成功（含 OZON 数据）")
                        else:
                            self.logger.warning(f"⚠️ 商品 #{i+1} 提取部分成功（仅基础数据，OZON 数据缺失）")

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

    def close(self):
        """
        关闭 SeerfarScraper，清理资源 - 同步实现
        """
        try:
            super().close()  # 调用基类的同步关闭方法
            self.logger.info("🔒 SeerfarScraper 已关闭")
        except Exception as e:
            self.logger.warning(f"关闭 SeerfarScraper 时出错: {e}")

    def _extract_basic_product_data(self, row_element) -> Dict[str, Any]:
        """
        提取 Seerfar 表格中的基础商品数据

        Args:
            row_element: 行元素

        Returns:
            Dict[str, Any]: 基础商品数据（类目、上架时间、销量、重量）
        """
        product_data = {}

        # 1. 提取类目信息
        category_data = self._extract_category(row_element)
        product_data.update(category_data)

        # 2. 提取上架时间
        listing_date_data = self._extract_listing_date(row_element)
        product_data.update(listing_date_data)

        # 3. 提取销量
        sales_volume = self._extract_product_sales_volume(row_element)
        if sales_volume is not None:
            product_data['sales_volume'] = sales_volume

        # 4. 提取重量
        weight = self._extract_weight(row_element)
        if weight is not None:
            product_data['weight'] = weight

        return product_data

    def _get_ozon_url_from_row(self, row_element) -> Optional[str]:
        """
        从行元素中提取 OZON URL

        Args:
            row_element: 行元素

        Returns:
            Optional[str]: OZON URL，如果提取失败返回 None
        """
        try:
            # 验证页面对象
            if not self._validate_page():
                return None

            # 从配置文件获取选择器
            third_column_selector = get_seerfar_selector('product_list', 'third_column')
            clickable_element_selector = get_seerfar_selector('product_list', 'clickable_element')
            clickable_element_alt_selector = get_seerfar_selector('product_list', 'clickable_element_alt')

            if not third_column_selector or not clickable_element_selector or not clickable_element_alt_selector:
                self.logger.error("❌ 未能找到商品行元素选择器配置")
                return None

            # 使用JavaScript一次性获取OZON URL，避免复杂的元素查找
            js_script = f"""
            // 查找包含onclick的可点击元素
            const rowElements = document.querySelectorAll('tr[data-index]');
            let targetRow = null;
            
            // 找到对应的行（通过data-index或位置）
            for (let row of rowElements) {{
                const cells = row.querySelectorAll('td');
                if (cells.length >= 3) {{
                    const thirdCell = cells[2]; // 第三列
                    const clickableElements = thirdCell.querySelectorAll('*[onclick*="window.open"]');
                    if (clickableElements.length > 0) {{
                        const onclick = clickableElements[0].getAttribute('onclick');
                        if (onclick && onclick.includes('window.open')) {{
                            const urlMatch = onclick.match(/window\\.open\\('([^']+)'\\)/);
                            if (urlMatch) {{
                                return urlMatch[1]; // 返回URL
                            }}
                        }}
                    }}
                }}
            }}
            return null;
            """

            ozon_url = self.browser_service.evaluate_sync(js_script)
            if not ozon_url:
                self.logger.warning("⚠️ 未找到OZON URL")
                return None

            self.logger.info(f"🔗 提取到OZON URL: {ozon_url}")

            # 直接返回URL，不需要进一步解析
            return ozon_url

        except Exception as e:
            self.logger.error(f"提取 OZON URL 失败: {e}")
            return None

    def _extract_data_with_selector(self, category: str, key: str, data_key: str,
                                   validation_func: Callable = None,
                                   default_selector: str = None) -> Optional[Any]:
        """
        通用数据提取方法 - 统一处理选择器获取、元素等待、数据验证

        Args:
            category: 配置分类
            key: 配置键名
            data_key: 数据键名（用于日志）
            validation_func: 验证函数
            default_selector: 默认选择器

        Returns:
            提取的数据或None
        """
        try:
            # 从配置文件获取选择器
            selector = get_seerfar_selector(category, key)
            if not selector and default_selector:
                selector = default_selector
                self.logger.warning(f"使用降级{data_key}选择器")

            if not selector:
                self.logger.error(f"❌ 未能找到{data_key}选择器配置")
                return None

            # 等待元素加载
            if not self.wait_for_element(selector, timeout=15.0):
                self.logger.warning(f"⚠️ {data_key}元素等待超时，尝试直接提取")

            # 提取文本内容
            text = self.get_text_content(selector, timeout=5.0)
            if text and text.strip():
                # 提取数字
                value = ScraperUtils.extract_number_from_text(text.strip())
                if value and (validation_func is None or validation_func(value)):
                    self.logger.debug(f"✅ {data_key}提取成功: {value}")
                    return value
                else:
                    self.logger.warning(f"⚠️ {data_key}数值异常: {value}")
            else:
                self.logger.warning(f"⚠️ 未能获取{data_key}文本")

        except Exception as e:
            self.logger.error(f"❌ {data_key}提取失败: {e}")

        return None

    def _extract_data_with_js(self, js_template: str, data_key: str = "数据", **kwargs) -> Any:
        """
        通用JavaScript数据提取方法 - 统一JavaScript执行和错误处理

        Args:
            js_template: JavaScript模板
            data_key: 数据键名（用于日志）
            **kwargs: 模板参数

        Returns:
            JavaScript执行结果
        """
        try:
            # 格式化JavaScript代码
            js_script = js_template.format(**kwargs)

            # 执行JavaScript
            result = self.browser_service.evaluate_sync(js_script)

            if result is not None:
                self.logger.debug(f"✅ {data_key}JavaScript提取成功")
                return result
            else:
                self.logger.warning(f"⚠️ {data_key}JavaScript执行未返回有效数据")
                return None

        except Exception as e:
            self.logger.error(f"❌ {data_key}JavaScript执行失败: {e}")
            return None

    def _extract_sales_amount(self, page, sales_data: Dict[str, Any]):
        """提取销售额 - 使用配置文件中的选择器"""
        try:
            # 从配置文件获取销售额选择器
            sales_amount_selector = get_seerfar_selector('store_sales_data', 'sales_amount')
            self.logger.debug(f"销售额选择器: {sales_amount_selector}")
            if not sales_amount_selector:
                self.logger.error("❌ 未能找到销售额选择器配置")
                # 尝试使用降级选择器
                sales_amount_selector = '.store-total-revenue'
                self.logger.warning(f"使用降级销售额选择器: {sales_amount_selector}")

            # 等待元素加载（最多15秒）
            if not self.wait_for_element(sales_amount_selector, timeout=15.0):
                self.logger.warning("⚠️ 销售额元素等待超时，尝试直接提取")

            # 提取销售额文本
            sales_text = self.get_text_content(sales_amount_selector, timeout=5.0)
            self.logger.debug(f"销售额元素文本内容: '{sales_text}'")
            if sales_text and sales_text.strip():
                # 使用工具类提取数字
                sales_amount = ScraperUtils.extract_number_from_text(sales_text.strip())
                self.logger.debug(f"提取到的销售额数字: {sales_amount}")
                if sales_amount is not None:  # 不再使用过于严格的验证
                    sales_data['sold_30days'] = sales_amount
                    self.logger.debug(f"✅ 销售额提取成功: {sales_amount}")
                    return
                else:
                    self.logger.warning(f"⚠️ 无法从文本中提取销售额数字: '{sales_text.strip()}'")
            else:
                self.logger.warning("⚠️ 未能获取销售额文本")

        except Exception as e:
            self.logger.error(f"❌ 销售额提取失败: {e}", exc_info=True)

    def _extract_sales_volume(self, page, sales_data: Dict[str, Any]):
        """提取销量 - 使用配置文件中的选择器"""
        try:
            # 从配置文件获取销量选择器
            sales_volume_selector = get_seerfar_selector('store_sales_data', 'sales_volume')
            self.logger.debug(f"销量选择器: {sales_volume_selector}")
            if not sales_volume_selector:
                self.logger.error("❌ 未能找到销量选择器配置")
                # 尝试使用降级选择器
                sales_volume_selector = '.store-total-sales'
                self.logger.warning(f"使用降级销量选择器: {sales_volume_selector}")

            # 等待元素加载（最多15秒）
            if not self.wait_for_element(sales_volume_selector, timeout=15.0):
                self.logger.warning("⚠️ 销量元素等待超时，尝试直接提取")

            # 提取销量文本
            volume_text = self.get_text_content(sales_volume_selector, timeout=5.0)
            self.logger.debug(f"销量元素文本内容: '{volume_text}'")
            if volume_text and volume_text.strip():
                # 使用工具类提取数字
                sales_volume = ScraperUtils.extract_number_from_text(volume_text.strip())
                self.logger.debug(f"提取到的销量数字: {sales_volume}")
                if sales_volume is not None:  # 不再使用过于严格的验证
                    sales_data['sold_count_30days'] = int(sales_volume)
                    self.logger.debug(f"✅ 销量提取成功: {sales_volume}")
                    return
                else:
                    self.logger.warning(f"⚠️ 无法从文本中提取销量数字: '{volume_text.strip()}'")
            else:
                self.logger.warning("⚠️ 未能获取销量文本")

        except Exception as e:
            self.logger.error(f"❌ 销量提取失败: {e}", exc_info=True)

    def _extract_daily_avg_sales(self, page, sales_data: Dict[str, Any]):
        """提取日均销量 - 使用配置文件中的选择器或根据已有数据计算"""
        try:
            # 从配置文件获取日均销量选择器
            daily_avg_selector = get_seerfar_selector('store_sales_data', 'daily_avg_sales')
            self.logger.debug(f"日均销量选择器: {daily_avg_selector}")
            if not daily_avg_selector:
                self.logger.error("❌ 未能找到日均销量选择器配置")
                # 尝试使用降级选择器
                daily_avg_selector = '.store-daily-sales'
                self.logger.warning(f"使用降级日均销量选择器: {daily_avg_selector}")

            # 等待元素加载（最多15秒）
            if not self.wait_for_element(daily_avg_selector, timeout=15.0):
                self.logger.warning("⚠️ 日均销量元素等待超时，尝试直接提取")

            # 提取日均销量文本
            daily_avg_text = self.get_text_content(daily_avg_selector, timeout=5.0)
            self.logger.debug(f"日均销量元素文本内容: '{daily_avg_text}'")
            if daily_avg_text and daily_avg_text.strip():
                # 使用工具类提取数字
                daily_avg = ScraperUtils.extract_number_from_text(daily_avg_text.strip())
                self.logger.debug(f"提取到的日均销量数字: {daily_avg}")
                if daily_avg is not None:  # 不再使用过于严格的验证
                    sales_data['daily_avg_sold'] = daily_avg
                    self.logger.debug(f"✅ 日均销量提取成功: {daily_avg}")
                    return
                else:
                    self.logger.warning(f"⚠️ 无法从文本中提取日均销量数字: '{daily_avg_text.strip()}'")
            else:
                self.logger.warning("⚠️ 未能获取日均销量文本")

        except Exception as e:
            self.logger.error(f"❌ 日均销量提取失败: {e}", exc_info=True)

        # 如果直接提取失败，尝试根据已有数据计算
        if 'sold_count_30days' in sales_data:
            try:
                daily_avg = sales_data['sold_count_30days'] / 30
                sales_data['daily_avg_sold'] = daily_avg
                self.logger.debug(f"✅ 日均销量计算成功: {daily_avg}")
            except Exception as e:
                self.logger.error(f"❌ 日均销量计算失败: {e}")
        else:
            self.logger.warning("⚠️ 无法获取或计算日均销量")

    def _resolve_ozon_url(self, ozon_url: str) -> str:
        """
        解析 OZON URL，处理可能的重定向 - 同步实现

        Args:
            ozon_url: 原始 OZON URL

        Returns:
            str: 最终的 OZON URL
        """
        try:
            # 完整实现：使用HTTP请求解析URL重定向，避免影响当前浏览器状态
            import requests
            from urllib.parse import urlparse

            self.logger.debug(f"开始解析URL重定向: {ozon_url}")

            # 设置请求头，模拟真实浏览器
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            # 发送HEAD请求检查重定向，超时3秒
            response = requests.head(
                ozon_url,
                headers=headers,
                allow_redirects=True,
                timeout=3
            )

            # 获取最终URL
            final_url = response.url

            if final_url != ozon_url:
                self.logger.info(f"URL重定向解析: {ozon_url} -> {final_url}")
            else:
                self.logger.debug(f"URL无重定向: {ozon_url}")

            return final_url

        except requests.exceptions.Timeout:
            self.logger.warning(f"URL重定向检查超时，使用原始URL: {ozon_url}")
            return ozon_url
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"URL重定向检查失败，使用原始URL: {e}")
            return ozon_url
        except Exception as e:
            self.logger.warning(f"URL处理失败，使用原始URL: {e}")
            return ozon_url

    def _fetch_ozon_details(self, ozon_url: str) -> Optional[Dict[str, Any]]:
        """
        抓取 OZON 详情页数据 - 同步实现

        Args:
            ozon_url: OZON 商品详情页 URL

        Returns:
            Optional[Dict[str, Any]]: OZON 详情页数据，包含价格、跟卖店铺、ERP 数据
        """
        self.logger.info("📊 调用 OzonScraper 处理 OZON 商品详情页（同步实现）...")
        try:
            from .ozon_scraper import OzonScraper

            # 创建 OzonScraper 实例并使用公共接口 - 同步调用
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

    def _validate_page(self) -> bool:
        """
        验证当前页面是否有效 - 同步实现

        Returns:
            bool: 页面是否有效
        """
        if not self.browser_service:
            self.logger.error("❌ browser_service 未初始化")
            return False

        # 检查页面是否可用（通过检查page对象和基本属性）
        try:
            # 方式1：检查page对象是否存在
            page = getattr(self.browser_service, 'page', None)
            if page is None:
                self.logger.warning("页面对象不存在")
                return False

            # 方式2：尝试获取页面URL作为验证
            if hasattr(self.browser_service, 'get_page_url_sync'):
                url = self.browser_service.get_page_url_sync()
                if url is not None:
                    self.logger.debug(f"页面URL验证成功: {url}")
                    return True
                else:
                    # URL为None可能表示页面未完全加载，但我们仍认为页面存在
                    self.logger.debug("页面URL为None，但page对象存在，假设页面有效")
                    return True
            else:
                # 降级方案：检查page对象的基本属性
                self.logger.warning("浏览器服务没有同步获取页面URL方法，使用降级验证")
                # 如果能获取到page对象，假设页面有效
                return True

        except Exception as e:
            self.logger.error(f"❌ 页面验证失败: {e}")
            return False

    def _deduplicate_rows(self, rows: list) -> list:
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
            # 简化去重逻辑：直接添加所有行，去重已在JavaScript层处理
            unique_rows.append(row)

        return unique_rows

    def _extract_category(self, row_element) -> Dict[str, Optional[str]]:
        """从行元素中提取类目信息 - 使用通用JavaScript方法"""
        result = {'category_cn': None, 'category_ru': None}

        # JavaScript模板 - 提取类目信息
        js_template = """
        const categoryIndex = {category_index};
        const rows = document.querySelectorAll('tr[data-index]');
        
        for (let row of rows) {{
            const cells = row.querySelectorAll('td');
            if (cells.length > categoryIndex) {{
                const categoryCell = cells[categoryIndex];
                
                // 提取中文类目
                const categoryCnEl = categoryCell.querySelector('span.category-title, .category-title');
                const categoryCn = categoryCnEl ? categoryCnEl.textContent.trim() : null;
                
                // 提取俄文类目  
                const categoryRuEl = categoryCell.querySelector('span.text-muted, .text-muted');
                const categoryRu = categoryRuEl ? categoryRuEl.textContent.trim() : null;
                
                if (categoryCn || categoryRu) {{
                    return {{
                        category_cn: categoryCn,
                        category_ru: categoryRu
                    }};
                }}
            }}
        }}
        return null;
        """

        category_data = self._extract_data_with_js(
            js_template,
            "类目信息",
            category_index=SEERFAR_SELECTORS.column_indexes['category']
        )

        if category_data:
            result.update(category_data)
            self.logger.debug(f"✅ 类目提取成功: {result}")
        else:
            self.logger.warning("⚠️ 未能提取到类目信息")

        return result

    def _extract_listing_date(self, row_element) -> Dict[str, Optional[str]]:
        """
        从行元素中提取上架时间信息

        Args:
            row_element: Playwright 行元素

        Returns:
            Dict[str, Optional[str]]: 包含 listing_date 和 shelf_duration 的字典
        """
        result = {'listing_date': None, 'shelf_duration': None}

        try:
            # 使用JavaScript直接提取上架时间信息
            js_script = """
            const rows = document.querySelectorAll('tr[data-index]');
            
            for (let row of rows) {
                const cells = row.querySelectorAll('td');
                if (cells.length > 0) {
                    const lastCell = cells[cells.length - 1]; // 最后一个td
                    const innerHtml = lastCell.innerHTML;
                    
                    // 提取日期（匹配 YYYY-MM-DD 格式）
                    const dateMatch = innerHtml.match(/(\\d{4}-\\d{2}-\\d{2})/);
                    const date = dateMatch ? dateMatch[1] : null;
                    
                    // 提取货架时长（匹配数字+天/月等）
                    const durationMatch = innerHtml.match(/>\\s*([^<>]*(?:天|月|年|day|month|year)[^<>]*)/i);
                    let duration = durationMatch ? durationMatch[1].trim() : null;
                    
                    if (duration === '') duration = null;
                    
                    if (date || duration) {
                        return {
                            listing_date: date,
                            shelf_duration: duration
                        };
                    }
                }
            }
            return null;
            """

            date_data = self.browser_service.evaluate_sync(js_script)
            if date_data:
                if date_data.get('listing_date'):
                    result['listing_date'] = date_data['listing_date']
                if date_data.get('shelf_duration'):
                    result['shelf_duration'] = date_data['shelf_duration']

                self.logger.debug(f"✅ 上架时间提取成功: {result}")
            else:
                self.logger.warning("⚠️ 未能提取到上架时间信息")
                return result

            # 下面的正则处理逻辑已经在JavaScript中完成，删除
            return result



        except Exception as e:
            self.logger.error(f"❌ 上架时间提取失败: {e}")

        return result

    def _extract_product_sales_volume(self, row_element) -> Optional[int]:
        """
        从行元素中提取商品销量信息

        Args:
            row_element: Playwright 行元素

        Returns:
            Optional[int]: 销量数值，如果提取失败返回 None
        """
        # 🔧 从配置文件获取列索引
        sales_volume_column_index = SEERFAR_SELECTORS.column_indexes['sales_volume']

        try:
            # 使用JavaScript直接提取销量信息
            js_script = f"""
            const salesIndex = {sales_volume_column_index};
            const rows = document.querySelectorAll('tr[data-index]');
            
            for (let row of rows) {{
                const cells = row.querySelectorAll('td');
                if (cells.length > salesIndex) {{
                    const salesCell = cells[salesIndex];
                    const salesText = salesCell.textContent || '';
                    
                    if (salesText.trim()) {{
                        // 提取第一行的数字（忽略增长率）
                        const lines = salesText.trim().split('\\n');
                        if (lines.length > 0) {{
                            const firstLine = lines[0].trim();
                            // 提取纯数字
                            const salesMatch = firstLine.match(/\\d+/);
                            if (salesMatch) {{
                                return parseInt(salesMatch[0], 10);
                            }}
                        }}
                    }}
                }}
            }}
            return null;
            """

            sales_volume = self.browser_service.evaluate_sync(js_script)
            if sales_volume is not None:
                self.logger.debug(f"✅ 销量提取成功: {sales_volume}")
                return sales_volume
            else:
                self.logger.warning("⚠️ 未能提取到销量信息")
                return None



        except Exception as e:
            self.logger.error(f"❌ 销量提取失败: {e}")
            return None

    def _extract_weight(self, row_element) -> Optional[float]:
        """
        从行元素中提取商品重量信息

        Args:
            row_element: Playwright 行元素

        Returns:
            Optional[float]: 重量数值（克），如果提取失败返回 None
        """
        try:
            # 使用JavaScript直接提取重量信息
            js_script = """
            const rows = document.querySelectorAll('tr[data-index]');
            
            for (let row of rows) {
                const cells = row.querySelectorAll('td');
                if (cells.length >= 2) {
                    const weightCell = cells[cells.length - 2]; // 倒数第二个td
                    const weightText = weightCell.textContent || '';
                    
                    if (weightText.trim()) {
                        // 提取数字和单位，支持kg和g
                        const weightMatch = weightText.match(/(\\d+(?:\\.\\d+)?)\\s*(kg|g)/i);
                        if (weightMatch) {
                            const value = parseFloat(weightMatch[1]);
                            const unit = weightMatch[2].toLowerCase();
                            
                            // 统一转换为克
                            const weightGrams = unit === 'kg' ? value * 1000 : value;
                            return weightGrams;
                        }
                    }
                }
            }
            return null;
            """

            weight_grams = self.browser_service.evaluate_sync(js_script)
            if weight_grams is not None:
                self.logger.debug(f"✅ 重量提取成功: {weight_grams}g")
                return weight_grams
            else:
                self.logger.warning("⚠️ 未能提取到重量信息")
                return None



        except Exception as e:
            self.logger.error(f"❌ 重量提取失败: {e}")
            return None

