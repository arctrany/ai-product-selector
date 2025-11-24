"""
Seerfar平台抓取器

负责从Seerfar平台抓取OZON店铺的销售数据和商品信息。
基于现代化的Playwright浏览器服务。
"""

import time
from typing import Dict, Any, List, Optional, Callable

from .base_scraper import BaseScraper
from .global_browser_singleton import get_global_browser_service
from common.models.scraping_result import ScrapingResult
from common.utils.wait_utils import WaitUtils
from common.utils.scraping_utils import ScrapingUtils
from common.utils.sales_data_utils import extract_sales_data_generic
from common.config.seerfar_selectors import SeerfarSelectors, get_seerfar_selector, SEERFAR_SELECTORS
# 接口导入已移除，直接继承BaseScraper


class SeerfarScraper(BaseScraper):
    """
    Seerfar平台抓取器

    实现IStoreScraper接口，提供标准化的店铺数据抓取功能
    """

    def __init__(self, selectors_config: Optional[SeerfarSelectors] = None):
        """初始化Seerfar抓取器"""
        super().__init__()
        import logging
        from common.config.base_config import get_config

        # 🔧 重构：使用新的配置系统
        self.selectors_config = selectors_config or SEERFAR_SELECTORS
        # 🔧 修复：config应该是系统配置对象，包含dryrun等系统级参数
        self.config = get_config()  # 获取包含dryrun属性的系统配置
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 🔧 重构：使用配置文件中的URL配置（符合架构分离原则）
        self.base_url = self.config.browser.seerfar_base_url
        self.store_detail_path = self.config.browser.seerfar_store_detail_path

        # 使用全局浏览器服务
        self.browser_service = get_global_browser_service()
        
        # 🔧 重构：初始化统一工具类
        self.wait_utils = WaitUtils(self.browser_service, self.logger)
        self.scraping_utils = ScrapingUtils(self.logger)

    def scrape_store_sales_data(self,
                               store_id: str,
                               period_days: int = 30,
                               options: Optional[Dict[str, Any]] = None) -> ScrapingResult:
        """
        抓取店铺销售数据（标准接口实现）

        Args:
            store_id: 店铺ID
            period_days: 统计天数，默认30天
            options: 抓取选项，可包含store_filter_func等配置

        Returns:
            ScrapingResult: 抓取结果，包含销售数据

        Raises:
            NavigationException: 页面导航失败
            DataExtractionException: 数据提取失败
        """
        # 构建店铺详情页URL
        url = f"{self.base_url}{self.store_detail_path}?storeId={store_id}&platform=OZON"

        # dryrun模式下记录入参，但仍执行真实的抓取流程
        if self.config.dryrun:
            self.logger.info(f"🧪 试运行模式 - Seerfar店铺销售数据抓取入参: 店铺ID={store_id}, URL={url}")
            self.logger.info("🧪 试运行模式 - 执行真实的销售数据抓取流程（结果不会保存到文件）")

        # 使用继承的抓取方法
        result = self.scrape_page_data(url, self._extract_sales_data)

        # 从选项中获取过滤函数并应用过滤
        # 注意：需要将字段名转换为统一格式
        store_filter_func = options.get('store_filter_func') if options else None
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

            # 2. 应用店铺过滤（FilterManager已统一处理字段名兼容性）
            if store_filter_func:
                if not store_filter_func(sales_result.data):
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
        """同步提取销售数据 - 使用配置文件中的选择器"""
        sales_data = {}
        try:
            page = browser_service.page
            if not self._validate_page():
                return {'sold_30days': 0, 'sold_count_30days': 0, 'daily_avg_sold': 0}

            self._extract_all_sales_data(page, sales_data)

            if not sales_data:
                sales_data = {'sold_30days': 0, 'sold_count_30days': 0, 'daily_avg_sold': 0}

            return sales_data
        except Exception as e:
            self.logger.error(f"提取销售数据失败: {e}")
            return {'sold_30days': 0, 'sold_count_30days': 0, 'daily_avg_sold': 0}

    def _extract_category_data(self, page, sales_data: Dict[str, Any]):
        """提取类目数据 - 使用配置文件中的选择器"""





    def _extract_all_products_data_js(self, product_rows_selector: str) -> List[Dict[str, Any]]:
        """
        使用 JavaScript evaluate 一次性提取所有商品行数据 - 使用专门的seerfar提取脚本
        """
        try:
            # 🔧 调试：增加详细的调试日志
            self.logger.info(f"🔧 DEBUG: 开始JavaScript提取，选择器: {product_rows_selector}")

            # 🔧 修复：使用专门的seerfar提取脚本，包含完整的OZON URL提取逻辑
            js_script = SEERFAR_SELECTORS.js_scripts['extract_products']
            self.logger.info(f"🔧 DEBUG: JavaScript脚本长度: {len(js_script)}")

            # 🔧 验证浏览器服务状态
            if not self.browser_service:
                self.logger.error("❌ CRITICAL: browser_service 为 None")
                return []

            self.logger.info(f"🔧 DEBUG: 浏览器服务类型: {type(self.browser_service)}")

            # 🔧 架构重构：通过scraping_utils统一执行JavaScript
            # 🔧 修复：支持参数传递，将选择器作为参数传递给JavaScript脚本
            self.logger.info("🔧 DEBUG: 调用 extract_data_with_js...")

            products_data = self.scraping_utils.extract_data_with_js(
                self.browser_service,
                js_script,
                "商品列表数据",
                product_rows_selector  # 传递选择器参数
            )

            self.logger.info(f"🔧 DEBUG: extract_data_with_js 返回结果类型: {type(products_data)}")
            self.logger.info(f"🔧 DEBUG: extract_data_with_js 返回结果: {products_data}")

            if products_data:
                self.logger.info(f"📋 JavaScript 提取到 {len(products_data)} 个商品行")
                return products_data
            else:
                self.logger.warning("⚠️ CRITICAL: products_data 为空或 None")
                return []

        except Exception as e:
            self.logger.error(f"❌ CRITICAL: JavaScript 提取商品数据失败: {e}")
            import traceback
            self.logger.error(f"❌ 异常详情:\n{traceback.format_exc()}")
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

            # 🔧 架构重构：通过scraping_utils统一执行JavaScript
            js_script = SEERFAR_SELECTORS.js_scripts['extract_ozon_url']
            ozon_url = self.scraping_utils.extract_data_with_js(
                self.browser_service, js_script, "OZON URL"
            )
            if not ozon_url:
                self.logger.warning("⚠️ 未找到OZON URL")
                return None

            self.logger.info(f"🔗 提取到OZON URL: {ozon_url}")

            # 直接返回URL，不需要进一步解析
            return ozon_url

        except Exception as e:
            self.logger.error(f"提取 OZON URL 失败: {e}")
            return None



    def _extract_all_sales_data(self, page, sales_data: Dict[str, Any]):
        """一次性提取所有销售数据 - 合并重复的提取逻辑"""
        extraction_configs = [
            ('store_sales_data', 'sales_amount', '销售额', 'sold_30days', '.store-total-revenue', False),
            ('store_sales_data', 'sales_volume', '销量', 'sold_count_30days', '.store-total-sales', True),
            ('store_sales_data', 'daily_avg_sales', '日均销量', 'daily_avg_sold', '.store-daily-sales', False)
        ]

        for config_key, selector_key, desc, result_key, default_selector, is_int in extraction_configs:
            result = extract_sales_data_generic(
                self.browser_service, self.wait_utils, get_seerfar_selector,
                config_key, selector_key, desc, result_key,
                default_selector=default_selector, is_int=is_int,
                logger=self.logger
            )
            if result:
                sales_data.update(result)

        # 日均销量计算后备方案
        if 'daily_avg_sold' not in sales_data and 'sold_count_30days' in sales_data:
            try:
                sales_data['daily_avg_sold'] = sales_data['sold_count_30days'] / 30
                self.logger.debug(f"✅ 日均销量计算成功: {sales_data['daily_avg_sold']}")
            except Exception as e:
                self.logger.error(f"❌ 日均销量计算失败: {e}")



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
            # 🔧 增强错误调试：获取完整的异常信息
            import traceback
            self.logger.error(f"❌ 调用 OzonScraper 失败: {scrape_error}")
            self.logger.error(f"❌ 异常类型: {type(scrape_error)}")
            self.logger.error(f"❌ 完整异常详情:\n{traceback.format_exc()}")
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



    def _extract_category(self, row_element) -> Dict[str, Optional[str]]:
        """从行元素中提取类目信息"""
        # 🔧 重构：使用外部化的JavaScript脚本
        js_script = SEERFAR_SELECTORS.js_scripts['extract_category']
        category_index = SEERFAR_SELECTORS.column_indexes['category']

        try:
            # 🔧 架构重构：通过scraping_utils统一执行JavaScript
            result = self.scraping_utils.extract_data_with_js(
                self.browser_service,
                f"({js_script})({category_index})",
                "商品类目"
            )
            return result or {'category_cn': None, 'category_ru': None}
        except Exception as e:
            self.logger.error(f"❌ 类目提取失败: {e}")
            return {'category_cn': None, 'category_ru': None}

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
            # 🔧 架构重构：通过scraping_utils统一执行JavaScript
            js_script = SEERFAR_SELECTORS.js_scripts['extract_listing_date']
            date_data = self.scraping_utils.extract_data_with_js(
                self.browser_service, js_script, "上架时间"
            )
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
            # 🔧 架构重构：通过scraping_utils统一执行JavaScript
            js_script = SEERFAR_SELECTORS.js_scripts['extract_sales_volume']
            # 调用外部脚本，传入销量列索引作为参数
            sales_volume = self.scraping_utils.extract_data_with_js(
                self.browser_service,
                f"({js_script})({sales_volume_column_index})",
                "商品销量"
            )
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
            # 🔧 架构重构：通过scraping_utils统一执行JavaScript
            js_script = SEERFAR_SELECTORS.js_scripts['extract_weight']
            weight_grams = self.scraping_utils.extract_data_with_js(
                self.browser_service, js_script, "商品重量"
            )
            if weight_grams is not None:
                self.logger.debug(f"✅ 重量提取成功: {weight_grams}g")
                return weight_grams
            else:
                self.logger.warning("⚠️ 未能提取到重量信息")
                return None



        except Exception as e:
            self.logger.error(f"❌ 重量提取失败: {e}")
            return None

    def scrape_store_info(self,
                         store_id: str,
                         include_products: bool = True,
                         max_products: Optional[int] = None,
                         options: Optional[Dict[str, Any]] = None) -> ScrapingResult:
        """
        抓取店铺基本信息（标准接口实现）

        Args:
            store_id: 店铺ID
            include_products: 是否包含商品信息
            max_products: 最大商品数量
            options: 抓取选项

        Returns:
            ScrapingResult: 店铺信息抓取结果

        Raises:
            NavigationException: 页面导航失败
            DataExtractionException: 数据提取失败
        """
        try:
            # 简化实现：直接调用核心scrape方法，避免复杂依赖
            return self.scrape(
                store_id=store_id,
                include_products=include_products,
                max_products=max_products,
                product_filter_func=options.get('product_filter_func') if options else None,
                store_filter_func=options.get('store_filter_func') if options else None
            )

        except Exception as e:
            return ScrapingResult(
                success=False,
                data={},
                error_message=f"店铺信息抓取失败: {str(e)}"
            )

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
            page_content = self.get_page_content()
            if not page_content:
                return {}

            # 使用默认的销售数据提取逻辑
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_content, 'html.parser')

            extracted_data = {}

            # 提取销售额、销量等关键指标
            sales_data = {}
            self._extract_sales_amount(None, sales_data)
            self._extract_sales_volume(None, sales_data)
            self._extract_daily_avg_sales(None, sales_data)

            extracted_data.update(sales_data)

            return extracted_data

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

            # 验证关键字段
            required_fields = ['sold_30days', 'sold_count_30days']
            for field in required_fields:
                if field in data:
                    value = data[field]
                    if value is not None and value >= 0:
                        continue
                    else:
                        self.logger.warning(f"字段 {field} 值无效: {value}")
                        return False

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
                'scraper_name': 'SeerfarScraper',
                'status': 'healthy',
                'browser_service_available': self.browser_service is not None,
                'last_operation_time': getattr(self, '_last_operation_time', None),
                'total_operations': getattr(self, '_operation_count', 0)
            }

            # 检查浏览器服务状态
            if self.browser_service:
                try:
                    # 🔧 架构重构：通过scraping_utils统一执行JavaScript
                    js_script = SEERFAR_SELECTORS.js_scripts['get_page_url']
                    page_url = self.scraping_utils.extract_data_with_js(
                        self.browser_service, js_script, "页面URL"
                    )
                    status['browser_responsive'] = page_url is not None
                    status['current_url'] = page_url
                except:
                    status['browser_responsive'] = False
                    status['status'] = 'degraded'
            else:
                status['status'] = 'unavailable'
                status['browser_responsive'] = False

            return status

        except Exception as e:
            return {
                'scraper_name': 'SeerfarScraper',
                'status': 'error',
                'error': str(e)
            }