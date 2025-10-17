"""
通用分页器模块 - 基于Playwright的数字分页处理
支持各种分页场景的自动化翻页和数据提取
"""

import re
import time
from typing import Callable, Optional, Any, List
from playwright.async_api import Page
from logger_config import get_logger


class UniversalPaginator:
    """通用分页器类 - 处理数字分页的自动化翻页"""

    def __init__(self, page: Page, debug_mode: bool = False):
        """
        初始化分页器
        
        Args:
            page: Playwright页面对象
            debug_mode: 是否启用调试模式
        """
        self.page = page
        self.debug_mode = debug_mode
        self.logger = get_logger(__name__)

    def _int_from_text(self, s: str) -> Optional[int]:
        """从文本中提取数字"""
        m = re.search(r'\d+', s or '')
        return int(m.group(0)) if m else None

    async def _current_page_num(self, pager) -> Optional[int]:
        """获取当前页码"""
        try:
            # 查找当前页标识
            cur = pager.locator('[aria-current="page"], li.active, .active').first
            count = await cur.count()

            if count == 0:
                return None

            # 可能 active 在 li 或 a/span 上
            t = await cur.inner_text()
            t = t.strip()
            n = self._int_from_text(t)

            if n is None:
                # 再尝试子元素
                try:
                    child = cur.locator('a, span').first
                    t = await child.inner_text()
                    t = t.strip()
                    n = self._int_from_text(t)
                except:
                    n = None

            if self.debug_mode and n:
                self.logger.debug(f"当前页码: {n}")

            return n
        except Exception as e:
            if self.debug_mode:
                self.logger.debug(f"获取当前页码失败: {e}")
            return None

    async def _wait_page_update(self, root, items, prev_page: Optional[int],
                                prev_last_text: Optional[str], wait_api_substr: Optional[str],
                                timeout_ms: int = 15000) -> bool:
        """等待页面更新完成 - 改进版本"""
        start = time.time()
        pager = root.locator('ul.pagination').first
        responded = False

        if self.debug_mode:
            self.logger.debug(f"等待页面更新，前一页: {prev_page}, 超时: {timeout_ms}ms")

        # 如果提供了接口特征，优先等待该请求完成
        if wait_api_substr:
            try:
                async with self.page.expect_response(lambda r: wait_api_substr in r.url, timeout=timeout_ms):
                    pass
                responded = True
                if self.debug_mode:
                    self.logger.debug(f"API请求完成: {wait_api_substr}")
                # API响应后，再等待一小段时间确保DOM更新
                await self.page.wait_for_timeout(1000)
                return True
            except Exception as e:
                if self.debug_mode:
                    self.logger.debug(f"等待API请求超时: {e}")

        # 等待条件：当前页号变化 或 列表内容变化
        check_interval = 500  # 增加检查间隔
        max_checks = int(timeout_ms / check_interval)

        for check_count in range(max_checks):
            try:
                # 检查页码变化
                cur = await self._current_page_num(pager)
                if prev_page is not None and cur is not None and cur > prev_page:
                    if self.debug_mode:
                        self.logger.debug(f"页码已更新: {prev_page} -> {cur}")
                    # 页码变化后，再等待一小段时间确保内容加载
                    await self.page.wait_for_timeout(1000)
                    return True
            except Exception as e:
                if self.debug_mode:
                    self.logger.debug(f"检查页码失败: {e}")

            try:
                # 检查列表内容变化
                cnt = await items.count()
                if cnt > 0:
                    last_item = items.last
                    last_text = await last_item.inner_text()
                    # 内容变化视为更新
                    if last_text != prev_last_text and last_text:
                        if self.debug_mode:
                            self.logger.debug(f"列表内容已更新，检查次数: {check_count + 1}")
                        # 内容变化后，再等待一小段时间确保完全加载
                        await self.page.wait_for_timeout(1000)
                        return True
            except Exception as e:
                if self.debug_mode:
                    self.logger.debug(f"检查列表内容失败: {e}")

            # 等待下次检查
            await self.page.wait_for_timeout(check_interval)

        # 超时处理
        if self.debug_mode:
            elapsed = time.time() - start
            self.logger.warning(f"页面更新等待超时，耗时: {elapsed:.1f}秒，API响应: {responded}")

        # 即使超时，如果有API响应也认为可能成功
        return responded

    async def paginate_numbers(self,
                               root_selector: str,
                               item_locator: str,
                               on_page: Callable[[Any], List[Any]],
                               max_pages: Optional[int] = None,
                               wait_api_substr: Optional[str] = None) -> List[Any]:
        """
        执行数字分页遍历
        
        Args:
            root_selector: 分页根容器选择器
            item_locator: 每页列表项选择器
            on_page: 页面数据提取回调函数
            max_pages: 最大翻页数量限制
            wait_api_substr: API请求URL片段（用于等待）
            
        Returns:
            所有页面提取的数据列表
        """
        self.logger.info(f"🔄 开始执行分页遍历")
        self.logger.info(f"   根容器: {root_selector}")
        self.logger.info(f"   列表项: {item_locator}")
        self.logger.info(f"   最大页数: {max_pages or '无限制'}")

        try:
            root = self.page.locator(root_selector)
            # 等待根容器与分页条出现
            await root.wait_for(state="visible", timeout=10000)

            pager = root.locator('ul.pagination').first
            await pager.wait_for(state="visible", timeout=10000)

            items = root.locator(item_locator)
            # 等待列表出现
            await items.first.wait_for(timeout=10000)

            all_data = []
            visited_pages = set()
            page_count = 0

            while True:
                page_count += 1
                self.logger.info(f"📄 处理第 {page_count} 页")

                cur = await self._current_page_num(pager)
                # 如果拿不到当前页，尝试从"选中的 li > a"解析
                if cur is None:
                    try:
                        active_link = pager.locator('li.active a, [aria-current="page"]').first
                        text = await active_link.inner_text()
                        cur = self._int_from_text(text)
                    except:
                        cur = None

                if self.debug_mode:
                    self.logger.debug(f"当前页码: {cur}")

                # 页面数据采集
                try:
                    data = await on_page(root)
                    all_data.extend(data)
                    self.logger.info(f"✅ 第 {page_count} 页数据提取完成，获得 {len(data)} 条记录")
                except Exception as e:
                    self.logger.error(f"❌ 第 {page_count} 页数据提取失败: {e}")
                    break

                if cur is None:
                    # 拿不到当前页，保守终止
                    self.logger.warning("⚠️ 无法获取当前页码，终止分页")
                    break

                if cur in visited_pages:
                    # 防止循环
                    self.logger.warning(f"⚠️ 检测到页面循环 (页码 {cur})，终止分页")
                    break

                visited_pages.add(cur)

                if max_pages and len(visited_pages) >= max_pages:
                    self.logger.info(f"✅ 已达到最大页数限制 ({max_pages})，终止分页")
                    break

                target = str(cur + 1)

                # 优先找"下一页的数字链接"（多种方式查找）
                # 方式1: 通过role和name查找
                next_num = pager.get_by_role("link", name=re.compile(rf"^{re.escape(target)}$"))
                next_num_count = await next_num.count()

                if next_num_count == 0:
                    # 方式2: 通过button role查找
                    next_num = pager.get_by_role("button", name=re.compile(rf"^{re.escape(target)}$"))
                    next_num_count = await next_num.count()

                if next_num_count == 0:
                    # 方式3: 直接通过文本内容查找链接
                    next_num = pager.locator(f'a:has-text("{target}")')
                    next_num_count = await next_num.count()

                if next_num_count == 0:
                    # 方式4: 查找包含目标数字的任何可点击元素
                    next_num = pager.locator(f'a, button').filter(has_text=target)
                    next_num_count = await next_num.count()

                # 备用：下一页箭头（›, >, 下一页）
                next_arrow = None
                if next_num_count == 0:
                    next_arrow = (
                        pager.get_by_role("link", name=re.compile(r"(下一页|›|>|»)"))
                        .or_(pager.get_by_role("button", name=re.compile(r"(下一页|›|>|»)")))
                        .first
                    )
                    next_arrow_count = await next_arrow.count()
                else:
                    next_arrow_count = 0

                if next_num_count == 0 and next_arrow_count == 0:
                    # 没有下一页，结束
                    self.logger.info("✅ 已到达最后一页，分页完成")
                    break

                prev_last_text = None
                try:
                    last_item = items.last
                    prev_last_text = await last_item.inner_text()
                except:
                    pass

                # 执行点击并等待更新
                try:
                    if next_num_count > 0:
                        is_visible = await next_num.first.is_visible()
                        if is_visible:
                            self.logger.info(f"🔢 点击数字页码: {target}")
                            await next_num.first.click()
                        else:
                            self.logger.info(f"🔢 数字页码 {target} 不可见，使用箭头")
                            await next_arrow.click()
                    else:
                        # 使用箭头
                        self.logger.info("➡️ 点击下一页箭头")
                        await next_arrow.click()
                except Exception as e:
                    self.logger.error(f"❌ 点击分页按钮失败: {e}")
                    break

                # 等待页面更新 - 增加超时时间到20秒
                ok = await self._wait_page_update(root, items, cur, prev_last_text, wait_api_substr, timeout_ms=20000)
                if not ok:
                    self.logger.warning("⚠️ 页面更新等待超时，终止分页")
                    break

                # 添加小延迟避免过快请求
                await self.page.wait_for_timeout(500)

            self.logger.info(f"🎉 分页遍历完成！")
            self.logger.info(f"   总页数: {len(visited_pages)}")
            self.logger.info(f"   总记录数: {len(all_data)}")

            return all_data

        except Exception as e:
            self.logger.error(f"❌ 分页遍历异常: {e}")
            return []

    async def get_total_pages_from_stats(self, root_selector: str) -> Optional[int]:
        """
        从统计信息中获取总页数
        
        Args:
            root_selector: 分页根容器选择器
            
        Returns:
            总页数，如果无法获取则返回None
        """
        try:
            root = self.page.locator(root_selector)
            detail = root.locator('.fixed-table-pagination .pagination-detail').first

            await detail.wait_for(state="visible", timeout=5000)
            detail_text = await detail.inner_text()

            # 解析统计信息，例如："总共 672 条记录 每页显示 20 条记录"
            total_match = re.search(r'总共\s*(\d+)\s*条', detail_text)
            size_match = re.search(r'每页显示\s*(\d+)\s*条', detail_text)

            if total_match and size_match:
                total = int(total_match.group(1))
                size = int(size_match.group(1))
                total_pages = (total + size - 1) // size

                self.logger.info(f"📊 统计信息解析: 总记录 {total} 条，每页 {size} 条，共 {total_pages} 页")
                return total_pages

        except Exception as e:
            if self.debug_mode:
                self.logger.debug(f"获取总页数失败: {e}")

        return None

    async def get_max_page_number(self, root_selector: str) -> Optional[int]:
        """
        从分页条中获取最大页码
        
        Args:
            root_selector: 分页根容器选择器
            
        Returns:
            最大页码，如果无法获取则返回None
        """
        try:
            root = self.page.locator(root_selector)
            pager = root.locator('ul.pagination').first

            # 获取所有数字链接
            links = pager.locator('a')
            count = await links.count()

            nums = []
            for i in range(count):
                try:
                    text = await links.nth(i).inner_text()
                    text = text.strip()
                    if text.isdigit():
                        nums.append(int(text))
                except:
                    continue

            if nums:
                max_page = max(nums)
                self.logger.info(f"📊 分页条解析: 最大页码 {max_page}")
                return max_page

        except Exception as e:
            if self.debug_mode:
                self.logger.debug(f"获取最大页码失败: {e}")

        return None
