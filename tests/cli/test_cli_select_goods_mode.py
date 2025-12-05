"""
CLI select-goods模式测试

测试CLI层面的select-goods模式功能，包括：
- 参数验证
- item_collect_file路径检查
- 模式组合验证
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
import os
import tempfile
from pathlib import Path

from cli.main import handle_start_command, load_user_data
from cli.models import UIConfig
from common.config.base_config import GoodStoreSelectorConfig


class TestCLISelectGoodsMode:
    """CLI select-goods模式测试"""
    
    def setup_method(self):
        """测试前准备"""
        # 创建临时文件
        self.temp_dir = tempfile.mkdtemp()
        self.temp_user_data = os.path.join(self.temp_dir, "user_data.json")
        self.temp_item_collect = os.path.join(self.temp_dir, "item_collect.xlsx")
        self.temp_excel = os.path.join(self.temp_dir, "stores.xlsx")
        self.temp_calc = os.path.join(self.temp_dir, "calculator.xlsx")
        
        # 创建文件
        Path(self.temp_item_collect).touch()
        Path(self.temp_excel).touch()
        Path(self.temp_calc).touch()
    
    def teardown_method(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_user_data_with_item_collect_file(self):
        """测试加载包含item_collect_file的用户数据"""
        user_data = {
            "excel_file_path": self.temp_excel,
            "profit_calculator_path": self.temp_calc,
            "item_collect_file": self.temp_item_collect,
            "browser_path": "/usr/bin/chrome",
            "user_data_dir": "/tmp/chrome",
            "selection_mode": "select-goods"
        }
        
        # 写入用户数据
        import json
        with open(self.temp_user_data, 'w', encoding='utf-8') as f:
            json.dump(user_data, f)
        
        # 加载用户数据
        ui_config = load_user_data(self.temp_user_data)
        
        # 验证
        assert ui_config.item_collect_file == self.temp_item_collect
        assert ui_config.selection_mode == "select-goods"
    
    def test_select_goods_mode_requires_item_collect_file(self):
        """测试select-goods模式必须提供item_collect_file"""
        # 创建参数对象
        args = MagicMock()
        args.user_data = self.temp_user_data
        args.config = None
        args.dryrun = False
        args.select_goods = True
        args.select_shops = False
        
        # 创建不包含item_collect_file的用户数据
        user_data = {
            "excel_file_path": self.temp_excel,
            "profit_calculator_path": self.temp_calc,
            "browser_path": "/usr/bin/chrome",
            "user_data_dir": "/tmp/chrome"
        }
        
        import json
        with open(self.temp_user_data, 'w', encoding='utf-8') as f:
            json.dump(user_data, f)
        
        # 模拟加载配置
        with patch('cli.main.load_system_config') as mock_load_config:
            mock_config = GoodStoreSelectorConfig()
            mock_load_config.return_value = mock_config
            
            # 执行并验证应该失败
            with pytest.raises(ValueError, match="select-goods模式需要提供item_collect_file"):
                handle_start_command(args)
    
    def test_item_collect_file_path_validation(self):
        """测试item_collect_file路径验证"""
        # 创建参数对象
        args = MagicMock()
        args.user_data = self.temp_user_data
        args.config = None
        args.dryrun = False
        args.select_goods = True
        args.select_shops = False
        
        # 创建包含不存在的item_collect_file的用户数据
        user_data = {
            "excel_file_path": self.temp_excel,
            "profit_calculator_path": self.temp_calc,
            "item_collect_file": "/path/to/nonexistent/file.xlsx",
            "browser_path": "/usr/bin/chrome",
            "user_data_dir": "/tmp/chrome"
        }
        
        import json
        with open(self.temp_user_data, 'w', encoding='utf-8') as f:
            json.dump(user_data, f)
        
        # 模拟加载配置
        with patch('cli.main.load_system_config') as mock_load_config:
            mock_config = GoodStoreSelectorConfig()
            mock_load_config.return_value = mock_config
            
            # 执行并验证应该失败
            with pytest.raises(FileNotFoundError, match="item_collect_file不存在"):
                handle_start_command(args)
    
    def test_selection_mode_priority(self):
        """测试选择模式优先级"""
        # 测试命令行参数优先级高于配置文件
        
        # 1. 只有select_goods标志
        args = MagicMock()
        args.user_data = self.temp_user_data
        args.config = None
        args.dryrun = False
        args.select_goods = True
        args.select_shops = False
        
        # 创建包含默认模式的用户数据
        user_data = {
            "excel_file_path": self.temp_excel,
            "profit_calculator_path": self.temp_calc,
            "item_collect_file": self.temp_item_collect,
            "browser_path": "/usr/bin/chrome",
            "user_data_dir": "/tmp/chrome",
            "selection_mode": "select-shops"  # 默认是select-shops
        }
        
        import json
        with open(self.temp_user_data, 'w', encoding='utf-8') as f:
            json.dump(user_data, f)
        
        # 通过handle_start_command验证命令行参数优先
        with patch('cli.main.TaskController'), \
             patch('cli.main.load_system_config') as mock_load_config:
            mock_config = GoodStoreSelectorConfig()
            mock_load_config.return_value = mock_config
            
            # 执行命令会设置selection_mode
            handle_start_command(args)
            
            # 验证配置被正确设置为select-goods（命令行参数优先）
            assert mock_config.selection_mode == "select-goods"
    
    @patch('cli.main.TaskController')
    def test_select_goods_mode_full_flow(self, mock_task_controller_class):
        """测试select-goods模式完整流程"""
        # 创建参数对象
        args = MagicMock()
        args.user_data = self.temp_user_data
        args.config = None
        args.dryrun = False
        args.select_goods = True
        args.select_shops = False
        
        # 创建完整的用户数据
        user_data = {
            "excel_file_path": self.temp_excel,
            "profit_calculator_path": self.temp_calc,
            "item_collect_file": self.temp_item_collect,
            "browser_path": "/usr/bin/chrome",
            "user_data_dir": "/tmp/chrome",
            "monitor_url": "http://localhost:8000"
        }
        
        import json
        with open(self.temp_user_data, 'w', encoding='utf-8') as f:
            json.dump(user_data, f)
        
        # 模拟TaskController
        mock_task_controller = Mock()
        mock_task_controller.start_task.return_value = True
        mock_task_controller_class.return_value = mock_task_controller
        
        # 模拟加载配置
        with patch('cli.main.load_system_config') as mock_load_config:
            mock_config = GoodStoreSelectorConfig()
            mock_load_config.return_value = mock_config
            
            # 执行
            result = handle_start_command(args)
            
            # 验证成功
            assert result == 0
            
            # 验证TaskController被调用
            mock_task_controller.start_task.assert_called_once()
            
            # 验证传递的UI配置
            ui_config = mock_task_controller.start_task.call_args[0][0]
            assert isinstance(ui_config, UIConfig)
            assert ui_config.item_collect_file == self.temp_item_collect
    
    def test_dryrun_mode_with_select_goods(self):
        """测试dryrun模式与select-goods结合"""
        # 创建参数对象
        args = MagicMock()
        args.user_data = self.temp_user_data
        args.config = None
        args.dryrun = True  # 启用dryrun
        args.select_goods = True
        args.select_shops = False
        
        # 创建用户数据
        user_data = {
            "excel_file_path": self.temp_excel,
            "profit_calculator_path": self.temp_calc,
            "item_collect_file": self.temp_item_collect,
            "browser_path": "/usr/bin/chrome",
            "user_data_dir": "/tmp/chrome"
        }
        
        import json
        with open(self.temp_user_data, 'w', encoding='utf-8') as f:
            json.dump(user_data, f)
        
        # 模拟TaskController
        with patch('cli.main.TaskController') as mock_task_controller_class, \
             patch('cli.main.load_system_config') as mock_load_config:
            
            mock_config = GoodStoreSelectorConfig()
            mock_load_config.return_value = mock_config
            
            mock_task_controller = Mock()
            mock_task_controller.start_task.return_value = True
            mock_task_controller_class.return_value = mock_task_controller
            
            # 执行
            result = handle_start_command(args)
            
            # 验证配置中包含dryrun
            assert mock_config.dryrun == True
            
            # 验证成功
            assert result == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])