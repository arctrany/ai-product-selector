"""
ExcelProductWriter 单元测试

测试商品Excel写入器功能，包括：
- 单个商品写入
- 批量写入
- 错误处理
- 数据格式转换
- dryrun模式
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import tempfile
import os

from common.excel_processor import ExcelProductWriter
from common.models.excel_models import ExcelProductData
from common.config.base_config import GoodStoreSelectorConfig


class TestExcelProductWriter(unittest.TestCase):
    """ExcelProductWriter 单元测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时文件
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        self.temp_file.close()
        
        # 创建配置
        self.config = GoodStoreSelectorConfig()
        self.config.dryrun = False
    
    def tearDown(self):
        """测试后清理"""
        try:
            os.unlink(self.temp_file.name)
        except:
            pass
    
    @patch('common.excel_processor.load_workbook')
    @patch('common.excel_processor.Workbook')
    def test_init_new_file(self, mock_workbook_class, mock_load_workbook):
        """测试创建新文件"""
        # 模拟文件不存在
        with patch('pathlib.Path.exists', return_value=False):
            mock_workbook = MagicMock()
            mock_worksheet = MagicMock()
            mock_workbook.active = mock_worksheet
            mock_workbook_class.return_value = mock_workbook
            
            # 创建写入器
            writer = ExcelProductWriter(self.temp_file.name, self.config)
            
            # 验证创建了新工作簿
            mock_workbook_class.assert_called_once()
            
            # 验证写入了表头
            self.assertTrue(mock_worksheet.__setitem__.called)
            
            # 验证设置了正确的起始行
            self.assertEqual(writer.current_row, 2)
    
    @patch('common.excel_processor.load_workbook')
    def test_init_existing_file(self, mock_load_workbook):
        """测试打开已存在的文件"""
        # 模拟文件存在
        with patch('pathlib.Path.exists', return_value=True):
            mock_workbook = MagicMock()
            mock_worksheet = MagicMock()
            mock_worksheet.max_row = 10
            mock_workbook.active = mock_worksheet
            mock_load_workbook.return_value = mock_workbook
            
            # 创建写入器
            writer = ExcelProductWriter(self.temp_file.name, self.config)
            
            # 验证打开了已存在的工作簿
            mock_load_workbook.assert_called_once_with(Path(self.temp_file.name))
            
            # 验证设置了正确的起始行
            self.assertEqual(writer.current_row, 11)  # max_row + 1
    
    def test_write_single_product(self):
        """测试写入单个商品"""
        with patch('common.excel_processor.load_workbook') as mock_load_workbook:
            
            mock_workbook = MagicMock()
            mock_worksheet = MagicMock()
            mock_workbook.active = mock_worksheet
            mock_worksheet.max_row = 1
            mock_load_workbook.return_value = mock_workbook
            
            # 创建写入器
            writer = ExcelProductWriter(self.temp_file.name, self.config)
            
            # 创建测试商品数据
            product_data = ExcelProductData(
                store_id="123456",
                product_id="prod-001",
                product_name="测试商品",
                image_url="http://example.com/image.jpg",
                green_price=100.0,
                black_price=120.0,
                commission_rate=0.15,
                weight=500.0,
                length=10.0,
                width=8.0,
                height=5.0,
                source_price=50.0,
                profit_rate=45.5,
                profit_amount=22.75
            )
            
            # 写入商品
            result = writer.write_product(product_data)
            
            # 验证返回成功
            self.assertTrue(result)
            
            # 验证写入了所有字段
            self.assertEqual(mock_worksheet.__setitem__.call_count, 14)  # 14个字段
            
            # 验证行号增加
            self.assertEqual(writer.current_row, 3)
    
    def test_batch_write_products(self):
        """测试批量写入商品"""
        with patch('common.excel_processor.load_workbook'), \
             patch('common.excel_processor.Workbook') as mock_workbook_class:
            
            mock_workbook = MagicMock()
            mock_worksheet = MagicMock()
            mock_workbook.active = mock_worksheet
            mock_workbook_class.return_value = mock_workbook
            
            # 创建写入器
            writer = ExcelProductWriter(self.temp_file.name, self.config)
            
            # 创建15个商品（测试批量处理）
            products = []
            for i in range(15):
                products.append(ExcelProductData(
                    store_id=f"store-{i}",
                    product_id=f"prod-{i:03d}",
                    product_name=f"商品{i}",
                    source_price=50.0 + i,
                    profit_rate=20.0 + i,
                    profit_amount=10.0 + i
                ))
            
            # 批量写入
            with patch.object(writer, 'save_changes') as mock_save:
                success_count = writer.batch_write_products(products)
            
            # 验证写入成功
            self.assertEqual(success_count, 15)
            
            # 验证保存被调用了2次（每10个一批）
            self.assertEqual(mock_save.call_count, 2)
    
    def test_write_product_with_error(self):
        """测试写入商品时的错误处理"""
        with patch('common.excel_processor.load_workbook') as mock_load_workbook:
            
            mock_workbook = MagicMock()
            mock_worksheet = MagicMock()
            mock_workbook.active = mock_worksheet
            mock_worksheet.max_row = 1
            mock_load_workbook.return_value = mock_workbook
            
            # 模拟写入时抛出异常
            mock_worksheet.__setitem__.side_effect = Exception("写入错误")
            
            # 创建写入器
            writer = ExcelProductWriter(self.temp_file.name, self.config)
            
            # 创建测试商品数据
            product_data = ExcelProductData(
                store_id="123456",
                product_id="error-prod"
            )
            
            # 写入商品
            result = writer.write_product(product_data)
            
            # 验证返回失败
            self.assertFalse(result)
            
            # 验证行号没有增加
            self.assertEqual(writer.current_row, 2)
    
    def test_batch_write_with_partial_failure(self):
        """测试批量写入时部分失败的情况"""
        with patch('common.excel_processor.load_workbook'), \
             patch('common.excel_processor.Workbook') as mock_workbook_class:
            
            mock_workbook = MagicMock()
            mock_worksheet = MagicMock()
            mock_workbook.active = mock_worksheet
            mock_workbook_class.return_value = mock_workbook
            
            # 创建写入器
            writer = ExcelProductWriter(self.temp_file.name, self.config)
            
            # 创建5个商品
            products = []
            for i in range(5):
                products.append(ExcelProductData(
                    store_id=f"store-{i}",
                    product_id=f"prod-{i:03d}"
                ))
            
            # 模拟第3个商品写入失败
            with patch.object(writer, 'write_product') as mock_write:
                mock_write.side_effect = [True, True, False, True, True]
                
                success_count = writer.batch_write_products(products)
            
            # 验证成功数量
            self.assertEqual(success_count, 4)
    
    def test_save_changes_normal_mode(self):
        """测试正常模式下的保存"""
        with patch('common.excel_processor.load_workbook') as mock_load_workbook:
            
            mock_workbook = MagicMock()
            mock_worksheet = MagicMock()
            mock_workbook.active = mock_worksheet
            mock_worksheet.max_row = 1
            mock_load_workbook.return_value = mock_workbook
            
            # 创建写入器
            writer = ExcelProductWriter(self.temp_file.name, self.config)
            
            # 保存更改
            writer.save_changes()
            
            # 验证调用了保存
            mock_workbook.save.assert_called_once_with(Path(self.temp_file.name))
    
    def test_save_changes_dryrun_mode(self):
        """测试dryrun模式下的保存"""
        with patch('common.excel_processor.load_workbook'), \
             patch('common.excel_processor.Workbook') as mock_workbook_class:
            
            mock_workbook = MagicMock()
            mock_worksheet = MagicMock()
            mock_workbook.active = mock_worksheet
            mock_workbook_class.return_value = mock_workbook
            
            # 设置为dryrun模式
            self.config.dryrun = True
            
            # 创建写入器
            writer = ExcelProductWriter(self.temp_file.name, self.config)
            
            # 保存更改
            writer.save_changes()
            
            # 验证没有调用保存
            mock_workbook.save.assert_not_called()
    
    def test_profit_rate_formatting(self):
        """测试利润率格式化"""
        with patch('common.excel_processor.load_workbook') as mock_load_workbook:
            
            mock_workbook = MagicMock()
            mock_worksheet = MagicMock()
            mock_workbook.active = mock_worksheet
            # 模拟worksheet的max_row属性
            mock_worksheet.max_row = 1
            mock_load_workbook.return_value = mock_workbook
            
            # 创建写入器
            writer = ExcelProductWriter(self.temp_file.name, self.config)
            
            # 创建测试商品数据
            product_data = ExcelProductData(
                store_id="123456",
                product_id="prod-001",
                profit_rate=45.678,  # 测试小数位
                profit_amount=123.456  # 测试小数位
            )
            
            # 写入商品
            writer.write_product(product_data)
            
            # 找到利润率和利润金额的调用
            calls = mock_worksheet.__setitem__.call_args_list
            
            # 验证利润率格式化为百分比
            profit_rate_written = False
            profit_amount_written = False
            
            # M列是利润率，N列是利润金额，应该写入第2行
            for call in calls:
                key = call[0][0]
                value = call[0][1]
                # 检查是否包含利润率列字母和行号
                if key.startswith(self.config.excel.product_profit_rate_column) and value == "45.7%":
                    profit_rate_written = True
                elif key.startswith(self.config.excel.product_profit_amount_column) and value == 123.46:
                    profit_amount_written = True
            
            self.assertTrue(profit_rate_written, f"利润率未被写入，所有调用: {[(c[0][0], c[0][1]) for c in calls]}")
            self.assertTrue(profit_amount_written, "利润金额未被写入")
    
    def test_close_workbook(self):
        """测试关闭工作簿"""
        with patch('common.excel_processor.load_workbook') as mock_load_workbook:
            
            mock_workbook = MagicMock()
            mock_worksheet = MagicMock()
            mock_workbook.active = mock_worksheet
            mock_load_workbook.return_value = mock_workbook
            
            # 创建写入器（使用已存在的文件）
            writer = ExcelProductWriter(self.temp_file.name, self.config)
            
            # 关闭
            writer.close()
            
            # 验证调用了关闭
            mock_workbook.close.assert_called_once()
            
            # 验证清理了内部状态
            self.assertIsNone(writer.workbook)
            self.assertIsNone(writer.worksheet)


if __name__ == '__main__':
    unittest.main()