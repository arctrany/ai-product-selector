"""
系统配置测试

测试系统级配置组件，包括日志配置、性能配置等
"""

import pytest
from common.config.system_config import LoggingConfig, PerformanceConfig


class TestLoggingConfig:
    """日志配置测试"""
    
    def test_logging_config_creation_default(self):
        """测试默认日志配置创建"""
        config = LoggingConfig()
        
        assert config.level == "INFO"
        assert config.console_output is True
        assert config.file_output is False
        assert config.log_file_path is None
        assert config.max_file_size_mb == 10
        assert config.backup_count == 5
        assert config.format_string == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    def test_logging_config_creation_custom(self):
        """测试自定义日志配置创建"""
        config = LoggingConfig(
            level="DEBUG",
            console_output=False,
            file_output=True,
            log_file_path="/var/log/app.log",
            max_file_size_mb=50,
            backup_count=10,
            format_string="%(asctime)s [%(levelname)s] %(message)s"
        )
        
        assert config.level == "DEBUG"
        assert config.console_output is False
        assert config.file_output is True
        assert config.log_file_path == "/var/log/app.log"
        assert config.max_file_size_mb == 50
        assert config.backup_count == 10
        assert config.format_string == "%(asctime)s [%(levelname)s] %(message)s"
    
    def test_logging_config_level_validation(self):
        """测试日志级别验证"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for level in valid_levels:
            config = LoggingConfig(level=level)
            assert config.level == level
    
    def test_logging_config_level_case_insensitive(self):
        """测试日志级别大小写不敏感"""
        test_cases = [
            ("debug", "DEBUG"),
            ("Info", "INFO"),
            ("WARNING", "WARNING"),
            ("error", "ERROR"),
            ("Critical", "CRITICAL")
        ]
        
        for input_level, expected_level in test_cases:
            config = LoggingConfig(level=input_level)
            assert config.level == expected_level
    
    def test_logging_config_file_size_validation(self):
        """测试日志文件大小验证"""
        # 测试有效文件大小
        valid_sizes = [1, 10, 50, 100, 1000]
        
        for size in valid_sizes:
            config = LoggingConfig(max_file_size_mb=size)
            assert config.max_file_size_mb == size
    
    def test_logging_config_backup_count_validation(self):
        """测试备份文件数量验证"""
        # 测试有效备份数量
        valid_counts = [0, 1, 5, 10, 20]
        
        for count in valid_counts:
            config = LoggingConfig(backup_count=count)
            assert config.backup_count == count
    
    def test_logging_config_output_combinations(self):
        """测试日志输出组合"""
        # 只输出到控制台
        config1 = LoggingConfig(console_output=True, file_output=False)
        assert config1.console_output is True
        assert config1.file_output is False
        
        # 只输出到文件
        config2 = LoggingConfig(console_output=False, file_output=True)
        assert config2.console_output is False
        assert config2.file_output is True
        
        # 同时输出到控制台和文件
        config3 = LoggingConfig(console_output=True, file_output=True)
        assert config3.console_output is True
        assert config3.file_output is True
        
        # 都不输出（虽然不常见，但应该支持）
        config4 = LoggingConfig(console_output=False, file_output=False)
        assert config4.console_output is False
        assert config4.file_output is False
    
    def test_logging_config_format_string_customization(self):
        """测试日志格式字符串自定义"""
        custom_formats = [
            "%(message)s",  # 仅消息
            "%(levelname)s: %(message)s",  # 级别和消息
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # 标准格式
            "[%(asctime)s] %(name)s.%(funcName)s:%(lineno)d - %(levelname)s - %(message)s"  # 详细格式
        ]
        
        for fmt in custom_formats:
            config = LoggingConfig(format_string=fmt)
            assert config.format_string == fmt
    
    def test_logging_config_file_path_handling(self):
        """测试日志文件路径处理"""
        file_paths = [
            None,  # 无文件路径
            "app.log",  # 相对路径
            "/var/log/app.log",  # 绝对路径（Unix）
            "C:\\logs\\app.log",  # 绝对路径（Windows）
            "./logs/app.log",  # 相对路径（子目录）
            "../logs/app.log"  # 相对路径（上级目录）
        ]
        
        for path in file_paths:
            config = LoggingConfig(log_file_path=path)
            assert config.log_file_path == path


class TestPerformanceConfig:
    """性能配置测试"""
    
    def test_performance_config_creation_default(self):
        """测试默认性能配置创建"""
        config = PerformanceConfig()
        
        assert config.max_concurrent_stores == 3
        assert config.max_concurrent_products == 5
        assert config.cache_ttl == 3600
        assert config.batch_size == 10
        assert config.request_timeout == 30
        assert config.retry_attempts == 3
        assert config.retry_delay == 1.0
        assert config.memory_limit_mb == 512
    
    def test_performance_config_creation_custom(self):
        """测试自定义性能配置创建"""
        config = PerformanceConfig(
            max_concurrent_stores=10,
            max_concurrent_products=20,
            cache_ttl=7200,
            batch_size=50,
            request_timeout=60,
            retry_attempts=5,
            retry_delay=2.0,
            memory_limit_mb=1024
        )
        
        assert config.max_concurrent_stores == 10
        assert config.max_concurrent_products == 20
        assert config.cache_ttl == 7200
        assert config.batch_size == 50
        assert config.request_timeout == 60
        assert config.retry_attempts == 5
        assert config.retry_delay == 2.0
        assert config.memory_limit_mb == 1024
    
    def test_performance_config_concurrency_limits(self):
        """测试并发限制配置"""
        # 测试不同的并发级别
        concurrency_configs = [
            (1, 1, "最小并发"),
            (3, 5, "默认并发"),
            (10, 20, "中等并发"),
            (50, 100, "高并发")
        ]
        
        for stores, products, description in concurrency_configs:
            config = PerformanceConfig(
                max_concurrent_stores=stores,
                max_concurrent_products=products
            )
            assert config.max_concurrent_stores == stores, f"测试失败: {description}"
            assert config.max_concurrent_products == products, f"测试失败: {description}"
    
    def test_performance_config_cache_settings(self):
        """测试缓存设置"""
        cache_configs = [
            (0, "禁用缓存"),
            (300, "5分钟缓存"),
            (1800, "30分钟缓存"),
            (3600, "1小时缓存"),
            (86400, "24小时缓存")
        ]
        
        for ttl, description in cache_configs:
            config = PerformanceConfig(cache_ttl=ttl)
            assert config.cache_ttl == ttl, f"测试失败: {description}"
    
    def test_performance_config_batch_processing(self):
        """测试批处理配置"""
        batch_sizes = [1, 5, 10, 25, 50, 100]
        
        for size in batch_sizes:
            config = PerformanceConfig(batch_size=size)
            assert config.batch_size == size
    
    def test_performance_config_timeout_settings(self):
        """测试超时设置"""
        timeout_configs = [
            (5, "快速超时"),
            (30, "标准超时"),
            (60, "长超时"),
            (120, "很长超时"),
            (300, "极长超时")
        ]
        
        for timeout, description in timeout_configs:
            config = PerformanceConfig(request_timeout=timeout)
            assert config.request_timeout == timeout, f"测试失败: {description}"
    
    def test_performance_config_retry_settings(self):
        """测试重试设置"""
        retry_configs = [
            (0, 0.0, "不重试"),
            (1, 0.5, "最小重试"),
            (3, 1.0, "标准重试"),
            (5, 2.0, "高重试"),
            (10, 5.0, "极高重试")
        ]
        
        for attempts, delay, description in retry_configs:
            config = PerformanceConfig(
                retry_attempts=attempts,
                retry_delay=delay
            )
            assert config.retry_attempts == attempts, f"测试失败: {description}"
            assert config.retry_delay == delay, f"测试失败: {description}"
    
    def test_performance_config_memory_limits(self):
        """测试内存限制"""
        memory_limits = [
            (128, "低内存"),
            (256, "标准内存"),
            (512, "中等内存"),
            (1024, "高内存"),
            (2048, "极高内存")
        ]
        
        for limit, description in memory_limits:
            config = PerformanceConfig(memory_limit_mb=limit)
            assert config.memory_limit_mb == limit, f"测试失败: {description}"


class TestSystemConfigIntegration:
    """系统配置集成测试"""
    
    def test_logging_performance_config_combination(self):
        """测试日志和性能配置组合"""
        logging_config = LoggingConfig(
            level="DEBUG",
            console_output=True,
            file_output=True,
            log_file_path="debug.log"
        )
        
        performance_config = PerformanceConfig(
            max_concurrent_stores=1,  # 低并发，便于调试
            request_timeout=60,  # 长超时，便于调试
            retry_attempts=1  # 少重试，便于调试
        )
        
        # 验证配置相互独立
        assert logging_config.level == "DEBUG"
        assert performance_config.max_concurrent_stores == 1
    
    def test_production_system_config(self):
        """测试生产环境系统配置"""
        logging_config = LoggingConfig(
            level="INFO",
            console_output=False,
            file_output=True,
            log_file_path="/var/log/app.log",
            max_file_size_mb=100,
            backup_count=10
        )
        
        performance_config = PerformanceConfig(
            max_concurrent_stores=5,
            max_concurrent_products=10,
            cache_ttl=3600,
            batch_size=20,
            request_timeout=30,
            retry_attempts=3,
            memory_limit_mb=1024
        )
        
        # 验证生产环境配置
        assert logging_config.level == "INFO"
        assert logging_config.console_output is False
        assert logging_config.file_output is True
        assert performance_config.max_concurrent_stores == 5
        assert performance_config.memory_limit_mb == 1024
    
    def test_development_system_config(self):
        """测试开发环境系统配置"""
        logging_config = LoggingConfig(
            level="DEBUG",
            console_output=True,
            file_output=False,  # 开发环境可能不需要文件日志
            format_string="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        
        performance_config = PerformanceConfig(
            max_concurrent_stores=2,  # 开发环境低并发
            max_concurrent_products=3,
            cache_ttl=300,  # 短缓存，便于测试
            request_timeout=60,  # 长超时，便于调试
            retry_attempts=1  # 少重试，快速失败
        )
        
        # 验证开发环境配置
        assert logging_config.level == "DEBUG"
        assert logging_config.console_output is True
        assert logging_config.file_output is False
        assert performance_config.max_concurrent_stores == 2
        assert performance_config.cache_ttl == 300
    
    def test_high_performance_system_config(self):
        """测试高性能系统配置"""
        performance_config = PerformanceConfig(
            max_concurrent_stores=20,
            max_concurrent_products=50,
            cache_ttl=7200,  # 长缓存
            batch_size=100,  # 大批次
            request_timeout=15,  # 短超时，快速处理
            retry_attempts=2,  # 适中重试
            memory_limit_mb=4096  # 高内存限制
        )
        
        # 对应的日志配置（性能优化）
        logging_config = LoggingConfig(
            level="WARNING",  # 只记录重要日志
            console_output=False,
            file_output=True,
            max_file_size_mb=200,  # 大日志文件
            backup_count=5
        )
        
        assert performance_config.max_concurrent_stores == 20
        assert performance_config.batch_size == 100
        assert performance_config.memory_limit_mb == 4096
        assert logging_config.level == "WARNING"


class TestSystemConfigValidation:
    """系统配置验证测试"""
    
    def test_logging_config_invalid_level(self):
        """测试无效日志级别处理"""
        # 注意：这里假设LoggingConfig会处理无效级别
        # 如果实际实现会抛出异常，需要用pytest.raises
        invalid_levels = ["INVALID", "TRACE", "VERBOSE", "", None]
        
        for level in invalid_levels:
            try:
                config = LoggingConfig(level=level)
                # 如果没有抛出异常，检查是否使用了默认值
                assert config.level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            except (ValueError, TypeError):
                # 如果抛出异常，这也是可接受的行为
                pass
    
    def test_performance_config_boundary_values(self):
        """测试性能配置边界值"""
        # 测试零值
        config_zero = PerformanceConfig(
            max_concurrent_stores=1,  # 最小并发
            max_concurrent_products=1,
            cache_ttl=0,  # 禁用缓存
            batch_size=1,  # 最小批次
            request_timeout=1,  # 最短超时
            retry_attempts=0,  # 不重试
            retry_delay=0.0,
            memory_limit_mb=64  # 最小内存
        )
        
        assert config_zero.max_concurrent_stores == 1
        assert config_zero.cache_ttl == 0
        assert config_zero.retry_attempts == 0
        
        # 测试大值
        config_large = PerformanceConfig(
            max_concurrent_stores=100,
            max_concurrent_products=500,
            cache_ttl=86400 * 7,  # 一周缓存
            batch_size=1000,
            request_timeout=3600,  # 1小时超时
            retry_attempts=20,
            retry_delay=60.0,  # 1分钟延迟
            memory_limit_mb=16384  # 16GB
        )
        
        assert config_large.max_concurrent_stores == 100
        assert config_large.cache_ttl == 86400 * 7
        assert config_large.memory_limit_mb == 16384
    
    def test_logging_config_file_output_without_path(self):
        """测试启用文件输出但未指定路径的情况"""
        config = LoggingConfig(
            file_output=True,
            log_file_path=None
        )
        
        # 应该能创建配置，但可能在实际使用时需要处理
        assert config.file_output is True
        assert config.log_file_path is None
    
    def test_performance_config_inconsistent_settings(self):
        """测试性能配置不一致设置"""
        # 例如：高并发但小批次
        config = PerformanceConfig(
            max_concurrent_stores=50,  # 高并发
            batch_size=1,  # 小批次
            memory_limit_mb=128  # 低内存
        )
        
        # 配置应该能创建，但可能不是最优的
        assert config.max_concurrent_stores == 50
        assert config.batch_size == 1
        assert config.memory_limit_mb == 128


class TestSystemConfigSerialization:
    """系统配置序列化测试"""
    
    def test_logging_config_to_dict(self):
        """测试日志配置转换为字典"""
        config = LoggingConfig(
            level="WARNING",
            console_output=False,
            file_output=True,
            log_file_path="/tmp/app.log",
            max_file_size_mb=25,
            backup_count=7
        )
        
        # 模拟转换为字典（假设有此方法）
        config_dict = {
            "level": config.level,
            "console_output": config.console_output,
            "file_output": config.file_output,
            "log_file_path": config.log_file_path,
            "max_file_size_mb": config.max_file_size_mb,
            "backup_count": config.backup_count,
            "format_string": config.format_string
        }
        
        assert config_dict["level"] == "WARNING"
        assert config_dict["console_output"] is False
        assert config_dict["file_output"] is True
        assert config_dict["log_file_path"] == "/tmp/app.log"
    
    def test_performance_config_to_dict(self):
        """测试性能配置转换为字典"""
        config = PerformanceConfig(
            max_concurrent_stores=8,
            max_concurrent_products=15,
            cache_ttl=1800,
            batch_size=30,
            request_timeout=45,
            retry_attempts=4,
            retry_delay=1.5,
            memory_limit_mb=768
        )
        
        # 模拟转换为字典
        config_dict = {
            "max_concurrent_stores": config.max_concurrent_stores,
            "max_concurrent_products": config.max_concurrent_products,
            "cache_ttl": config.cache_ttl,
            "batch_size": config.batch_size,
            "request_timeout": config.request_timeout,
            "retry_attempts": config.retry_attempts,
            "retry_delay": config.retry_delay,
            "memory_limit_mb": config.memory_limit_mb
        }
        
        assert config_dict["max_concurrent_stores"] == 8
        assert config_dict["cache_ttl"] == 1800
        assert config_dict["retry_delay"] == 1.5
        assert config_dict["memory_limit_mb"] == 768


class TestSystemConfigUseCases:
    """系统配置使用案例测试"""
    
    def test_minimal_resource_config(self):
        """测试最小资源配置（适用于资源受限环境）"""
        logging_config = LoggingConfig(
            level="ERROR",  # 只记录错误
            console_output=True,
            file_output=False  # 不写文件节省空间
        )
        
        performance_config = PerformanceConfig(
            max_concurrent_stores=1,
            max_concurrent_products=2,
            cache_ttl=300,  # 短缓存
            batch_size=5,  # 小批次
            memory_limit_mb=128  # 低内存
        )
        
        assert logging_config.level == "ERROR"
        assert performance_config.max_concurrent_stores == 1
        assert performance_config.memory_limit_mb == 128
    
    def test_debugging_config(self):
        """测试调试配置"""
        logging_config = LoggingConfig(
            level="DEBUG",
            console_output=True,
            file_output=True,
            log_file_path="debug.log",
            format_string="%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s"
        )
        
        performance_config = PerformanceConfig(
            max_concurrent_stores=1,  # 单线程便于调试
            max_concurrent_products=1,
            request_timeout=300,  # 长超时便于调试
            retry_attempts=1,  # 不重试，直接看到错误
            cache_ttl=60  # 短缓存，便于测试
        )
        
        assert logging_config.level == "DEBUG"
        assert "funcName" in logging_config.format_string
        assert performance_config.max_concurrent_stores == 1
        assert performance_config.request_timeout == 300
    
    def test_monitoring_config(self):
        """测试监控配置"""
        logging_config = LoggingConfig(
            level="INFO",
            console_output=False,
            file_output=True,
            log_file_path="/var/log/monitoring.log",
            max_file_size_mb=500,  # 大日志文件用于监控
            backup_count=20,  # 保留更多历史日志
            format_string="%(asctime)s [%(levelname)s] MONITOR - %(message)s"
        )
        
        performance_config = PerformanceConfig(
            max_concurrent_stores=10,
            max_concurrent_products=25,
            cache_ttl=1800,
            batch_size=50,
            request_timeout=30,
            retry_attempts=3,
            memory_limit_mb=2048
        )
        
        assert "MONITOR" in logging_config.format_string
        assert logging_config.max_file_size_mb == 500
        assert logging_config.backup_count == 20
        assert performance_config.max_concurrent_stores == 10
