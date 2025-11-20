"""
全局浏览器单例测试套件

测试范围：
1. 单例唯一性测试
2. 线程安全测试  
3. 状态管理测试
4. 错误恢复测试
5. 配置传递测试
6. Profile 检测和验证测试
7. 异常处理测试
8. 环境变量配置测试
"""

import pytest
import threading
import time
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any


@pytest.fixture(autouse=True)
def reset_global_state():
    """自动重置全局状态的 fixture"""
    import common.scrapers.global_browser_singleton as singleton_module
    
    # 测试前重置
    with singleton_module._global_lock:
        singleton_module._global_browser_service = None
        singleton_module._global_initialized = False
    
    yield
    
    # 测试后重置
    with singleton_module._global_lock:
        singleton_module._global_browser_service = None
        singleton_module._global_initialized = False


class TestGlobalBrowserSingletonBasic:
    """测试全局浏览器单例基本功能"""
    
    @patch('common.scrapers.global_browser_singleton.SimplifiedBrowserService')
    @patch('common.scrapers.global_browser_singleton.BrowserDetector')
    @patch('common.scrapers.global_browser_singleton.detect_active_profile')
    def test_first_call_creates_instance(self, mock_detect_profile, mock_detector_class, mock_service_class):
        """测试场景：第一次调用创建实例"""
        from common.scrapers.global_browser_singleton import get_global_browser_service

        # Mock 设置
        mock_detect_profile.return_value = "Default"
        mock_detector = Mock()
        mock_detector._get_edge_user_data_dir.return_value = "/fake/edge/data"
        mock_detector.is_profile_available.return_value = True
        mock_detector_class.return_value = mock_detector

        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # 调用函数
        result = get_global_browser_service()

        # 验证创建了实例
        assert result == mock_service
        mock_service_class.assert_called_once()

    @patch('common.scrapers.global_browser_singleton.SimplifiedBrowserService')
    @patch('common.scrapers.global_browser_singleton.BrowserDetector')
    @patch('common.scrapers.global_browser_singleton.detect_active_profile')
    def test_subsequent_calls_return_same_instance(self, mock_detect_profile, mock_detector_class, mock_service_class):
        """测试场景：后续调用返回同一实例"""
        from common.scrapers.global_browser_singleton import get_global_browser_service

        # Mock 设置
        mock_detect_profile.return_value = "Default"
        mock_detector = Mock()
        mock_detector._get_edge_user_data_dir.return_value = "/fake/edge/data"
        mock_detector.is_profile_available.return_value = True
        mock_detector_class.return_value = mock_detector

        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # 多次调用
        result1 = get_global_browser_service()
        result2 = get_global_browser_service()
        result3 = get_global_browser_service()

        # 验证返回同一实例
        assert result1 is result2
        assert result2 is result3
        assert result1 is result3

        # 验证只创建了一次
        mock_service_class.assert_called_once()


class TestGlobalBrowserSingletonThreadSafety:
    """测试全局浏览器单例线程安全"""
    
    @patch('common.scrapers.global_browser_singleton.SimplifiedBrowserService')
    @patch('common.scrapers.global_browser_singleton.BrowserDetector')
    @patch('common.scrapers.global_browser_singleton.detect_active_profile')
    def test_thread_safety_single_instance(self, mock_detect_profile, mock_detector_class, mock_service_class):
        """测试场景：多线程访问返回同一实例"""
        from common.scrapers.global_browser_singleton import get_global_browser_service

        # Mock 设置
        mock_detect_profile.return_value = "Default"
        mock_detector = Mock()
        mock_detector._get_edge_user_data_dir.return_value = "/fake/edge/data"
        mock_detector.is_profile_available.return_value = True
        mock_detector_class.return_value = mock_detector

        mock_service = Mock()
        mock_service_class.return_value = mock_service

        results = []
        
        def worker():
            result = get_global_browser_service()
            results.append(result)

        # 创建多个线程
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)

        # 启动所有线程
        for thread in threads:
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有结果都是同一实例
        assert len(results) == 5
        for result in results:
            assert result is results[0]

        # 验证只创建了一次
        mock_service_class.assert_called_once()

    @patch('common.scrapers.global_browser_singleton.SimplifiedBrowserService')
    @patch('common.scrapers.global_browser_singleton.BrowserDetector')
    @patch('common.scrapers.global_browser_singleton.detect_active_profile')
    def test_thread_safety_with_delay(self, mock_detect_profile, mock_detector_class, mock_service_class):
        """测试场景：有延迟的多线程访问"""
        from common.scrapers.global_browser_singleton import get_global_browser_service

        # Mock 设置
        mock_detect_profile.return_value = "Default"
        mock_detector = Mock()
        mock_detector._get_edge_user_data_dir.return_value = "/fake/edge/data"
        mock_detector.is_profile_available.return_value = True
        mock_detector_class.return_value = mock_detector

        mock_service = Mock()
        mock_service_class.return_value = mock_service

        results = []
        
        def worker_with_delay():
            time.sleep(0.01)  # 模拟延迟
            result = get_global_browser_service()
            results.append(result)

        # 创建多个线程
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=worker_with_delay)
            threads.append(thread)

        # 启动所有线程
        for thread in threads:
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有结果都是同一实例
        assert len(results) == 3
        for result in results:
            assert result is results[0]

        # 验证只创建了一次
        mock_service_class.assert_called_once()


class TestGlobalBrowserSingletonConfigurationHandling:
    """测试全局浏览器单例配置处理"""
    
    @patch.dict(os.environ, {
        'PREFERRED_BROWSER': 'chrome',
        'BROWSER_DEBUG_PORT': '9223'
    })
    @patch('common.scrapers.global_browser_singleton.SimplifiedBrowserService')
    @patch('common.scrapers.global_browser_singleton.BrowserDetector')
    @patch('common.scrapers.global_browser_singleton.detect_active_profile')
    def test_environment_variable_configuration(self, mock_detect_profile, mock_detector_class, mock_service_class):
        """测试场景：从环境变量读取配置"""
        from common.scrapers.global_browser_singleton import get_global_browser_service

        # Mock 设置
        mock_detect_profile.return_value = "Default"
        mock_detector = Mock()
        mock_detector._get_edge_user_data_dir.return_value = "/fake/edge/data"
        mock_detector.is_profile_available.return_value = True
        mock_detector_class.return_value = mock_detector

        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # 调用函数
        get_global_browser_service()

        # 验证环境变量被使用
        mock_service_class.assert_called_once()
        call_args = mock_service_class.call_args
        config_dict = call_args[0][0]

        # 验证调试端口配置
        assert config_dict['browser_config']['debug_port'] == 9223

    @patch('common.scrapers.global_browser_singleton.SimplifiedBrowserService')
    @patch('common.scrapers.global_browser_singleton.BrowserDetector')
    @patch('common.scrapers.global_browser_singleton.detect_active_profile')
    def test_custom_config_parameter(self, mock_detect_profile, mock_detector_class, mock_service_class):
        """测试场景：传递自定义配置参数"""
        from common.scrapers.global_browser_singleton import get_global_browser_service

        # Mock 设置
        mock_detect_profile.return_value = "Default"
        mock_detector = Mock()
        mock_detector._get_edge_user_data_dir.return_value = "/fake/edge/data"
        mock_detector.is_profile_available.return_value = True
        mock_detector_class.return_value = mock_detector

        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # 自定义配置
        custom_config = {'browser': {'headless': True}}
        
        # 调用函数
        get_global_browser_service(custom_config)

        # 验证配置被使用
        mock_service_class.assert_called_once()
        call_args = mock_service_class.call_args
        config_dict = call_args[0][0]

        # 验证 headless 配置
        assert config_dict['browser_config']['headless'] is True

    @patch('common.scrapers.global_browser_singleton.SimplifiedBrowserService')
    @patch('common.scrapers.global_browser_singleton.BrowserDetector')
    @patch('common.scrapers.global_browser_singleton.detect_active_profile')
    def test_subsequent_config_ignored(self, mock_detect_profile, mock_detector_class, mock_service_class):
        """测试场景：后续调用忽略配置参数"""
        from common.scrapers.global_browser_singleton import get_global_browser_service

        # Mock 设置
        mock_detect_profile.return_value = "Default"
        mock_detector = Mock()
        mock_detector._get_edge_user_data_dir.return_value = "/fake/edge/data"
        mock_detector.is_profile_available.return_value = True
        mock_detector_class.return_value = mock_detector

        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # 第一次调用
        config1 = {'browser': {'headless': True}}
        result1 = get_global_browser_service(config1)

        # 第二次调用（不同配置）
        config2 = {'browser': {'headless': False}}
        result2 = get_global_browser_service(config2)

        # 验证返回同一实例，配置被忽略
        assert result1 is result2
        mock_service_class.assert_called_once()


class TestGlobalBrowserSingletonStateManagement:
    """测试全局浏览器单例状态管理"""
    
    def test_initial_state_not_initialized(self):
        """测试场景：初始状态未初始化"""
        from common.scrapers.global_browser_singleton import is_global_browser_initialized
        
        assert is_global_browser_initialized() is False

    def test_set_initialized_state(self):
        """测试场景：设置初始化状态"""
        from common.scrapers.global_browser_singleton import (
            is_global_browser_initialized,
            set_global_browser_initialized
        )
        
        # 初始状态
        assert is_global_browser_initialized() is False
        
        # 设置为已初始化
        set_global_browser_initialized(True)
        assert is_global_browser_initialized() is True
        
        # 设置为未初始化
        set_global_browser_initialized(False)
        assert is_global_browser_initialized() is False

    def test_global_lock_type(self):
        """测试场景：全局锁类型检查"""
        from common.scrapers.global_browser_singleton import get_global_lock
        
        lock = get_global_lock()
        assert isinstance(lock, type(threading.Lock()))

    def test_reset_global_browser_on_failure(self):
        """测试场景：失败时重置全局浏览器"""
        from common.scrapers.global_browser_singleton import (
            reset_global_browser_on_failure,
            is_global_browser_initialized
        )
        import common.scrapers.global_browser_singleton as singleton_module
        
        # 模拟有全局服务实例
        mock_service = Mock()
        singleton_module._global_browser_service = mock_service
        singleton_module._global_initialized = True
        
        # 重置
        reset_global_browser_on_failure()
        
        # 验证状态被重置
        assert singleton_module._global_browser_service is None
        assert singleton_module._global_initialized is False


class TestGlobalBrowserSingletonProfileHandling:
    """测试全局浏览器单例 Profile 处理"""
    
    @patch('common.scrapers.global_browser_singleton.SimplifiedBrowserService')
    @patch('common.scrapers.global_browser_singleton.BrowserDetector')
    @patch('common.scrapers.global_browser_singleton.detect_active_profile')
    def test_profile_detection_success(self, mock_detect_profile, mock_detector_class, mock_service_class):
        """测试场景：成功检测到 Profile"""
        from common.scrapers.global_browser_singleton import get_global_browser_service

        # Mock 设置
        mock_detect_profile.return_value = "Profile 1"
        mock_detector = Mock()
        mock_detector._get_edge_user_data_dir.return_value = "/fake/edge/data"
        mock_detector.is_profile_available.return_value = True
        mock_detector_class.return_value = mock_detector

        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # 调用函数
        get_global_browser_service()

        # 验证检测到的 Profile 被使用
        mock_detector.is_profile_available.assert_called_with("/fake/edge/data", "Profile 1")

    @patch('common.scrapers.global_browser_singleton.SimplifiedBrowserService')
    @patch('common.scrapers.global_browser_singleton.BrowserDetector')
    @patch('common.scrapers.global_browser_singleton.detect_active_profile')
    def test_profile_detection_fallback_to_default(self, mock_detect_profile, mock_detector_class, mock_service_class):
        """测试场景：Profile 检测失败，回退到默认"""
        from common.scrapers.global_browser_singleton import get_global_browser_service

        # Mock 设置
        mock_detect_profile.return_value = None  # 检测失败
        mock_detector = Mock()
        mock_detector._get_edge_user_data_dir.return_value = "/fake/edge/data"
        mock_detector.is_profile_available.return_value = True
        mock_detector_class.return_value = mock_detector

        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # 调用函数
        get_global_browser_service()

        # 验证使用了默认 Profile
        mock_detector.is_profile_available.assert_called_with("/fake/edge/data", "Default")

    @patch('common.scrapers.global_browser_singleton.SimplifiedBrowserService')
    @patch('common.scrapers.global_browser_singleton.BrowserDetector')
    @patch('common.scrapers.global_browser_singleton.detect_active_profile')
    def test_profile_locked_recovery_success(self, mock_detect_profile, mock_detector_class, mock_service_class):
        """测试场景：Profile 被锁定，成功恢复"""
        from common.scrapers.global_browser_singleton import get_global_browser_service

        # Mock 设置
        mock_detect_profile.return_value = "Default"
        mock_detector = Mock()
        mock_detector._get_edge_user_data_dir.return_value = "/fake/edge/data"
        # 第一次检查不可用，第二次检查可用（恢复成功）
        mock_detector.is_profile_available.side_effect = [False, True]
        mock_detector.kill_browser_processes.return_value = True
        mock_detector.wait_for_profile_unlock.return_value = True
        mock_detector_class.return_value = mock_detector

        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # 调用函数
        result = get_global_browser_service()

        # 验证恢复流程被调用
        mock_detector.kill_browser_processes.assert_called_once()
        mock_detector.wait_for_profile_unlock.assert_called_once()

        # 验证最终成功创建服务
        assert result == mock_service

    @patch('common.scrapers.global_browser_singleton.BrowserDetector')
    @patch('common.scrapers.global_browser_singleton.detect_active_profile')
    def test_profile_locked_recovery_failed_unlock(self, mock_detect_profile, mock_detector_class):
        """测试场景：Profile 被锁定，解锁失败"""
        from common.scrapers.global_browser_singleton import get_global_browser_service

        # Mock 设置
        mock_detect_profile.return_value = "Default"
        mock_detector = Mock()
        mock_detector._get_edge_user_data_dir.return_value = "/fake/edge/data"
        mock_detector.is_profile_available.return_value = False
        mock_detector.kill_browser_processes.return_value = True
        mock_detector.wait_for_profile_unlock.return_value = False  # 解锁失败
        mock_detector_class.return_value = mock_detector

        # 调用函数应该抛出异常
        with pytest.raises(RuntimeError, match="清理后仍然被锁定"):
            get_global_browser_service()

    @patch('common.scrapers.global_browser_singleton.BrowserDetector')
    @patch('common.scrapers.global_browser_singleton.detect_active_profile')
    def test_profile_locked_kill_process_failed(self, mock_detect_profile, mock_detector_class):
        """测试场景：Profile 被锁定，清理进程失败"""
        from common.scrapers.global_browser_singleton import get_global_browser_service

        # Mock 设置
        mock_detect_profile.return_value = "Default"
        mock_detector = Mock()
        mock_detector._get_edge_user_data_dir.return_value = "/fake/edge/data"
        mock_detector.is_profile_available.return_value = False
        mock_detector.kill_browser_processes.return_value = False  # 清理失败
        mock_detector_class.return_value = mock_detector

        # 调用函数应该抛出异常
        with pytest.raises(RuntimeError, match="清理僵尸进程失败"):
            get_global_browser_service()


class TestGlobalBrowserSingletonExceptionHandling:
    """测试全局浏览器单例异常处理"""
    
    @patch('common.scrapers.global_browser_singleton.BrowserDetector')
    @patch('common.scrapers.global_browser_singleton.detect_active_profile')
    def test_no_user_data_dir(self, mock_detect_profile, mock_detector_class):
        """测试场景：无法获取用户数据目录"""
        from common.scrapers.global_browser_singleton import get_global_browser_service

        # Mock 设置
        mock_detect_profile.return_value = "Default"
        mock_detector = Mock()
        mock_detector._get_edge_user_data_dir.return_value = None  # 无法获取目录
        mock_detector_class.return_value = mock_detector

        # 调用函数应该抛出异常
        with pytest.raises(RuntimeError, match="无法获取用户数据目录"):
            get_global_browser_service()

    @patch('common.scrapers.global_browser_singleton.SimplifiedBrowserService')
    @patch('common.scrapers.global_browser_singleton.BrowserDetector')
    @patch('common.scrapers.global_browser_singleton.detect_active_profile')
    def test_browser_service_creation_exception(self, mock_detect_profile, mock_detector_class, mock_service_class):
        """测试场景：浏览器服务创建时抛出异常"""
        from common.scrapers.global_browser_singleton import get_global_browser_service

        # Mock 设置
        mock_detect_profile.return_value = "Default"
        mock_detector = Mock()
        mock_detector._get_edge_user_data_dir.return_value = "/fake/edge/data"
        mock_detector.is_profile_available.return_value = True
        mock_detector_class.return_value = mock_detector

        # 模拟服务创建失败
        mock_service_class.side_effect = Exception("Service creation failed")

        # 调用函数应该抛出异常
        with pytest.raises(Exception, match="Service creation failed"):
            get_global_browser_service()


class TestGlobalBrowserSingletonIntegration:
    """测试全局浏览器单例集成功能"""
    
    @patch('common.scrapers.global_browser_singleton.SimplifiedBrowserService')
    @patch('common.scrapers.global_browser_singleton.BrowserDetector')
    @patch('common.scrapers.global_browser_singleton.detect_active_profile')
    def test_full_workflow_success(self, mock_detect_profile, mock_detector_class, mock_service_class):
        """测试场景：完整工作流程成功"""
        from common.scrapers.global_browser_singleton import (
            get_global_browser_service,
            is_global_browser_initialized,
            set_global_browser_initialized,
            reset_global_browser_on_failure
        )

        # Mock 设置
        mock_detect_profile.return_value = "Profile 1"
        mock_detector = Mock()
        mock_detector._get_edge_user_data_dir.return_value = "/fake/edge/data"
        mock_detector.is_profile_available.return_value = True
        mock_detector_class.return_value = mock_detector

        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # 1. 初始状态检查
        assert is_global_browser_initialized() is False

        # 2. 获取服务（第一次）
        service1 = get_global_browser_service({'browser': {'headless': True}})
        assert service1 == mock_service

        # 3. 获取服务（第二次，应该返回同一实例）
        service2 = get_global_browser_service()
        assert service2 is service1

        # 4. 设置初始化状态
        set_global_browser_initialized(True)
        assert is_global_browser_initialized() is True

        # 5. 重置状态
        reset_global_browser_on_failure()
        
        # 6. 验证重置后状态
        import common.scrapers.global_browser_singleton as singleton_module
        assert singleton_module._global_browser_service is None
        assert singleton_module._global_initialized is False

        # 验证只创建了一次服务
        mock_service_class.assert_called_once()

    @patch('common.scrapers.global_browser_singleton.SimplifiedBrowserService')
    @patch('common.scrapers.global_browser_singleton.BrowserDetector')
    @patch('common.scrapers.global_browser_singleton.detect_active_profile')
    def test_configuration_precedence(self, mock_detect_profile, mock_detector_class, mock_service_class):
        """测试场景：配置优先级"""
        from common.scrapers.global_browser_singleton import get_global_browser_service

        # Mock 设置
        mock_detect_profile.return_value = "Default"
        mock_detector = Mock()
        mock_detector._get_edge_user_data_dir.return_value = "/fake/edge/data"
        mock_detector.is_profile_available.return_value = True
        mock_detector_class.return_value = mock_detector

        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # 传递配置参数
        config = {'browser': {'headless': True}}
        get_global_browser_service(config)

        # 验证配置被使用
        mock_service_class.assert_called_once()
        call_args = mock_service_class.call_args
        config_dict = call_args[0][0]
        
        # 验证配置参数生效
        assert config_dict['browser_config']['headless'] is True
