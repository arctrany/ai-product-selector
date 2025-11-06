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
                    
                    # 解析价格信息
                    price_data = await self._extract_price_data_from_content(page_content)
                    
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
            max_competitors: 最大跟卖店铺数量
            
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
                    
                    # 解析跟卖店铺信息
                    competitors = await self._extract_competitor_stores_from_content(page_content, max_competitors)
                    
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
    
    async def _extract_price_data_from_content(self, page_content: str) -> Dict[str, Any]:
        """
        从页面内容中提取价格数据
        
        Args:
            page_content: 页面HTML内容
            
        Returns:
            Dict[str, Any]: 价格数据
        """
        price_data = {}
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # 抓取绿标价格（促销价格）
            green_price_selectors = [
                "[data-widget='webPrice'] .price_discount",
                ".green-price",
                "[class*='discount']",
                "[class*='sale']"
            ]
            
            for selector in green_price_selectors:
                element = soup.select_one(selector)
                if element:
                    green_text = element.get_text(strip=True)
                    price = clean_price_string(green_text)
                    if price and price > 0:
                        price_data['green_price'] = price
                        break
            
            # 抓取黑标价格（原价）
            black_price_selectors = [
                "[data-widget='webPrice'] .price_original",
                ".black-price",
                "[class*='original']",
                "[class*='regular']"
            ]
            
            for selector in black_price_selectors:
                element = soup.select_one(selector)
                if element:
                    black_text = element.get_text(strip=True)
                    price = clean_price_string(black_text)
                    if price and price > 0:
                        price_data['black_price'] = price
                        break
            
            # 如果没有找到绿标价格，尝试查找主要价格
            if 'green_price' not in price_data:
                main_price_selectors = [
                    "[data-widget='webPrice'] span",
                    ".price span",
                    "[class*='price'] span"
                ]
                
                for selector in main_price_selectors:
                    elements = soup.select(selector)
                    for element in elements:
                        main_text = element.get_text(strip=True)
                        price = clean_price_string(main_text)
                        if price and price > 0:
                            price_data['green_price'] = price
                            break
                    if 'green_price' in price_data:
                        break
            
            # 如果没有黑标价格，使用绿标价格作为黑标价格
            if 'black_price' not in price_data and 'green_price' in price_data:
                price_data['black_price'] = price_data['green_price']
            
            # 尝试通用方法提取价格
            if not price_data:
                price_data = await self._extract_price_data_generic(soup)
            
            self.logger.debug(f"提取的价格数据: {price_data}")
            return price_data
            
        except Exception as e:
            self.logger.error(f"从页面内容提取价格数据失败: {e}")
            return {}
    
    async def _extract_price_data_generic(self, soup) -> Dict[str, Any]:
        """
        通用方法提取价格数据
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            Dict[str, Any]: 价格数据
        """
        price_data = {}
        
        try:
            # 查找所有包含价格符号的元素
            price_elements = soup.find_all(text=lambda text: text and ('₽' in text or 'руб' in text))
            
            prices = []
            for text in price_elements[:10]:  # 限制检查前10个元素
                price = clean_price_string(str(text))
                if price and price > 0:
                    prices.append(price)
            
            if prices:
                # 通常第一个价格是当前价格（绿标），最高价格可能是原价（黑标）
                prices.sort()
                price_data['green_price'] = prices[0]
                if len(prices) > 1:
                    price_data['black_price'] = prices[-1]
                else:
                    price_data['black_price'] = prices[0]
            
            return price_data
            
        except Exception as e:
            self.logger.error(f"通用方法提取价格数据失败: {e}")
            return {}
    
    async def _open_competitor_popup_async(self, browser_service):
        """
        异步打开跟卖店铺浮层
        
        Args:
            browser_service: 浏览器服务
        """
        try:
            # 这里可以添加点击操作来打开跟卖浮层
            # 由于我们使用的是页面内容解析，暂时跳过点击操作
            await asyncio.sleep(1)
            self.logger.debug("尝试打开跟卖店铺浮层")
            
        except Exception as e:
            self.logger.warning(f"打开跟卖店铺浮层失败: {e}")
    
    async def _extract_competitor_stores_from_content(self, page_content: str, max_competitors: int) -> List[Dict[str, Any]]:
        """
        从页面内容中提取跟卖店铺信息
        
        Args:
            page_content: 页面HTML内容
            max_competitors: 最大跟卖店铺数量
            
        Returns:
            List[Dict[str, Any]]: 跟卖店铺列表
        """
        competitors = []
        
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_content, 'html.parser')
            
            # 查找跟卖店铺列表
            competitor_selectors = [
                "[class*='seller'] [class*='item']",
                "[class*='competitor'] [class*='item']",
                "[class*='offer'] [class*='item']",
                "li[class*='seller']",
                "div[class*='seller']"
            ]
            
            competitor_elements = []
            for selector in competitor_selectors:
                competitor_elements = soup.select(selector)
                if competitor_elements:
                    break
            
            # 提取店铺信息
            for i, element in enumerate(competitor_elements[:max_competitors]):
                try:
                    competitor_data = await self._extract_competitor_from_element(element, i + 1)
                    if competitor_data:
                        competitors.append(competitor_data)
                        
                except Exception as e:
                    self.logger.warning(f"提取第{i+1}个跟卖店铺信息失败: {e}")
                    continue
            
            self.logger.info(f"成功提取{len(competitors)}个跟卖店铺信息")
            return competitors
            
        except Exception as e:
            self.logger.error(f"从页面内容提取跟卖店铺列表失败: {e}")
            return []
    
    async def _extract_competitor_from_element(self, element, ranking: int) -> Optional[Dict[str, Any]]:
        """
        从元素中提取跟卖店铺信息
        
        Args:
            element: 店铺元素
            ranking: 排名
            
        Returns:
            Dict[str, Any]: 店铺信息
        """
        try:
            competitor_data = {
                'ranking': ranking
            }
            
            # 提取店铺名称
            name_selectors = [
                "[class*='name']",
                "[class*='seller']",
                "[class*='store']"
            ]
            
            for selector in name_selectors:
                name_element = element.select_one(selector)
                if name_element:
                    competitor_data['store_name'] = name_element.get_text(strip=True)
                    break
            
            # 提取价格
            price_selectors = [
                "[class*='price']",
                "[class*='cost']"
            ]
            
            for selector in price_selectors:
                price_element = element.select_one(selector)
                if price_element:
                    price_text = price_element.get_text(strip=True)
                    price = clean_price_string(price_text)
                    if price and price > 0:
                        competitor_data['price'] = price
                        break
            
            # 提取店铺ID（如果有链接）
            link_element = element.select_one("a")
            if link_element and link_element.get('href'):
                href = link_element.get('href')
                # 从URL中提取店铺ID
                import re
                store_id_match = re.search(r'seller[/_](\d+)', href)
                if store_id_match:
                    competitor_data['store_id'] = store_id_match.group(1)
                else:
                    competitor_data['store_id'] = f"store_{ranking}"
            else:
                competitor_data['store_id'] = f"store_{ranking}"
            
            # 验证数据完整性
            if competitor_data.get('store_id'):
                return competitor_data
            else:
                return None
                
        except Exception as e:
            self.logger.warning(f"从元素提取跟卖店铺信息失败: {e}")
            return None
    
    def determine_real_price(self, green_price: Optional[float], 
                           black_price: Optional[float], 
                           competitor_price: Optional[float]) -> Tuple[float, float]:
        """
        根据价格比较逻辑确定真实价格
        
        Args:
            green_price: 绿标价格
            black_price: 黑标价格
            competitor_price: 跟卖价格
            
        Returns:
            Tuple[float, float]: (最终绿标价格, 最终黑标价格)
        """
        try:
            # 如果没有绿标价格，使用黑标价格
            if not green_price and black_price:
                return black_price, black_price
            
            # 如果没有跟卖价格，直接返回原价格
            if not competitor_price:
                return green_price or 0, black_price or 0
            
            # 价格比较逻辑
            if green_price and competitor_price:
                if green_price <= competitor_price:
                    # 分支1：使用当前商品详情页的价格
                    return green_price, black_price or green_price
                else:
                    # 分支2：使用跟卖价格作为更低的价格
                    return competitor_price, black_price or green_price
            
            return green_price or 0, black_price or 0
            
        except Exception as e:
            self.logger.error(f"确定真实价格失败: {e}")
            return green_price or 0, black_price or 0
    
    def close(self):
        """关闭抓取器"""
        try:
            if hasattr(self, 'browser_service') and self.browser_service:
                self.browser_service.close()
                self.logger.debug("OzonScraper 浏览器服务已关闭")
        except Exception as e:
            self.logger.warning(f"关闭 OzonScraper 时出现警告: {e}")

    def __enter__(self):
        """上下文管理器入口"""
        self.browser_service.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.browser_service.__exit__(exc_type, exc_val, exc_tb)