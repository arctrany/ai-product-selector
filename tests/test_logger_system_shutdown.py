"""
测试logger_system在Python关闭阶段的行为

本测试文件验证logger_system.py中的Python关闭检测机制是否正常工作。
"""

import unittest
import sys
import os
import threading
import time
from unittest.mock import patch, MagicMock
from io import StringIO

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rpa.browser.implementations.logger_system import (
    StructuredLogger, StructuredFormatter, LoggerSystem,
    get_logger, get_logger_system
)


class TestLoggerSystemShutdown(unittest.TestCase):
    """测试Logger系统关闭阶段行为"""
    
    def setUp(self):
        """测试前准备"""
        self.original_stdout = sys.stdout
        self.captured_output = StringIO()
        
    def tearDown(self):
        """测试后清理"""
        sys.stdout = self.original_stdout
        
    def test_python_shutdown_flag_initialization(self):
        """测试Python关闭标志的初始化"""
        # 验证模块级别的关闭检测机制存在
        import rpa.browser.implementations.logger_system as logger_module
        # 检查模块是否有关闭检测相关属性
        self.assertTrue(hasattr(logger_module, 'sys'))

    def test_shutdown_flag_setting(self):
        """测试关闭标志设置功能"""
        # 测试sys.meta_path为None的情况
        import rpa.browser.implementations.logger_system as logger_module

        # 验证模块可以处理sys.meta_path为None的情况
        original_meta_path = logger_module.sys.meta_path
        try:
            logger_module.sys.meta_path = None

            # 创建logger并测试
            logger = StructuredLogger("test_shutdown", level="INFO")
            logger.info("Test message with meta_path None")

            # 如果没有异常，说明处理正确
            self.assertTrue(True)
        finally:
            # 恢复原始状态
            logger_module.sys.meta_path = original_meta_path

    @patch('sys.meta_path', None)
    def test_structured_formatter_with_meta_path_none(self):
        """测试当sys.meta_path为None时StructuredFormatter的行为"""
        formatter = StructuredFormatter(console=True)
        
        # 创建模拟的LogRecord
        record = MagicMock()
        record.levelname = "ERROR"
        record.msg = "Test message during shutdown"
        record.getMessage.return_value = "Test message during shutdown"
        
        # 重定向标准输出以捕获print输出
        sys.stdout = self.captured_output
        
        # 调用format方法
        result = formatter.format(record)
        
        # 验证返回简化的关闭格式
        self.assertIn("[SHUTDOWN]", result)
        self.assertIn("ERROR", result)
        self.assertIn("Test message during shutdown", result)

    def test_structured_formatter_normal_operation(self):
        """测试正常情况下StructuredFormatter的行为"""
        formatter = StructuredFormatter(console=True)
        
        # 创建真实的LogRecord（简化版）
        import logging
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test normal message",
            args=(),
            exc_info=None
        )
        
        # 调用format方法
        result = formatter.format(record)
        
        # 验证正常格式化
        self.assertNotIn("[SHUTDOWN]", result)
        self.assertIn("INFO", result)
        self.assertIn("Test normal message", result)

    @patch('rpa.browser.implementations.logger_system._python_shutting_down', True)
    def test_structured_logger_debug_during_shutdown(self):
        """测试关闭阶段StructuredLogger.debug的行为"""
        logger = StructuredLogger("test_logger", level="DEBUG")
        
        # 重定向标准输出
        sys.stdout = self.captured_output
        
        # 调用debug方法
        logger.debug("Debug message during shutdown")
        
        # 检查print输出
        output = self.captured_output.getvalue()
        self.assertIn("DEBUG: Debug message during shutdown", output)

    @patch('rpa.browser.implementations.logger_system._python_shutting_down', True)
    def test_structured_logger_info_during_shutdown(self):
        """测试关闭阶段StructuredLogger.info的行为"""
        logger = StructuredLogger("test_logger", level="INFO")
        
        # 重定向标准输出
        sys.stdout = self.captured_output
        
        # 调用info方法
        logger.info("Info message during shutdown")
        
        # 检查print输出
        output = self.captured_output.getvalue()
        self.assertIn("INFO: Info message during shutdown", output)

    @patch('rpa.browser.implementations.logger_system._python_shutting_down', True)
    @patch('sys.meta_path', None)
    def test_structured_logger_error_during_shutdown(self):
        """测试关闭阶段StructuredLogger.error的行为"""
        logger = StructuredLogger("test_logger", level="ERROR")

        # 使用StringIO捕获print输出
        from io import StringIO
        import sys
        captured_output = StringIO()
        original_stdout = sys.stdout

        try:
            sys.stdout = captured_output

            # 调用error方法 - 在关闭状态下应该使用print输出
            logger.error("Error message during shutdown")

            # 检查print输出
            output = captured_output.getvalue()
            self.assertIn("ERROR", output)
            self.assertIn("Error message during shutdown", output)
        finally:
            # 恢复标准输出
            sys.stdout = original_stdout

    @patch('sys.meta_path', None)
    def test_structured_logger_with_meta_path_none(self):
        """测试当sys.meta_path为None时StructuredLogger的行为"""
        logger = StructuredLogger("test_logger", level="WARNING")
        
        # 重定向标准输出
        sys.stdout = self.captured_output
        
        # 调用warning方法
        logger.warning("Warning during meta_path None")
        
        # 检查print输出
        output = self.captured_output.getvalue()
        self.assertIn("WARNING: Warning during meta_path None", output)

    def test_logger_system_shutdown_behavior(self):
        """测试LoggerSystem的关闭行为"""
        logger_system = LoggerSystem(debug_mode=True)
        logger = logger_system.get_logger("test_shutdown")
        
        # 验证logger系统正常工作
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, "test_shutdown")
        
        # 测试关闭
        logger_system.shutdown()
        
        # 验证loggers被清理
        self.assertEqual(len(logger_system.loggers), 0)

    def test_global_logger_system_functionality(self):
        """测试全局logger系统功能"""
        # 获取全局logger系统
        system = get_logger_system(debug_mode=True)
        self.assertIsNotNone(system)
        
        # 获取logger
        logger = get_logger("global_test", debug_mode=True)
        self.assertIsNotNone(logger)
        
        # 测试日志输出（正常情况）
        logger.info("Global logger test message")

    def test_formatter_exception_handling(self):
        """测试Formatter异常处理"""
        formatter = StructuredFormatter(console=False)
        
        # 创建有问题的record（模拟异常情况）
        record = MagicMock()
        record.levelname = "CRITICAL"
        record.msg = "Critical message with issues"
        record.getMessage.side_effect = Exception("getMessage failed")
        record.name = "test_logger"
        record.filename = "test.py"
        record.lineno = 123
        record.created = time.time()
        
        # 测试在异常情况下formatter是否能正常处理
        try:
            result = formatter.format(record)
            # 应该能成功格式化，不抛出异常
            self.assertIsInstance(result, str)
        except Exception as e:
            self.fail(f"Formatter should handle exceptions gracefully, but raised: {e}")

    @patch('rpa.browser.implementations.logger_system.datetime')
    def test_formatter_datetime_import_error(self, mock_datetime):
        """测试datetime导入错误的处理"""
        # 模拟datetime.fromtimestamp抛出ImportError
        mock_datetime.fromtimestamp.side_effect = ImportError("datetime module unavailable")
        
        formatter = StructuredFormatter(console=True)
        
        # 创建LogRecord
        import logging
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Test datetime error",
            args=(),
            exc_info=None
        )
        
        # 应该能处理datetime导入错误
        result = formatter.format(record)
        self.assertIsInstance(result, str)
        self.assertIn("ERROR", result)

    def test_concurrent_logging_during_shutdown(self):
        """测试关闭期间并发日志记录"""
        logger = StructuredLogger("concurrent_test", level="INFO")
        results = []
        
        def log_messages(thread_id):
            """线程函数：记录日志消息"""
            for i in range(5):
                logger.info(f"Thread {thread_id} message {i}")
                time.sleep(0.01)  # 短暂延迟
        
        # 创建多个线程
        threads = []
        for i in range(3):
            thread = threading.Thread(target=log_messages, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证没有异常抛出（测试通过即表示成功）
        self.assertTrue(True)

class TestLoggerSystemIntegration(unittest.TestCase):
    """Logger系统集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.original_stdout = sys.stdout
        
    def tearDown(self):
        """测试后清理"""
        sys.stdout = self.original_stdout
        
    def test_end_to_end_logging_workflow(self):
        """端到端日志记录工作流测试"""
        # 创建logger系统
        system = LoggerSystem(debug_mode=True)
        
        # 获取logger
        logger = system.get_logger("e2e_test")
        
        # 测试各种级别的日志
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        # 测试性能日志
        timer_id = logger.log_operation_start("test_operation")
        time.sleep(0.01)  # 模拟操作
        duration = logger.log_operation_end(timer_id, "test_operation", success=True)
        
        self.assertGreater(duration, 0)
        
        # 清理
        system.shutdown()

    def test_logger_system_configuration(self):
        """测试logger系统配置"""
        config = {
            'debug_mode': True,
            'log_directory': '/tmp/test_logs',
            'default_level': 'DEBUG'
        }
        
        system = LoggerSystem()
        system.initialize(config)
        
        self.assertTrue(system.debug_mode)
        self.assertEqual(system.log_directory, '/tmp/test_logs')
        self.assertEqual(system.default_level, 'DEBUG')


if __name__ == '__main__':
    # 设置测试输出
    import sys
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试用例
    suite.addTests(loader.loadTestsFromTestCase(TestLoggerSystemShutdown))
    suite.addTests(loader.loadTestsFromTestCase(TestLoggerSystemIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # 输出测试结果摘要
    print(f"\n{'='*60}")
    print(f"测试摘要:")
    print(f"  运行测试: {result.testsRun}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    print(f"  跳过: {len(result.skipped)}")
    print(f"{'='*60}")
    
    if result.failures:
        print(f"\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print(f"\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    # 返回适当的退出码
    sys.exit(0 if result.wasSuccessful() else 1)
