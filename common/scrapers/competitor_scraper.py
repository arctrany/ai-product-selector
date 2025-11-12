"""
OZON跟卖店铺抓取器

专门处理OZON平台跟卖店铺的交互逻辑，包括：
1. 打开跟卖浮层
2. 提取跟卖店铺列表
3. 点击跟卖店铺跳转
4. 跟卖价格识别和过滤

重构版本：简化代码结构，消除硬编码，提高可维护性
"""

import asyncio
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup

from ..models import CompetitorStore, clean_price_string
from ..config.ozon_selectors import get_ozon_selectors_config, OzonSelectorsConfig


class CompetitorScraper:
    """OZON跟卖店铺抓取器 - 重构版本"""

    def __init__(self, selectors_config: Optional[OzonSelectorsConfig] = None):
        """初始化跟卖抓取器"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.selectors_config = selectors_config or get_ozon_selectors_config()

    async def _find_element_by_selectors(self, page_or_element, selectors: List[str],
                                       timeout: int = 2000) -> Tuple[Optional[Any], Optional[str]]:
        """
        通用选择器查找方法，避免重复代码

        Args:
            page_or_element: Playwright页面对象或元素
            selectors: 选择器列表
            timeout: 超时时间（毫秒）

        Returns:
            Tuple[element, used_selector]: 找到的元素和使用的选择器
        """
        for selector in selectors:
            try:
                element = await page_or_element.query_selector(selector)
                if element and await element.is_visible():
                    return element, selector
            except:
                continue
        return None, None

    async def _find_elements_by_selectors(self, page_or_element, selectors: List[str]) -> Tuple[List[Any], Optional[str]]:
        """
        通用多元素选择器查找方法

        Args:
            page_or_element: Playwright页面对象或元素
            selectors: 选择器列表

        Returns:
            Tuple[elements, used_selector]: 找到的元素列表和使用的选择器
        """
        best_elements = []
        best_selector = None

        for selector in selectors:
            try:
                elements = await page_or_element.query_selector_all(selector)
                if elements and len(elements) > len(best_elements):
                    best_elements = elements
                    best_selector = selector
            except:
                continue

        return best_elements, best_selector



    async def open_competitor_popup(self, page) -> Dict[str, Any]:
        """
        检测并打开跟卖浮层

        Args:
            page: Playwright页面对象

        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            self.logger.info("🔍 检测跟卖区域...")

            # 查找跟卖区域
            element, _ = await self._find_element_by_selectors(
                page, [self.selectors_config.PRECISE_COMPETITOR_SELECTOR]
            )

            if not element:
                self.logger.info("✅ 无跟卖区域")
                return {'success': True, 'has_competitors': False, 'popup_opened': False, 'error_message': None}

            # 点击跟卖区域
            await element.click()
            self.logger.info("✅ 点击跟卖区域")
            await asyncio.sleep(1.0)

            # 验证浮层打开
            popup_opened = await self._verify_popup_opened(page)

            if popup_opened:
                self.logger.info("✅ 跟卖浮层打开")
                await self._expand_if_needed(page)
                return {'success': True, 'has_competitors': True, 'popup_opened': True, 'error_message': None}
            else:
                self.logger.warning("⚠️ 浮层未打开")
                return {'success': True, 'has_competitors': False, 'popup_opened': False, 'error_message': "浮层未打开"}

        except Exception as e:
            self.logger.error(f"打开跟卖浮层失败: {e}")
            return {'success': False, 'has_competitors': False, 'popup_opened': False, 'error_message': str(e)}

    async def _verify_popup_opened(self, page) -> bool:
        """验证跟卖浮层是否打开"""
        try:
            await asyncio.sleep(0.5)

            # 查找浮层指示器
            element, _ = await self._find_element_by_selectors(page, self.selectors_config.POPUP_INDICATORS)

            if element:
                # 验证内容
                try:
                    text_content = await element.text_content()
                    if text_content and any(keyword in text_content.lower()
                                          for keyword in ['продавц', 'seller', '₽', 'руб']):
                        return True
                except:
                    pass
                return True  # 元素存在且可见就认为有效

            return False

        except Exception as e:
            self.logger.debug(f"验证浮层失败: {e}")
            return False

    async def _expand_if_needed(self, page) -> bool:
        """
        检查并展开跟卖店铺列表（简化版本）

        Args:
            page: Playwright页面对象

        Returns:
            bool: 是否成功展开或无需展开
        """
        try:
            await asyncio.sleep(0.5)

            # 查找展开按钮
            expand_button, used_selector = await self._find_element_by_selectors(
                page, self.selectors_config.EXPAND_SELECTORS
            )

            if not expand_button:
                self.logger.info("ℹ️ 无需展开，当前显示全部跟卖店铺")
                return True

            self.logger.info(f"🔍 开始展开跟卖店铺列表 (选择器: {used_selector})")

            # 连续点击展开按钮
            expanded_count = 0
            max_expansions = 5

            while expanded_count < max_expansions:
                try:
                    # 重新查找按钮
                    current_button = await page.query_selector(used_selector)
                    if not current_button or not await current_button.is_visible():
                        self.logger.info("✅ 展开按钮消失，展开完成")
                        break

                    await current_button.scroll_into_view_if_needed()
                    await asyncio.sleep(0.1)
                    await current_button.click(timeout=2000)
                    expanded_count += 1
                    self.logger.info(f"✅ 展开第{expanded_count}次")
                    await asyncio.sleep(1.0)

                except Exception as click_error:
                    self.logger.warning(f"⚠️ 点击展开按钮失败: {click_error}")
                    break

            if expanded_count > 0:
                self.logger.info(f"✅ 成功展开 {expanded_count} 次")

            return True

        except Exception as e:
            self.logger.warning(f"展开跟卖店铺列表失败: {e}")
            return True  # 即使展开失败，也继续抓取当前显示的内容

    async def expand_competitor_list_if_needed(self, page) -> bool:
        """
        检查并展开跟卖店铺列表（如果需要）

        Args:
            page: Playwright页面对象

        Returns:
            bool: 是否成功展开或无需展开
        """
        try:
            self.logger.info("🔍 检查是否需要展开跟卖店铺列表...")

            await asyncio.sleep(0.5)



            # 使用配置的展开按钮选择器
            expand_selectors = self.selectors_config.EXPAND_SELECTORS

            # 🔧 修复：先检查是否存在展开按钮，再决定是否点击
            expand_button_found = False
            expand_button_element = None
            used_selector = None

            # 查找展开按钮
            for selector in expand_selectors:
                try:
                    self.logger.debug(f"🔍 检查展开按钮选择器: {selector}")

                    # 短时间等待，检查按钮是否存在
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        expand_button_element = element
                        used_selector = selector
                        expand_button_found = True
                        self.logger.info(f"✅ 找到展开按钮: {selector}")
                        break

                except Exception as e:
                    self.logger.debug(f"展开按钮选择器 {selector} 检查失败: {e}")
                    continue

            # 第二步：如果找到展开按钮，则进行展开操作
            if expand_button_found and expand_button_element and used_selector:
                self.logger.info(f"🔍 开始展开跟卖店铺列表，使用选择器: {used_selector}")

                expanded_count = 0
                max_expansions = 5  # 最大展开次数，防止无限循环

                # 连续点击展开按钮，直到没有更多内容
                while expanded_count < max_expansions:
                    try:
                        # 重新查找按钮，确保仍然存在且可见
                        current_element = await page.query_selector(used_selector)
                        if current_element and await current_element.is_visible():
                            self.logger.info(f"🔍 点击展开按钮 (第{expanded_count + 1}次)...")

                            try:
                                await current_element.scroll_into_view_if_needed()
                                await asyncio.sleep(0.1)

                                await current_element.click(timeout=2000)
                                expanded_count += 1
                                self.logger.info(f"✅ 成功点击展开按钮 (第{expanded_count}次)")

                                await asyncio.sleep(1.0)

                            except Exception as click_error:
                                self.logger.warning(f"⚠️ 点击展开按钮失败: {click_error}")
                                # 🔧 尝试使用JavaScript点击作为备选方案
                                try:
                                    await page.evaluate(f'document.querySelector("{used_selector}").click()')
                                    expanded_count += 1
                                    self.logger.info(f"✅ 通过JavaScript成功点击展开按钮 (第{expanded_count}次)")
                                    await asyncio.sleep(2.0)
                                except Exception as js_error:
                                    self.logger.error(f"❌ JavaScript点击也失败: {js_error}")
                                    break
                        else:
                            self.logger.info("✅ 展开按钮消失，展开完成")
                            break

                    except Exception as click_e:
                        self.logger.error(f"❌ 点击展开按钮失败: {click_e}")
                        break

                if expanded_count > 0:
                    self.logger.info(f"✅ 成功展开 {expanded_count} 次，获取更多跟卖店铺")
                else:
                    self.logger.info("ℹ️ 展开按钮存在但无法点击，可能已经展开完毕")

                return True
            else:
                # 🔧 修复：如果没有找到展开按钮，说明当前显示的就是全部跟卖店铺，无需展开
                self.logger.info("ℹ️ 未找到展开按钮，当前显示的就是全部跟卖店铺，无需展开")
                return True

        except Exception as e:
            self.logger.warning(f"展开跟卖店铺列表失败: {e}")
            # 即使展开失败，也继续抓取当前显示的内容
            return True


    async def extract_competitors_from_content(self, page_content: str, max_competitors: int = 10) -> List[Dict[str, Any]]:
        """从页面内容中提取跟卖店铺信息"""
        try:
            soup = BeautifulSoup(page_content, 'html.parser')
            self.logger.info("🔍 提取跟卖店铺信息...")

            # 查找容器
            container = self._find_container_in_soup(soup)
            if not container:
                self.logger.warning("⚠️ 未找到跟卖店铺容器")
                return []

            # 查找店铺元素
            elements, selector = self._find_competitor_elements_in_soup(container)
            if not elements:
                self.logger.warning("⚠️ 未找到跟卖店铺元素")
                return []

            self.logger.info(f"🎯 找到 {len(elements)} 个跟卖店铺元素 (选择器: {selector})")

            # 提取店铺信息
            competitors = []
            for i, element in enumerate(elements[:max_competitors]):
                try:
                    competitor_data = self._extract_competitor_from_element(element, i + 1)
                    if competitor_data:
                        competitors.append(competitor_data)
                        self.logger.info(f"✅ 提取店铺{i+1}: {competitor_data.get('store_name', 'N/A')} - {competitor_data.get('price', 'N/A')}₽")
                except Exception as e:
                    self.logger.warning(f"提取第{i+1}个店铺失败: {e}")
                    continue

            self.logger.info(f"🎉 成功提取{len(competitors)}个跟卖店铺")
            return competitors

        except Exception as e:
            self.logger.error(f"提取跟卖店铺失败: {e}")
            return []

    def _find_container_in_soup(self, soup: BeautifulSoup):
        """在BeautifulSoup中查找跟卖店铺容器"""
        for selector in self.selectors_config.COMPETITOR_CONTAINER_SELECTORS:
            try:
                container = soup.select_one(selector)
                if container:
                    return container
            except:
                continue
        return None

    def _find_competitor_elements_in_soup(self, container) -> Tuple[List, Optional[str]]:
        """在容器中查找跟卖店铺元素 - 🔧 修复：使用多种选择器确保找到所有店铺"""
        best_elements = []
        best_selector = None

        for selector in self.selectors_config.COMPETITOR_ELEMENT_SELECTORS:
            try:
                elements = container.select(selector)
                if elements and len(elements) > len(best_elements):
                    best_elements = elements
                    best_selector = selector
                    self.logger.debug(f"✅ 使用选择器 '{selector}' 找到 {len(elements)} 个跟卖店铺元素")
                    # 🔧 关键修复：继续尝试其他选择器看是否能找到更多
            except Exception as e:
                self.logger.debug(f"选择器 '{selector}' 失败: {e}")
                continue

        return best_elements, best_selector

    def _extract_competitor_from_element(self, element, ranking: int) -> Optional[Dict[str, Any]]:
        """从元素中提取跟卖店铺信息 - 🔧 修复：恢复完整的提取逻辑，确保能提取多个店铺"""
        try:
            self.logger.debug(f"🔍 开始提取第{ranking}个跟卖店铺信息...")
            competitor_data = {'ranking': ranking}

            # 🔧 修复：使用配置的店铺名称选择器，包含回退逻辑
            name_selectors = self.selectors_config.STORE_NAME_SELECTORS
            store_name = None

            for selector in name_selectors:
                try:
                    name_element = element.select_one(selector)
                    if name_element:
                        store_name = name_element.get_text(strip=True)
                        if store_name and len(store_name) > 0:
                            competitor_data['store_name'] = store_name
                            self.logger.debug(f"✅ 提取到店铺名称: {store_name}")
                            break
                except:
                    continue

            # 🔧 修复：如果仍未找到店铺名称，尝试查找所有包含文本的元素
            if 'store_name' not in competitor_data:
                try:
                    text_elements = element.find_all(text=True)
                    for text in text_elements:
                        stripped_text = text.strip()
                        if (stripped_text and
                            len(stripped_text) > 1 and
                            '₽' not in stripped_text and
                            not stripped_text.replace('.', '').replace(',', '').isdigit()):
                            competitor_data['store_name'] = stripped_text
                            self.logger.debug(f"✅ 通过文本查找提取到店铺名称: {stripped_text}")
                            break
                except:
                    pass

            # 🔧 修复：使用配置的价格选择器，包含回退逻辑
            price_selectors = self.selectors_config.STORE_PRICE_SELECTORS
            price = None

            for selector in price_selectors:
                try:
                    price_element = element.select_one(selector)
                    if price_element:
                        price_text = price_element.get_text(strip=True)
                        self.logger.debug(f"🔍 尝试解析价格文本: '{price_text}'")
                        price = clean_price_string(price_text, self.selectors_config)
                        if price and price > 0:
                            competitor_data['price'] = price
                            self.logger.debug(f"✅ 提取到店铺价格: {price}₽")
                            break
                except:
                    continue

            # 🔧 修复：如果没有找到价格，尝试查找包含₽符号的文本
            if not price:
                try:
                    price_elements = element.find_all(text=lambda text: text and '₽' in text)
                    for price_text in price_elements:
                        price = clean_price_string(str(price_text), self.selectors_config)
                        if price and price > 0:
                            competitor_data['price'] = price
                            self.logger.debug(f"✅ 通过文本查找提取到店铺价格: {price}₽")
                            break
                except:
                    pass

            # 🔧 修复：使用配置的链接选择器
            link_element = None
            link_selectors = self.selectors_config.STORE_LINK_SELECTORS

            for selector in link_selectors:
                try:
                    link_element = element.select_one(selector)
                    if link_element and link_element.get('href'):
                        href = link_element.get('href')
                        if href and len(href) > 0:
                            self.logger.debug(f"🔍 找到店铺链接: {href}")
                            break
                    link_element = None
                except:
                    continue

            if link_element and link_element.get('href'):
                href = link_element.get('href')
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

            # 🔧 修复：如果没有提取到店铺名称，使用默认名称
            if 'store_name' not in competitor_data or not competitor_data['store_name']:
                competitor_data['store_name'] = f"店铺{ranking}"
                self.logger.debug(f"⚠️ 未提取到店铺名称，使用默认名称: {competitor_data['store_name']}")

            # 🔧 关键修复：放宽验证条件，只要有基本信息就返回，避免过滤掉店铺
            if competitor_data.get('store_name') or competitor_data.get('price') or competitor_data.get('store_id'):
                self.logger.debug(f"✅ 第{ranking}个跟卖店铺信息提取完成: {competitor_data}")
                return competitor_data
            else:
                self.logger.warning(f"⚠️ 第{ranking}个跟卖店铺信息完全为空，跳过")
                return None

        except Exception as e:
            self.logger.warning(f"从元素提取跟卖店铺信息失败: {e}")
            # 🔧 修复：即使出错也返回基本信息，避免完全丢失店铺
            return {
                'ranking': ranking,
                'store_name': f"店铺{ranking}",
                'store_id': f"store_{ranking}",
                'price': None
            }

    def _find_store_link_in_element(self, element):
        """在元素中查找店铺链接"""
        for selector in self.selectors_config.STORE_LINK_SELECTORS:
            try:
                link = element.select_one(selector)
                if link and link.get('href'):
                    return link
            except:
                continue
        return None

    def _extract_price_from_element(self, element) -> Optional[float]:
        """从元素中提取价格"""
        # 首先尝试具体选择器
        for selector in self.selectors_config.STORE_PRICE_SELECTORS:
            try:
                price_element = element.select_one(selector)
                if price_element:
                    price_text = price_element.get_text(strip=True)
                    price = clean_price_string(price_text, self.selectors_config)
                    if price and price > 0:
                        return price
            except:
                continue

        # 尝试查找包含₽符号的文本
        try:
            price_elements = element.find_all(text=lambda text: text and '₽' in text)
            for price_text in price_elements:
                price = clean_price_string(str(price_text).strip(), self.selectors_config)
                if price and price > 0:
                    return price
        except:
            pass

        return None

    def _extract_store_id_from_url(self, href: str) -> Optional[str]:
        """从URL中提取店铺ID"""
        try:
            patterns = [
                r'/seller/[^/]+-(\d+)/?$',  # /seller/name-123619/
                r'/seller/(\d+)/?$',       # /seller/123619/
                r'seller[/_](\d+)',        # seller/123619 或 seller_123619
                r'sellerId=(\d+)',         # sellerId=123619
                r'/shop/(\d+)',            # /shop/123619
                r'/store/(\d+)'            # /store/123619
            ]

            for pattern in patterns:
                match = re.search(pattern, href)
                if match:
                    return match.group(1)

            return None

        except Exception as e:
            self.logger.warning(f"提取店铺ID失败: {e}")
            return None

    async def click_competitor_to_product_page(self, page, ranking: int) -> bool:
        """点击跟卖列表中的指定排名店铺，跳转到商品详情页面"""
        try:
            self.logger.info(f"🔍 点击第{ranking}个跟卖店铺...")
            await asyncio.sleep(0.5)

            # 构建点击选择器
            click_selectors = []
            for template in self.selectors_config.COMPETITOR_CLICK_SELECTORS:
                try:
                    selector = template.format(ranking)
                    click_selectors.append(selector)
                except:
                    continue

            if not click_selectors:
                self.logger.warning("无可用点击选择器")
                return False

            # 查找并点击店铺行
            for selector in click_selectors:
                try:
                    if selector.startswith("//"):  # XPath
                        element = await page.query_selector(f'xpath={selector}')
                    else:  # CSS选择器
                        element = await page.query_selector(selector)

                    if element and await element.is_visible():
                        # 获取店铺信息用于日志（如果可能）
                        try:
                            # 使用配置的店铺链接选择器
                            for link_selector in self.selectors_config.STORE_LINK_SELECTORS:
                                store_link = await element.query_selector(link_selector)
                                if store_link:
                                    store_name = await store_link.text_content()
                                    href = await store_link.get_attribute('href')
                                    self.logger.debug(f"点击店铺行: {store_name} -> {href}")
                                    break
                        except:
                            pass

                        await element.click()
                        self.logger.info(f"✅ 点击第{ranking}个店铺 (选择器: {selector})")
                        await asyncio.sleep(2.0)

                        # 验证跳转
                        current_url = page.url
                        if '/seller/' in current_url or 'sellerId=' in current_url:
                            self.logger.info(f"✅ 跳转成功: {current_url}")
                            return True
                        else:
                            self.logger.warning(f"⚠️ 未跳转到店铺页面: {current_url}")
                            return False

                except Exception as e:
                    self.logger.debug(f"选择器 {selector} 失败: {e}")
                    continue

            self.logger.warning(f"⚠️ 未找到第{ranking}个跟卖店铺")
            return False

        except Exception as e:
            self.logger.error(f"点击跟卖店铺失败: {e}")
            return False

    async def _count_visible_competitors(self, page) -> int:
        """统计当前页面可见的跟卖店铺数量"""
        try:
            max_count = 0

            for container_selector in self.selectors_config.COMPETITOR_CONTAINER_SELECTORS:
                try:
                    container = await page.query_selector(container_selector)
                    if container:
                        elements, _ = await self._find_elements_by_selectors(
                            container, self.selectors_config.COMPETITOR_ELEMENT_SELECTORS
                        )
                        if elements and len(elements) > max_count:
                            max_count = len(elements)
                except:
                    continue

            return max_count

        except Exception as e:
            self.logger.debug(f"统计跟卖店铺数量失败: {e}")
            return 0




