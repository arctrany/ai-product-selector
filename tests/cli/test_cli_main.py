"""
CLI主程序测试

测试cli/main.py的核心功能，包括参数解析、命令处理、配置加载等
"""

import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

from cli.main import create_parser, load_user_data, load_system_config, handle_start_command
from cli.models import UIConfig
from common.config.base_config import GoodStoreSelectorConfig

class TestCLIParser:
    """测试CLI参数解析"""
    
    def setup_method(self):
        """测试前准备"""
        self.parser = create_parser()
    
    def test_start_command_with_required_args(self):
        """测试start命令必需参数"""
        # 测试必需的--data参数
        args = self.parser.parse_args(['start', '--data', 'test.json'])
        assert args.command == 'start'
        assert args.data == 'test.json'
    
    def test_start_command_with_dryrun(self):
        """测试start命令dryrun模式"""
        args = self.parser.parse_args(['start', '--data', 'test.json', '--dryrun'])
        assert args.dryrun is True
    
    def test_select_goods_mode(self):
        """测试select-goods模式"""
        args = self.parser.parse_args(['start', '--data', 'test.json', '--select-goods'])
        assert args.select_goods is True
        assert args.select_shops is False
    
    def test_select_shops_mode(self):
        """测试select-shops模式"""
        args = self.parser.parse_args(['start', '--data', 'test.json', '--select-shops'])
        assert args.select_shops is True
        assert args.select_goods is False
    
    def test_mode_mutual_exclusivity(self):
        """测试模式互斥性"""
        with pytest.raises(SystemExit):
            self.parser.parse_args(['start', '--data', 'test.json', '--select-goods', '--select-shops'])
    
    def test_status_command(self):
        """测试status命令"""
        args = self.parser.parse_args(['status'])
        assert args.command == 'status'
    
    def test_stop_command(self):
        """测试stop命令"""
        args = self.parser.parse_args(['stop'])
        assert args.command == 'stop'
    
    def test_pause_command(self):
        """测试pause命令"""
        args = self.parser.parse_args(['pause'])
        assert args.command == 'pause'
    
    def test_resume_command(self):
        """测试resume命令"""
        args = self.parser.parse_args(['resume'])
        assert args.command == 'resume'
    
    def test_create_template_command(self):
        """测试create-template命令"""
        args = self.parser.parse_args(['create-template'])
        assert args.command == 'create-template'
        assert args.mode == 'select-shops'  # 默认值
    
    def test_create_template_with_mode(self):
        """测试create-template命令指定模式"""
        args = self.parser.parse_args(['create-template', '--mode', 'select-goods'])
        assert args.mode == 'select-goods'

class TestConfigLoading:
    """测试配置加载"""
    
    def setup_method(self):
        """测试前准备"""
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.test_data_dir.mkdir(exparent=True, exist_ok=True)
    
    def test_load_user_data_success(self):
        """测试成功加载用户数据"""
        # 创建测试配置文件
        test_config = {
            "good_shop_file": "test_shops.xlsx",
            "margin": 0.15,
            "output_path": ".",
            "min_store_sales_30days": 500000.0,
            "min_store_orders_30days": 250
        }
        
        config_file = self.test_data_dir / "test_user_data.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)
        
        # 测试加载
        ui_config = load_user_data(str(config_file))
        assert isinstance(ui_config, UIConfig)
        assert ui_config.good_shop_file == "test_shops.xlsx"
        assert ui_config.margin == 0.15
    
    def test_load_user_data_file_not_exists(self):
        """测试加载不存在的用户数据文件"""
        with patch('sys.exit') as mock_exit:
            load_user_data("nonexistent.json")
            mock_exit.assert_called_once_with(1)
    
    def test_load_system_config_default(self):
        """测试加载默认系统配置"""
        config = load_system_config()
        assert isinstance(config, GoodStoreSelectorConfig)
        assert config.selection_mode == 'select-shops'  # 默认模式
    
    def test_load_system_config_from_file(self):
        """测试从文件加载系统配置"""
        # 创建测试系统配置文件
        test_system_config = {
            "selector_filter": {
                "store_min_sales_30days": 100000.0,
                "store_min_orders_30days": 100
            },
            "selection_mode": "select-goods"
        }
        
        config_file = self.test_data_dir / "test_system_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(test_system_config, f)
        
        # 测试加载
        config = load_system_config(str(config_file))
        assert isinstance(config, GoodStoreSelectorConfig)
        assert config.selection_mode == 'select-goods'

class TestCommandHandling:
    """测试命令处理"""
    
    def setup_method(self):
        """测试前准备"""
        # Mock任务控制器
        self.mock_task_controller = MagicMock()
        
        # Mock状态管理器
        self.mock_state_manager = MagicMock()
        
        # 保存原始导入
        self.original_task_controller = None
        self.original_ui_state_manager = None
        
        # Mock导入
        import cli.main
        if hasattr(cli.main, 'task_controller'):
            self.original_task_controller = cli.main.task_controller
        if hasattr(cli.main, 'UIStateManager'):
            self.original_ui_state_manager = cli.main.UIStateManager
            
        cli.main.task_controller = self.mock_task_controller
        cli.main.UIStateManager = MagicMock(return_value=self.mock_state_manager)
    
    def teardown_method(self):
        """测试后清理"""
        # 恢复原始导入
        import cli.main
        if self.original_task_controller is not None:
            cli.main.task_controller = self.original_task_controller
        if self.original_ui_state_manager is not None:
            cli.main.UIStateManager = self.original_ui_state_manager
    
    @patch('cli.main.load_user_data')
    @patch('cli.main.load_system_config')
    def test_handle_start_command_success(self, mock_load_system_config, mock_load_user_data):
        """测试成功处理start命令"""
        # Mock配置加载
        mock_ui_config = UIConfig(
            good_shop_file="test.xlsx",
            output_path="."
        )
        mock_load_user_data.return_value = mock_ui_config
        
        mock_system_config = GoodStoreSelectorConfig()
        mock_load_system_config.return_value = mock_system_config
        
        # Mock参数
        args = MagicMock()
        args.data = "test.json"
        args.config = None
        args.dryrun = False
        args.select_goods = False
        args.select_shops = False
        
        # Mock任务控制器方法
        self.mock_task_controller.start_task.return_value = True
        
        # Mock状态管理器
        self.mock_state_manager.state = MagicMock()
        self.mock_state_manager.progress = MagicMock()
        
        # 执行测试
        result = handle_start_command(args)
        
        # 验证调用
        mock_load_user_data.assert_called_once_with("test.json")
        mock_load_system_config.assert_called_once_with(None)
        self.mock_task_controller.start_task.assert_called_once_with(mock_ui_config)
        assert result == 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
