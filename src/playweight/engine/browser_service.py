"""
浏览器服务模块 - 服务系统环境
负责浏览器相关的初始化和管理功能，实现操作系统无关的代码，确保兼容性
支持Edge（默认）和Chrome浏览器，支持插件加载功能
"""

import asyncio
import io
import json
import os
import subprocess
import time
import tempfile
import platform
import socket
import shutil
import zipfile
from typing import Optional, Tuple, List, Dict, Union
from enum import Enum

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
except ImportError:
    print("⚠️ Playwright未安装，请运行: pip install playwright")
    print("⚠️ 安装后还需要运行: playwright install")
    async_playwright = None
    Browser = None
    BrowserContext = None
    Page = None


class BrowserType(Enum):
    """支持的浏览器类型"""
    EDGE = "edge"
    CHROME = "chrome"


class ExtensionFormat(Enum):
    """支持的扩展格式"""
    CRX = "crx"  # Chrome扩展文件
    UNPACKED = "unpacked"  # 解压的扩展目录


class BrowserService:
    """浏览器服务类 - 提供跨平台的浏览器管理功能，支持Edge（默认）和Chrome"""

    def __init__(self,
                 browser_type: BrowserType = BrowserType.EDGE,
                 debug_port: int = 9222,
                 extensions: Optional[List[str]] = None,
                 config_file: Optional[str] = None,
                 headless: bool = False):
        """
        初始化浏览器服务

        Args:
            browser_type: 浏览器类型，默认Edge
            debug_port: 调试端口，默认9222
            extensions: 扩展程序路径列表
            config_file: 配置文件路径
        """
        self.browser_type = browser_type
        self.debug_port = debug_port
        self.extensions = extensions or []
        self.config_file = config_file
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.current_browser_executable = None
        self.current_user_data_dir = None
        self._pw_loop: Optional[asyncio.AbstractEventLoop] = None

        # 加载配置
        self.config = self._load_config()

    def _get_browser_name(self, browser_type: BrowserType) -> str:
        """获取浏览器名称"""
        return "Edge" if browser_type == BrowserType.EDGE else "Chrome"

    def _get_user_data_dir(self, browser_type: BrowserType) -> str:
        """获取浏览器用户数据目录"""
        system = platform.system().lower()

        if browser_type == BrowserType.EDGE:
            if system == "darwin":
                return os.path.expanduser("~/Library/Application Support/Microsoft Edge")
            elif system == "windows":
                return os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\User Data")
            else:
                return os.path.expanduser("~/.config/microsoft-edge")
        else:  # Chrome
            if system == "darwin":
                return os.path.expanduser("~/Library/Application Support/Google/Chrome")
            elif system == "windows":
                return os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data")
            else:
                return os.path.expanduser("~/.config/google-chrome")

    def _find_executable_and_data_dir(self, executable_paths: List[str], data_dir_paths: List[str],
                                      browser_name: str) -> Tuple[Optional[str], Optional[str]]:
        """通用的可执行文件和数据目录查找方法"""
        # 查找可执行文件
        executable_path = None
        for path in executable_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                executable_path = path
                print(f"✅ 找到{browser_name}可执行文件: {path}")
                break

        if not executable_path:
            print(f"❌ 未找到{browser_name}可执行文件")
            return None, None

        # 查找用户数据目录
        user_data_dir = None
        for path in data_dir_paths:
            if os.path.exists(path):
                user_data_dir = path
                print(f"✅ 找到{browser_name}用户数据目录: {path}")
                break

        if not user_data_dir:
            # 使用默认路径
            user_data_dir = data_dir_paths[0] if data_dir_paths else None
            print(f"⚠️ 使用默认{browser_name}用户数据目录: {user_data_dir}")

        return executable_path, user_data_dir

    def _load_config(self) -> Dict[str, any]:
        """
        加载配置文件

        Returns:
            Dict[str, any]: 配置字典
        """
        import json

        default_config = {
            "browser": {
                "default_type": "edge",
                "fallback_to_chrome": True,
                "debug_port": 9222,
                "custom_paths": {
                    "edge": None,
                    "chrome": None
                }
            },
            "extensions": {
                "auto_load": True,
                "local_paths": [],
                "store_extensions": []
            },
            "user_data": {
                "persistent": True,
                "custom_dir": None
            }
        }

        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合并配置
                    default_config.update(user_config)
            except Exception as e:
                print(f"⚠️ 加载配置文件失败，使用默认配置: {e}")

        return default_config

    def get_edge_paths(self) -> Tuple[Optional[str], Optional[str]]:
        """
        获取Edge可执行文件路径和用户数据目录 - 跨平台支持

        Returns:
            Tuple[executable_path, user_data_dir]: Edge路径和用户数据目录
        """
        system = platform.system().lower()

        # 检查自定义路径
        custom_edge_path = self.config.get("browser", {}).get("custom_paths", {}).get("edge")
        if custom_edge_path and os.path.exists(custom_edge_path):
            print(f"✅ 使用自定义Edge路径: {custom_edge_path}")
            return custom_edge_path, self._get_user_data_dir(BrowserType.EDGE)

        # Edge可执行文件路径（按优先级排序）
        edge_paths = []
        user_data_dirs = []

        if system == "darwin":  # macOS
            edge_paths = [
                "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                "/Applications/Microsoft Edge Beta.app/Contents/MacOS/Microsoft Edge Beta",
                "/Applications/Microsoft Edge Dev.app/Contents/MacOS/Microsoft Edge Dev",
                "/Applications/Microsoft Edge Canary.app/Contents/MacOS/Microsoft Edge Canary",
                "/usr/local/bin/microsoft-edge",
                "/opt/homebrew/bin/microsoft-edge"
            ]
            user_data_dirs = [
                os.path.expanduser("~/Library/Application Support/Microsoft Edge"),
                os.path.expanduser("~/Library/Application Support/Microsoft Edge Beta"),
                os.path.expanduser("~/Library/Application Support/Microsoft Edge Dev"),
                os.path.expanduser("~/Library/Application Support/Microsoft Edge Canary")
            ]

        elif system == "windows":  # Windows
            edge_paths = [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                r"C:\Users\{}\AppData\Local\Microsoft\Edge\Application\msedge.exe".format(os.getenv('USERNAME', '')),
                r"C:\Program Files (x86)\Microsoft\Edge Beta\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge Beta\Application\msedge.exe",
                r"C:\Program Files (x86)\Microsoft\Edge Dev\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge Dev\Application\msedge.exe"
            ]
            user_data_dirs = [
                os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\User Data"),
                os.path.expanduser(r"~\AppData\Local\Microsoft\Edge Beta\User Data"),
                os.path.expanduser(r"~\AppData\Local\Microsoft\Edge Dev\User Data")
            ]

        else:  # Linux和其他Unix系统
            edge_paths = [
                "/usr/bin/microsoft-edge",
                "/usr/bin/microsoft-edge-stable",
                "/usr/bin/microsoft-edge-beta",
                "/usr/bin/microsoft-edge-dev",
                "/opt/microsoft/msedge/msedge",
                "/snap/bin/microsoft-edge",
                "/usr/local/bin/microsoft-edge"
            ]
            user_data_dirs = [
                os.path.expanduser("~/.config/microsoft-edge"),
                os.path.expanduser("~/.config/microsoft-edge-beta"),
                os.path.expanduser("~/.config/microsoft-edge-dev")
            ]

        return self._find_executable_and_data_dir(edge_paths, user_data_dirs, "Edge")

    def get_chrome_paths(self) -> Tuple[Optional[str], Optional[str]]:
        """
        获取Chrome可执行文件路径和用户数据目录 - 跨平台支持
        
        Returns:
            Tuple[executable_path, user_data_dir]: Chrome路径和用户数据目录
        """
        system = platform.system().lower()

        # 检查自定义路径
        custom_chrome_path = self.config.get("browser", {}).get("custom_paths", {}).get("chrome")
        if custom_chrome_path and os.path.exists(custom_chrome_path):
            print(f"✅ 使用自定义Chrome路径: {custom_chrome_path}")
            return custom_chrome_path, self._get_user_data_dir(BrowserType.CHROME)

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

        return self._find_executable_and_data_dir(chrome_paths, user_data_dirs, "Chrome")

    def get_browser_paths(self) -> Tuple[Optional[str], Optional[str], BrowserType]:
        """
        自动检测并获取可用的浏览器路径，优先Edge，备选Chrome

        Returns:
            Tuple[executable_path, user_data_dir, browser_type]: 浏览器路径、用户数据目录和类型
        """
        print("🔍 自动检测可用浏览器...")

        # 优先尝试Edge
        edge_executable, edge_user_data = self.get_edge_paths()
        if edge_executable:
            print("✅ 选择Edge作为默认浏览器")
            return edge_executable, edge_user_data, BrowserType.EDGE

        # 备选Chrome
        if self.config.get("browser", {}).get("fallback_to_chrome", True):
            print("⚠️ Edge不可用，尝试使用Chrome")
            chrome_executable, chrome_user_data = self.get_chrome_paths()
            if chrome_executable:
                print("✅ 选择Chrome作为备选浏览器")
                return chrome_executable, chrome_user_data, BrowserType.CHROME

        print("❌ 未找到可用的浏览器")
        return None, None, None

    def prepare_extensions(self) -> List[str]:
        """
        准备扩展程序参数

        Returns:
            List[str]: 扩展程序启动参数列表
        """
        extension_args = []

        # 从配置文件加载扩展
        config_extensions = self.config.get("extensions", {}).get("local_paths", [])
        all_extensions = list(set(self.extensions + config_extensions))  # 去重

        if not all_extensions:
            return extension_args

        print(f"🔌 准备加载 {len(all_extensions)} 个扩展程序...")

        valid_extensions = []
        for ext_path in all_extensions:
            if os.path.exists(ext_path):
                if os.path.isdir(ext_path):
                    # 解压的扩展目录
                    valid_extensions.append(ext_path)
                    print(f"✅ 找到扩展目录: {ext_path}")
                elif ext_path.endswith('.crx'):
                    # CRX文件需要先解压
                    unpacked_dir = self._unpack_crx_extension(ext_path)
                    if unpacked_dir:
                        valid_extensions.append(unpacked_dir)
                        print(f"✅ 解压CRX扩展: {ext_path} -> {unpacked_dir}")
                else:
                    print(f"⚠️ 不支持的扩展格式: {ext_path}")
            else:
                print(f"❌ 扩展路径不存在: {ext_path}")

        if valid_extensions:
            # 使用逗号分隔的路径列表
            extension_paths = ",".join(valid_extensions)
            extension_args.extend([
                f"--load-extension={extension_paths}",
                "--disable-extensions-except=" + extension_paths
            ])
            print(f"🔌 将加载扩展: {extension_paths}")

        return extension_args

    def _unpack_crx_extension(self, crx_path: str) -> Optional[str]:
        """
        解压CRX扩展文件

        Args:
            crx_path: CRX文件路径

        Returns:
            Optional[str]: 解压后的目录路径
        """
        try:
            import zipfile

            # 创建临时解压目录
            temp_dir = tempfile.mkdtemp(prefix="crx_extension_")

            # CRX文件实际上是ZIP格式，但有额外的头部
            with open(crx_path, 'rb') as f:
                # 跳过CRX头部（通常是16字节）
                magic = f.read(4)
                if magic != b'Cr24':
                    print(f"⚠️ 不是有效的CRX文件: {crx_path}")
                    return None

                version = int.from_bytes(f.read(4), 'little')
                pub_key_len = int.from_bytes(f.read(4), 'little')
                sig_len = int.from_bytes(f.read(4), 'little')

                # 跳过公钥和签名
                f.seek(pub_key_len + sig_len, 1)

                # 剩余部分是ZIP数据
                zip_data = f.read()

            # 解压ZIP数据
            with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
                zip_file.extractall(temp_dir)

            print(f"✅ CRX扩展解压成功: {temp_dir}")
            return temp_dir

        except Exception as e:
            print(f"❌ 解压CRX扩展失败: {e}")
            return None

    def check_debug_port(self, port: int) -> bool:
        """
        检查浏览器调试端口是否可用
        
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

    def check_browser_running(self, browser_type: BrowserType) -> bool:
        """
        检查浏览器是否正在运行（不管是否有调试端口）

        Args:
            browser_type: 浏览器类型

        Returns:
            bool: 浏览器是否正在运行
        """
        try:
            browser_name = "Microsoft Edge" if browser_type == BrowserType.EDGE else "Google Chrome"

            # 检查进程
            result = subprocess.run(['pgrep', '-f', browser_name],
                                    capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"⚠️ 检查浏览器进程时出现异常: {e}")
            return False

    def launch_browser_with_debug_port(self, executable_path: str, user_data_dir: str, debug_port: int,
                                       browser_type: BrowserType) -> bool:
        """
        启动带有调试端口的浏览器实例（支持Edge和Chrome）

        Args:
            executable_path: 浏览器可执行文件路径
            user_data_dir: 用户数据目录
            debug_port: 调试端口
            browser_type: 浏览器类型
            
        Returns:
            bool: 启动是否成功
        """
        try:
            browser_name = self._get_browser_name(browser_type)

            # 首先检查端口是否已被占用
            print(f"🔍 检查端口{debug_port}是否已有{browser_name}实例运行...")
            if self.check_debug_port(debug_port):
                print(f"✅ 检测到端口{debug_port}已被占用")
                print(f"🔄 将复用现有的{browser_name}实例，无需启动新实例")
                print(f"💡 这正是您需要的 - 使用已有的{browser_name}实例！")
                print(f"🔌 现有实例将保持您的所有插件和设置")
                return True

            # 检查是否有普通浏览器实例在运行
            print(f"🔍 检查是否有普通{browser_name}实例在运行...")
            if self.check_browser_running(browser_type):
                print(f"⚠️ 检测到普通{browser_name}实例正在运行，但没有调试端口")
                print(f"💡 为了保持您的插件和设置，建议您手动重启{browser_name}")
                print(f"📝 请按以下步骤操作：")
                print(f"   1. 完全关闭当前的{browser_name}浏览器")
                print(f"   2. 重新运行此程序，它将启动带调试端口的{browser_name}")
                print(f"   3. 这样可以确保您的插件和设置正常工作")
                print(f"")
                print(f"🤖 或者，程序可以自动为您重启{browser_name}（可能需要重新登录插件）")

                # 给用户5秒时间手动关闭浏览器
                print(f"⏳ 等待5秒，如果您想手动关闭{browser_name}...")
                for i in range(5):
                    time.sleep(1)
                    if not self.check_browser_running(browser_type):
                        print(f"✅ 检测到{browser_name}已关闭，继续启动调试实例")
                        break
                    print(f"⏳ 等待中... ({5 - i}秒后自动重启)")

                # 如果用户没有手动关闭，则自动关闭
                if self.check_browser_running(browser_type):
                    print(f"🔄 自动关闭现有{browser_name}实例...")
                    try:
                        if browser_type == BrowserType.EDGE:
                            subprocess.run(['pkill', '-f', 'Microsoft Edge'], check=False)
                        else:
                            subprocess.run(['pkill', '-f', 'Google Chrome'], check=False)

                        time.sleep(3)  # 等待进程完全关闭
                        print(f"✅ 已关闭现有{browser_name}实例")
                    except Exception as e:
                        print(f"⚠️ 关闭{browser_name}时出现警告: {e}")

            # 启动新实例
            print(f"🚀 启动{browser_name}实例，启用远程调试端口{debug_port}...")
            print(f"🔌 将使用您的用户配置目录以保持插件和设置")

            # 使用用户的实际浏览器配置目录，以便复用插件和设置
            debug_user_data_dir = user_data_dir

            # 确保用户数据目录存在
            if debug_user_data_dir and not os.path.exists(debug_user_data_dir):
                try:
                    os.makedirs(debug_user_data_dir, exist_ok=True)
                    print(f"✅ 创建用户数据目录: {debug_user_data_dir}")
                except Exception as e:
                    print(f"⚠️ 无法创建用户数据目录: {e}")
                    # 不使用临时目录，而是尝试使用默认位置
                    if browser_type == BrowserType.EDGE:
                        debug_user_data_dir = self._get_edge_user_data_dir()
                    else:
                        debug_user_data_dir = self._get_chrome_user_data_dir()
                    print(f"🔄 使用默认用户数据目录: {debug_user_data_dir}")

            # 准备扩展参数
            extension_args = self.prepare_extensions()

            # 浏览器启动参数 - 优化以保持插件兼容性和后台运行
            browser_args = [
                executable_path,
                f"--remote-debugging-port={debug_port}",
                f"--user-data-dir={debug_user_data_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-default-apps",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                # 保持插件兼容性的参数
                "--enable-extensions",
                "--load-extension-keep-alive",
                "--disable-extensions-file-access-check",
                # 后台运行优化参数 - 强制防止前台激活
                "--window-position=-2000,-2000",  # 窗口位置设置到屏幕外（更强力）
                "--window-size=800,600",  # 设置较小的窗口大小
                "--disable-popup-blocking",  # 禁用弹窗阻止
                "--disable-background-mode",  # 禁用后台模式
                "--disable-background-networking",  # 禁用后台网络
                "--disable-notifications",  # 禁用通知
                "--disable-desktop-notifications",  # 禁用桌面通知
                "--no-startup-window",  # 启动时不显示窗口
                # 强制后台运行参数 - 防止自动化操作时跳到前台
                "--disable-features=VizDisplayCompositor",  # 禁用显示合成器
                "--disable-gpu",  # 禁用GPU加速（防止窗口激活）
                "--disable-software-rasterizer",  # 禁用软件光栅化
                "--disable-ipc-flooding-protection",  # 禁用IPC洪水保护
                "--disable-hang-monitor",  # 禁用挂起监视器
                "--disable-prompt-on-repost",  # 禁用重新提交提示
                "--disable-client-side-phishing-detection",  # 禁用钓鱼检测
                "--disable-component-extensions-with-background-pages",  # 禁用后台页面扩展
                "--disable-sync",  # 禁用同步
                "--disable-translate",  # 禁用翻译
                "--disable-add-to-shelf",  # 禁用添加到书架
                "--autoplay-policy=no-user-gesture-required",  # 自动播放策略
                "--no-sandbox",  # 禁用沙盒（减少系统调用）
                "--disable-web-security",  # 禁用Web安全（减少弹窗）
                "--disable-features=TranslateUI",  # 禁用翻译UI
                "--disable-features=MediaRouter",  # 禁用媒体路由器
                "--disable-blink-features=AutomationControlled",  # 隐藏自动化控制标识
                # 超强力后台运行参数 - 彻底防止窗口激活和前台跳转
                "--disable-features=kBackgroundMode",  # 彻底禁用后台模式
                "--disable-field-trial-config",  # 禁用字段试验配置
                "--disable-background-sync",  # 禁用后台同步
                "--disable-background-fetch",  # 禁用后台获取
                "--disable-background-task-scheduler",  # 禁用后台任务调度器
                "--disable-background-tracing",  # 禁用后台跟踪
                # macOS特定的窗口管理参数
                "--disable-features=kMacSystemMediaPermissionInfoUi",  # 禁用macOS系统媒体权限UI
                "--disable-features=kMacViewsNativeAppWindows",  # 禁用macOS原生应用窗口
                "--disable-features=kMacSystemShareMenu",  # 禁用macOS系统分享菜单
                "--disable-features=kMacFullSizeContentView",  # 禁用macOS全尺寸内容视图
                "--disable-features=kMacTouchBar",  # 禁用macOS触控栏
                "--disable-features=kMacSystemNotificationPermissionInfoUi",  # 禁用macOS系统通知权限UI
                # 窗口焦点和激活控制
                "--disable-focus-manager",  # 禁用焦点管理器
                "--disable-window-activation",  # 禁用窗口激活
                "--disable-auto-reload",  # 禁用自动重载
                "--disable-session-crashed-bubble",  # 禁用会话崩溃气泡
                "--disable-infobars",  # 禁用信息栏
                "--disable-save-password-bubble",  # 禁用保存密码气泡
                "--disable-translate-new-ux",  # 禁用翻译新UX
                "--disable-features=TabHoverCards",  # 禁用标签悬停卡片
                "--disable-features=TabGroups",  # 禁用标签组
                "--disable-features=GlobalMediaControls",  # 禁用全局媒体控制
                # 彻底隐藏和最小化窗口
                "--start-minimized",  # 启动时最小化
                "--silent-launch",  # 静默启动
                "--disable-logging",  # 禁用日志记录
                "--log-level=3",  # 设置最高日志级别（只显示致命错误）
                "about:blank"
            ]

            # 添加扩展参数
            if extension_args:
                browser_args.extend(extension_args)
                print(f"🔌 启用自定义扩展支持")

            # 添加headless参数
            if self.headless:
                browser_args.append("--headless=new")
                print(f"👻 启用无头模式运行")
            else:
                print(f"🖥️ 启用有头模式运行")

            # 不禁用扩展系统，以确保用户插件正常工作
            print(f"🔌 保持扩展系统启用，确保您的插件正常工作")

            print(f"📁 使用用户数据目录: {debug_user_data_dir}")
            print(f"💡 这将启动一个带调试端口的{browser_name}实例，保持您的插件和设置")

            # 在后台启动浏览器
            process = subprocess.Popen(
                browser_args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )

            # 等待浏览器启动
            print(f"⏳ 等待{browser_name}启动...")
            for i in range(15):  # 增加等待时间到15秒，因为加载插件需要更多时间
                time.sleep(1)
                if self.check_debug_port(debug_port):
                    print(f"✅ {browser_name}成功启动，远程调试端口{debug_port}可用")
                    print(f"🔌 您的插件和设置应该已经加载完成")
                    return True
                print(f"⏳ 等待中... ({i + 1}/15)")

            print(f"❌ {browser_name}启动超时，端口{debug_port}不可用")
            return False

        except Exception as e:
            browser_name = self._get_browser_name(browser_type)
            print(f"❌ 启动{browser_name}失败: {e}")
            return False

    async def init_browser(self) -> bool:
        """
        初始化浏览器连接（支持Edge和Chrome自动检测）

        Returns:
            bool: 初始化是否成功
        """
        try:
            print("🔧 初始化浏览器连接...")

            # 自动检测可用浏览器
            executable_path, user_data_dir, detected_browser_type = self.get_browser_paths()

            if not executable_path:
                print("❌ 未找到可用的浏览器")
                return False

            # 更新当前使用的浏览器信息
            self.browser_type = detected_browser_type
            self.current_browser_executable = executable_path
            self.current_user_data_dir = user_data_dir

            browser_name = "Edge" if detected_browser_type == BrowserType.EDGE else "Chrome"
            print(f"✅ {browser_name}可执行文件: {executable_path}")

            # 确保浏览器调试实例在运行
            if not self.launch_browser_with_debug_port(executable_path, user_data_dir, self.debug_port,
                                                       detected_browser_type):
                return False

            # 连接到浏览器实例
            if not async_playwright:
                print("❌ Playwright未安装，无法连接到浏览器")
                return False

            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.connect_over_cdp(f"http://localhost:{self.debug_port}")

            browser_name = "Edge" if detected_browser_type == BrowserType.EDGE else "Chrome"
            print(f"✅ 成功连接到{browser_name}实例!")

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

            # 保存Playwright的原始事件循环
            self._pw_loop = asyncio.get_running_loop()
            print("✅ 已保存Playwright原始事件循环")

            # 绑定上下文事件，自动更新页面引用
            self._bind_context_events()
            print("✅ 已绑定上下文事件监听")

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

    def attach_page(self, page: Page):
        """
        主动绑定当前使用的页面

        Args:
            page: 要绑定的页面对象
        """
        self.page = page
        try:
            # 保持引用活跃，并监听弹窗事件
            page.on("domcontentloaded", lambda _: None)
            page.on("popup", lambda new_page: self.attach_page(new_page))
            print(f"✅ 已绑定页面: {page.url if hasattr(page, 'url') else 'unknown'}")
        except Exception as e:
            print(f"⚠️ 绑定页面事件时出现警告: {e}")

    def _bind_context_events(self):
        """
        绑定所有上下文的页面事件，自动更新页面引用
        """
        if not self.browser:
            return

        try:
            for ctx in self.browser.contexts:
                try:
                    # 当有新页面创建时，自动更新引用
                    ctx.on("page", lambda p: self._on_new_page(p))
                    print(f"✅ 已绑定上下文事件监听")
                except Exception as e:
                    print(f"⚠️ 绑定上下文事件时出现警告: {e}")
        except Exception as e:
            print(f"⚠️ 绑定上下文事件失败: {e}")

    def _on_new_page(self, page: Page):
        """
        新页面创建时的回调函数

        Args:
            page: 新创建的页面
        """
        try:
            print(f"🆕 检测到新页面: {page.url if hasattr(page, 'url') else 'about:blank'}")
            self.attach_page(page)
        except Exception as e:
            print(f"⚠️ 处理新页面时出现警告: {e}")

    def _pick_active_page(self) -> Optional[Page]:
        """
        选择最可能是活动页面的引用，确保页面未被关闭

        Returns:
            Optional[Page]: 最活跃的页面，如果没有则返回None
        """
        def is_page_valid(page) -> bool:
            """检查页面是否有效且未被关闭"""
            try:
                if not page:
                    return False
                # 尝试访问页面属性来检查是否已关闭
                _ = page.url
                return True
            except Exception:
                return False

        try:
            # 首先检查当前页面是否有效且不是空白页
            if (self.page and
                is_page_valid(self.page) and
                hasattr(self.page, "url") and
                self.page.url and
                self.page.url != "about:blank"):
                print(f"📄 使用当前页面: {self.page.url}")
                return self.page

            # 从所有上下文里挑最后一个非空白且有效的页面
            if self.browser:
                for ctx in reversed(self.browser.contexts):
                    try:
                        pages = ctx.pages
                        for p in reversed(pages):
                            try:
                                if (is_page_valid(p) and
                                    p.url and
                                    p.url != "about:blank"):
                                    print(f"📄 选择活跃页面: {p.url}")
                                    # 更新当前页面引用
                                    self.page = p
                                    return p
                            except Exception:
                                continue
                    except Exception:
                        continue

            # 如果所有页面都无效，尝试创建新页面
            if self.browser and self.browser.contexts:
                try:
                    ctx = self.browser.contexts[0]
                    if ctx:
                        print("📄 所有页面已关闭，尝试创建新页面")
                        # 注意：这里不能直接创建页面，因为我们在同步方法中
                        # 只能返回None，让调用方处理
                        return None
                except Exception as e:
                    print(f"⚠️ 尝试创建新页面失败: {e}")

            # 兜底返回None，表示没有可用页面
            print(f"📄 没有可用的页面")
            return None

        except Exception as e:
            print(f"⚠️ 选择活跃页面时出现警告: {e}")
            return None

    async def _run_on_pw_loop(self, coro):
        """
        在Playwright的原始事件循环中执行协程

        Args:
            coro: 要执行的协程

        Returns:
            协程的执行结果
        """
        # 如果当前没有运行的 loop（同步环境）或 loop 不同，就投递
        try:
            current = asyncio.get_running_loop()
        except RuntimeError:
            current = None

        if self._pw_loop is None:
            raise RuntimeError("Playwright loop not initialized")

        if current is self._pw_loop:
            return await coro

        # 投递到原始 Playwright loop
        cfut = asyncio.run_coroutine_threadsafe(coro, self._pw_loop)
        return await asyncio.wrap_future(cfut)

    async def take_screenshot(self, full_page: bool = False) -> Optional[bytes]:
        """
        截取当前页面的截图 - 正确处理事件循环

        Args:
            full_page: 是否截取整个页面，默认为False（仅可视区域）

        Returns:
            Optional[bytes]: 截图的字节数据，失败时返回None
        """
        try:
            if not self.page:
                print("❌ 页面未初始化，无法截图")
                return None

            print("📷 正在截取页面截图...")
            screenshot_bytes = await self._run_on_pw_loop(
                self.page.screenshot(full_page=full_page, type='png')
            )
            print("✅ 截图成功")
            return screenshot_bytes

        except Exception as e:
            print(f"❌ 截图失败: {str(e)}")
            return None

    def take_screenshot_sync(self, full_page: bool = False) -> Optional[bytes]:
        """
        同步方式截取当前页面的截图 - 用于非async环境/别的线程
        使用智能页面选择，确保截图总是对当前活动页

        Args:
            full_page: 是否截取整个页面，默认为False（仅可视区域）

        Returns:
            Optional[bytes]: 截图的字节数据，失败时返回None
        """
        if not self._pw_loop or not self.browser:
            print("❌ 截图失败：浏览器未初始化或事件循环未设置")
            return None

        # 刷新引用，选择最活跃的页面
        target = self._pick_active_page()
        if not target:
            print("❌ 没有可用页面进行截图 - 所有页面可能已被关闭")
            return None

        try:
            cfut = asyncio.run_coroutine_threadsafe(
                target.screenshot(full_page=full_page, type='png'),
                self._pw_loop
            )
            result = cfut.result(timeout=10)
            if result:
                print("✅ 截图成功")
            return result
        except Exception as e:
            # 如果是页面已关闭的错误，尝试重新选择页面
            if "closed" in str(e).lower() or "target" in str(e).lower():
                print(f"⚠️ 页面已关闭，尝试重新选择页面: {e}")
                # 清除当前页面引用，强制重新选择
                self.page = None
                target = self._pick_active_page()
                if target:
                    try:
                        cfut = asyncio.run_coroutine_threadsafe(
                            target.screenshot(full_page=full_page, type='png'),
                            self._pw_loop
                        )
                        result = cfut.result(timeout=10)
                        if result:
                            print("✅ 重新截图成功")
                        return result
                    except Exception as retry_e:
                        print(f"❌ 重试截图失败: {retry_e}")
                        return None
                else:
                    print("❌ 重新选择页面失败，没有可用页面")
                    return None
            else:
                print(f"❌ 截图失败: {e}")
                return None
