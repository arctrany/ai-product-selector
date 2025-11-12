"""
通用分页器实现

基于原有UniversalPaginator重构，遵循IPaginator接口规范
支持多种分页模式：数字分页、滚动分页、加载更多等
"""

import re
import time
import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator, Callable
from playwright.async_api import Page, ElementHandle

from ..core.interfaces.paginator import (
    IPaginator,
    IDataExtractor,
    IPaginationStrategy,
    IScrollPaginator,
    ILoadMorePaginator,
    PaginationType,
    PaginationDirection
)
from ..core.models.page_element import PageElement, ElementAttributes, ElementBounds, ElementState
from ..core.exceptions.browser_exceptions import (
    BrowserError,
    PaginationError,
    ElementNotFoundError,
    TimeoutError
)


class UniversalPaginator(IPaginator):
    """通用分页器实现 - 支持多种分页模式的统一分页器"""
    
    def __init__(self, page: Page, debug_mode: bool = False):
        """
        初始化通用分页器
        
        Args:
            page: Playwright页面对象
            debug_mode: 是否启用调试模式
        """
        self.page = page
        self.debug_mode = debug_mode
        self.root_selector = ""
        self.config = {}
        self.pagination_type = PaginationType.NUMERIC
        self.current_page_cache = None
        self.total_pages_cache = None
        self.visited_pages = set()
        
        print(f"🎯 通用分页器初始化完成")
        print(f"   调试模式: {'启用' if debug_mode else '禁用'}")

    async def initialize(self, root_selector: str, config: Dict[str, Any]) -> bool:
        """
        初始化分页器
        
        Args:
            root_selector: 分页容器选择器
            config: 分页配置
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            print(f"🔧 初始化分页器")
            print(f"   根容器: {root_selector}")
            print(f"   配置: {config}")
            
            self.root_selector = root_selector
            self.config = config
            
            # 等待根容器出现
            root = self.page.locator(root_selector)
            await root.wait_for(state="visible", timeout=10000)
            
            # 检测分页类型
            self.pagination_type = await self.detect_pagination_type()
            print(f"   检测到分页类型: {self.pagination_type.value}")
            
            # 清空缓存
            self.current_page_cache = None
            self.total_pages_cache = None
            self.visited_pages.clear()
            
            return True
            
        except Exception as e:
            print(f"❌ 分页器初始化失败: {e}")
            return False

    async def detect_pagination_type(self) -> PaginationType:
        """
        检测分页类型
        
        Returns:
            PaginationType: 检测到的分页类型
        """
        try:
            root = self.page.locator(self.root_selector)
            
            # 检测数字分页
            pagination_ul = root.locator('ul.pagination, .pagination')
            if await pagination_ul.count() > 0:
                # 检查是否有数字链接
                number_links = pagination_ul.locator('a, button').filter(has_text=re.compile(r'^\d+$'))
                if await number_links.count() > 0:
                    return PaginationType.NUMERIC
            
            # 检测加载更多按钮
            load_more_patterns = [
                'button:has-text("加载更多")',
                'button:has-text("Load More")',
                'a:has-text("加载更多")',
                'a:has-text("Load More")',
                '.load-more',
                '[data-action="load-more"]'
            ]
            
            for pattern in load_more_patterns:
                if await root.locator(pattern).count() > 0:
                    return PaginationType.LOAD_MORE
            
            # 检测无限滚动（通过检查是否有滚动容器）
            scroll_containers = root.locator('[style*="overflow"], .scroll-container, .infinite-scroll')
            if await scroll_containers.count() > 0:
                return PaginationType.INFINITE
            
            # 默认返回数字分页
            return PaginationType.NUMERIC
            
        except Exception as e:
            print(f"⚠️ 分页类型检测失败: {e}")
            return PaginationType.NUMERIC

    async def get_current_page(self) -> int:
        """
        获取当前页码
        
        Returns:
            int: 当前页码，如果无法确定返回-1
        """
        try:
            if self.pagination_type != PaginationType.NUMERIC:
                return -1
            
            root = self.page.locator(self.root_selector)
            pager = root.locator('ul.pagination, .pagination').first
            
            # 查找当前页标识
            current_selectors = [
                '[aria-current="page"]',
                'li.active',
                '.active',
                '.current',
                '[class*="current"]'
            ]
            
            for selector in current_selectors:
                current_elem = pager.locator(selector).first
                if await current_elem.count() > 0:
                    text = await current_elem.inner_text()
                    page_num = self._extract_number_from_text(text)
                    if page_num is not None:
                        self.current_page_cache = page_num
                        return page_num
                    
                    # 尝试子元素
                    child = current_elem.locator('a, span, button').first
                    if await child.count() > 0:
                        text = await child.inner_text()
                        page_num = self._extract_number_from_text(text)
                        if page_num is not None:
                            self.current_page_cache = page_num
                            return page_num
            
            return -1
            
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 获取当前页码失败: {e}")
            return -1

    async def get_total_pages(self) -> Optional[int]:
        """
        获取总页数
        
        Returns:
            Optional[int]: 总页数，如果无法确定返回None
        """
        try:
            if self.pagination_type != PaginationType.NUMERIC:
                return None
            
            # 尝试从统计信息获取
            total_from_stats = await self._get_total_pages_from_stats()
            if total_from_stats is not None:
                self.total_pages_cache = total_from_stats
                return total_from_stats
            
            # 尝试从分页条获取最大页码
            total_from_pager = await self._get_max_page_number()
            if total_from_pager is not None:
                self.total_pages_cache = total_from_pager
                return total_from_pager
            
            return None
            
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 获取总页数失败: {e}")
            return None

    async def has_next_page(self) -> bool:
        """
        检查是否有下一页
        
        Returns:
            bool: 是否有下一页
        """
        try:
            if self.pagination_type == PaginationType.NUMERIC:
                return await self._has_next_page_numeric()
            elif self.pagination_type == PaginationType.LOAD_MORE:
                return await self._has_next_page_load_more()
            elif self.pagination_type == PaginationType.INFINITE:
                return await self._has_next_page_infinite()
            else:
                return False
                
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 检查下一页失败: {e}")
            return False

    async def has_previous_page(self) -> bool:
        """
        检查是否有上一页
        
        Returns:
            bool: 是否有上一页
        """
        try:
            if self.pagination_type != PaginationType.NUMERIC:
                return False
            
            current = await self.get_current_page()
            if current <= 1:
                return False
            
            root = self.page.locator(self.root_selector)
            pager = root.locator('ul.pagination, .pagination').first
            
            # 查找上一页按钮
            prev_selectors = [
                'a:has-text("上一页")',
                'button:has-text("上一页")',
                'a:has-text("Previous")',
                'button:has-text("Previous")',
                'a:has-text("‹")',
                'button:has-text("‹")',
                'a:has-text("<")',
                'button:has-text("<")',
                '[aria-label*="previous"]',
                '[aria-label*="上一页"]'
            ]
            
            for selector in prev_selectors:
                prev_btn = pager.locator(selector).first
                if await prev_btn.count() > 0:
                    is_disabled = await prev_btn.is_disabled()
                    has_disabled_class = await prev_btn.evaluate('el => el.classList.contains("disabled")')
                    return not (is_disabled or has_disabled_class)
            
            return True
            
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 检查上一页失败: {e}")
            return False

    async def go_to_next_page(self, wait_for_load: bool = True) -> bool:
        """
        跳转到下一页
        
        Args:
            wait_for_load: 是否等待页面加载完成
            
        Returns:
            bool: 跳转是否成功
        """
        try:
            if not await self.has_next_page():
                return False
            
            if self.pagination_type == PaginationType.NUMERIC:
                return await self._go_to_next_page_numeric(wait_for_load)
            elif self.pagination_type == PaginationType.LOAD_MORE:
                return await self._go_to_next_page_load_more(wait_for_load)
            elif self.pagination_type == PaginationType.INFINITE:
                return await self._go_to_next_page_infinite(wait_for_load)
            else:
                return False
                
        except Exception as e:
            print(f"❌ 跳转下一页失败: {e}")
            return False

    async def go_to_previous_page(self, wait_for_load: bool = True) -> bool:
        """
        跳转到上一页
        
        Args:
            wait_for_load: 是否等待页面加载完成
            
        Returns:
            bool: 跳转是否成功
        """
        try:
            if not await self.has_previous_page():
                return False
            
            if self.pagination_type != PaginationType.NUMERIC:
                return False
            
            root = self.page.locator(self.root_selector)
            pager = root.locator('ul.pagination, .pagination').first
            
            # 查找上一页按钮
            prev_selectors = [
                'a:has-text("上一页")',
                'button:has-text("上一页")',
                'a:has-text("Previous")',
                'button:has-text("Previous")',
                'a:has-text("‹")',
                'button:has-text("‹")',
                'a:has-text("<")',
                'button:has-text("<")'
            ]
            
            prev_btn = None
            for selector in prev_selectors:
                btn = pager.locator(selector).first
                if await btn.count() > 0 and await btn.is_visible():
                    prev_btn = btn
                    break
            
            if prev_btn is None:
                return False
            
            # 记录当前状态
            current_page = await self.get_current_page()
            
            # 点击上一页
            print(f"⬅️ 点击上一页按钮")
            await prev_btn.click()
            
            # 等待页面更新
            if wait_for_load:
                success = await self._wait_for_page_update(current_page - 1)
                if success:
                    self.current_page_cache = current_page - 1
                return success
            
            return True
            
        except Exception as e:
            print(f"❌ 跳转上一页失败: {e}")
            return False

    async def go_to_page(self, page_number: int, wait_for_load: bool = True) -> bool:
        """
        跳转到指定页
        
        Args:
            page_number: 目标页码
            wait_for_load: 是否等待页面加载完成
            
        Returns:
            bool: 跳转是否成功
        """
        try:
            if self.pagination_type != PaginationType.NUMERIC:
                return False
            
            if page_number < 1:
                return False
            
            current = await self.get_current_page()
            if current == page_number:
                return True
            
            root = self.page.locator(self.root_selector)
            pager = root.locator('ul.pagination, .pagination').first
            
            # 查找目标页码链接
            target_str = str(page_number)
            target_selectors = [
                f'a:has-text("{target_str}")',
                f'button:has-text("{target_str}")',
                f'[aria-label="{target_str}"]'
            ]
            
            target_btn = None
            for selector in target_selectors:
                btn = pager.locator(selector).first
                if await btn.count() > 0 and await btn.is_visible():
                    # 确保是精确匹配
                    text = await btn.inner_text()
                    if text.strip() == target_str:
                        target_btn = btn
                        break
            
            if target_btn is None:
                print(f"⚠️ 未找到页码 {page_number} 的链接")
                return False
            
            # 点击目标页码
            print(f"🔢 点击页码: {page_number}")
            await target_btn.click()
            
            # 等待页面更新
            if wait_for_load:
                success = await self._wait_for_page_update(page_number)
                if success:
                    self.current_page_cache = page_number
                    self.visited_pages.add(page_number)
                return success
            
            return True
            
        except Exception as e:
            print(f"❌ 跳转到页码 {page_number} 失败: {e}")
            return False

    async def iterate_pages(self, 
                          max_pages: Optional[int] = None,
                          direction: PaginationDirection = PaginationDirection.FORWARD) -> AsyncGenerator[int, None]:
        """
        迭代所有页面
        
        Args:
            max_pages: 最大页数限制
            direction: 分页方向
            
        Yields:
            int: 当前页码
        """
        try:
            if direction != PaginationDirection.FORWARD:
                raise PaginationError("当前只支持向前分页")
            
            page_count = 0
            
            while True:
                page_count += 1
                
                # 检查页数限制
                if max_pages and page_count > max_pages:
                    print(f"✅ 已达到最大页数限制 ({max_pages})")
                    break
                
                # 获取当前页码
                current_page = await self.get_current_page()
                
                # 防止循环
                if current_page in self.visited_pages:
                    print(f"⚠️ 检测到页面循环 (页码 {current_page})")
                    break
                
                if current_page > 0:
                    self.visited_pages.add(current_page)
                
                # 返回当前页码
                yield current_page if current_page > 0 else page_count
                
                # 检查是否有下一页
                if not await self.has_next_page():
                    print("✅ 已到达最后一页")
                    break
                
                # 跳转到下一页
                success = await self.go_to_next_page(wait_for_load=True)
                if not success:
                    print("❌ 跳转下一页失败")
                    break
                
                # 添加延迟避免过快请求
                await asyncio.sleep(0.5)
                
        except Exception as e:
            print(f"❌ 页面迭代失败: {e}")
            return

    # ==================== 内部实现方法 ====================
    
    def _extract_number_from_text(self, text: str) -> Optional[int]:
        """从文本中提取数字"""
        if not text:
            return None
        match = re.search(r'\d+', text.strip())
        return int(match.group(0)) if match else None

    async def _get_total_pages_from_stats(self) -> Optional[int]:
        """从统计信息中获取总页数"""
        try:
            root = self.page.locator(self.root_selector)
            
            # 常见的统计信息选择器
            stats_selectors = [
                '.pagination-detail',
                '.fixed-table-pagination .pagination-detail',
                '.pagination-info',
                '.page-info',
                '[class*="pagination"][class*="info"]'
            ]
            
            for selector in stats_selectors:
                detail = root.locator(selector).first
                if await detail.count() > 0:
                    detail_text = await detail.inner_text()
                    
                    # 解析统计信息
                    total_match = re.search(r'总共\s*(\d+)\s*条|共\s*(\d+)\s*条|total\s*(\d+)', detail_text, re.IGNORECASE)
                    size_match = re.search(r'每页显示\s*(\d+)\s*条|每页\s*(\d+)\s*条|per\s*page\s*(\d+)', detail_text, re.IGNORECASE)
                    
                    if total_match and size_match:
                        total = int(total_match.group(1) or total_match.group(2) or total_match.group(3))
                        size = int(size_match.group(1) or size_match.group(2) or size_match.group(3))
                        total_pages = (total + size - 1) // size
                        
                        print(f"📊 统计信息解析: 总记录 {total} 条，每页 {size} 条，共 {total_pages} 页")
                        return total_pages
            
            return None
            
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 从统计信息获取总页数失败: {e}")
            return None

    async def _get_max_page_number(self) -> Optional[int]:
        """从分页条中获取最大页码"""
        try:
            root = self.page.locator(self.root_selector)
            pager = root.locator('ul.pagination, .pagination').first
            
            # 获取所有数字链接
            links = pager.locator('a, button')
            count = await links.count()
            
            page_numbers = []
            for i in range(count):
                try:
                    text = await links.nth(i).inner_text()
                    text = text.strip()
                    if text.isdigit():
                        page_numbers.append(int(text))
                except:
                    continue
            
            if page_numbers:
                max_page = max(page_numbers)
                print(f"📊 分页条解析: 最大页码 {max_page}")
                return max_page
            
            return None
            
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 从分页条获取最大页码失败: {e}")
            return None

    async def _has_next_page_numeric(self) -> bool:
        """检查数字分页是否有下一页"""
        try:
            current = await self.get_current_page()
            total = await self.get_total_pages()
            
            # 如果知道总页数，直接比较
            if total is not None and current > 0:
                return current < total
            
            # 否则查找下一页按钮
            root = self.page.locator(self.root_selector)
            pager = root.locator('ul.pagination, .pagination').first
            
            # 查找下一页数字链接
            if current > 0:
                next_page_str = str(current + 1)
                next_num = pager.locator(f'a:has-text("{next_page_str}"), button:has-text("{next_page_str}")').first
                if await next_num.count() > 0:
                    return True
            
            # 查找下一页箭头
            next_selectors = [
                'a:has-text("下一页")',
                'button:has-text("下一页")',
                'a:has-text("Next")',
                'button:has-text("Next")',
                'a:has-text("›")',
                'button:has-text("›")',
                'a:has-text(">")',
                'button:has-text(">")',
                '[aria-label*="next"]',
                '[aria-label*="下一页"]'
            ]
            
            for selector in next_selectors:
                next_btn = pager.locator(selector).first
                if await next_btn.count() > 0:
                    is_disabled = await next_btn.is_disabled()
                    has_disabled_class = await next_btn.evaluate('el => el.classList.contains("disabled")')
                    return not (is_disabled or has_disabled_class)
            
            return False
            
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 检查数字分页下一页失败: {e}")
            return False

    async def _has_next_page_load_more(self) -> bool:
        """检查加载更多是否可用"""
        try:
            root = self.page.locator(self.root_selector)
            
            load_more_selectors = [
                'button:has-text("加载更多")',
                'button:has-text("Load More")',
                'a:has-text("加载更多")',
                'a:has-text("Load More")',
                '.load-more',
                '[data-action="load-more"]'
            ]
            
            for selector in load_more_selectors:
                btn = root.locator(selector).first
                if await btn.count() > 0 and await btn.is_visible():
                    is_disabled = await btn.is_disabled()
                    return not is_disabled
            
            return False
            
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 检查加载更多失败: {e}")
            return False

    async def _has_next_page_infinite(self) -> bool:
        """检查无限滚动是否还有内容"""
        try:
            # 滚动到底部
            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            
            # 等待可能的新内容加载
            await asyncio.sleep(1)
            
            # 检查是否有加载指示器
            loading_selectors = [
                '.loading',
                '.spinner',
                '[class*="loading"]',
                '[class*="spinner"]'
            ]
            
            for selector in loading_selectors:
                if await self.page.locator(selector).count() > 0:
                    return True
            
            # 简单的启发式检查：如果页面高度还在增加，可能还有内容
            return True  # 保守返回true，让调用者决定何时停止
            
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 检查无限滚动失败: {e}")
            return False

    async def _go_to_next_page_numeric(self, wait_for_load: bool) -> bool:
        """数字分页跳转下一页"""
        try:
            current = await self.get_current_page()
            root = self.page.locator(self.root_selector)
            pager = root.locator('ul.pagination, .pagination').first
            
            next_btn = None
            
            # 优先查找下一页数字链接
            if current > 0:
                next_page_str = str(current + 1)
                next_num = pager.locator(f'a:has-text("{next_page_str}"), button:has-text("{next_page_str}")').first
                if await next_num.count() > 0 and await next_num.is_visible():
                    next_btn = next_num
                    print(f"🔢 点击数字页码: {next_page_str}")
            
            # 否则查找下一页箭头
            if next_btn is None:
                next_selectors = [
                    'a:has-text("下一页")',
                    'button:has-text("下一页")',
                    'a:has-text("Next")',
                    'button:has-text("Next")',
                    'a:has-text("›")',
                    'button:has-text("›")',
                    'a:has-text(">")',
                    'button:has-text(">")'
                ]
                
                for selector in next_selectors:
                    btn = pager.locator(selector).first
                    if await btn.count() > 0 and await btn.is_visible():
                        next_btn = btn
                        print("➡️ 点击下一页箭头")
                        break
            
            if next_btn is None:
                return False
            
            # 点击按钮
            await next_btn.click()
            
            # 等待页面更新
            if wait_for_load:
                target_page = current + 1 if current > 0 else -1
                success = await self._wait_for_page_update(target_page)
                if success and target_page > 0:
                    self.current_page_cache = target_page
                    self.visited_pages.add(target_page)
                return success
            
            return True
            
        except Exception as e:
            print(f"❌ 数字分页跳转下一页失败: {e}")
            return False

    async def _go_to_next_page_load_more(self, wait_for_load: bool) -> bool:
        """加载更多模式跳转下一页"""
        try:
            root = self.page.locator(self.root_selector)
            
            load_more_selectors = [
                'button:has-text("加载更多")',
                'button:has-text("Load More")',
                'a:has-text("加载更多")',
                'a:has-text("Load More")',
                '.load-more',
                '[data-action="load-more"]'
            ]
            
            load_more_btn = None
            for selector in load_more_selectors:
                btn = root.locator(selector).first
                if await btn.count() > 0 and await btn.is_visible():
                    load_more_btn = btn
                    break
            
            if load_more_btn is None:
                return False
            
            print("📥 点击加载更多按钮")
            await load_more_btn.click()
            
            # 等待内容加载
            if wait_for_load:
                await asyncio.sleep(2)  # 等待内容加载
            
            return True
            
        except Exception as e:
            print(f"❌ 加载更多失败: {e}")
            return False

    async def _go_to_next_page_infinite(self, wait_for_load: bool) -> bool:
        """无限滚动模式跳转下一页"""
        try:
            # 滚动到底部
            await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            
            # 等待新内容加载
            if wait_for_load:
                await asyncio.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"❌ 无限滚动失败: {e}")
            return False

    async def _wait_for_page_update(self, expected_page: int, timeout_ms: int = 15000) -> bool:
        """等待页面更新完成"""
        try:
            start_time = time.time()
            check_interval = 500
            max_checks = int(timeout_ms / check_interval)
            
            # 等待API请求（如果配置了）
            wait_api_substr = self.config.get('wait_api_substr')
            if wait_api_substr:
                try:
                    async with self.page.expect_response(
                        lambda r: wait_api_substr in r.url, 
                        timeout=timeout_ms
                    ):
                        pass
                    print(f"✅ API请求完成: {wait_api_substr}")
                    await asyncio.sleep(1)  # 等待DOM更新
                    return True
                except Exception as e:
                    if self.debug_mode:
                        print(f"⚠️ 等待API请求超时: {e}")
            
            # 等待页码变化或内容变化
            for check_count in range(max_checks):
                try:
                    # 检查页码变化
                    if expected_page > 0:
                        current = await self.get_current_page()
                        if current == expected_page:
                            print(f"✅ 页码已更新到: {expected_page}")
                            await asyncio.sleep(1)  # 确保内容完全加载
                            return True
                    
                    # 检查内容是否稳定（简单检查）
                    if check_count > 2:  # 至少等待一段时间
                        return True
                    
                except Exception as e:
                    if self.debug_mode:
                        print(f"⚠️ 检查页面更新失败: {e}")
                
                await asyncio.sleep(check_interval / 1000)
            
            # 超时但仍然返回成功（保守策略）
            elapsed = time.time() - start_time
            print(f"⚠️ 页面更新等待超时，耗时: {elapsed:.1f}秒")
            return True
            
        except Exception as e:
            print(f"❌ 等待页面更新失败: {e}")
            return False


class UniversalDataExtractor(IDataExtractor):
    """通用数据提取器实现"""
    
    def __init__(self, page: Page, debug_mode: bool = False):
        self.page = page
        self.debug_mode = debug_mode

    async def extract_page_data(self, page_number: int) -> List[Dict[str, Any]]:
        """
        提取当前页数据
        
        Args:
            page_number: 页码
            
        Returns:
            List[Dict[str, Any]]: 页面数据列表
        """
        try:
            # 这是一个通用实现，实际使用时应该根据具体需求定制
            print(f"📊 提取第 {page_number} 页数据")
            
            # 示例：提取所有可见的文本内容
            elements = await self.page.query_selector_all('[data-item], .item, .list-item, tr')
            data = []
            
            for i, element in enumerate(elements):
                try:
                    text = await element.inner_text()
                    if text and text.strip():
                        data.append({
                            'index': i,
                            'text': text.strip(),
                            'page': page_number
                        })
                except Exception as e:
                    if self.debug_mode:
                        print(f"⚠️ 提取元素 {i} 数据失败: {e}")
                    continue
            
            print(f"✅ 第 {page_number} 页提取完成，获得 {len(data)} 条记录")
            return data
            
        except Exception as e:
            print(f"❌ 提取第 {page_number} 页数据失败: {e}")
            return []

    async def extract_item_data(self, item_selector: str, item_index: int) -> Dict[str, Any]:
        """
        提取单个项目数据
        
        Args:
            item_selector: 项目选择器
            item_index: 项目索引
            
        Returns:
            Dict[str, Any]: 项目数据
        """
        try:
            elements = await self.page.query_selector_all(item_selector)
            if item_index >= len(elements):
                return {}
            
            element = elements[item_index]
            text = await element.inner_text()
            
            return {
                'index': item_index,
                'selector': item_selector,
                'text': text.strip() if text else '',
                'html': await element.inner_html()
            }
            
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 提取项目数据失败: {e}")
            return {}

    async def validate_data_completeness(self, data: List[Dict[str, Any]]) -> bool:
        """
        验证数据完整性
        
        Args:
            data: 要验证的数据
            
        Returns:
            bool: 数据是否完整
        """
        try:
            if not data:
                return False
            
            # 简单的完整性检查
            valid_count = 0
            for item in data:
                if isinstance(item, dict) and item.get('text'):
                    valid_count += 1
            
            # 至少80%的数据有效才认为完整
            completeness_ratio = valid_count / len(data)
            is_complete = completeness_ratio >= 0.8
            
            if self.debug_mode:
                print(f"📊 数据完整性: {valid_count}/{len(data)} ({completeness_ratio:.1%})")
            
            return is_complete
            
        except Exception as e:
            if self.debug_mode:
                print(f"⚠️ 验证数据完整性失败: {e}")
            return False


class SequentialPaginationStrategy(IPaginationStrategy):
    """顺序分页策略实现"""
    
    async def execute_pagination(self, 
                               paginator: IPaginator,
                               data_extractor: IDataExtractor,
                               config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        执行分页策略
        
        Args:
            paginator: 分页器实例
            data_extractor: 数据提取器实例
            config: 配置参数
            
        Returns:
            List[Dict[str, Any]]: 所有页面的数据
        """
        try:
            all_data = []
            max_pages = config.get('max_pages')
            
            print(f"🚀 开始执行顺序分页策略")
            print(f"   最大页数: {max_pages or '无限制'}")
            
            async for page_number in paginator.iterate_pages(max_pages=max_pages):
                try:
                    # 提取当前页数据
                    page_data = await data_extractor.extract_page_data(page_number)
                    
                    # 验证数据完整性
                    if await data_extractor.validate_data_completeness(page_data):
                        all_data.extend(page_data)
                    else:
                        print(f"⚠️ 第 {page_number} 页数据不完整，跳过")
                    
                except Exception as e:
                    print(f"❌ 处理第 {page_number} 页失败: {e}")
                    continue
            
            print(f"🎉 分页策略执行完成，共获得 {len(all_data)} 条记录")
            return all_data
            
        except Exception as e:
            print(f"❌ 分页策略执行失败: {e}")
            return []

    async def handle_pagination_error(self, error: Exception, context: Dict[str, Any]) -> bool:
        """
        处理分页错误
        
        Args:
            error: 发生的错误
            context: 错误上下文
            
        Returns:
            bool: 是否应该继续分页
        """
        try:
            error_type = type(error).__name__
            print(f"⚠️ 分页错误: {error_type} - {str(error)}")
            
            # 根据错误类型决定是否继续
            if isinstance(error, (TimeoutError, ElementNotFoundError)):
                # 超时或元素未找到，可以重试
                return True
            elif isinstance(error, PaginationError):
                # 分页相关错误，通常应该停止
                return False
            else:
                # 其他错误，保守停止
                return False
                
        except Exception as e:
            print(f"❌ 处理分页错误失败: {e}")
            return False