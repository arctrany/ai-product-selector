"""
增强版 Playwright 浏览器驱动

在原有基础上增加浏览器自动降级功能和更好的错误处理机制
"""

import asyncio
import logging
import os
import platform
import sys
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext, Page

from rpa.browser.core.exceptions.browser_exceptions import BrowserError, BrowserInitializationError
from rpa.browser.core.models.browser_config import BrowserType


class EnhancedPlaywrightBrowserDriver:
    """增强版 Playwright 浏览器驱动"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化浏览器驱动

        Args:
            config: 浏览器配置字典
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Playwright 组件
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # 状态管理
        self._initialized = False
        self._is_persistent_context = False

        # 浏览器类型和降级列表
        self.browser_type = config.get('browser_type', 'edge')
        self.browser_fallback_list = ['edge', 'chrome', 'chromium']

    async def initialize(self) -> bool:
        """
        初始化浏览器驱动 - 支持自动降级

        Returns:
            bool: 初始化是否成功
        """
        try:
            if self._initialized:
                return True

            self.logger.info("🔧 开始初始化增强版浏览器驱动")

            # 初始化 Playwright
            self.playwright = await async_playwright().start()

            # 尝试启动浏览器，支持自动降级
            success = await self._launch_browser_with_fallback()
            
            if not success:
                error_msg = "❌ 所有浏览器类型都无法启动"
                self.logger.error(error_msg)
                await self._cleanup_on_failure()
                raise BrowserInitializationError(error_msg)

            self._initialized = True
            self.logger.info("✅ 增强版浏览器驱动初始化完成")
            return True

        except Exception as e:
            self.logger.error(f"❌ 浏览器驱动初始化失败: {e}")
            await self._cleanup_on_failure()
            raise

    async def _launch_browser_with_fallback(self) -> bool:
        """
        尝试启动浏览器，支持自动降级

        Returns:
            bool: 启动是否成功
        """
        # 确定要尝试的浏览器列表
        browsers_to_try = self._get_browsers_to_try()
        self.logger.info(f"🔧 将尝试以下浏览器类型: {browsers_to_try}")

        # 获取配置参数
        headless = self.config.get('headless', False)
        user_data_dir = self.config.get('user_data_dir')
        launch_args = self.config.get('launch_args', [])

        # 依次尝试每种浏览器类型
        for browser_type in browsers_to_try:
            try:
                self.logger.info(f"🚀 尝试启动浏览器: {browser_type}")
                
                success = await self._launch_browser(browser_type, headless, user_data_dir, launch_args)
                
                if success:
                    self.logger.info(f"✅ 浏览器启动成功: {browser_type}")
                    # 更新实际使用的浏览器类型
                    self.browser_type = browser_type
                    return True
                else:
                    self.logger.warning(f"⚠️ 浏览器启动失败: {browser_type}")
                    
            except Exception as e:
                self.logger.warning(f"⚠️ 启动浏览器 {browser_type} 时出现异常: {e}")
                # 继续尝试下一个浏览器类型

        # 所有浏览器类型都失败
        return False

    def _get_browsers_to_try(self) -> List[str]:
        """
        获取要尝试的浏览器列表

        Returns:
            List[str]: 浏览器类型列表
        """
        # 如果指定了特定浏览器类型，优先尝试该类型
        preferred_browser = self.config.get('browser_type', 'edge')
        
        if preferred_browser and preferred_browser != 'playwright':
            # 将首选浏览器放在第一位，然后是其他浏览器
            browsers = [preferred_browser]
            browsers.extend([b for b in self.browser_fallback_list if b != preferred_browser])
            return browsers
        else:
            # 使用默认的降级列表
            return self.browser_fallback_list

    async def _launch_browser(self, browser_type: str, headless: bool, 
                            user_data_dir: Optional[str], launch_args: List[str]) -> bool:
        """
        启动指定类型的浏览器

        Args:
            browser_type: 浏览器类型
            headless: 是否无头模式
            user_data_dir: 用户数据目录
            launch_args: 启动参数

        Returns:
            bool: 启动是否成功
        """
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
            
            self.logger.info(f"🔧 启动浏览器: {browser_type}, headless={headless}")

            # 处理用户数据目录
            if user_data_dir is not None:
                self.logger.info(f"🔍 使用指定的用户数据目录: {user_data_dir}")
                
                launch_options_with_extensions = {
                    'headless': headless,
                    'args': launch_options.get('args', []),
                    'ignore_default_args': [
                        # 扩展相关
                        '--disable-extensions',
                        '--disable-component-extensions-with-background-pages',
                        '--disable-default-apps',
                        '--enable-automation',
                        '--disable-component-update',
                        # 关键：忽略破坏登录状态的参数
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

                # 使用指定的用户数据目录
                self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    **launch_options_with_extensions
                )
                self._is_persistent_context = True
                self.logger.info(f"Browser launched with custom user data dir: {user_data_dir}")
            else:
                # 使用系统默认的用户数据目录
                default_user_data_dir = self._get_default_user_data_dir(browser_type)

                if default_user_data_dir and os.path.exists(default_user_data_dir):
                    self.logger.info(f"🔍 使用默认用户数据目录: {default_user_data_dir}")
                    
                    launch_options_with_profile = launch_options.copy()
                    if '--profile-directory=Default' not in launch_options['args']:
                        launch_options_with_profile['args'] = launch_options['args'] + ['--profile-directory=Default']

                    # 启用扩展的参数
                    extension_friendly_args = launch_options_with_profile['args'] + [
                        '--enable-extensions',
                    ]

                    # 移除可能冲突的参数
                    filtered_args = []
                    for arg in extension_friendly_args:
                        if not any(skip in arg for skip in [
                            '--disable-extensions',
                            '--disable-component-extensions',
                            '--disable-default-apps'
                        ]):
                            filtered_args.append(arg)

                    launch_options_with_profile['args'] = filtered_args

                    # 最终启动参数
                    launch_options_with_profile.update({
                        'ignore_default_args': [
                            # 扩展相关
                            '--disable-extensions',
                            '--disable-component-extensions-with-background-pages',
                            '--disable-default-apps',
                            '--enable-automation',
                            '--disable-component-update',
                            # 关键：忽略破坏登录状态的参数
                            '--password-store=basic',
                            '--use-mock-keychain',
                            '--disable-background-networking',
                            '--metrics-recording-only',
                            '--no-service-autorun',
                            '--disable-sync',
                            # 关键：忽略破坏输入记忆的参数
                            '--disable-features=AutofillShowTypePredictions',
                            '--disable-features=PasswordGeneration',
                            '--disable-background-timer-throttling',
                            # 性能优化
                            '--disable-backgrounding-occluded-windows',
                            '--disable-renderer-backgrounding',
                            '--disable-ipc-flooding-protection',
                            '--disable-background-media-suspend',
                            '--no-proxy-server',
                        ]
                    })

                    self.context = await self.playwright.chromium.launch_persistent_context(
                        user_data_dir=default_user_data_dir,
                        **launch_options_with_profile
                    )
                    self._is_persistent_context = True
                    self.logger.info(f"Browser launched with default user data dir: {default_user_data_dir}")
                else:
                    # 如果找不到默认目录，创建临时上下文
                    self.logger.warning(f"🔍 默认用户数据目录不存在，使用临时上下文")
                    self.browser = await self.playwright.chromium.launch(**launch_options)
                    self.context = await self.browser.new_context()
                    self._is_persistent_context = False
                    self.logger.warning("Default user data dir not found, using temporary context")
            
            # 创建页面
            self.page = await self.context.new_page()
            
            # 注入反检测脚本
            await self._inject_stealth_scripts()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to launch browser {browser_type}: {e}")
            return False

    def _get_browser_channel(self, browser_type: str) -> Optional[str]:
        """获取浏览器 channel"""
        system = platform.system().lower()

        if browser_type == 'edge' and system in ["windows", "darwin"]:
            return "msedge"
        elif browser_type == 'chrome' and system in ["windows", "darwin"]:
            return "chrome"

        return "chromium"

    def _get_default_user_data_dir(self, browser_type: str) -> Optional[str]:
        """获取默认用户数据目录"""
        system = platform.system()
        
        if system == "Darwin":  # macOS
            if browser_type == 'edge':
                return os.path.expanduser("~/Library/Application Support/Microsoft Edge")
            else:  # chrome
                return os.path.expanduser("~/Library/Application Support/Google/Chrome")
        elif system == "Windows":
            if browser_type == 'edge':
                return os.path.expanduser("~/AppData/Local/Microsoft/Edge/User Data")
            else:  # chrome
                return os.path.expanduser("~/AppData/Local/Google/Chrome/User Data")
        elif system == "Linux":
            if browser_type == 'edge':
                return os.path.expanduser("~/.config/microsoft-edge")
            else:  # chrome
                return os.path.expanduser("~/.config/google-chrome")
        
        return None

    def _get_default_launch_args(self) -> List[str]:
        """获取默认启动参数"""
        return [
            '--no-first-run',
            '--no-default-browser-check',
            '--lang=zh-CN',
            '--disable-infobars',
            '--enable-extensions',
            '--disable-blink-features=AutomationControlled',
            '--exclude-switches=enable-automation',
            '--enable-password-generation',
            '--enable-autofill',
            '--enable-sync',
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
            
            self.logger.debug("Stealth scripts injected successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to inject stealth scripts: {e}")

    async def _cleanup_on_failure(self) -> None:
        """启动失败时的清理工作"""
        try:
            # 关闭页面
            if self.page:
                await self.page.close()
                self.page = None
            
            # 关闭上下文
            if self.context:
                await self.context.close()
                self.context = None
            
            # 关闭浏览器
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            # 停止 Playwright
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
        except Exception as e:
            self.logger.warning(f"清理资源时出现异常: {e}")

        # 重置状态
        self._initialized = False
        self._is_persistent_context = False

    async def shutdown(self) -> bool:
        """关闭浏览器驱动"""
        if not self._initialized:
            return True
        
        try:
            self.logger.info("Shutting down Enhanced Playwright browser driver...")
            
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
            self.logger.info("Enhanced Playwright browser driver shutdown successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to shutdown browser driver: {e}")
            return False

    def is_initialized(self) -> bool:
        """检查驱动是否已初始化"""
        return self._initialized

    async def open_page(self, url: str, wait_until: str = 'load', timeout: int = 30000) -> bool:
        """打开页面"""
        if not self._initialized or not self.page:
            self.logger.error("Browser driver not initialized")
            return False

        try:
            self.logger.info(f"Navigating to: {url}")
            await self.page.goto(url, wait_until=wait_until, timeout=timeout)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to open page: {e}")
            return False

    async def get_page_title_async(self) -> Optional[str]:
        """获取页面标题"""
        if not self.page:
            return None
        
        try:
            return await self.page.title()
        except Exception as e:
            self.logger.error(f"Failed to get page title: {e}")
            return None

    def get_page(self) -> Optional[Page]:
        """获取页面对象"""
        return self.page

    def get_context(self) -> Optional[BrowserContext]:
        """获取浏览器上下文"""
        return self.context

    def get_browser(self) -> Optional[Browser]:
        """获取浏览器实例"""
        return self.browser

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.shutdown()
