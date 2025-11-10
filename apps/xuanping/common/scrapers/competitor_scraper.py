"""
OZON跟卖店铺抓取器

专门处理OZON平台跟卖店铺的交互逻辑，包括：
1. 打开跟卖浮层
2. 提取跟卖店铺列表
3. 点击跟卖店铺跳转
4. 跟卖价格识别和过滤
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

from ..models import CompetitorStore, clean_price_string


class CompetitorScraper:
    """OZON跟卖店铺抓取器"""
    
    def __init__(self):
        """初始化跟卖抓取器"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def open_competitor_popup(self, page) -> bool:
        """
        打开跟卖店铺浮层
        
        Args:
            page: Playwright页面对象
            
        Returns:
            bool: 是否成功打开
        """
        try:
            self.logger.info("🔍 开始查找并点击跟卖区域...")

            # 🔧 使用更准确的选择器，按成功率排序
            competitor_button_selectors = [
                # 高成功率选择器
                "button span div.pdp_t1",
                # 基于文本内容的选择器
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
                    await page.wait_for_selector(selector, timeout=3000)
                    element = await page.query_selector(selector)
                    
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

            return clicked

        except Exception as e:
            self.logger.error(f"打开跟卖店铺浮层失败: {e}")
            import traceback
            self.logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False
    
    async def extract_competitors_from_content(self, page_content: str, max_competitors: int = 10) -> List[Dict[str, Any]]:
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
            soup = BeautifulSoup(page_content, 'html.parser')
            
            self.logger.info("🔍 开始提取跟卖店铺信息...")

            # 🔧 使用多种选择器查找跟卖店铺列表容器
            seller_list_container = None
            alternative_selectors = [
                "#seller-list",  # 原始选择器
                "[data-widget='sellerList']",
                "[class*='seller-list']",
                "[class*='competitor-list']",
                "[data-test-id*='seller-list']",
                ".seller-list",
                ".competitor-list",
                "[class*='modal']",  # 浮层容器
                "[class*='popup']",  # 弹窗容器
                "[data-widget*='seller']"  # 数据组件
            ]

            for selector in alternative_selectors:
                seller_list_container = soup.select_one(selector)
                if seller_list_container:
                    self.logger.debug(f"✅ 使用选择器找到跟卖店铺列表容器: {selector}")
                    break

            # 如果仍未找到，尝试查找包含"seller"或"продавец"的容器
            if not seller_list_container:
                # 查找所有div元素，检查文本内容
                div_elements = soup.find_all('div')
                for element in div_elements:
                    # 检查元素文本是否包含关键词
                    text = element.get_text(strip=True).lower()
                    if 'seller' in text or 'продавец' in text or 'магазин' in text:
                        # 检查该元素是否有子元素包含价格信息
                        price_elements = element.find_all(text=lambda t: t and '₽' in t)
                        if price_elements:
                            seller_list_container = element
                            self.logger.debug("✅ 通过关键词和价格信息找到跟卖店铺列表容器")
                            break

            # 查找跟卖店铺列表项
            competitor_elements = []
            if seller_list_container:
                self.logger.debug("✅ 找到跟卖店铺列表容器")

                # 尝试多种选择器查找店铺元素
                potential_selectors = [
                    ":scope > div > div",
                    ":scope > div",
                    ":scope > li",
                    ":scope > [class*='item']",
                    ":scope > [class*='seller']",
                    ":scope > [class*='competitor']",
                    "[class*='seller-item']",
                    "[class*='competitor-item']",
                    "[data-test-id*='seller']"
                ]

                for selector in potential_selectors:
                    elements = seller_list_container.select(selector)
                    if elements:
                        competitor_elements = elements
                        self.logger.debug(f"✅ 使用选择器 {selector} 找到 {len(elements)} 个跟卖店铺元素")
                        break

                # 如果仍未找到，尝试在整个容器中查找包含价格的元素
                if not competitor_elements:
                    # 查找容器内所有包含价格符号的元素
                    price_elements = seller_list_container.find_all(text=lambda text: text and '₽' in text)
                    for price_element in price_elements:
                        # 获取父元素
                        parent = price_element.parent
                        # 向上查找几层，找到可能的店铺元素容器
                        current = parent
                        level = 0
                        while current and level < 3:  # 最多向上查找3层
                            if current.name in ['div', 'li', 'tr']:
                                # 检查是否已添加过这个元素
                                if current not in competitor_elements:
                                    competitor_elements.append(current)
                                break
                            current = current.parent
                            level += 1

            else:
                self.logger.warning("⚠️ 未找到跟卖店铺列表容器，将在整个页面中查找跟卖店铺元素")
                # 直接在整个页面中查找跟卖店铺元素
                competitor_elements = self._find_competitors_in_full_page(soup)

            if not competitor_elements:
                self.logger.warning("⚠️ 未找到跟卖店铺列表项")
                return []

            self.logger.info(f"🎯 共找到 {len(competitor_elements)} 个跟卖店铺元素")

            # 提取店铺信息
            for i, element in enumerate(competitor_elements[:max_competitors]):
                try:
                    self.logger.debug(f"开始提取第{i+1}个跟卖店铺信息...")
                    competitor_data = self._extract_competitor_from_element(element, i + 1)
                    if competitor_data:
                        self.logger.info(f"✅ 成功提取第{i+1}个跟卖店铺: {competitor_data.get('store_name', 'N/A')} - {competitor_data.get('price', 'N/A')}₽")
                        competitors.append(competitor_data)
                    else:
                        self.logger.warning(f"⚠️ 第{i+1}个跟卖店铺信息提取失败")

                except Exception as e:
                    self.logger.warning(f"提取第{i+1}个跟卖店铺信息失败: {e}")
                    continue

            self.logger.info(f"🎉 成功提取{len(competitors)}个跟卖店铺信息")
            return competitors

        except Exception as e:
            self.logger.error(f"从页面内容提取跟卖店铺列表失败: {e}")
            import traceback
            self.logger.error(f"详细错误信息: {traceback.format_exc()}")
            return []

    def _find_competitors_in_full_page(self, soup) -> List:
        """
        在整个页面中查找跟卖店铺元素
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            List: 跟卖店铺元素列表
        """
        competitor_elements = []
        
        try:
            # 查找所有包含价格符号的元素
            price_elements = soup.find_all(text=lambda text: text and '₽' in text)
            for price_element in price_elements:
                # 获取父元素
                parent = price_element.parent
                # 向上查找几层，找到可能的店铺元素容器
                current = parent
                level = 0
                while current and level < 5:  # 最多向上查找5层
                    # 检查当前元素是否可能是店铺元素容器
                    if current.name in ['div', 'li', 'tr'] and len(current.find_all(text=lambda t: '₽' in t)) >= 1:
                        # 检查是否已添加过这个元素
                        if current not in competitor_elements:
                            competitor_elements.append(current)
                            break
                    current = current.parent
                    level += 1

            if competitor_elements:
                self.logger.info(f"🎯 在整个页面中找到 {len(competitor_elements)} 个跟卖店铺元素")
            
            return competitor_elements
            
        except Exception as e:
            self.logger.error(f"在整个页面中查找跟卖店铺元素失败: {e}")
            return []

    def _extract_competitor_from_element(self, element, ranking: int) -> Optional[Dict[str, Any]]:
        """
        从元素中提取跟卖店铺信息
        
        Args:
            element: 店铺元素
            ranking: 排名
            
        Returns:
            Dict[str, Any]: 店铺信息
        """
        try:
            self.logger.debug(f"🔍 开始提取第{ranking}个跟卖店铺信息...")
            competitor_data = {
                'ranking': ranking
            }

            # 提取店铺名称 - 使用更准确的选择器，增加更多变体
            name_selectors = [
                "[data-test-id*='seller']",
                "[class*='sellerName']",
                "[class*='seller-name']",
                "[class*='name']",
                "[class*='seller']",
                "[class*='store']",
                "div[class*='name']",
                "span[class*='name']",
                # 增加更多可能的选择器
                "[data-test-id='seller-name']",
                "[data-test-id='store-name']",
                ".seller-name",
                ".store-name",
                ".competitor-name",
                "div.seller-name",
                "span.seller-name"
            ]

            store_name = None
            for selector in name_selectors:
                name_element = element.select_one(selector)
                if name_element:
                    store_name = name_element.get_text(strip=True)
                    if store_name and len(store_name) > 0:
                        competitor_data['store_name'] = store_name
                        self.logger.debug(f"✅ 提取到店铺名称: {store_name}")
                        break

            # 如果仍未找到店铺名称，尝试查找所有包含文本的元素
            if 'store_name' not in competitor_data:
                # 查找所有文本节点，过滤出可能的店铺名称
                text_elements = element.find_all(text=True)
                for text in text_elements:
                    # 过滤掉纯空白字符和价格信息
                    stripped_text = text.strip()
                    if (stripped_text and
                        len(stripped_text) > 1 and
                        '₽' not in stripped_text and
                        not stripped_text.replace('.', '').replace(',', '').isdigit()):
                        competitor_data['store_name'] = stripped_text
                        self.logger.debug(f"✅ 通过文本查找提取到店铺名称: {stripped_text}")
                        break

            # 提取价格 - 使用更准确的选择器
            price_selectors = [
                "[data-test-id*='price']",
                "[class*='priceValue']",
                "[class*='price-current']",
                "[class*='price']",
                "[class*='cost']",
                "div[class*='price']",
                "span[class*='price']",
                # 增加更多可能的选择器
                ".price-value",
                ".current-price",
                "[data-test-id='price']",
                "div.price",
                "span.price"
            ]

            price = None
            for selector in price_selectors:
                price_element = element.select_one(selector)
                if price_element:
                    price_text = price_element.get_text(strip=True)
                    self.logger.debug(f"🔍 尝试解析价格文本: '{price_text}'")
                    price = clean_price_string(price_text)
                    if price and price > 0:
                        competitor_data['price'] = price
                        self.logger.debug(f"✅ 提取到店铺价格: {price}₽")
                        break

            # 如果没有找到价格，尝试查找包含₽符号的文本
            if not price:
                price_elements = element.find_all(text=lambda text: text and '₽' in text)
                for price_text in price_elements:
                    price = clean_price_string(str(price_text))
                    if price and price > 0:
                        competitor_data['price'] = price
                        self.logger.debug(f"✅ 通过文本查找提取到店铺价格: {price}₽")
                        break

            # 提取店铺ID（如果有链接）- 增强链接查找逻辑
            link_element = None
            # 尝试多种链接选择器
            link_selectors = [
                "a[href*='/seller/']",
                "a[href*='sellerId=']",
                "a[href*='seller']",
                "a[href*='/seller-']",
                "a[href*='sellerId/']",
                "a[href*='shop/']",
                "a"  # 最后尝试查找任意链接
            ]

            for selector in link_selectors:
                link_element = element.select_one(selector)
                if link_element and link_element.get('href'):
                    href = link_element.get('href')
                    if href and len(href) > 0:
                        self.logger.debug(f"🔍 找到店铺链接: {href}")
                        break
                link_element = None

            if link_element and link_element.get('href'):
                href = link_element.get('href')
                self.logger.debug(f"🔍 店铺链接: {href}")
                # 从URL中提取店铺ID
                store_id = self._extract_store_id_from_url(href)
                if store_id:
                    competitor_data['store_id'] = store_id
                    self.logger.debug(f"✅ 提取到店铺ID: {store_id}")
                else:
                    competitor_data['store_id'] = f"store_{ranking}"
                    self.logger.debug(f"⚠️ 未找到店铺ID，使用默认ID: store_{ranking}")
            else:
                competitor_data['store_id'] = f"store_{ranking}"
                self.logger.debug(f"⚠️ 未找到店铺链接，使用默认ID: store_{ranking}")

            # 如果没有提取到店铺名称，使用默认名称
            if 'store_name' not in competitor_data or not competitor_data['store_name']:
                competitor_data['store_name'] = f"店铺{ranking}"
                self.logger.debug(f"⚠️ 未提取到店铺名称，使用默认名称: {competitor_data['store_name']}")

            # 验证数据完整性
            if competitor_data.get('store_id'):
                self.logger.debug(f"✅ 第{ranking}个跟卖店铺信息提取完成: {competitor_data}")
                return competitor_data
            else:
                self.logger.warning(f"⚠️ 第{ranking}个跟卖店铺信息不完整")
                return None

        except Exception as e:
            self.logger.warning(f"从元素提取跟卖店铺信息失败: {e}")
            import traceback
            self.logger.error(f"详细错误信息: {traceback.format_exc()}")
            return None

    def _extract_store_id_from_url(self, href: str) -> Optional[str]:
        """
        从URL中提取店铺ID
        
        Args:
            href: 店铺链接
            
        Returns:
            str: 店铺ID，如果提取失败返回None
        """
        try:
            import re
            # 优化正则表达式顺序，按最常见的情况排序
            patterns = [
                # 1. 最常见的格式: /seller/riv-gosh-123619/ 或 /seller/riv-gosh-123619
                r'/seller/[^/]+-(\d+)/?$',
                r'/seller/[^/]+-(\d+)',
                # 2. 数字ID格式: /seller/123619/
                r'/seller/(\d+)/?$',
                r'/seller/(\d+)',
                # 3. 其他格式
                r'seller[/_](\d+)',
                r'sellerId=(\d+)',
                r'/seller-(\d+)',
                r'sellerId/(\d+)',
                r'seller_(\d+)',
                r'/shop/(\d+)',
                r'shop/(\d+)',
                r'/store/(\d+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, href)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            self.logger.warning(f"从URL提取店铺ID失败: {e}")
            return None

    async def click_competitor_to_product_page(self, page, ranking: int) -> bool:
        """
        点击跟卖列表中的指定排名店铺，跳转到商品详情页面

        Args:
            page: Playwright页面对象
            ranking: 跟卖店铺排名 (1-based)

        Returns:
            bool: 是否成功跳转
        """
        try:
            self.logger.info(f"🔍 开始点击第{ranking}个跟卖店铺跳转到商品详情页...")

            # 等待跟卖浮层加载完成
            await asyncio.sleep(2)

            # 查找指定排名的跟卖店铺元素
            # 使用多种选择器尝试定位第ranking个跟卖店铺
            competitor_selectors = [
                f"//*[@id='seller-list']/div/div[{ranking}]",  # 原始XPath
                f"//div[@data-widget='sellerList']//div[{ranking}]",  # 数据组件选择器
                f"//*[contains(@class, 'seller-list')]//div[{ranking}]",  # 类选择器
                f"//*[contains(@class, 'competitor-list')]//div[{ranking}]",  # 竞争对手列表选择器
                f"//div[contains(text(), 'seller') or contains(text(), 'продавец')]//div[{ranking}]"  # 文本选择器
            ]

            competitor_element = None
            used_selector = None

            for selector in competitor_selectors:
                try:
                    self.logger.debug(f"🔍 尝试使用选择器定位跟卖店铺: {selector}")
                    if selector.startswith("/"):  # XPath
                        await page.wait_for_selector(f'xpath={selector}', timeout=3000)
                        element = await page.query_selector(f'xpath={selector}')
                    else:  # CSS选择器
                        await page.wait_for_selector(selector, timeout=3000)
                        element = await page.query_selector(selector)

                    if element:
                        competitor_element = element
                        used_selector = selector
                        self.logger.debug(f"✅ 使用选择器找到跟卖店铺元素: {selector}")
                        break
                except Exception as wait_e:
                    self.logger.debug(f"等待元素出现失败: {wait_e}")
                    continue

            if competitor_element:
                # 检查元素是否可见
                is_visible = await competitor_element.is_visible()
                if is_visible:
                    # 点击该元素
                    await competitor_element.click()
                    self.logger.info(f"✅ 成功点击第{ranking}个跟卖店铺 (使用选择器: {used_selector})")

                    # 等待页面跳转
                    await asyncio.sleep(3)
                    self.logger.info(f"✅ 已跳转到第{ranking}个跟卖店铺的商品详情页")
                    return True
                else:
                    self.logger.warning(f"⚠️ 第{ranking}个跟卖店铺元素不可见")
                    return False
            else:
                self.logger.warning(f"⚠️ 未找到第{ranking}个跟卖店铺元素")
                return False

        except Exception as e:
            self.logger.error(f"点击跟卖店铺跳转到商品详情页失败: {e}")
            return False

    def is_competitor_price_element(self, element) -> bool:
        """
        严格检测元素是否为跟卖价格
        
        Args:
            element: BeautifulSoup元素
            
        Returns:
            bool: 是否为跟卖价格
        """
        try:
            # 🔍 多层级上下文检测，更严格的跟卖价格识别
            current = element
            max_levels = 5  # 最多向上检查5层
            
            for level in range(max_levels):
                if not current:
                    break
                    
                # 获取当前层级的文本内容
                try:
                    text_content = current.get_text(strip=True).lower()
                    
                    # 🚨 严格的跟卖关键词检测
                    competitor_keywords = [
                        'у других продавцов',  # "在其他卖家那里"
                        'других продавцов',    # "其他卖家"
                        'от других продавцов', # "来自其他卖家"
                        'есть дешевле',        # "有更便宜的"
                        'есть быстрее',        # "有更快的"
                        'другие предложения',  # "其他报价"
                        'competitor',
                        'seller'
                    ]
                    
                    # 检查是否包含跟卖关键词
                    for keyword in competitor_keywords:
                        if keyword in text_content:
                            self.logger.debug(f"🚫 检测到跟卖关键词 '{keyword}' 在第{level}层: {text_content[:100]}")
                            return True
                    
                    # 🔍 检查CSS类名和属性
                    if hasattr(current, 'get'):
                        class_names = current.get('class', [])
                        if isinstance(class_names, list):
                            class_str = ' '.join(class_names).lower()
                            if any(keyword in class_str for keyword in ['competitor', 'seller', 'other']):
                                self.logger.debug(f"🚫 检测到跟卖相关CSS类: {class_str}")
                                return True
                        
                        # 检查data属性
                        for attr_name, attr_value in current.attrs.items():
                            if isinstance(attr_value, str) and any(keyword in attr_value.lower() for keyword in ['competitor', 'seller']):
                                self.logger.debug(f"🚫 检测到跟卖相关属性: {attr_name}={attr_value}")
                                return True
                
                except Exception:
                    pass
                
                # 向上一层
                current = current.parent if hasattr(current, 'parent') else None
            
            return False
            
        except Exception as e:
            self.logger.warning(f"跟卖价格检测失败: {e}")
            return False  # 检测失败时保守处理，不认为是跟卖价格

