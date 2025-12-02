"""
OZON跟卖店铺抓取器

专门处理OZON平台跟卖店铺的交互逻辑，包括：
1. 打开跟卖浮层
2. 提取跟卖店铺列表
3. 点击跟卖店铺跳转
4. 跟卖价格识别和过滤

重构版本：简化代码结构，消除硬编码，提高可维护性
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup

# 🔧 重构后的导入：使用新的数据模型和统一工具类
from common.utils.scraping_utils import clean_price_string
from common.models.scraping_result import ScrapingResult
from common.utils.wait_utils import WaitUtils, wait_for_content_smart
from common.utils.scraping_utils import ScrapingUtils
from .base_scraper import BaseScraper
from common.config.ozon_selectors_config import *


# 异常类导入已移除，使用通用异常处理


class CompetitorScraper(BaseScraper):
    """
    OZON跟卖店铺抓取器 - 重构版本

    实现ICompetitorScraper接口，提供标准化的跟卖检测和抓取功能
    
    专注于跟卖店铺数据抓取，使用统一工具类
    """

    def __init__(self, selectors_config: Optional[OzonSelectorsConfig] = None,
                 browser_service=None):
        """
        初始化跟卖抓取器
        
        Args:
            selectors_config: 选择器配置
            browser_service: 浏览器服务实例（可选，默认使用全局单例）
        """
        from rpa.browser.browser_service import SimplifiedBrowserService
        from common.config.timeout_config import get_timing_config

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.selectors_config = selectors_config or get_ozon_selectors_config()
        self.timing_config = get_timing_config()

        # 🔧 修复：使用现代浏览器服务API，确保浏览器全局唯一性
        if browser_service is None:
            self.browser_service = SimplifiedBrowserService.get_global_instance()
        else:
            self.browser_service = browser_service
        # 🔧 重构：初始化统一工具类
        self.wait_utils = WaitUtils(self.browser_service, self.logger)
        self.scraping_utils = ScrapingUtils(self.logger)

    def _present_competitor_popup(self, expand: bool) -> Dict[str, Any]:
        """
        处理竞品弹窗的完整流程
        
        1. 点击竞品容器区域弹出弹窗
        2. 等待弹窗加载完成
        3. 如果需要，展开更多竞品信息
        4. 返回弹窗容器和相关信息
        
        Args:
            expand: 是否需要展开更多竞品
            
        Returns:
            Dict包含: success, popup_container, expanded等信息
        """
        try:
            self.logger.info("🔍 开始处理竞品容器点击和弹窗加载...")

            # 获取浏览器页面实例
            page = self.browser_service.get_page()
            if not page:
                self.logger.error("❌ 无法获取浏览器页面实例")
                return {"success": False, "error": "浏览器页面不可用"}

            # 极简化：点击任意竞品容器区域就会弹出pop_layer
            self.logger.info("🎯 点击竞品容器弹出pop_layer...")

            # 使用配置化的选择器策略，按优先级尝试点击
            click_selectors = self.selectors_config.competitor_area_click_selectors
            clicked = False

            for i, selector in enumerate(click_selectors):
                try:
                    self.logger.info(f"🎯 尝试点击选择器 {i+1}/{len(click_selectors)}: {selector}")

                    # 先检查元素是否存在（使用同步方法）
                    try:
                        check_timeout = self.timing_config.timeout.element_wait_timeout_ms
                        if selector.startswith("//"):
                            element_exists = self.browser_service.query_selector_sync(f"xpath={selector}", timeout=check_timeout) is not None
                        else:
                            element_exists = self.browser_service.query_selector_sync(selector, timeout=check_timeout) is not None
                        
                        if not element_exists:
                            self.logger.debug(f"⏭️  选择器 {selector} 对应的元素不存在，跳过")
                            continue
                    except TimeoutError:
                        self.logger.debug(f"⏭️  选择器 {selector} 超时，元素不存在")
                        continue
                    except Exception as check_e:
                        self.logger.debug(f"⏭️  检查选择器 {selector} 时出错: {check_e}")
                        continue

                    # 判断选择器类型并相应处理
                    click_timeout = self.timing_config.timeout.get_timeout_ms('element_wait') * 3
                    if selector.startswith("//"):
                        # XPath选择器
                        self.browser_service.click_sync(f"xpath={selector}", timeout=click_timeout)
                    else:
                        # CSS选择器
                        self.browser_service.click_sync(selector, timeout=click_timeout)

                    self.logger.info(f"✅ 成功点击竞品区域，使用选择器: {selector}")
                    clicked = True
                    break
                except TimeoutError:
                    self.logger.debug(f"⏭️  选择器 {selector} 超时")
                    continue
                except Exception as e:
                    self.logger.warning(f"⚠️ 选择器 {selector} 点击失败: {str(e)}")
                    continue

            if not clicked:
                self.logger.warning("⚠️ 未找到可点击的竞品容器，该商品可能没有跟卖信息")
                return {
                    "success": False,
                    "error": "no_competitors",
                    "popup_container": None,
                    "expanded": False
                }

            # 等待弹窗加载
            self.logger.info("⏳ 等待竞品弹窗加载...")

            wait_for_content_smart(self.selectors_config.competitor_popup_selectors, 
                                  browser_service=self.browser_service)

            # 如果需要展开更多内容
            if expand:
                self.logger.info("🔄 开始展开更多竞品信息...")
                expand_success = self._expand_competitor_list()
                if expand_success:
                    self.logger.info("✅ 成功展开更多竞品")
                    # 展开后需要更长时间等待新内容加载
                    self.logger.info("⏳ 等待展开后的内容加载...")
                    self.wait_utils.smart_wait(5.0)
                else:
                    self.logger.warning("⚠️ 展开操作失败或无需展开")

            # 获取最终的页面内容
            try:
                # 使用同步API获取页面内容
                content_timeout = self.timing_config.timeout.get_timeout_s('data_extraction')
                page_content = self.browser_service.get_page_content_sync(timeout=content_timeout)
                if not page_content:
                    self.logger.error("❌ 获取页面内容失败")
                    return {"success": False, "error": "获取页面内容失败"}
                
                popup_soup = BeautifulSoup(page_content, 'html.parser')

                # 查找弹窗容器
                popup_container = None
                for selector in self.selectors_config.competitor_popup_selectors:
                    popup_container = popup_soup.select_one(selector)
                    if popup_container:
                        self.logger.info(f"✅ 找到弹窗容器: {selector}")
                        break

                result = {
                    "success": True,
                    "popup_container": popup_container,
                    "expanded": expand
                }

                self.logger.info("🎉 竞品容器点击和弹窗加载完成")
                return result

            except TimeoutError:
                self.logger.error(f"❌ 获取页面内容超时")
                return {
                    "success": False,
                    "error": "获取页面内容超时",
                    "popup_container": None,
                    "expanded": False
                }
            except Exception as content_error:
                self.logger.error(f"❌ 获取页面内容失败: {content_error}")
                return {
                    "success": False,
                    "error": f"获取内容失败: {content_error}",
                    "popup_container": None,
                    "expanded": False
                }

        except TimeoutError as e:
            self.logger.error(f"❌ 竞品弹窗处理超时: {e}")
            return {
                "success": False,
                "error": f"操作超时: {e}",
                "popup_container": None,
                "expanded": False
            }
        except Exception as e:
            self.logger.error(f"❌ 竞品弹窗处理失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "popup_container": None,
                "expanded": False
            }

    def _find_element_by_selectors(self, selectors: List[str], timeout: Optional[int] = None) -> Optional[Any]:
        """
        通用的选择器查找方法
        
        Args:
            selectors: 选择器列表
            timeout: 超时时间（毫秒），如果为None则使用配置的默认值
            
        Returns:
            找到的元素或None
        """
        if timeout is None:
            timeout = self.timing_config.timeout.element_wait_timeout_ms
        
        for selector in selectors:
            try:
                element = self.browser_service.query_selector_sync(selector, timeout=timeout)
                if element:
                    return element
            except (TimeoutError, Exception) as e:
                self.logger.debug(f"选择器 {selector} 查找失败: {e.__class__.__name__}")
                continue
        return None

    def _expand_competitor_list(self) -> bool:
        """在pop_layer中点击展开按钮，展示更多竞品信息"""
        try:
            page = self.browser_service.get_page()
            if not page:
                self.logger.warning("⚠️ 无法获取页面对象，展开操作失败")
                return False

            self.logger.info("🔍 开始查找展开按钮...")
            click_timeout = self.timing_config.timeout.get_timeout_ms('element_wait') * 3
            
            # 尝试所有展开选择器
            for i, selector in enumerate(self.selectors_config.expand_selectors):
                try:
                    self.logger.debug(f"🎯 尝试展开选择器 {i+1}/{len(self.selectors_config.expand_selectors)}: {selector}")
                    
                    # 先检查元素是否存在
                    element = self.browser_service.query_selector_sync(selector, timeout=1000)
                    if not element:
                        self.logger.debug(f"⏭️  选择器 {selector} 未找到元素")
                        continue
                    
                    self.logger.info(f"✅ 找到展开按钮: {selector}")
                    
                    # 点击展开按钮
                    self.browser_service.click_sync(selector, timeout=click_timeout)
                    self.logger.info(f"🎉 成功点击展开按钮")
                    
                    # 等待展开内容加载
                    wait_time = self.timing_config.timeout.short_wait_s
                    self.logger.info(f"⏳ 等待 {wait_time}s 加载展开内容...")
                    self.wait_utils.smart_wait(wait_time)
                    
                    return True
                    
                except TimeoutError:
                    self.logger.debug(f"⏭️  选择器 {selector} 超时")
                    continue
                except Exception as e:
                    self.logger.debug(f"⏭️  选择器 {selector} 失败: {e.__class__.__name__}")
                    continue

            # 找不到展开按钮
            self.logger.info("ℹ️  未找到展开按钮，可能已全部显示或无需展开")
            return True  # 返回True，因为可能已经全部显示
            
        except TimeoutError:
            self.logger.warning("⚠️ 展开操作超时")
            return False
        except Exception as e:
            self.logger.warning(f"⚠️ 展开操作失败: {e.__class__.__name__}: {e}")
            return False

    def extract_competitors_from_content(self, full_pop_layer, max_competitors: int = 10) -> List[
        Dict[str, Any]]:
        """从pop_layer卖店铺信息,包括店铺ID，商品ID"""
        try:
            self.logger.info("🔍 提取跟卖店铺信息...")
            if not full_pop_layer:
                self.logger.warning("⚠️ 未找到跟卖店铺容器")
                return []

            # 查找店铺元素
            elements, selector = self._find_competitor_elements_in_soup(full_pop_layer)
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
                        # 从配置获取货币符号，避免硬编码
                        currency_symbol = getattr(self.selectors_config, 'currency_symbol', "₽")
                        self.logger.info(
                            f"✅ 提取店铺{i + 1}: {competitor_data.get('store_name', 'N/A')} - {competitor_data.get('price', 'N/A')}{currency_symbol}")
                except Exception as e:
                    self.logger.warning(f"提取第{i + 1}个店铺失败: {e.__class__.__name__}: {e}")
                    continue

            self.logger.info(f"🎉 成功提取{len(competitors)}个跟卖店铺")
            return competitors

        except Exception as e:
            self.logger.error(f"提取跟卖店铺失败: {e.__class__.__name__}: {e}")
            return []

    def _find_competitor_elements_in_soup(self, container) -> Tuple[List, Optional[str]]:
        """
          在容器中查找跟卖店铺元素
        """

        best_elements = []
        best_selector = None

        for selector in self.selectors_config.competitor_element_selectors:
            try:
                elements = container.select(selector)
                if elements and len(elements) > len(best_elements):
                    best_elements = elements
                    best_selector = selector
                    self.logger.debug(f"✅ 使用选择器 '{selector}' 找到 {len(elements)} 个跟卖店铺元素")
                    # 🔧 关键修复：继续尝试其他选择器看是否能找到更多
            except Exception as e:
                self.logger.debug(f"选择器 '{selector}' 失败: {e.__class__.__name__}")
                continue

        return best_elements, best_selector

    def _extract_competitor_from_element(self, element, ranking: int) -> Optional[Dict[str, Any]]:
        """从元素中提取跟卖店铺信息 - 🔧 修复：恢复完整的提取逻辑，确保能提取多个店铺"""
        try:
            self.logger.debug(f"🔍 开始提取第{ranking}个跟卖店铺信息...")
            competitor_data = {'ranking': ranking}

            # 🔧 修复：使用配置的店铺名称选择器，包含回退逻辑
            name_selectors = self.selectors_config.store_name_selectors
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
            price_selectors = self.selectors_config.store_price_selectors
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
            link_selectors = self.selectors_config.store_link_selectors

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
            self.logger.warning(f"从元素提取跟卖店铺信息失败: {e.__class__.__name__}: {e}")
            # 🔧 修复：即使出错也返回基本信息，避免完全丢失店铺
            return {
                'ranking': ranking,
                'store_name': f"店铺{ranking}",
                'store_id': f"store_{ranking}",
                'price': None
            }



    def _extract_store_id_from_url(self, href: str) -> Optional[str]:
        """
        从URL中提取店铺ID

        注意：此方法已重构为委托给 scraping_utils 中的通用方法，
        建议直接使用 self.scraping_utils.extract_store_id_from_url()
        """
        return self.scraping_utils.extract_store_id_from_url(href)

    

    def _get_first_competitor_product(self, popup_container, ranking: int = 1) -> Optional[Dict[str, Any]]:
        """
        获取指定排名店铺的商品ID
        
        实现策略：
        1. 优先从DOM中提取商品链接（快速）
        2. 如果找不到，则点击跳转提取（慢速）
        
        Args:
            popup_container: BeautifulSoup解析的弹窗容器
            ranking: 店铺排名，默认1（第一个店铺）
            
        Returns:
            Dict包含: success, product_id, product_url, method等信息
        """
        try:
            self.logger.info(f"🎯 开始获取排名{ranking}的店铺商品ID...")
            
            # 1. 查找指定排名的店铺元素
            elements, selector = self._find_competitor_elements_in_soup(popup_container)
            if not elements or len(elements) < ranking:
                self.logger.warning(f"⚠️ 未找到排名{ranking}的店铺元素")
                return {
                    "success": False,
                    "error": f"店铺元素不足，当前只有{len(elements)}个",
                    "product_id": None
                }
            
            target_element = elements[ranking - 1]
            self.logger.info(f"✅ 找到排名{ranking}的店铺元素")
            
            # 2. 策略A：尝试从DOM中提取商品链接
            product_info = self._extract_product_link_from_element(target_element, ranking)
            if product_info and product_info.get("product_id"):
                self.logger.info(f"✅ 通过DOM提取到商品ID: {product_info['product_id']}")
                return {
                    "success": True,
                    "product_id": product_info["product_id"],
                    "product_url": product_info.get("product_url"),
                    "method": "dom_extraction",
                    "ranking": ranking
                }
            
            # 3. 策略B：点击跳转提取（如果DOM提取失败）
            self.logger.info("⚠️ DOM中未找到商品链接，尝试点击跳转...")
            product_info = self._click_and_extract_product_id(target_element, ranking)
            if product_info and product_info.get("product_id"):
                self.logger.info(f"✅ 通过点击跳转提取到商品ID: {product_info['product_id']}")
                return {
                    "success": True,
                    "product_id": product_info["product_id"],
                    "product_url": product_info.get("product_url"),
                    "method": "click_navigation",
                    "ranking": ranking
                }
            
            # 4. 两种策略都失败
            self.logger.error(f"❌ 无法获取排名{ranking}店铺的商品ID")
            return {
                "success": False,
                "error": "所有提取策略都失败",
                "product_id": None
            }
            
        except Exception as e:
            self.logger.error(f"❌ 获取商品ID失败: {e.__class__.__name__}: {e}")
            return {
                "success": False,
                "error": str(e),
                "product_id": None
            }
    
    def _extract_product_link_from_element(self, element, ranking: int) -> Optional[Dict[str, Any]]:
        """
        从店铺元素中提取商品链接和ID（DOM方法）
        
        查找策略：
        1. 查找包含/product/的链接
        2. 排除店铺链接(/seller/)
        3. 复用工具类从URL中提取商品ID
        """
        try:
            # 查找所有链接
            all_links = element.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href', '')
                
                # 跳过店铺链接
                if '/seller/' in href:
                    continue
                
                # 查找商品链接
                if '/product/' in href:
                    self.logger.debug(f"🔍 找到商品链接: {href}")
                    
                    # 🔧 关键修复：复用工具类提取商品ID
                    product_id = self.scraping_utils.extract_product_id_from_url(href)
                    if product_id:
                        return {
                            "product_id": product_id,
                            "product_url": href if href.startswith('http') else f"https://www.ozon.ru{href}"
                        }
            
            self.logger.debug(f"⚠️ 排名{ranking}的店铺元素中未找到商品链接")
            return None
            
        except Exception as e:
            self.logger.debug(f"从DOM提取商品链接失败: {e}")
            return None
    
    
    
    def _click_and_extract_product_id(self, element, ranking: int) -> Optional[Dict[str, Any]]:
        """
        通过点击店铺元素跳转并提取商品ID（点击方法）
        
        实现策略：
        1. 在弹窗中定位到指定排名的店铺元素
        2. 点击价格区域（div.pdp_b3k）或整个店铺行
        3. 等待页面跳转到商品详情页
        4. 从新页面URL提取商品ID
        5. 返回商品ID和URL
        
        Args:
            element: BeautifulSoup店铺元素（用于确认排名）
            ranking: 店铺排名
            
        Returns:
            Dict包含product_id和product_url，失败返回None
        """
        try:
            start_time = time.time()
            self.logger.info(f"🖱️ 开始点击跳转提取排名{ranking}的商品ID...")
            
            # 获取当前页面URL作为基准
            page = self.browser_service.get_page()
            if not page:
                self.logger.error("❌ 无法获取页面对象")
                return None
            
            original_url = page.url
            self.logger.debug(f"📍 当前页面URL: {original_url}")
            
            # 构建点击选择器：定位到弹窗中第N个店铺的价格区域
            # 使用CSS选择器定位：#seller-list中的第N个店铺项的价格区域
            click_selectors = [
                f"#seller-list > div > div:nth-child({ranking}) div.pdp_b3k",  # 价格区域
                f"#seller-list > div > div:nth-child({ranking}) div.pdp_b2k.pdp_b3k",  # 完整价格区域路径
                f"#seller-list > div > div:nth-child({ranking})",  # 整个店铺行（后备方案）
            ]
            
            clicked = False
            for selector in click_selectors:
                try:
                    self.logger.debug(f"🎯 尝试点击选择器: {selector}")
                    
                    # 检查元素是否存在
                    element_exists = self.browser_service.query_selector_sync(
                        selector, 
                        timeout=self.timing_config.timeout.element_wait_timeout_ms
                    )
                    
                    if not element_exists:
                        self.logger.debug(f"⏭️  选择器 {selector} 元素不存在")
                        continue
                    
                    # 点击元素
                    click_timeout = self.timing_config.timeout.get_timeout_ms('element_wait') * 3
                    self.browser_service.click_sync(selector, timeout=click_timeout)
                    self.logger.info(f"✅ 成功点击元素: {selector}")
                    clicked = True
                    break
                    
                except TimeoutError:
                    self.logger.debug(f"⏭️  选择器 {selector} 超时")
                    continue
                except Exception as e:
                    self.logger.debug(f"⏭️  选择器 {selector} 失败: {e.__class__.__name__}")
                    continue
            
            if not clicked:
                self.logger.warning(f"⚠️ 无法点击排名{ranking}的店铺元素")
                return None
            
            # 等待页面跳转
            self.logger.info("⏳ 等待页面跳转...")
            max_wait_time = 10  # 最多等待10秒
            wait_interval = 0.5
            elapsed_time = 0
            
            while elapsed_time < max_wait_time:
                current_url = page.url
                if current_url != original_url and '/product/' in current_url:
                    self.logger.info(f"✅ 页面已跳转: {current_url}")
                    
                    # 从新页面URL提取商品ID
                    product_id = self.scraping_utils.extract_product_id_from_url(current_url)
                    if product_id:
                        execution_time = time.time() - start_time
                        self.logger.info(f"🎉 成功提取商品ID: {product_id} (耗时: {execution_time:.2f}s)")
                        return {
                            "product_id": product_id,
                            "product_url": current_url
                        }
                    else:
                        self.logger.warning(f"⚠️ 页面已跳转但无法提取商品ID: {current_url}")
                        return None
                
                time.sleep(wait_interval)
                elapsed_time += wait_interval
            
            # 超时
            self.logger.error(f"❌ 页面跳转超时({max_wait_time}s)")
            return None
            
        except TimeoutError:
            self.logger.error(f"❌ 点击跳转超时")
            return None
        except Exception as e:
            self.logger.error(f"❌ 点击跳转提取失败: {e.__class__.__name__}: {e}")
            return None

    # 标准scrape接口实现
    def scrape(self,
               url: str,
               context: Optional[Dict[str, Any]] = None,
               **kwargs) -> ScrapingResult:
        """
        统一的抓取接口（标准接口实现）

        Args:
            target: 抓取目标（商品URL）
            mode: 抓取模式
            options: 抓取选项配置
            **kwargs: 额外参数

        Returns:
            ScrapingResult: 标准化抓取结果

        Raises:
            ScrapingException: 抓取异常
            :param url:
            :param target:
            :param mode:
            :param context:
        """

        # 🔧 关键修复：在任何抓取操作前确保浏览器已正确启动
        try:
            self.logger.info("🌐 准备开始抓取，首先确保浏览器已启动...")
            # self._ensure_browser_initialized()

            # 🔧 关键修复：导航到目标页面
            self.logger.info(f"🎯 导航到目标页面: {url}")
            nav_success = self.browser_service.navigate_to_sync(url, wait_until="domcontentloaded")
            if not nav_success:
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message=f"无法导航到目标页面: {url}",
                    execution_time=0
                )
            self.logger.info("✅ 页面导航成功")

        except TimeoutError as e:
            self.logger.error(f"❌ 浏览器启动或页面导航超时: {e}")
            return ScrapingResult(
                success=False,
                data={},
                error_message=f"浏览器启动超时: {str(e)}",
                execution_time=0
            )
        except Exception as e:
            self.logger.error(f"❌ 浏览器启动或页面导航失败: {e.__class__.__name__}: {e}")
            return ScrapingResult(
                success=False,
                data={},
                error_message=f"浏览器启动失败: {str(e)}",
                execution_time=0
            )

        # 如果 context 里的 competitor_cnt = 0 或为空则直接返回
        if context and ('competitor_cnt' in context and context['competitor_cnt'] == 0):
            return ScrapingResult(
                success=True,
                data={'competitors': [], 'total_count': 0, 'scraped_at': time.time(), 'target_url': url},
                execution_time=0
            )

        # 如果 context 里的 competitor_cnt > 5 则进行expand
        # 默认情况下（context为None或没有competitor_cnt字段），不进行expand
        expand_pop_layer = False
        if context and 'competitor_cnt' in context:
            expand_pop_layer = context['competitor_cnt'] > 5
            self.logger.info(f"📊 Context competitor_cnt={context['competitor_cnt']}, expand_pop_layer={expand_pop_layer}")

        try:
            # 从kwargs中提取参数，避免重复传递
            max_competitors = kwargs.pop('max_competitors', 10)
            expand_pop_layer_param = kwargs.pop('expand_pop_layer', expand_pop_layer)
            
            self.logger.info(f"🎯 开始抓取: max_competitors={max_competitors}, expand={expand_pop_layer_param}")

            # 默认使用跟卖数据抓取
            return self._scrape(
                target_url=url,
                max_competitors=max_competitors,
                expand_pop_layer=expand_pop_layer_param,
                **kwargs
            )

        except TimeoutError as e:
            self.logger.error(f"❌ 抓取超时: {e}")
            raise RuntimeError(f"抓取超时: {str(e)}")
        except Exception as e:
            self.logger.error(f"❌ 抓取失败: {e.__class__.__name__}: {e}")
            raise RuntimeError(f"抓取失败: {str(e)}")

    def _scrape(self,
                target_url: str,
                static_soup: Optional[BeautifulSoup] = None,
                max_competitors: int = 10,
                expand_pop_layer: bool = False,
                **kwargs) -> ScrapingResult:
        """
        综合跟卖抓取（内部方法，保持向后兼容）

        Args:
            target_url: 目标商品URL
            max_competitors: 最大跟卖数量
            **kwargs: 其他参数

        Returns:
            ScrapingResult: 跟卖抓取结果
        """
        start_time = time.time()

        try:
            # 调用实际的抓取流程 - 安全获取选择器配置
            open_popup_selectors = getattr(self.selectors_config, 'open_popup_button_selector', [".pdp_bi8"])
            
            # 验证 browser_service 状态
            if not self.browser_service:
                self.logger.error("❌ browser_service 为 None，无法继续抓取")
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message="浏览器服务未初始化",
                    execution_time=time.time() - start_time
                )
            
            # 根据是否有 static_soup 决定传参方式
            if static_soup:
                result = wait_for_content_smart(open_popup_selectors,
                                                browser_service=self.browser_service,
                                                soup=static_soup)
            else:
                result = wait_for_content_smart(open_popup_selectors,
                                                browser_service=self.browser_service)

            # 弹出竞品容器并获取内容
            popup_result = self._present_competitor_popup(expand_pop_layer)

            if not popup_result.get('success'):
                # 检查是否是因为没有跟卖信息
                if popup_result.get('error') == 'no_competitors':
                    self.logger.info("ℹ️  该商品没有跟卖信息，返回空结果")
                    return ScrapingResult(
                        success=True,
                        data={
                            'competitors': [],
                            'total_count': 0,
                            'scraped_at': time.time(),
                            'target_url': target_url,
                            'has_competitors': False
                        },
                        execution_time=time.time() - start_time
                    )
                
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message=popup_result.get('error', '弹出竞品容器失败'),
                    execution_time=time.time() - start_time
                )

            # 提取竞品信息
            competitors_info = self.extract_competitors_from_content(
                popup_result.get('popup_container'), max_competitors)

            # 构建实际的抓取结果
            competitors_data = {
                'competitors': competitors_info,
                'total_count': len(competitors_info),
                'scraped_at': time.time(),
                'target_url': target_url,
                'expanded': popup_result.get('expanded', False)
            }

            # 🔧 新功能：提取第一个竞品的商品ID（如果context中启用）
            extract_first_product = kwargs.get('extract_first_product', False)
            if extract_first_product and len(competitors_info) > 0:
                self.logger.info("🎯 开始提取第一个竞品的商品ID...")
                product_result = self._get_first_competitor_product(
                    popup_result.get('popup_container'),
                    ranking=1
                )
                
                if product_result and product_result.get('success'):
                    competitors_data['first_competitor_product_id'] = product_result.get('product_id')
                    competitors_data['first_competitor_product_url'] = product_result.get('product_url')
                    competitors_data['extraction_method'] = product_result.get('method')
                    self.logger.info(f"✅ 成功提取第一个竞品商品ID: {product_result.get('product_id')}")
                else:
                    competitors_data['first_competitor_product_id'] = None
                    competitors_data['first_competitor_product_url'] = None
                    self.logger.warning("⚠️ 未能提取第一个竞品的商品ID")
            elif extract_first_product:
                self.logger.info("ℹ️  无竞品信息，跳过商品ID提取")
                competitors_data['first_competitor_product_id'] = None

            return ScrapingResult(
                success=True,
                data=competitors_data,
                execution_time=time.time() - start_time
            )

        except TimeoutError as e:
            self.logger.error(f"综合跟卖抓取超时: {e}")
            return ScrapingResult(
                success=False,
                data={},
                error_message=f"抓取超时: {str(e)}",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            self.logger.error(f"综合跟卖抓取失败: {e.__class__.__name__}: {e}")
            return ScrapingResult(
                success=False,
                data={},
                error_message=str(e),
                execution_time=time.time() - start_time
            )
