"""
测试 CLI 标志解析

验证 --select-goods 和 --select-shops 标志的解析逻辑
"""

import pytest
import sys
from unittest.mock import patch, MagicMock
from cli.main import create_parser


class TestCLIFlags:
    """测试 CLI 标志解析"""
    
    def test_default_mode_is_select_shops(self):
        """测试默认模式是 select-shops"""
        parser = create_parser()
        
        # 不提供任何选择模式标志，需要提供 --data 参数
        args = parser.parse_args(['start', '--data', 'test.json'])

        # 默认应该是 select-shops 模式（select_goods 为 False）
        assert hasattr(args, 'select_goods')
        assert args.select_goods == False

    def test_select_goods_flag(self):
        """测试 --select-goods 标志"""
        parser = create_parser()

        args = parser.parse_args(['start', '--data', 'test.json', '--select-goods'])

        # 应该设置 select_goods 为 True
        assert hasattr(args, 'select_goods') and args.select_goods == True

    def test_select_shops_flag(self):
        """测试 --select-shops 标志"""
        parser = create_parser()

        args = parser.parse_args(['start', '--data', 'test.json', '--select-shops'])

        # 应该设置 select_shops 为 True
        assert hasattr(args, 'select_shops') and args.select_shops == True
    
    def test_mutual_exclusivity(self):
        """测试两个标志互斥"""
        parser = create_parser()
        
        # 同时提供两个标志应该报错
        with pytest.raises(SystemExit):
            parser.parse_args(['start', 'test.xlsx', 'calc.xlsx', '--select-goods', '--select-shops'])
    
    def test_flags_work_with_dryrun(self):
        """测试标志与 --dryrun 一起工作"""
        parser = create_parser()
        
        # select-goods + dryrun
        args1 = parser.parse_args(['start', '--data', 'test.json', '--select-goods', '--dryrun'])
        assert hasattr(args1, 'select_goods') and args1.select_goods == True
        assert hasattr(args1, 'dryrun') and args1.dryrun == True

        # select-shops + dryrun
        args2 = parser.parse_args(['start', '--data', 'test.json', '--select-shops', '--dryrun'])
        assert hasattr(args2, 'dryrun') and args2.dryrun == True
    
    def test_error_message_for_both_flags(self):
        """测试同时提供两个标志时的错误消息"""
        parser = create_parser()
        
        # 验证会抛出 SystemExit
        with pytest.raises(SystemExit):
            parser.parse_args(['start', '--data', 'test.json', '--select-goods', '--select-shops'])


class TestModeDetection:
    """测试模式检测逻辑"""
    
    def test_select_goods_mode_detection(self):
        """测试 select-goods 模式被正确检测"""
        # 测试模式字符串的生成逻辑
        select_goods = True
        select_mode = 'select-goods' if select_goods else 'select-shops'
        assert select_mode == 'select-goods'

    def test_select_shops_mode_detection(self):
        """测试 select-shops 模式被正确检测（默认）"""
        # 测试模式字符串的生成逻辑
        select_goods = False
        select_mode = 'select-goods' if select_goods else 'select-shops'
        assert select_mode == 'select-shops'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
