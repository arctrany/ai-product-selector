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

    # ==================== 生命周期管理 ====================

    async def initialize(self) -> bool:
        """初始化浏览器驱动"""
        if self._initialized:
            return True
        
        try:
            self._logger.info("Initializing Playwright browser driver...")
            
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
                
                # 设置资源拦截（如果需要）
                # await self._setup_resource_blocking()

                # 注入反检测脚本
                await self._inject_stealth_scripts()
                
                self._initialized = True
                self._logger.info("Playwright browser driver initialized successfully")
                return True
            
            return False
            
        except Exception as e:
            self._logger.error(f"Failed to initialize browser driver: {e}")
            raise BrowserInitializationError(f"Initialization failed: {e}")

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

    async def shutdown(self) -> bool:
        """关闭浏览器驱动"""
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
            
            self._initialized = False
            self._logger.info("Playwright browser driver shutdown successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to shutdown browser driver: {e}")
            return False

    def is_initialized(self) -> bool:
        """检查驱动是否已初始化"""
        return self._initialized

    # ==================== 页面操作 ====================

    async def open_page(self, url: str, wait_until: str = 'load', timeout: int = 30000) -> bool:
        """打开页面"""
        if not self._initialized or not self.page:
            self._logger.error("Browser driver not initialized")
            return False

        try:
            self._logger.info(f"Navigating to: {url}")
            await self.page.goto(url, wait_until=wait_until, timeout=timeout)
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to open page: {e}")
            return False

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

    async def execute_script(self, script: str) -> Any:
        """执行 JavaScript 脚本"""
        if not self.page:
            return None
        
        try:
            return await self.page.evaluate(script)
        except Exception as e:
            self._logger.error(f"Failed to execute script: {e}")
            return None

    def get_page_url(self) -> Optional[str]:
        """获取当前页面URL"""
        if not self.page:
            return None

        try:
            return self.page.url
        except Exception as e:
            self._logger.error(f"Failed to get page URL: {e}")
            return None

    # ==================== 元素交互方法 ====================

    async def wait_for_element(self, selector: str, timeout: int = 30000) -> bool:
        """等待元素出现"""
        if not self.page:
            return False

        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            self._logger.error(f"Failed to wait for element {selector}: {e}")
            return False

    async def click_element(self, selector: str) -> bool:
        """点击指定元素"""
        if not self.page:
            return False

        try:
            await self.page.click(selector)
            return True
        except Exception as e:
            self._logger.error(f"Failed to click element {selector}: {e}")
            return False

    async def fill_input(self, selector: str, text: str) -> bool:
        """填充输入框"""
        if not self.page:
            return False

        try:
            await self.page.fill(selector, text)
            return True
        except Exception as e:
            self._logger.error(f"Failed to fill input {selector}: {e}")
            return False

    async def get_element_text(self, selector: str) -> Optional[str]:
        """获取元素文本内容"""
        if not self.page:
            return None

        try:
            return await self.page.text_content(selector)
        except Exception as e:
            self._logger.error(f"Failed to get element text {selector}: {e}")
            return None

    # ==================== 会话管理方法 ====================

    async def verify_login_state(self, domain: str) -> Dict[str, Any]:
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
        """保存浏览器存储状态到文件"""
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
        """从文件加载浏览器存储状态"""
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

            # 🔧 关键修复：当 user_data_dir 为 None 时，使用默认用户数据目录
            if user_data_dir is not None:
                # 🔍 DEBUG: 打印指定的用户数据目录信息
                import os
                self._logger.info(f"🔍 使用指定的用户数据目录: {user_data_dir}")
                self._logger.info(f"🔍 目录是否存在: {os.path.exists(user_data_dir) if user_data_dir else False}")

                # 🔧 关键修复：添加 ignore_default_args 以启用扩展和保留登录态
                # 注意：launch_persistent_context 支持 args 参数
                self._logger.info(f"🔍 启动参数: {launch_options.get('args', [])}")

                launch_options_with_extensions = {
                    'headless': headless,
                    'args': launch_options.get('args', []),  # 确保包含 --profile-directory 等参数
                    'ignore_default_args': [
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

                # 使用指定的用户数据目录
                self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
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

    def _get_default_launch_args(self) -> List[str]:
        """获取默认启动参数 - 🔧 保持用户登录状态和输入记忆"""
        return [
            '--no-first-run',
            '--no-default-browser-check',
            '--lang=zh-CN',
            # 🔧 关键修复：保持用户状态，移除破坏性参数
            '--disable-infobars',
            '--enable-extensions',  # 启用扩展
            # 🔧 保持登录状态的关键参数
            '--disable-blink-features=AutomationControlled',  # 隐藏自动化特征
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

    def screenshot(self, file_path: Union[str, Path]) -> Optional[Path]:
        """同步截图方法"""
        try:
            loop = asyncio.get_running_loop()
            return asyncio.run_coroutine_threadsafe(
                self.screenshot_async(file_path), loop
            ).result()
        except RuntimeError:
            return asyncio.run(self.screenshot_async(file_path))

    def get_page_title(self) -> Optional[str]:
        """同步获取页面标题"""
        try:
            loop = asyncio.get_running_loop()
            return asyncio.run_coroutine_threadsafe(
                self.get_page_title_async(), loop
            ).result()
        except RuntimeError:
            return asyncio.run(self.get_page_title_async())

    # ==================== 上下文管理器 ====================

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