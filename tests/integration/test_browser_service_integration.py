# """
# SimplifiedBrowserService全局单例集成测试
#
# 验证重构后的全局单例管理功能在实际使用场景中的整体功能
# """
#
# import pytest
# import warnings
# from unittest.mock import patch, MagicMock
#
# from rpa.browser.browser_service import SimplifiedBrowserService
#
#
# class TestBrowserServiceIntegration:
#     """SimplifiedBrowserService全局单例集成测试"""
#
#     def setup_method(self):
#         """测试前重置全局状态"""
#         SimplifiedBrowserService.reset_global_instance()
#
#     def teardown_method(self):
#         """测试后清理全局状态"""
#         SimplifiedBrowserService.reset_global_instance()
#
#     def test_end_to_end_global_singleton_workflow(self):
#         """测试端到端全局单例工作流程"""
#         # 模拟配置
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
#             # 步骤1：首次获取全局实例
#             assert not SimplifiedBrowserService.has_global_instance()
#             instance1 = SimplifiedBrowserService.get_global_instance(config)
#             assert SimplifiedBrowserService.has_global_instance()
#             assert instance1 is not None
#
#             # 步骤2：再次获取应返回同一实例
#             instance2 = SimplifiedBrowserService.get_global_instance()
#             assert instance1 is instance2
#
#             # 步骤3：检查初始化状态
#             assert not SimplifiedBrowserService.is_global_instance_initialized()
#             SimplifiedBrowserService.set_global_instance_initialized(True)
#             assert SimplifiedBrowserService.is_global_instance_initialized()
#
#             # 步骤4：重置全局实例
#             success = SimplifiedBrowserService.reset_global_instance()
#             assert success
#             assert not SimplifiedBrowserService.has_global_instance()
#             assert not SimplifiedBrowserService.is_global_instance_initialized()
#
#             # 步骤5：重新创建实例验证完全重置
#             instance3 = SimplifiedBrowserService.get_global_instance(config)
#             assert instance3 is not instance1
#             assert SimplifiedBrowserService.has_global_instance()
#
#     def test_global_singleton_with_deprecated_wrapper(self):
#         """测试全局单例与弃用包装器的集成"""
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
#                 # 使用弃用的包装器API
#                 from common.scrapers.global_browser_singleton import (
#                     get_global_browser_service,
#                     is_global_browser_initialized,
#                     set_global_browser_initialized
#                 )
#
#                 # 通过弃用API获取实例
#                 deprecated_instance = get_global_browser_service(config)
#
#                 # 通过新API获取实例，应该是同一个
#                 new_instance = SimplifiedBrowserService.get_global_instance()
#                 assert deprecated_instance is new_instance
#
#                 # 验证弃用警告
#                 assert len(w) >= 1
#                 assert any(issubclass(warning.category, DeprecationWarning) for warning in w)
#
#                 # 测试状态同步
#                 set_global_browser_initialized(True)
#                 assert is_global_browser_initialized()
#                 assert SimplifiedBrowserService.is_global_instance_initialized()
#
#     def test_configuration_integration(self):
#         """测试配置集成功能"""
#         # 测试默认配置创建
#         with patch('rpa.browser.browser_service.detect_active_profile') as mock_detect:
#             with patch('rpa.browser.browser_service.BrowserDetector') as mock_detector_class:
#                 # 模拟检测器
#                 mock_detector = MagicMock()
#                 mock_detector_class.return_value = mock_detector
#                 mock_detector._get_edge_user_data_dir.return_value = '/test/edge/data'
#                 mock_detector.kill_browser_processes.return_value = True
#                 mock_detector.is_profile_available.return_value = True
#
#                 # 模拟profile检测
#                 mock_detect.return_value = 'TestProfile'
#
#                 # 不提供配置，应该使用默认配置创建
#                 instance = SimplifiedBrowserService.get_global_instance()
#                 assert instance is not None
#                 assert SimplifiedBrowserService.has_global_instance()
#
#     def test_error_handling_integration(self):
#         """测试错误处理集成"""
#         # 测试配置创建失败的情况
#         with patch.object(SimplifiedBrowserService, '_create_default_global_config') as mock_config:
#             mock_config.side_effect = RuntimeError("配置创建失败")
#
#             with pytest.raises(RuntimeError, match="配置创建失败"):
#                 SimplifiedBrowserService.get_global_instance()
#
#             # 确保失败后没有创建全局实例
#             assert not SimplifiedBrowserService.has_global_instance()
#
#     def test_reset_with_active_browser_integration(self):
#         """测试带有活跃浏览器的重置集成"""
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
#             instance = SimplifiedBrowserService.get_global_instance(config)
#
#             # 模拟浏览器启动状态
#             with patch.object(instance, '_browser_started', True):
#                 with patch.object(instance, 'close_sync', return_value=True) as mock_close:
#                     # 重置应该先关闭浏览器
#                     success = SimplifiedBrowserService.reset_global_instance()
#                     assert success
#                     mock_close.assert_called_once()
#                     assert not SimplifiedBrowserService.has_global_instance()
#
#     def test_cross_module_compatibility(self):
#         """测试跨模块兼容性集成"""
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
#             with warnings.catch_warnings(record=True):
#                 warnings.simplefilter("always")
#
#                 # 混合使用新旧API
#                 from common.scrapers.global_browser_singleton import get_global_browser_service
#
#                 # 通过旧API创建
#                 old_instance = get_global_browser_service(config)
#
#                 # 通过新API访问
#                 new_instance = SimplifiedBrowserService.get_global_instance()
#                 assert old_instance is new_instance
#
#                 # 状态管理
#                 SimplifiedBrowserService.set_global_instance_initialized(True)
#                 assert SimplifiedBrowserService.is_global_instance_initialized()
#
#                 # 重置
#                 SimplifiedBrowserService.reset_global_instance()
#                 assert not SimplifiedBrowserService.has_global_instance()
#
#
# if __name__ == '__main__':
#     pytest.main([__file__, '-v'])
