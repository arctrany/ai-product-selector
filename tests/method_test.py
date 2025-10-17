# 测试常见的浏览器方法名
# 用于找出影刀RPA的正确API

import xbot
from xbot import print

def test_browser_methods():
    """测试常见的浏览器方法"""
    print("=== 测试浏览器方法 ===")
    
    browser = None
    try:
        # 创建浏览器
        print("1. 创建浏览器...")
        browser = xbot.web.create("https://www.baidu.com", "chrome", load_timeout=20)
        print("✅ 浏览器创建成功")
        
        # 测试URL
        test_url = "https://www.baidu.com"
        
        # 测试各种可能的导航方法
        navigation_methods = ['get', 'goto', 'navigate', 'open', 'visit', 'go', 'load', 'fetch']
        
        print(f"\n2. 测试导航方法到: {test_url}")
        for method_name in navigation_methods:
            try:
                if hasattr(browser, method_name):
                    print(f"✅ 找到方法: {method_name}")
                    method = getattr(browser, method_name)
                    print(f"   方法类型: {type(method)}")
                    # 尝试调用
                    try:
                        method(test_url)
                        print(f"   ✅ {method_name}(url) 调用成功!")
                        break
                    except Exception as e:
                        print(f"   ❌ {method_name}(url) 调用失败: {str(e)}")
                else:
                    print(f"❌ 方法不存在: {method_name}")
            except Exception as e:
                print(f"❌ 检查方法 {method_name} 时出错: {str(e)}")
        
        # 测试元素查找方法
        print(f"\n3. 测试元素查找方法")
        element_methods = ['find_element', 'findElement', 'find_element_by_xpath', 'findElementByXpath', 'select', 'locate']
        
        for method_name in element_methods:
            try:
                if hasattr(browser, method_name):
                    print(f"✅ 找到元素查找方法: {method_name}")
                    method = getattr(browser, method_name)
                    print(f"   方法类型: {type(method)}")
                else:
                    print(f"❌ 元素查找方法不存在: {method_name}")
            except Exception as e:
                print(f"❌ 检查元素查找方法 {method_name} 时出错: {str(e)}")
        
        # 测试关闭方法
        print(f"\n4. 测试关闭方法")
        close_methods = ['close', 'quit', 'exit', 'stop', 'destroy']
        
        for method_name in close_methods:
            try:
                if hasattr(browser, method_name):
                    print(f"✅ 找到关闭方法: {method_name}")
                    method = getattr(browser, method_name)
                    print(f"   方法类型: {type(method)}")
                else:
                    print(f"❌ 关闭方法不存在: {method_name}")
            except Exception as e:
                print(f"❌ 检查关闭方法 {method_name} 时出错: {str(e)}")
                
    except Exception as e:
        print(f"❌ 测试失败：{str(e)}")
        print(f"🔍 错误类型: {type(e).__name__}")
        
    finally:
        if browser:
            try:
                browser.close()
                print("\n✅ 浏览器关闭成功")
            except:
                pass
    
    print("\n=== 测试完成 ===")

# 执行测试
test_browser_methods()
