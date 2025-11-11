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

            # 🎯 使用用户提供的精确跟卖区域选择器
            precise_competitor_selector = "#layoutPage > div.b6 > div.container.c > div.pdp_sa1.pdp_as5.pdp_as7 > div.pdp_mb9 > div > div > div.pdp_sa1.pdp_as8.pdp_as5.pdp_sa5 > div.pdp_i6b.pdp_bi9 > div.pdp_ib7 > div > div > div > button > span > div"

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

                # 等待页面响应
                self.logger.info("⏳ 等待跟卖浮层加载...")
                await asyncio.sleep(3)

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
            # 等待浮层内容加载
            await asyncio.sleep(2)

            # 🔧 增强浮层指示器检测 - 添加更多可能的选择器
            popup_indicators = [
                "#seller-list",  # 最常见的seller-list ID
                "[data-widget='sellerList']",  # 数据组件
                "[class*='seller-list']",  # 包含seller-list的类
                "[class*='sellerList']",  # 驼峰命名的类
                "[class*='popup']",  # 通用弹窗类
                "[class*='modal']",  # 模态框类
                "[class*='overlay']",  # 覆盖层类
                "[class*='dropdown']",  # 下拉框类
                "[class*='seller']",  # 包含seller的类
                "div[class*='seller'][class*='container']",  # seller容器
                "div[class*='seller'][class*='wrapper']",  # seller包装器
                # 🆕 新增更具体的选择器
                "[data-testid*='seller']",  # 测试ID
                "[data-test-id*='seller']",  # 测试ID变体
                "div[role='dialog']",  # 对话框角色
                "div[role='menu']",  # 菜单角色
                "div[role='listbox']",  # 列表框角色
                # 🆕 基于内容的选择器
                "div:has(a[href*='/seller/'])",  # 包含seller链接的div
                "div:has([class*='price'])",  # 包含价格的div
                "div:has(span:contains('₽'))",  # 包含卢布符号的div
            ]

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

            # 🆕 如果所有指示器都没找到，尝试检查页面是否有新的元素出现
            try:
                # 检查页面是否有新增的包含价格或seller相关的元素
                new_elements = await page.query_selector_all("div:has-text('₽'), div:has-text('продавц'), div:has-text('seller')")
                if new_elements:
                    for element in new_elements:
                        if await element.is_visible():
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
            
            # 等待页面稳定
            await asyncio.sleep(2)
            
            # 🎯 多种展开按钮选择器，按优先级排序
            expand_selectors = [
                "#seller-list > button > div.b25_4_4-a",  # 用户提供的精确选择器
            ]

            # 🔧 修复：先检查是否存在展开按钮，再决定是否点击
            expand_button_found = False
            expand_button_element = None
            used_selector = None

            # 第一步：查找展开按钮 - 只要找到一个就停止
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
                            await current_element.click()
                            expanded_count += 1

                            # 等待内容加载
                            await asyncio.sleep(3)

                            self.logger.info(f"✅ 成功点击展开按钮 (第{expanded_count}次)")
                        else:
                            self.logger.info("✅ 展开按钮消失，展开完成")
                            break

                    except Exception as click_e:
                        self.logger.debug(f"点击展开按钮失败: {click_e}")
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

            # 🔧 简化选择器查找逻辑 - 删除过度复杂的选择器尝试
            seller_list_container = None

            # 🔧 增强容器选择器 - 支持更多HTML结构
            primary_selectors = [
                "#seller-list",
                "[data-widget='sellerList']",
                "[class*='seller-list']",
                "[class*='sellerList']",
                "[data-widget*='seller']",
                "[data-widget*='Seller']",
                ".seller-popup",
                ".sellers-popup",
                "[class*='popup'] [class*='seller']",
                "[class*='modal'] [class*='seller']",
                "[class*='overlay'] [class*='seller']",
                "div[class*='seller'][class*='container']",
                "div[class*='seller'][class*='wrapper']"
            ]

            for selector in primary_selectors:
                seller_list_container = soup.select_one(selector)
                if seller_list_container:
                    self.logger.debug(f"✅ 找到跟卖店铺列表容器: {selector}")
                    break

            # 🔧 增强店铺元素查找逻辑 - 使用多种选择器确保找到所有店铺
            competitor_elements = []
            if seller_list_container:
                # 尝试多种选择器来查找跟卖店铺元素
                element_selectors = [
                    ":scope > div",  # 直接子div
                    ":scope div[class*='seller']",  # 包含seller的div
                    ":scope div[class*='competitor']",  # 包含competitor的div
                    ":scope > div > div",  # 二级子div
                    ":scope [data-test-id*='seller']",  # 包含seller的测试ID
                    ":scope div[class*='item']",  # 包含item的div
                    ":scope li",  # 列表项
                    ":scope > *",  # 所有直接子元素
                ]

                for selector in element_selectors:
                    try:
                        elements = seller_list_container.select(selector)
                        if elements and len(elements) > len(competitor_elements):
                            competitor_elements = elements
                            self.logger.debug(f"✅ 使用选择器 '{selector}' 找到 {len(elements)} 个跟卖店铺元素")
                            # 如果找到了多个元素，继续尝试其他选择器看是否能找到更多
                    except Exception as e:
                        self.logger.debug(f"选择器 '{selector}' 失败: {e}")
                        continue

            # 如果仍未找到，尝试在整个页面中查找
            if not competitor_elements:
                self.logger.warning("⚠️ 在容器中未找到跟卖店铺，尝试全页面搜索...")

                # 🔧 增强全页面搜索选择器 - 支持更多HTML结构
                global_selectors = [
                    "div[class*='seller-item']",
                    "div[class*='competitor-item']",
                    "[data-test-id*='seller-item']",
                    "div[class*='seller'] div[class*='item']",
                    ".seller-list div",
                    "[class*='seller-list'] > div",
                    "[class*='competitor-list'] > div",
                    # 新增更多可能的选择器
                    "div[class*='seller'][class*='row']",
                    "div[class*='seller'][class*='card']",
                    "div[class*='seller'][class*='block']",
                    "[class*='popup'] div[class*='item']",
                    "[class*='modal'] div[class*='item']",
                    "[class*='overlay'] div[class*='item']",
                    "div[data-widget*='seller']",
                    "div[data-widget*='Seller']",
                    "[role='listitem']",
                    "[role='option']",
                    "li[class*='seller']",
                    "tr[class*='seller']",
                    "div[class*='offer']",
                    "div[class*='vendor']",
                    "div[class*='merchant']",
                    # 通用的列表项选择器
                    "div > div > div[class*='price']",
                    "div:has(span[class*='price'])",
                    "div:has([class*='₽'])",
                    # 基于文本内容的选择器（如果支持）
                    "div:contains('₽')",
                    "div:contains('руб')"
                ]

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




