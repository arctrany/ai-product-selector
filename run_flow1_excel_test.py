#!/usr/bin/env python3
"""
Flow1 Excel文件提交测试运行脚本
简化版本，直接运行测试
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """运行Flow1 Excel测试"""
    print("🚀 Flow1 Excel文件提交测试")
    print("=" * 50)
    
    # 检查Excel文件是否存在
    excel_file = "/Users/haowu/IdeaProjects/ai-product-selector3/docs/好店推荐10.xlsx"
    if not os.path.exists(excel_file):
        print(f"❌ Excel文件不存在: {excel_file}")
        print("请确保文件路径正确")
        return
    
    print(f"✅ Excel文件存在: {excel_file}")
    
    # 运行测试
    test_script = Path(__file__).parent / "src_new" / "tests" / "test_flow1_excel_submission.py"
    
    if not test_script.exists():
        print(f"❌ 测试脚本不存在: {test_script}")
        return
    
    print(f"🔧 运行测试脚本: {test_script}")
    print("-" * 50)
    
    try:
        # 运行测试脚本
        result = subprocess.run([
            sys.executable, 
            str(test_script),
            "--url", "http://localhost:8889",
            "--file", excel_file
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n✅ 测试执行完成")
        else:
            print(f"\n⚠️ 测试执行完成，返回码: {result.returncode}")
            
    except Exception as e:
        print(f"❌ 执行测试时出错: {str(e)}")

if __name__ == "__main__":
    main()