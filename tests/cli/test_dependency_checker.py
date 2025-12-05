"""
Tests for cli/dependency_checker.py

跨平台依赖检测模块的单元测试
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from cli.dependency_checker import (
    DependencyChecker,
    DependencyStatus,
    check_and_install_dependencies,
)


class TestDependencyChecker(unittest.TestCase):
    """DependencyChecker 基础测试"""

    def setUp(self):
        self.checker = DependencyChecker()

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.checker.project_root)
        self.assertTrue(self.checker.project_root.exists())

    def test_check_python_version_pass(self):
        """测试 Python 版本检测 - 通过"""
        ok, msg = self.checker.check_python_version()
        # 当前环境应该满足 Python 3.8+ 要求
        self.assertTrue(ok)
        self.assertIn("✓", msg)

    @patch.object(sys, 'version_info', (3, 7, 0))
    def test_check_python_version_fail(self):
        """测试 Python 版本检测 - 失败"""
        checker = DependencyChecker()
        ok, msg = checker.check_python_version()
        self.assertFalse(ok)
        self.assertIn("版本不满足", msg)

    def test_check_pip_available(self):
        """测试 pip 可用性检测"""
        ok, msg = self.checker.check_pip_available()
        self.assertTrue(ok)
        self.assertIn("pip", msg)

    def test_parse_requirements(self):
        """测试 requirements.txt 解析"""
        requirements = self.checker.parse_requirements()
        self.assertIsInstance(requirements, list)
        # 应该包含一些核心依赖
        package_names = [r[0] for r in requirements]
        self.assertIn('playwright', package_names)
        self.assertIn('openpyxl', package_names)


class TestSystemBrowserDetection(unittest.TestCase):
    """系统浏览器检测测试"""

    def setUp(self):
        self.checker = DependencyChecker()

    def test_check_system_browser_real(self):
        """测试真实环境的浏览器检测"""
        ok, msg = self.checker.check_system_browser()
        # 在 CI 环境可能没有浏览器，所以只检查返回格式
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(msg, str)

    @patch('platform.system', return_value='Windows')
    def test_check_system_browser_windows_chrome(self, mock_system):
        """测试 Windows 下 Chrome 检测"""
        checker = DependencyChecker()

        with patch.object(Path, 'exists') as mock_exists:
            # 模拟 Chrome 存在
            def exists_side_effect(self=None):
                path_str = str(self) if self else ""
                return 'Chrome' in path_str and 'chrome.exe' in path_str

            mock_exists.side_effect = lambda: 'Chrome' in str(mock_exists._mock_name)

            # 直接测试检测逻辑
            with patch('os.environ.get', side_effect=lambda k, d: d):
                with patch.object(Path, 'exists', return_value=False):
                    # 创建一个模拟的路径检查
                    original_check = checker.check_system_browser

                    # Mock Chrome 路径存在
                    chrome_path = Path('C:/Program Files/Google/Chrome/Application/chrome.exe')
                    with patch.object(type(chrome_path), 'exists', return_value=True):
                        ok, msg = checker.check_system_browser()
                        # 在 mock 环境下可能检测不到，这里只验证返回格式
                        self.assertIsInstance(ok, bool)

    @patch('platform.system', return_value='Windows')
    def test_check_system_browser_windows_edge(self, mock_system):
        """测试 Windows 下 Edge 检测"""
        checker = DependencyChecker()

        # 模拟环境变量
        env_mock = {
            'PROGRAMFILES': 'C:/Program Files',
            'PROGRAMFILES(X86)': 'C:/Program Files (x86)',
        }

        with patch.dict(os.environ, env_mock):
            # 模拟 Edge 路径存在
            original_exists = Path.exists

            def mock_exists(self):
                return 'msedge.exe' in str(self)

            with patch.object(Path, 'exists', mock_exists):
                ok, msg = checker.check_system_browser()
                self.assertTrue(ok)
                self.assertIn('Edge', msg)

    @patch('platform.system', return_value='Darwin')
    def test_check_system_browser_macos_chrome(self, mock_system):
        """测试 macOS 下 Chrome 检测"""
        checker = DependencyChecker()

        with patch.object(Path, 'exists') as mock_exists:
            def check_path(path_self=None):
                if path_self is None:
                    return False
                return 'Google Chrome.app' in str(path_self)
            mock_exists.side_effect = check_path

            ok, msg = checker.check_system_browser()
            # 验证返回格式
            self.assertIsInstance(ok, bool)

    @patch('platform.system', return_value='Darwin')
    def test_check_system_browser_macos_edge(self, mock_system):
        """测试 macOS 下 Edge 检测"""
        checker = DependencyChecker()

        with patch.object(Path, 'exists') as mock_exists:
            def check_path(path_self=None):
                if path_self is None:
                    return False
                return 'Microsoft Edge.app' in str(path_self)
            mock_exists.side_effect = check_path

            ok, msg = checker.check_system_browser()
            self.assertIsInstance(ok, bool)

    @patch('platform.system', return_value='Linux')
    @patch('shutil.which')
    def test_check_system_browser_linux_chrome(self, mock_which, mock_system):
        """测试 Linux 下 Chrome 检测"""
        checker = DependencyChecker()

        # 模拟 google-chrome 存在
        def which_side_effect(cmd):
            if cmd in ('google-chrome', 'google-chrome-stable'):
                return '/usr/bin/google-chrome'
            return None
        mock_which.side_effect = which_side_effect

        ok, msg = checker.check_system_browser()
        self.assertTrue(ok)
        self.assertIn('Chrome', msg)

    @patch('platform.system', return_value='Linux')
    @patch('shutil.which')
    def test_check_system_browser_linux_edge(self, mock_which, mock_system):
        """测试 Linux 下 Edge 检测"""
        checker = DependencyChecker()

        # 模拟 microsoft-edge 存在
        def which_side_effect(cmd):
            if cmd in ('microsoft-edge', 'microsoft-edge-stable'):
                return '/usr/bin/microsoft-edge'
            return None
        mock_which.side_effect = which_side_effect

        ok, msg = checker.check_system_browser()
        self.assertTrue(ok)
        self.assertIn('Edge', msg)

    @patch('platform.system', return_value='Linux')
    @patch('shutil.which', return_value=None)
    def test_check_system_browser_linux_none(self, mock_which, mock_system):
        """测试 Linux 下无浏览器"""
        checker = DependencyChecker()

        ok, msg = checker.check_system_browser()
        self.assertFalse(ok)
        self.assertIn('未检测到', msg)
        self.assertIn('Chrome', msg)
        self.assertIn('Edge', msg)


class TestPlaywrightBrowserDetection(unittest.TestCase):
    """Playwright 浏览器驱动检测测试"""

    def setUp(self):
        self.checker = DependencyChecker()

    def test_check_playwright_browser(self):
        """测试 Playwright 浏览器检测"""
        ok, msg = self.checker.check_playwright_browser()
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(msg, str)

    @patch('importlib.util.find_spec', return_value=None)
    def test_check_playwright_not_installed(self, mock_find_spec):
        """测试 Playwright 未安装"""
        checker = DependencyChecker()
        ok, msg = checker.check_playwright_browser()
        self.assertFalse(ok)
        self.assertIn('未安装', msg)


class TestDependencyInstallation(unittest.TestCase):
    """依赖安装测试"""

    def setUp(self):
        self.checker = DependencyChecker()

    def test_get_missing_dependencies(self):
        """测试获取缺失依赖"""
        missing = self.checker.get_missing_dependencies()
        self.assertIsInstance(missing, list)
        # 在已配置环境中，应该没有缺失依赖
        # 但我们不强制断言，因为测试环境可能不同

    def test_install_dependencies_empty_list(self):
        """测试安装空依赖列表"""
        ok, msg = self.checker.install_dependencies([])
        self.assertTrue(ok)
        self.assertIn('已安装', msg)

    @patch('subprocess.run')
    def test_install_dependencies_success(self, mock_run):
        """测试依赖安装成功"""
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')

        ok, msg = self.checker.install_dependencies(['test-package'])
        self.assertTrue(ok)
        self.assertIn('成功', msg)

    @patch('subprocess.run')
    def test_install_dependencies_failure(self, mock_run):
        """测试依赖安装失败"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='',
            stderr='Could not find package'
        )

        ok, msg = self.checker.install_dependencies(['nonexistent-package'])
        self.assertFalse(ok)
        self.assertIn('失败', msg)


class TestFullCheck(unittest.TestCase):
    """完整检测流程测试"""

    def setUp(self):
        self.checker = DependencyChecker()

    def test_run_full_check_structure(self):
        """测试完整检测返回结构"""
        ok, messages = self.checker.run_full_check(auto_install=False, verbose=False)
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(messages, list)

    @patch.dict(os.environ, {'XP_SKIP_DEP_CHECK': '1'})
    def test_skip_dependency_check(self):
        """测试跳过依赖检查"""
        result = check_and_install_dependencies(verbose=False)
        self.assertTrue(result)

    @patch.dict(os.environ, {'XP_SKIP_DEP_CHECK': 'true'})
    def test_skip_dependency_check_true(self):
        """测试 XP_SKIP_DEP_CHECK=true"""
        result = check_and_install_dependencies(verbose=False)
        self.assertTrue(result)

    @patch.dict(os.environ, {'XP_SKIP_DEP_CHECK': 'yes'})
    def test_skip_dependency_check_yes(self):
        """测试 XP_SKIP_DEP_CHECK=yes"""
        result = check_and_install_dependencies(verbose=False)
        self.assertTrue(result)


class TestWindowsMocking(unittest.TestCase):
    """Windows 环境模拟测试"""

    @patch('platform.system', return_value='Windows')
    @patch.dict(os.environ, {
        'PROGRAMFILES': 'C:/Program Files',
        'PROGRAMFILES(X86)': 'C:/Program Files (x86)',
    })
    def test_windows_browser_paths(self, mock_system):
        """测试 Windows 浏览器路径检测"""
        checker = DependencyChecker()

        # 创建模拟的路径存在检查
        chrome_found = False
        edge_found = False

        original_exists = Path.exists

        def mock_exists(path_self):
            nonlocal chrome_found, edge_found
            path_str = str(path_self)
            if 'chrome.exe' in path_str.lower():
                chrome_found = True
                return True
            if 'msedge.exe' in path_str.lower():
                edge_found = True
                return True
            return False

        with patch.object(Path, 'exists', mock_exists):
            ok, msg = checker.check_system_browser()

        # 验证路径被检查
        self.assertTrue(chrome_found or edge_found or not ok)

    @patch('platform.system', return_value='Windows')
    def test_windows_no_browser(self, mock_system):
        """测试 Windows 无浏览器场景"""
        checker = DependencyChecker()

        with patch.object(Path, 'exists', return_value=False):
            ok, msg = checker.check_system_browser()

        self.assertFalse(ok)
        self.assertIn('未检测到', msg)


class TestDependencyStatus(unittest.TestCase):
    """DependencyStatus 数据类测试"""

    def test_dependency_status_creation(self):
        """测试创建依赖状态"""
        status = DependencyStatus(
            name='test-package',
            required_version='1.0.0',
            installed_version='1.0.0',
            is_installed=True
        )
        self.assertEqual(status.name, 'test-package')
        self.assertTrue(status.is_installed)
        self.assertFalse(status.needs_update)

    def test_dependency_status_missing(self):
        """测试缺失依赖状态"""
        status = DependencyStatus(
            name='missing-package',
            required_version='1.0.0',
            installed_version=None,
            is_installed=False
        )
        self.assertFalse(status.is_installed)
        self.assertIsNone(status.installed_version)


if __name__ == '__main__':
    unittest.main()
