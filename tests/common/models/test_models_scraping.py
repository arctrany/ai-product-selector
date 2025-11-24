"""
抓取模型测试

测试 common/models/scraping_result.py 中定义的抓取相关数据模型
"""

import pytest
from datetime import datetime
from common.models.scraping_result import ScrapingResult, ScrapingStatus
from common.services.scraping_orchestrator import ScrapingMode


class TestScrapingStatus:
    """抓取状态枚举测试"""
    
    def test_scraping_status_values(self):
        """测试抓取状态枚举值"""
        assert ScrapingStatus.SUCCESS.value == "success"
        assert ScrapingStatus.FAILED.value == "failed"
        assert ScrapingStatus.ERROR.value == "error"
        assert ScrapingStatus.TIMEOUT.value == "timeout"
        assert ScrapingStatus.CANCELLED.value == "cancelled"
    
    def test_scraping_status_members(self):
        """测试抓取状态枚举成员"""
        expected_members = {"SUCCESS", "FAILED", "ERROR", "TIMEOUT", "CANCELLED"}
        actual_members = {member.name for member in ScrapingStatus}
        assert actual_members == expected_members
    
    def test_scraping_status_string_conversion(self):
        """测试状态字符串转换"""
        assert str(ScrapingStatus.SUCCESS) == "ScrapingStatus.SUCCESS"
        assert ScrapingStatus.SUCCESS.value == "success"


class TestScrapingMode:
    """抓取模式枚举测试"""
    
    def test_scraping_mode_values(self):
        """测试抓取模式枚举值"""
        assert ScrapingMode.STORE_ANALYSIS.value == "store_analysis"
        assert ScrapingMode.PRODUCT_ATTRIBUTES.value == "product_attributes"
        assert ScrapingMode.DETECT_COMPETITORS.value == "detect_competitors"
        assert ScrapingMode.PRODUCT_DATA.value == "product_data"
    
    def test_scraping_mode_members(self):
        """测试抓取模式枚举成员"""
        expected_members = {"STORE_ANALYSIS", "PRODUCT_ATTRIBUTES", "DETECT_COMPETITORS", "PRODUCT_DATA"}
        actual_members = {member.name for member in ScrapingMode}
        assert actual_members == expected_members


class TestScrapingResult:
    """抓取结果模型测试"""
    
    def test_scraping_result_creation_success(self):
        """测试成功抓取结果创建"""
        data = {"products": ["product1", "product2"], "count": 2}
        result = ScrapingResult(
            success=True,
            data=data,
            execution_time=1.5
        )
        
        assert result.success is True
        assert result.data == data
        assert result.execution_time == 1.5
        assert result.error_message is None
        assert result.status == ScrapingStatus.SUCCESS
        assert isinstance(result.metadata, dict)
        assert isinstance(result.timestamp, datetime)
    
    def test_scraping_result_creation_failure(self):
        """测试失败抓取结果创建"""
        result = ScrapingResult(
            success=False,
            data={},
            error_message="网络连接超时"
        )
        
        assert result.success is False
        assert result.data == {}
        assert result.error_message == "网络连接超时"
        assert result.status == ScrapingStatus.FAILED
        assert result.execution_time is None
    
    def test_scraping_result_post_init_status_setting(self):
        """测试post_init自动状态设置"""
        # 测试成功状态
        success_result = ScrapingResult(success=True, data={"test": "data"})
        assert success_result.status == ScrapingStatus.SUCCESS
        
        # 测试超时状态
        timeout_result = ScrapingResult(
            success=False,
            data={},
            error_message="Connection timeout occurred"
        )
        assert timeout_result.status == ScrapingStatus.TIMEOUT
        
        # 测试一般错误状态
        error_result = ScrapingResult(
            success=False,
            data={},
            error_message="Failed to parse HTML"
        )
        assert error_result.status == ScrapingStatus.ERROR
        
        # 测试失败状态（无错误消息）
        failed_result = ScrapingResult(success=False, data={})
        assert failed_result.status == ScrapingStatus.FAILED
    
    def test_scraping_result_to_dict(self):
        """测试转换为字典"""
        timestamp = datetime.now()
        result = ScrapingResult(
            success=True,
            data={"key": "value"},
            execution_time=2.5,
            metadata={"scraper": "ozon"},
            timestamp=timestamp
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["success"] is True
        assert result_dict["data"] == {"key": "value"}
        assert result_dict["execution_time"] == 2.5
        assert result_dict["status"] == "success"
        assert result_dict["metadata"] == {"scraper": "ozon"}
        assert result_dict["timestamp"] == timestamp.isoformat()
        assert result_dict["error_message"] is None
    
    def test_scraping_result_create_success_classmethod(self):
        """测试create_success类方法"""
        data = {"stores": ["store1", "store2"]}
        metadata = {"scraper_version": "1.0"}
        
        result = ScrapingResult.create_success(
            data=data,
            execution_time=3.0,
            metadata=metadata
        )
        
        assert result.success is True
        assert result.data == data
        assert result.execution_time == 3.0
        assert result.metadata == metadata
        assert result.status == ScrapingStatus.SUCCESS
        assert result.error_message is None
    
    def test_scraping_result_create_failure_classmethod(self):
        """测试create_failure类方法"""
        error_msg = "抓取失败：元素未找到"
        
        result = ScrapingResult.create_failure(
            error_message=error_msg,
            execution_time=1.2
        )
        
        assert result.success is False
        assert result.data == {}
        assert result.error_message == error_msg
        assert result.execution_time == 1.2
        assert result.status == ScrapingStatus.ERROR
        assert isinstance(result.metadata, dict)
    
    def test_scraping_result_with_metadata(self):
        """测试包含元数据的抓取结果"""
        metadata = {
            "scraper_name": "seerfar_scraper",
            "page_url": "https://example.com",
            "retry_count": 2,
            "browser_type": "chrome"
        }
        
        result = ScrapingResult(
            success=True,
            data={"sales": 1000},
            metadata=metadata
        )
        
        assert result.metadata == metadata
        assert result.metadata["scraper_name"] == "seerfar_scraper"
        assert result.metadata["retry_count"] == 2
    
    def test_scraping_result_timestamp_behavior(self):
        """测试时间戳行为"""
        # 测试自动生成时间戳
        result1 = ScrapingResult(success=True, data={})
        assert isinstance(result1.timestamp, datetime)
        
        # 测试自定义时间戳
        custom_timestamp = datetime(2024, 1, 1, 12, 0, 0)
        result2 = ScrapingResult(
            success=True,
            data={},
            timestamp=custom_timestamp
        )
        assert result2.timestamp == custom_timestamp
    
    def test_scraping_result_error_message_timeout_detection(self):
        """测试错误消息中的超时检测"""
        timeout_messages = [
            "Connection timeout",
            "Request TIMEOUT occurred",
            "timeout exceeded",
            "Operation timed out"
        ]
        
        for msg in timeout_messages:
            result = ScrapingResult(
                success=False,
                data={},
                error_message=msg
            )
            assert result.status == ScrapingStatus.TIMEOUT
    
    def test_scraping_result_data_types(self):
        """测试数据类型处理"""
        # 测试复杂数据结构
        complex_data = {
            "stores": [
                {"id": "123", "name": "Store 1", "sales": 15000.50},
                {"id": "456", "name": "Store 2", "sales": 22000.75}
            ],
            "summary": {
                "total_stores": 2,
                "total_sales": 37000.25,
                "average_sales": 18500.125
            },
            "metadata": {
                "scraping_date": "2024-01-01",
                "source": "seerfar"
            }
        }
        
        result = ScrapingResult(success=True, data=complex_data)
        assert result.data == complex_data
        assert len(result.data["stores"]) == 2
        assert result.data["summary"]["total_stores"] == 2


class TestScrapingResultEdgeCases:
    """抓取结果边界情况测试"""
    
    def test_empty_data_handling(self):
        """测试空数据处理"""
        result = ScrapingResult(success=True, data={})
        assert result.data == {}
        assert result.success is True
        assert result.status == ScrapingStatus.SUCCESS
    
    def test_none_execution_time(self):
        """测试None执行时间"""
        result = ScrapingResult(success=True, data={}, execution_time=None)
        assert result.execution_time is None
    
    def test_zero_execution_time(self):
        """测试零执行时间"""
        result = ScrapingResult(success=True, data={}, execution_time=0.0)
        assert result.execution_time == 0.0
    
    def test_negative_execution_time(self):
        """测试负执行时间（边界情况）"""
        result = ScrapingResult(success=True, data={}, execution_time=-1.0)
        assert result.execution_time == -1.0  # 允许负值，由调用方保证数据合理性
    
    def test_very_large_data(self):
        """测试大数据量"""
        large_data = {
            f"item_{i}": f"value_{i}"
            for i in range(1000)
        }
        
        result = ScrapingResult(success=True, data=large_data)
        assert len(result.data) == 1000
        assert result.data["item_500"] == "value_500"
    
    def test_unicode_error_message(self):
        """测试Unicode错误消息"""
        unicode_error = "抓取失败：无法解析HTML内容 ©™® 特殊字符"
        result = ScrapingResult(
            success=False,
            data={},
            error_message=unicode_error
        )
        
        assert result.error_message == unicode_error
        assert result.status == ScrapingStatus.ERROR
    
    def test_default_metadata_factory(self):
        """测试默认元数据工厂"""
        result1 = ScrapingResult(success=True, data={})
        result2 = ScrapingResult(success=True, data={})
        
        # 确保每个实例都有独立的metadata字典
        result1.metadata["test"] = "value1"
        result2.metadata["test"] = "value2"
        
        assert result1.metadata["test"] == "value1"
        assert result2.metadata["test"] == "value2"
        assert result1.metadata is not result2.metadata


class TestScrapingResultSerialization:
    """抓取结果序列化测试"""
    
    def test_json_serializable_output(self):
        """测试JSON可序列化输出"""
        result = ScrapingResult(
            success=True,
            data={"test": "data"},
            execution_time=1.5,
            metadata={"version": "1.0"}
        )
        
        serialized = result.to_dict()
        
        # 验证所有值都是JSON可序列化的
        import json
        json_str = json.dumps(serialized)
        parsed = json.loads(json_str)
        
        assert parsed["success"] is True
        assert parsed["data"] == {"test": "data"}
        assert parsed["execution_time"] == 1.5
        assert parsed["status"] == "success"
        assert parsed["metadata"] == {"version": "1.0"}
    
    def test_roundtrip_serialization(self):
        """测试往返序列化"""
        original_result = ScrapingResult.create_success(
            data={"products": [1, 2, 3]},
            execution_time=2.0,
            metadata={"source": "test"}
        )
        
        # 序列化
        serialized = original_result.to_dict()
        
        # 反序列化（模拟）
        reconstructed = ScrapingResult(
            success=serialized["success"],
            data=serialized["data"],
            error_message=serialized["error_message"],
            execution_time=serialized["execution_time"],
            metadata=serialized["metadata"]
        )
        
        # 验证数据一致性
        assert reconstructed.success == original_result.success
        assert reconstructed.data == original_result.data
        assert reconstructed.execution_time == original_result.execution_time
        assert reconstructed.metadata == original_result.metadata
