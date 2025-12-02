# """
# SimplifiedBrowserService全局单例功能单元测试
#
# 测试范围:
# - 全局单例管理功能
# - 线程安全性
# - 配置管理
# - 状态管理
# - 兼容性包装器
# """
#
# import pytest
# import threading
# import time
# import warnings
# from unittest.mock import patch, MagicMock
# from typing import Dict, Any
#
# from rpa.browser.browser_service import SimplifiedBrowserService
#
#
# class TestBrowserServiceSingleton:
#     """SimplifiedBrowserService全局单例功能测试"""
#
#     def setup_method(self):
#         """测试前重置全局状态"""
#         SimplifiedBrowserService.reset_global_instance()
#
#     def teardown_method(self):
#         """测试后清理全局状态"""
#         SimplifiedBrowserService.reset_global_instance()
#
#     def test_get_global_instance_creates_singleton(self):
#         """测试首次调用创建单例"""
#         # 确认初始状态
#         assert not SimplifiedBrowserService.has_global_instance()
#
#         # 创建配置
#         config = {
#             'browser': {
#                 'browser_type': 'edge',
#                 'headless': True,
#                 'debug_port': 9222
#             }
#         }
#
#         # 首次调用应创建实例
#         with patch.object(SimplifiedBrowserService, '_create_default_global_config') as mock_config:
#             mock_config.return_value = config
#
#             instance1 = SimplifiedBrowserService.get_global_instance(config)
#
#         assert SimplifiedBrowserService.has_global_instance()
#         assert instance1 is not None
#         assert isinstance(instance1, SimplifiedBrowserService)
#
#     def test_get_global_instance_returns_same_instance(self):
#         """测试后续调用返回同一实例"""
#         config = {
#             'browser': {
#                 'browser_type': 'edge',
#                 'headless': True,
#                 'debug_port': 9222
#             }
#         }
#
#         with patch.object(SimplifiedBrowserService, '_create_default_global_config') as mock_config:
#             mock_config.return_value = config
#
#             instance1 = SimplifiedBrowserService.get_global_instance(config)
#             instance2 = SimplifiedBrowserService.get_global_instance(config)
#             instance3 = SimplifiedBrowserService.get_global_instance(None)  # 不同配置
#
#         # 应该返回同一个实例
#         assert instance1 is instance2
#         assert instance2 is instance3
#         assert SimplifiedBrowserService.has_global_instance()
#
#     def test_reset_global_instance(self):
#         """测试重置全局实例"""
#         config = {
#             'browser': {
#                 'browser_type': 'edge',
#                 'headless': True,
#                 'debug_port': 9222
#             }
#         }
#
#         with patch.object(SimplifiedBrowserService, '_create_default_global_config') as mock_config:
#             mock_config.return_value = config
#
#             # 创建实例
#             instance1 = SimplifiedBrowserService.get_global_instance(config)
#             assert SimplifiedBrowserService.has_global_instance()
#
#             # 重置
#             success = SimplifiedBrowserService.reset_global_instance()
#             assert success
#             assert not SimplifiedBrowserService.has_global_instance()
#
#             # 重新创建应该是新实例
#             instance2 = SimplifiedBrowserService.get_global_instance(config)
#             assert instance1 is not instance2
#
#     def test_initialization_state_management(self):
#         """测试初始化状态管理"""
#         config = {
#             'browser': {
#                 'browser_type': 'edge',
#                 'headless': True,
#                 'debug_port': 9222
#             }
#         }
#
#         with patch.object(SimplifiedBrowserService, '_create_default_global_config') as mock_config:
#             mock_config.return_value = config
#
#             # 创建实例，初始应该未初始化
#             instance = SimplifiedBrowserService.get_global_instance(config)
#             assert not SimplifiedBrowserService.is_global_instance_initialized()
#
#             # 手动设置初始化状态
#             SimplifiedBrowserService.set_global_instance_initialized(True)
#             assert SimplifiedBrowserService.is_global_instance_initialized()
#
#             # 重置应该清除初始化状态
#             SimplifiedBrowserService.set_global_instance_initialized(False)
#             assert not SimplifiedBrowserService.is_global_instance_initialized()
#
#     def test_thread_safety(self):
#         """测试线程安全性"""
#         config = {
#             'browser': {
#                 'browser_type': 'edge',
#                 'headless': True,
#                 'debug_port': 9222
#             }
#         }
#
#         instances = []
#         errors = []
#
#         def create_instance():
#             """线程函数：创建全局实例"""
#             try:
#                 with patch.object(SimplifiedBrowserService, '_create_default_global_config') as mock_config:
#                     mock_config.return_value = config
#                     instance = SimplifiedBrowserService.get_global_instance(config)
#                     instances.append(instance)
#             except Exception as e:
#                 errors.append(e)
#
#         # 创建多个线程同时调用
#         threads = []
#         for i in range(10):
#             thread = threading.Thread(target=create_instance)
#             threads.append(thread)
#
#         # 同时启动所有线程
#         for thread in threads:
#             thread.start()
#
#         # 等待所有线程完成
#         for thread in threads:
#             thread.join()
#
#         # 验证结果
#         assert len(errors) == 0, f"线程执行出现错误: {errors}"
#         assert len(instances) == 10, "应该有10个实例返回"
#
#         # 所有实例应该是同一个对象
#         first_instance = instances[0]
#         for instance in instances[1:]:
#             assert instance is first_instance, "所有线程应该得到同一个实例"
#
#     def test_create_default_global_config_with_env_vars(self):
#         """测试默认配置创建（使用环境变量）"""
#         with patch.dict('os.environ', {
#             'PREFERRED_BROWSER': 'chrome',
#             'BROWSER_DEBUG_PORT': '9223',
#             'BROWSER_HEADLESS': 'true'
#         }):
#             with patch('rpa.browser.browser_service.detect_active_profile') as mock_detect:
#                 with patch('rpa.browser.browser_service.BrowserDetector') as mock_detector_class:
#                     # 模拟检测器
#                     mock_detector = MagicMock()
#                     mock_detector_class.return_value = mock_detector
#                     mock_detector._get_chrome_user_data_dir.return_value = '/test/chrome/data'
#                     mock_detector.kill_browser_processes.return_value = True
#                     mock_detector.is_profile_available.return_value = True
#
#                     # 模拟profile检测
#                     mock_detect.return_value = 'TestProfile'
#
#                     config = SimplifiedBrowserService._create_default_global_config()
#
#                     # 验证配置
#                     assert config is not None
#                     assert isinstance(config, dict)
#                     browser_config = config.get('browser_config', {})
#                     assert browser_config.get('browser_type') == 'chrome'
#                     assert browser_config.get('headless') is True
#                     assert browser_config.get('debug_port') == 9223
#                     assert 'TestProfile' in browser_config.get('user_data_dir', '')
#
#     def test_create_default_global_config_error_handling(self):
#         """测试默认配置创建错误处理"""
#         with patch('rpa.browser.browser_service.BrowserDetector') as mock_detector_class:
#             # 模拟检测器抛出异常
#             mock_detector = MagicMock()
#             mock_detector_class.return_value = mock_detector
#             mock_detector._get_edge_user_data_dir.return_value = None
#
#             with pytest.raises(RuntimeError, match="无法获取用户数据目录"):
#                 SimplifiedBrowserService._create_default_global_config()
#
#     def test_reset_with_running_instance(self):
#         """测试重置运行中的实例"""
#         config = {
#             'browser': {
#                 'browser_type': 'edge',
#                 'headless': True,
#                 'debug_port': 9222
#             }
#         }
#
#         with patch.object(SimplifiedBrowserService, '_create_default_global_config') as mock_config:
#             mock_config.return_value = config
#
#             # 创建实例并模拟启动状态
#             instance = SimplifiedBrowserService.get_global_instance(config)
#
#             with patch.object(instance, '_browser_started', True):
#                 with patch.object(instance, 'close_sync', return_value=True) as mock_close:
#                     # 重置应该调用关闭方法
#                     success = SimplifiedBrowserService.reset_global_instance()
#                     assert success
#                     mock_close.assert_called_once()
#
#     def test_reset_empty_instance(self):
#         """测试重置空实例"""
#         # 没有全局实例时重置应该成功
#         assert not SimplifiedBrowserService.has_global_instance()
#         success = SimplifiedBrowserService.reset_global_instance()
#         assert success
#
#
# class TestGlobalBrowserSingletonCompatibility:
#     """global_browser_singleton兼容性包装器测试"""
#
#     def setup_method(self):
#         """测试前重置全局状态"""
#         SimplifiedBrowserService.reset_global_instance()
#
#     def teardown_method(self):
#         """测试后清理全局状态"""
#         SimplifiedBrowserService.reset_global_instance()
#
#     def test_get_global_browser_service_deprecation_warning(self):
#         """测试get_global_browser_service弃用警告"""
#         config = {
#             'browser': {
#                 'browser_type': 'edge',
#                 'headless': True,
#                 'debug_port': 9222
#             }
#         }
#
#         with patch.object(SimplifiedBrowserService, '_create_default_global_config') as mock_config:
#             mock_config.return_value = config
#
#             with warnings.catch_warnings(record=True) as w:
#                 warnings.simplefilter("always")
#
#                 from common.scrapers.global_browser_singleton import get_global_browser_service
#                 instance = get_global_browser_service(config)
#
#                 # 验证弃用警告
#                 assert len(w) == 1
#                 assert issubclass(w[0].category, DeprecationWarning)
#                 assert "已弃用" in str(w[0].message)
#
#                 # 验证功能正常
#                 assert instance is not None
#                 assert isinstance(instance, SimplifiedBrowserService)
#
#     def test_is_global_browser_initialized_compatibility(self):
#         """测试is_global_browser_initialized兼容性"""
#         with warnings.catch_warnings(record=True) as w:
#             warnings.simplefilter("always")
#
#             from common.scrapers.global_browser_singleton import is_global_browser_initialized
#             result = is_global_browser_initialized()
#
#             # 验证弃用警告
#             assert len(w) == 1
#             assert issubclass(w[0].category, DeprecationWarning)
#
#             # 验证功能正常
#             assert result is False  # 初始状态
#
#     def test_set_global_browser_initialized_compatibility(self):
#         """测试set_global_browser_initialized兼容性"""
#         config = {
#             'browser': {
#                 'browser_type': 'edge',
#                 'headless': True,
#                 'debug_port': 9222
#             }
#         }
#
#         with patch.object(SimplifiedBrowserService, '_create_default_global_config') as mock_config:
#             mock_config.return_value = config
#
#             # 先创建全局实例
#             SimplifiedBrowserService.get_global_instance(config)
#
#             with warnings.catch_warnings(record=True) as w:
#                 warnings.simplefilter("always")
#
#                 from common.scrapers.global_browser_singleton import (
#                     set_global_browser_initialized,
#                     is_global_browser_initialized
#                 )
#
#                 set_global_browser_initialized(True)
#                 result = is_global_browser_initialized()
#
#                 # 验证弃用警告（两次调用）
#                 assert len(w) >= 2
#
#                 # 验证功能正常
#                 assert result is True
#
#     def test_reset_global_browser_on_failure_compatibility(self):
#         """测试reset_global_browser_on_failure兼容性"""
#         config = {
#             'browser': {
#                 'browser_type': 'edge',
#                 'headless': True,
#                 'debug_port': 9222
#             }
#         }
#
#         with patch.object(SimplifiedBrowserService, '_create_default_global_config') as mock_config:
#             mock_config.return_value = config
#
#             # 先创建全局实例
#             SimplifiedBrowserService.get_global_instance(config)
#             assert SimplifiedBrowserService.has_global_instance()
#
#             with warnings.catch_warnings(record=True) as w:
#                 warnings.simplefilter("always")
#
#                 from common.scrapers.global_browser_singleton import reset_global_browser_on_failure
#                 result = reset_global_browser_on_failure()
#
#                 # 验证弃用警告
#                 assert len(w) == 1
#                 assert issubclass(w[0].category, DeprecationWarning)
#
#                 # 验证功能正常
#                 assert result is True
#                 assert not SimplifiedBrowserService.has_global_instance()
#
#     def test_get_global_lock_compatibility(self):
#         """测试get_global_lock兼容性"""
#         with warnings.catch_warnings(record=True) as w:
#             warnings.simplefilter("always")
#
#             from common.scrapers.global_browser_singleton import get_global_lock
#             result = get_global_lock()
#
#             # 验证弃用警告
#             assert len(w) == 1
#             assert issubclass(w[0].category, DeprecationWarning)
#
#             # 验证返回None（锁现在内部管理）
#             assert result is None
#
#     def test_set_browser_service_closed_compatibility(self):
#         """测试set_browser_service_closed兼容性"""
#         with warnings.catch_warnings(record=True) as w:
#             warnings.simplefilter("always")
#
#             from common.scrapers.global_browser_singleton import set_browser_service_closed
#             set_browser_service_closed()
#
#             # 验证弃用警告
#             assert len(w) == 1
#             assert issubclass(w[0].category, DeprecationWarning)
#
#     def test_set_browser_service_initialized_compatibility(self):
#         """测试set_browser_service_initialized兼容性"""
#         with warnings.catch_warnings(record=True) as w:
#             warnings.simplefilter("always")
#
#             from common.scrapers.global_browser_singleton import set_browser_service_initialized
#             set_browser_service_initialized()
#
#             # 验证弃用警告
#             assert len(w) == 1
#             assert issubclass(w[0].category, DeprecationWarning)
#
#
# if __name__ == '__main__':
#     pytest.main([__file__, '-v'])
