#!/usr/bin/env python3
"""
测试Excel文件读取功能
"""
import sys
import os
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.xuanping.common.excel_processor import ExcelProcessor
from apps.xuanping.common.config import GoodStoreSelectorConfig

def test_excel_reading():
    """测试Excel文件读取"""
    print("=== 测试Excel文件读取功能 ===")
    
    # 配置文件路径
    config_file = "/Users/haowu/IdeaProjects/ai-product-selector3/docs/good_shops.xlsx"
    
    print(f"测试文件: {config_file}")
    print(f"文件是否存在: {os.path.exists(config_file)}")
    
    if not os.path.exists(config_file):
        print("❌ 文件不存在")
        return False
    
    try:
        # 创建配置
        config = GoodStoreSelectorConfig()
        
        # 创建Excel处理器
        processor = ExcelProcessor(config)
        
        print("正在读取Excel文件...")
        stores = processor.load_stores_from_excel(config_file)
        
        print(f"✅ 成功读取到 {len(stores)} 个店铺")
        
        # 显示前几个店铺信息
        for i, store in enumerate(stores[:3]):
            print(f"店铺 {i+1}: {store}")
            
        return True
        
    except Exception as e:
        print(f"❌ 读取Excel文件失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_excel_reading()
    sys.exit(0 if success else 1)