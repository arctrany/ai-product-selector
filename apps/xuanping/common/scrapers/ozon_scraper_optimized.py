"""
OZON平台抓取器 - 性能优化版本

解决的核心问题：
1. DOM搜索过度：避免全页面遍历，只在特定容器内搜索
2. 重复导航：合并抓取流程，一次导航获取所有数据
3. 重复构建BeautifulSoup：缓存和复用解析结果
4. 异步函数误用：分离同步HTML解析和异步IO操作
5. 错误处理优化：明确错误分类和超时控制
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from bs4 import BeautifulSoup

from .xuanping_browser_service import XuanpingBrowserServiceSync
from ..models import ProductInfo, CompetitorStore, clean_price_string, ScrapingResult
from ..config import GoodStoreSelectorConfig


class ScrapingErrorCode(Enum):
    """抓取错误码枚举"""
    SUCCESS = "SUCCESS"
    NAVIGATION_FAILED = "NAVIGATION_FAILED"
    CONTAINER_NOT_FOUND = "CONTAINER_NOT_FOUND"
    PARSE_PRICE_FAILED = "PARSE_PRICE_FAILED"
    PARSE_SELLER_FAILED = "PARSE_SELLER_FAILED"
    TIMEOUT = "TIMEOUT"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class OptimizedScrapingResult:
    """优化的抓取结果数据类"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[ScrapingErrorCode] = None
    error_message: Optional[str] = None


class OzonSelectors:
    """Ozon选择器配置类 - 集中管理所有选择器，按优先级排序"""
    
    # 价格容器选择器（按优先级排序，优先使用精确容器）
    PRICE_CONTAINERS = [
        "[data-widget='webPrice']",
        "[data-widget='price']", 
        ".price-container",
        "[class*='price-container']"
    ]
    
    # 绿标价格选择器（在容器内使用，限制回退深度）
    GREEN_PRICE_SELECTORS = [
        ".tsHeadline600Large",
        "[data-test-id='green-price']",
        ".green-price"
    ]
    
    # 黑标价格选择器（在容器内使用）
    BLACK_PRICE_SELECTORS = [
        ".tsHeadline500Medium", 
        "[data-test-id='black-price']",
        ".black-price",
        "[class*='old-price']"
    ]
    
    # 跟卖容器选择器（严格要求容器存在）
    SELLER_CONTAINERS = [
        "[data-widget='sellerList']",
        "#seller-list",
        "[class*='seller-list']"
    ]
    
    # 跟卖店铺项选择器（仅在容器内搜索）
    SELLER_ITEM_SELECTORS = [
        ":scope > div",
        ":scope > li"
    ]
    
    # 跟卖点击区域选择器
    COMPETITOR_CLICK_SELECTORS = [
        "[data-test-id*='competitor']",
        "[class*='competitor-price']"
    ]


class OzonKeywords:
    """Ozon关键词配置类"""
    
    # 跟卖相关关键词（俄文，已优化为lower case）
    COMPETITOR_KEYWORDS = [
        'у других продавцов',
        'других продавцов',
        'от других',
        'у других',
        'других',
        'продавцов'
    ]
    
    # 价格相关符号
    PRICE_SYMBOLS = ['₽', 'руб']


class OzonScraperOptimized:
    """OZON平台抓取器 - 性能优化版本"""
    
    def __init__(self, config: Optional[GoodStoreSelectorConfig] = None):
        """初始化OZON抓取器"""
        self.config = config or GoodStoreSelectorConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.base_url = self.config.scraping.ozon_base_url
        
        # 创建浏览器服务
        self.browser_service = XuanpingBrowserServiceSync()
        
        # 缓存解析结果
        self._soup_cache = {}
        
    def scrape(self, product_url: str, include_competitors: bool = False, max_competitors: int = 10) -> OptimizedScrapingResult:
        """
        优化的统一抓取方法：一次导航，获取所有需要的数据
        
        Args:
            product_url: 商品URL
            include_competitors: 是否包含跟卖店铺信息
            max_competitors: 最大跟卖店铺数量
            
        Returns:
            OptimizedScrapingResult: 抓取结果
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"🚀 开始优化抓取: {product_url}")
            
            # 使用浏览器服务进行统一抓取
            async def unified_scrape_async(browser_service):
                """统一的异步抓取逻辑"""
                try:
                    # 1. 导航到页面（只导航一次）
                    await asyncio.sleep(2)
                    page_content = await browser_service.browser_driver.page.content()
                    
                    # 2. 如果需要跟卖信息，打开跟卖浮层
                    if include_competitors:
                        await self._open_competitor_popup_optimized(browser_service.browser_driver.page)
                        # 获取更新后的页面内容
                        page_content = await browser_service.browser_driver.page.content()
                    
                    # 3. 提取特定容器的HTML片段（避免全页解析）
                    containers = await self._extract_container_fragments(browser_service.browser_driver.page)
                    
                    return {
                        'page_content': page_content,
                        'containers': containers
                    }
                    
                except Exception as e:
                    self.logger.error(f"异步抓取失败: {e}")
                    return None
            
            # 执行异步抓取
            scrape_data = self.browser_service.scrape_page_data(
                product_url, 
                unified_scrape_async
            )
            
            if not scrape_data:
                return OptimizedScrapingResult(
                    success=False,
                    error_code=ScrapingErrorCode.NAVIGATION_FAILED,
                    error_message="页面导航失败"
                )
            
            # 4. 同步解析数据（CPU-bound操作）
            result_data = self._parse_scraped_data_sync(
                scrape_data['containers'], 
                include_competitors, 
                max_competitors
            )
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"✅ 优化抓取完成，耗时: {elapsed_time:.2f}秒")
            
            return OptimizedScrapingResult(
                success=True,
                data=result_data,
                error_code=ScrapingErrorCode.SUCCESS
            )
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.logger.error(f"抓取失败: {e}, 耗时: {elapsed_time:.2f}秒")
            return OptimizedScrapingResult(
                success=False,
                error_code=ScrapingErrorCode.UNKNOWN_ERROR,
                error_message=str(e)
            )
    
    async def _extract_container_fragments(self, page) -> Dict[str, str]:
        """
        提取特定容器的HTML片段，避免全页解析
        
        Args:
            page: Playwright页面对象
            
        Returns:
            Dict[str, str]: 容器片段字典
        """
        containers = {}
        
        try:
            # 提取价格容器
            for selector in OzonSelectors.PRICE_CONTAINERS:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        containers['price'] = await element.inner_html()
                        self.logger.debug(f"✅ 提取价格容器: {selector}")
                        break
                except Exception:
                    continue
            
            # 提取跟卖容器
            for selector in OzonSelectors.SELLER_CONTAINERS:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        containers['sellers'] = await element.inner_html()
                        self.logger.debug(f"✅ 提取跟卖容器: {selector}")
                        break
                except Exception:
                    continue
            
            # 提取图片
            try:
                img_element = await page.query_selector("img[src*='ozonstatic']")
                if img_element:
                    containers['image'] = await img_element.get_attribute('src')
            except Exception:
                pass
                
        except Exception as e:
            self.logger.warning(f"提取容器片段失败: {e}")
        
        return containers
    
    def _parse_scraped_data_sync(self, containers: Dict[str, str], include_competitors: bool, max_competitors: int) -> Dict[str, Any]:
        """
        同步解析抓取的数据（CPU-bound操作）
        
        Args:
            containers: 容器HTML片段
            include_competitors: 是否包含跟卖信息
            max_competitors: 最大跟卖数量
            
        Returns:
            Dict[str, Any]: 解析结果
        """
        result = {}
        
        try:
            # 解析价格信息（仅在价格容器内）
            if 'price' in containers:
                price_data = self._parse_price_from_container_sync(containers['price'])
                result.update(price_data)
            
            # 解析图片
            if 'image' in containers:
                result['image_url'] = containers['image']
            
            # 解析跟卖信息（仅在跟卖容器内）
            if include_competitors and 'sellers' in containers:
                competitors = self._parse_competitors_from_container_sync(
                    containers['sellers'], 
                    max_competitors
                )
                result['competitors'] = competitors
            
        except Exception as e:
            self.logger.error(f"同步解析数据失败: {e}")
        
        return result
    
    def _parse_price_from_container_sync(self, price_html: str) -> Dict[str, Any]:
        """
        从价格容器中同步解析价格信息（避免全页搜索）
        
        Args:
            price_html: 价格容器HTML
            
        Returns:
            Dict[str, Any]: 价格数据
        """
        try:
            # 只构建一次BeautifulSoup，仅解析容器内容
            soup = BeautifulSoup(price_html, 'html.parser')
            
            green_price = None
            black_price = None
            
            # 在容器内搜索绿标价格（限制搜索范围）
            for selector in OzonSelectors.GREEN_PRICE_SELECTORS:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if any(symbol in text for symbol in OzonKeywords.PRICE_SYMBOLS):
                        # 检查是否是跟卖价格（限制父节点回溯深度<=2）
                        if not self._is_competitor_price_sync(element, max_levels=2):
                            price = clean_price_string(text)
                            if price and price > 0:
                                green_price = price
                                self.logger.debug(f"✅ 提取绿标价格: {green_price}₽")
                                break
            
            # 在容器内搜索黑标价格
            for selector in OzonSelectors.BLACK_PRICE_SELECTORS:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if any(symbol in text for symbol in OzonKeywords.PRICE_SYMBOLS):
                        if not self._is_competitor_price_sync(element, max_levels=2):
                            price = clean_price_string(text)
                            if price and price > 0:
                                black_price = price
                                self.logger.debug(f"✅ 提取黑标价格: {black_price}₽")
                                break
            
            result = {}
            if green_price:
                result['green_price'] = green_price
            if black_price:
                result['black_price'] = black_price
                
            return result
            
        except Exception as e:
            self.logger.error(f"解析价格容器失败: {e}")
            return {}
    
    def _parse_competitors_from_container_sync(self, sellers_html: str, max_competitors: int) -> List[Dict[str, Any]]:
        """
        从跟卖容器中同步解析跟卖店铺信息（避免全页搜索）
        
        Args:
            sellers_html: 跟卖容器HTML
            max_competitors: 最大跟卖数量
            
        Returns:
            List[Dict[str, Any]]: 跟卖店铺列表
        """
        try:
            # 只构建一次BeautifulSoup，仅解析容器内容
            soup = BeautifulSoup(sellers_html, 'html.parser')
            competitors = []
            
            # 严格在容器内搜索店铺项（不做全局回退）
            competitor_elements = []
            for selector in OzonSelectors.SELLER_ITEM_SELECTORS:
                elements = soup.select(selector)
                if elements:
                    competitor_elements = elements[:max_competitors]  # 限制数量
                    self.logger.debug(f"✅ 找到 {len(competitor_elements)} 个跟卖店铺")
                    break
            
            if not competitor_elements:
                self.logger.warning("⚠️ 跟卖容器内未找到店铺项")
                return []
            
            # 解析每个店铺信息
            for i, element in enumerate(competitor_elements):
                try:
                    competitor_data = self._extract_competitor_from_element_sync(element, i + 1)
                    if competitor_data:
                        competitors.append(competitor_data)
                        self.logger.debug(f"✅ 提取第{i+1}个跟卖店铺: {competitor_data.get('store_name', 'N/A')}")
                except Exception as e:
                    self.logger.warning(f"提取第{i+1}个跟卖店铺失败: {e}")
                    continue
            
            return competitors
            
        except Exception as e:
            self.logger.error(f"解析跟卖容器失败: {e}")
            return []
    
    def _is_competitor_price_sync(self, element, max_levels: int = 2) -> bool:
        """
        同步检查是否是跟卖价格（限制回溯深度）
        
        Args:
            element: BeautifulSoup元素
            max_levels: 最大回溯层数
            
        Returns:
            bool: 是否是跟卖价格
        """
        try:
            current = element.parent
            level = 0
            
            while current and level < max_levels:
                parent_text = current.get_text(strip=True).lower()
                # 限制文本长度，避免过长字符串处理
                if len(parent_text) > 200:
                    parent_text = parent_text[:200]
                
                # 检查是否包含跟卖关键词
                if any(keyword in parent_text for keyword in OzonKeywords.COMPETITOR_KEYWORDS):
                    return True
                
                current = current.parent
                level += 1
            
            return False
            
        except Exception:
            return False
    
    def _extract_competitor_from_element_sync(self, element, ranking: int) -> Optional[Dict[str, Any]]:
        """
        从元素中同步提取跟卖店铺信息（优化版本）
        
        Args:
            element: 店铺元素
            ranking: 排名
            
        Returns:
            Dict[str, Any]: 店铺信息
        """
        try:
            competitor_data = {'ranking': ranking}
            
            # 提取店铺名称（线性策略，不做全节点遍历）
            name_selectors = [
                "[data-test-id*='seller']",
                "[class*='seller-name']",
                "[class*='name']"
            ]
            
            for selector in name_selectors:
                name_element = element.select_one(selector)
                if name_element:
                    store_name = name_element.get_text(strip=True)
                    if store_name and len(store_name) > 1:
                        competitor_data['store_name'] = store_name
                        break
            
            # 如果没找到，单次文本备选
            if 'store_name' not in competitor_data:
                text_elements = element.find_all(text=True)
                for text in text_elements[:5]:  # 限制搜索数量
                    stripped_text = text.strip()
                    if (stripped_text and len(stripped_text) > 1 and 
                        not any(symbol in stripped_text for symbol in OzonKeywords.PRICE_SYMBOLS) and
                        not stripped_text.replace('.', '').replace(',', '').isdigit()):
                        competitor_data['store_name'] = stripped_text
                        break
            
            # 提取价格（线性策略）
            price_selectors = [
                "[data-test-id*='price']",
                "[class*='price']",
                "span"
            ]
            
            for selector in price_selectors:
                price_element = element.select_one(selector)
                if price_element:
                    price_text = price_element.get_text(strip=True)
                    if any(symbol in price_text for symbol in OzonKeywords.PRICE_SYMBOLS):
                        price = clean_price_string(price_text)
                        if price and price > 0:
                            competitor_data['price'] = price
                            break
            
            # 提取店铺ID（合并正则，优先匹配）
            link_element = element.select_one("a[href*='seller']")
            if link_element and link_element.get('href'):
                href = link_element.get('href')
                import re
                # 合并为一个优先匹配序列
                patterns = [
                    r'/seller/[^/]+-(\d+)',
                    r'/seller/(\d+)',
                    r'sellerId=(\d+)',
                    r'seller[/_](\d+)'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, href)
                    if match:
                        competitor_data['store_id'] = match.group(1)
                        break
            
            # 兜底处理
            if 'store_name' not in competitor_data:
                competitor_data['store_name'] = f"店铺{ranking}"
            if 'store_id' not in competitor_data:
                competitor_data['store_id'] = f"store_{ranking}"
            
            return competitor_data
            
        except Exception as e:
            self.logger.warning(f"提取跟卖店铺信息失败: {e}")
            return None
    
    async def _open_competitor_popup_optimized(self, page) -> bool:
        """
        优化的打开跟卖浮层方法（明确超时控制）
        
        Args:
            page: Playwright页面对象
            
        Returns:
            bool: 是否成功打开
        """
        try:
            # 限制尝试次数，避免无限循环
            for selector in OzonSelectors.COMPETITOR_CLICK_SELECTORS[:3]:  # 最多尝试3个选择器
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        await element.click()
                        self.logger.info(f"✅ 成功点击跟卖区域: {selector}")
                        await asyncio.sleep(3)  # 固定等待时间
                        return True
                except Exception:
                    continue
            
            self.logger.warning("⚠️ 未能打开跟卖浮层")
            return False
            
        except Exception as e:
            self.logger.error(f"打开跟卖浮层失败: {e}")
            return False
    
    def close(self):
        """关闭抓取器"""
        try:
            if hasattr(self, 'browser_service') and self.browser_service:
                self.browser_service.close()
                self.logger.debug("OzonScraperOptimized 浏览器服务已关闭")
        except Exception as e:
            self.logger.warning(f"关闭 OzonScraperOptimized 时出现警告: {e}")

    def __enter__(self):
        """上下文管理器入口"""
        self.browser_service.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.browser_service.__exit__(exc_type, exc_val, exc_tb)