"""
浏览器服务模块 - 服务系统环境
负责浏览器相关的初始化和管理功能，实现操作系统无关的代码，确保兼容性
"""

import asyncio
import os
import subprocess
import time
import tempfile
import platform
import socket
from typing import Optional, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class BrowserService:
    """浏览器服务类 - 提供跨平台的浏览器管理功能"""
    
    def __init__(self, debug_port: int = 9222):
        """
        初始化浏览器服务
        
        Args:
            debug_port: Chrome调试端口，默认9222
        """
        self.debug_port = debug_port
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
    def get_chrome_paths(self) -> Tuple[Optional[str], Optional[str]]:
        """
        获取Chrome可执行文件路径和用户数据目录 - 跨平台支持
        
        Returns:
            Tuple[executable_path, user_data_dir]: Chrome路径和用户数据目录
        """
        system = platform.system().lower()
        
        # Chrome可执行文件路径（按优先级排序）
        chrome_paths = []
        user_data_dirs = []
        
        if system == "darwin":  # macOS
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
                "/usr/local/bin/google-chrome",
                "/usr/local/bin/chromium"
            ]
            user_data_dirs = [
                os.path.expanduser("~/Library/Application Support/Google/Chrome"),
                os.path.expanduser("~/Library/Application Support/Chromium")
            ]


            # Fixme: 这里写死了，应该使用一个系统变量来指定
        elif system == "windows":  # Windows
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', '')),
                r"C:\Program Files\Chromium\Application\chromium.exe",
                r"C:\Program Files (x86)\Chromium\Application\chromium.exe"
            ]
            user_data_dirs = [
                os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data"),
                os.path.expanduser(r"~\AppData\Local\Chromium\User Data")
            ]
            
        else:  # Linux和其他Unix系统
            chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
                "/snap/bin/chromium",
                "/usr/local/bin/google-chrome",
                "/usr/local/bin/chromium"
            ]
            user_data_dirs = [
                os.path.expanduser("~/.config/google-chrome"),
                os.path.expanduser("~/.config/chromium")
            ]
        
        # 查找可用的Chrome可执行文件
        executable_path = None
        for path in chrome_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                executable_path = path
                print(f"✅ 找到Chrome可执行文件: {path}")
                break
        
        if not executable_path:
            print("❌ 未找到Chrome可执行文件")
            print("💡 请确保已安装Google Chrome或Chromium浏览器")
            return None, None
        
        # 查找用户数据目录
        user_data_dir = None
        for path in user_data_dirs:
            if os.path.exists(path):
                user_data_dir = path
                print(f"✅ 找到用户数据目录: {path}")
                break
        
        if not user_data_dir:
            # 使用默认路径
            user_data_dir = user_data_dirs[0] if user_data_dirs else None
            print(f"⚠️ 使用默认用户数据目录: {user_data_dir}")
        
        return executable_path, user_data_dir
    
    def check_chrome_debug_port(self, port: int) -> bool:
        """
        检查Chrome调试端口是否可用
        
        Args:
            port: 要检查的端口号
            
        Returns:
            bool: 端口是否被占用
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result == 0  # 0表示连接成功，端口被占用
        except Exception as e:
            print(f"⚠️ 检查端口时出现异常: {e}")
            return False
    
    def launch_chrome_with_debug_port(self, executable_path: str, user_data_dir: str, debug_port: int) -> bool:
        """
        启动带有调试端口的Chrome实例
        
        Args:
            executable_path: Chrome可执行文件路径
            user_data_dir: 用户数据目录
            debug_port: 调试端口
            
        Returns:
            bool: 启动是否成功
        """
        try:
            # 检查端口是否已被占用
            if self.check_chrome_debug_port(debug_port):
                print(f"✅ 检测到端口{debug_port}已被占用，将尝试连接到现有Chrome实例")
                return True

            print(f"🚀 启动Chrome实例，启用远程调试端口{debug_port}...")
            print("💡 提示：如果启动失败，请先关闭所有Chrome实例后重试")

            # 使用独立的用户数据目录子目录，避免冲突
            debug_user_data_dir = os.path.join(tempfile.gettempdir(), "chrome-debug-session")
            
            # 确保目录存在
            os.makedirs(debug_user_data_dir, exist_ok=True)

            # Chrome启动参数
            chrome_args = [
                executable_path,
                f"--remote-debugging-port={debug_port}",
                f"--user-data-dir={debug_user_data_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-default-apps",
                "about:blank"
            ]

            print(f"📁 使用调试用户数据目录: {debug_user_data_dir}")
            print("💡 注意：这将启动一个独立的Chrome实例用于调试")

            # 在后台启动Chrome
            process = subprocess.Popen(
                chrome_args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )

            # 等待Chrome启动
            print("⏳ 等待Chrome启动...")
            for i in range(10):  # 最多等待10秒
                time.sleep(1)
                if self.check_chrome_debug_port(debug_port):
                    print(f"✅ Chrome成功启动，远程调试端口{debug_port}可用")
                    return True
                print(f"⏳ 等待中... ({i+1}/10)")

            print(f"❌ Chrome启动超时，端口{debug_port}不可用")
            return False
            
        except Exception as e:
            print(f"❌ 启动Chrome失败: {e}")
            return False
    
    async def init_browser(self) -> bool:
        """
        初始化浏览器连接
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            print("🔧 初始化浏览器连接...")
            
            # 获取Chrome路径
            executable_path, user_data_dir = self.get_chrome_paths()
            
            if not executable_path:
                print("❌ 未找到Chrome可执行文件")
                return False
            
            print(f"✅ Chrome可执行文件: {executable_path}")
            
            # 确保Chrome调试实例在运行
            if not self.launch_chrome_with_debug_port(executable_path, user_data_dir, self.debug_port):
                return False
            
            # 连接到Chrome实例
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.connect_over_cdp(f"http://localhost:{self.debug_port}")
            
            print("✅ 成功连接到Chrome实例!")
            
            # 获取或创建浏览器上下文
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
                print(f"✅ 使用现有浏览器上下文，页面数量: {len(self.context.pages)}")
            else:
                self.context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                print("✅ 创建新的浏览器上下文")
            
            # 获取或创建页面
            pages = self.context.pages
            if pages:
                self.page = pages[0]
                print("✅ 使用现有页面")
            else:
                self.page = await self.context.new_page()
                print("✅ 创建新页面")
            
            # 设置页面超时
            self.page.set_default_timeout(30000)  # 30秒
            
            return True
            
        except Exception as e:
            print(f"❌ 初始化浏览器失败: {str(e)}")
            return False
    
    async def get_page(self) -> Optional[Page]:
        """
        获取当前页面对象
        
        Returns:
            Optional[Page]: 页面对象，如果未初始化则返回None
        """
        return self.page
    
    async def navigate_to_url(self, url: str, wait_until: str = 'networkidle') -> bool:
        """
        导航到指定URL
        
        Args:
            url: 目标URL
            wait_until: 等待条件，默认为'networkidle'
            
        Returns:
            bool: 导航是否成功
        """
        try:
            if not self.page:
                print("❌ 页面未初始化")
                return False
                
            print(f"🌐 导航到: {url}")
            await self.page.goto(url, wait_until=wait_until, timeout=30000)
            print("✅ 页面加载完成")
            return True
            
        except Exception as e:
            print(f"❌ 页面导航失败: {str(e)}")
            return False
    
    async def close_browser(self):
        """关闭浏览器和相关资源"""
        try:
            if self.context:
                await self.context.close()
                print("✅ 浏览器上下文已关闭")
                
            if self.browser:
                await self.browser.close()
                print("✅ 浏览器连接已关闭")
                
            if self.playwright:
                await self.playwright.stop()
                print("✅ Playwright已停止")
                
            # 重置状态
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
            
            print("✅ 浏览器资源已完全清理")
            
        except Exception as e:
            print(f"⚠️ 清理浏览器资源时出现警告: {str(e)}")
    
    def is_initialized(self) -> bool:
        """
        检查浏览器是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        return all([self.playwright, self.browser, self.context, self.page])