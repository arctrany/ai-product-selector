"""
选评专用浏览器服务

基于现有的 src_new/rpa/browser 框架，为选评系统提供专门的浏览器自动化服务
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path

from rpa.browser.browser_service import SimplifiedBrowserService, create_debug_browser_service, create_shared_browser_service
from rpa.browser.core.config.config import create_default_browser_service_config
from rpa.browser.core.exceptions.browser_exceptions import BrowserError

from ..models import ScrapingError, ScrapingResult


class XuanpingBrowserService:
    """
    选品专用浏览器服务（线程安全单例模式）

    基于现有的 BrowserService，提供选评系统所需的特定功能：
    - 自动配置用户数据目录和Profile
    - 支持调试端口和会话复用
    - 集成选评系统的配置和异常处理
    - 🔧 关键修复：线程安全的单例模式，确保所有 Scraper 共享同一个浏览器进程
    - 🔧 Task 3.1 (P0-2): 添加引用计数机制，防止一个 Scraper 关闭影响其他 Scraper
    """

    _instance = None
    _lock = None  # 将在类方法中初始化
    # 🔧 Task 3.3 (P1-7): 移除类级别的 _initialized，统一使用实例级别状态管理
    # _initialized = False  # 已移除，使用实例级别的 _initialized

    # 🔧 Task 3.1 (P0-2): 添加引用计数机制
    _reference_count = 0
    _ref_count_lock = None  # 将在类方法中初始化

    def __new__(cls, config: Optional[Dict[str, Any]] = None):
        """线程安全的单例模式：确保只有一个浏览器服务实例"""
        import threading

        # 使用线程锁而不是异步锁，因为 __new__ 是同步的
        if cls._lock is None:
            cls._lock = threading.Lock()

        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized_singleton = False
            return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化选评浏览器服务

        Args:
            config: 浏览器配置，None表示使用默认配置
        """
        import threading

        # 防止重复初始化
        if hasattr(self, '_initialized_singleton') and self._initialized_singleton:
            # 🔧 Task 3.1 (P0-2): 即使是重复初始化，也要增加引用计数
            if self.__class__._ref_count_lock is None:
                self.__class__._ref_count_lock = threading.Lock()
            with self.__class__._ref_count_lock:
                self.__class__._reference_count += 1
                self.logger.info(f"🔢 引用计数增加: {self.__class__._reference_count}")
            return

        self.logger = logging.getLogger(__name__)
        self.config = config or {}

        # 创建浏览器配置
        browser_config = self._create_browser_config()

        # 🔧 关键修复：创建共享的浏览器服务实例，配置持久化上下文和浏览器复用
        self.browser_service = create_shared_browser_service(browser_config)

        # 🔧 Task 3.3 (P1-7): 状态管理统一使用实例级别
        self._initialized = False
        self._browser_started = False
        self._initialized_singleton = True

        # 🔧 Task 3.1 (P0-2): 初始化引用计数锁和增加引用计数
        if self.__class__._ref_count_lock is None:
            self.__class__._ref_count_lock = threading.Lock()

        with self.__class__._ref_count_lock:
            self.__class__._reference_count += 1
            self.logger.info(f"🔢 引用计数初始化: {self.__class__._reference_count}")
        
        self.logger.info("🚀 选评浏览器服务创建完成")
    
    def _create_browser_config(self) -> Dict[str, Any]:
        """
        创建浏览器配置

        🔧 重构逻辑：
        1. 从系统配置读取 required_login_domains
        2. 检查浏览器是否在运行
        3. 验证所有必需域名的登录态（AND 逻辑）
        4. 配置为只连接模式，不启动新浏览器
        5. 如果检测失败，抛出明确错误提示用户手动启动浏览器
        """
        from rpa.browser.utils import detect_active_profile, BrowserDetector, LoginRequiredError
        import json
        import os

        # 从环境变量获取配置
        browser_type = os.environ.get('PREFERRED_BROWSER', 'edge').lower()
        debug_port = os.environ.get('BROWSER_DEBUG_PORT', '9222')

        # 🔧 新增：从系统配置读取 required_login_domains
        required_domains = []
        system_config_path = Path("test_system_config.json")

        if system_config_path.exists():
            try:
                with open(system_config_path, 'r', encoding='utf-8') as f:
                    system_config = json.load(f)
                    required_domains = system_config.get('browser', {}).get('required_login_domains', [])
                    if required_domains:
                        self.logger.info(f"📋 从系统配置读取必需登录域名: {required_domains}")
            except Exception as e:
                self.logger.warning(f"⚠️ 读取系统配置失败，使用默认域名: {e}")
                required_domains = ["seerfar.cn"]
        else:
            self.logger.warning("⚠️ 系统配置文件不存在，使用默认域名")
            required_domains = ["seerfar.cn"]

        # 检查浏览器是否在运行
        detector = BrowserDetector()
        is_browser_running = detector.is_browser_running()

        if not is_browser_running:
            # 启动模式：浏览器未运行
            self.logger.info("🚀 未检测到运行中的浏览器，配置为启动模式")

            # 从配置读取 headless 模式
            browser_config_dict = self.config.get('browser', {})
            headless = browser_config_dict.get('headless', False)

            # 检测有登录态的 Profile
            active_profile = detect_active_profile(required_domains[0] if required_domains else "seerfar.cn")

            # 获取用户数据目录（父目录）
            user_data_dir = detector._get_edge_user_data_dir() if browser_type == 'edge' else None

            # 🔧 关键修复：根据 Playwright 官方文档
            # user_data_dir 应该是父目录，Profile 通过 --profile-directory 参数指定
            # 参考：https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch-persistent-context
            # "Chromium's user data directory is the parent directory of the Profile Path"

            if not active_profile:
                active_profile = "Default"
                self.logger.warning("⚠️ 未检测到有登录态的 Profile，将使用默认 Profile")
            else:
                self.logger.info(f"✅ 检测到有登录态的 Profile: {active_profile}")

            if not user_data_dir:
                self.logger.error("❌ 无法获取用户数据目录")
                raise RuntimeError("无法获取用户数据目录")

            self.logger.info(f"📁 用户数据目录（父目录）: {user_data_dir}")
            self.logger.info(f"📁 Profile 名称: {active_profile}")

            # 启动模式配置
            # 注意：user_data_dir 是父目录，Profile 通过 launch_args 指定
            config = {
                'debug_mode': True,
                'browser_config': {
                    'browser_type': browser_type,
                    'headless': headless,
                    'debug_port': int(debug_port),
                    'user_data_dir': user_data_dir,  # 父目录，不是 Profile 目录
                    'viewport': {
                        'width': 1280,
                        'height': 800
                    },
                    'launch_args': [f'--profile-directory={active_profile}']  # 通过参数指定 Profile
                },
                'use_persistent_context': False,
                'connect_to_existing': False
            }

            self.logger.info(f"🚀 配置为启动模式: headless={headless}, profile={active_profile}")
            return config

        # 连接模式：浏览器正在运行
        self.logger.info("🔗 检测到运行中的浏览器，配置为连接模式")

        # 🔧 新增：验证所有必需域名的登录态（AND 逻辑）
        try:
            is_valid, missing_domains, report = detector.validate_required_logins(required_domains)

            if not is_valid:
                # 输出详细的登录状态报告
                self.logger.error("❌ 登录态验证失败")
                self.logger.error(report)

                # 抛出 LoginRequiredError
                raise LoginRequiredError(
                    missing_domains=missing_domains,
                    message=f"缺少必需域名的登录态: {', '.join(missing_domains)}"
                )

            self.logger.info("✅ 所有必需域名的登录态验证通过")

            # 输出详细的登录状态报告（调试用）
            if self.config.get('debug_mode', False):
                detector.print_login_status_report(required_domains)

        except LoginRequiredError:
            # 直接向上抛出 LoginRequiredError
            raise
        except Exception as e:
            self.logger.error(f"❌ 登录态验证过程出错: {e}")
            raise RuntimeError(f"登录态验证失败: {e}")

        # 检测活跃的 Profile（使用第一个必需域名）
        active_profile = detect_active_profile(required_domains[0])

        if not active_profile:
            error_msg = (
                f"❌ 未找到有 {required_domains[0]} 登录态的 Profile\n"
                "💡 请确保：\n"
                f"   1. 已在 Edge 浏览器中登录 {required_domains[0]}\n"
                "   2. 浏览器正在运行\n"
                "   3. 使用的 Profile 有登录态"
            )
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

        self.logger.info(f"✅ 检测到活跃 Profile: {active_profile}（已验证所有必需域名登录态）")

        # 检查现有浏览器的调试端口
        existing_browser = self._check_existing_browser(debug_port)

        if not existing_browser:
            error_msg = (
                f"❌ 浏览器正在运行，但调试端口 {debug_port} 未开启\n"
                f"💡 请关闭浏览器，然后运行启动脚本：\n"
                f"   ./start_edge_with_debug.sh\n"
                f"   或手动启动：\n"
                f"   /Applications/Microsoft\\ Edge.app/Contents/MacOS/Microsoft\\ Edge \\\n"
                f"     --remote-debugging-port={debug_port} \\\n"
                f"     --profile-directory=\"{active_profile}\""
            )
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

        self.logger.info(f"✅ 检测到浏览器调试端口: {debug_port}")

        # 🔧 关键修复：只配置连接模式，不允许启动新浏览器
        config = {
            'debug_mode': True,
            'browser_config': {
                'browser_type': browser_type,
                'headless': False,
                'debug_port': int(debug_port),
                'user_data_dir': None,  # 连接模式不需要指定用户数据目录
                'viewport': {
                    'width': 1280,
                    'height': 800
                },
                'launch_args': []  # 连接模式不需要启动参数
            },
            'use_persistent_context': False,  # 连接模式不使用持久化上下文
            'connect_to_existing': True,  # 强制连接模式
            'profile_name': active_profile
        }

        self.logger.info(f"🔗 配置为连接模式: Profile={active_profile}, Port={debug_port}")

        return config

    def _check_existing_browser(self, debug_port: str) -> bool:
        """
        检查是否有现有浏览器在指定调试端口运行，并且 CDP 端点可用

        🔧 关键修复：不仅检查端口是否被占用，还要验证 CDP 端点是否真的可用
        """
        try:
            import socket
            import urllib.request
            import json

            # 第一步：检查端口是否被占用
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)  # 1秒超时
            result = sock.connect_ex(('localhost', int(debug_port)))
            sock.close()

            if result != 0:
                self.logger.info(f"🔍 端口 {debug_port} 未被占用，需要创建新浏览器实例")
                return False

            # 第二步：验证 CDP 端点是否可用
            # 尝试访问 /json/version 端点来确认 CDP 是否真的可用
            cdp_url = f"http://localhost:{debug_port}/json/version"
            try:
                req = urllib.request.Request(cdp_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=2) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    # 检查是否有 webSocketDebuggerUrl 字段
                    if 'webSocketDebuggerUrl' in data:
                        self.logger.info(f"✅ 检测到现有浏览器实例在端口 {debug_port}，CDP 端点可用")
                        return True
                    else:
                        self.logger.warning(f"⚠️ 端口 {debug_port} 被占用，但 CDP 端点不可用")
                        return False
            except Exception as cdp_error:
                self.logger.warning(f"⚠️ 端口 {debug_port} 被占用，但无法访问 CDP 端点: {cdp_error}")
                return False

        except Exception as e:
            self.logger.debug(f"检查现有浏览器失败: {e}")
            return False
    
    async def initialize(self) -> bool:
        """
        初始化浏览器服务
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            if self._initialized:
                return True
            
            self.logger.info("🔧 开始初始化选评浏览器服务")
            
            # 初始化浏览器服务
            success = await self.browser_service.initialize()
            if not success:
                raise ScrapingError("浏览器服务初始化失败")
            
            self._initialized = True
            self.logger.info("✅ 选评浏览器服务初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 选评浏览器服务初始化失败: {e}")
            return False
    
    async def start_browser(self) -> bool:
        """
        启动浏览器 - 🔧 关键修复：优先连接现有浏览器，失败时提供用户友好的解决方案

        Returns:
            bool: 启动是否成功
        """
        try:
            if not self._initialized:
                await self.initialize()

            if self._browser_started:
                return True

            self.logger.info("🌐 启动浏览器")

            # 🔧 关键修复：尝试启动浏览器，如果失败则提供解决方案
            try:
                success = await self.browser_service.start_browser()
                if success:
                    self._browser_started = True
                    self.logger.info("✅ 浏览器启动成功")
                    return True
                else:
                    raise ScrapingError("浏览器启动失败")

            except Exception as browser_error:
                # 🔧 关键修复：检查是否是浏览器进程冲突问题
                error_msg = str(browser_error).lower()
                if "processingleton" in error_msg or "already in use" in error_msg or "profile is already" in error_msg:
                    self.logger.warning("⚠️ 检测到浏览器进程冲突，尝试解决方案...")

                    # 尝试解决方案1：等待一段时间后重试
                    self.logger.info("🔄 等待3秒后重试...")
                    await asyncio.sleep(3)

                    try:
                        success = await self.browser_service.start_browser()
                        if success:
                            self._browser_started = True
                            self.logger.info("✅ 重试成功，浏览器启动完成")
                            return True
                    except Exception:
                        pass

                    # 🔧 关键修复：提供用户友好的错误信息和解决方案
                    self.logger.error("❌ 浏览器进程冲突无法自动解决")
                    self.logger.error("💡 解决方案：")
                    self.logger.error("   1. 关闭所有 Edge 浏览器窗口")
                    self.logger.error("   2. 或者在终端运行：pkill -f 'Microsoft Edge'")
                    self.logger.error("   3. 然后重新运行程序")

                    # 🔧 不直接退出程序，而是返回失败状态
                    return False
                else:
                    # 其他类型的错误
                    raise browser_error

        except Exception as e:
            self.logger.error(f"❌ 浏览器启动失败: {e}")
            return False
    
    async def navigate_to(self, url: str) -> bool:
        """
        导航到指定URL
        
        Args:
            url: 目标URL
            
        Returns:
            bool: 导航是否成功
        """
        try:
            if not self._browser_started:
                await self.start_browser()
            
            self.logger.info(f"🔗 导航到: {url}")
            
            success = await self.browser_service.navigate_to(url)
            if success:
                self.logger.info("✅ 页面导航成功")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 页面导航失败: {e}")
            return False
    
    async def scrape_page_data(self, url: str, extractor_func) -> ScrapingResult:
        """
        抓取页面数据
        
        Args:
            url: 目标URL
            extractor_func: 数据提取函数
            
        Returns:
            ScrapingResult: 抓取结果
        """
        # 🔧 Task 3.2 (P1-9): 使用 get_running_loop() 替代 get_event_loop()
        start_time = asyncio.get_running_loop().time()

        try:
            # 导航到页面
            success = await self.navigate_to(url)
            if not success:
                return ScrapingResult(
                    success=False,
                    data={},
                    error_message="页面导航失败",
                    execution_time=asyncio.get_running_loop().time() - start_time
                )
            
            # 等待页面加载
            await asyncio.sleep(1)
            
            # 提取数据
            data = await extractor_func(self.browser_service)
            
            # 🔧 Task 3.2 (P1-9): 使用 get_running_loop() 替代 get_event_loop()
            execution_time = asyncio.get_running_loop().time() - start_time

            return ScrapingResult(
                success=True,
                data=data,
                execution_time=execution_time
            )

        except Exception as e:
            # 🔧 Task 3.2 (P1-9): 使用 get_running_loop() 替代 get_event_loop()
            execution_time = asyncio.get_running_loop().time() - start_time
            self.logger.error(f"❌ 页面数据抓取失败: {e}")
            
            return ScrapingResult(
                success=False,
                data={},
                error_message=str(e),
                execution_time=execution_time
            )
    
    async def get_page_content(self) -> str:
        """
        获取页面内容
        
        Returns:
            str: 页面HTML内容
        """
        try:
            return await self.browser_service.get_page_content()
        except Exception as e:
            self.logger.error(f"❌ 获取页面内容失败: {e}")
            return ""
    
    async def close(self, force: bool = False) -> bool:
        """
        关闭浏览器服务

        🔧 Task 3.1 (P0-2): 添加引用计数机制
        - 只有当引用计数降为 0 时才真正关闭浏览器
        - 支持 force 参数强制关闭

        Args:
            force: 是否强制关闭，忽略引用计数

        Returns:
            bool: 关闭是否成功
        """
        import threading

        try:
            # 🔧 Task 3.1 (P0-2): 引用计数管理
            if self.__class__._ref_count_lock is None:
                self.__class__._ref_count_lock = threading.Lock()

            with self.__class__._ref_count_lock:
                # 减少引用计数
                if self.__class__._reference_count > 0:
                    self.__class__._reference_count -= 1
                    self.logger.info(f"🔢 引用计数减少: {self.__class__._reference_count}")

                # 检查是否应该真正关闭浏览器
                if force:
                    self.logger.warning(f"⚠️ 强制关闭浏览器（忽略引用计数: {self.__class__._reference_count}）")
                    should_close = True
                    # 强制关闭时重置引用计数
                    self.__class__._reference_count = 0
                elif self.__class__._reference_count <= 0:
                    self.logger.info("✅ 引用计数为 0，执行真正的关闭")
                    should_close = True
                else:
                    self.logger.info(f"🔄 还有 {self.__class__._reference_count} 个引用，保持浏览器运行")
                    should_close = False

            # 如果不应该关闭，只重置实例状态
            if not should_close:
                self._initialized = False
                self._browser_started = False
                self.logger.info("✅ 实例状态已重置（浏览器保持运行）")
                return True

            # 真正关闭浏览器
            success = await self.browser_service.close()
            
            self._initialized = False
            self._browser_started = False
            
            if success:
                self.logger.info("✅ 选评浏览器服务已关闭")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ 关闭选评浏览器服务失败: {e}")
            return False
    
    # 上下文管理器支持
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        await self.start_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()


# 工厂函数
def create_xuanping_browser_service(config: Optional[Dict[str, Any]] = None) -> XuanpingBrowserService:
    """
    创建选评浏览器服务
    
    Args:
        config: 配置字典
        
    Returns:
        XuanpingBrowserService: 选评浏览器服务实例
    """
    return XuanpingBrowserService(config)


# 同步包装器（向后兼容）
class XuanpingBrowserServiceSync:
    """
    选评浏览器服务的同步包装器
    
    直接暴露常用对象以简化 API：
    - browser_service.page: Playwright Page 对象
    - browser_service.browser: Browser 对象
    - browser_service.context: BrowserContext 对象

    🔧 关键修复：使用共享事件循环确保所有 Playwright 操作在同一个事件循环中执行
    """

    # 类级别的共享事件循环和线程
    _shared_loop: Optional[asyncio.AbstractEventLoop] = None
    _shared_thread: Optional[Any] = None
    _loop_lock = None  # 将在第一次使用时初始化

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.async_service = XuanpingBrowserService(config)
        self.logger = logging.getLogger(__name__)

        # 初始化锁
        if XuanpingBrowserServiceSync._loop_lock is None:
            import threading
            XuanpingBrowserServiceSync._loop_lock = threading.Lock()

        # 确保共享事件循环已启动
        self._ensure_shared_loop()

        # 直接暴露常用属性（初始为 None，启动浏览器后更新）
        self.page = None
        self.browser = None
        self.context = None

    def _ensure_shared_loop(self):
        """确保共享事件循环已启动 - 🔧 关键修复：所有实例共享同一个事件循环"""
        import threading

        with XuanpingBrowserServiceSync._loop_lock:
            if XuanpingBrowserServiceSync._shared_loop is not None:
                # 检查事件循环是否仍在运行
                if XuanpingBrowserServiceSync._shared_loop.is_running():
                    return
                else:
                    # 事件循环已停止，需要重新创建
                    self.logger.warning("⚠️ 共享事件循环已停止，重新创建")
                    XuanpingBrowserServiceSync._shared_loop = None
                    XuanpingBrowserServiceSync._shared_thread = None

            # 创建新的事件循环和线程
            def run_event_loop():
                """在独立线程中运行事件循环"""
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                XuanpingBrowserServiceSync._shared_loop = loop

                self.logger.info("🔄 共享事件循环已启动")

                try:
                    loop.run_forever()
                except Exception as e:
                    self.logger.error(f"❌ 共享事件循环异常: {e}")
                finally:
                    try:
                        # 清理未完成的任务
                        pending = asyncio.all_tasks(loop)
                        for task in pending:
                            task.cancel()
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                        loop.close()
                    except Exception as e:
                        self.logger.error(f"❌ 清理事件循环失败: {e}")

                    XuanpingBrowserServiceSync._shared_loop = None
                    self.logger.info("🛑 共享事件循环已停止")

            # 启动事件循环线程
            thread = threading.Thread(target=run_event_loop, daemon=True, name="AsyncEventLoop")
            thread.start()
            XuanpingBrowserServiceSync._shared_thread = thread

            # 等待事件循环准备就绪
            import time
            max_wait = 5  # 最多等待5秒
            waited = 0
            while XuanpingBrowserServiceSync._shared_loop is None and waited < max_wait:
                time.sleep(0.1)
                waited += 0.1

            if XuanpingBrowserServiceSync._shared_loop is None:
                raise RuntimeError("共享事件循环创建失败")

            self.logger.info("✅ 共享事件循环准备就绪")

    def _run_async(self, coro):
        """
        运行异步函数 - 🔧 关键修复：在共享事件循环中执行所有异步操作

        这确保了所有 Playwright 对象始终在同一个事件循环中操作，
        从而彻底解决 "The future belongs to a different loop" 错误
        """
        try:
            # 确保共享事件循环正在运行
            if (XuanpingBrowserServiceSync._shared_loop is None or
                not XuanpingBrowserServiceSync._shared_loop.is_running()):
                self._ensure_shared_loop()

            # 在共享事件循环中执行协程
            future = asyncio.run_coroutine_threadsafe(
                coro,
                XuanpingBrowserServiceSync._shared_loop
            )

            # 等待结果（60秒超时）
            return future.result(timeout=60)

        except Exception as e:
            self.logger.error(f"❌ 异步函数执行失败: {e}")
            raise


    
    def initialize(self) -> bool:
        """
        同步初始化

        🔧 Task 4.3 (P1-8): 初始化成功后自动更新浏览器对象
        """
        result = self._run_async(self.async_service.initialize())
        if result:
            # 🔧 Task 4.3: 初始化成功后尝试更新浏览器对象
            # 注意：初始化后可能还没有 page 对象，所以这里可能会失败，这是正常的
            try:
                self._update_browser_objects()
            except BrowserError:
                # 初始化后可能还没有 page，这是正常的，忽略错误
                pass
        return result
    
    def start_browser(self) -> bool:
        """同步启动浏览器，并更新暴露的属性"""
        result = self._run_async(self.async_service.start_browser())
        if result:
            # 更新暴露的属性
            self._update_browser_objects()
        return result

    def _update_browser_objects(self):
        """
        更新暴露的浏览器对象

        🔧 Task 4.1 (P0-6): 简化访问路径，添加逐层验证
        🔧 Task 4.2 (P0-1): 增强错误处理，失败时抛出异常
        """
        try:
            # 🔧 Task 4.1: 逐层验证，提供明确的错误信息

            # 第 1 层：验证 async_service
            if not self.async_service:
                raise BrowserError("async_service is None - XuanpingBrowserService not initialized")

            # 第 2 层：验证 browser_service
            if not hasattr(self.async_service, 'browser_service') or not self.async_service.browser_service:
                raise BrowserError("browser_service is None - SimplifiedBrowserService not initialized")

            browser_service = self.async_service.browser_service

            # 第 3 层：验证 browser_driver
            if not hasattr(browser_service, 'browser_driver') or not browser_service.browser_driver:
                raise BrowserError("browser_driver is None - PlaywrightBrowserDriver not initialized")

            driver = browser_service.browser_driver

            # 第 4 层：验证浏览器对象
            if not hasattr(driver, 'page') or not driver.page:
                raise BrowserError("page is None - Browser page not created")

            if not hasattr(driver, 'browser'):
                raise BrowserError("browser attribute not found on driver")

            if not hasattr(driver, 'context'):
                raise BrowserError("context attribute not found on driver")

            # 所有验证通过，更新对象
            self.page = driver.page
            self.browser = driver.browser
            self.context = driver.context

            self.logger.debug("✅ 浏览器对象已更新")

        except BrowserError:
            # 🔧 Task 4.2: BrowserError 直接向上抛出
            raise
        except (AttributeError, TypeError) as e:
            # 🔧 Task 4.2: 其他异常包装为 BrowserError 并抛出
            self.logger.error(f"❌ 更新浏览器对象失败: {e}")
            raise BrowserError(f"Failed to update browser objects: {e}") from e
    
    def navigate_to(self, url: str) -> bool:
        """
        同步导航

        🔧 Task 4.3 (P1-8): 导航成功后自动更新浏览器对象
        """
        result = self._run_async(self.async_service.navigate_to(url))
        if result:
            # 🔧 Task 4.3: 导航成功后自动更新浏览器对象
            self._update_browser_objects()
        return result
    
    def scrape_page_data(self, url: str, extractor_func) -> ScrapingResult:
        """
        同步抓取数据 - 传递 self 以便提取函数可以访问 page 属性

        🔧 Task 4.4 (P1-10): 增强异步/同步边界安全性
        """
        async def wrapper_extractor(browser_service):
            # 🔧 Task 4.4: 在提取数据前，确保浏览器对象已更新
            # 因为 navigate_to 可能会启动浏览器，但不会自动更新同步包装器的属性
            try:
                self._update_browser_objects()
            except BrowserError as e:
                # 🔧 Task 4.4: 如果更新失败，提供明确的错误信息
                self.logger.error(f"❌ 更新浏览器对象失败，无法提取数据: {e}")
                raise

            # 传递 self 而不是 browser_service，这样提取函数可以访问 self.page
            return await extractor_func(self)

        return self._run_async(self.async_service.scrape_page_data(url, wrapper_extractor))
    
    def close(self) -> bool:
        """同步关闭"""
        return self._run_async(self.async_service.close())
    
    def __enter__(self):
        """同步上下文管理器入口"""
        self.initialize()
        self.start_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """同步上下文管理器出口"""
        self.close()


# 导出
__all__ = [
    'XuanpingBrowserService',
    'XuanpingBrowserServiceSync',
    'create_xuanping_browser_service'
]