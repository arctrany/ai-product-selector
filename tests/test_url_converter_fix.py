#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
URL转换器修复验证测试
验证修改后的URL转换逻辑是否正确生成有效的OZON产品URL
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.url_converter import convert_image_url_to_product_url

def test_url_conversion():
    """测试URL转换功能"""
    print("🧪 URL转换器修复验证测试")
    print("=" * 50)
    
    # 测试用例
    test_cases = [
        # OZON图片URL示例
        "https://cdn1.ozone.ru/s3/multimedia-x/wc1000/6123456789.jpg",
        "https://ir.ozone.ru/multimedia/7/wc1000/7242104659.jpg",
        "https://cdn1.ozone.ru/s3/multimedia-y/wc750/1234567890.png",
        # 其他可能的格式
        "https://example.com/path/9876543210.webp",
    ]
    
    print("📋 测试用例:")
    for i, image_url in enumerate(test_cases, 1):
        print(f"  {i}. {image_url}")
    
    print("\n" + "=" * 50)
    print("🔧 测试结果:")
    
    success_count = 0
    for i, image_url in enumerate(test_cases, 1):
        result = convert_image_url_to_product_url(image_url)
        print(f"  测试 {i}:")
        print(f"    输入: {image_url}")
        print(f"    输出: {result}")
        
        if result and "product/" in result and not result.endswith("/-"):
            print(f"    ✅ 转换成功")
            success_count += 1
        else:
            print(f"    ❌ 转换失败")
        print()
    
    print("=" * 50)
    print(f"📊 测试总结: {success_count}/{len(test_cases)} 个测试通过")
    
    if success_count == len(test_cases):
        print("🎉 所有测试通过！URL转换器修复成功！")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False

def main():
    """主函数"""
    try:
        success = test_url_conversion()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
