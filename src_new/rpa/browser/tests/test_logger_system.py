"""
Unit tests for LoggerSystem implementation.

Tests the logging system functionality including:
- Structured logging with context
- Performance monitoring and metrics
- Multiple output formats and handlers
- Log rotation and file management
- Compatibility with original logger_config
"""

import unittest
import tempfile
import os
import json
import time
from unittest.mock import Mock, patch, MagicMock
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src_new.rpa.browser.implementations.logger_system import (
    StructuredLogger,
    PerformanceLogger,
    LoggerSystem,
    get_logger_system,
    get_logger,
    set_debug_mode
)


class TestStructuredLogger(unittest.TestCase):
    """Test StructuredLogger implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for log files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create logger with temporary log file
        self.log_file = os.path.join(self.temp_dir, 'test.log')
        self.logger = StructuredLogger(
            name='test_logger',
            log_file=self.log_file,
            level=logging.DEBUG
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up handlers to avoid resource leaks
        for handler in self.logger.logger.handlers[:]:
            handler.close()
            self.logger.logger.removeHandler(handler)
        
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_logger_initialization(self):
        """Test logger initialization."""
        self.assertEqual(self.logger.name, 'test_logger')
        self.assertEqual(self.logger.logger.level, logging.DEBUG)
        self.assertGreater(len(self.logger.logger.handlers), 0)
    
    def test_basic_logging(self):
        """Test basic logging functionality."""
        # Test different log levels
        self.logger.debug('Debug message')
        self.logger.info('Info message')
        self.logger.warning('Warning message')
        self.logger.error('Error message')
        self.logger.critical('Critical message')
        
        # Verify log file was created
        self.assertTrue(os.path.exists(self.log_file))
        
        # Read log file and verify content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        self.assertIn('Debug message', log_content)
        self.assertIn('Info message', log_content)
        self.assertIn('Warning message', log_content)
        self.assertIn('Error message', log_content)
        self.assertIn('Critical message', log_content)
    
    def test_structured_logging_with_context(self):
        """Test structured logging with context information."""
        # Set context
        context = {
            'user_id': '12345',
            'session_id': 'abc-def-ghi',
            'operation': 'test_operation'
        }
        
        self.logger.set_context(context)
        
        # Log with context
        self.logger.info('Operation completed', extra={
            'duration': 1.5,
            'status': 'success'
        })
        
        # Verify log file contains context information
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        self.assertIn('user_id', log_content)
        self.assertIn('12345', log_content)
        self.assertIn('session_id', log_content)
        self.assertIn('duration', log_content)
    
    def test_json_format_logging(self):
        """Test JSON format logging."""
        # Create logger with JSON format
        json_log_file = os.path.join(self.temp_dir, 'test_json.log')
        json_logger = StructuredLogger(
            name='json_logger',
            log_file=json_log_file,
            format_type='json'
        )
        
        try:
            # Log structured data
            json_logger.info('Test message', extra={
                'data': {'key': 'value'},
                'count': 42,
                'success': True
            })
            
            # Verify JSON format
            with open(json_log_file, 'r') as f:
                log_lines = f.readlines()
            
            self.assertGreater(len(log_lines), 0)
            
            # Parse first log line as JSON
            log_entry = json.loads(log_lines[0])
            
            self.assertIn('message', log_entry)
            self.assertIn('timestamp', log_entry)
            self.assertIn('level', log_entry)
            self.assertEqual(log_entry['message'], 'Test message')
            self.assertEqual(log_entry['data']['key'], 'value')
            self.assertEqual(log_entry['count'], 42)
            self.assertTrue(log_entry['success'])
            
        finally:
            # Clean up handlers
            for handler in json_logger.logger.handlers[:]:
                handler.close()
                json_logger.logger.removeHandler(handler)
    
    def test_context_manager(self):
        """Test logger as context manager."""
        with self.logger.context({'operation': 'context_test'}):
            self.logger.info('Inside context')
        
        # Context should be cleared after exiting
        self.logger.info('Outside context')
        
        # Verify log content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Should contain context information for first message
        lines = log_content.strip().split('\n')
        self.assertGreater(len(lines), 1)
    
    def test_exception_logging(self):
        """Test exception logging."""
        try:
            raise ValueError("Test exception")
        except ValueError:
            self.logger.exception('An error occurred')
        
        # Verify exception information is logged
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        self.assertIn('An error occurred', log_content)
        self.assertIn('ValueError', log_content)
        self.assertIn('Test exception', log_content)
        self.assertIn('Traceback', log_content)
    
    def test_log_rotation(self):
        """Test log file rotation."""
        # Create logger with small max file size for testing
        rotating_log_file = os.path.join(self.temp_dir, 'rotating.log')
        rotating_logger = StructuredLogger(
            name='rotating_logger',
            log_file=rotating_log_file,
            max_file_size=1024,  # 1KB
            backup_count=3
        )
        
        try:
            # Generate enough log data to trigger rotation
            for i in range(100):
                rotating_logger.info(f'Log message {i} with some additional content to increase size')
            
            # Check if rotation occurred (backup files should exist)
            backup_files = [f for f in os.listdir(self.temp_dir) if f.startswith('rotating.log.')]
            self.assertGreater(len(backup_files), 0)
            
        finally:
            # Clean up handlers
            for handler in rotating_logger.logger.handlers[:]:
                handler.close()
                rotating_logger.logger.removeHandler(handler)
    
    def test_multiple_handlers(self):
        """Test logger with multiple handlers."""
        # Create logger with both file and console handlers
        multi_logger = StructuredLogger(
            name='multi_logger',
            log_file=os.path.join(self.temp_dir, 'multi.log'),
            console_output=True
        )
        
        try:
            # Should have both file and console handlers
            self.assertGreaterEqual(len(multi_logger.logger.handlers), 2)
            
            # Log a message
            multi_logger.info('Multi-handler test')
            
            # Verify file handler worked
            with open(os.path.join(self.temp_dir, 'multi.log'), 'r') as f:
                log_content = f.read()
            
            self.assertIn('Multi-handler test', log_content)
            
        finally:
            # Clean up handlers
            for handler in multi_logger.logger.handlers[:]:
                handler.close()
                multi_logger.logger.removeHandler(handler)


class TestPerformanceLogger(unittest.TestCase):
    """Test PerformanceLogger implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for log files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create performance logger
        self.perf_logger = PerformanceLogger(
            name='perf_logger',
            log_file=os.path.join(self.temp_dir, 'perf.log')
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up handlers
        for handler in self.perf_logger.logger.handlers[:]:
            handler.close()
            self.perf_logger.logger.removeHandler(handler)
        
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_operation_timing(self):
        """Test operation timing functionality."""
        # Start timing an operation
        self.perf_logger.start_operation('test_operation')
        
        # Simulate some work
        time.sleep(0.1)
        
        # End timing
        duration = self.perf_logger.end_operation('test_operation')
        
        # Verify duration is reasonable
        self.assertGreater(duration, 0.05)  # At least 50ms
        self.assertLess(duration, 0.5)      # Less than 500ms
    
    def test_operation_context_manager(self):
        """Test operation timing using context manager."""
        with self.perf_logger.time_operation('context_operation') as timer:
            time.sleep(0.05)
            # Can access timer within context
            self.assertIsNotNone(timer)
        
        # Operation should be automatically logged
        log_file = os.path.join(self.temp_dir, 'perf.log')
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        self.assertIn('context_operation', log_content)
        self.assertIn('completed', log_content)
    
    def test_performance_metrics(self):
        """Test performance metrics collection."""
        # Record some metrics
        self.perf_logger.record_metric('cpu_usage', 75.5)
        self.perf_logger.record_metric('memory_usage', 1024)
        self.perf_logger.record_metric('response_time', 0.25)
        
        # Get metrics
        metrics = self.perf_logger.get_metrics()
        
        self.assertIn('cpu_usage', metrics)
        self.assertIn('memory_usage', metrics)
        self.assertIn('response_time', metrics)
        
        self.assertEqual(metrics['cpu_usage'][-1], 75.5)
        self.assertEqual(metrics['memory_usage'][-1], 1024)
        self.assertEqual(metrics['response_time'][-1], 0.25)
    
    def test_metrics_statistics(self):
        """Test metrics statistics calculation."""
        # Record multiple values for a metric
        values = [10, 20, 30, 40, 50]
        for value in values:
            self.perf_logger.record_metric('test_metric', value)
        
        # Get statistics
        stats = self.perf_logger.get_metric_stats('test_metric')
        
        self.assertEqual(stats['count'], 5)
        self.assertEqual(stats['min'], 10)
        self.assertEqual(stats['max'], 50)
        self.assertEqual(stats['avg'], 30)
        self.assertEqual(stats['sum'], 150)
    
    def test_performance_report(self):
        """Test performance report generation."""
        # Record some operations and metrics
        with self.perf_logger.time_operation('operation1'):
            time.sleep(0.02)
        
        with self.perf_logger.time_operation('operation2'):
            time.sleep(0.03)
        
        self.perf_logger.record_metric('requests_per_second', 100)
        self.perf_logger.record_metric('requests_per_second', 120)
        
        # Generate report
        report = self.perf_logger.generate_report()
        
        self.assertIn('operations', report)
        self.assertIn('metrics', report)
        self.assertIn('operation1', report['operations'])
        self.assertIn('operation2', report['operations'])
        self.assertIn('requests_per_second', report['metrics'])
    
    def test_threshold_alerts(self):
        """Test performance threshold alerts."""
        # Set threshold for a metric
        self.perf_logger.set_threshold('response_time', max_value=0.5)
        
        # Record values below threshold (should not alert)
        self.perf_logger.record_metric('response_time', 0.3)
        
        # Record value above threshold (should alert)
        with patch.object(self.perf_logger, '_log_threshold_alert') as mock_alert:
            self.perf_logger.record_metric('response_time', 0.8)
            mock_alert.assert_called_once()
    
    def test_operation_nesting(self):
        """Test nested operation timing."""
        with self.perf_logger.time_operation('parent_operation'):
            time.sleep(0.01)
            
            with self.perf_logger.time_operation('child_operation'):
                time.sleep(0.01)
            
            time.sleep(0.01)
        
        # Both operations should be recorded
        log_file = os.path.join(self.temp_dir, 'perf.log')
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        self.assertIn('parent_operation', log_content)
        self.assertIn('child_operation', log_content)


class TestLoggerSystem(unittest.TestCase):
    """Test LoggerSystem implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for log files
        self.temp_dir = tempfile.mkdtemp()
        
        # Create logger system
        self.logger_system = LoggerSystem(
            log_directory=self.temp_dir,
            default_level=logging.INFO
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up logger system
        self.logger_system.shutdown()
        
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_logger_creation(self):
        """Test logger creation and management."""
        # Create different types of loggers
        app_logger = self.logger_system.get_logger('app')
        db_logger = self.logger_system.get_logger('database')
        api_logger = self.logger_system.get_logger('api')
        
        # Verify loggers are different instances
        self.assertNotEqual(app_logger, db_logger)
        self.assertNotEqual(db_logger, api_logger)
        
        # Verify same name returns same instance
        app_logger2 = self.logger_system.get_logger('app')
        self.assertEqual(app_logger, app_logger2)
    
    def test_performance_logger_creation(self):
        """Test performance logger creation."""
        perf_logger = self.logger_system.get_performance_logger('performance')
        
        self.assertIsInstance(perf_logger, PerformanceLogger)
        
        # Test performance logging
        with perf_logger.time_operation('test_op'):
            time.sleep(0.01)
        
        # Verify performance log file exists
        perf_log_file = os.path.join(self.temp_dir, 'performance.log')
        self.assertTrue(os.path.exists(perf_log_file))
    
    def test_global_configuration(self):
        """Test global logger configuration."""
        # Configure all loggers
        self.logger_system.configure_all_loggers(
            level=logging.DEBUG,
            format_type='json'
        )
        
        # Create new logger after configuration
        test_logger = self.logger_system.get_logger('configured_test')
        
        # Verify configuration was applied
        self.assertEqual(test_logger.logger.level, logging.DEBUG)
    
    def test_context_propagation(self):
        """Test context propagation across loggers."""
        # Set global context
        global_context = {
            'request_id': 'req-123',
            'user_id': 'user-456'
        }
        
        self.logger_system.set_global_context(global_context)
        
        # Create loggers and verify they inherit context
        logger1 = self.logger_system.get_logger('service1')
        logger2 = self.logger_system.get_logger('service2')
        
        logger1.info('Service 1 message')
        logger2.info('Service 2 message')
        
        # Verify context appears in both log files
        for service in ['service1', 'service2']:
            log_file = os.path.join(self.temp_dir, f'{service}.log')
            with open(log_file, 'r') as f:
                log_content = f.read()
            
            self.assertIn('req-123', log_content)
            self.assertIn('user-456', log_content)
    
    def test_log_aggregation(self):
        """Test log aggregation functionality."""
        # Create multiple loggers and log messages
        loggers = []
        for i in range(3):
            logger = self.logger_system.get_logger(f'service_{i}')
            loggers.append(logger)
            logger.info(f'Message from service {i}')
        
        # Aggregate logs
        aggregated_logs = self.logger_system.aggregate_logs(
            time_range=(time.time() - 60, time.time())
        )
        
        # Verify aggregation contains messages from all services
        self.assertGreater(len(aggregated_logs), 0)
        
        # Check that messages from different services are included
        log_text = '\n'.join([log['message'] for log in aggregated_logs])
        for i in range(3):
            self.assertIn(f'Message from service {i}', log_text)
    
    def test_log_filtering(self):
        """Test log filtering functionality."""
        # Create logger and log different levels
        test_logger = self.logger_system.get_logger('filter_test')
        
        test_logger.debug('Debug message')
        test_logger.info('Info message')
        test_logger.warning('Warning message')
        test_logger.error('Error message')
        
        # Filter logs by level
        error_logs = self.logger_system.filter_logs(
            logger_name='filter_test',
            min_level=logging.ERROR
        )
        
        # Should only contain error message
        self.assertEqual(len(error_logs), 1)
        self.assertIn('Error message', error_logs[0]['message'])
        
        # Filter logs by content
        info_logs = self.logger_system.filter_logs(
            logger_name='filter_test',
            contains='Info'
        )
        
        self.assertEqual(len(info_logs), 1)
        self.assertIn('Info message', info_logs[0]['message'])
    
    def test_system_shutdown(self):
        """Test logger system shutdown."""
        # Create some loggers
        logger1 = self.logger_system.get_logger('shutdown_test1')
        logger2 = self.logger_system.get_logger('shutdown_test2')
        
        # Log some messages
        logger1.info('Before shutdown')
        logger2.info('Before shutdown')
        
        # Shutdown system
        self.logger_system.shutdown()
        
        # Verify handlers are closed (no exceptions should occur)
        # This is mainly to ensure proper cleanup
        self.assertTrue(True)  # If we get here, shutdown worked


class TestLoggerSystemIntegration(unittest.TestCase):
    """Test logger system integration and compatibility."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_global_logger_functions(self):
        """Test global logger functions."""
        # Test get_logger_system
        system1 = get_logger_system()
        system2 = get_logger_system()
        
        # Should return same instance (singleton)
        self.assertEqual(system1, system2)
        
        # Test get_logger
        logger1 = get_logger('global_test')
        logger2 = get_logger('global_test')
        
        # Should return same logger instance
        self.assertEqual(logger1, logger2)
        
        # Test set_debug_mode
        set_debug_mode(True)
        debug_logger = get_logger('debug_test')
        self.assertEqual(debug_logger.logger.level, logging.DEBUG)
        
        set_debug_mode(False)
        info_logger = get_logger('info_test')
        self.assertEqual(info_logger.logger.level, logging.INFO)
    
    def test_original_logger_compatibility(self):
        """Test compatibility with original logger_config."""
        # This test ensures our new system can work alongside
        # or replace the original logger_config module
        
        # Test that we can create loggers with similar interface
        logger = get_logger('compatibility_test')
        
        # Test basic logging methods exist and work
        logger.debug('Debug message')
        logger.info('Info message')
        logger.warning('Warning message')
        logger.error('Error message')
        logger.critical('Critical message')
        
        # Test exception logging
        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.exception('Exception occurred')
        
        # If we get here without errors, compatibility is maintained
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main(verbosity=2)