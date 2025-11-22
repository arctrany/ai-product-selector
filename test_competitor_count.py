#!/usr/bin/env python3
"""
测试跟卖数量识别准确性
"""

import re
from common.config.language_config import LanguageConfig, SupportedLanguage
from common.config.ozon_selectors_config import OzonSelectorsConfig

def test_competitor_count_recognition():
    """测试跟卖数量识别"""
    print("=== 跟卖数量识别准确性分析 ===\n")
    
    # 当前配置
    language_config = LanguageConfig()
    selectors_config = OzonSelectorsConfig()
    
    # 1. 查看跟卖数量提取相关的选择器
    print("1. 跟卖数量提取相关的选择器:")
    print(f"   competitor_count_selectors: {selectors_config.competitor_count_selectors}")
    print()
    
    # 2. 检查 competitor_count_patterns 正则表达式模式
    print("2. competitor_count_patterns 正则表达式模式:")
    for lang in language_config.get_all_supported_languages():
        patterns = language_config.get_competitor_count_patterns(lang)
        print(f"   {lang.value}: {patterns}")
    print()
    
    # 3. 验证当前配置是否能识别div.pdp_ga9中的数量'2'
    print("3. 验证当前配置是否能识别div.pdp_ga9中的数量'2':")
    
    # 模拟用户HTML中数量'2'的位置：在div.pdp_ga9中
    test_html_texts = [
        "2",  # 纯数字
        "2 продавца",  # 俄语格式
        "2 продавцов",  # 俄语格式
        "2 магазина",  # 俄语格式
        "2 магазинов",  # 俄语格式
        "Всего 2",  # 俄语格式
        "2 других",  # 俄语格式
        "2 sellers",  # 英语格式
        "2 stores",  # 英语格式
        "Total 2",  # 英语格式
        "2 other",  # 英语格式
        "2 additional",  # 英语格式
        "2 more",  # 英语格式
        "2 个卖家",  # 中文格式
        "2 家店铺",  # 中文格式
        "共 2",  # 中文格式
        "总计 2"  # 中文格式
    ]
    
    print("   测试文本识别:")
    for text in test_html_texts:
        # 使用配置的正则表达式模式解析数量
        found = False
        for lang in language_config.get_all_supported_languages():
            patterns = language_config.get_competitor_count_patterns(lang)
            for pattern in patterns:
                try:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        count = int(match.group(1))
                        print(f"     '{text}' -> {count} (语言: {lang.value}, 模式: {pattern})")
                        found = True
                        break
                except (ValueError, IndexError) as e:
                    continue
            if found:
                break
        
        # 如果所有模式都失败，尝试提取纯数字
        if not found:
            try:
                numbers = re.findall(r'\d+', text)
                if numbers:
                    count = int(numbers[0])  # 取第一个数字
                    print(f"     '{text}' -> {count} (通过数字提取)")
                else:
                    print(f"     '{text}' -> 无法识别")
            except ValueError:
                print(f"     '{text}' -> 无法识别")
    
    print()
    
    # 4. 分析当前配置的不足
    print("4. 当前配置分析:")
    print("   问题分析:")
    print("   - 当前的 competitor_count_selectors 只包含 [class*='competitors-count'] 和 [class*='seller-count']")
    print("   - 用户HTML中数量'2'在 div.pdp_ga9 中，当前选择器无法匹配")
    print("   - 需要添加更多选择器来匹配不同的HTML结构")
    print()
    
    # 5. 提供改进方案
    print("5. 改进方案:")
    print("   建议添加的选择器:")
    selectors_suggestions = [
        "div.pdp_ga9",  # 用户提到的具体位置
        "[class*='pdp_ga9']",  # 通用类名匹配
        ".competitor-count",  # 通用类名
        "[data-test-id*='competitor-count']",  # 数据属性匹配
        ".seller-count-display",  # 可能的类名
        "[class*='count-display']"  # 通用计数显示
    ]
    
    print("   建议的 competitor_count_selectors:")
    for selector in selectors_suggestions:
        print(f"     - {selector}")
    
    print()
    print("   建议添加的正则表达式模式:")
    additional_patterns = {
        "ru": [
            r'(\d+)\s*продавец',  # 单数形式
            r'(\d+)\s*магазин',  # 单数形式
        ],
        "en": [
            r'(\d+)\s*seller',  # 单数形式
            r'(\d+)\s*store',  # 单数形式
        ],
        "zh": [
            r'(\d+)\s*个',  # 通用量词
            r'(\d+)\s*家',  # 店铺量词
        ]
    }
    
    for lang, patterns in additional_patterns.items():
        print(f"   {lang} 语言:")
        for pattern in patterns:
            print(f"     - {pattern}")

if __name__ == "__main__":
    test_competitor_count_recognition()
