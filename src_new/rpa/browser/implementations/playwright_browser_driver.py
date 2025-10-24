"""
Playwright浏览器驱动实现

基于原有BrowserService重构，遵循IBrowserDriver接口规范
支持跨平台浏览器管理、调试端口管理、页面生命周期管理
"""

import asyncio
import os
import platform
import subprocess
import time
import threading
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

from ..core.interfaces.browser_driver import IBrowserDriver, IPageManager, IResourceManager
from ..core.models.browser_config import BrowserConfig, ViewportConfig, ProxyConfig
from ..core.models.page_element import PageElement
from ..core.exceptions.browser_exceptions import (
    BrowserInitializationError,
    BrowserConnectionError,
    PageNavigationError,
    BrowserTimeoutError,
    ResourceManagementError,
    handle_browser_error
)


class PlaywrightBrowserDriver(IBrowserDriver):
    """Playwright浏览器驱动实现"""
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        """
        初始化Playwright浏览器驱动
        
        Args:
            config: 浏览器配置，如果为None则使用默认配置
        """
        from ..core.models.browser_config import create_default_config
        self.config = config or create_default_config()
        
        # Playwright相关对象
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # 内部状态管理
        self._pw_loop: Optional[asyncio.AbstractEventLoop] = None
        self._initialized = False
        self._lock = threading.Lock()
        
        # 浏览器进程信息
        self.current_browser_executable: Optional[str] = None
        self.current_user_data_dir: Optional[str] = None
        
        print(f"🎯 Playwright浏览器驱动初始化完成")
        print(f"   浏览器类型: {self.config.browser_type}")
        print(f"   调试端口: {self.config.debug_port}")
        print(f"   无头模式: {self.config.headless}")

    async def initialize(self) -> bool:
        """
        初始化浏览器驱动
        
        Returns:
            bool: 初始化是否成功
            
        Raises:
            BrowserInitializationError: 初始化失败时抛出
        """
        try:
            with self._lock:
                if self._initialized:
                    print("✅ 浏览器驱动已初始化")
                    return True
                
                print("🔧 开始初始化浏览器驱动...")
                
                # 自动检测可用浏览器
                executable_path, user_data_dir, detected_browser_type = self._get_browser_paths()
                
                if not executable_path:
                    raise BrowserInitializationError("未找到可用的浏览器")
                
                # 更新配置中的浏览器类型
                self.config.browser_type = detected_browser_type
                self.current_browser_executable = executable_path
                self.current_user_data_dir = user_data_dir
                
                browser_name = "Edge" if detected_browser_type == "edge" else "Chrome"
                print(f"✅ 检测到{browser_name}: {executable_path}")
                
                # 启动浏览器调试实例
                if not self._launch_browser_with_debug_port():
                    raise BrowserInitializationError("启动浏览器调试实例失败")
                
                # 连接到浏览器实例
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.connect_over_cdp(
                    f"http://localhost:{self.config.debug_port}"
                )
                
                print(f"✅ 成功连接到{browser_name}实例")
                
                # 获取或创建浏览器上下文
                await self._setup_browser_context()
                
                # 获取或创建页面
                await self._setup_initial_page()
                
                # 保存事件循环引用
                self._pw_loop = asyncio.get_running_loop()
                
                # 绑定事件监听
                self._bind_context_events()
                
                self._initialized = True
                print("✅ 浏览器驱动初始化完成")
                return True
                
        except Exception as e:
            raise BrowserInitializationError(f"浏览器驱动初始化失败: {str(e)}") from e

    async def navigate_to(self, url: str, wait_until: str = 'networkidle') -> bool:
        """
        导航到指定URL

        Args:
            url: 目标URL
            wait_until: 等待条件

        Returns:
            bool: 导航是否成功
        """
        try:
            if not self.page:
                raise PageNavigationError("页面未初始化")

            print(f"🌐 导航到: {url}")
            await self.page.goto(url, wait_until=wait_until, timeout=self.config.page_timeout)
            print("✅ 页面导航完成")
            return True

        except Exception as e:
            print(f"❌ 页面导航失败: {str(e)}")
            return False

    async def find_element(self, selector: str, timeout: int = 10000) -> Optional[PageElement]:
        """
        查找页面元素

        Args:
            selector: 元素选择器
            timeout: 超时时间(毫秒)

        Returns:
            Optional[PageElement]: 找到的元素，未找到返回None
        """
        try:
            if not self.page:
                return None

            element = await self.page.wait_for_selector(selector, timeout=timeout)
            if element:
                return PageElement(
                    selector=selector,
                    tag_name=await element.evaluate('el => el.tagName.toLowerCase()'),
                    text=await element.text_content() or "",
                    attributes=await element.evaluate('el => Object.fromEntries(Array.from(el.attributes).map(attr => [attr.name, attr.value]))')
                )
            return None

        except Exception as e:
            print(f"⚠️ 查找元素失败: {str(e)}")
            return None

    async def find_elements(self, selector: str, timeout: int = 10000) -> List[PageElement]:
        """
        查找多个页面元素

        Args:
            selector: 元素选择器
            timeout: 超时时间(毫秒)

        Returns:
            List[PageElement]: 找到的元素列表
        """
        try:
            if not self.page:
                return []

            elements = await self.page.query_selector_all(selector)
            result = []

            for element in elements:
                page_element = PageElement(
                    selector=selector,
                    tag_name=await element.evaluate('el => el.tagName.toLowerCase()'),
                    text=await element.text_content() or "",
                    attributes=await element.evaluate('el => Object.fromEntries(Array.from(el.attributes).map(attr => [attr.name, attr.value]))')
                )
                result.append(page_element)

            return result

        except Exception as e:
            print(f"⚠️ 查找多个元素失败: {str(e)}")
            return []

    async def click_element(self, selector: str, timeout: int = 10000) -> bool:
        """
        点击页面元素

        Args:
            selector: 元素选择器
            timeout: 超时时间(毫秒)

        Returns:
            bool: 点击是否成功
        """
        try:
            if not self.page:
                return False

            await self.page.click(selector, timeout=timeout)
            return True

        except Exception as e:
            print(f"⚠️ 点击元素失败: {str(e)}")
            return False

    async def input_text(self, selector: str, text: str, timeout: int = 10000) -> bool:
        """
        向元素输入文本

        Args:
            selector: 元素选择器
            text: 要输入的文本
            timeout: 超时时间(毫秒)

        Returns:
            bool: 输入是否成功
        """
        try:
            if not self.page:
                return False

            await self.page.fill(selector, text, timeout=timeout)
            return True

        except Exception as e:
            print(f"⚠️ 输入文本失败: {str(e)}")
            return False

    async def take_screenshot(self, full_page: bool = False) -> Optional[bytes]:
        """
        截取页面截图

        Args:
            full_page: 是否截取整个页面

        Returns:
            Optional[bytes]: 截图数据，失败返回None
        """
        try:
            if not self.page:
                return None

            screenshot_bytes = await self.page.screenshot(full_page=full_page, type='png')
            return screenshot_bytes

        except Exception as e:
            print(f"⚠️ 截图失败: {str(e)}")
            return None

    async def execute_script(self, script: str, *args) -> Any:
        """
        执行JavaScript脚本

        Args:
            script: JavaScript代码
            *args: 脚本参数

        Returns:
            Any: 脚本执行结果
        """
        try:
            if not self.page:
                return None

            return await self.page.evaluate(script, *args)

        except Exception as e:
            print(f"⚠️ 执行脚本失败: {str(e)}")
            return None

    async def wait_for_element(self, selector: str, timeout: int = 10000) -> bool:
        """
        等待元素出现

        Args:
            selector: 元素选择器
            timeout: 超时时间(毫秒)

        Returns:
            bool: 元素是否出现
        """
        try:
            if not self.page:
                return False

            await self.page.wait_for_selector(selector, timeout=timeout)
            return True

        except Exception as e:
            print(f"⚠️ 等待元素失败: {str(e)}")
            return False

    async def get_page_title(self) -> str:
        """
        获取页面标题

        Returns:
            str: 页面标题
        """
        try:
            if not self.page:
                return ""

            return await self.page.title()

        except Exception as e:
            print(f"⚠️ 获取页面标题失败: {str(e)}")
            return ""

    async def get_current_url(self) -> str:
        """
        获取当前页面URL

        Returns:
            str: 当前URL
        """
        try:
            if not self.page:
                return ""

            return self.page.url

        except Exception as e:
            print(f"⚠️ 获取当前URL失败: {str(e)}")
            return ""

    async def close(self) -> None:
        """关闭浏览器驱动，释放资源"""
        await self.cleanup()

    async def cleanup(self) -> bool:
        """
        清理浏览器资源
        
        Returns:
            bool: 清理是否成功
        """
        try:
            with self._lock:
                if not self._initialized:
                    return True
                
                print("🧹 开始清理浏览器资源...")
                
                # 关闭页面
                if self.page:
                    try:
                        await self.page.close()
                        print("✅ 页面已关闭")
                    except Exception as e:
                        print(f"⚠️ 关闭页面时出现警告: {e}")
                
                # 关闭上下文
                if self.context:
                    try:
                        await self.context.close()
                        print("✅ 浏览器上下文已关闭")
                    except Exception as e:
                        print(f"⚠️ 关闭上下文时出现警告: {e}")
                
                # 关闭浏览器连接
                if self.browser:
                    try:
                        await self.browser.close()
                        print("✅ 浏览器连接已关闭")
                    except Exception as e:
                        print(f"⚠️ 关闭浏览器连接时出现警告: {e}")
                
                # 停止Playwright
                if self.playwright:
                    try:
                        await self.playwright.stop()
                        print("✅ Playwright已停止")
                    except Exception as e:
                        print(f"⚠️ 停止Playwright时出现警告: {e}")
                
                # 重置状态
                self.page = None
                self.context = None
                self.browser = None
                self.playwright = None
                self._pw_loop = None
                self._initialized = False
                
                print("✅ 浏览器资源清理完成")
                return True
                
        except Exception as e:
            print(f"❌ 清理浏览器资源失败: {str(e)}")
            return False

    def is_initialized(self) -> bool:
        """
        检查驱动是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        return self._initialized and all([
            self.playwright, 
            self.browser, 
            self.context, 
            self.page
        ])

    async def get_page_manager(self) -> IPageManager:
        """
        获取页面管理器
        
        Returns:
            IPageManager: 页面管理器实例
        """
        return PlaywrightPageManager(self)

    async def get_resource_manager(self) -> IResourceManager:
        """
        获取资源管理器
        
        Returns:
            IResourceManager: 资源管理器实例
        """
        return PlaywrightResourceManager(self)

    def get_config(self) -> BrowserConfig:
        """
        获取当前配置
        
        Returns:
            BrowserConfig: 浏览器配置
        """
        return self.config

    async def update_config(self, config: BrowserConfig) -> bool:
        """
        更新配置
        
        Args:
            config: 新的浏览器配置
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 检查是否需要重新初始化
            needs_reinit = (
                config.browser_type != self.config.browser_type or
                config.debug_port != self.config.debug_port or
                config.headless != self.config.headless
            )
            
            self.config = config
            
            if needs_reinit and self._initialized:
                print("🔄 配置变更需要重新初始化浏览器...")
                await self.cleanup()
                return await self.initialize()
            
            print("✅ 配置更新完成")
            return True
            
        except Exception as e:
            print(f"❌ 更新配置失败: {str(e)}")
            return False

    # ==================== 内部实现方法 ====================
    
    def _get_browser_paths(self) -> tuple[Optional[str], Optional[str], str]:
        """
        获取浏览器路径信息
        
        Returns:
            tuple: (可执行文件路径, 用户数据目录, 浏览器类型)
        """
        system = platform.system()
        
        # 优先尝试Edge
        edge_path = self._get_edge_executable_path(system)
        if edge_path and os.path.exists(edge_path):
            user_data_dir = self._get_edge_user_data_dir(system)
            return edge_path, user_data_dir, "edge"
        
        # 回退到Chrome
        chrome_path = self._get_chrome_executable_path(system)
        if chrome_path and os.path.exists(chrome_path):
            user_data_dir = self._get_chrome_user_data_dir(system)
            return chrome_path, user_data_dir, "chrome"
        
        return None, None, "chrome"

    def _get_edge_executable_path(self, system: str) -> Optional[str]:
        """获取Edge可执行文件路径"""
        if system == "Darwin":  # macOS
            return "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
        elif system == "Windows":
            paths = [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
            ]
            for path in paths:
                if os.path.exists(path):
                    return path
        elif system == "Linux":
            return "/usr/bin/microsoft-edge"
        return None

    def _get_chrome_executable_path(self, system: str) -> Optional[str]:
        """获取Chrome可执行文件路径"""
        if system == "Darwin":  # macOS
            return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        elif system == "Windows":
            paths = [
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            ]
            for path in paths:
                if os.path.exists(path):
                    return path
        elif system == "Linux":
            return "/usr/bin/google-chrome"
        return None

    def _get_edge_user_data_dir(self, system: str) -> str:
        """获取Edge用户数据目录"""
        if system == "Darwin":  # macOS
            return os.path.expanduser("~/Library/Application Support/Microsoft Edge")
        elif system == "Windows":
            return os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\User Data")
        else:  # Linux
            return os.path.expanduser("~/.config/microsoft-edge")

    def _get_chrome_user_data_dir(self, system: str) -> str:
        """获取Chrome用户数据目录"""
        if system == "Darwin":  # macOS
            return os.path.expanduser("~/Library/Application Support/Google/Chrome")
        elif system == "Windows":
            return os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data")
        else:  # Linux
            return os.path.expanduser("~/.config/google-chrome")

    def _check_debug_port(self, port: int) -> bool:
        """检查调试端口是否可用"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result == 0
        except Exception:
            return False

    def _launch_browser_with_debug_port(self) -> bool:
        """启动带调试端口的浏览器实例"""
        try:
            executable_path = self.current_browser_executable
            user_data_dir = self.current_user_data_dir
            debug_port = self.config.debug_port
            
            if not executable_path:
                return False
            
            browser_name = "Edge" if self.config.browser_type == "edge" else "Chrome"
            
            # 检查端口是否已被占用
            if self._check_debug_port(debug_port):
                print(f"✅ 调试端口{debug_port}已可用，跳过浏览器启动")
                return True
            
            print(f"🚀 启动{browser_name}实例，调试端口: {debug_port}")
            
            # 构建启动参数
            browser_args = self._build_browser_args(executable_path, user_data_dir, debug_port)
            
            # 启动浏览器进程
            process = subprocess.Popen(
                browser_args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )
            
            # 等待浏览器启动
            print(f"⏳ 等待{browser_name}启动...")
            for i in range(15):
                time.sleep(1)
                if self._check_debug_port(debug_port):
                    print(f"✅ {browser_name}启动成功，调试端口{debug_port}可用")
                    return True
                print(f"⏳ 等待中... ({i + 1}/15)")
            
            print(f"❌ {browser_name}启动超时")
            return False
            
        except Exception as e:
            print(f"❌ 启动浏览器失败: {str(e)}")
            return False

    def _build_browser_args(self, executable_path: str, user_data_dir: str, debug_port: int) -> List[str]:
        """构建浏览器启动参数"""
        args = [
            executable_path,
            f"--remote-debugging-port={debug_port}",
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-default-apps",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--enable-extensions",
            "--disable-popup-blocking",
            "--disable-notifications",
            "--disable-desktop-notifications",
            "--no-sandbox",
            "--disable-web-security",
            "--disable-blink-features=AutomationControlled",
            "about:blank"
        ]
        
        # 添加无头模式参数
        if self.config.headless:
            args.append("--headless=new")
        else:
            # 有头模式下的窗口管理参数
            args.extend([
                "--window-position=-2000,-2000",
                "--window-size=800,600",
                "--start-minimized",
                "--silent-launch"
            ])
        
        return args

    async def _setup_browser_context(self):
        """设置浏览器上下文"""
        contexts = self.browser.contexts
        if contexts:
            self.context = contexts[0]
            print(f"✅ 使用现有浏览器上下文，页面数量: {len(self.context.pages)}")
        else:
            # 构建上下文选项
            context_options = {
                'viewport': {
                    'width': self.config.viewport.width,
                    'height': self.config.viewport.height
                },
                'user_agent': self.config.user_agent
            }
            
            # 添加代理配置
            if self.config.proxy and self.config.proxy.server:
                context_options['proxy'] = {
                    'server': self.config.proxy.server,
                    'username': self.config.proxy.username,
                    'password': self.config.proxy.password
                }
            
            self.context = await self.browser.new_context(**context_options)
            print("✅ 创建新的浏览器上下文")

    async def _setup_initial_page(self):
        """设置初始页面"""
        pages = self.context.pages
        if pages:
            self.page = pages[0]
            print("✅ 使用现有页面")
        else:
            self.page = await self.context.new_page()
            print("✅ 创建新页面")
        
        # 设置页面超时
        self.page.set_default_timeout(self.config.page_timeout)

    def _bind_context_events(self):
        """绑定上下文事件监听"""
        if not self.context:
            return
        
        try:
            # 监听新页面创建
            self.context.on("page", self._on_new_page)
            print("✅ 已绑定上下文事件监听")
        except Exception as e:
            print(f"⚠️ 绑定上下文事件失败: {e}")

    def _on_new_page(self, page: Page):
        """新页面创建时的回调"""
        try:
            print(f"🆕 检测到新页面: {page.url}")
            # 更新当前页面引用为最新页面
            self.page = page
        except Exception as e:
            print(f"⚠️ 处理新页面时出现警告: {e}")


class PlaywrightPageManager(IPageManager):
    """Playwright页面管理器实现"""
    
    def __init__(self, driver: PlaywrightBrowserDriver):
        self.driver = driver
        self.page_registry = {}  # 页面ID到页面对象的映射

    async def new_page(self) -> str:
        """
        创建新页面

        Returns:
            str: 页面ID
        """
        try:
            if not self.driver.context:
                raise BrowserConnectionError("浏览器上下文未初始化")

            page = await self.driver.context.new_page()
            page_id = str(id(page))
            self.page_registry[page_id] = page

            # 更新当前页面引用
            self.driver.page = page
            print(f"✅ 创建新页面，ID: {page_id}")
            return page_id
        except Exception as e:
            print(f"❌ 创建新页面失败: {str(e)}")
            return ""

    async def switch_to_page(self, page_id: str) -> bool:
        """
        切换到指定页面

        Args:
            page_id: 页面ID

        Returns:
            bool: 切换是否成功
        """
        try:
            if page_id not in self.page_registry:
                print(f"❌ 页面ID {page_id} 不存在")
                return False

            page = self.page_registry[page_id]
            if page.is_closed():
                print(f"❌ 页面ID {page_id} 已关闭")
                del self.page_registry[page_id]
                return False

            self.driver.page = page
            print(f"✅ 切换到页面 {page_id}")
            return True
        except Exception as e:
            print(f"❌ 切换页面失败: {str(e)}")
            return False

    async def close_page(self, page_id: str) -> bool:
        """
        关闭指定页面

        Args:
            page_id: 页面ID

        Returns:
            bool: 关闭是否成功
        """
        try:
            if page_id not in self.page_registry:
                print(f"❌ 页面ID {page_id} 不存在")
                return False

            page = self.page_registry[page_id]
            await page.close()
            del self.page_registry[page_id]

            # 如果关闭的是当前页面，需要更新引用
            if self.driver.page == page:
                # 尝试切换到其他页面
                if self.driver.context and self.driver.context.pages:
                    self.driver.page = self.driver.context.pages[-1]
                else:
                    self.driver.page = None

            print(f"✅ 页面 {page_id} 已关闭")
            return True
        except Exception as e:
            print(f"❌ 关闭页面失败: {str(e)}")
            return False

    async def get_all_pages(self) -> List[str]:
        """
        获取所有页面ID

        Returns:
            List[str]: 页面ID列表
        """
        try:
            # 清理已关闭的页面
            closed_pages = []
            for page_id, page in self.page_registry.items():
                if page.is_closed():
                    closed_pages.append(page_id)

            for page_id in closed_pages:
                del self.page_registry[page_id]

            return list(self.page_registry.keys())
        except Exception as e:
            print(f"❌ 获取页面列表失败: {str(e)}")
            return []

    async def navigate_to(self, url: str, wait_until: str = 'networkidle', timeout: Optional[int] = None) -> bool:
        """
        导航到指定URL
        
        Args:
            url: 目标URL
            wait_until: 等待条件
            timeout: 超时时间（毫秒）
            
        Returns:
            bool: 导航是否成功
            
        Raises:
            PageNavigationError: 导航失败时抛出
        """
        try:
            if not self.driver.page:
                raise PageNavigationError("页面未初始化")
            
            timeout = timeout or self.driver.config.page_timeout
            print(f"🌐 导航到: {url}")
            
            await self.driver.page.goto(url, wait_until=wait_until, timeout=timeout)
            print("✅ 页面导航完成")
            return True
            
        except Exception as e:
            raise PageNavigationError(f"页面导航失败: {str(e)}") from e

    async def get_current_page(self) -> Optional[Page]:
        """
        获取当前页面
        
        Returns:
            Optional[Page]: 当前页面对象
        """
        return self.driver.page

    async def create_new_page(self) -> Page:
        """
        创建新页面
        
        Returns:
            Page: 新创建的页面对象
        """
        if not self.driver.context:
            raise BrowserConnectionError("浏览器上下文未初始化")
        
        page = await self.driver.context.new_page()
        self.driver.page = page  # 更新当前页面引用
        print("✅ 创建新页面")
        return page

    async def close_page(self, page: Optional[Page] = None) -> bool:
        """
        关闭页面
        
        Args:
            page: 要关闭的页面，如果为None则关闭当前页面
            
        Returns:
            bool: 关闭是否成功
        """
        try:
            target_page = page or self.driver.page
            if not target_page:
                return True
            
            await target_page.close()
            
            # 如果关闭的是当前页面，需要更新引用
            if target_page == self.driver.page:
                # 尝试切换到其他页面
                if self.driver.context and self.driver.context.pages:
                    self.driver.page = self.driver.context.pages[-1]
                else:
                    self.driver.page = None
            
            print("✅ 页面已关闭")
            return True
            
        except Exception as e:
            print(f"❌ 关闭页面失败: {str(e)}")
            return False

    async def get_page_info(self) -> Dict[str, Any]:
        """
        获取页面信息
        
        Returns:
            Dict[str, Any]: 页面信息
        """
        if not self.driver.page:
            return {}
        
        try:
            return {
                'url': self.driver.page.url,
                'title': await self.driver.page.title(),
                'viewport': self.driver.page.viewport_size,
                'is_closed': self.driver.page.is_closed()
            }
        except Exception as e:
            print(f"⚠️ 获取页面信息失败: {e}")
            return {}

    async def take_screenshot(self, full_page: bool = False, path: Optional[str] = None) -> Optional[bytes]:
        """
        截取页面截图
        
        Args:
            full_page: 是否截取整个页面
            path: 保存路径，如果为None则返回字节数据
            
        Returns:
            Optional[bytes]: 截图字节数据（当path为None时）
        """
        try:
            if not self.driver.page:
                raise ResourceManagementError("页面未初始化")
            
            print("📷 正在截取页面截图...")
            screenshot_options = {
                'full_page': full_page,
                'type': 'png'
            }
            
            if path:
                screenshot_options['path'] = path
                await self.driver.page.screenshot(**screenshot_options)
                print(f"✅ 截图已保存到: {path}")
                return None
            else:
                screenshot_bytes = await self.driver.page.screenshot(**screenshot_options)
                print("✅ 截图完成")
                return screenshot_bytes
                
        except Exception as e:
            raise ResourceManagementError(f"截图失败: {str(e)}") from e


class PlaywrightResourceManager(IResourceManager):
    """Playwright资源管理器实现"""
    
    def __init__(self, driver: PlaywrightBrowserDriver):
        self.driver = driver
        self.managed_resources = {}  # 资源注册表

    async def acquire_resource(self, resource_type: str, config: Dict[str, Any]) -> Any:
        """
        获取资源

        Args:
            resource_type: 资源类型
            config: 资源配置

        Returns:
            Any: 资源对象
        """
        try:
            if resource_type == "browser":
                if not self.driver.is_initialized():
                    await self.driver.initialize(self.driver.config)
                resource = self.driver.browser
            elif resource_type == "context":
                if not self.driver.context:
                    raise ResourceManagementError("浏览器上下文未初始化")
                resource = self.driver.context
            elif resource_type == "page":
                if not self.driver.page:
                    page_manager = await self.driver.get_page_manager()
                    page_id = await page_manager.new_page()
                    resource = self.driver.page
                else:
                    resource = self.driver.page
            else:
                raise ResourceManagementError(f"不支持的资源类型: {resource_type}")

            # 注册资源
            resource_id = str(id(resource))
            self.managed_resources[resource_id] = {
                'type': resource_type,
                'resource': resource,
                'config': config,
                'acquired_at': time.time()
            }

            print(f"✅ 获取资源成功: {resource_type} (ID: {resource_id})")
            return resource

        except Exception as e:
            print(f"❌ 获取资源失败: {str(e)}")
            raise ResourceManagementError(f"获取资源失败: {str(e)}") from e

    async def release_resource(self, resource: Any) -> None:
        """
        释放资源

        Args:
            resource: 要释放的资源
        """
        try:
            resource_id = str(id(resource))
            if resource_id not in self.managed_resources:
                print(f"⚠️ 资源 {resource_id} 未在管理器中注册")
                return

            resource_info = self.managed_resources[resource_id]
            resource_type = resource_info['type']

            if resource_type == "page" and hasattr(resource, 'close'):
                await resource.close()
            elif resource_type == "context" and hasattr(resource, 'close'):
                await resource.close()
            elif resource_type == "browser" and hasattr(resource, 'close'):
                await resource.close()

            # 从注册表中移除
            del self.managed_resources[resource_id]
            print(f"✅ 资源已释放: {resource_type} (ID: {resource_id})")

        except Exception as e:
            print(f"❌ 释放资源失败: {str(e)}")

    async def cleanup_all(self) -> None:
        """清理所有资源"""
        try:
            print("🧹 开始清理所有管理的资源...")

            # 按类型顺序清理：页面 -> 上下文 -> 浏览器
            for resource_type in ["page", "context", "browser"]:
                resources_to_cleanup = [
                    (rid, info) for rid, info in self.managed_resources.items()
                    if info['type'] == resource_type
                ]

                for resource_id, resource_info in resources_to_cleanup:
                    try:
                        await self.release_resource(resource_info['resource'])
                    except Exception as e:
                        print(f"⚠️ 清理资源 {resource_id} 时出现警告: {e}")

            # 清空注册表
            self.managed_resources.clear()
            print("✅ 所有资源清理完成")

        except Exception as e:
            print(f"❌ 清理资源失败: {str(e)}")

    async def get_memory_usage(self) -> Dict[str, Any]:
        """
        获取内存使用情况

        Returns:
            Dict[str, Any]: 内存使用信息
        """
        try:
            if not self.driver.page:
                return {}

            # 获取页面性能指标
            metrics = await self.driver.page.evaluate("""
                () => {
                    const memory = performance.memory || {};
                    return {
                        used_heap_size: memory.usedJSHeapSize || 0,
                        total_heap_size: memory.totalJSHeapSize || 0,
                        heap_size_limit: memory.jsHeapSizeLimit || 0
                    };
                }
            """)

            return {
                'javascript_heap': metrics,
                'timestamp': time.time(),
                'managed_resources_count': len(self.managed_resources)
            }

        except Exception as e:
            print(f"⚠️ 获取内存使用情况失败: {e}")
            return {}

    async def clear_cache(self) -> bool:
        """
        清理缓存

        Returns:
            bool: 清理是否成功
        """
        try:
            if not self.driver.context:
                return False

            # 清理浏览器缓存
            await self.driver.context.clear_cookies()
            await self.driver.context.clear_permissions()

            print("✅ 缓存清理完成")
            return True

        except Exception as e:
            print(f"❌ 清理缓存失败: {str(e)}")
            return False

    async def get_network_conditions(self) -> Dict[str, Any]:
        """
        获取网络状况

        Returns:
            Dict[str, Any]: 网络状况信息
        """
        # Playwright没有直接的网络状况API，返回基本信息
        return {
            'online': True,
            'connection_type': 'unknown',
            'effective_type': '4g'
        }

    async def set_network_conditions(self, conditions: Dict[str, Any]) -> bool:
        """
        设置网络状况

        Args:
            conditions: 网络状况配置

        Returns:
            bool: 设置是否成功
        """
        try:
            if not self.driver.context:
                return False

            # 设置网络模拟
            if 'offline' in conditions and conditions['offline']:
                await self.driver.context.set_offline(True)
            else:
                await self.driver.context.set_offline(False)

            print("✅ 网络状况设置完成")
            return True

        except Exception as e:
            print(f"❌ 设置网络状况失败: {str(e)}")
            return False

    async def monitor_resources(self) -> Dict[str, Any]:
        """
        监控资源使用

        Returns:
            Dict[str, Any]: 资源监控信息
        """
        memory_info = await self.get_memory_usage()
        network_info = await self.get_network_conditions()

        return {
            'memory': memory_info,
            'network': network_info,
            'timestamp': time.time(),
            'browser_initialized': self.driver.is_initialized(),
            'managed_resources': {
                'count': len(self.managed_resources),
                'types': list(set(info['type'] for info in self.managed_resources.values()))
            }
        }