"""
依赖检测和安装模块

提供跨平台的依赖检测和自动安装功能。
"""

import subprocess
import sys
import os
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass


@dataclass
class DependencyStatus:
    """依赖状态"""
    name: str
    required_version: Optional[str]
    installed_version: Optional[str]
    is_installed: bool
    needs_update: bool = False


class DependencyChecker:
    """依赖检测器"""

    # 最低 Python 版本要求
    MIN_PYTHON_VERSION = (3, 8)

    # 核心依赖（必须安装）
    CORE_DEPENDENCIES = [
        'playwright',
        'openpyxl',
        'requests',
        'Pillow',
    ]

    def __init__(self, project_root: Optional[Path] = None):
        """
        初始化依赖检测器

        Args:
            project_root: 项目根目录，默认为当前脚本所在目录的父目录
        """
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.absolute()
        else:
            self.project_root = Path(project_root)

        self.requirements_file = self.project_root / 'requirements.txt'
        self._installed_packages: Optional[Dict[str, str]] = None

    def check_python_version(self) -> Tuple[bool, str]:
        """
        检测 Python 版本

        Returns:
            (是否满足要求, 消息)
        """
        current = sys.version_info[:2]
        required = self.MIN_PYTHON_VERSION

        if current >= required:
            return True, f"Python {current[0]}.{current[1]} ✓"
        else:
            return False, (
                f"Python 版本不满足要求\n"
                f"  当前版本: {current[0]}.{current[1]}\n"
                f"  需要版本: {required[0]}.{required[1]}+\n"
                f"  请升级 Python 后重试"
            )

    def check_pip_available(self) -> Tuple[bool, str]:
        """
        检测 pip 是否可用

        Returns:
            (是否可用, 消息)
        """
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                version_match = re.search(r'pip (\d+\.\d+)', result.stdout)
                version = version_match.group(1) if version_match else 'unknown'
                return True, f"pip {version} ✓"
            else:
                return False, "pip 不可用，请安装 pip"
        except subprocess.TimeoutExpired:
            return False, "pip 检测超时"
        except Exception as e:
            return False, f"pip 检测失败: {e}"

    def parse_requirements(self) -> List[Tuple[str, Optional[str]]]:
        """
        解析 requirements.txt

        Returns:
            [(包名, 版本要求), ...] 列表
        """
        requirements = []

        if not self.requirements_file.exists():
            return requirements

        with open(self.requirements_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue

                # 解析包名和版本
                # 支持格式: package, package>=1.0.0, package==1.0.0, package[extra]>=1.0
                match = re.match(r'^([a-zA-Z0-9_-]+)(?:\[[^\]]+\])?(?:([><=!]+)(.+))?$', line)
                if match:
                    name = match.group(1)
                    version_spec = match.group(3) if match.group(2) else None
                    requirements.append((name, version_spec))

        return requirements

    def _get_installed_packages(self) -> Dict[str, str]:
        """获取已安装的包列表（带缓存）"""
        if self._installed_packages is not None:
            return self._installed_packages

        self._installed_packages = {}
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list', '--format=freeze'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if '==' in line:
                        name, version = line.split('==', 1)
                        # 规范化包名（转小写，替换下划线为连字符）
                        self._installed_packages[name.lower().replace('_', '-')] = version
        except Exception:
            pass

        return self._installed_packages

    def check_dependencies(self) -> List[DependencyStatus]:
        """
        检测依赖安装状态

        Returns:
            依赖状态列表
        """
        requirements = self.parse_requirements()
        installed = self._get_installed_packages()
        statuses = []

        for name, version_spec in requirements:
            # 规范化包名
            normalized_name = name.lower().replace('_', '-')
            installed_version = installed.get(normalized_name)

            status = DependencyStatus(
                name=name,
                required_version=version_spec,
                installed_version=installed_version,
                is_installed=installed_version is not None
            )
            statuses.append(status)

        return statuses

    def get_missing_dependencies(self) -> List[str]:
        """
        获取缺失的依赖列表

        Returns:
            缺失的包名列表
        """
        statuses = self.check_dependencies()
        return [s.name for s in statuses if not s.is_installed]

    def install_dependencies(self, packages: Optional[List[str]] = None,
                            use_user: bool = True) -> Tuple[bool, str]:
        """
        安装依赖

        Args:
            packages: 要安装的包列表，None 表示安装所有缺失的依赖
            use_user: 是否使用 --user 标志（非虚拟环境时）

        Returns:
            (是否成功, 消息)
        """
        if packages is None:
            packages = self.get_missing_dependencies()

        if not packages:
            return True, "所有依赖已安装 ✓"

        # 检测是否在虚拟环境中
        in_venv = (
            hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
        )

        # 构建安装命令
        cmd = [sys.executable, '-m', 'pip', 'install']

        if not in_venv and use_user:
            cmd.append('--user')

        cmd.extend(packages)

        try:
            print(f"正在安装依赖: {', '.join(packages)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )

            if result.returncode == 0:
                # 清除缓存
                self._installed_packages = None
                return True, f"依赖安装成功 ✓\n  已安装: {', '.join(packages)}"
            else:
                error_msg = result.stderr or result.stdout
                return False, f"依赖安装失败:\n{error_msg}"

        except subprocess.TimeoutExpired:
            return False, "依赖安装超时（超过5分钟）"
        except Exception as e:
            return False, f"依赖安装失败: {e}"

    def check_system_browser(self) -> Tuple[bool, str]:
        """
        检测系统是否安装了 Chrome 或 Edge 浏览器

        Returns:
            (是否已安装, 消息)
        """
        import platform
        import shutil

        system = platform.system()
        found_browsers = []

        if system == 'Windows':
            # Windows 浏览器路径
            chrome_paths = [
                Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / 'Google/Chrome/Application/chrome.exe',
                Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')) / 'Google/Chrome/Application/chrome.exe',
                Path.home() / 'AppData/Local/Google/Chrome/Application/chrome.exe',
            ]
            edge_paths = [
                Path(os.environ.get('PROGRAMFILES', 'C:/Program Files')) / 'Microsoft/Edge/Application/msedge.exe',
                Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')) / 'Microsoft/Edge/Application/msedge.exe',
            ]

            for path in chrome_paths:
                if path.exists():
                    found_browsers.append('Chrome')
                    break

            for path in edge_paths:
                if path.exists():
                    found_browsers.append('Edge')
                    break

        elif system == 'Darwin':  # macOS
            chrome_path = Path('/Applications/Google Chrome.app')
            edge_path = Path('/Applications/Microsoft Edge.app')

            if chrome_path.exists():
                found_browsers.append('Chrome')
            if edge_path.exists():
                found_browsers.append('Edge')

        else:  # Linux
            # 使用 which 命令检测
            if shutil.which('google-chrome') or shutil.which('google-chrome-stable'):
                found_browsers.append('Chrome')
            if shutil.which('microsoft-edge') or shutil.which('microsoft-edge-stable'):
                found_browsers.append('Edge')

        if found_browsers:
            return True, f"系统浏览器: {', '.join(found_browsers)} ✓"
        else:
            return False, (
                "未检测到 Chrome 或 Edge 浏览器\n"
                "  请安装以下浏览器之一:\n"
                "  - Google Chrome: https://www.google.com/chrome/\n"
                "  - Microsoft Edge: https://www.microsoft.com/edge/"
            )

    def check_playwright_browser(self) -> Tuple[bool, str]:
        """
        检测 Playwright 浏览器驱动

        Returns:
            (是否已安装, 消息)
        """
        try:
            # 检查 playwright 是否可导入
            import importlib.util
            spec = importlib.util.find_spec('playwright')
            if spec is None:
                return False, "Playwright 未安装"

            # 检查浏览器驱动目录
            # Playwright 浏览器通常安装在 ~/.cache/ms-playwright/
            import platform
            system = platform.system()

            if system == 'Windows':
                browser_path = Path.home() / 'AppData' / 'Local' / 'ms-playwright'
            else:
                browser_path = Path.home() / '.cache' / 'ms-playwright'

            if browser_path.exists() and any(browser_path.iterdir()):
                return True, "Playwright 浏览器驱动已安装 ✓"
            else:
                return False, "Playwright 浏览器驱动未安装"

        except Exception as e:
            return False, f"检测 Playwright 浏览器失败: {e}"

    def install_playwright_browser(self, browser: str = 'chromium') -> Tuple[bool, str]:
        """
        安装 Playwright 浏览器驱动

        Args:
            browser: 浏览器类型 (chromium, firefox, webkit)

        Returns:
            (是否成功, 消息)
        """
        try:
            print(f"正在安装 Playwright {browser} 浏览器驱动...")
            result = subprocess.run(
                [sys.executable, '-m', 'playwright', 'install', browser],
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时（浏览器下载可能较慢）
            )

            if result.returncode == 0:
                return True, f"Playwright {browser} 浏览器驱动安装成功 ✓"
            else:
                error_msg = result.stderr or result.stdout
                return False, f"Playwright 浏览器驱动安装失败:\n{error_msg}"

        except subprocess.TimeoutExpired:
            return False, "Playwright 浏览器驱动安装超时（超过10分钟）"
        except Exception as e:
            return False, f"Playwright 浏览器驱动安装失败: {e}"

    def run_full_check(self, auto_install: bool = True,
                       verbose: bool = True) -> Tuple[bool, List[str]]:
        """
        运行完整的依赖检测

        Args:
            auto_install: 是否自动安装缺失的依赖
            verbose: 是否输出详细信息

        Returns:
            (是否全部通过, 消息列表)
        """
        messages = []
        all_passed = True

        # 1. 检查 Python 版本
        ok, msg = self.check_python_version()
        if verbose:
            print(f"[1/5] 检测 Python 版本... {msg}")
        if not ok:
            messages.append(msg)
            return False, messages

        # 2. 检查 pip
        ok, msg = self.check_pip_available()
        if verbose:
            print(f"[2/5] 检测 pip... {msg}")
        if not ok:
            messages.append(msg)
            return False, messages

        # 3. 检查系统浏览器 (Chrome 或 Edge)
        ok, msg = self.check_system_browser()
        if verbose:
            print(f"[3/5] 检测系统浏览器... {msg}")
        if not ok:
            messages.append(msg)
            # 浏览器缺失是严重问题，直接返回
            return False, messages

        # 4. 检查依赖
        missing = self.get_missing_dependencies()
        if missing:
            if verbose:
                print(f"[4/5] 检测依赖... 缺失 {len(missing)} 个包")
            if auto_install:
                ok, msg = self.install_dependencies(missing)
                if verbose:
                    print(f"      {msg}")
                if not ok:
                    messages.append(msg)
                    all_passed = False
            else:
                messages.append(f"缺失依赖: {', '.join(missing)}")
                all_passed = False
        else:
            if verbose:
                print("[4/5] 检测依赖... 所有依赖已安装 ✓")

        # 5. 检查 Playwright 浏览器
        ok, msg = self.check_playwright_browser()
        if not ok:
            if verbose:
                print(f"[5/5] 检测 Playwright 浏览器... {msg}")
            if auto_install:
                ok, msg = self.install_playwright_browser()
                if verbose:
                    print(f"      {msg}")
                if not ok:
                    messages.append(msg)
                    all_passed = False
            else:
                messages.append(msg)
                all_passed = False
        else:
            if verbose:
                print(f"[5/5] 检测 Playwright 浏览器... {msg}")

        return all_passed, messages


def check_and_install_dependencies(auto_install: bool = True,
                                   verbose: bool = True) -> bool:
    """
    便捷函数：检测并安装依赖

    Args:
        auto_install: 是否自动安装
        verbose: 是否输出详细信息

    Returns:
        是否全部通过
    """
    # 检查是否跳过依赖检查
    if os.environ.get('XP_SKIP_DEP_CHECK', '').lower() in ('1', 'true', 'yes'):
        if verbose:
            print("跳过依赖检查 (XP_SKIP_DEP_CHECK=1)")
        return True

    checker = DependencyChecker()
    ok, messages = checker.run_full_check(auto_install=auto_install, verbose=verbose)

    if not ok and messages:
        print("\n⚠️ 依赖检测发现问题:")
        for msg in messages:
            print(f"  - {msg}")
        print("\n提示: 设置环境变量 XP_SKIP_DEP_CHECK=1 可跳过依赖检查")

    return ok


if __name__ == '__main__':
    # 独立运行时执行检测
    import argparse

    parser = argparse.ArgumentParser(description='依赖检测工具')
    parser.add_argument('--no-install', action='store_true',
                        help='只检测不安装')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='静默模式')
    args = parser.parse_args()

    success = check_and_install_dependencies(
        auto_install=not args.no_install,
        verbose=not args.quiet
    )

    sys.exit(0 if success else 1)
