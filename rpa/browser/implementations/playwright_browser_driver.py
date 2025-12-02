"""
精简版 Playwright 浏览器驱动

🔧 重构目标：
1. 专注于 Playwright 底层操作
2. 删除配置管理逻辑（由上层处理）
3. 简化生命周期管理
4. 统一错误处理
5. 从 1041 行精简到约 300-400 行
"""

import asyncio
import os
import platform
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

from .logger_system import get_logger
from ..core.interfaces.browser_driver import IBrowserDriver
from ..core.exceptions.browser_exceptions import BrowserError, BrowserInitializationError


class SimplifiedPlaywrightBrowserDriver(IBrowserDriver):
    """
    精简版 Playwright 浏览器驱动
    
    🔧 重构后的设计原则：
    1. 只负责 Playwright 底层操作
    2. 配置由上层 BrowserService 管理
    3. 简化的生命周期管理
    4. 统一的错误处理
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 Playwright 浏览器驱动
        
        Args:
            config: 浏览器配置（由上层传入）
        """
        self.config = config or {}
        self._logger = get_logger("PlaywrightDriver")
        
        # Playwright 核心实例
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # 状态管理
        self._initialized = False
        self._is_persistent_context = False

        # 🔧 关键修复：创建专用后台事件循环线程
        self._loop_thread: Optional[threading.Thread] = None
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_ready = threading.Event()  # 用于同步线程启动

    # ==================== 生命周期管理 ====================

    def initialize(self) -> bool:
        """同步初始化浏览器驱动"""
        if self._initialized:
            return True
        
        try:
            self._logger.info("Initializing Playwright browser driver...")
            
            # 🔧 关键修复：启动专用后台事件循环线程
            if not self._event_loop or not self._event_loop.is_running():
                self._start_event_loop_thread()
                # 等待事件循环启动
                self._loop_ready.wait(timeout=5)
                if not self._event_loop:
                    raise RuntimeError("Failed to start event loop thread")
                self._logger.info(f"✅ 专用事件循环线程已启动: {self._event_loop}")

            # 在专用事件循环中初始化 Playwright
            future = asyncio.run_coroutine_threadsafe(
                self._async_initialize(),
                self._event_loop
            )
            return future.result(timeout=30)

        except Exception as e:
            self._logger.error(f"Failed to initialize browser driver: {e}")
            raise BrowserInitializationError(f"Initialization failed: {e}")

    async def _async_initialize(self) -> bool:
        """在专用事件循环中执行的异步初始化逻辑"""
        try:
            # 启动 Playwright
            self.playwright = await async_playwright().start()
            
            # 获取配置
            browser_type = self.config.get('browser_type', 'chrome')
            headless = self.config.get('headless', False)
            user_data_dir = self.config.get('user_data_dir')
            launch_args = self.config.get('launch_args', [])
            
            # 启动浏览器
            success = await self._launch_browser(
                browser_type=browser_type,
                headless=headless,
                user_data_dir=user_data_dir,
                launch_args=launch_args
            )
            
            if success and self.context:
                # 创建页面
                self.page = await self.context.new_page()
                
                # 注入反检测脚本
                await self._inject_stealth_scripts()

                self._initialized = True
                self._logger.info("Playwright browser driver initialized successfully")
                return True

            return False

        except Exception as e:
            self._logger.error(f"Failed to initialize in event loop: {e}")
            raise

    async def connect_to_existing_browser(self, cdp_url: str) -> bool:
        """
        连接到现有的浏览器实例（通过 CDP）

        Args:
            cdp_url: Chrome DevTools Protocol URL，格式如 "http://localhost:9222"

        Returns:
            bool: 连接成功返回 True，失败返回 False
        """
        try:
            self._logger.info(f"Attempting to connect to existing browser at: {cdp_url}")

            # 启动 Playwright
            if not self.playwright:
                self.playwright = await async_playwright().start()

            # 通过 CDP 连接到现有浏览器
            self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
            self._logger.info(f"Successfully connected to browser via CDP: {cdp_url}")

            # 获取或创建浏览器上下文
            contexts = self.browser.contexts
            if contexts:
                # 使用第一个现有上下文
                self.context = contexts[0]
                self._logger.info(f"Using existing browser context (found {len(contexts)} contexts)")
            else:
                # 创建新上下文
                self.context = await self.browser.new_context()
                self._logger.info("Created new browser context")

            # 获取或创建页面
            pages = self.context.pages
            if pages:
                # 使用第一个现有页面
                self.page = pages[0]
                self._logger.info(f"Using existing page (found {len(pages)} pages)")
            else:
                # 创建新页面
                self.page = await self.context.new_page()
                self._logger.info("Created new page")

            # 注入反检测脚本
            await self._inject_stealth_scripts()

            self._initialized = True
            self._is_persistent_context = False  # CDP 连接不是持久化上下文
            self._logger.info("Successfully connected to existing browser")
            return True

        except Exception as e:
            self._logger.error(f"Failed to connect to existing browser: {e}")
            # 清理部分初始化的对象
            if self.browser:
                try:
                    await self.browser.close()
                except:
                    pass
                self.browser = None
            if self.playwright:
                try:
                    await self.playwright.stop()
                except:
                    pass
                self.playwright = None
            return False

    def shutdown(self) -> bool:
        """关闭浏览器驱动 - 使用专用事件循环进行清理"""
        if not self._initialized:
            return True

        try:
            self._logger.info("Shutting down Playwright browser driver...")

            # 标记为未初始化
            self._initialized = False

            # 🔧 在专用事件循环中执行清理
            if self._event_loop and self._event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self._async_shutdown(),
                    self._event_loop
                )
                # 增加超时时间到30秒，因为浏览器关闭可能需要较长时间
                future.result(timeout=30)
            else:
                # 如果事件循环不可用，尝试直接清理
                try:
                    if self.browser:
                        self.browser.close()
                    if self.playwright:
                        self.playwright.stop()
                except Exception as e:
                    self._logger.warning(f"Error during direct cleanup: {e}")

            self._logger.info("Playwright browser driver shutdown successfully")

            # 🔧 关键修复：停止专用事件循环线程
            if self._event_loop and self._event_loop.is_running():
                self._event_loop.call_soon_threadsafe(self._event_loop.stop)
                self._logger.info("Event loop stopped")

            # 等待线程结束
            if self._loop_thread and self._loop_thread.is_alive():
                self._loop_thread.join(timeout=5)
                self._logger.info("Event loop thread joined")

            return True

        except Exception as e:
            self._logger.error(f"Failed to shutdown browser driver: {e}")
            # 确保状态重置
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
            self._initialized = False
            return False

    def __del__(self):
        """析构函数，确保资源被正确释放"""
        try:
            self.shutdown()
        except:
            # 在Python关闭阶段可能无法正常执行清理，忽略异常
            pass

    async def _async_shutdown(self) -> None:
        """在专用事件循环中执行的异步关闭逻辑"""
        try:
            # 关闭页面
            if self.page:
                try:
                    await self.page.close()
                except Exception as e:
                    self._logger.error(f"Error closing page: {e}")
                finally:
                    self.page = None

            # 关闭上下文
            if self.context:
                try:
                    await self.context.close()
                except Exception as e:
                    self._logger.error(f"Error closing context: {e}")
                finally:
                    self.context = None

            # 关闭浏览器（仅非持久化上下文）
            if self.browser and not self._is_persistent_context:
                try:
                    await self.browser.close()
                except Exception as e:
                    self._logger.error(f"Error closing browser: {e}")
                finally:
                    self.browser = None

            # 关闭 Playwright
            if self.playwright:
                try:
                    await self.playwright.stop()
                except Exception as e:
                    self._logger.error(f"Error stopping playwright: {e}")
                finally:
                    self.playwright = None

        except Exception as e:
            self._logger.error(f"Error in async shutdown: {e}")

    def is_initialized(self) -> bool:
        """检查驱动是否已初始化"""
        return self._initialized

    # ==================== 页面操作 ====================

    def open_page(self, url: str, wait_until: str = 'domcontentloaded', timeout: int = 10000) -> bool:
        """
        打开页面

        Args:
            url: 目标URL
            wait_until: 等待条件，默认 "domcontentloaded"（只等待DOM加载）
                - "domcontentloaded": 等待DOM加载完成（推荐，速度快）
                - "load": 等待所有资源加载完成（可能很慢）
                - "networkidle": 等待网络空闲
            timeout: 超时时间（毫秒），默认10秒（快速发现问题）
        """
        if not self._initialized or not self.page:
            self._logger.error("Browser driver not initialized")
            return False

        try:
            import time
            start_time = time.time()



            # 使用事件循环同步执行页面导航
            if self._event_loop and self._event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self.page.goto(url, wait_until=wait_until, timeout=timeout),
                    self._event_loop
                )
                future.result(timeout=timeout/1000 + 5)
            else:
                self._logger.error("Event loop is not running")
                return False

            elapsed = time.time() - start_time

            return True

        except Exception as e:
            elapsed = time.time() - start_time if 'start_time' in locals() else 0

            return False

    def open_page_sync(self, url: str, wait_until: str = 'domcontentloaded', timeout: int = 45000) -> bool:
        """
        同步打开页面方法 - 使用专用后台事件循环

        🔧 关键修复：使用专用后台事件循环，确保与 Playwright 对象在同一循环中

        Args:
            url: 目标URL
            wait_until: 等待条件，默认 "domcontentloaded"（只等待DOM加载）
            timeout: 超时时间（毫秒），默认45秒（适应复杂页面加载）
        """
        try:
            if not self._initialized or not self.page:
                self._logger.error("Browser driver not initialized")
                return False

            if not self._event_loop or not self._event_loop.is_running():
                self._logger.error("Event loop is not running. Browser may not be initialized properly.")
                return False

            import time
            start_time = time.time()


            # 🔧 关键修复：直接调用 page.goto() 协程，而不是同步的 open_page() 方法
            future = asyncio.run_coroutine_threadsafe(
                self.page.goto(url, wait_until=wait_until, timeout=timeout),
                self._event_loop
            )

            # 等待导航完成
            future.result(timeout=timeout/1000 + 5)

            elapsed = time.time() - start_time
            self._logger.info(f"✅ Page navigation successful after {elapsed:.2f}s: {url}")
            return True

        except TimeoutError:
            elapsed = time.time() - start_time if 'start_time' in locals() else 0
            self._logger.error(f"⏱️ Timeout opening page after {elapsed:.2f}s (timeout: {timeout}ms): {url}")
            return False
        except Exception as e:
            elapsed = time.time() - start_time if 'start_time' in locals() else 0
            self._logger.error(f"❌ Failed to open page after {elapsed:.2f}s: {url} - Error: {str(e)}")
            return False

    def navigate_to_sync(self, url: str, wait_until: str = 'domcontentloaded', timeout: int = 45000) -> bool:
        """
        同步导航到指定URL - 与SimplifiedBrowserService接口保持一致

        🔧 修复：这是open_page_sync方法的别名，用于兼容期望使用navigate_to_sync方法的代码

        Args:
            url: 目标URL
            wait_until: 等待条件，默认 "domcontentloaded"
            timeout: 超时时间（毫秒），默认45秒（适应复杂页面加载）

        Returns:
            bool: 导航是否成功
        """
        return self.open_page_sync(url, wait_until, timeout)

    async def get_page_title_async(self) -> Optional[str]:
        """获取页面标题"""
        if not self.page:
            return None
        
        try:
            return await self.page.title()
        except Exception as e:
            self._logger.error(f"Failed to get page title: {e}")
            return None

    async def screenshot_async(self, file_path: Union[str, Path]) -> Optional[Path]:
        """截图"""
        if not self.page:
            return None
        
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            await self.page.screenshot(path=str(path), full_page=True)
            self._logger.info(f"Screenshot saved: {path}")
            return path
            
        except Exception as e:
            self._logger.error(f"Failed to take screenshot: {e}")
            return None

    def execute_script(self, script: str) -> Any:
        """执行 JavaScript 脚本"""
        if not self.page:
            return None
        
        try:
            # 使用事件循环同步执行JavaScript
            if self._event_loop and self._event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self.page.evaluate(script),
                    self._event_loop
                )
                return future.result(timeout=10)
            else:
                self._logger.error("Event loop is not running")
                return None
        except Exception as e:
            self._logger.error(f"Failed to execute script: {e}")
            return None

    def get_page_url(self) -> Optional[str]:
        """
        获取当前页面URL - 同步方法

        🔧 修复：使用专用事件循环安全访问异步属性
        """
        if not self.page:
            return None

        try:
            if not self._event_loop or not self._event_loop.is_running():
                self._logger.error("Event loop is not running")
                return None

            # 通过专用事件循环安全访问异步属性
            async def get_url():
                return self.page.url

            future = asyncio.run_coroutine_threadsafe(get_url(), self._event_loop)
            return future.result(timeout=5)

        except Exception as e:
            self._logger.error(f"Failed to get page URL: {e}")
            return None

    # ==================== 元素交互方法 ====================

    def wait_for_element(self, selector: str, timeout: int = 30000) -> bool:
        """等待元素出现"""
        if not self.page:
            return False

        try:
            # 使用事件循环同步等待元素
            if self._event_loop and self._event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self.page.wait_for_selector(selector, timeout=timeout),
                    self._event_loop
                )
                future.result(timeout=timeout/1000 + 5)
                return True
            else:
                self._logger.error("Event loop is not running")
                return False
        except Exception as e:
            self._logger.error(f"Failed to wait for element {selector}: {e}")
            return False

    def click_element(self, selector: str) -> bool:
        """点击指定元素"""
        if not self.page:
            return False

        try:
            # 使用事件循环同步点击元素
            if self._event_loop and self._event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self.page.click(selector),
                    self._event_loop
                )
                future.result(timeout=10)
                return True
            else:
                self._logger.error("Event loop is not running")
                return False
        except Exception as e:
            self._logger.error(f"Failed to click element {selector}: {e}")
            return False

    def fill_input(self, selector: str, text: str) -> bool:
        """填充输入框"""
        if not self.page:
            return False

        try:
            # 使用事件循环同步填充输入框
            if self._event_loop and self._event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self.page.fill(selector, text),
                    self._event_loop
                )
                future.result(timeout=10)
                return True
            else:
                self._logger.error("Event loop is not running")
                return False
        except Exception as e:
            self._logger.error(f"Failed to fill input {selector}: {e}")
            return False

    def get_element_text(self, selector: str) -> Optional[str]:
        """获取元素文本内容"""
        if not self.page:
            return None

        try:
            # 使用事件循环同步获取元素文本
            if self._event_loop and self._event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self.page.text_content(selector),
                    self._event_loop
                )
                return future.result(timeout=10)
            else:
                self._logger.error("Event loop is not running")
                return None
        except Exception as e:
            self._logger.error(f"Failed to get element text {selector}: {e}")
            return None

    # ==================== 会话管理方法 ====================

    def verify_login_state(self, domain: str) -> Dict[str, Any]:
        """验证指定域名的登录状态"""
        result = {
            'success': False,
            'cookie_count': 0,
            'cookies': [],
            'message': ''
        }

        try:
            if not self.context:
                result['message'] = 'Browser context not available'
                return result

            # 使用事件循环同步获取cookies
            if self._event_loop and self._event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self.context.cookies(domain),
                    self._event_loop
                )
                cookies = future.result(timeout=10)
            else:
                self._logger.error("Event loop is not running")
                result['message'] = 'Event loop not available'
                return result
            result['cookie_count'] = len(cookies)
            result['cookies'] = [{'name': c['name'], 'domain': c['domain']} for c in cookies]

            if cookies:
                result['success'] = True
                result['message'] = f'Found {len(cookies)} cookies for {domain}'
                self._logger.info(f"Login state verified for {domain}: {len(cookies)} cookies")
            else:
                result['message'] = f'No cookies found for {domain}'
                self._logger.warning(f"No login cookies found for {domain}")

            return result

        except Exception as e:
            result['message'] = f'Failed to verify login state: {e}'
            self._logger.error(f"Failed to verify login state for {domain}: {e}")
            return result

    def save_storage_state(self, file_path: str) -> bool:
        """保存浏览器存储状态到文件"""
        try:
            if not self.context:
                self._logger.error("Browser context not available")
                return False

            # 使用事件循环同步保存存储状态
            if self._event_loop and self._event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self.context.storage_state(path=file_path),
                    self._event_loop
                )
                future.result(timeout=10)
            else:
                self._logger.error("Event loop is not running")
                return False
            self._logger.info(f"Storage state saved to: {file_path}")
            return True

        except Exception as e:
            self._logger.error(f"Failed to save storage state: {e}")
            return False

    def load_storage_state(self, file_path: str) -> bool:
        """从文件加载浏览器存储状态"""
        try:
            if not os.path.exists(file_path):
                self._logger.error(f"Storage state file not found: {file_path}")
                return False

            if not self.browser:
                self._logger.error("Browser not available for loading storage state")
                return False

            # 创建新上下文并加载存储状态
            if self._event_loop and self._event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self.browser.new_context(storage_state=file_path),
                    self._event_loop
                )
                new_context = future.result(timeout=10)
            else:
                self._logger.error("Event loop is not running")
                return False

            # 关闭旧上下文
            if self.context:
                if self._event_loop and self._event_loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(
                        self.context.close(),
                        self._event_loop
                    )
                    future.result(timeout=10)

            self.context = new_context

            # 重新创建页面
            if self.page:
                if self._event_loop and self._event_loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(
                        self.page.close(),
                        self._event_loop
                    )
                    future.result(timeout=10)

            if self._event_loop and self._event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(
                    self.context.new_page(),
                    self._event_loop
                )
                self.page = future.result(timeout=10)
            else:
                self._logger.error("Event loop is not running")
                return False

            self._logger.info(f"Storage state loaded from: {file_path}")
            return True

        except Exception as e:
            self._logger.error(f"Failed to load storage state: {e}")
            return False

    # ==================== 访问器方法 ====================

    def get_page(self) -> Optional[Page]:
        """获取页面对象"""
        return self.page

    def get_context(self) -> Optional[BrowserContext]:
        """获取浏览器上下文"""
        return self.context

    def get_browser(self) -> Optional[Browser]:
        """获取浏览器实例"""
        return self.browser

    # ==================== 内部实现方法 ====================

    async def _launch_browser(self, browser_type: str, headless: bool, 
                            user_data_dir: Optional[str], launch_args: List[str]) -> bool:
        """启动浏览器"""
        try:
            # 构建启动选项
            launch_options = {
                'headless': headless,
                'args': launch_args or self._get_default_launch_args()
            }
            
            # 获取浏览器 channel
            channel = self._get_browser_channel(browser_type)
            if channel:
                launch_options['channel'] = channel
            
            # 🔧 优化：简化日志输出，只显示关键信息
            self._logger.info(f"🔧 启动浏览器: {browser_type}, headless={headless}")

            # 🔧 关键修复：正确配置用户数据目录
            if user_data_dir is not None:
                import os

                # 🔧 修复根因：检查路径是否指向Profile子目录
                profile_name = "Default"  # 默认Profile
                if user_data_dir.endswith('/Default') or user_data_dir.endswith('\\Default'):
                    # 提取主User Data目录和Profile名称
                    actual_user_data_dir = os.path.dirname(user_data_dir)
                    profile_name = os.path.basename(user_data_dir)
                    self._logger.info(f"🔧 修正路径：{user_data_dir} -> {actual_user_data_dir} + Profile={profile_name}")
                else:
                    actual_user_data_dir = user_data_dir

                self._logger.info(f"🔍 使用主用户数据目录: {actual_user_data_dir}")
                self._logger.info(f"🔍 Profile名称: {profile_name}")
                self._logger.info(f"🔍 目录是否存在: {os.path.exists(actual_user_data_dir)}")

                # 🔧 关键修复：在启动参数中指定Profile
                corrected_args = launch_options.get('args', []).copy()

                # 添加Profile目录参数（如果不是Default，或者用户明确指定了）
                if profile_name != "Default" or user_data_dir.endswith(('/Default', '\\Default')):
                    profile_arg = f"--profile-directory={profile_name}"
                    if profile_arg not in corrected_args:
                        corrected_args.append(profile_arg)
                        self._logger.info(f"🔧 添加Profile参数: {profile_arg}")

                self._logger.info(f"🔍 启动参数: {corrected_args}")

                launch_options_with_extensions = {
                    'headless': headless,
                    'args': corrected_args,
                    'ignore_default_args': [
                        # 🔧 安全修复：排除不安全的参数
                        '--no-sandbox',  # 排除不安全的沙盒禁用参数
                        '--disable-setuid-sandbox',  # 排除另一个沙盒相关参数
                        # 扩展相关
                        '--disable-extensions',
                        '--disable-component-extensions-with-background-pages',
                        '--disable-default-apps',
                        '--enable-automation',
                        '--disable-component-update',
                        # 🔧 关键：忽略破坏登录状态的参数
                        '--password-store=basic',
                        '--use-mock-keychain',
                        '--disable-background-networking',
                        '--metrics-recording-only',
                        '--no-service-autorun',
                        '--disable-sync',
                    ]
                }

                # 添加 channel（如果有）
                if 'channel' in launch_options:
                    launch_options_with_extensions['channel'] = launch_options['channel']

                self._logger.info(f"🔍 最终启动配置: args={launch_options_with_extensions.get('args')}")

                # 🔧 关键修复：使用主用户数据目录（不是Profile子目录）
                self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=actual_user_data_dir,
                    **launch_options_with_extensions
                )
                self._is_persistent_context = True
                self._logger.info(f"Browser launched with custom user data dir: {user_data_dir}")
            else:
                # 🔧 关键修复：使用系统默认的用户数据目录
                # 不传 user_data_dir 参数，让 Playwright 使用默认的用户数据目录
                import os
                default_user_data_dir = None

                # 根据操作系统获取默认用户数据目录
                system = platform.system().lower()
                self._logger.info(f"🔍 检测操作系统: {system}")
                self._logger.info(f"🔍 浏览器类型: {browser_type}")

                if system == "darwin":  # macOS
                    if browser_type == 'edge':
                        default_user_data_dir = os.path.expanduser("~/Library/Application Support/Microsoft Edge")
                    else:  # chrome
                        default_user_data_dir = os.path.expanduser("~/Library/Application Support/Google/Chrome")
                elif system == "windows":
                    if browser_type == 'edge':
                        default_user_data_dir = os.path.expanduser("~/AppData/Local/Microsoft/Edge/User Data")
                    else:  # chrome
                        default_user_data_dir = os.path.expanduser("~/AppData/Local/Google/Chrome/User Data")
                elif system == "linux":
                    if browser_type == 'edge':
                        default_user_data_dir = os.path.expanduser("~/.config/microsoft-edge")
                    else:  # chrome
                        default_user_data_dir = os.path.expanduser("~/.config/google-chrome")

                self._logger.info(f"🔍 计算出的默认用户数据目录: {default_user_data_dir}")
                self._logger.info(f"🔍 默认目录是否存在: {os.path.exists(default_user_data_dir) if default_user_data_dir else False}")

                if default_user_data_dir and os.path.exists(default_user_data_dir):
                    # 🔍 DEBUG: 检查Profile目录
                    default_profile_dir = os.path.join(default_user_data_dir, "Default")
                    self._logger.info(f"🔍 Default Profile 目录: {default_profile_dir}")
                    self._logger.info(f"🔍 Default Profile 是否存在: {os.path.exists(default_profile_dir)}")

                    if os.path.exists(default_profile_dir):
                        extensions_dir = os.path.join(default_profile_dir, "Extensions")


                        if os.path.exists(extensions_dir):
                            try:
                                extensions = [d for d in os.listdir(extensions_dir) if os.path.isdir(os.path.join(extensions_dir, d))]
                                self._logger.debug(f"🔍 发现 {len(extensions)} 个扩展目录: {extensions[:5]}...")  # 只显示前5个
                            except Exception as e:
                                self._logger.debug(f"🔍 无法读取扩展目录: {e}")

                    # 使用系统默认的用户数据目录，并明确指定默认 Profile
                    # 在启动参数中添加默认 Profile 目录
                    launch_options_with_profile = launch_options.copy()
                    if '--profile-directory=Default' not in launch_options['args']:
                        launch_options_with_profile['args'] = launch_options['args'] + ['--profile-directory=Default']

                    self._logger.info(f"🔍 最终启动参数: {launch_options_with_profile['args']}")

                    # 🔧 关键修复：禁用Playwright自动添加的扩展禁用参数
                    # Playwright的launch_persistent_context会自动添加--disable-extensions等参数
                    # 我们需要明确覆盖这些参数来启用扩展
                    extension_friendly_args = launch_options_with_profile['args'] + [
                        '--enable-extensions',  # 明确启用扩展
                    ]

                    # 移除可能冲突的参数
                    filtered_args = []
                    for arg in extension_friendly_args:
                        # 跳过可能禁用扩展的参数
                        if not any(skip in arg for skip in [
                            '--disable-extensions',
                            '--disable-component-extensions',
                            '--disable-default-apps'
                        ]):
                            filtered_args.append(arg)

                    launch_options_with_profile['args'] = filtered_args

                    # 🔧 最终解决方案：强制覆盖破坏登录状态和输入记忆的参数
                    launch_options_with_profile.update({
                        'ignore_default_args': [
                            # 🔧 安全修复：排除不安全的参数
                            '--no-sandbox',  # 排除不安全的沙盒禁用参数
                            '--disable-setuid-sandbox',  # 排除另一个沙盒相关参数
                            # 扩展相关
                            '--disable-extensions',
                            '--disable-component-extensions-with-background-pages',
                            '--disable-default-apps',
                            '--enable-automation',
                            '--disable-component-update',
                            # 🔧 关键：忽略破坏登录状态的参数
                            '--password-store=basic',
                            '--use-mock-keychain',
                            '--disable-background-networking',
                            '--metrics-recording-only',
                            '--no-service-autorun',
                            '--disable-sync',
                            # 🔧 关键：忽略破坏输入记忆的参数
                            '--disable-features=AutofillShowTypePredictions',
                            '--disable-features=PasswordGeneration',
                            '--disable-background-timer-throttling',
                            # 🔧 性能优化：禁用不必要的功能以提高页面加载速度
                            '--disable-backgrounding-occluded-windows',
                            '--disable-renderer-backgrounding',
                            '--disable-ipc-flooding-protection',
                            '--disable-background-media-suspend',
                            '--no-proxy-server',  # 禁用代理以提高速度
                        ]
                    })

                    self._logger.info(f"🔧 扩展友好启动参数: {filtered_args}")

                    self.context = await self.playwright.chromium.launch_persistent_context(
                        user_data_dir=default_user_data_dir,
                        **launch_options_with_profile
                    )
                    self._is_persistent_context = True
                    self._logger.info(f"Browser launched with default user data dir: {default_user_data_dir} and Default profile")
                else:
                    # 如果找不到默认目录，创建临时上下文
                    self._logger.warning(f"🔍 默认用户数据目录不存在，使用临时上下文")
                    self.browser = await self.playwright.chromium.launch(**launch_options)
                    self.context = await self.browser.new_context()
                    self._is_persistent_context = False
                    self._logger.warning("Default user data dir not found, using temporary context")
            
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to launch browser: {e}")
            return False

    def _get_browser_channel(self, browser_type: str) -> Optional[str]:
        """获取浏览器 channel - 🔧 根据实际需求支持 Edge 和 Chrome"""
        system = platform.system().lower()

        # 🔧 修复：恢复对 Edge 和 Chrome 的支持
        # 根据 Dev.to 文章：https://dev.to/mxschmitt/running-playwright-codegen-with-existing-chromium-profiles-5g7k
        # Playwright 可以使用 Edge 的现有 Profile，需要使用 'msedge' channel
        if browser_type == 'edge' and system in ["windows", "darwin"]:
            return "msedge"
        elif browser_type == 'chrome' and system in ["windows", "darwin"]:
            return "chrome"

        # 如果需要扩展支持但不是 Edge/Chrome，则使用 Chromium
        return "chromium"

    def _start_event_loop_thread(self) -> None:
        """启动专用后台事件循环线程"""
        def run_event_loop():
            """在后台线程中运行事件循环"""
            try:
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                self._event_loop = loop

                # 通知主线程事件循环已准备好
                self._loop_ready.set()

                self._logger.info("Background event loop thread started")

                # 运行事件循环
                loop.run_forever()

            except Exception as e:
                self._logger.error(f"Error in event loop thread: {e}")
            finally:
                try:
                    loop.close()
                except Exception as e:
                    self._logger.error(f"Error closing event loop: {e}")
                self._logger.info("Background event loop thread stopped")

        # 创建并启动后台线程
        self._loop_thread = threading.Thread(target=run_event_loop, daemon=True, name="PlaywrightEventLoop")
        self._loop_thread.start()
        self._logger.info("Started background event loop thread")

    def _get_default_launch_args(self) -> List[str]:
        """获取默认启动参数 - 🔧 保持用户登录状态和输入记忆"""
        args = [
            '--no-first-run',
            '--no-default-browser-check',
            '--lang=zh-CN',
            # 🔧 关键修复：保持用户状态，移除破坏性参数
            '--disable-infobars',
            '--enable-extensions',  # 启用扩展
            # 🔧 保持登录状态的关键参数
            '--disable-blink-features=AutomationControlled',  # 🔧 修复：恢复反自动化检测参数
            '--exclude-switches=enable-automation',  # 排除自动化开关
            # 🔧 保持输入记忆的参数
            '--enable-password-generation',  # 启用密码生成
            '--enable-autofill',  # 启用自动填充
            '--enable-sync',  # 启用同步（如果用户已登录Google账户）
            # 🔧 移除这些破坏性参数：
            # '--allow-running-insecure-content',  # 这会清除安全设置
            # '--disable-web-security',  # 这会重置Cookie和存储
            # '--disable-extensions-except',  # 这会影响扩展状态
        ]

        # 🔧 新增：添加CDP端口配置支持
        if hasattr(self, '_config') and self._config and self._config.get('debug_port'):
            args.append(f'--remote-debugging-port={self._config["debug_port"]}')
        elif hasattr(self, 'config') and self.config and self.config.get('debug_port'):
            args.append(f'--remote-debugging-port={self.config["debug_port"]}')

        return args

    async def _inject_stealth_scripts(self) -> None:
        """注入反检测脚本"""
        if not self.page:
            return
        
        try:
            stealth_script = """
            // 隐藏 webdriver 属性
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });

            // 重写 chrome 属性
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };

            // 重写 plugins 属性
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
                configurable: true
            });

            // 重写 languages 属性
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en-US', 'en'],
                configurable: true
            });

            // 移除自动化相关属性
            ['cdc_adoQpoasnfa76pfcZLmcfl_Array', 'cdc_adoQpoasnfa76pfcZLmcfl_Promise', 
             'cdc_adoQpoasnfa76pfcZLmcfl_Symbol'].forEach(prop => {
                try { delete window[prop]; } catch(e) {}
            });
            """
            
            await self.page.add_init_script(stealth_script)
            
            # 设置请求头
            await self.page.set_extra_http_headers({
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            })
            
            self._logger.debug("Stealth scripts injected successfully")
            
        except Exception as e:
            self._logger.warning(f"Failed to inject stealth scripts: {e}")

    # ==================== 同步包装方法 ====================
    # 🔧 所有同步方法都使用专用事件循环，确保线程安全和事件循环一致性

    def screenshot_sync(self, file_path: Union[str, Path], timeout: int = 30000) -> Optional[Path]:
        """
        同步截图方法

        Args:
            file_path: 截图保存路径
            timeout: 超时时间（毫秒）

        Returns:
            截图文件路径，失败返回 None
        """
        try:
            if not self._event_loop or not self._event_loop.is_running():
                self._logger.error("Event loop is not running")
                return None

            future = asyncio.run_coroutine_threadsafe(
                self.screenshot_async(file_path),
                self._event_loop
            )
            return future.result(timeout=timeout/1000 + 5)

        except TimeoutError:
            self._logger.error(f"⏱️ Timeout taking screenshot: {file_path}")
            return None
        except Exception as e:
            self._logger.error(f"Failed to take screenshot: {e}")
            return None

    def get_page_title_sync(self, timeout: int = 10000) -> Optional[str]:
        """
        同步获取页面标题

        Args:
            timeout: 超时时间（毫秒）

        Returns:
            页面标题，失败返回 None
        """
        try:
            if not self._event_loop or not self._event_loop.is_running():
                self._logger.error("Event loop is not running")
                return None

            future = asyncio.run_coroutine_threadsafe(
                self.get_page_title_async(),
                self._event_loop
            )
            return future.result(timeout=timeout/1000 + 5)

        except TimeoutError:
            self._logger.error("⏱️ Timeout getting page title")
            return None
        except Exception as e:
            self._logger.error(f"Failed to get page title: {e}")
            return None

    # ==================== 页面查询同步方法 ====================

    def query_selector_sync(self, selector: str, timeout: int = 30000) -> Optional[Any]:
        """
        同步查询单个元素

        Args:
            selector: CSS 选择器
            timeout: 超时时间（毫秒）

        Returns:
            元素对象，未找到或失败返回 None
        """
        try:
            if not self.page:
                self._logger.error("Page not available")
                return None

            if not self._event_loop or not self._event_loop.is_running():
                self._logger.error("Event loop is not running")
                return None

            async def query():
                return await self.page.query_selector(selector)

            future = asyncio.run_coroutine_threadsafe(query(), self._event_loop)
            return future.result(timeout=timeout/1000 + 5)

        except TimeoutError:
            self._logger.error(f"⏱️ Timeout querying selector: {selector}")
            return None
        except Exception as e:
            self._logger.error(f"Failed to query selector {selector}: {e}")
            return None

    def query_selector_all_sync(self, selector: str, timeout: int = 30000) -> List[Any]:
        """
        同步查询所有匹配的元素

        Args:
            selector: CSS 选择器
            timeout: 超时时间（毫秒）

        Returns:
            元素列表，失败返回空列表
        """
        try:
            if not self.page:
                self._logger.error("Page not available")
                return []

            if not self._event_loop or not self._event_loop.is_running():
                self._logger.error("Event loop is not running")
                return []

            async def query_all():
                return await self.page.query_selector_all(selector)

            future = asyncio.run_coroutine_threadsafe(query_all(), self._event_loop)
            result = future.result(timeout=timeout/1000 + 5)
            return result if result else []

        except TimeoutError:
            self._logger.error(f"⏱️ Timeout querying all selectors: {selector}")
            return []
        except Exception as e:
            self._logger.error(f"Failed to query all selectors {selector}: {e}")
            return []

    def wait_for_selector_sync(self, selector: str, state: str = 'visible', timeout: int = 30000) -> bool:
        """
        同步等待元素出现

        Args:
            selector: CSS 选择器
            state: 等待状态 ('attached', 'detached', 'visible', 'hidden')
            timeout: 超时时间（毫秒）

        Returns:
            成功返回 True，失败或超时返回 False
        """
        try:
            if not self.page:
                self._logger.error("Page not available")
                return False

            if not self._event_loop or not self._event_loop.is_running():
                self._logger.error("Event loop is not running")
                return False

            async def wait():
                await self.page.wait_for_selector(selector, state=state, timeout=timeout)
                return True

            future = asyncio.run_coroutine_threadsafe(wait(), self._event_loop)
            return future.result(timeout=timeout/1000 + 5)

        except TimeoutError:
            self._logger.error(f"⏱️ Timeout waiting for selector: {selector}")
            return False
        except Exception as e:
            self._logger.error(f"Failed to wait for selector {selector}: {e}")
            return False

    # ==================== 元素交互同步方法 ====================

    def click_sync(self, selector: str, timeout: int = 30000) -> bool:
        """
        同步点击元素

        Args:
            selector: CSS 选择器
            timeout: 超时时间（毫秒）

        Returns:
            成功返回 True，失败返回 False
        """
        try:
            if not self.page:
                self._logger.error("Page not available")
                return False

            if not self._event_loop or not self._event_loop.is_running():
                self._logger.error("Event loop is not running")
                return False

            async def click():
                await self.page.click(selector, timeout=timeout)
                return True

            future = asyncio.run_coroutine_threadsafe(click(), self._event_loop)
            return future.result(timeout=timeout/1000 + 5)

        except TimeoutError:
            self._logger.error(f"⏱️ Timeout clicking selector: {selector}")
            return False
        except Exception as e:
            self._logger.error(f"Failed to click selector {selector}: {e}")
            return False

    def fill_sync(self, selector: str, value: str, timeout: int = 30000) -> bool:
        """
        同步填充输入框

        Args:
            selector: CSS 选择器
            value: 要填充的值
            timeout: 超时时间（毫秒）

        Returns:
            成功返回 True，失败返回 False
        """
        try:
            if not self.page:
                self._logger.error("Page not available")
                return False

            if not self._event_loop or not self._event_loop.is_running():
                self._logger.error("Event loop is not running")
                return False

            async def fill():
                await self.page.fill(selector, value, timeout=timeout)
                return True

            future = asyncio.run_coroutine_threadsafe(fill(), self._event_loop)
            return future.result(timeout=timeout/1000 + 5)

        except TimeoutError:
            self._logger.error(f"⏱️ Timeout filling selector: {selector}")
            return False
        except Exception as e:
            self._logger.error(f"Failed to fill selector {selector}: {e}")
            return False

    def type_sync(self, selector: str, text: str, delay: Optional[float] = None, timeout: int = 30000) -> bool:
        """
        同步输入文本（模拟打字）

        Args:
            selector: CSS 选择器
            text: 要输入的文本
            delay: 按键之间的延迟（毫秒），None 表示无延迟
            timeout: 超时时间（毫秒）

        Returns:
            成功返回 True，失败返回 False
        """
        try:
            if not self.page:
                self._logger.error("Page not available")
                return False

            if not self._event_loop or not self._event_loop.is_running():
                self._logger.error("Event loop is not running")
                return False

            async def type_text():
                if delay is not None:
                    await self.page.type(selector, text, delay=delay, timeout=timeout)
                else:
                    await self.page.type(selector, text, timeout=timeout)
                return True

            future = asyncio.run_coroutine_threadsafe(type_text(), self._event_loop)
            return future.result(timeout=timeout/1000 + 5)

        except TimeoutError:
            self._logger.error(f"⏱️ Timeout typing into selector: {selector}")
            return False
        except Exception as e:
            self._logger.error(f"Failed to type into selector {selector}: {e}")
            return False

    def select_option_sync(self, selector: str, value: Union[str, List[str]], timeout: int = 30000) -> bool:
        """
        同步选择下拉框选项

        Args:
            selector: CSS 选择器
            value: 要选择的值（单个或多个）
            timeout: 超时时间（毫秒）

        Returns:
            成功返回 True，失败返回 False
        """
        try:
            if not self.page:
                self._logger.error("Page not available")
                return False

            if not self._event_loop or not self._event_loop.is_running():
                self._logger.error("Event loop is not running")
                return False

            async def select():
                await self.page.select_option(selector, value, timeout=timeout)
                return True

            future = asyncio.run_coroutine_threadsafe(select(), self._event_loop)
            return future.result(timeout=timeout/1000 + 5)

        except TimeoutError:
            self._logger.error(f"⏱️ Timeout selecting option in selector: {selector}")
            return False
        except Exception as e:
            self._logger.error(f"Failed to select option in selector {selector}: {e}")
            return False

    # ==================== 页面状态同步方法 ====================

    def inner_text_sync(self, selector: str, timeout: int = 30000) -> Optional[str]:
        """
        同步获取元素的 innerText

        Args:
            selector: CSS 选择器
            timeout: 超时时间（毫秒）

        Returns:
            元素的 innerText，失败返回 None
        """
        try:
            if not self.page:
                self._logger.error("Page not available")
                return None

            if not self._event_loop or not self._event_loop.is_running():
                self._logger.error("Event loop is not running")
                return None

            async def get_text():
                return await self.page.inner_text(selector, timeout=timeout)

            future = asyncio.run_coroutine_threadsafe(get_text(), self._event_loop)
            return future.result(timeout=timeout/1000 + 5)

        except TimeoutError:
            self._logger.error(f"⏱️ Timeout getting inner text of selector: {selector}")
            return None
        except Exception as e:
            self._logger.error(f"Failed to get inner text of selector {selector}: {e}")
            return None

    def text_content_sync(self, selector: str, timeout: int = 30000) -> Optional[str]:
        """
        同步获取元素的 textContent

        Args:
            selector: CSS 选择器
            timeout: 超时时间（毫秒）

        Returns:
            元素的 textContent，失败返回 None
        """
        try:
            if not self.page:
                self._logger.error("Page not available")
                return None

            if not self._event_loop or not self._event_loop.is_running():
                self._logger.error("Event loop is not running")
                return None

            async def get_content():
                return await self.page.text_content(selector, timeout=timeout)

            future = asyncio.run_coroutine_threadsafe(get_content(), self._event_loop)
            return future.result(timeout=timeout/1000 + 5)

        except TimeoutError:
            self._logger.error(f"⏱️ Timeout getting text content of selector: {selector}")
            return None
        except Exception as e:
            self._logger.error(f"Failed to get text content of selector {selector}: {e}")
            return None

    def get_page_content_sync(self, timeout: int = 10) -> Optional[str]:
        """
        同步获取页面完整HTML内容

        Args:
            timeout: 超时时间（秒）

        Returns:
            页面HTML内容，失败返回 None
        """
        try:
            if not self.page:
                self._logger.error("Page not available")
                return None

            if not self._event_loop or not self._event_loop.is_running():
                self._logger.error("Event loop is not running")
                return None

            async def get_content():
                return await self.page.content()

            future = asyncio.run_coroutine_threadsafe(get_content(), self._event_loop)
            return future.result(timeout=timeout)

        except TimeoutError:
            self._logger.error(f"⏱️ Timeout getting page content")
            return None
        except Exception as e:
            self._logger.error(f"Failed to get page content: {e}")
            return None

    def get_attribute_sync(self, selector: str, name: str, timeout: int = 30000) -> Optional[str]:
        """
        同步获取元素属性值

        Args:
            selector: CSS 选择器
            name: 属性名
            timeout: 超时时间（毫秒）

        Returns:
            属性值，失败返回 None
        """
        try:
            if not self.page:
                self._logger.error("Page not available")
                return None

            if not self._event_loop or not self._event_loop.is_running():
                self._logger.error("Event loop is not running")
                return None

            async def get_attr():
                return await self.page.get_attribute(selector, name, timeout=timeout)

            future = asyncio.run_coroutine_threadsafe(get_attr(), self._event_loop)
            return future.result(timeout=timeout/1000 + 5)

        except TimeoutError:
            self._logger.error(f"⏱️ Timeout getting attribute '{name}' of selector: {selector}")
            return None
        except Exception as e:
            self._logger.error(f"Failed to get attribute '{name}' of selector {selector}: {e}")
            return None

    def is_visible_sync(self, selector: str, timeout: int = 5000) -> bool:
        """
        同步检查元素是否可见

        Args:
            selector: CSS 选择器
            timeout: 超时时间（毫秒）

        Returns:
            可见返回 True，不可见或失败返回 False
        """
        try:
            if not self.page:
                self._logger.error("Page not available")
                return False

            if not self._event_loop or not self._event_loop.is_running():
                self._logger.error("Event loop is not running")
                return False

            async def check_visible():
                return await self.page.is_visible(selector, timeout=timeout)

            future = asyncio.run_coroutine_threadsafe(check_visible(), self._event_loop)
            return future.result(timeout=timeout/1000 + 5)

        except TimeoutError:
            self._logger.debug(f"⏱️ Timeout checking visibility of selector: {selector}")
            return False
        except Exception as e:
            self._logger.debug(f"Element not visible {selector}: {e}")
            return False

    # ==================== 工具方法同步封装 ====================

    def evaluate_sync(self, script: str, timeout: int = 30000) -> Any:
        """
        同步执行 JavaScript 脚本

        Args:
            script: JavaScript 代码
            timeout: 超时时间（毫秒）

        Returns:
            脚本执行结果，失败返回 None
        """
        try:
            if not self.page:
                self._logger.error("Page not available")
                return None

            if not self._event_loop or not self._event_loop.is_running():
                self._logger.error("Event loop is not running")
                return None

            async def evaluate():
                return await self.page.evaluate(script)

            future = asyncio.run_coroutine_threadsafe(evaluate(), self._event_loop)
            return future.result(timeout=timeout/1000 + 5)

        except TimeoutError:
            self._logger.error(f"⏱️ Timeout evaluating script")
            return None
        except Exception as e:
            self._logger.error(f"Failed to evaluate script: {e}")
            return None

    # ==================== 上下文管理器 ====================

    def __enter__(self):
        """同步上下文管理器入口"""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """同步上下文管理器出口"""
        self.shutdown()

    # ==================== 向后兼容接口实现 ====================

    def get_page_title(self) -> Optional[str]:
        """
        同步获取页面标题方法（向后兼容）

        Returns:
            Optional[str]: 页面标题
        """
        return self.get_page_title_sync()

    def screenshot(self, file_path: Union[str, Path]) -> Optional[Path]:
        """
        同步截图方法（向后兼容）

        Args:
            file_path: 截图保存路径

        Returns:
            Optional[Path]: 截图文件路径
        """
        return self.screenshot_sync(file_path)

    def navigate(self, url: str, wait_until: str = "domcontentloaded") -> bool:
        """
        导航到指定URL（向后兼容方法）

        这是navigate_to_sync方法的别名，用于兼容期望使用navigate方法的测试代码

        Args:
            url: 目标URL
            wait_until: 等待条件

        Returns:
            bool: 导航是否成功
        """
        return self.navigate_to_sync(url, wait_until)

    def close(self):
        """
        关闭浏览器驱动（向后兼容）

        这是shutdown方法的别名，用于兼容期望使用close方法的代码
        """
        self.shutdown()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.shutdown()


# 向后兼容别名
PlaywrightBrowserDriver = SimplifiedPlaywrightBrowserDriver

__all__ = [
    'SimplifiedPlaywrightBrowserDriver',
    'PlaywrightBrowserDriver'
]