"""
🎯 BrowserService 优化版本
根据五个维度进行全面重构：功能对等、性能优化、编码规范、稳定性、可维护性

主要改进：
1. 统一 Edge/Chrome 支持和持久化上下文策略
2. 去掉高风险启动参数，确保硬件加速
3. 异步接口一致化，统一日志系统
4. Profile 锁冲突检测和优雅处理
5. 跨平台兼容性和资源管理
"""

import asyncio
import json
import locale as system_locale
import os
import platform
import signal
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
from concurrent.futures import ThreadPoolExecutor

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

from .core.interfaces.browser_driver import IBrowserDriver
from .implementations.logger_system import LoggerSystem
from .implementations.config_manager import ConfigManager


class BrowserService:
    """
    🎯 优化的浏览器服务类
    
    统一支持 Edge 和 Chrome，提供一致的持久化上下文策略
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化浏览器服务"""
        self._logger = LoggerSystem()
        self._config_manager = ConfigManager()
        self._executor = ThreadPoolExecutor(max_workers=2)
        
        # 配置参数
        self.config = config or {}
        
        # Playwright 相关
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # 状态管理
        self._initialized = False
        self._is_persistent_context = False
        self._main_loop = None  # 记录主事件循环

        # 日志器
        self._logger_instance = self._logger.get_logger()

    # ========================================
    # 🔧 跨平台用户目录获取（统一 Edge/Chrome）
    # ========================================

    @staticmethod
    def get_browser_user_data_dir(browser_type: str) -> str:
        """
        获取浏览器用户数据根目录
        
        Args:
            browser_type: 'edge' 或 'chrome'
            
        Returns:
            str: 用户数据根目录路径
        """
        system = platform.system().lower()
        
        if browser_type == 'edge':
            if system == 'windows':
                return os.path.expanduser('~/AppData/Local/Microsoft/Edge/User Data')
            elif system == 'darwin':  # macOS
                return os.path.expanduser('~/Library/Application Support/Microsoft Edge')
            elif system == 'linux':
                return os.path.expanduser('~/.config/microsoft-edge')
        
        elif browser_type == 'chrome':
            if system == 'windows':
                return os.path.expanduser('~/AppData/Local/Google/Chrome/User Data')
            elif system == 'darwin':  # macOS
                return os.path.expanduser('~/Library/Application Support/Google/Chrome')
            elif system == 'linux':
                return os.path.expanduser('~/.config/google-chrome')
        
        raise ValueError(f"Unsupported browser type: {browser_type}")

    @staticmethod
    def get_last_used_profile(base_dir: str) -> str:
        """
        从 Local State 文件读取最近使用的 Profile

        Args:
            base_dir: 浏览器用户数据根目录

        Returns:
            str: 最近使用的 Profile 名称，失败时返回 "Default"
        """
        try:
            local_state_path = Path(base_dir) / "Local State"
            if local_state_path.exists():
                data = json.loads(local_state_path.read_text(encoding="utf-8"))
                return data.get("profile", {}).get("last_used", "Default")
        except Exception:
            pass
        return "Default"

    @staticmethod
    def get_browser_profile_dir(browser_type: str, profile_name: str = "Default") -> str:
        """
        获取浏览器具体 Profile 目录
        
        Args:
            browser_type: 'edge' 或 'chrome'
            profile_name: Profile 名称，默认 "Default"
            
        Returns:
            str: 具体 Profile 目录路径
        """
        base_dir = BrowserService.get_browser_user_data_dir(browser_type)
        return str(Path(base_dir) / profile_name)

    @staticmethod
    def get_browser_channel(browser_type: str) -> Optional[str]:
        """
        获取浏览器 channel 参数
        
        Args:
            browser_type: 'edge' 或 'chrome'
            
        Returns:
            Optional[str]: channel 参数，Linux 上可能返回 None
        """
        system = platform.system().lower()
        
        if browser_type == 'edge':
            if system in ['windows', 'darwin']:
                return 'msedge'
            else:  # Linux
                return None  # 回退到 chromium
        
        elif browser_type == 'chrome':
            if system in ['windows', 'darwin']:
                return 'chrome'
            else:  # Linux
                return None  # 回退到 chromium
        
        return None

    # ========================================
    # 🔧 启动参数优化（去掉高风险参数）
    # ========================================

    @staticmethod
    def get_minimal_launch_args(profile_name: str = "Default", enable_extensions: bool = True) -> List[str]:
        """
        获取最小稳定启动参数
        
        Args:
            profile_name: Profile 名称
            enable_extensions: 是否启用扩展
            
        Returns:
            List[str]: 启动参数列表
        """
        args = [
            "--no-first-run",
            "--no-default-browser-check", 
            "--disable-default-apps",
            f"--profile-directory={profile_name}"
        ]
        
        # 仅在明确需要时启用扩展
        if enable_extensions:
            args.extend([
                "--enable-extensions",
                "--disable-extensions-file-access-check"
            ])
        
        return args

    # ========================================
    # 🔧 Profile 锁冲突检测和处理
    # ========================================

    def _check_profile_locks(self, profile_dir: str) -> List[str]:
        """
        检查 Profile 目录的锁文件
        
        Args:
            profile_dir: Profile 目录路径
            
        Returns:
            List[str]: 发现的锁文件列表
        """
        lock_files = [
            "SingletonLock",
            "SingletonCookie", 
            "DevToolsActivePort",
            "lockfile"
        ]
        
        found_locks = []
        profile_path = Path(profile_dir)
        
        for lock_file in lock_files:
            lock_path = profile_path / lock_file
            if lock_path.exists():
                found_locks.append(str(lock_path))
        
        return found_locks

    async def _wait_for_lock_release(self, profile_dir: str, timeout: int = 10) -> bool:
        """
        等待 Profile 锁文件释放
        
        Args:
            profile_dir: Profile 目录路径
            timeout: 超时时间（秒）
            
        Returns:
            bool: 锁文件是否已释放
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            locks = self._check_profile_locks(profile_dir)
            if not locks:
                return True
            
            self._logger_instance.info(f"Waiting for profile locks to release: {locks}")
            await asyncio.sleep(1)
        
        return False

    def _get_browser_processes(self, browser_type: str) -> List[int]:
        """
        获取浏览器进程 PID 列表
        
        Args:
            browser_type: 'edge' 或 'chrome'
            
        Returns:
            List[int]: 进程 PID 列表
        """
        pids = []
        system = platform.system().lower()
        
        try:
            if browser_type == 'edge':
                if system == "windows":
                    result = subprocess.run(
                        ['tasklist', '/FI', 'IMAGENAME eq msedge.exe', '/FO', 'CSV'],
                        capture_output=True, text=True, check=False
                    )
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        for line in lines[1:]:
                            if 'msedge.exe' in line:
                                parts = line.split(',')
                                if len(parts) >= 2:
                                    pid = parts[1].strip('"')
                                    if pid.isdigit():
                                        pids.append(int(pid))
                
                elif system == "darwin":
                    result = subprocess.run(
                        ['pgrep', '-f', 'Microsoft Edge'],
                        capture_output=True, text=True, check=False
                    )
                    if result.returncode == 0:
                        for pid in result.stdout.strip().split('\n'):
                            if pid.strip().isdigit():
                                pids.append(int(pid.strip()))
                
                elif system == "linux":
                    result = subprocess.run(
                        ['pgrep', '-f', 'microsoft-edge'],
                        capture_output=True, text=True, check=False
                    )
                    if result.returncode == 0:
                        for pid in result.stdout.strip().split('\n'):
                            if pid.strip().isdigit():
                                pids.append(int(pid.strip()))
            
            elif browser_type == 'chrome':
                if system == "windows":
                    result = subprocess.run(
                        ['tasklist', '/FI', 'IMAGENAME eq chrome.exe', '/FO', 'CSV'],
                        capture_output=True, text=True, check=False
                    )
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        for line in lines[1:]:
                            if 'chrome.exe' in line:
                                parts = line.split(',')
                                if len(parts) >= 2:
                                    pid = parts[1].strip('"')
                                    if pid.isdigit():
                                        pids.append(int(pid))
                
                elif system in ["darwin", "linux"]:
                    process_name = 'Google Chrome' if system == "darwin" else 'chrome'
                    result = subprocess.run(
                        ['pgrep', '-f', process_name],
                        capture_output=True, text=True, check=False
                    )
                    if result.returncode == 0:
                        for pid in result.stdout.strip().split('\n'):
                            if pid.strip().isdigit():
                                pids.append(int(pid.strip()))
        
        except Exception as e:
            self._logger_instance.error(f"Failed to get {browser_type} processes: {e}")
        
        return pids

    # ========================================
    # 🚀 统一初始化方法
    # ========================================

    async def initialize(self) -> bool:
        """
        异步初始化浏览器服务
        
        Returns:
            bool: 初始化是否成功
        """
        if self._initialized:
            return True
        
        try:
            self._logger_instance.info("Initializing browser service...")
            
            # 启动 Playwright
            self.playwright = await async_playwright().start()
            
            # 记录主事件循环
            self._main_loop = asyncio.get_event_loop()

            # 获取配置
            browser_type = self.config.get('browser_type', 'edge')
            headless = self.config.get('headless', False)  # 默认 headful
            enable_extensions = self.config.get('enable_extensions', True)
            user_data_dir = self.config.get('user_data_dir')

            # 智能 Profile 选择
            if user_data_dir:
                profile_dir = user_data_dir
            else:
                base_dir = self.get_browser_user_data_dir(browser_type)
                profile_name = self.config.get('profile_name') or self.get_last_used_profile(base_dir)
                profile_dir = str(Path(base_dir) / profile_name)
            
            # 检查 Profile 锁冲突
            locks = self._check_profile_locks(profile_dir)
            if locks:
                self._logger_instance.warning(f"Profile directory has locks: {locks}")
                
                # 尝试等待锁释放
                if not await self._wait_for_lock_release(profile_dir, timeout=5):
                    self._logger_instance.error("Profile directory is locked, please close existing browser instances")
                    return False
            
            # 获取启动参数和 channel
            launch_args = self.get_minimal_launch_args(profile_name, enable_extensions)
            channel = self.get_browser_channel(browser_type)
            
            # 启动浏览器
            success = await self._launch_browser(
                browser_type=browser_type,
                profile_dir=profile_dir,
                headless=headless,
                channel=channel,
                launch_args=launch_args
            )
            
            if success:
                # 创建页面
                self.page = await self.context.new_page()
                self._initialized = True

                # 结构化日志输出
                self._logger_instance.info("Browser service initialized successfully", extra={
                    'browser_type': browser_type,
                    'channel': channel,
                    'profile_dir': profile_dir,
                    'headless': headless,
                    'launch_args': launch_args,
                    'is_persistent_context': self._is_persistent_context,
                    'locale': self.config.get('locale', 'en-US')
                })

                # 可选的登录状态验证
                verify_domain = self.config.get('verify_domain')
                if verify_domain:
                    login_result = await self.verify_login_state(verify_domain)
                    self._logger_instance.info(f"Login state verification: {login_result['message']}")

                return True

            return False

        except Exception as e:
            self._logger_instance.error(f"Failed to initialize browser service: {e}")
            return False

    async def _launch_browser(self, browser_type: str, profile_dir: str,
                            headless: bool, channel: Optional[str],
                            launch_args: List[str]) -> bool:
        """
        启动浏览器（统一 Edge/Chrome 逻辑）

        Args:
            browser_type: 浏览器类型
            profile_dir: Profile 目录
            headless: 是否无头模式
            channel: channel 参数
            launch_args: 启动参数

        Returns:
            bool: 启动是否成功
        """
        try:
            # 获取系统 locale
            try:
                system_locale_name = system_locale.getdefaultlocale()[0] or 'en-US'
                if '_' in system_locale_name:
                    system_locale_name = system_locale_name.replace('_', '-')
            except:
                system_locale_name = 'en-US'

            # 持久化上下文配置
            context_options = {
                'headless': headless,
                'viewport': {'width': 1280, 'height': 800},
                'locale': self.config.get('locale', 'en-US'),
                'args': launch_args
                # 不覆盖 user_agent，使用真实浏览器 UA
            }
            
            self._logger_instance.info(f"Launching {browser_type} with persistent context")
            self._logger_instance.info(f"Profile directory: {profile_dir}")
            self._logger_instance.info(f"Headless mode: {headless}")
            self._logger_instance.info(f"Launch args: {launch_args}")
            
            if channel:
                # 使用系统浏览器
                self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=profile_dir,
                    channel=channel,
                    **context_options
                )
                self.browser = None  # 持久化上下文不需要单独的 browser 对象
                self._is_persistent_context = True
                
            else:
                # Linux/无channel：仍使用持久化上下文
                self._logger_instance.warning("Channel not available; launching Chromium persistent context")
                self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=profile_dir,
                    **context_options
                )
                self.browser = None  # 持久化上下文不需要单独的 browser 对象
                self._is_persistent_context = True
            
            self._logger_instance.info(f"{browser_type} launched successfully")
            return True
            
        except Exception as e:
            self._logger_instance.error(f"Failed to launch {browser_type}: {e}")
            return False

    # ========================================
    # 🔧 登录状态验证和管理（统一接口）
    # ========================================

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
                self._logger_instance.info(f"Login state verified for {domain}: {len(cookies)} cookies")
            else:
                result['message'] = f'No cookies found for {domain}'
                self._logger_instance.warning(f"No login cookies found for {domain}")
            
            return result
            
        except Exception as e:
            result['message'] = f'Failed to verify login state: {e}'
            self._logger_instance.error(f"Failed to verify login state for {domain}: {e}")
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
                self._logger_instance.error("Browser context not available")
                return False
            
            await self.context.storage_state(path=file_path)
            self._logger_instance.info(f"Storage state saved to: {file_path}")
            return True
            
        except Exception as e:
            self._logger_instance.error(f"Failed to save storage state: {e}")
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
                self._logger_instance.error(f"Storage state file not found: {file_path}")
                return False
            
            if not self.browser:
                self._logger_instance.error("Browser not available for loading storage state")
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
            
            self._logger_instance.info(f"Storage state loaded from: {file_path}")
            return True
            
        except Exception as e:
            self._logger_instance.error(f"Failed to load storage state: {e}")
            return False

    # ========================================
    # 🚀 异步页面操作方法
    # ========================================

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
            self._logger_instance.error("Browser service not initialized")
            return False
        
        try:
            await self.page.goto(url, wait_until=wait_until)
            self._logger_instance.info(f"Successfully opened page: {url}")
            return True
            
        except Exception as e:
            self._logger_instance.error(f"Failed to open page {url}: {e}")
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
            self._logger_instance.error("Browser service not initialized")
            return None
        
        try:
            path = Path(file_path)
            await self.page.screenshot(path=str(path))
            self._logger_instance.info(f"Screenshot saved to: {path}")
            return path
            
        except Exception as e:
            self._logger_instance.error(f"Failed to take screenshot: {e}")
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
            title = await self.page.title()
            return title
        except Exception as e:
            self._logger_instance.error(f"Failed to get page title: {e}")
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
            self._logger_instance.error(f"Failed to wait for element {selector}: {e}")
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
            self._logger_instance.info(f"Successfully clicked element: {selector}")
            return True
        except Exception as e:
            self._logger_instance.error(f"Failed to click element {selector}: {e}")
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
            self._logger_instance.info(f"Successfully filled input {selector}")
            return True
        except Exception as e:
            self._logger_instance.error(f"Failed to fill input {selector}: {e}")
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
            self._logger_instance.error(f"Failed to get element text {selector}: {e}")
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
            self._logger_instance.error(f"Failed to execute script: {e}")
            return None

    # ========================================
    # 🔄 同步包装方法（向后兼容）
    # ========================================

    def screenshot(self, file_path: Union[str, Path]) -> Optional[Path]:
        """
        同步截图方法（向后兼容）
        
        Args:
            file_path: 截图保存路径
            
        Returns:
            Optional[Path]: 截图文件路径
        """
        if asyncio.get_event_loop().is_running():
            # 在已有事件循环中使用线程池
            future = self._executor.submit(
                asyncio.run, 
                self.screenshot_async(file_path)
            )
            return future.result()
        else:
            # 没有事件循环时直接运行
            return asyncio.run(self.screenshot_async(file_path))

    def get_page_title(self) -> Optional[str]:
        """
        同步获取页面标题方法（向后兼容）
        
        Returns:
            Optional[str]: 页面标题
        """
        if asyncio.get_event_loop().is_running():
            # 在已有事件循环中使用线程池
            future = self._executor.submit(
                asyncio.run, 
                self.get_page_title_async()
            )
            return future.result()
        else:
            # 没有事件循环时直接运行
            return asyncio.run(self.get_page_title_async())

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
            self._logger_instance.error(f"Failed to get page URL: {e}")
            return None

    # ========================================
    # 🧹 资源清理和关闭
    # ========================================

    async def shutdown(self) -> bool:
        """
        异步关闭浏览器服务
        
        Returns:
            bool: 关闭是否成功
        """
        if not self._initialized:
            return True
        
        try:
            self._logger_instance.info("Shutting down browser service...")
            
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
            self._logger_instance.info("Browser service shutdown successfully")
            return True
            
        except Exception as e:
            self._logger_instance.error(f"Failed to shutdown browser service: {e}")
            return False

    # ========================================
    # 🔍 访问器方法
    # ========================================

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
        """检查服务是否已初始化"""
        return self._initialized

    def is_persistent_context(self) -> bool:
        """检查是否使用持久化上下文"""
        return self._is_persistent_context

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


# ========================================
# 🔧 便利函数
# ========================================

def get_edge_profile_dir(profile_name: str = "Default") -> str:
    """获取 Edge Profile 目录（向后兼容）"""
    return BrowserService.get_browser_profile_dir('edge', profile_name)

def get_chrome_profile_dir(profile_name: str = "Default") -> str:
    """获取 Chrome Profile 目录"""
    return BrowserService.get_browser_profile_dir('chrome', profile_name)

def get_edge_user_data_dir() -> str:
    """获取 Edge 用户数据根目录（向后兼容）"""
    return BrowserService.get_browser_user_data_dir('edge')

def get_chrome_user_data_dir() -> str:
    """获取 Chrome 用户数据根目录"""
    return BrowserService.get_browser_user_data_dir('chrome')