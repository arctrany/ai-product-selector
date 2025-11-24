"""
模型枚举类型测试

测试 common/models/enums.py 中定义的所有枚举类型
"""

import pytest
from common.models.enums import StoreStatus, GoodStoreFlag


class TestStoreStatus:
    """店铺处理状态枚举测试"""
    
    def test_store_status_values(self):
        """测试枚举值定义"""
        assert StoreStatus.PENDING == "未处理"
        assert StoreStatus.PROCESSED == "已处理"
        assert StoreStatus.FAILED == "抓取异常"
        assert StoreStatus.EMPTY == ""
    
    def test_store_status_enum_members(self):
        """测试枚举成员完整性"""
        expected_members = {"PENDING", "PROCESSED", "FAILED", "EMPTY"}
        actual_members = {member.name for member in StoreStatus}
        assert actual_members == expected_members
    
    def test_store_status_string_behavior(self):
        """测试字符串枚举行为"""
        # 测试字符串比较
        assert StoreStatus.PENDING == "未处理"
        assert str(StoreStatus.PENDING) == "未处理"
        
        # 测试枚举比较
        assert StoreStatus.PENDING != StoreStatus.PROCESSED
        
    def test_store_status_iteration(self):
        """测试枚举迭代"""
        statuses = list(StoreStatus)
        assert len(statuses) == 4
        assert StoreStatus.PENDING in statuses
        assert StoreStatus.PROCESSED in statuses
        assert StoreStatus.FAILED in statuses
        assert StoreStatus.EMPTY in statuses


class TestGoodStoreFlag:
    """好店标记枚举测试"""
    
    def test_good_store_flag_values(self):
        """测试枚举值定义"""
        assert GoodStoreFlag.YES == "是"
        assert GoodStoreFlag.NO == "否" 
        assert GoodStoreFlag.EMPTY == ""
    
    def test_good_store_flag_enum_members(self):
        """测试枚举成员完整性"""
        expected_members = {"YES", "NO", "EMPTY"}
        actual_members = {member.name for member in GoodStoreFlag}
        assert actual_members == expected_members
    
    def test_good_store_flag_boolean_logic(self):
        """测试布尔逻辑转换"""
        # 测试转换为布尔值的逻辑
        def is_good_store(flag: GoodStoreFlag) -> bool:
            return flag == GoodStoreFlag.YES
        
        assert is_good_store(GoodStoreFlag.YES) is True
        assert is_good_store(GoodStoreFlag.NO) is False
        assert is_good_store(GoodStoreFlag.EMPTY) is False
    
    def test_good_store_flag_string_behavior(self):
        """测试字符串枚举行为"""
        # 测试字符串比较
        assert GoodStoreFlag.YES == "是"
        assert str(GoodStoreFlag.YES) == "是"
        
        # 测试枚举比较
        assert GoodStoreFlag.YES != GoodStoreFlag.NO


class TestEnumInteroperability:
    """枚举互操作性测试"""
    
    def test_enum_in_dict(self):
        """测试枚举作为字典键和值"""
        status_map = {
            StoreStatus.PENDING: "等待处理",
            StoreStatus.PROCESSED: "处理完成",
            StoreStatus.FAILED: "处理失败"
        }
        
        assert status_map[StoreStatus.PENDING] == "等待处理"
        assert status_map[StoreStatus.PROCESSED] == "处理完成"
        assert status_map[StoreStatus.FAILED] == "处理失败"
    
    def test_enum_serialization(self):
        """测试枚举序列化"""
        # 测试转换为JSON可序列化格式
        data = {
            'store_status': StoreStatus.PROCESSED.value,
            'is_good_store': GoodStoreFlag.YES.value
        }
        
        assert data['store_status'] == "已处理"
        assert data['is_good_store'] == "是"
    
    def test_enum_deserialization(self):
        """测试从字符串反序列化"""
        # 模拟从配置文件或API响应中读取
        status_str = "已处理"
        flag_str = "是"
        
        status = StoreStatus(status_str)
        flag = GoodStoreFlag(flag_str)
        
        assert status == StoreStatus.PROCESSED
        assert flag == GoodStoreFlag.YES
    
    def test_invalid_enum_values(self):
        """测试无效枚举值"""
        with pytest.raises(ValueError):
            StoreStatus("无效状态")
        
        with pytest.raises(ValueError):
            GoodStoreFlag("无效标记")


class TestEnumEdgeCases:
    """枚举边界情况测试"""
    
    def test_empty_value_handling(self):
        """测试空值处理"""
        empty_status = StoreStatus.EMPTY
        empty_flag = GoodStoreFlag.EMPTY
        
        # 测试空值行为
        assert empty_status == ""
        assert empty_flag == ""
        assert bool(empty_status) is False  # 空字符串为False
        assert bool(empty_flag) is False
    
    def test_enum_hashing(self):
        """测试枚举哈希行为"""
        # 枚举应该可以用作集合元素
        status_set = {StoreStatus.PENDING, StoreStatus.PROCESSED, StoreStatus.PENDING}
        flag_set = {GoodStoreFlag.YES, GoodStoreFlag.NO, GoodStoreFlag.YES}
        
        assert len(status_set) == 2  # 重复的PENDING被去重
        assert len(flag_set) == 2    # 重复的YES被去重
    
    def test_enum_ordering(self):
        """测试枚举排序（如果需要）"""
        # 注意：String枚举默认不支持排序，但可以测试相等性
        statuses = [StoreStatus.FAILED, StoreStatus.PENDING, StoreStatus.PROCESSED]
        
        # 测试去重和成员检查
        unique_statuses = list(set(statuses))
        assert len(unique_statuses) == 3
        
        for status in statuses:
            assert status in StoreStatus
