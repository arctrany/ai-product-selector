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
from ..config.ozon_selectors import get_ozon_selectors_config, OzonSelectorsConfig


class CompetitorScraper:
    """OZON跟卖店铺抓取器"""
    
    def __init__(self, selectors_config: Optional[OzonSelectorsConfig] = None):
        """初始化跟卖抓取器"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.selectors_config = selectors_config or get_ozon_selectors_config()

    async def open_competitor_popup(self, page) -> Dict[str, Any]:
        """
        🔧 修复：严格的跟卖区域检测和点击逻辑

        Args:
            page: Playwright页面对象

        Returns:
            Dict[str, Any]: 包含详细状态信息
            {
                'success': bool,           # 操作是否成功
                'has_competitors': bool,   # 是否确实有跟卖
                'popup_opened': bool,      # 浮层是否打开
                'error_message': str       # 错误信息（如果有）
            }
        """
        try:
            self.logger.info("🔍 开始严格检测跟卖区域...")

            # 🎯 使用配置化的精确跟卖区域选择器
            precise_competitor_selector = self.selectors_config.PRECISE_COMPETITOR_SELECTOR

            # 🔧 修复：先检查跟卖区域是否存在，不存在直接返回无跟卖
            self.logger.debug(f"🔍 检查跟卖区域是否存在: {precise_competitor_selector}")

            try:
                # 短时间等待，如果元素不存在会立即超时
                await page.wait_for_selector(precise_competitor_selector, timeout=2000)
                element = await page.query_selector(precise_competitor_selector)

                if not element:
                    self.logger.info("✅ 跟卖区域不存在，确认无跟卖")
                    return {
                        'success': True,
                        'has_competitors': False,
                        'popup_opened': False,
                        'error_message': None
                    }

                # 检查元素是否可见
                is_visible = await element.is_visible()
                if not is_visible:
                    self.logger.info("✅ 跟卖区域存在但不可见，确认无跟卖")
                    return {
                        'success': True,
                        'has_competitors': False,
                        'popup_opened': False,
                        'error_message': None
                    }

                # 获取元素文本内容用于日志
                try:
                    text_content = await element.text_content()
                    self.logger.debug(f"跟卖区域文本内容: {text_content[:100] if text_content else 'N/A'}")
                except:
                    pass

                # 🎯 尝试点击跟卖区域
                self.logger.info("🔍 跟卖区域存在且可见，尝试点击...")
                await element.click()
                self.logger.info("✅ 成功点击跟卖区域")

                # 等待浮层加载
                self.logger.info("⏳ 等待跟卖浮层加载...")
                await asyncio.sleep(2.0)

                # 🔧 验证浮层是否真的打开并包含跟卖内容
                popup_opened = await self._verify_competitor_popup_opened(page)

                if popup_opened:
                    self.logger.info("✅ 跟卖浮层成功打开")
                    # 🎯 检查并展开跟卖店铺列表（如果需要）
                    await self.expand_competitor_list_if_needed(page)

                    return {
                        'success': True,
                        'has_competitors': True,
                        'popup_opened': True,
                        'error_message': None
                    }
                else:
                    self.logger.warning("⚠️ 点击成功但浮层未正确打开，可能无跟卖内容")
                    return {
                        'success': True,
                        'has_competitors': False,
                        'popup_opened': False,
                        'error_message': "浮层未正确打开"
                    }

            except Exception as e:
                # 选择器超时或其他错误，说明跟卖区域不存在
                self.logger.info(f"✅ 跟卖区域不存在（{str(e)[:50]}），确认无跟卖")
                return {
                    'success': True,
                    'has_competitors': False,
                    'popup_opened': False,
                    'error_message': None
                }

        except Exception as e:
            self.logger.error(f"检测跟卖区域失败: {e}")
            return {
                'success': False,
                'has_competitors': False,
                'popup_opened': False,
                'error_message': str(e)
            }

    async def _verify_competitor_popup_opened(self, page) -> bool:
        """
        验证跟卖浮层是否真的打开并包含内容

        Args:
            page: Playwright页面对象

        Returns:
            bool: 浮层是否正确打开
        """
        try:
            await asyncio.sleep(0.5)

            # 使用配置化的浮层指示器选择器
            popup_indicators = self.selectors_config.POPUP_INDICATORS

            for indicator in popup_indicators:
                try:
                    self.logger.debug(f"🔍 检查浮层指示器: {indicator}")
                    element = await page.query_selector(indicator)
                    if element and await element.is_visible():
                        # 🔧 进一步验证元素是否包含跟卖内容
                        try:
                            text_content = await element.text_content()
                            if text_content and (
                                'продавц' in text_content.lower() or  # 俄语"卖家"
                                'seller' in text_content.lower() or   # 英语"卖家"
                                '₽' in text_content or                # 卢布符号
                                'руб' in text_content.lower()         # 俄语"卢布"
                            ):
                                self.logger.debug(f"✅ 找到有效浮层指示器: {indicator} (包含跟卖内容)")
                                return True
                            else:
                                self.logger.debug(f"🔍 找到元素但内容不匹配: {indicator}")
                        except:
                            # 如果无法获取文本内容，但元素存在且可见，也认为是有效的
                            self.logger.debug(f"✅ 找到浮层指示器: {indicator} (无法验证内容)")
                            return True
                except Exception as e:
                    self.logger.debug(f"检查指示器 {indicator} 失败: {e}")
                    continue

            # 🆕 如果所有指示器都没找到，尝试通过JavaScript检查页面内容
            try:
                # 使用JavaScript检查页面是否有包含价格或seller相关的新元素
                has_price_elements = await page.evaluate("""
                    () => {
                        const elements = document.querySelectorAll('div');
                        for (let element of elements) {
                            const text = element.textContent || '';
                            if ((text.includes('₽') || text.includes('продавц') || text.includes('seller')) && 
                                element.offsetWidth > 0 && element.offsetHeight > 0) {
                                return true;
                            }
                        }
                        return false;
                    }
                """)
                if has_price_elements:
                    self.logger.debug("✅ 通过内容检测找到浮层")
                    return True
            except:
                pass

            self.logger.debug("⚠️ 未找到浮层指示器")
            return False

        except Exception as e:
            self.logger.debug(f"验证浮层失败: {e}")
            return False

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
                                await asyncio.sleep(0.5)

                                await current_element.click(timeout=10000)
                                expanded_count += 1
                                self.logger.info(f"✅ 成功点击展开按钮 (第{expanded_count}次)")

                                await asyncio.sleep(2.0)

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

            seller_list_container = None

            for selector in self.selectors_config.COMPETITOR_CONTAINER_SELECTORS:
                seller_list_container = soup.select_one(selector)
                if seller_list_container:
                    self.logger.debug(f"✅ 找到跟卖店铺列表容器: {selector}")
                    break

            # 查找店铺元素
            competitor_elements = []
            best_selector = None
            if seller_list_container:
                for selector in self.selectors_config.COMPETITOR_ELEMENT_SELECTORS:
                    try:
                        elements = seller_list_container.select(selector)
                        if elements and len(elements) >= len(competitor_elements):
                            # 优先选择找到更多元素的选择器，数量相同时选择后面的（通常更精确）
                            if len(elements) > len(competitor_elements) or (len(elements) == len(competitor_elements) and elements):
                                competitor_elements = elements
                                best_selector = selector
                                self.logger.debug(f"✅ 使用选择器 '{selector}' 找到 {len(elements)} 个跟卖店铺元素")
                    except Exception as e:
                        self.logger.debug(f"选择器 '{selector}' 失败: {e}")
                        continue

                if best_selector:
                    self.logger.debug(f"🎯 最终选择选择器: {best_selector}，找到 {len(competitor_elements)} 个元素")

            # 如果仍未找到，尝试在整个页面中查找
            if not competitor_elements:
                self.logger.warning("⚠️ 在容器中未找到跟卖店铺，尝试全页面搜索...")

                # 使用配置的全局选择器
                global_selectors = self.selectors_config.COMPETITOR_CONTAINER_SELECTORS

                for selector in global_selectors:
                    try:
                        elements = soup.select(selector)
                        if elements and len(elements) > len(competitor_elements):
                            competitor_elements = elements
                            self.logger.debug(f"✅ 全页面搜索使用选择器 '{selector}' 找到 {len(elements)} 个跟卖店铺元素")
                    except Exception as e:
                        self.logger.debug(f"全页面选择器 '{selector}' 失败: {e}")
                        continue

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

            # 🔧 修复：基于用户提供的实际页面结构的精确选择器
            store_link_selectors = [
                # 🎯 基于用户提供的实际HTML结构的精确选择器（优先级最高）
                "div.pdp_jb5.pdp_b6j > div.pdp_ae4 > div.pdp_a4e > div.pdp_ea4 > a.pdp_ae5",  # 完整路径
                "div.pdp_ae4 > div.pdp_a4e > div.pdp_ea4 > a.pdp_ae5",  # 简化路径
                "div.pdp_a4e > div.pdp_ea4 > a.pdp_ae5",  # 更简化路径
                "div.pdp_ea4 > a.pdp_ae5",  # 最简化路径
                "a.pdp_ae5[href*='/seller/']",  # 店铺链接的具体类

                # 🔄 备用选择器
                "a[href*='/seller/']",          # 任何包含/seller/的链接
                "a[href*='sellerId=']",         # sellerId参数的链接
                "a[href*='seller']",            # 包含seller的链接
                "a"                             # 最后备用：任何链接
            ]

            store_link_element = None
            used_selector = None
            for selector in store_link_selectors:
                try:
                    store_link_element = element.select_one(selector)
                    if store_link_element and store_link_element.get('href'):
                        used_selector = selector
                        self.logger.debug(f"✅ 使用选择器 '{selector}' 找到店铺链接")
                        break
                except Exception as e:
                    self.logger.debug(f"选择器 '{selector}' 查找失败: {e}")
                    continue

            if store_link_element and store_link_element.get('href'):
                # 提取店铺名称
                store_name = store_link_element.get_text(strip=True)
                if store_name:
                    competitor_data['store_name'] = store_name
                    self.logger.debug(f"✅ 提取到店铺名称: {store_name}")

                # 提取店铺URL和ID
                href = store_link_element.get('href')
                self.logger.debug(f"✅ 提取到店铺链接: {href} (使用选择器: {used_selector})")

                # 从URL中提取店铺ID
                store_id = self._extract_store_id_from_url(href)
                if store_id:
                    competitor_data['store_id'] = store_id
                    self.logger.debug(f"✅ 提取到店铺ID: {store_id}")
                else:
                    competitor_data['store_id'] = f"store_{ranking}"
                    self.logger.debug(f"⚠️ 未能从URL提取店铺ID，使用默认ID: store_{ranking}")
            else:
                # 🔧 调试：输出元素的HTML结构以便分析
                element_html = str(element)[:500] + "..." if len(str(element)) > 500 else str(element)
                self.logger.debug(f"⚠️ 未找到店铺链接，元素HTML结构: {element_html}")

                competitor_data['store_id'] = f"store_{ranking}"
                competitor_data['store_name'] = f"店铺{ranking}"

            # 🔧 修复：基于用户提供的实际HTML结构的精确价格选择器
            price_selectors = [
                # 🎯 基于用户提供的正确选择器路径（优先级最高）
                "div.pdp_jb5.pdp_jb6 > div > div",  # 用户提供的正确路径
                "div.pdp_jb5.pdp_jb6 > div.pdp_bk0 > div.pdp_b1k",  # 完整路径的价格选择器
                "div.pdp_bk0 > div.pdp_b1k",      # 简化路径的价格选择器
                "div.pdp_b1k",                    # 主要价格类

                # 🔄 备用价格选择器
                "div.pdp_jb5.pdp_jb6 div.pdp_b1k", # 后代选择器版本
                "span[class*='price']",           # 价格相关的span
                "div[class*='price']",            # 价格相关的div
                "[class*='pdp_b1k']",            # 包含价格类的元素
                "span[class*='pdp_b']",          # 价格相关的span类
                "div[class*='pdp_b']"            # 价格相关的div类
            ]

            price = None
            used_price_selector = None

            # 首先尝试使用具体的选择器
            for selector in price_selectors:
                try:
                    price_element = element.select_one(selector)
                    if price_element:
                        price_text = price_element.get_text(strip=True)
                        self.logger.debug(f"🔍 尝试解析价格文本: '{price_text}' (选择器: {selector})")
                        price = clean_price_string(price_text, self.selectors_config)
                        if price and price > 0:
                            competitor_data['price'] = price
                            used_price_selector = selector
                            self.logger.debug(f"✅ 提取到店铺价格: {price}₽ (使用选择器: {selector})")
                            break
                except Exception as e:
                    self.logger.debug(f"价格选择器 '{selector}' 查找失败: {e}")
                    continue

            # 如果具体选择器都失败了，尝试查找包含₽符号的文本
            if not price:
                try:
                    price_elements = element.find_all(text=lambda text: text and '₽' in text)
                    for price_text in price_elements:
                        price_text_str = str(price_text).strip()
                        self.logger.debug(f"🔍 尝试解析包含₽的文本: '{price_text_str}'")
                        price = clean_price_string(price_text_str, self.selectors_config)
                        if price and price > 0:
                            competitor_data['price'] = price
                            used_price_selector = "text_search"
                            self.logger.debug(f"✅ 通过文本查找提取到店铺价格: {price}₽")
                            break
                except Exception as e:
                    self.logger.debug(f"文本价格查找失败: {e}")

            # 如果还是没找到价格，输出调试信息
            if not price:
                element_text = element.get_text(strip=True)[:200] + "..." if len(element.get_text(strip=True)) > 200 else element.get_text(strip=True)
                self.logger.debug(f"⚠️ 未找到价格信息，元素文本内容: {element_text}")

            # 确保有基本信息
            if 'store_name' not in competitor_data or not competitor_data['store_name']:
                competitor_data['store_name'] = f"店铺{ranking}"
                self.logger.debug(f"⚠️ 使用默认店铺名称: {competitor_data['store_name']}")

            self.logger.debug(f"✅ 第{ranking}个跟卖店铺信息提取完成: {competitor_data}")
            return competitor_data

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

            await asyncio.sleep(0.5)

            # 🔧 修复：使用配置化的店铺行选择器（整行都可以点击）
            # 构建基于配置的店铺行选择器
            competitor_row_selectors = []

            # 🎯 使用配置的点击选择器
            for selector_template in self.selectors_config.COMPETITOR_CLICK_SELECTORS:
                try:
                    # 将模板中的{}替换为实际排名
                    selector = selector_template.format(ranking)
                    competitor_row_selectors.append(selector)
                except Exception as e:
                    self.logger.debug(f"格式化选择器模板失败: {selector_template}, 错误: {e}")
                    continue

            # 🔄 如果配置的选择器为空，使用基本的备用选择器
            if not competitor_row_selectors:
                self.logger.warning("配置的点击选择器为空，使用备用选择器")
                competitor_row_selectors = [
                    f"#seller-list div.pdp_kb2:nth-child({ranking})",
                    f"//div[@id='seller-list']//div[contains(@class, 'pdp_kb2')][{ranking}]"
                ]

            competitor_row_element = None
            used_selector = None

            # 查找店铺行元素
            for selector in competitor_row_selectors:
                try:
                    self.logger.debug(f"🔍 尝试使用选择器定位店铺行: {selector}")

                    if selector.startswith("//"):  # XPath
                        element = await page.query_selector(f'xpath={selector}')
                    else:  # CSS选择器
                        element = await page.query_selector(selector)

                    if element and await element.is_visible():
                        competitor_row_element = element
                        used_selector = selector
                        self.logger.debug(f"✅ 找到第{ranking}个店铺行: {selector}")
                        break
                    else:
                        self.logger.debug(f"🔍 选择器未找到可见元素: {selector}")

                except Exception as e:
                    self.logger.debug(f"选择器 {selector} 检查失败: {e}")
                    continue

            if competitor_row_element:
                try:
                    # 🎯 点击整个店铺行
                    self.logger.info(f"🔍 点击第{ranking}个跟卖店铺行...")

                    # 获取店铺信息用于日志（如果可能）
                    try:
                        store_link = await competitor_row_element.query_selector("a[href*='/seller/']")
                        if store_link:
                            store_name = await store_link.text_content()
                            href = await store_link.get_attribute('href')
                            self.logger.debug(f"点击店铺行: {store_name} -> {href}")
                    except:
                        pass

                    # 点击店铺行
                    await competitor_row_element.click()
                    self.logger.info(f"✅ 成功点击第{ranking}个跟卖店铺行 (使用选择器: {used_selector})")

                    await asyncio.sleep(2.0)

                    # 🔧 验证是否成功跳转到店铺页面
                    current_url = page.url
                    if '/seller/' in current_url or 'sellerId=' in current_url:
                        self.logger.info(f"✅ 成功跳转到店铺页面: {current_url}")
                        return True
                    else:
                        self.logger.warning(f"⚠️ 点击成功但未跳转到店铺页面，当前URL: {current_url}")
                        return False

                except Exception as click_e:
                    self.logger.error(f"点击店铺行失败: {click_e}")
                    return False
            else:
                self.logger.warning(f"⚠️ 未找到第{ranking}个跟卖店铺行")

                # 🔧 调试信息：列出当前页面的所有店铺行
                try:
                    all_rows = await page.query_selector_all("#seller-list div.pdp_kb2")
                    self.logger.debug(f"页面中共找到 {len(all_rows)} 个店铺行")
                    for i, row in enumerate(all_rows[:5]):  # 只显示前5个
                        try:
                            store_link = await row.query_selector("a[href*='/seller/']")
                            if store_link:
                                store_name = await store_link.text_content()
                                href = await store_link.get_attribute('href')
                                self.logger.debug(f"店铺行{i+1}: {store_name} -> {href}")
                        except:
                            self.logger.debug(f"店铺行{i+1}: 无法获取详细信息")
                except:
                    pass

                return False

        except Exception as e:
            self.logger.error(f"点击跟卖店铺跳转到商品详情页失败: {e}")
            import traceback
            self.logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False




