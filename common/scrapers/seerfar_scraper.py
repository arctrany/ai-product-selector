"""
Seerfar平台抓取器

负责从Seerfar平台抓取OZON店铺的销售数据和商品信息。
基于现代化的Playwright浏览器服务。
"""

import time
import re
from typing import Dict, Any, List, Optional, Callable

from .xuanping_browser_service import XuanpingBrowserServiceSync
from ..models import ScrapingResult
from common.config import GoodStoreSelectorConfig
from common.config.seerfar_selectors import get_seerfar_selector


class SeerfarScraper:
    """Seerfar平台抓取器"""

    def __init__(self, config: Optional[GoodStoreSelectorConfig] = None):
        """初始化Seerfar抓取器"""
        from common.config import get_config
        import logging

        self.config = config or get_config()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.base_url = self.config.scraping.seerfar_base_url
        self.store_detail_path = self.config.scraping.seerfar_store_detail_path

        # 创建浏览器服务
        self.browser_service = XuanpingBrowserServiceSync()

    def scrape_store_sales_data(self, store_id: str, filter_func=None) -> ScrapingResult:
        """
        抓取店铺销售数据

        Args:
            store_id: 店铺ID
            filter_func: 过滤函数，用于筛选店铺

        Returns:
            ScrapingResult: 抓取结果，包含销售数据
        """
        # 构建店铺详情页URL
        url = f"{self.base_url}{self.store_detail_path}?storeId={store_id}&platform=OZON"

        # dryrun模式下记录入参，但仍执行真实的抓取流程
        if self.config.dryrun:
            self.logger.info(f"🧪 试运行模式 - Seerfar店铺销售数据抓取入参: 店铺ID={store_id}, URL={url}")
            self.logger.info("🧪 试运行模式 - 执行真实的销售数据抓取流程（结果不会保存到文件）")

        # 使用浏览器服务抓取数据
        result = self.browser_service.scrape_page_data(url, self._extract_sales_data_async)

        # 如果提供了过滤函数，则应用过滤
        if result.success and filter_func and result.data:
            if not filter_func(result.data):
                self.logger.info(f"店铺{store_id}不符合筛选条件")
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message="店铺不符合筛选条件",
                    execution_time=result.execution_time
                )

        return result

    def scrape_store_products(self, store_id: str, max_products: Optional[int] = None, filter_func: Optional[Callable[[Dict[str, Any]], bool]] = None) -> ScrapingResult:
        """
        抓取店铺商品列表

        Args:
            store_id: 店铺ID
            max_products: 最大抓取商品数量
            filter_func: 商品过滤函数，接受商品数据字典，返回布尔值

        Returns:
            ScrapingResult: 抓取结果，包含商品列表
        """
        max_products = max_products or self.config.store_filter.max_products_to_check

        # 构建店铺详情页URL
        url = f"{self.base_url}{self.store_detail_path}?storeId={store_id}&platform=OZON"

        # dryrun模式下记录入参，但仍执行真实的抓取流程
        if self.config.dryrun:
            self.logger.info(f"🧪 试运行模式 - Seerfar店铺商品抓取入参: 店铺ID={store_id}, "
                             f"最大商品数={max_products}, URL={url}")
            self.logger.info("🧪 试运行模式 - 执行真实的商品抓取流程（结果不会保存到文件）")

        # 创建提取函数
        async def extract_products(browser_service):
            products = await self._extract_products_list_async(browser_service, max_products)

            # 如果提供了过滤函数，则应用过滤
            if filter_func and products:
                filtered_products = [p for p in products if filter_func(p)]
                self.logger.info(f"商品过滤完成，原始数量: {len(products)}, 过滤后数量: {len(filtered_products)}")
                products = filtered_products

            return {'products': products, 'total_count': len(products)}

        # 使用浏览器服务抓取数据
        return self.browser_service.scrape_page_data(url, extract_products)

    def scrape(self, store_id: str, include_products: bool = True, **kwargs) -> ScrapingResult:
        """
        综合抓取店铺信息
        
        Args:
            store_id: 店铺ID
            include_products: 是否包含商品信息
            **kwargs: 其他参数
            
        Returns:
            ScrapingResult: 抓取结果
        """
        start_time = time.time()

        try:
            # 抓取销售数据
            sales_result = self.scrape_store_sales_data(store_id)
            if not sales_result.success:
                return sales_result

            result_data = {
                'store_id': store_id,
                'sales_data': sales_result.data
            }

            # 如果需要，抓取商品信息
            if include_products:
                products_result = self.scrape_store_products(store_id)
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
            # 使用Playwright的页面API进行元素查找
            page = browser_service.browser_driver.page

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
            sales_amount_xpath = get_seerfar_selector('store_sales_data', 'sales_amount')
            if not sales_amount_xpath:
                self.logger.error("❌ 未能找到销售额选择器配置")
                return

            # 等待元素出现
            try:
                await page.wait_for_selector(f'xpath={sales_amount_xpath}', timeout=5000)
            except:
                self.logger.debug("销售额元素等待超时，继续尝试提取")

            element = await page.query_selector(f'xpath={sales_amount_xpath}')
            if element:
                text = await element.text_content()
                if text and text.strip():
                    # 提取数字并转换为销售额
                    number = self._extract_number_from_text(text.strip())
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
            sales_volume_xpath = get_seerfar_selector('store_sales_data', 'sales_volume')
            if not sales_volume_xpath:
                self.logger.error("❌ 未能找到销量选择器配置")
                return

            # 等待元素出现
            try:
                await page.wait_for_selector(f'xpath={sales_volume_xpath}', timeout=5000)
            except:
                self.logger.debug("销量元素等待超时，继续尝试提取")

            element = await page.query_selector(f'xpath={sales_volume_xpath}')
            if element:
                text = await element.text_content()
                if text and text.strip():
                    # 提取数字并转换为销量
                    number = self._extract_number_from_text(text.strip())
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
            daily_avg_xpath = get_seerfar_selector('store_sales_data', 'daily_avg_sales')
            if not daily_avg_xpath:
                self.logger.error("❌ 未能找到日均销量选择器配置")
                return

            # 等待元素出现
            try:
                await page.wait_for_selector(f'xpath={daily_avg_xpath}', timeout=5000)
            except:
                self.logger.debug("日均销量元素等待超时，继续尝试提取")

            element = await page.query_selector(f'xpath={daily_avg_xpath}')
            if element:
                text = await element.text_content()
                if text and text.strip():
                    # 提取数字并转换为日均销量
                    number = self._extract_number_from_text(text.strip())
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
                        number = self._extract_number_from_text(text)
                        if number and number > 1000:  # 销售额通常较大
                            sales_data['sold_30days'] = number

                    # 判断是否为销量
                    elif any(keyword in text for keyword in ['销量', '订单', '件数']):
                        number = self._extract_number_from_text(text)
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

    async def _extract_products_list_async(self, browser_service, max_products: int) -> List[Dict[str, Any]]:
        """
        异步提取商品列表
        
        Args:
            browser_service: 浏览器服务实例
            max_products: 最大商品数量
            
        Returns:
            List[Dict[str, Any]]: 商品列表
        """
        products = []

        try:
            page = browser_service.browser_driver.page

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

            # for i, row in enumerate(product_rows[:max_products]):
            #     try:
            #         product_data = await self._extract_product_from_row_async(row)
            #         if product_data:
            #             products.append(product_data)
            #
            #     except Exception as e:
            #         self.logger.warning(f"提取第{i + 1}个商品信息失败: {e}")
            #         continue

            if products:
                self.logger.info(f"成功提取{len(products)}个有效商品信息")
            else:
                self.logger.warning("未提取到有效的商品信息")
            return products

        except Exception as e:
            self.logger.error(f"提取商品列表失败: {e}")
            return []

    async def _extract_product_from_row_async(self, row_element) -> Optional[Dict[str, Any]]:
        """
        异步从行元素中提取商品信息并点击进入OZON详情页

        Args:
            row_element: 行元素

        Returns:
            Dict[str, Any]: 完整的商品信息（包含OZON详情页数据）
        """
        try:
            product_data = {}

            # 简化：直接查找并点击商品图片
            try:
                # 获取页面对象
                page = self.browser_service.browser_driver.page

                # 从配置文件获取选择器
                third_column_selector = get_seerfar_selector('product_list', 'third_column')
                clickable_element_selector = get_seerfar_selector('product_list', 'clickable_element')
                clickable_element_alt_selector = get_seerfar_selector('product_list', 'clickable_element_alt')

                if not third_column_selector or not clickable_element_selector or not clickable_element_alt_selector:
                    self.logger.error("❌ 未能找到商品行元素选择器配置")
                    return None

                # 查找第三列中有onclick事件的元素
                # 根据用户提供的XPath，商品在第三列（td[3]）
                td3_element = await row_element.query_selector(third_column_selector)
                if not td3_element:
                    self.logger.warning("⚠️ 未找到第三列，跳过此商品")
                    return None

                # 查找有onclick事件的可点击元素（优先查找span.avatar）
                clickable_element = await td3_element.query_selector(clickable_element_selector)
                if not clickable_element:
                    # 如果没有onclick，尝试查找其他可点击元素
                    clickable_element = await td3_element.query_selector(clickable_element_alt_selector)
                    if not clickable_element:
                        self.logger.warning("⚠️ 未找到可点击的商品元素，跳过此商品")
                        return None

                # 记录找到的元素类型，便于调试
                element_tag = await clickable_element.evaluate("el => el.tagName")
                element_class = await clickable_element.evaluate("el => el.className")
                self.logger.info(f"🔗 找到可点击元素: {element_tag}.{element_class}")

                # 直接提取onclick中的URL并打开
                onclick_attr = await clickable_element.get_attribute("onclick")
                if onclick_attr and "window.open" in onclick_attr:
                    # 提取URL并在新标签页打开
                    import re
                    url_match = re.search(r"window\.open\('([^']+)'\)", onclick_attr)
                    if url_match:
                        ozon_url = url_match.group(1)
                        self.logger.info(f"打开OZON URL: {ozon_url}")

                        # 性能优化：使用 try-finally 确保页面资源清理
                        new_page = None
                        try:
                            new_page = await page.context.new_page()
                            await new_page.goto(ozon_url)
                            await new_page.wait_for_load_state('domcontentloaded', timeout=5000)

                            # 调用现有的OzonScraper来处理OZON详情页
                            self.logger.info("📊 调用OzonScraper处理OZON商品详情页...")
                            from .ozon_scraper import OzonScraper

                            # 创建OzonScraper实例并提取数据
                            ozon_scraper = OzonScraper(self.config)
                            page_content = await new_page.content()
                            ozon_price_data = await ozon_scraper._extract_price_data_from_content(page_content)
                            ozon_competitor_data = await ozon_scraper._extract_competitor_stores_from_content(
                                page_content, 10)

                            # 合并OZON数据
                            product_data.update(ozon_price_data)
                            if ozon_competitor_data:
                                product_data['competitors'] = ozon_competitor_data

                            self.logger.info(
                                f"✅ OZON数据提取完成: 价格数据={len(ozon_price_data)}项, 跟卖店铺={len(ozon_competitor_data)}个")
                            return product_data

                        finally:
                            # 关键修复：确保页面资源始终被释放
                            if new_page:
                                try:
                                    await new_page.close()
                                except Exception as close_error:
                                    self.logger.warning(f"关闭页面时出错: {close_error}")
                else:
                    self.logger.warning("未找到有效的onclick事件")
                    return None

                # 性能优化：减少不必要的页面等待时间
                await page.wait_for_load_state('domcontentloaded', timeout=2000)

                # 调用现有的OzonScraper来处理OZON详情页
                self.logger.info("📊 调用OzonScraper处理OZON商品详情页...")

                try:
                    from .ozon_scraper import OzonScraper

                    # 创建OzonScraper实例并提取数据
                    # ozon_scraper = OzonScraper(self.config)
                    # page_content = await page.content()
                    # ozon_price_data = await ozon_scraper._extract_price_data_from_content(page_content)
                    # ozon_competitor_data = await ozon_scraper._extract_competitor_stores_from_content(page_content, 10)

                    # 合并OZON数据
                    # product_data.update(ozon_price_data)
                    # if ozon_competitor_data:
                    #     product_data['competitors'] = ozon_competitor_data
                    #
                    # self.logger.info(f"✅ OZON数据提取完成: 价格数据={len(ozon_price_data)}项, 跟卖店铺={len(ozon_competitor_data)}个")

                finally:
                    # 性能优化：确保返回原页面，减少等待时间
                    try:
                        await page.go_back()
                        await page.wait_for_load_state('domcontentloaded', timeout=2000)
                    except Exception as nav_error:
                        self.logger.warning(f"返回原页面时出错: {nav_error}")

            except Exception as e:
                self.logger.error(f"点击商品图片或提取OZON数据失败: {e}")
                return None

            # 生成商品ID
            if not product_data.get('product_id'):
                if product_data.get('image_url'):
                    url_match = re.search(r'/(\d+)', product_data['image_url'])
                    if url_match:
                        product_data['product_id'] = url_match.group(1)
                    else:
                        product_data['product_id'] = str(hash(product_data['image_url']))[:10]
                else:
                    product_data['product_id'] = f"product_{int(time.time())}"

            return product_data if product_data else None

        except Exception as e:
            self.logger.error(f"提取商品信息失败: {e}")
            return None

    def _extract_number_from_text(self, text: str) -> Optional[float]:
        """
        从文本中提取数字
        
        Args:
            text: 包含数字的文本
            
        Returns:
            float: 提取的数字，如果提取失败返回None
        """
        if not text:
            return None

        # 移除常见的非数字字符
        cleaned_text = re.sub(r'[^\d.,\-+]', '', text.replace(',', '').replace(' ', ''))

        try:
            # 尝试转换为浮点数
            return float(cleaned_text)
        except (ValueError, TypeError):
            # 尝试提取第一个数字
            numbers = re.findall(r'-?\d+\.?\d*', text)
            if numbers:
                try:
                    return float(numbers[0])
                except (ValueError, TypeError):
                    pass

            return None

    def close(self):
        """关闭抓取器"""
        if hasattr(self, 'browser_service'):
            self.browser_service.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
