# 影刀RPA浏览器API测试
# 用于验证浏览器API的正确用法

import xbot
from xbot import print

def test_browser_api():
    """测试浏览器API的正确用法"""
    print("=== 浏览器API测试开始 ===")
    
    browser = None
    try:
        # 测试浏览器创建
        print("1. 测试浏览器创建...")
        browser = xbot.web.create("https://www.baidu.com", "chrome", load_timeout=20)
        print("✅ 浏览器创建成功")
        
        # 测试页面导航
        print("2. 测试页面导航...")
        browser.navigate("https://www.baidu.com")
        print("✅ 页面导航成功")
        
        # 测试元素查找
        print("3. 测试元素查找...")
        try:
            element = browser.find_by_xpath("//input[@id='kw']")
            if element:
                print("✅ 元素查找成功")
            else:
                print("⚠️ 元素未找到，但API调用成功")
        except Exception as e:
            print(f"⚠️ 元素查找失败：{str(e)}")
        
        # 测试标签页关闭
        print("4. 测试标签页关闭...")
        try:
            browser.close_tab()
            print("✅ 标签页关闭成功")
        except Exception as e:
            print(f"⚠️ 标签页关闭失败：{str(e)}")
        
        print("=== 浏览器API测试完成 ===")
        
    except Exception as e:
        print(f"❌ 浏览器API测试失败：{str(e)}")
        print("可能的原因：")
        print("1. Chrome浏览器未正确安装影刀插件")
        print("2. Chrome浏览器未启动")
        print("3. 权限问题")
        print("4. 影刀RPA版本兼容性问题")
        
    finally:
        # 测试浏览器关闭
        if browser:
            try:
                print("5. 测试浏览器关闭...")
                browser.close()
                print("✅ 浏览器关闭成功")
            except Exception as e:
                print(f"⚠️ 浏览器关闭失败：{str(e)}")

# 执行测试
test_browser_api()
