# 最简单的影刀RPA测试
# 用于验证基本API是否正确

import xbot
from xbot import print

print("=== 简单测试开始 ===")

try:
    # 测试浏览器创建
    print("创建浏览器...")
    browser = xbot.web.create("https://www.baidu.com", "chrome", load_timeout=20)
    print("✅ 浏览器创建成功")
    
    # 测试页面导航
    print("导航到页面...")
    browser.navigate("https://www.baidu.com")
    print("✅ 页面导航成功")
    
    # 关闭浏览器
    print("关闭浏览器...")
    browser.close()
    print("✅ 浏览器关闭成功")
    
except Exception as e:
    print(f"❌ 测试失败：{str(e)}")
    print("错误类型：", type(e).__name__)

print("=== 简单测试结束 ===")
