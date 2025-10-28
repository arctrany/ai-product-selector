"""
Playwright浏览器驱动实现

本模块提供基于Playwright的浏览器驱动实现，
负责所有与Playwright相关的具体操作。
"""

import asyncio
import os
import platform
import subprocess
import locale as system_locale
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright


# ConfigManager removed - using simplified config system
from .logger_system import get_logger
from ..core.interfaces.browser_driver import IBrowserDriver


class PlaywrightBrowserDriver(IBrowserDriver):
    """
    基于Playwright的浏览器驱动实现
    
    负责所有与Playwright相关的具体操作：
    - 浏览器启动和管理
    - 页面操作和导航
    - 异步操作处理
    - 资源生命周期管理
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Playwright浏览器驱动

        Args:
            config: 浏览器配置字典
        """
        self.config = config or {}  # 使用简化配置系统
        self._logger = get_logger("PlaywrightDriver")
        
        # Playwright 相关实例
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # 状态管理
        self._initialized = False
        self._is_persistent_context = False
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None
        self._executor = ThreadPoolExecutor(max_workers=2)

    # ========================================
    # 🚀 浏览器驱动核心方法
    # ========================================

    async def initialize(self) -> bool:
        """
        异步初始化浏览器驱动
        
        Returns:
            bool: 初始化是否成功
        """
        if self._initialized:
            return True
        
        try:
            self._logger.info("Initializing Playwright browser driver...")
            
            # 使用简化配置系统
            if not self.config:
                self.config = {}

            # 启动 Playwright
            self.playwright = await async_playwright().start()
            
            # 记录主事件循环
            self._main_loop = asyncio.get_event_loop()

            # 获取配置
            browser_type = self.config.get('browser_type', 'edge')
            headless = self.config.get('headless', False)
            enable_extensions = self.config.get('enable_extensions', True)

            # 用户数据根目录（始终是根目录，不是具体Profile目录）
            user_data_dir_root = self.config.get('user_data_dir') or self._get_browser_user_data_dir(browser_type)

            # 推断profile_name（优先显式配置，否则从Local State读取last_used）
            profile_name = self.config.get('profile_name') or self._get_last_used_profile(user_data_dir_root)

            # 🔧 关键修复：确保使用真正的默认Profile
            if profile_name == "Default":
                # 验证Default Profile是否存在
                default_profile_path = Path(user_data_dir_root) / "Default"
                if not default_profile_path.exists():
                    # 如果Default不存在，查找实际的默认Profile
                    actual_profile = self._find_actual_default_profile(user_data_dir_root)
                    if actual_profile:
                        profile_name = actual_profile
                        self._logger.info(f"Default profile not found, using actual default: {profile_name}")

            # 添加调试日志
            self._logger.info(f"Profile configuration: name='{profile_name}', root_dir='{user_data_dir_root}'", extra={
                'user_data_dir_root': user_data_dir_root,
                'profile_name': profile_name,
                'profile_path': str(Path(user_data_dir_root) / profile_name)
            })
            
            # 注意：移除了锁检查逻辑，因为锁文件可能在浏览器异常退出时残留
            # Playwright 会自动处理 Profile 冲突，无需手动检查锁文件
            
            # 获取启动参数和 channel
            launch_args = self._get_minimal_launch_args(profile_name, enable_extensions)
            channel = self._get_browser_channel(browser_type)
            
            # 启动浏览器
            success = await self._launch_browser(
                browser_type=browser_type,
                profile_dir=user_data_dir_root,
                headless=headless,
                channel=channel,
                launch_args=launch_args,
                enable_extensions=enable_extensions
            )
            
            if success:
                # 创建页面
                self.page = await self.context.new_page()
                self._initialized = True

                self._logger.info("Playwright browser driver initialized successfully", extra={
                    'browser_type': browser_type,
                    'channel': channel,
                    'profile_dir': user_data_dir_root,
                    'headless': headless,
                    'is_persistent_context': self._is_persistent_context
                })

                return True

            return False

        except Exception as e:
            self._logger.error(f"Failed to initialize Playwright browser driver: {e}")
            return False

    async def open_page(self, url: str, wait_until: str = 'networkidle') -> bool:
        """
        打开指定URL的页面
        
        Args:
            url: 要打开的URL
            wait_until: 等待条件
            
        Returns:
            bool: 操作是否成功
        """
        if not self._initialized or not self.page:
            self._logger.error("Browser driver not initialized")
            return False
        
        try:
            await self.page.goto(url, wait_until=wait_until)
            self._logger.info(f"Successfully opened page: {url}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to open page {url}: {e}")
            return False

    async def screenshot_async(self, file_path: Union[str, Path]) -> Optional[Path]:
        """
        异步截取当前页面的截图
        
        Args:
            file_path: 截图保存路径
            
        Returns:
            Optional[Path]: 截图文件路径，失败时返回 None
        """
        if not self._initialized or not self.page:
            self._logger.error("Browser driver not initialized")
            return None
        
        try:
            path = Path(file_path)
            await self.page.screenshot(path=str(path))
            self._logger.info(f"Screenshot saved to: {path}")
            return path
            
        except Exception as e:
            self._logger.error(f"Failed to take screenshot: {e}")
            return None

    async def get_page_title_async(self) -> Optional[str]:
        """
        异步获取当前页面标题
        
        Returns:
            Optional[str]: 页面标题，失败时返回 None
        """
        if not self._initialized or not self.page:
            return None
        
        try:
            # 使用更安全的方式获取页面标题，避免事件循环冲突
            title = await self.page.evaluate("() => document.title")
            return title if title else None
        except Exception as e:
            self._logger.error(f"Failed to get page title: {e}")
            return None

    def get_page_url(self) -> Optional[str]:
        """
        获取当前页面URL
        
        Returns:
            Optional[str]: 页面URL
        """
        if not self._initialized or not self.page:
            return None
        
        try:
            return self.page.url
        except Exception as e:
            self._logger.error(f"Failed to get page URL: {e}")
            return None

    async def wait_for_element(self, selector: str, timeout: int = 30000) -> bool:
        """
        等待元素出现
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（毫秒）
            
        Returns:
            bool: 元素是否出现
        """
        if not self._initialized or not self.page:
            return False
        
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            self._logger.error(f"Failed to wait for element {selector}: {e}")
            return False

    async def click_element(self, selector: str) -> bool:
        """
        点击指定元素
        
        Args:
            selector: 元素选择器
            
        Returns:
            bool: 操作是否成功
        """
        if not self._initialized or not self.page:
            return False
        
        try:
            await self.page.click(selector)
            self._logger.info(f"Successfully clicked element: {selector}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to click element {selector}: {e}")
            return False

    async def fill_input(self, selector: str, text: str) -> bool:
        """
        填充输入框
        
        Args:
            selector: 输入框选择器
            text: 要填充的文本
            
        Returns:
            bool: 操作是否成功
        """
        if not self._initialized or not self.page:
            return False
        
        try:
            await self.page.fill(selector, text)
            self._logger.info(f"Successfully filled input {selector}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to fill input {selector}: {e}")
            return False

    async def get_element_text(self, selector: str) -> Optional[str]:
        """
        异步获取元素文本内容
        
        Args:
            selector: 元素选择器
            
        Returns:
            Optional[str]: 元素文本内容，失败时返回 None
        """
        if not self._initialized or not self.page:
            return None
        
        try:
            text = await self.page.text_content(selector)
            return text
        except Exception as e:
            self._logger.error(f"Failed to get element text {selector}: {e}")
            return None

    async def execute_script(self, script: str) -> Any:
        """
        异步执行JavaScript脚本
        
        Args:
            script: JavaScript代码
            
        Returns:
            Any: 脚本执行结果
        """
        if not self._initialized or not self.page:
            return None
        
        try:
            result = await self.page.evaluate(script)
            return result
        except Exception as e:
            self._logger.error(f"Failed to execute script: {e}")
            return None

    async def shutdown(self) -> bool:
        """
        异步关闭浏览器驱动
        
        Returns:
            bool: 关闭是否成功
        """
        if not self._initialized:
            return True
        
        try:
            self._logger.info("Shutting down Playwright browser driver...")
            
            # 关闭页面
            if self.page:
                await self.page.close()
                self.page = None
            
            # 关闭上下文
            if self.context:
                await self.context.close()
                self.context = None
            
            # 关闭浏览器（仅非持久化上下文）
            if self.browser and not self._is_persistent_context:
                await self.browser.close()
                self.browser = None
            
            # 关闭 Playwright
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
            # 关闭线程池
            self._executor.shutdown(wait=True)
            
            self._initialized = False
            self._logger.info("Playwright browser driver shutdown successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to shutdown Playwright browser driver: {e}")
            return False

    def get_page(self) -> Optional[Page]:
        """获取 Playwright 页面对象"""
        return self.page

    def get_context(self) -> Optional[BrowserContext]:
        """获取 Playwright 浏览器上下文"""
        return self.context

    def get_browser(self) -> Optional[Browser]:
        """获取 Playwright 浏览器实例"""
        return self.browser

    def is_initialized(self) -> bool:
        """检查驱动是否已初始化"""
        return self._initialized

    def is_persistent_context(self) -> bool:
        """检查是否使用持久化上下文"""
        return self._is_persistent_context

    async def verify_login_state(self, domain: str) -> Dict[str, Any]:
        """
        验证指定域名的登录状态

        Args:
            domain: 要验证的域名（如 "https://example.com"）

        Returns:
            Dict[str, Any]: 验证结果
        """
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

            cookies = await self.context.cookies(domain)
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

    async def save_storage_state(self, file_path: str) -> bool:
        """
        保存浏览器存储状态到文件

        Args:
            file_path: 保存路径

        Returns:
            bool: 保存是否成功
        """
        try:
            if not self.context:
                self._logger.error("Browser context not available")
                return False

            await self.context.storage_state(path=file_path)
            self._logger.info(f"Storage state saved to: {file_path}")
            return True

        except Exception as e:
            self._logger.error(f"Failed to save storage state: {e}")
            return False

    async def load_storage_state(self, file_path: str) -> bool:
        """
        从文件加载浏览器存储状态

        Args:
            file_path: 文件路径

        Returns:
            bool: 加载是否成功
        """
        try:
            if not os.path.exists(file_path):
                self._logger.error(f"Storage state file not found: {file_path}")
                return False

            if not self.browser:
                self._logger.error("Browser not available for loading storage state")
                return False

            # 创建新上下文并加载存储状态
            new_context = await self.browser.new_context(storage_state=file_path)

            # 关闭旧上下文
            if self.context:
                await self.context.close()

            self.context = new_context

            # 重新创建页面
            if self.page:
                await self.page.close()
            self.page = await self.context.new_page()

            self._logger.info(f"Storage state loaded from: {file_path}")
            return True

        except Exception as e:
            self._logger.error(f"Failed to load storage state: {e}")
            return False

    # ========================================
    # 🔧 内部实现方法
    # ========================================

    async def _launch_browser(self, browser_type: str, profile_dir: str,
                            headless: bool, channel: Optional[str],
                            launch_args: List[str], enable_extensions: bool = True) -> bool:
        """
        启动浏览器（统一 Edge/Chrome 逻辑）
        """
        try:
            import sys

            # 获取系统 locale
            try:
                system_locale_name = system_locale.getdefaultlocale()[0] or 'zh-CN'
                if '_' in system_locale_name:
                    system_locale_name = system_locale_name.replace('_', '-')
            except:
                system_locale_name = 'zh-CN'

            # 构建 ignore_default_args 列表
            ignore_list = []

            # macOS 关键修复：移除阻止 Cookie 解密和影响登录态的参数
            if sys.platform == 'darwin':
                ignore_list.extend([
                    '--use-mock-keychain',
                    '--password-store=basic',
                    '--disable-features=Translate',  # 移除禁用翻译，恢复语言功能
                    '--disable-background-networking',  # 移除禁用后台网络，恢复登录状态同步
                    '--disable-component-update',  # 移除禁用组件更新，恢复语言包
                    '--disable-client-side-phishing-detection',  # 移除过度安全限制
                    '--no-service-autorun',  # 移除禁用服务自动运行
                    '--disable-field-trial-config'  # 移除禁用字段试验配置
                ])
                self._logger.info("macOS detected: ignoring args that may affect login state and language")

            # 当启用扩展时，忽略 Playwright 的禁用扩展参数
            if enable_extensions:
                ignore_list.extend([
                    '--disable-extensions',
                    '--disable-component-extensions-with-background-pages',
                    '--disable-default-apps',
                    '--disable-dev-shm-usage'
                ])

            # 持久化上下文配置
            context_options = {
                'headless': headless,
                'viewport': {'width': 1280, 'height': 800},
                'locale': self.config.get('locale', 'zh-CN'),  # 修正默认语言
                'args': launch_args,
                'ignore_default_args': ignore_list if ignore_list else None
            }

            # 移除 None 值的选项
            context_options = {k: v for k, v in context_options.items() if v is not None}
            
            self._logger.info(f"Launching {browser_type} with persistent context")
            self._logger.info(f"Profile directory: {profile_dir}")
            
            # 检查是否指定了可执行文件路径
            executable_path = self.config.get('executable_path')

            if executable_path and os.path.exists(executable_path):
                # 使用指定的可执行文件路径
                self._logger.info(f"Using executable path: {executable_path}")
                self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=profile_dir,
                    executable_path=executable_path,
                    **context_options
                )
                self.browser = None
                self._is_persistent_context = True

            elif channel:
                # 使用系统浏览器channel
                self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=profile_dir,
                    channel=channel,
                    **context_options
                )
                self.browser = None
                self._is_persistent_context = True
                
            else:
                # Linux/无channel：仍使用持久化上下文
                self._logger.warning("Channel not available; launching Chromium persistent context")
                self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=profile_dir,
                    **context_options
                )
                self.browser = None
                self._is_persistent_context = True
            
            self._logger.info(f"{browser_type} launched successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to launch {browser_type}: {e}")
            return False

    def _get_browser_user_data_dir(self, browser_type: str) -> str:
        """获取浏览器用户数据根目录"""
        system = platform.system().lower()
        
        if browser_type == 'edge':
            if system == "windows":
                return os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")
            elif system == "darwin":
                return os.path.expanduser("~/Library/Application Support/Microsoft Edge")
            elif system == "linux":
                return os.path.expanduser("~/.config/microsoft-edge")
        
        elif browser_type == 'chrome':
            if system == "windows":
                return os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
            elif system == "darwin":
                return os.path.expanduser("~/Library/Application Support/Google Chrome")
            elif system == "linux":
                return os.path.expanduser("~/.config/google-chrome")
        
        # 默认返回 Chrome 路径
        if system == "windows":
            return os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
        elif system == "darwin":
            return os.path.expanduser("~/Library/Application Support/Google Chrome")
        else:
            return os.path.expanduser("~/.config/google-chrome")

    def _get_last_used_profile(self, base_dir: str) -> str:
        """获取最后使用的Profile"""
        try:
            local_state_path = Path(base_dir) / "Local State"
            if local_state_path.exists():
                import json
                with open(local_state_path, 'r', encoding='utf-8') as f:
                    local_state = json.load(f)
                
                # 优先使用 last_used 配置
                profile_data = local_state.get('profile', {})
                last_used = profile_data.get('last_used')
                if last_used:
                    self._logger.info(f"Found last_used profile: {last_used}")
                    return last_used

                # 如果没有 last_used，查找 info_cache 中的第一个
                profile_info = profile_data.get('info_cache', {})
                if profile_info:
                    first_profile = list(profile_info.keys())[0]
                    self._logger.info(f"Using first available profile: {first_profile}")
                    return first_profile

        except Exception as e:
            self._logger.debug(f"Could not determine last used profile: {e}")

        return "Default"

    def _find_actual_default_profile(self, base_dir: str) -> Optional[str]:
        """查找实际存在的默认Profile"""
        try:
            base_path = Path(base_dir)

            # 检查常见的Profile目录
            common_profiles = ["Default", "Profile 1", "Person 1"]

            for profile_name in common_profiles:
                profile_path = base_path / profile_name
                if profile_path.exists() and profile_path.is_dir():
                    # 检查是否有基本的Profile文件
                    preferences_file = profile_path / "Preferences"
                    if preferences_file.exists():
                        self._logger.info(f"Found valid profile directory: {profile_name}")
                        return profile_name

            # 如果没有找到常见的，查找所有以"Profile"开头的目录
            for item in base_path.iterdir():
                if item.is_dir() and (item.name.startswith("Profile") or item.name == "Default"):
                    preferences_file = item / "Preferences"
                    if preferences_file.exists():
                        self._logger.info(f"Found alternative profile directory: {item.name}")
                        return item.name

        except Exception as e:
            self._logger.debug(f"Could not find actual default profile: {e}")

        return None

    def _check_profile_locks(self, profile_dir: str) -> List[str]:
        """检查Profile目录的锁文件"""
        locks = []
        lock_files = ['SingletonLock', 'SingletonSocket', 'SingletonCookie']
        
        for lock_file in lock_files:
            lock_path = Path(profile_dir) / lock_file
            if lock_path.exists():
                locks.append(lock_file)
        
        return locks

    async def _wait_for_lock_release(self, profile_dir: str, timeout: int = 5) -> bool:
        """等待Profile锁释放"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            locks = self._check_profile_locks(profile_dir)
            if not locks:
                return True
            await asyncio.sleep(0.5)
        
        return False

    def _get_minimal_launch_args(self, profile_name: str, enable_extensions: bool) -> List[str]:
        """获取保持用户状态的启动参数"""
        args = [
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-default-apps',
            f'--profile-directory={profile_name}',  # 关键：显式选择Profile
        ]

        # 只有当明确禁用扩展时才添加 --disable-extensions
        if enable_extensions is False:
            args.append('--disable-extensions')

        # 当启用扩展时，确保不添加任何禁用扩展的参数
        if enable_extensions:
            self._logger.info(f"Extensions enabled - using Profile: {profile_name}")
        
        return args

    def _get_browser_channel(self, browser_type: str) -> Optional[str]:
        """获取浏览器channel"""
        system = platform.system().lower()
        
        if browser_type == 'edge':
            if system in ["windows", "darwin"]:
                return "msedge"
        elif browser_type == 'chrome':
            if system in ["windows", "darwin"]:
                return "chrome"
        
        return None

    # ========================================
    # 🔄 同步包装方法（向后兼容）
    # ========================================

    def screenshot(self, file_path: Union[str, Path]) -> Optional[Path]:
        """同步截图方法（向后兼容）"""
        try:
            # 检查是否在异步上下文中
            loop = asyncio.get_running_loop()
            # 如果在运行的事件循环中，使用线程池执行
            future = self._executor.submit(self._sync_screenshot, file_path)
            return future.result()
        except RuntimeError:
            # 没有运行的事件循环，可以直接使用 asyncio.run
            return asyncio.run(self.screenshot_async(file_path))

    def _sync_screenshot(self, file_path: Union[str, Path]) -> Optional[Path]:
        """在新的事件循环中同步截图"""
        return asyncio.run(self.screenshot_async(file_path))

    def get_page_title(self) -> Optional[str]:
        """同步获取页面标题方法（向后兼容）"""
        try:
            # 检查是否在异步上下文中
            loop = asyncio.get_running_loop()
            # 如果在运行的事件循环中，使用线程池执行
            future = self._executor.submit(self._sync_get_page_title)
            return future.result()
        except RuntimeError:
            # 没有运行的事件循环，可以直接使用 asyncio.run
            return asyncio.run(self.get_page_title_async())

    def _sync_get_page_title(self) -> Optional[str]:
        """在新的事件循环中同步获取页面标题"""
        return asyncio.run(self.get_page_title_async())

    # ========================================
    # 🔄 上下文管理器支持
    # ========================================

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.shutdown()