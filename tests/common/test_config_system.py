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
        
        assert config.log_level == "INFO"
        assert config.log_format == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        assert config.log_file is None
        assert config.max_log_file_size == 10 * 1024 * 1024  # 10MB in bytes
        assert config.backup_count == 5

    def test_logging_config_creation_custom(self):
        """测试自定义日志配置创建"""
        config = LoggingConfig(
            log_level="DEBUG",
            log_format="%(asctime)s [%(levelname)s] %(message)s",
            log_file="/var/log/app.log",
            max_log_file_size=50 * 1024 * 1024,  # 50MB in bytes
            backup_count=10
        )

        assert config.log_level == "DEBUG"
        assert config.log_format == "%(asctime)s [%(levelname)s] %(message)s"
        assert config.log_file == "/var/log/app.log"
        assert config.max_log_file_size == 50 * 1024 * 1024
        assert config.backup_count == 10

    def test_logging_config_level_validation(self):
        """测试日志级别验证"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            config = LoggingConfig(log_level=level)
            assert config.log_level == level

    def test_logging_config_format_customization(self):
        """测试日志格式自定义"""
        custom_formats = [
            "%(message)s",  # 仅消息
            "%(levelname)s: %(message)s",  # 级别和消息
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # 标准格式
            "[%(asctime)s] %(name)s.%(funcName)s:%(lineno)d - %(levelname)s - %(message)s"  # 详细格式
        ]

        for fmt in custom_formats:
            config = LoggingConfig(log_format=fmt)
            assert config.log_format == fmt

    def test_logging_config_file_size_validation(self):
        """测试日志文件大小验证"""
        # 测试不同文件大小（以字节为单位）
        test_sizes = [
            1024,  # 1KB
            1024 * 1024,  # 1MB
            10 * 1024 * 1024,  # 10MB (default)
            100 * 1024 * 1024,  # 100MB
            1024 * 1024 * 1024  # 1GB
        ]

        for size in test_sizes:
            config = LoggingConfig(max_log_file_size=size)
            assert config.max_log_file_size == size

    def test_logging_config_backup_count_validation(self):
        """测试备份文件数量验证"""
        valid_counts = [0, 1, 5, 10, 20, 50]

        for count in valid_counts:
            config = LoggingConfig(backup_count=count)
            assert config.backup_count == count

    def test_logging_config_file_path_handling(self):
        """测试日志文件路径处理"""
        file_paths = [
            None,  # 无文件路径（控制台输出）
            "app.log",  # 相对路径
            "/var/log/app.log",  # 绝对路径（Unix）
            "C:\\logs\\app.log",  # 绝对路径（Windows）
            "./logs/app.log",  # 相对路径（子目录）
            "../logs/app.log"  # 相对路径（上级目录）
        ]

        for path in file_paths:
            config = LoggingConfig(log_file=path)
            assert config.log_file == path


class TestPerformanceConfig:
    """性能配置测试"""

    def test_performance_config_creation_default(self):
        """测试默认性能配置创建"""
        config = PerformanceConfig()

        assert config.max_concurrent_stores == 5
        assert config.max_concurrent_products == 10
        assert config.enable_cache is True
        assert config.cache_ttl == 3600
        assert config.batch_size == 100

    def test_performance_config_creation_custom(self):
        """测试自定义性能配置创建"""
        config = PerformanceConfig(
            max_concurrent_stores=15,
            max_concurrent_products=30,
            enable_cache=False,
            cache_ttl=7200,
            batch_size=200
        )

        assert config.max_concurrent_stores == 15
        assert config.max_concurrent_products == 30
        assert config.enable_cache is False
        assert config.cache_ttl == 7200
        assert config.batch_size == 200
    
    def test_performance_config_concurrency_limits(self):
        """测试并发限制配置"""
        # 测试不同的并发级别
        concurrency_configs = [
            (1, 1, "最小并发"),
            (5, 10, "默认并发"),
            (15, 30, "中等并发"),
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
        # 测试缓存启用/禁用
        config_enabled = PerformanceConfig(enable_cache=True)
        assert config_enabled.enable_cache is True

        config_disabled = PerformanceConfig(enable_cache=False)
        assert config_disabled.enable_cache is False

        # 测试缓存TTL
        cache_ttl_configs = [
            (300, "5分钟缓存"),
            (1800, "30分钟缓存"),
            (3600, "1小时缓存"),
            (86400, "24小时缓存")
        ]

        for ttl, description in cache_ttl_configs:
            config = PerformanceConfig(cache_ttl=ttl)
            assert config.cache_ttl == ttl, f"测试失败: {description}"

    def test_performance_config_batch_processing(self):
        """测试批处理配置"""
        batch_sizes = [1, 10, 50, 100, 500, 1000]

        for size in batch_sizes:
            config = PerformanceConfig(batch_size=size)
            assert config.batch_size == size


class TestSystemConfigIntegration:
    """系统配置集成测试"""
    
    def test_logging_performance_config_combination(self):
        """测试日志和性能配置组合"""
        logging_config = LoggingConfig(
            log_level="DEBUG",
            log_format="%(asctime)s [%(levelname)s] %(message)s",
            log_file="debug.log"
        )

        performance_config = PerformanceConfig(
            max_concurrent_stores=1,  # 低并发，便于调试
            max_concurrent_products=2,
            enable_cache=False,  # 调试时禁用缓存
            batch_size=5  # 小批次便于调试
        )

        # 验证配置相互独立
        assert logging_config.log_level == "DEBUG"
        assert performance_config.max_concurrent_stores == 1
    
    def test_production_system_config(self):
        """测试生产环境系统配置"""
        logging_config = LoggingConfig(
            log_level="INFO",
            log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            log_file="/var/log/app.log",
            max_log_file_size=100 * 1024 * 1024,  # 100MB
            backup_count=10
        )

        performance_config = PerformanceConfig(
            max_concurrent_stores=10,
            max_concurrent_products=20,
            enable_cache=True,
            cache_ttl=3600,
            batch_size=100
        )

        # 验证生产环境配置
        assert logging_config.log_level == "INFO"
        assert logging_config.log_file == "/var/log/app.log"
        assert logging_config.max_log_file_size == 100 * 1024 * 1024
        assert performance_config.max_concurrent_stores == 10
        assert performance_config.enable_cache is True
    
    def test_development_system_config(self):
        """测试开发环境系统配置"""
        logging_config = LoggingConfig(
            log_level="DEBUG",
            log_format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            log_file=None,  # 开发环境不写文件
            max_log_file_size=10 * 1024 * 1024,
            backup_count=3
        )

        performance_config = PerformanceConfig(
            max_concurrent_stores=2,  # 开发环境低并发
            max_concurrent_products=5,
            enable_cache=True,
            cache_ttl=300,  # 短缓存，便于测试
            batch_size=10
        )

        # 验证开发环境配置
        assert logging_config.log_level == "DEBUG"
        assert logging_config.log_file is None
        assert performance_config.max_concurrent_stores == 2
        assert performance_config.cache_ttl == 300
    
    def test_high_performance_system_config(self):
        """测试高性能系统配置"""
        performance_config = PerformanceConfig(
            max_concurrent_stores=20,
            max_concurrent_products=50,
            enable_cache=True,
            cache_ttl=7200,  # 长缓存
            batch_size=500  # 大批次
        )

        # 对应的日志配置（性能优化）
        logging_config = LoggingConfig(
            log_level="WARNING",  # 只记录重要日志
            log_format="%(asctime)s [%(levelname)s] %(message)s",
            log_file="/var/log/performance.log",
            max_log_file_size=200 * 1024 * 1024,  # 200MB
            backup_count=5
        )

        assert performance_config.max_concurrent_stores == 20
        assert performance_config.batch_size == 500
        assert performance_config.enable_cache is True
        assert logging_config.log_level == "WARNING"


class TestSystemConfigValidation:
    """系统配置验证测试"""
    
    def test_logging_config_invalid_level(self):
        """测试无效日志级别处理"""
        # 测试有效日志级别
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            config = LoggingConfig(log_level=level)
            assert config.log_level == level
    
    def test_performance_config_boundary_values(self):
        """测试性能配置边界值"""
        # 测试最小值
        config_min = PerformanceConfig(
            max_concurrent_stores=1,  # 最小并发
            max_concurrent_products=1,
            enable_cache=False,  # 禁用缓存
            cache_ttl=0,  # 零缓存时间
            batch_size=1  # 最小批次
        )

        assert config_min.max_concurrent_stores == 1
        assert config_min.max_concurrent_products == 1
        assert config_min.enable_cache is False
        assert config_min.cache_ttl == 0
        assert config_min.batch_size == 1

        # 测试大值
        config_large = PerformanceConfig(
            max_concurrent_stores=100,
            max_concurrent_products=500,
            enable_cache=True,
            cache_ttl=86400 * 7,  # 一周缓存
            batch_size=10000  # 大批次
        )

        assert config_large.max_concurrent_stores == 100
        assert config_large.max_concurrent_products == 500
        assert config_large.enable_cache is True
        assert config_large.cache_ttl == 86400 * 7
        assert config_large.batch_size == 10000
    
    def test_logging_config_file_path_scenarios(self):
        """测试日志文件路径场景"""
        # 测试无文件路径（控制台输出）
        config_console = LoggingConfig(log_file=None)
        assert config_console.log_file is None

        # 测试有文件路径
        config_file = LoggingConfig(log_file="app.log")
        assert config_file.log_file == "app.log"
    
    def test_performance_config_various_combinations(self):
        """测试性能配置各种组合"""
        # 高并发小批次组合
        config1 = PerformanceConfig(
            max_concurrent_stores=50,  # 高并发
            max_concurrent_products=100,
            enable_cache=True,
            cache_ttl=1800,
            batch_size=10  # 小批次
        )

        assert config1.max_concurrent_stores == 50
        assert config1.batch_size == 10
        assert config1.enable_cache is True

        # 低并发大批次组合
        config2 = PerformanceConfig(
            max_concurrent_stores=2,  # 低并发
            max_concurrent_products=5,
            enable_cache=False,
            cache_ttl=0,
            batch_size=1000  # 大批次
        )

        assert config2.max_concurrent_stores == 2
        assert config2.batch_size == 1000
        assert config2.enable_cache is False


class TestSystemConfigSerialization:
    """系统配置序列化测试"""
    
    def test_logging_config_to_dict(self):
        """测试日志配置转换为字典"""
        config = LoggingConfig(
            log_level="WARNING",
            log_format="%(asctime)s [%(levelname)s] %(message)s",
            log_file="/tmp/app.log",
            max_log_file_size=25 * 1024 * 1024,  # 25MB in bytes
            backup_count=7
        )

        # 模拟转换为字典
        config_dict = {
            "log_level": config.log_level,
            "log_format": config.log_format,
            "log_file": config.log_file,
            "max_log_file_size": config.max_log_file_size,
            "backup_count": config.backup_count
        }

        assert config_dict["log_level"] == "WARNING"
        assert config_dict["log_format"] == "%(asctime)s [%(levelname)s] %(message)s"
        assert config_dict["log_file"] == "/tmp/app.log"
        assert config_dict["max_log_file_size"] == 25 * 1024 * 1024
    
    def test_performance_config_to_dict(self):
        """测试性能配置转换为字典"""
        config = PerformanceConfig(
            max_concurrent_stores=8,
            max_concurrent_products=15,
            enable_cache=True,
            cache_ttl=1800,
            batch_size=200
        )

        # 模拟转换为字典
        config_dict = {
            "max_concurrent_stores": config.max_concurrent_stores,
            "max_concurrent_products": config.max_concurrent_products,
            "enable_cache": config.enable_cache,
            "cache_ttl": config.cache_ttl,
            "batch_size": config.batch_size
        }

        assert config_dict["max_concurrent_stores"] == 8
        assert config_dict["max_concurrent_products"] == 15
        assert config_dict["enable_cache"] is True
        assert config_dict["cache_ttl"] == 1800
        assert config_dict["batch_size"] == 200


class TestSystemConfigUseCases:
    """系统配置使用案例测试"""
    
    def test_minimal_resource_config(self):
        """测试最小资源配置（适用于资源受限环境）"""
        logging_config = LoggingConfig(
            log_level="ERROR",  # 只记录错误
            log_format="%(levelname)s: %(message)s",  # 简化格式
            log_file=None,  # 不写文件节省空间
            max_log_file_size=1024 * 1024,  # 1MB
            backup_count=1
        )

        performance_config = PerformanceConfig(
            max_concurrent_stores=1,
            max_concurrent_products=2,
            enable_cache=False,  # 禁用缓存节省内存
            cache_ttl=300,  # 短缓存
            batch_size=5  # 小批次
        )

        assert logging_config.log_level == "ERROR"
        assert logging_config.log_file is None
        assert performance_config.max_concurrent_stores == 1
        assert performance_config.enable_cache is False
    
    def test_debugging_config(self):
        """测试调试配置"""
        logging_config = LoggingConfig(
            log_level="DEBUG",
            log_format="%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s",
            log_file="debug.log",
            max_log_file_size=50 * 1024 * 1024,  # 50MB for detailed logs
            backup_count=3
        )

        performance_config = PerformanceConfig(
            max_concurrent_stores=1,  # 单线程便于调试
            max_concurrent_products=1,
            enable_cache=False,  # 禁用缓存便于调试
            cache_ttl=60,  # 短缓存，便于测试
            batch_size=1  # 最小批次便于调试
        )

        assert logging_config.log_level == "DEBUG"
        assert "funcName" in logging_config.log_format
        assert performance_config.max_concurrent_stores == 1
        assert performance_config.enable_cache is False
    
    def test_monitoring_config(self):
        """测试监控配置"""
        logging_config = LoggingConfig(
            log_level="INFO",
            log_format="%(asctime)s [%(levelname)s] MONITOR - %(message)s",
            log_file="/var/log/monitoring.log",
            max_log_file_size=500 * 1024 * 1024,  # 500MB for monitoring
            backup_count=20  # 保留更多历史日志
        )

        performance_config = PerformanceConfig(
            max_concurrent_stores=15,
            max_concurrent_products=30,
            enable_cache=True,
            cache_ttl=1800,
            batch_size=100
        )

        assert "MONITOR" in logging_config.log_format
        assert logging_config.max_log_file_size == 500 * 1024 * 1024
        assert logging_config.backup_count == 20
        assert performance_config.max_concurrent_stores == 15
        assert performance_config.enable_cache is True
