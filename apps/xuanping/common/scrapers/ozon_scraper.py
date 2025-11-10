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


class OzonScraper:
    """OZON平台抓取器 - 基于browser_service架构"""
    
    def __init__(self, config: Optional[GoodStoreSelectorConfig] = None):
        """初始化OZON抓取器"""
        self.config = config or GoodStoreSelectorConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.base_url = self.config.scraping.ozon_base_url
        
        # 创建浏览器服务
        self.browser_service = XuanpingBrowserServiceSync()

        # 创建跟卖抓取器
        self.competitor_scraper = CompetitorScraper()

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
                    # 等待页面加载
                    await asyncio.sleep(2)

                    # 获取页面内容
                    page_content = await browser_service.get_page_content()
                    if not page_content:
                        self.logger.error("未能获取页面内容")
                        return {}

                    # 解析价格信息 - 修复：改为同步调用
                    price_data = self._extract_price_data_from_content_sync(page_content)

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
    
    def scrape_competitor_stores(self, product_url: str, max_competitors: int = 15) -> ScrapingResult:
        """
        抓取跟卖店铺信息

        Args:
            product_url: 商品URL
            max_competitors: 最大跟卖店铺数量，默认15个（原默认10个）
            
        Returns:
            ScrapingResult: 抓取结果，包含跟卖店铺信息
        """
        start_time = time.time()
        
        try:
            async def extract_competitor_data(browser_service):
                """异步提取跟卖店铺数据"""
                try:
                    # 等待页面加载
                    await asyncio.sleep(2)
                    
                    # 尝试打开跟卖浮层
                    await self._open_competitor_popup_async(browser_service)
                    
                    # 获取页面内容
                    page_content = await browser_service.get_page_content()
                    
                    # 解析跟卖店铺信息 - 修复：使用CompetitorScraper
                    competitors = await self.competitor_scraper.extract_competitors_from_content(page_content, max_competitors)
                    
                    return {'competitors': competitors, 'total_count': len(competitors)}
                    
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
                'price_data': price_result.data
            }
            
            # 如果需要，抓取跟卖店铺信息
            if include_competitors:
                competitors_result = self.scrape_competitor_stores(product_url)
                if competitors_result.success:
                    result_data['competitors'] = competitors_result.data['competitors']
                else:
                    self.logger.warning(f"抓取跟卖店铺信息失败: {competitors_result.error_message}")
                    result_data['competitors'] = []
            
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

    # 价格选择器配置 - 修正：只提取商品本身价格，排除跟卖价格
    PRICE_SELECTORS = [
        ("[data-widget='webPrice'] .tsHeadline500Medium", "green"),  # 修正：中等字体通常是绿标
        ("[data-widget='webPrice'] .tsHeadline600Large", "black"),   # 修正：大字体通常是黑标
        ("[data-widget='webPrice'] span", "auto"),                   # 🔧 限制在webPrice容器内，避免跟卖价格
        # 🚫 删除过于宽泛的选择器，避免误提取跟卖价格
        # (".b5v3 span", "auto"),                                   # 太宽泛，会匹配跟卖价格
        # ("[class*='price'] span", "auto"),                        # 太宽泛，会匹配跟卖价格
        # ("[data-test-id*='price'] span", "auto"),                 # 太宽泛，会匹配跟卖价格
    ]

    # 图片选择器配置 - 统一配置避免重复
    IMAGE_SELECTORS = [
        "#layoutPage > div:nth-child(1) > div:nth-child(3) > div:nth-child(3) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div > div > div > div:nth-child(1) > div > div > div:nth-child(1) > div:nth-child(1) > div > div > div:nth-child(2) > div > div > div > img",
        "[class*='pdp_y3']",
        "[class*='b95_3_3-a']",
        "img[src*='multimedia']",
        "img[src*='ozone.ru']"
    ]

    def _extract_price_data_core(self, soup, is_async=False) -> Dict[str, Any]:
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
            competitor_keywords = ['у других продавцов', 'есть дешевле', 'есть быстрее']

            # 检测跟卖关键词
            for keyword in competitor_keywords:
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
            self.logger.error(f"提取价格数据失败: {e}")
            return {}

    def _extract_basic_prices(self, soup) -> Dict[str, Any]:
        """提取基础价格（绿标、黑标）"""
        prices = {}
        green_price = None
        black_price = None
        auto_prices = []  # 收集auto类型的价格

        for selector, price_type in self.PRICE_SELECTORS:
            if green_price and black_price:
                break

            try:
                elements = soup.select(selector)
                for element in elements:
                    price = self._extract_price_from_element(element)
                    if not price:
                        continue

                    if price_type == "green" and not green_price:
                        green_price = price
                        self.logger.info(f"✅ 绿标价格: {green_price}₽")
                    elif price_type == "black" and not black_price:
                        black_price = price
                        self.logger.info(f"✅ 黑标价格: {black_price}₽")
                    elif price_type == "auto":
                        auto_prices.append((price, element))

                    if green_price and black_price:
                        break
            except Exception:
                continue

        # 🔧 修复：删除智能分配逻辑，OzonScraper只负责原样提取价格
        # auto_prices 中的价格不应该被自动分配，应该由上层业务逻辑处理
        if auto_prices:
            self.logger.debug(f"🔍 发现auto类型价格: {auto_prices}，但不进行自动分配")

        # 🔧 修复：绿标价格不存在时应该为空，不要添加到返回数据中
        if green_price:
            prices['green_price'] = green_price
        if black_price:
            prices['black_price'] = black_price

        return prices

    # 🚫 删除智能价格分配逻辑 - 用户明确要求不要进行任何价格计算！

    # 🚫 删除冗余的跟卖价格提取方法 - 功能已集成到主要价格提取流程中

    def _extract_competitor_price_value(self, soup) -> Optional[float]:
        """提取具体的跟卖价格数值 - 使用用户提供的精确选择器"""
        try:
            # 🎯 使用用户提供的精确跟卖价格选择器
            # 选择器：span.q6b3_0_2-a1
            # 元素：<span class="q6b3_0_2-a1">From 3 800 ₽</span>

            competitor_price_selector = "span.q6b3_0_2-a1"

            self.logger.debug(f"🔍 使用精确跟卖价格选择器: {competitor_price_selector}")

            # 查找跟卖价格元素
            competitor_elements = soup.select(competitor_price_selector)

            for element in competitor_elements:
                text = element.get_text(strip=True)
                self.logger.debug(f"🔍 找到跟卖价格元素文本: '{text}'")

                # 提取价格数值 - 处理 "From 3 800 ₽" 格式
                price = self._extract_price_from_element(element)
                if price and price > 0:
                    self.logger.debug(f"🎯 成功提取跟卖价格: {price}₽")
                    return price

            self.logger.debug("⚠️ 未找到跟卖价格元素")
            return None

        except Exception as e:
            self.logger.error(f"提取跟卖价格失败: {e}")
            return None

    # 🔧 修复：删除重复的跟卖店铺提取逻辑，这些功能应该由 CompetitorScraper 负责
    # 删除了大量重复的跟卖店铺相关代码，职责分离：
    # - OzonScraper: 负责价格提取
    # - CompetitorScraper: 负责跟卖店铺交互和提取

    def _extract_price_from_element(self, element) -> Optional[float]:
        """从元素中提取价格 - 修复价格截断bug"""
        try:
            text = element.get_text(strip=True)
            if '₽' in text or 'руб' in text:
                # 🔧 修复：直接使用 clean_price_string 函数，避免价格截断
                from apps.xuanping.common.models import clean_price_string
                price = clean_price_string(text)
                if price and price > 0:
                    return price
            return None
        except Exception:
            return None

    def _extract_product_image_core(self, soup) -> Optional[str]:
        """
        核心图片提取逻辑 - 统一实现避免重复

        Args:
            soup: BeautifulSoup对象

        Returns:
            str: 商品图片URL，如果提取失败返回None
        """
        try:
            for selector in self.IMAGE_SELECTORS:
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
            self.logger.error(f"提取商品图片失败: {e}")
            return None

    def _extract_price_data_from_content_sync(self, page_content: str) -> Dict[str, Any]:
        """
        从页面内容中提取价格数据 - 同步版本（调用核心逻辑）
        """
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_content, 'html.parser')
            return self._extract_price_data_core(soup, is_async=False)
        except Exception as e:
            self.logger.error(f"从页面内容提取价格数据失败: {e}")
            return {}

    def _extract_product_image_from_content_sync(self, soup) -> Optional[str]:
        """
        从页面内容中提取商品图片地址 - 同步版本（调用核心逻辑）
        """
        return self._extract_product_image_core(soup)

    async def _extract_product_image_from_content(self, soup) -> Optional[str]:
        """
        从页面内容中提取商品图片地址 - 异步版本（调用核心逻辑）
        """
        return self._extract_product_image_core(soup)

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




    
    async def _open_competitor_popup_async(self, browser_service):
        """
        异步打开跟卖店铺浮层
        
        Args:
            browser_service: 浏览器服务
        """
        try:
            page = browser_service.browser_driver.page
            self.logger.info("🔍 开始查找并点击跟卖区域...")

            # 🔧 使用更准确的XPath和CSS选择器，按成功率排序
            # 根据测试日志，最有效的选择器是 "button span div.pdp_t1"
            competitor_button_selectors = [
                # 高成功率选择器
                "button span div.pdp_t1",
                # 基于文本内容的选择器（添加更多变体）
                "button:has-text('Есть дешевле')",
                "div:has-text('Есть дешевле')",
                "button:has-text('Есть быстрее')",
                "div:has-text('Есть быстрее')",
                # 简化版选择器
                "[class*='pdp_t1'] button",
                ".pdp_t1 button",
                "div.pdp_t1 button"
            ]

            clicked = False

            for selector in competitor_button_selectors:
                try:
                    self.logger.debug(f"🔍 尝试使用选择器: {selector}")
                    # 等待元素出现
                    try:
                        if selector.startswith("#layoutPage"):
                            # 使用XPath
                            xpath = "//*[@id='layoutPage']/div[1]/div[3]/div[3]/div[2]/div/div/div[2]/div[3]/div[2]/div/div/div/button/span/div"
                            self.logger.debug(f"🔍 使用XPath: {xpath}")
                            await page.wait_for_selector(f'xpath={xpath}', timeout=3000)
                            element = await page.query_selector(f'xpath={xpath}')
                        else:
                            # 使用CSS选择器
                            self.logger.debug(f"🔍 使用CSS选择器: {selector}")
                            await page.wait_for_selector(selector, timeout=3000)
                            element = await page.query_selector(selector)
                    except Exception as wait_e:
                        self.logger.debug(f"等待元素出现失败: {wait_e}")
                        continue

                    if element:
                        # 检查元素是否可见和可点击
                        is_visible = await element.is_visible()
                        self.logger.debug(f"元素可见性: {is_visible}")
                        if is_visible:
                            # 获取元素文本内容用于日志
                            try:
                                text_content = await element.text_content()
                                self.logger.debug(f"元素文本内容: {text_content[:100] if text_content else 'N/A'}")
                            except:
                                pass

                            # 尝试点击元素
                            await element.click()
                            self.logger.info(f"✅ 成功点击跟卖区域: {selector}")
                            clicked = True

                            # 等待页面响应
                            self.logger.info("⏳ 等待页面响应...")
                            await asyncio.sleep(3)
                            break
                        else:
                            self.logger.debug(f"元素不可见: {selector}")

                except Exception as e:
                    self.logger.debug(f"选择器 {selector} 点击失败: {e}")
                    continue



            if clicked:
                self.logger.info("🎯 跟卖浮层已打开，等待内容加载...")
                await asyncio.sleep(5)  # 增加等待时间确保浮层内容加载
                self.logger.info("✅ 跟卖浮层内容加载完成")
            else:
                self.logger.warning("⚠️ 未能找到或点击跟卖区域，可能页面结构已变化")

        except Exception as e:
            self.logger.error(f"打开跟卖店铺浮层失败: {e}")

    def close(self):
        """
        关闭抓取器，清理资源
        """
        try:
            if hasattr(self, 'browser_service') and self.browser_service:
                self.browser_service.close()
                self.logger.info("🔒 OzonScraper 已关闭")
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




    

    




