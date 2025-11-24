"""
XP CLI测试

测试cli/xp_cli.py的核心功能
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from cli.xp_cli import XuanpingCLIController, create_parser

class TestXuanpingCLIController:
    """测试XuanpingCLIController类"""
    
    def setup_method(self):
        """测试前准备"""
        with patch('cli.xp_cli.Path.mkdir'):
            self.controller = XuanpingCLIController()
    
    @patch('cli.xp_cli.Path.exists')
    def test_load_config_from_file(self, mock_exists):
        """测试从文件加载配置"""
        mock_exists.return_value = True
        
        with patch('cli.models.UIConfig.from_config_file') as mock_from_config_file:
            mock_config = MagicMock()
            mock_from_config_file.return_value = mock_config
            
            config = self.controller.load_config("test_config.json")
            
            mock_from_config_file.assert_called_once_with("test_config.json")
            assert config == mock_config
    
    @patch('cli.xp_cli.Path.exists')
    def test_load_config_default(self, mock_exists):
        """测试加载默认配置"""
        mock_exists.return_value = False
        
        with patch('cli.models.UIConfig') as mock_ui_config:
            mock_config = MagicMock()
            mock_ui_config.return_value = mock_config
            
            config = self.controller.load_config()
            
            mock_ui_config.assert_called_once()
            assert config == mock_config
    
    @patch('cli.xp_cli.Path.exists')
    def test_save_config(self, mock_exists):
        """测试保存配置"""
        mock_exists.return_value = True
        
        with patch('cli.models.UIConfig.save_to_file') as mock_save_to_file:
            mock_config = MagicMock()
            self.controller.save_config(mock_config)
            
            mock_save_to_file.assert_called_once()
    
    @patch('cli.xp_cli.task_controller')
    def test_start_task_success(self, mock_task_controller):
        """测试成功启动任务"""
        # Mock配置
        mock_config = MagicMock()
        mock_config.good_shop_file = "test.xlsx"
        mock_config.output_path = "."
        
        with patch.object(self.controller, 'load_config', return_value=mock_config), \
             patch('cli.xp_cli.Path.exists', return_value=True), \
             patch.object(self.controller, 'save_config'):
            
            mock_task_controller.start_task.return_value = True
            
            result = self.controller.start_task("test_config.json")
            
            assert result is True
            mock_task_controller.start_task.assert_called_once_with(mock_config)
    
    @patch('cli.xp_cli.task_controller')
    def test_start_task_missing_good_shop_file(self, mock_task_controller):
        """测试缺少好店文件时启动任务"""
        # Mock配置
        mock_config = MagicMock()
        mock_config.good_shop_file = ""  # 空文件路径
        mock_config.output_path = "."
        
        with patch.object(self.controller, 'load_config', return_value=mock_config):
            result = self.controller.start_task("test_config.json")
            assert result is False
    
    @patch('cli.xp_cli.task_controller')
    def test_start_task_missing_output_path(self, mock_task_controller):
        """测试缺少输出路径时启动任务"""
        # Mock配置
        mock_config = MagicMock()
        mock_config.good_shop_file = "test.xlsx"
        mock_config.output_path = ""  # 空输出路径
        
        with patch.object(self.controller, 'load_config', return_value=mock_config):
            result = self.controller.start_task("test_config.json")
            assert result is False
    
    @patch('cli.xp_cli.task_controller')
    def test_start_task_file_not_exists(self, mock_task_controller):
        """测试文件不存在时启动任务"""
        # Mock配置
        mock_config = MagicMock()
        mock_config.good_shop_file = "nonexistent.xlsx"
        mock_config.output_path = "."
        
        with patch.object(self.controller, 'load_config', return_value=mock_config), \
             patch('cli.xp_cli.Path.exists', side_effect=[True, False, True]):  # 配置文件存在，好店文件不存在，输出路径存在
            
            result = self.controller.start_task("test_config.json")
            assert result is False
    
    @patch('cli.xp_cli.task_controller')
    def test_pause_task_success(self, mock_task_controller):
        """测试成功暂停任务"""
        mock_task_controller.pause_task.return_value = True
        
        result = self.controller.pause_task()
        
        assert result is True
        mock_task_controller.pause_task.assert_called_once()
    
    @patch('cli.xp_cli.task_controller')
    def test_pause_task_failure(self, mock_task_controller):
        """测试暂停任务失败"""
        mock_task_controller.pause_task.return_value = False
        
        result = self.controller.pause_task()
        
        assert result is False
        mock_task_controller.pause_task.assert_called_once()
    
    @patch('cli.xp_cli.task_controller')
    def test_resume_task_success(self, mock_task_controller):
        """测试成功恢复任务"""
        mock_task_controller.resume_task.return_value = True
        
        result = self.controller.resume_task()
        
        assert result is True
        mock_task_controller.resume_task.assert_called_once()
    
    @patch('cli.xp_cli.task_controller')
    def test_resume_task_failure(self, mock_task_controller):
        """测试恢复任务失败"""
        mock_task_controller.resume_task.return_value = False
        
        result = self.controller.resume_task()
        
        assert result is False
        mock_task_controller.resume_task.assert_called_once()
    
    @patch('cli.xp_cli.task_controller')
    def test_stop_task_success(self, mock_task_controller):
        """测试成功停止任务"""
        mock_task_controller.stop_task.return_value = True
        
        result = self.controller.stop_task()
        
        assert result is True
        mock_task_controller.stop_task.assert_called_once()
    
    @patch('cli.xp_cli.task_controller')
    def test_stop_task_failure(self, mock_task_controller):
        """测试停止任务失败"""
        mock_task_controller.stop_task.return_value = False
        
        result = self.controller.stop_task()
        
        assert result is False
        mock_task_controller.stop_task.assert_called_once()

class TestXPCLIParser:
    """测试XP CLI参数解析"""
    
    def setup_method(self):
        """测试前准备"""
        self.parser = create_parser()
    
    def test_start_command(self):
        """测试start命令"""
        args = self.parser.parse_args(['start'])
        assert args.command == 'start'
        assert args.config is None
    
    def test_start_command_with_config(self):
        """测试带配置文件的start命令"""
        args = self.parser.parse_args(['start', '--config', 'test.json'])
        assert args.command == 'start'
        assert args.config == 'test.json'
    
    def test_pause_command(self):
        """测试pause命令"""
        args = self.parser.parse_args(['pause'])
        assert args.command == 'pause'
    
    def test_resume_command(self):
        """测试resume命令"""
        args = self.parser.parse_args(['resume'])
        assert args.command == 'resume'
    
    def test_stop_command(self):
        """测试stop命令"""
        args = self.parser.parse_args(['stop'])
        assert args.command == 'stop'
    
    def test_status_command(self):
        """测试status命令"""
        args = self.parser.parse_args(['status'])
        assert args.command == 'status'
    
    def test_progress_command(self):
        """测试progress命令"""
        args = self.parser.parse_args(['progress'])
        assert args.command == 'progress'
    
    def test_logs_command(self):
        """测试logs命令"""
        args = self.parser.parse_args(['logs'])
        assert args.command == 'logs'
        assert args.lines == 50  # 默认值
    
    def test_logs_command_with_lines(self):
        """测试带行数的logs命令"""
        args = self.parser.parse_args(['logs', '--lines', '100'])
        assert args.command == 'logs'
        assert args.lines == 100
    
    def test_config_list_command(self):
        """测试config list命令"""
        args = self.parser.parse_args(['config', 'list'])
        assert args.command == 'config'
        assert args.config_action == 'list'
    
    def test_config_set_command(self):
        """测试config set命令"""
        args = self.parser.parse_args(['config', 'set', 'margin=0.2'])
        assert args.command == 'config'
        assert args.config_action == 'set'
        assert args.assignment == 'margin=0.2'

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
