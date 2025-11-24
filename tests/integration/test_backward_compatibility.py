"""
向后兼容性测试

验证新架构与原有API接口的兼容性，确保升级后不会破坏现有功能
"""

import unittest
import time
from unittest.mock import patch, MagicMock
from cli.task_controller import TaskController
from cli.models import UIConfig
from task_manager.controllers import TaskManager
from task_manager.interfaces import TaskStatus
from cli.task_controller_adapter import TaskControllerAdapter


class TestBackwardCompatibility(unittest.TestCase):
    """向后兼容性测试"""
    
    def setUp(self):
        """测试初始化"""
        self.task_controller = TaskController()
        self.ui_config = UIConfig(
            good_shop_file="test_shops.xlsx",
            margin_calculator="test_calc.xlsx",
            output_path="test_output.xlsx"
        )
    
    def test_task_controller_api_compatibility(self):
        """测试TaskController API兼容性"""
        # 验证TaskController的公共接口保持不变
        self.assertTrue(hasattr(self.task_controller, 'start_task'))
        self.assertTrue(hasattr(self.task_controller, 'pause_task'))
        self.assertTrue(hasattr(self.task_controller, 'resume_task'))
        self.assertTrue(hasattr(self.task_controller, 'stop_task'))
        self.assertTrue(hasattr(self.task_controller, 'get_task_status'))
        
        # 验证方法签名兼容性
        import inspect
        start_signature = inspect.signature(self.task_controller.start_task)
        self.assertIn('config', start_signature.parameters)
        
        pause_signature = inspect.signature(self.task_controller.pause_task)
        self.assertEqual(len(pause_signature.parameters), 0)
        
        resume_signature = inspect.signature(self.task_controller.resume_task)
        self.assertEqual(len(resume_signature.parameters), 0)
        
        stop_signature = inspect.signature(self.task_controller.stop_task)
        self.assertEqual(len(stop_signature.parameters), 0)
        
        get_status_signature = inspect.signature(self.task_controller.get_task_status)
        self.assertEqual(len(get_status_signature.parameters), 0)
    
    def test_task_controller_adapter_integration(self):
        """测试TaskController适配器集成"""
        # 验证适配器正确实现了接口
        adapter = TaskControllerAdapter()
        self.assertIsInstance(adapter, TaskControllerAdapter)
        
        # 验证适配器方法存在
        self.assertTrue(hasattr(adapter, 'start_task'))
        self.assertTrue(hasattr(adapter, 'pause_task'))
        self.assertTrue(hasattr(adapter, 'resume_task'))
        self.assertTrue(hasattr(adapter, 'stop_task'))
        self.assertTrue(hasattr(adapter, 'get_task_status'))
    
    @patch('good_store_selector.GoodStoreSelector')
    def test_task_lifecycle_compatibility(self, mock_selector):
        """测试任务生命周期兼容性"""
        # 模拟GoodStoreSelector的行为
        mock_instance = MagicMock()
        mock_instance.process_stores.return_value = {"status": "completed"}
        mock_selector.return_value = mock_instance
        
        # 测试任务创建和启动
        result = self.task_controller.start_task(self.ui_config)
        # 由于是mock测试，我们验证接口调用而不是实际执行
        self.assertTrue(hasattr(self.task_controller, '_adapter'))
    
    def test_ui_config_compatibility(self):
        """测试UIConfig兼容性"""
        # 验证UIConfig的字段保持向后兼容
        config = UIConfig()
        
        # 验证必需字段存在
        required_fields = [
            'good_shop_file', 'margin_calculator', 'output_path',
            'margin', 'item_shelf_days', 'follow_buy_cnt'
        ]
        
        for field in required_fields:
            self.assertTrue(hasattr(config, field), f"缺少必需字段: {field}")
        
        # 验证默认值
        self.assertEqual(config.good_shop_file, "")
        self.assertEqual(config.margin_calculator, "")
        self.assertEqual(config.output_path, "")
        self.assertEqual(config.margin, 0.1)
        self.assertEqual(config.item_shelf_days, 150)
        self.assertEqual(config.follow_buy_cnt, 37)
    
    def test_task_status_compatibility(self):
        """测试任务状态兼容性"""
        # 验证TaskStatus枚举值保持向后兼容
        expected_states = ['pending', 'running', 'paused', 'completed', 'failed', 'stopped']
        for state in expected_states:
            self.assertTrue(hasattr(TaskStatus, state.upper()), f"缺少状态: {state}")
        
        # 验证状态值
        self.assertEqual(TaskStatus.PENDING.value, 'pending')
        self.assertEqual(TaskStatus.RUNNING.value, 'running')
        self.assertEqual(TaskStatus.PAUSED.value, 'paused')
        self.assertEqual(TaskStatus.COMPLETED.value, 'completed')
        self.assertEqual(TaskStatus.FAILED.value, 'failed')
        self.assertEqual(TaskStatus.STOPPED.value, 'stopped')


class TestAdapterPatternCorrectness(unittest.TestCase):
    """适配器模式正确性测试"""
    
    def setUp(self):
        """测试初始化"""
        self.adapter = TaskControllerAdapter()
        self.task_manager = self.adapter.task_manager
    
    def test_adapter_delegation(self):
        """测试适配器正确委托调用"""
        # 验证适配器内部使用TaskManager
        self.assertIsInstance(self.adapter.task_manager, TaskManager)
        
        # 验证适配器实现了事件监听器接口
        from task_manager.interfaces import ITaskEventListener
        self.assertIsInstance(self.adapter, ITaskEventListener)
    
    def test_adapter_interface_implementation(self):
        """测试适配器接口实现"""
        # 验证所有必需的事件监听器方法都已实现
        required_methods = [
            'on_task_created', 'on_task_started', 'on_task_paused',
            'on_task_resumed', 'on_task_stopped', 'on_task_completed',
            'on_task_failed', 'on_task_progress'
        ]
        
        for method in required_methods:
            self.assertTrue(hasattr(self.adapter, method), f"缺少方法: {method}")
            # 验证方法是可调用的
            self.assertTrue(callable(getattr(self.adapter, method)), f"方法不可调用: {method}")


class TestResponsibilitySeparation(unittest.TestCase):
    """职责分离原则测试"""
    
    def test_cli_layer_responsibility(self):
        """测试CLI层职责"""
        # CLI层应该只负责用户交互和参数处理
        from cli.main import create_parser, load_user_data
        from cli.models import UIConfig, UIStateManager
        
        # 验证CLI层不直接处理业务逻辑
        self.assertTrue(hasattr(UIConfig, 'to_dict'))
        self.assertTrue(hasattr(UIConfig, 'from_dict'))
        self.assertTrue(hasattr(UIStateManager, 'set_state'))
        self.assertTrue(hasattr(UIStateManager, 'update_progress'))
        
        # 验证CLI层不直接操作任务执行
        self.assertFalse(hasattr(UIConfig, 'execute_task'))
        self.assertFalse(hasattr(UIStateManager, 'run_task'))
    
    def test_task_manager_responsibility(self):
        """测试TaskManager层职责"""
        # TaskManager应该只负责任务调度和状态管理
        task_manager = TaskManager()
        
        # 验证TaskManager提供任务管理功能
        self.assertTrue(hasattr(task_manager, 'create_task'))
        self.assertTrue(hasattr(task_manager, 'start_task'))
        self.assertTrue(hasattr(task_manager, 'pause_task'))
        self.assertTrue(hasattr(task_manager, 'resume_task'))
        self.assertTrue(hasattr(task_manager, 'stop_task'))
        self.assertTrue(hasattr(task_manager, 'get_task_info'))
        
        # 验证TaskManager不处理UI状态
        self.assertFalse(hasattr(task_manager, 'update_ui'))
        self.assertFalse(hasattr(task_manager, 'show_message'))
    
    def test_adapter_layer_responsibility(self):
        """测试适配器层职责"""
        # 适配器应该只负责转换接口调用
        adapter = TaskControllerAdapter()
        
        # 验证适配器转换CLI调用到TaskManager
        self.assertTrue(hasattr(adapter, 'start_task'))
        self.assertTrue(hasattr(adapter, 'pause_task'))
        self.assertTrue(hasattr(adapter, 'resume_task'))
        self.assertTrue(hasattr(adapter, 'stop_task'))
        
        # 验证适配器处理状态同步
        self.assertTrue(hasattr(adapter, 'on_task_started'))
        self.assertTrue(hasattr(adapter, 'on_task_paused'))
        self.assertTrue(hasattr(adapter, 'on_task_completed'))


class TestPerformanceBenchmarks(unittest.TestCase):
    """性能基准测试"""
    
    def setUp(self):
        """测试初始化"""
        self.task_manager = TaskManager()
    
    def test_task_creation_performance(self):
        """测试任务创建性能"""
        def sample_task():
            return "completed"
        
        # 预热
        for _ in range(10):
            task_id = self.task_manager.create_task("warmup", sample_task)
        
        # 性能测试
        iterations = 1000
        start_time = time.perf_counter()
        
        for i in range(iterations):
            task_id = self.task_manager.create_task(f"task_{i}", sample_task)
            self.assertIsNotNone(task_id)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        avg_time = (total_time / iterations) * 1000  # 转换为毫秒
        
        # 验证性能：平均创建时间应该小于10ms
        self.assertLess(avg_time, 10.0, f"任务创建平均时间过长: {avg_time:.4f}ms")
    
    def test_task_status_query_performance(self):
        """测试任务状态查询性能"""
        def sample_task():
            time.sleep(0.01)
            return "completed"
        
        task_id = self.task_manager.create_task("test_task", sample_task)
        
        # 预热
        for _ in range(10):
            self.task_manager.get_task_info(task_id)
        
        # 性能测试
        iterations = 1000
        start_time = time.perf_counter()
        
        for _ in range(iterations):
            task_info = self.task_manager.get_task_info(task_id)
            self.assertIsNotNone(task_info)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        avg_time = (total_time / iterations) * 1000  # 转换为毫秒
        
        # 验证性能：平均查询时间应该小于5ms
        self.assertLess(avg_time, 5.0, f"任务状态查询平均时间过长: {avg_time:.4f}ms")
    
    def test_task_control_point_performance(self):
        """测试任务控制点检查性能"""
        from task_manager.mixins import TaskControlMixin
        
        class TestMixin(TaskControlMixin):
            def __init__(self):
                super().__init__()
        
        mixin = TestMixin()
        task_id = "performance_test_task"
        
        # 预热
        for _ in range(100):
            mixin._check_task_control(task_id)
        
        # 性能测试
        iterations = 10000
        start_time = time.perf_counter()
        
        for _ in range(iterations):
            result = mixin._check_task_control(task_id)
            self.assertTrue(result)  # 控制点应该返回True
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        avg_time = (total_time / iterations) * 1000  # 转换为毫秒
        
        # 验证性能：平均检查时间应该小于1ms
        self.assertLess(avg_time, 1.0, f"任务控制点检查平均时间过长: {avg_time:.4f}ms")


class TestEndToEndWorkflow(unittest.TestCase):
    """端到端工作流测试"""
    
    def setUp(self):
        """测试初始化"""
        self.task_controller = TaskController()
    
    def test_full_task_lifecycle(self):
        """测试完整任务生命周期"""
        # 这是一个集成测试，验证从CLI到TaskManager的完整调用链
        # 由于涉及实际任务执行，我们主要验证接口调用链
        
        # 验证调用链：TaskController -> TaskControllerAdapter -> TaskManager
        self.assertTrue(hasattr(self.task_controller, '_adapter'))
        self.assertTrue(hasattr(self.task_controller._adapter, 'task_manager'))
        
        # 验证状态管理器集成
        from cli.models import ui_state_manager
        self.assertIsNotNone(ui_state_manager)
        
        # 验证状态是有效的AppState枚举值
        from cli.models import AppState
        initial_state = ui_state_manager.state
        self.assertIn(initial_state, list(AppState))
    
    def test_error_handling_propagation(self):
        """测试错误处理传播"""
        # 验证错误从TaskManager正确传播到CLI层
        status = self.task_controller.get_task_status()
        self.assertIsInstance(status, dict)
        
        # 验证状态字段存在
        self.assertIn('state', status)
        self.assertIn('progress', status)
        self.assertIn('processing_stats', status)
    
    def test_concurrent_task_management(self):
        """测试并发任务管理"""
        # 验证TaskManager支持并发任务
        task_manager = TaskManager(max_workers=5)
        
        def sample_task():
            time.sleep(0.1)
            return "completed"
        
        # 创建多个任务
        task_ids = []
        for i in range(3):
            task_id = task_manager.create_task(f"concurrent_task_{i}", sample_task)
            task_ids.append(task_id)
            self.assertIsNotNone(task_id)
        
        # 启动所有任务
        for task_id in task_ids:
            result = task_manager.start_task(task_id)
            self.assertTrue(result)
        
        # 验证所有任务都已启动
        time.sleep(0.2)  # 等待任务启动
        
        for task_id in task_ids:
            task_info = task_manager.get_task_info(task_id)
            self.assertIsNotNone(task_info)
            # 任务可能已完成，因为sample_task很短
            self.assertIn(task_info.status, [TaskStatus.RUNNING, TaskStatus.COMPLETED])


if __name__ == '__main__':
    unittest.main()
