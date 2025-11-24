"""
Excel处理器测试

测试common/excel_processor.py的核心功能
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from common.excel_processor import ExcelStoreProcessor
from common.models.excel_models import ExcelStoreData
from common.models.enums import GoodStoreFlag, StoreStatus
from common.config.base_config import GoodStoreSelectorConfig

class TestExcelStoreProcessor:
    """测试ExcelStoreProcessor类"""
    
    def setup_method(self):
        """测试前准备"""
        self.config = GoodStoreSelectorConfig()
        
        # Mock Workbook和Worksheet
        self.mock_workbook = MagicMock()
        self.mock_worksheet = MagicMock()
        self.mock_workbook.active = self.mock_worksheet
        self.mock_workbook.worksheets = [self.mock_worksheet]
        
        # Mock openpyxl
        self.mock_load_workbook = MagicMock(return_value=self.mock_workbook)
    
    def test_initialization_success(self):
        """测试成功初始化"""
        with patch('common.excel_processor.Path.exists', return_value=True), \
             patch('common.excel_processor.load_workbook', self.mock_load_workbook):
            
            processor = ExcelStoreProcessor("test.xlsx", self.config)
            
            assert processor.excel_file_path.name == "test.xlsx"
            assert processor.config == self.config
            self.mock_load_workbook.assert_called_once_with(Path("test.xlsx"))
    
    def test_initialization_file_not_exists(self):
        """测试文件不存在时初始化"""
        with patch('common.excel_processor.Path.exists', return_value=False):
            with pytest.raises(Exception, match="Excel文件不存在"):
                ExcelStoreProcessor("nonexistent.xlsx", self.config)
    
    def test_read_store_data_success(self):
        """测试成功读取店铺数据"""
        with patch('common.excel_processor.Path.exists', return_value=True), \
             patch('common.excel_processor.load_workbook', self.mock_load_workbook):
            
            processor = ExcelStoreProcessor("test.xlsx", self.config)
            
            # Mock工作表数据
            self.mock_worksheet.max_row = 3
            mock_store_id_cell = MagicMock()
            mock_store_id_cell.value = "STORE001"
            mock_good_store_cell = MagicMock()
            mock_good_store_cell.value = "是"
            mock_status_cell = MagicMock()
            mock_status_cell.value = "已处理"
            
            self.mock_worksheet.__getitem__.side_effect = lambda key: {
                'A2': mock_store_id_cell,
                'B2': mock_good_store_cell,
                'C2': mock_status_cell
            }.get(key, MagicMock())
            
            # 执行测试
            result = processor.read_store_data()
            
            # 验证
            assert len(result) == 1
            assert result[0].row_index == 2
            assert result[0].store_id == "STORE001"
            assert result[0].is_good_store == GoodStoreFlag.YES
            assert result[0].status == StoreStatus.PROCESSED
    
    def test_read_store_data_empty_store_id(self):
        """测试读取空店铺ID"""
        with patch('common.excel_processor.Path.exists', return_value=True), \
             patch('common.excel_processor.load_workbook', self.mock_load_workbook):
            
            processor = ExcelStoreProcessor("test.xlsx", self.config)
            
            # Mock工作表数据
            self.mock_worksheet.max_row = 3
            mock_store_id_cell = MagicMock()
            mock_store_id_cell.value = ""  # 空店铺ID
            
            self.mock_worksheet.__getitem__.side_effect = lambda key: {
                'A2': mock_store_id_cell
            }.get(key, MagicMock())
            
            # 执行测试并验证异常
            with pytest.raises(Exception, match="店铺ID为空"):
                processor.read_store_data()
    
    def test_filter_pending_stores(self):
        """测试过滤待处理店铺"""
        with patch('common.excel_processor.Path.exists', return_value=True), \
             patch('common.excel_processor.load_workbook', self.mock_load_workbook):
            
            processor = ExcelStoreProcessor("test.xlsx", self.config)
            
            # Mock数据
            store_data_list = [
                ExcelStoreData(1, "STORE001", GoodStoreFlag.EMPTY, StoreStatus.EMPTY),
                ExcelStoreData(2, "STORE002", GoodStoreFlag.EMPTY, StoreStatus.PENDING),
                ExcelStoreData(3, "STORE003", GoodStoreFlag.YES, StoreStatus.PROCESSED),
                ExcelStoreData(4, "STORE004", GoodStoreFlag.NO, StoreStatus.FAILED)
            ]
            
            # 执行测试
            result = processor.filter_pending_stores(store_data_list)
            
            # 验证
            assert len(result) == 2
            assert result[0].store_id == "STORE001"
            assert result[1].store_id == "STORE002"
    
    def test_update_store_status(self):
        """测试更新店铺状态"""
        with patch('common.excel_processor.Path.exists', return_value=True), \
             patch('common.excel_processor.load_workbook', self.mock_load_workbook):
            
            processor = ExcelStoreProcessor("test.xlsx", self.config)
            
            # Mock数据
            store_data = ExcelStoreData(2, "STORE001", GoodStoreFlag.EMPTY, StoreStatus.EMPTY)
            
            # 执行测试
            processor.update_store_status(store_data, GoodStoreFlag.YES, StoreStatus.PROCESSED)
            
            # 验证
            # 验证好店标记更新
            self.mock_worksheet.__setitem__.assert_any_call('B2', '是')
            # 验证状态更新
            self.mock_worksheet.__setitem__.assert_any_call('C2', '已处理')
    
    def test_batch_update_stores(self):
        """测试批量更新店铺状态"""
        with patch('common.excel_processor.Path.exists', return_value=True), \
             patch('common.excel_processor.load_workbook', self.mock_load_workbook):
            
            processor = ExcelStoreProcessor("test.xlsx", self.config)
            
            # Mock数据
            store_data1 = ExcelStoreData(2, "STORE001", GoodStoreFlag.EMPTY, StoreStatus.EMPTY)
            store_data2 = ExcelStoreData(3, "STORE002", GoodStoreFlag.EMPTY, StoreStatus.EMPTY)
            
            updates = [
                (store_data1, GoodStoreFlag.YES, StoreStatus.PROCESSED),
                (store_data2, GoodStoreFlag.NO, StoreStatus.FAILED)
            ]
            
            # 执行测试
            processor.batch_update_stores(updates)
            
            # 验证调用次数
            assert processor.update_store_status.call_count == 2
    
    def test_save_changes_dryrun(self):
        """测试保存更改（dryrun模式）"""
        with patch('common.excel_processor.Path.exists', return_value=True), \
             patch('common.excel_processor.load_workbook', self.mock_load_workbook):
            
            # 设置dryrun模式
            config = GoodStoreSelectorConfig()
            config.dryrun = True
            
            processor = ExcelStoreProcessor("test.xlsx", config)
            
            # 执行测试
            processor.save_changes()
            
            # 验证没有保存文件
            self.mock_workbook.save.assert_not_called()
    
    def test_save_changes_normal(self):
        """测试保存更改（正常模式）"""
        with patch('common.excel_processor.Path.exists', return_value=True), \
             patch('common.excel_processor.load_workbook', self.mock_load_workbook):
            
            # 设置正常模式
            config = GoodStoreSelectorConfig()
            config.dryrun = False
            
            processor = ExcelStoreProcessor("test.xlsx", config)
            
            # 执行测试
            processor.save_changes()
            
            # 验证保存文件
            self.mock_workbook.save.assert_called_once_with(Path("test.xlsx"))
    
    def test_validate_excel_format_success(self):
        """测试成功验证Excel格式"""
        with patch('common.excel_processor.Path.exists', return_value=True), \
             patch('common.excel_processor.load_workbook', self.mock_load_workbook):
            
            processor = ExcelStoreProcessor("test.xlsx", self.config)
            
            # Mock工作表数据
            mock_cell = MagicMock()
            mock_cell.value = "店铺ID"
            self.mock_worksheet.__getitem__.return_value = mock_cell
            self.mock_worksheet.max_row = 5
            
            # 执行测试
            result = processor.validate_excel_format()
            
            # 验证
            assert result is True
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        with patch('common.excel_processor.Path.exists', return_value=True), \
             patch('common.excel_processor.load_workbook', self.mock_load_workbook):
            
            processor = ExcelStoreProcessor("test.xlsx", self.config)
            
            # Mock工作表数据
            self.mock_worksheet.max_row = 5
            self.mock_worksheet.max_column = 3
            
            # Mock read_store_data
            mock_store_data_list = [
                ExcelStoreData(1, "STORE001", GoodStoreFlag.YES, StoreStatus.PROCESSED),
                ExcelStoreData(2, "STORE002", GoodStoreFlag.NO, StoreStatus.PROCESSED),
                ExcelStoreData(3, "STORE003", GoodStoreFlag.EMPTY, StoreStatus.PENDING)
            ]
            processor.read_store_data = MagicMock(return_value=mock_store_data_list)
            
            # 执行测试
            result = processor.get_statistics()
            
            # 验证
            assert result['total_stores'] == 3
            assert result['pending_stores'] == 1
            assert result['processed_stores'] == 2
            assert result['good_stores'] == 1
            assert result['max_row'] == 5
            assert result['max_column'] == 3

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
