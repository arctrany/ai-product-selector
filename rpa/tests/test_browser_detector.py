"""
BrowserDetector 完整测试套件

测试范围：
1. 跨平台兼容性测试 (macOS/Windows/Linux)
2. Profile 检测和管理
3. 浏览器进程检测和管理
4. 异常处理和边界条件
5. 便捷函数测试
"""

import pytest
import platform
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
import subprocess
import time

from rpa.browser.utils.browser_detector import (
    BrowserDetector,
    detect_active_profile,
    get_browser_info
)


class TestBrowserDetectorInit:
    """测试 BrowserDetector 初始化"""
    
    def test_init_sets_system_info(self):
        """测试场景：初始化时正确设置系统信息"""
        detector = BrowserDetector()
        
        assert hasattr(detector, 'logger')
        assert hasattr(detector, 'system')
        assert detector.system == platform.system()


class TestBrowserDetectorUserDataDir:
    """测试用户数据目录获取"""
    
    def test_get_edge_user_data_dir_macos(self):
        """测试场景：macOS 上获取 Edge 用户数据目录"""
        detector = BrowserDetector()
        
        with patch('platform.system', return_value='Darwin'):
            detector.system = 'Darwin'
            result = detector._get_edge_user_data_dir()
        
        expected = os.path.expanduser("~/Library/Application Support/Microsoft Edge")
        assert result == expected
    
    def test_get_edge_user_data_dir_windows(self):
        """测试场景：Windows 上获取 Edge 用户数据目录"""
        detector = BrowserDetector()
        
        with patch('platform.system', return_value='Windows'):
            detector.system = 'Windows'
            result = detector._get_edge_user_data_dir()
        
        expected = os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data")
        assert result == expected
    
    def test_get_edge_user_data_dir_linux(self):
        """测试场景：Linux 上获取 Edge 用户数据目录"""
        detector = BrowserDetector()
        
        with patch('platform.system', return_value='Linux'):
            detector.system = 'Linux'
            result = detector._get_edge_user_data_dir()
        
        expected = os.path.expanduser("~/.config/microsoft-edge")
        assert result == expected
    
    def test_get_edge_user_data_dir_unsupported_system(self):
        """测试场景：不支持的操作系统返回 None"""
        detector = BrowserDetector()
        
        with patch('platform.system', return_value='FreeBSD'):
            detector.system = 'FreeBSD'
            result = detector._get_edge_user_data_dir()
        
        assert result is None


class TestBrowserDetectorProfileListing:
    """测试 Profile 列表功能"""
    
    def test_list_profiles_with_default_and_numbered(self):
        """测试场景：存在 Default 和编号 Profile"""
        detector = BrowserDetector()
        
        # 创建临时目录结构
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建 Profile 目录
            default_dir = os.path.join(temp_dir, "Default")
            profile1_dir = os.path.join(temp_dir, "Profile 1")
            profile2_dir = os.path.join(temp_dir, "Profile 2")
            
            os.makedirs(default_dir)
            os.makedirs(profile1_dir)
            os.makedirs(profile2_dir)
            
            # 设置不同的修改时间（模拟使用时间）
            os.utime(default_dir, (time.time() - 100, time.time() - 100))  # 最老
            os.utime(profile2_dir, (time.time() - 50, time.time() - 50))   # 中间
            os.utime(profile1_dir, (time.time() - 10, time.time() - 10))   # 最新
            
            profiles = detector._list_profiles(temp_dir)
            
            # 应该按最近使用时间排序
            assert profiles == ["Profile 1", "Profile 2", "Default"]
    
    def test_list_profiles_empty_directory(self):
        """测试场景：空的用户数据目录"""
        detector = BrowserDetector()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            profiles = detector._list_profiles(temp_dir)
            assert profiles == []
    
    def test_list_profiles_only_default(self):
        """测试场景：只有 Default Profile"""
        detector = BrowserDetector()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            default_dir = os.path.join(temp_dir, "Default")
            os.makedirs(default_dir)
            
            profiles = detector._list_profiles(temp_dir)
            assert profiles == ["Default"]
    
    def test_list_profiles_permission_error(self):
        """测试场景：目录访问权限错误"""
        detector = BrowserDetector()
        
        with patch('os.path.exists', side_effect=PermissionError("Access denied")):
            profiles = detector._list_profiles("/nonexistent")
            assert profiles == []


class TestBrowserDetectorProfileLocking:
    """测试 Profile 锁定检测"""
    
    def test_is_profile_locked_with_singleton_lock(self):
        """测试场景：存在 Singleton Lock 文件"""
        detector = BrowserDetector()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            lock_file = os.path.join(temp_dir, "Singleton Lock")
            Path(lock_file).touch()
            
            result = detector.is_profile_locked(temp_dir)
            assert result is True
    
    def test_is_profile_locked_with_lockfile(self):
        """测试场景：存在 lockfile 文件"""
        detector = BrowserDetector()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            lock_file = os.path.join(temp_dir, "lockfile")
            Path(lock_file).touch()
            
            result = detector.is_profile_locked(temp_dir)
            assert result is True
    
    def test_is_profile_locked_with_singleton_lock_windows(self):
        """测试场景：存在 SingletonLock 文件（Windows）"""
        detector = BrowserDetector()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            lock_file = os.path.join(temp_dir, "SingletonLock")
            Path(lock_file).touch()
            
            result = detector.is_profile_locked(temp_dir)
            assert result is True
    
    def test_is_profile_locked_no_lock_files(self):
        """测试场景：没有锁定文件"""
        detector = BrowserDetector()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = detector.is_profile_locked(temp_dir)
            assert result is False
    
    def test_is_profile_locked_nonexistent_directory(self):
        """测试场景：Profile 目录不存在"""
        detector = BrowserDetector()
        
        result = detector.is_profile_locked("/nonexistent/profile")
        assert result is False
    
    def test_is_profile_locked_exception_handling(self):
        """测试场景：检查锁定状态时发生异常"""
        detector = BrowserDetector()
        
        with patch('os.path.exists', side_effect=PermissionError("Access denied")):
            result = detector.is_profile_locked("/some/path")
            assert result is False  # 出错时假设未锁定


class TestBrowserDetectorProfileAvailability:
    """测试 Profile 可用性检查"""
    
    def test_is_profile_available_success(self):
        """测试场景：Profile 存在且可用"""
        detector = BrowserDetector()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_dir = os.path.join(temp_dir, "Default")
            os.makedirs(profile_dir)
            
            with patch.object(detector, 'is_profile_locked', return_value=False):
                result = detector.is_profile_available(temp_dir, "Default")
                assert result is True
    
    def test_is_profile_available_nonexistent(self):
        """测试场景：Profile 不存在"""
        detector = BrowserDetector()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = detector.is_profile_available(temp_dir, "NonExistent")
            assert result is False
    
    def test_is_profile_available_locked(self):
        """测试场景：Profile 被锁定"""
        detector = BrowserDetector()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_dir = os.path.join(temp_dir, "Default")
            os.makedirs(profile_dir)
            
            with patch.object(detector, 'is_profile_locked', return_value=True):
                result = detector.is_profile_available(temp_dir, "Default")
                assert result is False
    
    @patch('os.access')
    def test_is_profile_available_no_permission(self, mock_access):
        """测试场景：Profile 无访问权限"""
        detector = BrowserDetector()
        mock_access.return_value = False
        
        with tempfile.TemporaryDirectory() as temp_dir:
            profile_dir = os.path.join(temp_dir, "Default")
            os.makedirs(profile_dir)
            
            result = detector.is_profile_available(temp_dir, "Default")
            assert result is False
    
    def test_is_profile_available_exception(self):
        """测试场景：检查可用性时发生异常"""
        detector = BrowserDetector()
        
        with patch('os.path.exists', side_effect=Exception("Unexpected error")):
            result = detector.is_profile_available("/some/path", "Default")
            assert result is False


class TestBrowserDetectorProcessDetection:
    """测试浏览器进程检测"""
    
    @patch('subprocess.run')
    def test_is_browser_running_macos_running(self, mock_run):
        """测试场景：macOS 上浏览器正在运行"""
        detector = BrowserDetector()
        detector.system = 'Darwin'
        
        mock_run.return_value = Mock(returncode=0)
        
        result = detector.is_browser_running()
        assert result is True
        mock_run.assert_called_with(
            ["pgrep", "-f", "Microsoft Edge"],
            capture_output=True,
            text=True
        )
    
    @patch('subprocess.run')
    def test_is_browser_running_macos_not_running(self, mock_run):
        """测试场景：macOS 上浏览器未运行"""
        detector = BrowserDetector()
        detector.system = 'Darwin'
        
        mock_run.return_value = Mock(returncode=1)
        
        result = detector.is_browser_running()
        assert result is False
    
    @patch('subprocess.run')
    def test_is_browser_running_windows_running(self, mock_run):
        """测试场景：Windows 上浏览器正在运行"""
        detector = BrowserDetector()
        detector.system = 'Windows'
        
        mock_run.return_value = Mock(stdout="msedge.exe running", returncode=0)
        
        result = detector.is_browser_running()
        assert result is True
        mock_run.assert_called_with(
            ["tasklist", "/FI", "IMAGENAME eq msedge.exe"],
            capture_output=True,
            text=True
        )
    
    @patch('subprocess.run')
    def test_is_browser_running_windows_not_running(self, mock_run):
        """测试场景：Windows 上浏览器未运行"""
        detector = BrowserDetector()
        detector.system = 'Windows'
        
        mock_run.return_value = Mock(stdout="No processes found", returncode=0)
        
        result = detector.is_browser_running()
        assert result is False
    
    @patch('subprocess.run')
    def test_is_browser_running_linux_running(self, mock_run):
        """测试场景：Linux 上浏览器正在运行"""
        detector = BrowserDetector()
        detector.system = 'Linux'
        
        mock_run.return_value = Mock(returncode=0)
        
        result = detector.is_browser_running()
        assert result is True
        mock_run.assert_called_with(
            ["pgrep", "-f", "microsoft-edge"],
            capture_output=True,
            text=True
        )
    
    @patch('subprocess.run')
    def test_is_browser_running_linux_not_running(self, mock_run):
        """测试场景：Linux 上浏览器未运行"""
        detector = BrowserDetector()
        detector.system = 'Linux'
        
        mock_run.return_value = Mock(returncode=1)
        
        result = detector.is_browser_running()
        assert result is False
    
    def test_is_browser_running_unsupported_system(self):
        """测试场景：不支持的操作系统"""
        detector = BrowserDetector()
        detector.system = 'FreeBSD'
        
        result = detector.is_browser_running()
        assert result is False
    
    @patch('subprocess.run')
    def test_is_browser_running_exception(self, mock_run):
        """测试场景：进程检测时发生异常"""
        detector = BrowserDetector()
        detector.system = 'Darwin'
        
        mock_run.side_effect = Exception("Command failed")
        
        result = detector.is_browser_running()
        assert result is False


class TestBrowserDetectorProcessKilling:
    """测试浏览器进程清理"""
    
    @patch('subprocess.run')
    @patch('time.sleep')
    def test_kill_browser_processes_macos_success(self, mock_sleep, mock_run):
        """测试场景：macOS 上成功清理浏览器进程"""
        detector = BrowserDetector()
        detector.system = 'Darwin'
        
        mock_run.return_value = Mock(returncode=0)
        
        result = detector.kill_browser_processes(force=True)
        assert result is True
        mock_run.assert_called_with(
            ["pkill", "-9", "-f", "Microsoft Edge"],
            capture_output=True,
            text=True
        )
        mock_sleep.assert_called_once_with(1)
    
    @patch('subprocess.run')
    @patch('time.sleep')
    def test_kill_browser_processes_macos_no_process(self, mock_sleep, mock_run):
        """测试场景：macOS 上没有进程需要清理"""
        detector = BrowserDetector()
        detector.system = 'Darwin'
        
        mock_run.return_value = Mock(returncode=1)  # 没有找到进程
        
        result = detector.kill_browser_processes(force=False)
        assert result is True
        mock_run.assert_called_with(
            ["pkill", "-15", "-f", "Microsoft Edge"],
            capture_output=True,
            text=True
        )
    
    @patch('subprocess.run')
    @patch('time.sleep')
    def test_kill_browser_processes_windows_success(self, mock_sleep, mock_run):
        """测试场景：Windows 上成功清理浏览器进程"""
        detector = BrowserDetector()
        detector.system = 'Windows'
        
        mock_run.return_value = Mock(returncode=0)
        
        result = detector.kill_browser_processes(force=True)
        assert result is True
        mock_run.assert_called_with(
            ["taskkill", "/F", "/IM", "msedge.exe", "/T"],
            capture_output=True,
            text=True
        )
    
    @patch('subprocess.run')
    @patch('time.sleep')
    def test_kill_browser_processes_windows_not_found(self, mock_sleep, mock_run):
        """测试场景：Windows 上进程不存在"""
        detector = BrowserDetector()
        detector.system = 'Windows'
        
        mock_run.return_value = Mock(returncode=1, stdout="Process not found")
        
        result = detector.kill_browser_processes(force=False)
        assert result is True
        mock_run.assert_called_with(
            ["taskkill", "", "/IM", "msedge.exe", "/T"],
            capture_output=True,
            text=True
        )
    
    @patch('subprocess.run')
    @patch('time.sleep')
    def test_kill_browser_processes_linux_success(self, mock_sleep, mock_run):
        """测试场景：Linux 上成功清理浏览器进程"""
        detector = BrowserDetector()
        detector.system = 'Linux'
        
        mock_run.return_value = Mock(returncode=0)
        
        result = detector.kill_browser_processes(force=True)
        assert result is True
        mock_run.assert_called_with(
            ["pkill", "-9", "-f", "microsoft-edge"],
            capture_output=True,
            text=True
        )
    
    def test_kill_browser_processes_unsupported_system(self):
        """测试场景：不支持的操作系统"""
        detector = BrowserDetector()
        detector.system = 'FreeBSD'
        
        result = detector.kill_browser_processes()
        assert result is False
    
    @patch('subprocess.run')
    def test_kill_browser_processes_exception(self, mock_run):
        """测试场景：清理进程时发生异常"""
        detector = BrowserDetector()
        detector.system = 'Darwin'
        
        mock_run.side_effect = Exception("Command failed")
        
        result = detector.kill_browser_processes()
        assert result is False


class TestBrowserDetectorWaitForUnlock:
    """测试等待 Profile 解锁"""
    
    @patch('time.sleep')
    def test_wait_for_profile_unlock_success(self, mock_sleep):
        """测试场景：Profile 成功解锁"""
        detector = BrowserDetector()
        
        # 模拟第一次检查时锁定，第二次检查时解锁
        with patch.object(detector, 'is_profile_locked', side_effect=[True, False]):
            result = detector.wait_for_profile_unlock("/fake/profile", max_wait_seconds=2)
            assert result is True
    
    @patch('time.sleep')
    def test_wait_for_profile_unlock_timeout(self, mock_sleep):
        """测试场景：等待超时，Profile 仍然锁定"""
        detector = BrowserDetector()
        
        # 模拟始终锁定
        with patch.object(detector, 'is_profile_locked', return_value=True):
            result = detector.wait_for_profile_unlock("/fake/profile", max_wait_seconds=1)
            assert result is False
    
    @patch('time.sleep')
    def test_wait_for_profile_unlock_immediate(self, mock_sleep):
        """测试场景：Profile 立即可用（未锁定）"""
        detector = BrowserDetector()
        
        with patch.object(detector, 'is_profile_locked', return_value=False):
            result = detector.wait_for_profile_unlock("/fake/profile", max_wait_seconds=5)
            assert result is True
            # 不应该有睡眠调用
            mock_sleep.assert_not_called()
    
    @patch('time.sleep')
    def test_wait_for_profile_unlock_exception(self, mock_sleep):
        """测试场景：等待过程中发生异常"""
        detector = BrowserDetector()
        
        with patch.object(detector, 'is_profile_locked', side_effect=Exception("Error")):
            result = detector.wait_for_profile_unlock("/fake/profile", max_wait_seconds=1)
            assert result is False


class TestBrowserDetectorActiveProfile:
    """测试活动 Profile 检测"""
    
    def test_detect_active_profile_success(self):
        """测试场景：成功检测到活动 Profile"""
        detector = BrowserDetector()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建 Profile 目录
            profile_dir = os.path.join(temp_dir, "Default")
            os.makedirs(profile_dir)
            
            with patch.object(detector, '_get_edge_user_data_dir', return_value=temp_dir):
                with patch.object(detector, '_list_profiles', return_value=["Default"]):
                    result = detector.detect_active_profile()
                    assert result == "Default"
    
    def test_detect_active_profile_no_user_data_dir(self):
        """测试场景：无法获取用户数据目录"""
        detector = BrowserDetector()
        
        with patch.object(detector, '_get_edge_user_data_dir', return_value=None):
            result = detector.detect_active_profile()
            assert result is None
    
    def test_detect_active_profile_user_data_dir_not_exists(self):
        """测试场景：用户数据目录不存在"""
        detector = BrowserDetector()
        
        with patch.object(detector, '_get_edge_user_data_dir', return_value="/nonexistent"):
            result = detector.detect_active_profile()
            assert result is None
    
    def test_detect_active_profile_no_profiles(self):
        """测试场景：没有找到任何 Profile"""
        detector = BrowserDetector()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(detector, '_get_edge_user_data_dir', return_value=temp_dir):
                with patch.object(detector, '_list_profiles', return_value=[]):
                    result = detector.detect_active_profile()
                    assert result is None
    
    def test_detect_active_profile_multiple_profiles(self):
        """测试场景：多个 Profile，返回最近使用的"""
        detector = BrowserDetector()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(detector, '_get_edge_user_data_dir', return_value=temp_dir):
                profiles = ["Profile 1", "Default", "Profile 2"]
                with patch.object(detector, '_list_profiles', return_value=profiles):
                    result = detector.detect_active_profile()
                    assert result == "Profile 1"  # 第一个是最近使用的
    
    def test_detect_active_profile_exception(self):
        """测试场景：检测过程中发生异常"""
        detector = BrowserDetector()
        
        with patch.object(detector, '_get_edge_user_data_dir', side_effect=Exception("Error")):
            result = detector.detect_active_profile()
            assert result is None


class TestBrowserDetectorBrowserInfo:
    """测试浏览器信息获取"""
    
    def test_get_browser_info_complete(self):
        """测试场景：获取完整的浏览器信息"""
        detector = BrowserDetector()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(detector, 'is_browser_running', return_value=True):
                with patch.object(detector, '_get_edge_user_data_dir', return_value=temp_dir):
                    with patch.object(detector, '_list_profiles', return_value=["Default", "Profile 1"]):
                        with patch.object(detector, 'detect_active_profile', return_value="Default"):
                            info = detector.get_browser_info()
                            
                            assert info['is_running'] is True
                            assert info['user_data_dir'] == temp_dir
                            assert info['active_profile'] == "Default"
                            assert info['all_profiles'] == ["Default", "Profile 1"]
    
    def test_get_browser_info_no_user_data_dir(self):
        """测试场景：无用户数据目录的浏览器信息"""
        detector = BrowserDetector()
        
        with patch.object(detector, 'is_browser_running', return_value=False):
            with patch.object(detector, '_get_edge_user_data_dir', return_value=None):
                info = detector.get_browser_info()
                
                assert info['is_running'] is False
                assert info['user_data_dir'] is None
                assert info['active_profile'] is None
                assert info['all_profiles'] == []
    
    def test_get_browser_info_user_data_dir_not_exists(self):
        """测试场景：用户数据目录不存在"""
        detector = BrowserDetector()
        
        with patch.object(detector, 'is_browser_running', return_value=False):
            with patch.object(detector, '_get_edge_user_data_dir', return_value="/nonexistent"):
                info = detector.get_browser_info()
                
                assert info['is_running'] is False
                assert info['user_data_dir'] == "/nonexistent"
                assert info['active_profile'] is None
                assert info['all_profiles'] == []


class TestBrowserDetectorConvenienceFunctions:
    """测试便捷函数"""
    
    @patch('rpa.browser.utils.browser_detector.BrowserDetector')
    def test_detect_active_profile_function(self, mock_detector_class):
        """测试场景：便捷函数调用 BrowserDetector"""
        mock_instance = Mock()
        mock_instance.detect_active_profile.return_value = "Default"
        mock_detector_class.return_value = mock_instance
        
        result = detect_active_profile()
        
        assert result == "Default"
        mock_detector_class.assert_called_once()
        mock_instance.detect_active_profile.assert_called_once()
    
    @patch('rpa.browser.utils.browser_detector.BrowserDetector')
    def test_get_browser_info_function(self, mock_detector_class):
        """测试场景：便捷函数获取浏览器信息"""
        mock_instance = Mock()
        expected_info = {
            'is_running': True,
            'user_data_dir': '/fake/path',
            'active_profile': 'Default',
            'all_profiles': ['Default']
        }
        mock_instance.get_browser_info.return_value = expected_info
        mock_detector_class.return_value = mock_instance
        
        result = get_browser_info()
        
        assert result == expected_info
        mock_detector_class.assert_called_once()
        mock_instance.get_browser_info.assert_called_once()


class TestBrowserDetectorIntegration:
    """集成测试"""
    
    def test_full_workflow_with_mock_filesystem(self):
        """测试场景：完整工作流程的集成测试"""
        detector = BrowserDetector()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建模拟的浏览器目录结构
            default_profile = os.path.join(temp_dir, "Default")
            profile1 = os.path.join(temp_dir, "Profile 1")
            os.makedirs(default_profile)
            os.makedirs(profile1)
            
            # 设置修改时间（Profile 1 更新）
            os.utime(default_profile, (time.time() - 100, time.time() - 100))
            os.utime(profile1, (time.time() - 10, time.time() - 10))
            
            # Mock 系统相关方法
            with patch.object(detector, '_get_edge_user_data_dir', return_value=temp_dir):
                with patch.object(detector, 'is_browser_running', return_value=False):
                    
                    # 测试完整流程
                    info = detector.get_browser_info()
                    
                    assert info['is_running'] is False
                    assert info['user_data_dir'] == temp_dir
                    assert info['active_profile'] == "Profile 1"  # 最近使用的
                    assert "Profile 1" in info['all_profiles']
                    assert "Default" in info['all_profiles']
                    
                    # 测试 Profile 可用性
                    assert detector.is_profile_available(temp_dir, "Default") is True
                    assert detector.is_profile_available(temp_dir, "Profile 1") is True
                    assert detector.is_profile_available(temp_dir, "NonExistent") is False


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
