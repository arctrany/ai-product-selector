"""
Excel模型测试

测试 common/models/excel_models.py 中定义的Excel处理相关数据模型
"""

import pytest
from common.models.excel_models import ExcelStoreData
from common.models.enums import GoodStoreFlag, StoreStatus
from common.models.business_models import StoreInfo


class TestExcelStoreData:
    """Excel店铺数据模型测试"""
    
    def test_excel_store_data_creation(self):
        """测试Excel店铺数据创建"""
        excel_data = ExcelStoreData(
            row_index=5,
            store_id="EXCEL123",
            is_good_store=GoodStoreFlag.YES,
            status=StoreStatus.PROCESSED
        )
        
        assert excel_data.row_index == 5
        assert excel_data.store_id == "EXCEL123"
        assert excel_data.is_good_store == GoodStoreFlag.YES
        assert excel_data.status == StoreStatus.PROCESSED
    
    def test_excel_store_data_creation_with_defaults(self):
        """测试使用默认值创建Excel店铺数据"""
        excel_data = ExcelStoreData(
            row_index=1,
            store_id="DEFAULT001",
            is_good_store=GoodStoreFlag.EMPTY,
            status=StoreStatus.EMPTY
        )
        
        assert excel_data.row_index == 1
        assert excel_data.store_id == "DEFAULT001"
        assert excel_data.is_good_store == GoodStoreFlag.EMPTY
        assert excel_data.status == StoreStatus.EMPTY
    
    def test_excel_store_data_row_index_handling(self):
        """测试行索引处理"""
        # 测试各种行索引值
        test_cases = [
            (1, "第一行数据"),
            (100, "第100行数据"),
            (0, "表头行或零索引"),
            (65536, "Excel最大行数附近")
        ]
        
        for row_idx, description in test_cases:
            excel_data = ExcelStoreData(
                row_index=row_idx,
                store_id=f"STORE_{row_idx}",
                is_good_store=GoodStoreFlag.EMPTY,
                status=StoreStatus.EMPTY
            )
            assert excel_data.row_index == row_idx, f"测试失败：{description}"
    
    def test_excel_store_data_store_id_variations(self):
        """测试店铺ID变化"""
        store_ids = [
            "123456789",  # 纯数字
            "STORE_ABC_123",  # 字母数字组合
            "店铺_中文_001",  # 中文字符
            "store@domain.com",  # 特殊字符
            "   PADDED_ID   "  # 带空格
        ]
        
        for store_id in store_ids:
            excel_data = ExcelStoreData(
                row_index=1,
                store_id=store_id,
                is_good_store=GoodStoreFlag.NO,
                status=StoreStatus.PENDING
            )
            assert excel_data.store_id == store_id
    
    def test_excel_store_data_enum_combinations(self):
        """测试枚举组合"""
        combinations = [
            (GoodStoreFlag.YES, StoreStatus.PROCESSED),
            (GoodStoreFlag.NO, StoreStatus.PROCESSED),
            (GoodStoreFlag.EMPTY, StoreStatus.PENDING),
            (GoodStoreFlag.YES, StoreStatus.FAILED),
            (GoodStoreFlag.NO, StoreStatus.EMPTY)
        ]
        
        for good_store_flag, status in combinations:
            excel_data = ExcelStoreData(
                row_index=1,
                store_id="COMBO_TEST",
                is_good_store=good_store_flag,
                status=status
            )
            
            assert excel_data.is_good_store == good_store_flag
            assert excel_data.status == status
    
    def test_excel_store_data_to_store_info_conversion(self):
        """测试转换为StoreInfo对象"""
        excel_data = ExcelStoreData(
            row_index=10,
            store_id="CONVERT123",
            is_good_store=GoodStoreFlag.YES,
            status=StoreStatus.PROCESSED
        )
        
        store_info = excel_data.to_store_info()
        
        # 验证转换结果
        assert isinstance(store_info, StoreInfo)
        assert store_info.store_id == "CONVERT123"
        assert store_info.is_good_store == GoodStoreFlag.YES
        assert store_info.status == StoreStatus.PROCESSED
        
        # 验证StoreInfo的默认值
        assert store_info.sold_30days is None
        assert store_info.sold_count_30days is None
        assert store_info.daily_avg_sold is None
        assert store_info.profitable_products_count == 0
        assert store_info.total_products_checked == 0
        assert store_info.needs_split is False
    
    def test_excel_store_data_conversion_preserves_data(self):
        """测试转换保持数据完整性"""
        test_data = [
            ExcelStoreData(1, "STORE001", GoodStoreFlag.YES, StoreStatus.PROCESSED),
            ExcelStoreData(2, "STORE002", GoodStoreFlag.NO, StoreStatus.FAILED),
            ExcelStoreData(3, "STORE003", GoodStoreFlag.EMPTY, StoreStatus.PENDING)
        ]
        
        for excel_data in test_data:
            store_info = excel_data.to_store_info()
            
            # 验证数据一致性
            assert store_info.store_id == excel_data.store_id
            assert store_info.is_good_store == excel_data.is_good_store
            assert store_info.status == excel_data.status
    
    def test_excel_store_data_conversion_independence(self):
        """测试转换对象独立性"""
        excel_data = ExcelStoreData(
            row_index=5,
            store_id="INDEPENDENT",
            is_good_store=GoodStoreFlag.YES,
            status=StoreStatus.PROCESSED
        )
        
        store_info1 = excel_data.to_store_info()
        store_info2 = excel_data.to_store_info()
        
        # 验证是不同的对象
        assert store_info1 is not store_info2
        
        # 但数据相同
        assert store_info1.store_id == store_info2.store_id
        assert store_info1.is_good_store == store_info2.is_good_store
        assert store_info1.status == store_info2.status


class TestExcelStoreDataValidation:
    """Excel店铺数据验证测试"""
    
    def test_excel_store_data_field_types(self):
        """测试字段类型"""
        excel_data = ExcelStoreData(
            row_index=42,
            store_id="TYPE_TEST",
            is_good_store=GoodStoreFlag.YES,
            status=StoreStatus.PROCESSED
        )
        
        assert isinstance(excel_data.row_index, int)
        assert isinstance(excel_data.store_id, str)
        assert isinstance(excel_data.is_good_store, GoodStoreFlag)
        assert isinstance(excel_data.status, StoreStatus)
    
    def test_excel_store_data_immutability_concept(self):
        """测试数据类不可变性概念"""
        excel_data = ExcelStoreData(
            row_index=1,
            store_id="IMMUTABLE",
            is_good_store=GoodStoreFlag.YES,
            status=StoreStatus.PROCESSED
        )
        
        # dataclass默认是可变的，但我们可以测试字段访问
        original_store_id = excel_data.store_id
        excel_data.store_id = "MODIFIED"
        
        assert excel_data.store_id == "MODIFIED"  # 数据类默认可变
        
        # 如果需要不可变，可以在dataclass装饰器中设置frozen=True
        # 这里只是验证当前行为
    
    def test_excel_store_data_serialization_compatibility(self):
        """测试序列化兼容性"""
        excel_data = ExcelStoreData(
            row_index=25,
            store_id="SERIALIZE_TEST",
            is_good_store=GoodStoreFlag.NO,
            status=StoreStatus.FAILED
        )
        
        # 模拟序列化为字典
        serialized = {
            'row_index': excel_data.row_index,
            'store_id': excel_data.store_id,
            'is_good_store': excel_data.is_good_store.value,
            'status': excel_data.status.value
        }
        
        assert serialized['row_index'] == 25
        assert serialized['store_id'] == "SERIALIZE_TEST"
        assert serialized['is_good_store'] == "否"
        assert serialized['status'] == "抓取异常"
        
        # 模拟反序列化
        deserialized = ExcelStoreData(
            row_index=serialized['row_index'],
            store_id=serialized['store_id'],
            is_good_store=GoodStoreFlag(serialized['is_good_store']),
            status=StoreStatus(serialized['status'])
        )
        
        assert deserialized.row_index == excel_data.row_index
        assert deserialized.store_id == excel_data.store_id
        assert deserialized.is_good_store == excel_data.is_good_store
        assert deserialized.status == excel_data.status


class TestExcelStoreDataEdgeCases:
    """Excel店铺数据边界情况测试"""
    
    def test_excel_store_data_negative_row_index(self):
        """测试负数行索引"""
        # 虽然实际Excel不会有负数行，但测试边界情况
        excel_data = ExcelStoreData(
            row_index=-1,
            store_id="NEGATIVE_ROW",
            is_good_store=GoodStoreFlag.EMPTY,
            status=StoreStatus.EMPTY
        )
        
        assert excel_data.row_index == -1
        assert excel_data.store_id == "NEGATIVE_ROW"
    
    def test_excel_store_data_very_large_row_index(self):
        """测试很大的行索引"""
        large_row = 1048576  # Excel 2007+的最大行数
        excel_data = ExcelStoreData(
            row_index=large_row,
            store_id="LARGE_ROW",
            is_good_store=GoodStoreFlag.YES,
            status=StoreStatus.PROCESSED
        )
        
        assert excel_data.row_index == large_row
        assert excel_data.store_id == "LARGE_ROW"
    
    def test_excel_store_data_empty_store_id(self):
        """测试空店铺ID"""
        # ExcelStoreData可以接受空店铺ID，验证会在转换时进行
        excel_data = ExcelStoreData(
            row_index=1,
            store_id="",
            is_good_store=GoodStoreFlag.EMPTY,
            status=StoreStatus.EMPTY
        )
        
        assert excel_data.store_id == ""
        
        # 转换为StoreInfo时会进行验证
        with pytest.raises(ValueError, match="店铺ID不能为空"):
            excel_data.to_store_info()
    
    def test_excel_store_data_whitespace_store_id(self):
        """测试空白字符店铺ID"""
        excel_data = ExcelStoreData(
            row_index=1,
            store_id="   ",
            is_good_store=GoodStoreFlag.EMPTY,
            status=StoreStatus.EMPTY
        )
        
        assert excel_data.store_id == "   "
        
        # 转换为StoreInfo时会进行验证
        with pytest.raises(ValueError, match="店铺ID不能为空"):
            excel_data.to_store_info()
    
    def test_excel_store_data_unicode_store_id(self):
        """测试Unicode店铺ID"""
        unicode_ids = [
            "店铺123",
            "STORE™®©",
            "مخزن123",  # 阿拉伯文
            "商店🏪123",  # 包含emoji
            "Магазин123"  # 俄文
        ]
        
        for unicode_id in unicode_ids:
            excel_data = ExcelStoreData(
                row_index=1,
                store_id=unicode_id,
                is_good_store=GoodStoreFlag.YES,
                status=StoreStatus.PROCESSED
            )
            
            assert excel_data.store_id == unicode_id
            
            # 转换也应该成功
            store_info = excel_data.to_store_info()
            assert store_info.store_id == unicode_id


class TestExcelStoreDataIntegration:
    """Excel店铺数据集成测试"""
    
    def test_batch_excel_data_processing(self):
        """测试批量Excel数据处理"""
        excel_data_list = [
            ExcelStoreData(1, "BATCH001", GoodStoreFlag.YES, StoreStatus.PROCESSED),
            ExcelStoreData(2, "BATCH002", GoodStoreFlag.NO, StoreStatus.PROCESSED),
            ExcelStoreData(3, "BATCH003", GoodStoreFlag.EMPTY, StoreStatus.PENDING),
            ExcelStoreData(4, "BATCH004", GoodStoreFlag.YES, StoreStatus.FAILED),
            ExcelStoreData(5, "BATCH005", GoodStoreFlag.NO, StoreStatus.EMPTY)
        ]
        
        # 批量转换
        store_infos = [data.to_store_info() for data in excel_data_list]
        
        assert len(store_infos) == 5
        assert all(isinstance(info, StoreInfo) for info in store_infos)
        
        # 验证转换后的数据
        for i, (excel_data, store_info) in enumerate(zip(excel_data_list, store_infos)):
            assert store_info.store_id == excel_data.store_id
            assert store_info.is_good_store == excel_data.is_good_store
            assert store_info.status == excel_data.status
    
    def test_excel_data_filtering(self):
        """测试Excel数据过滤"""
        excel_data_list = [
            ExcelStoreData(1, "FILTER001", GoodStoreFlag.YES, StoreStatus.PROCESSED),
            ExcelStoreData(2, "FILTER002", GoodStoreFlag.NO, StoreStatus.PROCESSED),
            ExcelStoreData(3, "FILTER003", GoodStoreFlag.YES, StoreStatus.FAILED),
            ExcelStoreData(4, "FILTER004", GoodStoreFlag.EMPTY, StoreStatus.PENDING)
        ]
        
        # 过滤好店
        good_stores = [data for data in excel_data_list 
                      if data.is_good_store == GoodStoreFlag.YES]
        
        assert len(good_stores) == 2
        assert good_stores[0].store_id == "FILTER001"
        assert good_stores[1].store_id == "FILTER003"
        
        # 过滤已处理状态
        processed_stores = [data for data in excel_data_list 
                           if data.status == StoreStatus.PROCESSED]
        
        assert len(processed_stores) == 2
        assert processed_stores[0].store_id == "FILTER001"
        assert processed_stores[1].store_id == "FILTER002"
    
    def test_excel_data_row_index_sorting(self):
        """测试按行索引排序"""
        # 创建乱序的Excel数据
        excel_data_list = [
            ExcelStoreData(5, "SORT005", GoodStoreFlag.YES, StoreStatus.PROCESSED),
            ExcelStoreData(1, "SORT001", GoodStoreFlag.NO, StoreStatus.PROCESSED),
            ExcelStoreData(3, "SORT003", GoodStoreFlag.EMPTY, StoreStatus.PENDING),
            ExcelStoreData(2, "SORT002", GoodStoreFlag.YES, StoreStatus.FAILED),
            ExcelStoreData(4, "SORT004", GoodStoreFlag.NO, StoreStatus.EMPTY)
        ]
        
        # 按行索引排序
        sorted_data = sorted(excel_data_list, key=lambda x: x.row_index)
        
        expected_order = ["SORT001", "SORT002", "SORT003", "SORT004", "SORT005"]
        actual_order = [data.store_id for data in sorted_data]
        
        assert actual_order == expected_order
        
        # 验证行索引顺序
        expected_indices = [1, 2, 3, 4, 5]
        actual_indices = [data.row_index for data in sorted_data]
        
        assert actual_indices == expected_indices
