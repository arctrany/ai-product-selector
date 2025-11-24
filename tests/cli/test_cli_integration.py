"""
CLI集成测试

测试CLI模块与其他模块的集成
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from pathlib import Path

from cli.main import load_user_data, load_system_config, handle_start_command
from cli.xp_cli import XuanpingCLIController
from cli.models import UIConfig
from common.config.base_config import GoodStoreSelectorConfig

class TestCLIIntegration:
    """测试CLI集成"""
    
    def setup_method(self):
        """测试前准备"""
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)
    
    def test_load_user_data_integration(self):
        """测试加载用户数据集成"""
        # 创建测试配置文件，使用项目中实际存在的Excel文件路径
        test_config = {
            "good_shop_file": "docs/good_shops.xlsx",
            "margin_calculator": "docs/profits_calculator.xlsx",
            "margin": 0.15,
            "output_path": ".",
            "min_store_sales_30days": 500000.0,
            "min_store_orders_30days": 250
        }
        
        config_file = self.test_data_dir / "integration_test_user_data.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)
        
        # 测试加载
        ui_config = load_user_data(str(config_file))
        
        # 验证
        assert isinstance(ui_config, UIConfig)
        assert ui_config.good_shop_file == "docs/good_shops.xlsx"
        assert ui_config.margin == 0.15
        assert ui_config.min_store_sales_30days == 500000.0
        assert ui_config.min_store_orders_30days == 250
    
    def test_load_system_config_integration(self):
        """测试加载系统配置集成"""
        # 创建测试系统配置文件
        test_system_config = {
            "selector_filter": {
                "store_min_sales_30days": 100000.0,
                "store_min_orders_30days": 100
            },
            "selection_mode": "select-goods",
            "dryrun": False
        }
        
        config_file = self.test_data_dir / "integration_test_system_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(test_system_config, f)
        
        # 测试加载
        config = load_system_config(str(config_file))
        
        # 验证
        assert isinstance(config, GoodStoreSelectorConfig)
        assert config.selection_mode == 'select-goods'
        assert config.selector_filter.store_min_sales_30days == 100000.0
        assert config.selector_filter.store_min_orders_30days == 100
    
    @patch('cli.main.task_controller')
    @patch('cli.main.UIStateManager')
    def test_handle_start_command_integration(self, mock_state_manager_class, mock_task_controller):
        """测试处理start命令集成"""
        # Mock状态管理器
        mock_state_manager = MagicMock()
        mock_state_manager_class.return_value = mock_state_manager
        mock_state_manager.state = MagicMock()
        
        # Mock任务控制器
        mock_task_controller.start_task.return_value = True
        mock_task_controller.get_task_status.return_value = {"state": "completed"}
        
        # 创建测试配置文件，使用项目中实际存在的Excel文件路径
        test_config = {
            "good_shop_file": "docs/good_shops.xlsx",
            "margin_calculator": "docs/profits_calculator.xlsx",
            "margin": 0.15,
            "output_path": "."
        }
        
        config_file = self.test_data_dir / "integration_test_start_command.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f)
        
        # Mock参数
        args = MagicMock()
        args.data = str(config_file)
        args.config = None
        args.dryrun = False
        args.select_goods = False
        args.select_shops = False
        
        # Mock配置加载
        with patch('cli.main.load_user_data') as mock_load_user_data, \
             patch('cli.main.load_system_config') as mock_load_system_config:
            
            mock_ui_config = UIConfig(
                good_shop_file="docs/good_shops.xlsx",
                margin_calculator="docs/profits_calculator.xlsx",
                output_path="."
            )
            mock_load_user_data.return_value = mock_ui_config
            
            mock_system_config = GoodStoreSelectorConfig()
            mock_load_system_config.return_value = mock_system_config
            
            # 执行测试
            result = handle_start_command(args)
            
            # 验证
            assert result == 0
            mock_load_user_data.assert_called_once_with(str(config_file))
            mock_load_system_config.assert_called_once_with(None)
            mock_task_controller.start_task.assert_called_once_with(mock_ui_config)
    
    @patch('cli.xp_cli.task_controller')
    @patch('cli.xp_cli.UIConfig')
    def test_xp_cli_controller_integration(self, mock_ui_config_class, mock_task_controller):
        """测试XP CLI控制器集成"""
        with patch('cli.xp_cli.Path.mkdir'), \
             patch('cli.xp_cli.Path.exists', return_value=True):
            
            controller = XuanpingCLIController()
            
            # Mock配置
            mock_config = MagicMock()
            mock_config.good_shop_file = "test.xlsx"
            mock_config.output_path = "."
            mock_ui_config_class.from_config_file.return_value = mock_config
            mock_ui_config_class.return_value = mock_config
            
            # Mock任务控制器
            mock_task_controller.start_task.return_value = True
            
            # Mock路径检查
            with patch('cli.xp_cli.Path.exists') as mock_path_exists:
                mock_path_exists.side_effect = [True, True, True]  # 配置文件存在，好店文件存在，输出路径存在
                
                # 执行测试
                result = controller.start_task("test_config.json")
                
                # 验证
                assert result is True
                mock_ui_config_class.from_config_file.assert_called_once_with("test_config.json")
                mock_task_controller.start_task.assert_called_once_with(mock_config)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
